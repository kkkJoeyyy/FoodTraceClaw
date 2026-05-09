# food-chat Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
