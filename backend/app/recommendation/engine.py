import math
from app.database import get_connection


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in km between two coordinates using the Haversine formula."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def fetch_all_stores_by_location(
    location_query: str,
    lat: float | None = None,
    lon: float | None = None,
) -> dict:
    """Return ALL stores matching a location, sorted by distance or recency."""
    conn = get_connection()

    all_stores = conn.execute("SELECT * FROM stores").fetchall()

    # Filter by location first
    scored = []
    for s in all_stores:
        s = dict(s)
        loc = s.get("location", "")
        if not loc or location_query not in loc:
            continue  # skip stores not matching the queried location
        if lat is not None and lon is not None and s["lat"] is not None and s["lon"] is not None:
            d = haversine(lat, lon, s["lat"], s["lon"])
            scored.append((s, d))
        else:
            scored.append((s, float("inf")))
    scored.sort(key=lambda x: x[1])

    total = len(scored)
    result_stores = []
    for store, dist in scored:
        dishes = conn.execute(
            "SELECT * FROM dishes WHERE store_id = ?", (store["id"],)
        ).fetchall()
        store["dishes"] = [dict(d) for d in dishes]
        store["_distance_km"] = round(dist, 2) if dist != float("inf") else None
        result_stores.append(store)

    conn.close()

    return {
        "stores": result_stores,
        "total": total,
    }
