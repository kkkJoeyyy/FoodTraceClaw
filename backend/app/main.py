from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import chat, ingest, stores, stats

app = FastAPI(title="FoodTrace", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(stores.router, prefix="/api", tags=["stores"])
app.include_router(stats.router, prefix="/api", tags=["stats"])


@app.on_event("startup")
def on_startup():
    init_db()
