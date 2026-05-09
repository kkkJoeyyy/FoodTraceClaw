# Design: WeChat Bot + Location Recommendations

## Context

FoodTrace 目前仅支持 Web Chat 访问。用户手机端使用时需切换 App 粘贴文案，体验差。接入微信后用户在聊天窗口直接与 Bot 交互，同时利用微信位置分享实现「最近美食」按距离排序。

现有架构: FastAPI 后端 + React 前端，SSE 流式响应。微信接入不修改现有 /api/chat 核心逻辑，而是新增桥接层做消息转换。

## Goals / Non-Goals

**Goals:**
- 个人微信收发消息，转发到现有 /api/chat 处理
- 接收微信位置分享，存储用户位置用于附近推荐
- 查询时支持「附近」语义：无具体地点则用最近分享的位置排序
- 微信消息格式 ↔ ChatRequest/SSE Response 转换

**Non-Goals:**
- 不支持群聊（仅单聊）
- 不做多用户账号体系（单用户场景）
- 不处理微信支付、小程序、视频号等
- 不在微信端实现 SSE 流式（微信不支持，使用同步回复）

## Decisions

### 1. 微信桥接方案: wechaty (TypeScript 独立服务)

**选择**: wechaty + wechaty-puppet-xp，作为独立 Docker 服务运行。

**理由**:
- wechaty 是最成熟的开源微信 Bot 框架，持续维护
- puppet-xp 基于 Windows WeChat 协议，macOS/Linux 均可运行
- TypeScript 类型安全，与 Python 后端通过 HTTP 通信
- 轻量化：只做消息收发和格式转换，业务逻辑全在 FastAPI

**备选**: itchat (Python, 不再维护)、wxauto (仅 Windows)。不采用。

### 2. 桥接通信: 两步式 HTTP REST 调用

微信不支持 SSE，采用两步式交互提升体验：

```
用户发消息
  ↓
wechaty 立即回复状态（秒回，用户无等待感）
  "收到～正在分析记录中..."（extract）
  "收到～正在查询中..."（query）
  ↓
wechaty 调用 GET /api/chat?message=...&session_id=...（同步阻塞，几秒）
  ↓
wechaty 发送结果（第二条消息）
```

新增 **GET /api/chat?message=...&session_id=...** 同步接口，内部调用现有逻辑但返回完整 JSON（非 SSE）。

### 3. 位置存储: 内存 dict + SQLite 持久化

- 数据结构: `{wechat_user_id: {lat, lon, updated_at}}`
- 用户每次分享位置时更新
- 服务重启不丢失（持久化到文件或 SQLite）

### 4. 「附近」意图处理

修改 `classify_intent` prompt，增加识别模式：
- "附近有什么好吃的" / "最近的美食" / "这附近有啥好吃的" → intent=query, location=null, nearby=true
- 在 _process_query 中，若 location 为空且 nearby=true，从位置存储读取用户位置
- 若位置存储为空，返回「请先发送你的位置信息」

### 5. 图片处理

微信图片消息通过 wechaty 获取图片 URL → 下载为 base64 → 传入 ChatRequest.images

## Risks / Trade-offs

- **[R] 个人微信封号风险**: 非官方 API，有概率被封 → **Mitigation**: 使用 puppet-xp 协议（较安全），控制消息频率
- **[R] puppet-xp 需运行 WeChat 客户端**: 需要在有 GUI 的环境或容器中运行 → **Mitigation**: Docker 使用 wine 或使用 padlocal 云端 puppet
- **[R] 微信位置格式兼容性**: 不同版本微信位置消息格式可能变化 → **Mitigation**: wechaty 已封装位置消息类型，稳定
