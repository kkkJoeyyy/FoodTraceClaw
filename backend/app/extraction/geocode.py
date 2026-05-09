import httpx
from app.config import GEOCODE_PROVIDER, AMAP_API_KEY


async def geocode(address: str) -> tuple[float, float] | None:
    """Convert an address string to (lat, lon). Returns None on failure."""
    if GEOCODE_PROVIDER == "amap" and AMAP_API_KEY:
        return await _geocode_amap(address)
    return await _geocode_nominatim(address)


async def _geocode_nominatim(address: str) -> tuple[float, float] | None:
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": "FoodTraceClaw/0.1"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=headers)
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None


async def _geocode_amap(address: str) -> tuple[float, float] | None:
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {"key": AMAP_API_KEY, "address": address, "output": "json"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            if data.get("status") == "1" and data.get("geocodes"):
                loc = data["geocodes"][0]["location"]
                lon, lat = loc.split(",")
                return float(lat), float(lon)
    except Exception:
        pass
    return None
