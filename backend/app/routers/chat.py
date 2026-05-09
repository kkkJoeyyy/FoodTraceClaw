import asyncio
import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.models import ChatRequest, StoreOut, DishOut
from app.extraction.llm_extractor import extract_from_text, classify_intent
from app.extraction.vl_extractor import extract_from_image
from app.extraction.geocode import geocode
from app.extraction.web_search import search_store_locations
from app.database import insert_store, insert_dish_skip_duplicate, find_store_by_name_location, get_store
from app.recommendation.engine import fetch_all_stores_by_location

router = APIRouter()

# In-memory state
_pending_nearby: dict[str, bool] = {}
_last_query: dict[str, dict] = {}  # session_id -> {location_query, all_stores, shown_count}


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _extract_city(address: str) -> str:
    """Extract city name from Chinese address like '广东省广州市天河区' → '广州市'."""
    import re
    matches = re.findall(r'([一-龥]{2,4}市)', address)
    return matches[-1] if matches else ""


def _store_to_out(store: dict) -> StoreOut:
    return StoreOut(
        id=store["id"],
        name=store["name"],
        location=store["location"],
        address=store.get("address", ""),
        lat=store.get("lat"),
        lon=store.get("lon"),
        description=store.get("description", ""),
        category=store.get("category", ""),
        source_type=store.get("source_type", "text"),
        created_at=store.get("created_at", ""),
        dishes=[DishOut(**d) for d in store.get("dishes", [])],
        distance_km=store.get("_distance_km"),
        closest_addr=store.get("_closest_addr", ""),
    )


# ---- Core logic (returns dict, used by both SSE and sync) ----


async def _do_extract(message: str, images: list[str]) -> dict:
    if images:
        result = await extract_from_image(images[0])
    else:
        result = await extract_from_text(message)

    if result.get("has_food") is False:
        return {"intent": "extract", "reply": "没有从中找到美食信息，换一段内容试试？"}

    stores_data = result.get("stores", [])
    summary = result.get("summary", "")
    if not stores_data:
        store_data = result.get("store", {})
        if store_data:
            stores_data = [store_data]

    if not stores_data:
        return {"intent": "extract", "reply": "未能识别店铺信息，请补充地点后重试。"}

    # Pre-fetch all web search results in parallel
    import asyncio as _asyncio
    _search_sem = _asyncio.Semaphore(2)  # Amap limit: 3 req/s, play safe with 2

    async def _search_one(name: str, loc: str) -> tuple:
        async with _search_sem:
            try:
                return await search_store_locations(name, loc)
            except Exception:
                return []

    web_results: dict[str, list[dict]] = {}
    searches = [
        (s.get("name", ""), s.get("location", ""))
        for s in stores_data
        if s.get("name") and not find_store_by_name_location(s["name"], s.get("location", ""))
    ]
    if searches:
        tasks = [_search_one(name, loc) for name, loc in searches]
        results_list = await _asyncio.gather(*tasks)
        for (name, loc), result in zip(searches, results_list):
            web_results[f"{name}|{loc}"] = result

    saved_stores = []
    for store_data in stores_data:
        store_name = store_data.get("name", "")
        store_location = store_data.get("location", "")
        if not store_name or not store_location:
            continue

        existing = find_store_by_name_location(store_name, store_location)
        if existing:
            store_id = existing["id"]
            for d in store_data.get("dishes", []):
                insert_dish_skip_duplicate(store_id, d.get("name", ""), d.get("description", ""))
            s = get_store(store_id)
            if s:
                saved_stores.append(_store_to_out(s))
            continue  # Skip POI search + chain creation for existing stores
        else:
            # Use pre-fetched Amap POI results for precise location
            web_locations = web_results.get(f"{store_name}|{store_location}", [])
            if not web_locations:
                continue  # POI not found, skip this store

            try:
                # Collect addresses with coordinates (same city only), dedup by address
                loc_addrs = []
                seen = set()
                for wl in web_locations:
                    addr = wl.get("address", "").strip()
                    wl_lat = wl.get("lat")
                    wl_lon = wl.get("lon")
                    if addr and wl_lat and wl_lon and addr not in seen:
                        seen.add(addr)
                        loc_addrs.append({"addr": addr, "lat": wl_lat, "lon": wl_lon})

                if not loc_addrs:
                    continue  # No valid addresses in this city

                # Primary coords from first address
                first = loc_addrs[0]
                store_id = insert_store(
                    name=store_name, location=store_location,
                    address=json.dumps(loc_addrs, ensure_ascii=False),
                    lat=first["lat"], lon=first["lon"],
                    description=store_data.get("description", ""),
                    category=store_data.get("category", ""),
                    source_text=message[:500], source_type="text",
                )
                for d in store_data.get("dishes", []):
                    insert_dish_skip_duplicate(store_id, d.get("name", ""), d.get("description", ""))

                s = get_store(store_id)
                if s:
                    saved_stores.append(_store_to_out(s))
            except Exception:
                pass  # POI processing failed, skip this store

    reply = summary or f"已记录 {len(saved_stores)} 家店铺"
    return {
        "intent": "extract",
        "reply": reply,
        "summary": summary,
        "stores": [s.model_dump() for s in saved_stores],
    }


