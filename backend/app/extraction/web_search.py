"""Search store locations via Amap POI search API."""

import asyncio
import time

_last_request = 0.0
_lock = asyncio.Lock()


async def search_store_locations(store_name: str, city: str) -> list[dict]:
    """Search Amap POI for store locations. Returns [{address, lat, lon}].
    Handles chain stores by returning multiple locations."""
    from app.config import AMAP_API_KEY
    if not AMAP_API_KEY:
        return []

    import httpx

    # Rate limit: 3 req/s
    global _last_request
    async with _lock:
        elapsed = time.time() - _last_request
        if elapsed < 0.35:
            await asyncio.sleep(0.35 - elapsed)
        _last_request = time.time()

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://restapi.amap.com/v3/place/text",
                params={
                    "key": AMAP_API_KEY,
                    "keywords": store_name,
                    "city": city,
                    "offset": 5,
                    "extensions": "base",
                },
            )
            data = resp.json()
            if data.get("status") != "1":
                return []

            pois = data.get("pois", [])
            results = []
            for p in pois:
                loc = p.get("location", "")
                if loc and "," in loc:
                    lon, lat = loc.split(",", 1)
                    results.append({
                        "address": p.get("address") or p.get("name", ""),
                        "lat": float(lat),
                        "lon": float(lon),
                        "source": "amap_poi",
                    })
            return results
    except Exception as e:
        print(f"[AmapPOI] Search error: {e}")
        return []
