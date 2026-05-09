import sqlite3
import os
from app.config import DB_PATH


def get_db_path() -> str:
    path = DB_PATH
    if path.startswith("/app/"):
        cwd_path = os.path.join(os.getcwd(), "data", "foodtrace.db")
        if os.path.exists(os.path.dirname(cwd_path)) or not path.startswith("/app/data"):
            pass
    return path


def _resolve_path() -> str:
    """Resolve DB path. Uses ./data/ locally, /app/data/ in Docker."""
    path = DB_PATH
    # Check if we're in Docker (/app/data exists or is writable)
    docker_data = "/app/data"
    try:
        os.makedirs(docker_data, exist_ok=True)
        return path
    except OSError:
        # Not in Docker, use local ./data/
        local = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "foodtrace.db"
        )
        os.makedirs(os.path.dirname(local), exist_ok=True)
        return local


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_resolve_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS stores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            location    TEXT NOT NULL,
            address     TEXT DEFAULT '[]',
            lat         REAL,
            lon         REAL,
            description TEXT DEFAULT '',
            category    TEXT DEFAULT '',
            source_text TEXT DEFAULT '',
            source_type TEXT DEFAULT 'text',
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS dishes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id    INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
            name        TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at  TEXT DEFAULT (datetime('now'))
        );

        -- Remove existing duplicate dishes (keep the one with lowest id)
        DELETE FROM dishes WHERE id NOT IN (
            SELECT MIN(id) FROM dishes GROUP BY store_id, name
        );

        -- Prevent future duplicates
        CREATE UNIQUE INDEX IF NOT EXISTS idx_dishes_store_name
            ON dishes(store_id, name);

        CREATE TABLE IF NOT EXISTS recommendations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            store_id        INTEGER NOT NULL REFERENCES stores(id),
            location_query  TEXT NOT NULL,
            shown_at        TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_stores_location ON stores(location);
        CREATE INDEX IF NOT EXISTS idx_stores_category ON stores(category);
        CREATE INDEX IF NOT EXISTS idx_dishes_store ON dishes(store_id);
        CREATE INDEX IF NOT EXISTS idx_rec_session
            ON recommendations(session_id, location_query);
    """)
    conn.commit()
    conn.close()


# ---- Store CRUD ----

def insert_store(
    name: str,
    location: str,
    address: str = "[]",
    lat: float | None = None,
    lon: float | None = None,
    description: str = "",
    category: str = "",
    source_text: str = "",
    source_type: str = "text",
) -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO stores (name, location, address, lat, lon, description,
           category, source_text, source_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, location, address, lat, lon, description, category,
         source_text, source_type),
    )
    conn.commit()
    store_id = cur.lastrowid
    conn.close()
    return store_id


def insert_dish(store_id: int, name: str, description: str = "") -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO dishes (store_id, name, description) VALUES (?, ?, ?)",
        (store_id, name, description),
    )
    conn.commit()
    dish_id = cur.lastrowid
    conn.close()
    return dish_id


def insert_dish_skip_duplicate(store_id: int, name: str, description: str = "") -> int | None:
    """Insert a dish, skipping if same name already exists for this store."""
    if not name.strip():
        return None
    conn = get_connection()
    cur = conn.execute(
        "INSERT OR IGNORE INTO dishes (store_id, name, description) VALUES (?, ?, ?)",
        (store_id, name, description),
    )
    conn.commit()
    dish_id = cur.lastrowid if cur.lastrowid > 0 else None
    conn.close()
    return dish_id


def find_store_by_name_location(
    name: str, location: str, radius_km: float = 3.0
) -> dict | None:
    """Find existing store with same name near the same location."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM stores WHERE name = ? AND location = ?",
        (name, location),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_store(store_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM stores WHERE id = ?", (store_id,)).fetchone()
    if row:
        store = dict(row)
        dishes = conn.execute(
            "SELECT * FROM dishes WHERE store_id = ?", (store_id,)
        ).fetchall()
        store["dishes"] = [dict(d) for d in dishes]
        conn.close()
        return store
    conn.close()
    return None


def get_stores(
    page: int = 1,
    page_size: int = 20,
    location: str = "",
    category: str = "",
) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM stores WHERE 1=1"
    params: list = []
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([page_size, (page - 1) * page_size])
    rows = conn.execute(query, params).fetchall()
    stores = []
    for row in rows:
        store = dict(row)
        dishes = conn.execute(
            "SELECT * FROM dishes WHERE store_id = ?", (store["id"],)
        ).fetchall()
        store["dishes"] = [dict(d) for d in dishes]
        stores.append(store)
    conn.close()
    return stores


def delete_store(store_id: int) -> bool:
    conn = get_connection()
    cur = conn.execute("DELETE FROM stores WHERE id = ?", (store_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def get_dishes(store_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM dishes WHERE store_id = ?", (store_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---- Stats ----

def get_stats() -> dict:
    conn = get_connection()
    total_stores = conn.execute("SELECT COUNT(*) FROM stores").fetchone()[0]
    total_dishes = conn.execute("SELECT COUNT(*) FROM dishes").fetchone()[0]
    cat_rows = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM stores "
        "WHERE category != '' GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return {
        "total_stores": total_stores,
        "total_dishes": total_dishes,
        "categories": {r["category"]: r["cnt"] for r in cat_rows},
    }
