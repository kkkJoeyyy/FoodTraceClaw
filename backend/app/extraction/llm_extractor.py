import json
from typing import AsyncIterator
from app.config import LLM_PROVIDER, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, OLLAMA_HOST, OLLAMA_MODEL


EXTRACTION_PROMPT = """你是一个美食记录助手猫猫。用户会分享美食相关内容（抖音/小红书文案、个人美食日记等）。

请仔细阅读内容，理解其中的美食信息，提取出所有出现的**餐厅/店铺**及其**菜品**，返回 JSON：

{
  "summary": "一句话总结（如：记录了广州8家餐厅、佛山2家餐厅）",
  "stores": [
    {
      "name": "餐厅名称",
      "location": "城市+区域（根据上下文推断，如内容提到广州则填广州）",
      "address": "详细地址（如有）",
      "description": "一句话描述亮点",
      "category": "分类（粤菜/早茶/火锅/烧烤/川菜/小吃等）",
      "dishes": [
        {"name": "菜品名", "description": "描述（如👍推荐/👎不推荐等备注）"}
      ]
    }
  ]
}

规则：
- 从上下文推断 location（如标题写"广州接待备忘录"，则下面所有店铺 location 默认"广州"）
- 如果有明确地点标记（如"佛山："），该标记下的店铺使用对应地点
- 菜品后面有 👍 标记的，在 description 中注明"推荐"
- dishes 至少一个，没有明确菜品的填一个空菜品
- 如果没有任何美食信息，返回 {"has_food": false}

只返回 JSON。"""


async def extract_from_text(text: str) -> dict:
    if LLM_PROVIDER == "ollama":
        return await _extract_ollama(text)
    return await _extract_openai(text)


async def extract_from_text_stream(text: str) -> AsyncIterator[str]:
    """Stream the LLM's natural-language response, then yield structured result."""
    if LLM_PROVIDER == "ollama":
        async for chunk in _extract_ollama_stream(text):
            yield chunk
    else:
        async for chunk in _extract_openai_stream(text):
            yield chunk


async def classify_intent(text: str) -> dict:
    prompt = f"""分析用户消息的意图，返回 JSON：

- intent: "extract" (分享美食信息) / "query" (询问具体地点有什么好吃的) / "nearby" (询问附近/周边有什么好吃的) / "more" (要更多推荐) / "other"
- location: 目标地点（query 时提取，如"成都"；nearby/other 时为 null）

消息："{text}"

只返回 JSON。"""

    if LLM_PROVIDER == "ollama":
        return await _call_ollama_json(prompt)
    return await _call_openai_json(prompt)


async def _extract_openai(text: str) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    response = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT + "\n\n内容：\n" + text}],
        temperature=0.1,
    )
    return _parse_json(response.choices[0].message.content or "")


async def _extract_openai_stream(text: str) -> AsyncIterator[str]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    stream = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT + "\n\n内容：\n" + text}],
        temperature=0.1,
        stream=True,
    )
    full = ""
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else ""
        if delta:
            full += delta
            yield delta
    # Final structured result marker
    yield "\n<!--RESULT:" + json.dumps(_parse_json(full), ensure_ascii=False) + "-->"


async def _extract_ollama(text: str) -> dict:
    import ollama

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT + "\n\n内容：\n" + text}],
    )
    return _parse_json(response["message"]["content"])


async def _extract_ollama_stream(text: str) -> AsyncIterator[str]:
    import ollama

    stream = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT + "\n\n内容：\n" + text}],
        stream=True,
    )
    full = ""
    for chunk in stream:
        delta = chunk["message"]["content"]
        if delta:
            full += delta
            yield delta
    yield "\n<!--RESULT:" + json.dumps(_parse_json(full), ensure_ascii=False) + "-->"


async def _call_openai_json(prompt: str) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    response = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return _parse_json(response.choices[0].message.content or "")


async def _call_ollama_json(prompt: str) -> dict:
    import ollama

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_json(response["message"]["content"])


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"has_food": False}
