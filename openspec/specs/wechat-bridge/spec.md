# wechat-bridge Specification

## Purpose
TBD - created by archiving change wechat-bot. Update Purpose after archive.
## Requirements
### Requirement: Receive and forward WeChat text messages with acknowledgment

The wechaty bridge SHALL immediately acknowledge every incoming message before calling the backend, then send results when processing completes.

#### Scenario: Text message extraction with acknowledgment

- **WHEN** user sends "成都春熙路蜀大侠火锅，毛肚好吃！" via WeChat
- **THEN** the bridge SHALL immediately reply "收到～正在分析记录中..."
- **AND** SHALL call GET /api/chat with the text and session_id
- **AND** SHALL send the extraction result as a follow-up message

#### Scenario: Text message query with acknowledgment

- **WHEN** user sends "广州有什么好吃的？" via WeChat
- **THEN** the bridge SHALL immediately reply "收到～正在查询中..."
- **AND** SHALL call GET /api/chat
- **AND** SHALL send the recommendations as a follow-up message

#### Scenario: Image message

- **WHEN** user sends a food-related image via WeChat
- **THEN** the bridge SHALL immediately reply "收到图片～正在识别中..."
- **AND** SHALL download the image, convert to base64
- **AND** SHALL pass it in ChatRequest.images for VL extraction
- **AND** SHALL send the extraction result as a follow-up message

#### Scenario: Backend error

- **WHEN** the backend call fails or times out
- **THEN** the bridge SHALL send "抱歉，处理失败，请稍后重试"

---

### Requirement: WeChat session mapping

The system SHALL map each WeChat user ID to a stable session_id for recommendation tracking.

#### Scenario: First message from a WeChat user

- **WHEN** a WeChat user sends their first message
- **THEN** the system SHALL generate and persist a session_id for that WeChat user ID

#### Scenario: Returning user

- **WHEN** the same WeChat user sends subsequent messages
- **THEN** the system SHALL use the previously assigned session_id

---

### Requirement: Synchronous chat API for WeChat

A new GET /api/chat endpoint SHALL provide synchronous (non-SSE) responses for WeChat Bot consumption.

#### Scenario: Sync chat query

- **WHEN** GET /api/chat?message=广州有什么好吃的&session_id=wx_abc is called
- **THEN** the response SHALL be a complete JSON ChatResponse (not SSE)
- **AND** SHALL include all matching stores and reply text

#### Scenario: Sync chat extract

- **WHEN** GET /api/chat with food-related text is called
- **THEN** the system SHALL extract and store food data
- **AND** SHALL return the extraction result as JSON

