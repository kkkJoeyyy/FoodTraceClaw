import json
import math
from app.database import get_connection

NEARBY_RADIUS_KM = 20.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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


def _same_city(store_location: str, query_location: str) -> bool:
    """Check if store is in the same city as the query."""
    if not store_location or not query_location:
        return True  # can't determine, include
    # Strip district/street details to just city name
    city = query_location[:2] if len(query_location) >= 2 else query_location
    return city in store_location


async def fetch_all_stores_by_location(
    location_query: str,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> dict:
    """Return stores matching location, sorted by distance.

    - location_query only: match by string LIKE
    - lat/lon only (nearby): within radius_km (default 20km)
    - location_query + lat/lon: match by string AND within radius, sorted by distance
    """
    if lat is not None and lon is not None and not location_query:
        radius_km = radius_km or NEARBY_RADIUS_KM

    conn = get_connection()
    all_stores = conn.execute("SELECT * FROM stores").fetchall()

    scored = []
    for s in all_stores:
        s = dict(s)
        loc = s.get("location", "")

        # Filter by location string
        if location_query:
            if not loc or location_query not in loc:
                continue

        # Calculate distance using the closest address
        if lat is not None and lon is not None:
            min_dist = float("inf")
            # Parse addresses JSON array for multiple coordinates
            addr_str = s.get("address", "[]")
            try:
                addrs = json.loads(addr_str) if isinstance(addr_str, str) else []
                if isinstance(addrs, list):
                    for a in addrs:
                        if isinstance(a, dict) and a.get("lat") and a.get("lon"):
                            d = haversine(lat, lon, a["lat"], a["lon"])
                            if d < min_dist:
                                min_dist = d
                                s["_closest_addr"] = a.get("addr", "")
                else:
                    min_dist = None
            except (json.JSONDecodeError, TypeError):
                min_dist = None

            if min_dist is not None and min_dist != float("inf"):
                if radius_km and min_dist > radius_km:
                    continue
                scored.append((s, min_dist))
            elif s.get("lat") is not None and s.get("lon") is not None:
                # Fallback to single lat/lon
                d = haversine(lat, lon, s["lat"], s["lon"])
                if radius_km and d > radius_km:
                    continue
                scored.append((s, d))
            elif not radius_km:
                scored.append((s, float("inf")))
        elif lat is not None and lon is not None:
            # Store has no coordinates, include with infinite distance
            if radius_km:
                continue  # Can't determine distance, skip
            scored.append((s, float("inf")))
        else:
            scored.append((s, float("inf")))

    scored.sort(key=lambda x: x[1])

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
        "total": len(result_stores),
    }
