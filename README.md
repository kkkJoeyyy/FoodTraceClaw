# FoodTraceClaw
FoodTrace Claw 是一个基于SSD开发的面向美食爱好者的轻量化多模态助手，核心功能是从抖音、小红书、文本等多源内容中，通过 VL 大模型 + LLM 自动提取美食名称与地理位置，存入私有数据库。当你询问「附近有什么好吃的」或「XX 地方有什么美食」时，它会基于你的 IP 定位推送 Top5 附近美食，并支持分批追加推荐，直到库内内容推送完毕。

## 项目结构

```
FoodTraceClaw/
├── backend/          # FastAPI 后端 (Python)
├── frontend/         # React 前端 (TypeScript + Vite)
├── openspec/         # 规范驱动开发文档
├── docker-compose.yml
└── .env.example
```

## 快速开始 (本地开发)

### 环境要求
- Python 3.12+
- Node.js 20+
- OpenAI 兼容 API Key（如 DashScope 阿里云百炼）

### 1. 克隆并配置

```bash
cp .env.example .env
# 编辑 .env，填入 API Key 和模型配置
```

**.env 示例**（使用阿里云百炼 + 千问）：
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen3.5-omni-plus-2026-03-15
VL_MODEL=qwen3.5-omni-plus-2026-03-15
GEOCODE_PROVIDER=osm
```

### 2. 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端运行在 http://localhost:8000

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

## 核心流程

### 录入美食

```
用户粘贴分享文案/截图
        ↓
   SSE 流式响应：「好滴收到～正在为您记录...」
        ↓
   LLM 理解内容 → 提取店铺名、地点、菜品
   （理解上下文推断地点、识别 👍👎 标记、归类）
        ↓
   地理编码（地址 → 经纬度）
        ↓
   去重入库（同名同地点 → 追加新菜品，不重复）
        ↓
   返回记录结果
```

**支持的内容格式：**
- 抖音/小红书分享文案
- 个人美食日记（自由格式）
- 带分类、备注、评分的列表

### 查询推荐

```
用户：「广州有什么好吃的？」
        ↓
   提取地点「广州」→ 地理编码
        ↓
   一次返回全部匹配店铺（按距离排序）
        ↓
   前端显示 Top 5，点击「查看更多」即时展开（无网络请求）
        ↓
   全部显示后提示「已经竭尽数据库了！」
```

## 使用方式

1. 打开 http://localhost:5173
2. **录入美食**：粘贴抖音/小红书的分享文案或截图，助手自动提取店铺和菜品
3. **查询推荐**：输入「广州有什么好吃的？」一次拉取全部数据
4. **查看更多**：点击「查看更多」即刻展开，无需等待

## Docker 部署

```bash
docker-compose up
```

- 后端: http://localhost:8000
- 前端: http://localhost:3000
- SQLite 数据持久化在 `./data` 目录

可选启用本地 Ollama：
```bash
docker-compose --profile ollama up
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 主对话接口 |
| POST | `/api/ingest` | 直接录入店铺 |
| GET | `/api/stores` | 店铺列表 |
| GET | `/api/stores/{id}` | 店铺详情 |
| DELETE | `/api/stores/{id}` | 删除店铺 |
| GET | `/api/stats` | 统计信息 |