from fastapi import APIRouter, HTTPException
from app.models import StoreOut, DishOut
from app.database import get_stores, get_store, delete_store

router = APIRouter()


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


@router.get("/stores")
async def list_stores(page: int = 1, page_size: int = 20, location: str = "", category: str = ""):
    stores = get_stores(page=page, page_size=page_size, location=location, category=category)
    return {"stores": [_store_to_out(s) for s in stores], "page": page}


@router.get("/stores/{store_id}")
async def get_store_by_id(store_id: int):
    store = get_store(store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return _store_to_out(store)


@router.delete("/stores/{store_id}")
async def remove_store(store_id: int):
    ok = delete_store(store_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Store not found")
    return {"status": "deleted"}
