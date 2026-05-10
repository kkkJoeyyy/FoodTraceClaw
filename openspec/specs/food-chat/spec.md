# food-chat Specification

## Purpose
TBD - created by archiving change food-trace-v1. Update Purpose after archive.
## Requirements
### Requirement: Chat Intent Routing

The system SHALL classify incoming chat messages into one of five intents: extract, query, more, nearby, or other.

#### Scenario: User pastes food-related text

Given a user message "在成都春熙路发现蜀大侠火锅，毛肚好吃！"
When the system processes the message
Then the intent SHALL be classified as "extract"
And the system SHALL extract store and dish info from the text

#### Scenario: User asks for food recommendations

Given a user message "成都有什么好吃的？"
When the system processes the message
Then the intent SHALL be classified as "query"
And the system SHALL return all stores near the specified location

#### Scenario: User asks for nearby food

Given a user message "附近有什么好吃的？" or "最近有什么美食？"
When the system processes the message
Then the intent SHALL be classified as "nearby"
And the system SHALL request a fresh location from the user

#### Scenario: User requests more results

Given a user has previously received Top 5 store recommendations
When the user sends "还有吗" or "再来点"
Then the intent SHALL be classified as "more"
And the system SHALL return the next page of 5 stores

#### Scenario: General conversation

Given a user message that is not food-related
When the system processes the message
Then the intent SHALL be classified as "other"

---

### Requirement: Store and Dish Extraction via LLM

The system SHALL extract structured store and dish information from text using LLM.

#### Scenario: Extract store with dishes

Given a text "成都春熙路蜀大侠火锅，毛肚鲜嫩，鹅肠必点"
When the extraction is performed
Then the result SHALL contain a store object with name "蜀大侠火锅", location "成都春熙路"
And the result SHALL contain a dishes array with at least [{name: "毛肚"}, {name: "鹅肠"}]

#### Scenario: No food info in text

Given a text without food-related content
When the extraction is performed
Then the result SHALL be `{"has_food": false}`

#### Scenario: OpenAI provider

Given LLM_PROVIDER is set to "openai"
When extraction is called
Then the system SHALL use the OpenAI-compatible API

#### Scenario: Ollama provider

Given LLM_PROVIDER is set to "ollama"
When extraction is called
Then the system SHALL use the Ollama API

---

### Requirement: Store Deduplication

When extracting, if a store with the same name already exists near the same location, the system SHALL reuse the existing store and append new dishes to it.

#### Scenario: New content refers to existing store

Given "蜀大侠火锅" already exists in "成都春熙路"
When new content mentions "蜀大侠火锅" with a new dish "虾滑"
Then the store SHALL NOT be duplicated
And "虾滑" SHALL be added to the existing store's dishes

#### Scenario: Same name, different location

Given "蜀大侠火锅" exists in "成都春熙路"
When new content mentions "蜀大侠火锅" in "重庆解放碑"
Then a NEW store record SHALL be created for the Chongqing location

---

### Requirement: Food Extraction from Images via VL Model

The system SHALL extract store and dish information from images using vision-language models.

#### Scenario: Extract food from image

Given an image containing food content (screenshot from Douyin/XHS)
When VL extraction is performed
Then the result SHALL include store and dishes if identifiable

---

### Requirement: Location Geocoding

The system SHALL convert location names to lat/lon coordinates.

#### Scenario: Geocode Chinese address

Given "成都春熙路"
When geocoding is performed
Then valid lat and lon SHALL be returned

#### Scenario: Geocode failure

Given an unrecognizable location
When geocoding fails
Then the store SHALL be stored with NULL lat/lon
And it SHALL still be queryable by location name string match

---

### Requirement: Location-based Store Recommendation

The system SHALL recommend top 5 stores near a queried location, each with its dishes.

#### Scenario: Top 5 stores with dishes

Given multiple stores stored for "成都"
When user queries "成都有什么好吃的？"
Then exactly 5 stores SHALL be returned, ordered by distance
Each store SHALL include its list of dishes
And the response SHALL indicate `has_more: true`

#### Scenario: Second page

Given user has seen the first 5 stores
When user asks "还有吗"
Then the next 5 stores SHALL be returned
And previously shown stores SHALL NOT be included

#### Scenario: All results exhausted

Given user has seen all stores for the queried location
When user asks for more
Then the system SHALL respond "已经竭尽数据库了！"

#### Scenario: No stores in location

Given no stores for "北京"
When user queries "北京有什么好吃的？"
Then the system SHALL respond that no stores were found

#### Scenario: Session isolation

Given user A has seen stores 1-5 for "成都"
When user B queries "成都有什么好吃的？"
Then user B SHALL receive stores starting from rank 1
And user A's seen list SHALL NOT affect user B

---

### Requirement: Store and Dish Storage

The system SHALL persist stores and dishes in SQLite with proper foreign key relationships.

#### Scenario: Store a new store with dishes

Given extracted data: store {name, location, lat, lon}, dishes [{name}, {name}]
When saved
Then one row SHALL be inserted into stores
And two rows SHALL be inserted into dishes referencing the store

#### Scenario: Cascade delete

Given an existing store with dishes
When DELETE /api/stores/{id} is called
Then both the store and all its dishes SHALL be removed

---

### Requirement: Chat API

The system SHALL expose a POST /api/chat endpoint (SSE streaming) and a GET /api/chat endpoint (synchronous JSON, for WeChat Bot).

#### Scenario: Chat with text (SSE)

Given POST /api/chat with `{"message": "成都美食？", "session_id": "abc"}`
Then the response SHALL be SSE text/event-stream

#### Scenario: Chat with image

Given POST /api/chat with an image
Then the system SHALL perform VL extraction and return results via SSE

#### Scenario: Chat with text (sync)

Given GET /api/chat?message=广州有什么好吃的&session_id=wx_abc
Then the response SHALL be application/json ChatResponse (non-SSE, complete)
And SHALL include all matching stores, reply text, and intent

### Requirement: Frontend Chat Interface

The system SHALL provide a React web chat interface.

#### Scenario: Send text and receive store cards

Given the chat UI is loaded
When user types "成都有什么好吃的？" and sends
Then the response SHALL display store cards with name, location, category, and dish tags

#### Scenario: Paste image

Given the chat UI is loaded
When user pastes a food screenshot
Then extraction results SHALL appear as a store card

#### Scenario: Session persistence

Given a first-time visitor
Then a session_id SHALL be generated and stored in localStorage

---

### Requirement: Docker Deployment

The system SHALL be deployable via `docker-compose up`.

#### Scenario: Start services

Given docker-compose.yml
When `docker-compose up` is run
Then backend SHALL be on port 8000, frontend on port 3000
And SQLite data SHALL persist in a mounted volume

### Requirement: Nearby intent requests fresh location

When the intent is classified as "nearby", the system SHALL NOT search the database immediately. It SHALL prompt the user to share their current location.

#### Scenario: Nearby with pending flag

- **WHEN** user sends "附近有什么好吃的？"
- **THEN** the system SHALL set a pending nearby flag for that user
- **AND** SHALL respond: "请先发送你的位置信息（点击+→位置），我来告诉你附近有什么好吃的～"

#### Scenario: Location message resolves nearby request

- **WHEN** user sends a WeChat location message with lat/lon
- **AND** the user has a pending nearby flag
- **THEN** the system SHALL use the lat/lon to query nearby stores sorted by distance
- **AND** SHALL clear the pending flag