async def _do_query(message: str, session_id: str) -> dict:
    intent_result = await classify_intent(message)
    location = intent_result.get("location", "")

    if not location:
        return {
            "intent": "query",
            "reply": "你想查询哪个地方的美食？请告诉我城市或区域名称。",
        }

    coords = await geocode(location)
    result = await fetch_all_stores_by_location(
        location_query=location,
        lat=coords[0] if coords else None,
        lon=coords[1] if coords else None,
    )

    stores = result["stores"]
    if not stores:
        return {
            "intent": "query",
            "reply": f"在 {location} 还没收录美食，快去抖音/小红书找找灵感吧！",
        }

    total = result["total"]
    if total <= 5:
        reply = f"{location} 找到 {total} 家店铺："
    else:
        reply = f"{location} 找到 {total} 家店铺，前 5 家："

    store_outs = [_store_to_out(s).model_dump() for s in stores]
    # Save query state for pagination
    _last_query[session_id] = {
        "location": location, "all_stores": stores, "shown": 5
    }
    return {
        "intent": "query",
        "reply": reply,
        "stores": store_outs[:5],
        "all_stores": store_outs,
        "total": total,
    }


async def _do_nearby(session_id: str, lat: float | None = None, lon: float | None = None) -> dict:
    """Handle nearby intent. If lat/lon provided, do nearby query; else set pending flag."""
    if lat is not None and lon is not None:
        result = await fetch_all_stores_by_location(
            location_query="", lat=lat, lon=lon,
        )
        stores = result["stores"]
        _pending_nearby.pop(session_id, None)

        if not stores:
            return {
                "intent": "nearby",
                "reply": "你附近还没收录美食，快去抖音/小红书找找灵感吧！",
            }

        total = result["total"]
        if total <= 5:
            reply = f"你附近找到 {total} 家店铺："
        else:
            reply = f"你附近找到 {total} 家店铺，前 5 家："

        store_outs = [_store_to_out(s).model_dump() for s in stores]
        # Save query state for pagination
        _last_query[session_id] = {
            "location": "附近", "all_stores": stores, "shown": 5
        }
        return {
            "intent": "nearby",
            "reply": reply,
            "stores": store_outs[:5],
            "all_stores": store_outs,
            "total": total,
        }
    else:
        _pending_nearby[session_id] = True
        return {
            "intent": "nearby",
            "reply": "请先发送你的位置信息（点击+→位置），我来告诉你附近有什么好吃的～",
        }


# ---- SSE generators (wrap core logic for streaming) ----

async def _process_extract_sse(message: str, images: list[str]):
    yield _sse({"type": "status", "text": "好滴收到～正在为您记录..."})
    await asyncio.sleep(0.3)
    yield _sse({"type": "status", "text": "正在分析内容中的美食信息..."})

    result = await _do_extract(message, images)

    yield _sse({"type": "status", "text": "分析完成，正在保存..."})
    yield _sse({"type": "done", **result})


async def _process_query_sse(message: str, session_id: str):
    result = await _do_query(message, session_id)
    yield _sse({"type": "done", **result})


async def _process_nearby_sse(session_id: str):
    result = await _do_nearby(session_id)
    yield _sse({"type": "done", **result})


