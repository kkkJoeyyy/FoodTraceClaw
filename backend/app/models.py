from pydantic import BaseModel


class DishIn(BaseModel):
    name: str
    description: str = ""


class DishOut(BaseModel):
    id: int
    store_id: int
    name: str
    description: str


class StoreIn(BaseModel):
    name: str
    location: str
    address: str = ""
    lat: float | None = None
    lon: float | None = None
    description: str = ""
    category: str = ""
    source_text: str = ""
    source_type: str = "text"
    dishes: list[DishIn] = []


class StoreOut(BaseModel):
    id: int
    name: str
    location: str
    address: str
    lat: float | None
    lon: float | None
    description: str
    category: str
    source_type: str
    created_at: str
    dishes: list[DishOut] = []
    distance_km: float | None = None
    closest_addr: str = ""


class ChatRequest(BaseModel):
    message: str
    session_id: str
    images: list[str] = []  # base64 encoded


class ChatResponse(BaseModel):
    intent: str  # extract | query | more | other
    reply: str
    stores: list[StoreOut] = []
    has_more: bool = False
    total_remaining: int = 0


class IngestRequest(BaseModel):
    store: StoreIn


class StatsResponse(BaseModel):
    total_stores: int
    total_dishes: int
    categories: dict[str, int]
