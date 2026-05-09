# FoodTrace - 美食追踪助手

从抖音/小红书分享文案中提取美食店铺和菜品，按地点推荐 Top 5 店铺。支持 Web Chat 和微信 Bot 两种交互方式。

## 项目结构

```
FoodTraceClaw/
├── backend/              # FastAPI 后端 (Python)
├── frontend/             # React 前端 (TypeScript + Vite)
├── wechaty-bridge/       # 微信 Bot 桥接 (TypeScript)
├── openspec/             # 规范驱动开发文档
├── docker-compose.yml
└── .env.example
```

## 快速开始

### 环境要求
- Python 3.12+
- Node.js 20+
- OpenAI 兼容 API Key（如 DashScope 阿里云百炼）
- 高德地图 API Key（用于 POI 搜索和地理编码）

### 1. 配置

```bash
cp .env.example .env
```

**.env 示例**：
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen3.5-omni-plus-2026-03-15
VL_MODEL=qwen3.5-omni-plus-2026-03-15
GEOCODE_PROVIDER=amap
AMAP_API_KEY=你的高德Key
```

### 2. 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173

## 核心流程

### 录入美食

```
用户粘贴分享文案/截图
  → LLM 理解内容，提取店铺名、地点、菜品
    （上下文推断地点、识别 👍👎 标记、自动归类）
  → 高德 POI 搜索精确地址和坐标（舍弃搜不到的店）
  → 去重入库：同名同地点只存一条，地址存为 JSON 数组
    [{"addr":"中山三路33号","lat":23.11,"lon":113.26}, ...]
```

### 查询推荐

```
用户：「广州有什么好吃的？」
  → 提取地点 → 返回全部匹配店铺
  → 按距离排序，多地址取最近距离
  → Top 5 +「还有吗」服务端分页（5→5→3→竭尽）
```

### 附近推荐

```
用户：发送微信位置
  → 高德地理编码 → 20km 半径内店铺
  → 按最近地址距离排序，显示距离+地址
```

## 微信 Bot 接入

使用 wechaty + wechaty-puppet-wechat4u：

```bash
cd wechaty-bridge
npm install
WHITELIST="你的昵称" BACKEND_URL=http://localhost:8000 npm start
```

白名单模式：只有 `WHITELIST` 中指定昵称的用户可以使用 Bot。微信交互两步式回复：

```
你: 发送 test.txt 内容
Bot: "收到～正在分析记录中..."          ← 秒回
Bot: "已记录 14 家店铺"                  ← 处理完成后
```

发送微信位置直接返回附近美食。

## 使用方式

1. **Web Chat**: 打开 http://localhost:5173
2. **微信 Bot**: wechaty-bridge 扫码登录，另一账号发消息
3. **录入**: 粘贴分享文案，高德 POI 自动精确坐标
4. **查询**: 「XX 有什么好吃的？」返回全部数据
5. **附近**: 发送微信位置直接返回 20km 内美食
6. **翻页**: 「还有吗」继续查看

## Docker 部署

```bash
docker-compose up
```

| 服务 | 端口 |
|------|------|
| 后端 | 8000 |
| 前端 | 3000 |
| 微信 Bot | wechaty-bridge 独立运行 |

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 主对话 (SSE) |
| GET | `/api/chat?message=&session_id=` | 主对话 (JSON，供 Bot 调用) |
| POST | `/api/ingest` | 直接录入店铺 |
| POST | `/api/location?session_id=&lat=&lon=` | 接收位置（支持 address 参数） |
| GET | `/api/stores` | 店铺列表 |
| DELETE | `/api/stores/{id}` | 删除店铺 |
| GET | `/api/stats` | 统计信息 |
