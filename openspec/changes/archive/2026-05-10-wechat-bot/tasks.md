# Tasks

## 1. Backend: Nearby Intent + GET /api/chat

- [x] 1.1 Update classify_intent prompt to recognize nearby intent
- [x] 1.2 Add GET /api/chat endpoint with query params (message, session_id) returning sync JSON
- [x] 1.3 Refactor chat logic to support both SSE (POST) and sync (GET) execution paths
- [x] 1.4 Add pending_nearby flag storage per session (in-memory dict)
- [x] 1.5 Handle nearby intent: check pending flag, request location if not set

## 2. Backend: Location Message Handling

- [x] 2.1 Add POST /api/location endpoint (accepts lat/lon or address param)
- [x] 2.2 Location with address: geocode via Amap, then nearby query
- [x] 2.3 Direct location share returns nearby results (no pending flag needed)
- [x] 2.4 Fallback when geocode fails: extract city from address, query by name

## 3. Wechaty Bridge Service

- [x] 3.1 Scaffold wechaty-bridge/ with TypeScript, package.json, tsconfig
- [x] 3.2 Initialize wechaty with wechat4u puppet, QR code login
- [x] 3.3 Handle text messages: immediately reply status, then call GET /api/chat, send result
- [x] 3.4 Detect location text pattern, extract address, forward to backend for geocoding
- [x] 3.5 Handle image messages: reply status, convert to base64, forward to /api/chat
- [x] 3.6 Map WeChat user ID to session_id for recommendation continuity
- [x] 3.7 Format replies: show distance, closest address, dishes
- [x] 3.8 Whitelist mode: only respond to specified WeChat nicknames

## 4. Docker Integration

- [x] 4.1 Add wechaty-bridge service to docker-compose.yml (profile: wechat)
- [x] 4.2 Create Dockerfile for wechaty-bridge
- [x] 4.3 Add env vars to .env.example (BACKEND_URL, WHITELIST)
- [x] 4.4 Configure wechaty-bridge backend internal networking

## 5. Nearby: 20km Radius Filter

- [x] 5.1 Add 20km radius limit in fetch_all_stores_by_location
- [x] 5.2 Multi-address distance: use closest address coordinate for distance calculation
- [x] 5.3 Return closest_addr in response for display

## 6. Amap POI Search for Store Details

- [x] 6.1 Create web_search.py with Amap POI place/text API
- [x] 6.2 Pre-fetch POI results in parallel (semaphore-limited, rate-limited)
- [x] 6.3 Store addresses as JSON array with coordinates: [{"addr":"...", "lat":..., "lon":...}]
- [x] 6.4 Store dedup: same name+location stores one row, skip if POI not found
- [x] 6.5 City filter removed (Amap city param sufficient)

## 7. Cleanup: Remove Feishu

- [x] 7.1 Delete backend/app/feishu.py
- [x] 7.2 Remove feishu imports from main.py, config.py
- [x] 7.3 Remove feishu from .env, .env.example, README
- [x] 7.4 Update README with WeChat Bot section

## 8. Server-side Pagination

- [x] 8.1 In-memory query state tracking (session → location + all_stores + shown_count)
- [x] 8.2 _do_more returns next 5 unseen stores
- [x] 8.3 "已经竭尽数据库了" when all stores shown

## 9. Test & Verify

- [x] 9.1 Scan WeChat QR code to log in
- [x] 9.2 Send test.txt → extract 14 stores with POI coordinates
- [x] 9.3 Send "广州有什么好吃的？" → 14 stores with distance + address
- [x] 9.4 Send location → 13 nearby stores within 20km, sorted by distance
- [x] 9.5 "还有吗" pagination: 5→5→3→exhausted
- [x] 9.6 No duplicate stores (same name+location = 1 row)
