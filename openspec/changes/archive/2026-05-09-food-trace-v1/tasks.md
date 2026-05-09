# Tasks

## 1. Project Scaffold
- [x] Create backend/ with requirements.txt, Dockerfile
- [x] Create frontend/ with Vite + React + TypeScript
- [x] Create docker-compose.yml, .env.example
- [x] Configure openspec/config.yaml with project context

## 2. Backend Core
- [x] database.py: sqlite3 init, stores + dishes + recommendations tables, CRUD functions
- [x] config.py: environment variable management (LLM_PROVIDER, API keys, model names)
- [x] models.py: Pydantic request/response models (Store, Dish, ChatRequest, ChatResponse)

## 3. Extraction Module
- [x] llm_extractor.py: extract store + dishes[] from text via OpenAI / Ollama
- [x] store dedup: match by name + nearby location, reuse or create store, append dishes
- [x] vl_extractor.py: extract store + dishes from image via VL model
- [x] geocode.py: address → lat/lon via OSM Nominatim / Amap API

## 4. Recommendation Engine
- [x] engine.py: geo-distance query with dishes JOIN, pagination (LIMIT 5 OFFSET N), session dedup via recommendations table
- [x] Fallback: string match on location when geocode fails

## 5. API Routes
- [x] chat.py: POST /api/chat — intent routing (extract / query / more / other), integrate LLM + recommendation
- [x] ingest.py: POST /api/ingest — direct store + dishes entry
- [x] stores.py: GET /api/stores, GET /api/stores/{id}, DELETE /api/stores/{id}
- [x] stats.py: GET /api/stats — store count, dish count, category breakdown

## 6. React Frontend
- [x] App.tsx + useChat hook: message state, session_id generation
- [x] ChatWindow.tsx: message list with auto-scroll
- [x] MessageBubble.tsx: render text / store card / image
- [x] StoreCard.tsx: store name, location, category, description, dish tags
- [x] StoreList.tsx: Top 5 store recommendation list
- [x] InputArea.tsx: text input + image paste + send button
- [x] api.ts: fetch wrapper for backend endpoints

## 7. Integration & Verify
- [ ] docker-compose up — Docker Hub 镜像拉取超时（已配置镜像加速，待验证）
- [x] Paste text → extract store + dishes → verify stored
- [x] Paste second text mentioning same store → verify dishes appended, no duplicate store
- [ ] Paste image → VL extract — 待测试
- [x] Ask "XX有什么好吃的？" → Top 5 stores with dishes
- [x] Ask "还有吗？" → instant local pagination
- [ ] Switch LLM_PROVIDER to ollama → 待测试
