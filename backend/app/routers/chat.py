import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models import ChatRequest, StoreOut, DishOut
from app.extraction.llm_extractor import extract_from_text, classify_intent
from app.extraction.vl_extractor import extract_from_image
from app.extraction.geocode import geocode
from app.database import insert_store, insert_dish, insert_dish_skip_duplicate, find_store_by_name_location, get_store
from app.recommendation.engine import fetch_all_stores_by_location

router = APIRouter()


def _sse(data: dict) -> str:
    """Format a dict as an SSE event."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


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
    )


async def _process_extract(message: str, images: list[str]):
    """Generator that yields SSE messages for the extract flow."""
    yield _sse({"type": "status", "text": "好滴收到～正在为您记录..."})

    await asyncio.sleep(0.3)
    yield _sse({"type": "status", "text": "正在分析内容中的美食信息..."})

    # Run extraction (non-streaming for clean structured output)
    if images:
        result = await extract_from_image(images[0])
    else:
        result = await extract_from_text(message)

    yield _sse({"type": "status", "text": "分析完成，正在保存..."})

    if result.get("has_food") is False:
        yield _sse({
            "type": "done",
            "intent": "extract",
            "reply": "没有从中找到美食信息，换一段内容试试？",
        })
        return

    stores_data = result.get("stores", [])
    summary = result.get("summary", "")

    if not stores_data:
        # Backward compat: single store
        store_data = result.get("store", {})
        if store_data:
            stores_data = [store_data]

    if not stores_data:
        yield _sse({
            "type": "done",
            "intent": "extract",
            "reply": "未能识别店铺信息，请补充地点后重试。",
        })
        return

    saved_stores = []
    for store_data in stores_data:
        store_name = store_data.get("name", "")
        store_location = store_data.get("location", "")
        if not store_name or not store_location:
            continue

        coords = await geocode(
            f"{store_data.get('address', '')} {store_location}".strip() or store_location
        )

        existing = find_store_by_name_location(store_name, store_location)
        if existing:
            store_id = existing["id"]
            for d in store_data.get("dishes", []):
                insert_dish_skip_duplicate(store_id, d.get("name", ""), d.get("description", ""))
        else:
            store_id = insert_store(
                name=store_name,
                location=store_location,
                address=store_data.get("address", ""),
                lat=coords[0] if coords else None,
                lon=coords[1] if coords else None,
                description=store_data.get("description", ""),
                category=store_data.get("category", ""),
                source_text=message[:500],
                source_type="text",
            )
            for d in store_data.get("dishes", []):
                insert_dish_skip_duplicate(store_id, d.get("name", ""), d.get("description", ""))

        s = get_store(store_id)
        if s:
            saved_stores.append(_store_to_out(s))

    reply = summary or f"已记录 {len(saved_stores)} 家店铺"
    yield _sse({
        "type": "done",
        "intent": "extract",
        "reply": reply,
        "summary": summary,
        "stores": [s.model_dump() for s in saved_stores],
    })


async def _process_query(message: str, session_id: str):
    """Query handler: returns ALL matching stores. Frontend handles local pagination."""
    intent_result = await classify_intent(message)
    location = intent_result.get("location", "")

    if not location:
        yield _sse({
            "type": "done", "intent": "query",
            "reply": "你想查询哪个地方的美食？请告诉我城市或区域名称。",
        })
        return

    coords = await geocode(location)
    result = await fetch_all_stores_by_location(
        location_query=location,
        lat=coords[0] if coords else None,
        lon=coords[1] if coords else None,
    )

    stores = result["stores"]
    if not stores:
        yield _sse({
            "type": "done", "intent": "query",
            "reply": f"在 {location} 还没收录美食，快去抖音/小红书找找灵感吧！",
        })
        return

    total = result["total"]
    if total <= 5:
        reply = f"{location} 找到 {total} 家店铺："
    else:
        reply = f"{location} 找到 {total} 家店铺，前 5 家："
    yield _sse({
        "type": "done",
        "intent": "query",
        "reply": reply,
        "stores": [_store_to_out(s).model_dump() for s in stores],
        "all_stores": [_store_to_out(s).model_dump() for s in stores],
        "total": result["total"],
    })


@router.post("/chat")
async def chat(req: ChatRequest):
    message = req.message.strip()
    session_id = req.session_id
    images = req.images

    if images and not message:
        return StreamingResponse(
            _process_extract("", images),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    if not message:
        return {"intent": "other", "reply": ""}

    intent_result = await classify_intent(message)
    intent = intent_result.get("intent", "other")

    if intent == "extract":
        generator = _process_extract(message, images)
    elif intent == "query":
        generator = _process_query(message, session_id)
    elif intent == "more":
        # Frontend handles local pagination — no backend call needed
        generator = _process_other()
    else:
        generator = _process_other()

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


async def _process_other():
    yield _sse({
        "type": "done",
        "intent": "other",
        "reply": (
            "我可以帮你：\n"
            "1. 粘贴抖音/小红书的分享文案，我提取其中的美食店铺和菜品\n"
            "2. 询问「XX有什么好吃的？」查看推荐\n"
            "3. 发送「还有吗」查看更多\n"
            "试试看吧！"
        ),
    })
