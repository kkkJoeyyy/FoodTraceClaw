from fastapi import APIRouter
from app.models import IngestRequest, StoreOut, DishOut
from app.database import insert_store, insert_dish, insert_dish_skip_duplicate, find_store_by_name_location, get_store
from app.extraction.geocode import geocode

router = APIRouter()


@router.post("/ingest")
async def ingest(req: IngestRequest):
    store_in = req.store
    existing = find_store_by_name_location(store_in.name, store_in.location)

    if existing:
        store_id = existing["id"]
        for d in store_in.dishes:
            insert_dish_skip_duplicate(store_id, d.name, d.description)
        store = get_store(store_id)
        return {"status": "updated", "store": _store_to_out(store) if store else None}

    coords = None
    if store_in.lat is None and store_in.lon is None:
        search_addr = f"{store_in.address} {store_in.location}".strip()
        coords = await geocode(search_addr or store_in.location)

    store_id = insert_store(
        name=store_in.name,
        location=store_in.location,
        address=store_in.address,
        lat=coords[0] if coords else store_in.lat,
        lon=coords[1] if coords else store_in.lon,
        description=store_in.description,
        category=store_in.category,
        source_text=store_in.source_text,
        source_type=store_in.source_type,
    )
    for d in store_in.dishes:
        insert_dish(store_id, d.name, d.description)

    store = get_store(store_id)
    return {"status": "created", "store": _store_to_out(store) if store else None}


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