async def _do_more(session_id: str) -> dict:
    """Return next page of stores for the last query."""
    state = _last_query.get(session_id)
    if not state:
        return {"intent": "more", "reply": "还没有查询过，试试问「XX有什么好吃的」吧！"}

    all_stores = state["all_stores"]
    shown = state["shown"]
    location = state["location"]
    remaining = len(all_stores) - shown

    if remaining <= 0:
        return {"intent": "more", "reply": "已经竭尽数据库了！换一个地方问问吧。"}

    next_batch = all_stores[shown:shown + 5]
    state["shown"] = shown + len(next_batch)
    new_remaining = len(all_stores) - state["shown"]

    reply = f"继续推荐 {location} 的美食："
    if new_remaining > 0:
        reply += f"（还有 {new_remaining} 家，回复「还有吗」继续）"

    store_outs = [_store_to_out(s).model_dump() for s in next_batch]
    return {
        "intent": "more",
        "reply": reply,
        "stores": store_outs,
        "has_more": new_remaining > 0,
        "total_remaining": new_remaining,
    }


async def _process_other_sse():
    yield _sse({
        "type": "done",
        "intent": "other",
        "reply": (
            "我可以帮你：\n"
            "1. 粘贴抖音/小红书的分享文案，我提取其中的美食店铺和菜品\n"
            "2. 询问「XX有什么好吃的？」查看推荐\n"
            "3. 发送「附近有什么好吃的」查看周边美食\n"
            "试试看吧！"
        ),
    })


# ---- Routes ----

@router.post("/chat")
async def chat_post(req: ChatRequest):
    message = req.message.strip()
    session_id = req.session_id
    images = req.images

    if images and not message:
        return StreamingResponse(
            _process_extract_sse("", images),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    if not message:
        return {"intent": "other", "reply": ""}

    intent_result = await classify_intent(message)
    intent = intent_result.get("intent", "other")

    if intent == "extract":
        gen = _process_extract_sse(message, images)
    elif intent == "query":
        gen = _process_query_sse(message, session_id)
    elif intent == "nearby":
        gen = _process_nearby_sse(session_id)
    else:
        gen = _process_other_sse()

    return StreamingResponse(
        gen,
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


@router.get("/chat")
async def chat_get(
    message: str = Query(...),
    session_id: str = Query(...),
):
    """Synchronous chat endpoint for WeChat Bot (returns JSON, not SSE)."""
    if not message.strip():
        return {"intent": "other", "reply": ""}

    intent_result = await classify_intent(message.strip())
    intent = intent_result.get("intent", "other")

    if intent == "extract":
        return await _do_extract(message.strip(), [])
    elif intent == "query":
        return await _do_query(message.strip(), session_id)
    elif intent == "nearby":
        return await _do_nearby(session_id)
    elif intent == "more":
        return await _do_more(session_id)
    else:
        return {
            "intent": "other",
            "reply": (
                "我可以帮你：\n"
                "1. 粘贴抖音/小红书的分享文案，我提取其中的美食店铺和菜品\n"
                "2. 询问「XX有什么好吃的？」查看推荐\n"
                "3. 发送「附近有什么好吃的」查看周边美食\n"
                "试试看吧！"
            ),
        }


# ---- Location endpoint (called by wechaty bridge) ----

@router.post("/location")
async def receive_location(
    session_id: str = Query(...),
    lat: float | None = Query(None),
    lon: float | None = Query(None),
    address: str | None = Query(None),
):
    """Receive a location share. If user has pending nearby request, do query."""
    # Geocode address if provided instead of lat/lon
    if address and (lat is None or lon is None):
        coords = await geocode(address)
        if coords:
            lat, lon = coords[0], coords[1]
        else:
            # Geocode failed — fallback: extract city from address for location query
            city = _extract_city(address)
            if city and _pending_nearby.get(session_id):
                result = await _do_query(f"{city}有什么好吃的", session_id)
                # Override intent to nearby
                result["intent"] = "nearby"
                _pending_nearby.pop(session_id, None)
                return result
            elif city:
                _pending_nearby.pop(session_id, None)
                result = await _do_query(f"{city}有什么好吃的", session_id)
                result["intent"] = "nearby"
                result["reply"] = f"无法获取精确位置，为你搜索「{city}」的美食：\n{result['reply']}"
                return result
            else:
                return {
                    "intent": "other",
                    "reply": "无法识别地址，请发送更具体的位置或在消息中说明城市名～",
                }

    if lat is not None and lon is not None:
        result = await _do_nearby(session_id, lat=lat, lon=lon)
        return result
    else:
        return {
            "intent": "other",
            "reply": "收到位置！你可以问「附近有什么好吃的」来查看周边美食～",
        }
