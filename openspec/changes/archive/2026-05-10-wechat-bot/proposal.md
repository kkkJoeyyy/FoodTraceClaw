# WeChat Bot + Location Recommendations

## Why

目前只能通过 Web 页面使用 FoodTrace，手机上复制文案后需要切换到浏览器粘贴，流程繁琐。接入微信后，直接在微信聊天窗口 @Bot 即可录入和查询美食。同时补充基于微信定位的「附近美食」能力，让 Bot 能按距离排序推荐。

## What Changes

- 新增个人微信 Bot 桥接服务（wechaty），两步式回复（秒回状态 + 异步结果）
- 支持微信位置分享：发送位置直接返回附近美食（无需先问）
- 白名单模式：仅允许指定微信昵称使用 Bot
- 录入时**高德 POI 搜索**获取店铺精确地址和坐标，同城才收录
- 地址存为 JSON 数组带坐标 `[{"addr":"...", "lat":..., "lon":...}]`，一店一条记录
- 附近搜索：地址数组中取最近坐标计算距离，20km 半径过滤
- 新增 GET /api/chat 同步接口 + 服务端分页（「还有吗」翻页）

## Capabilities

### New Capabilities
- `wechat-bridge`: 微信消息桥接 — wechaty 收发，白名单，两步式回复
- `location-recommend`: 定位推荐 — 直接发位置即返回附近美食，20km 半径
- `amap-poi-extract`: 录入时高德 POI 搜索精确地址+坐标

### Modified Capabilities
- `food-chat`: 新增 nearby 意图、GET /api/chat 同步接口、服务端「还有吗」分页

## Impact

- 新增 `wechaty-bridge/` (TypeScript)
- 新增 `backend/app/extraction/web_search.py` — 高德 POI 搜索
- 修改 `backend/app/routers/chat.py` — GET /api/chat, nearby, more 分页, POI 集成
- 修改 `backend/app/recommendation/engine.py` — 多地址最近距离 + 20km 半径
- 修改 `backend/app/database.py` — address 存 JSON 数组
- 修改 `backend/app/models.py` — StoreOut 新增 distance_km, closest_addr

## Non-goals

- 不支持群聊（仅单聊）
- 不接入企业微信/飞书/公众号
- 不做多用户账号体系
