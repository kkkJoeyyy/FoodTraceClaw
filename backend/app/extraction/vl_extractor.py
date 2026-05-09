import base64
import json
from app.config import LLM_PROVIDER, OPENAI_API_KEY, OPENAI_BASE_URL, VL_MODEL, OLLAMA_HOST, OLLAMA_MODEL


VL_PROMPT = """从这张图片中提取美食店铺和菜品信息，返回 JSON：

- store.name: 店铺/餐厅名称
- store.location: 城市+区域
- store.address: 详细地址（如有）
- store.description: 店铺描述
- store.category: 分类
- dishes: 菜品数组 [{name, description}]

如果图片中没有可识别的美食信息，返回 {"has_food": false}

只返回 JSON，不要任何其他文字。"""


async def extract_from_image(image_base64: str) -> dict:
    if LLM_PROVIDER == "ollama":
        return await _extract_ollama_vl(image_base64)
    return await _extract_openai_vl(image_base64)


async def _extract_openai_vl(image_base64: str) -> dict:
    from openai import AsyncOpenAI

    # Strip data URI prefix if present
    img_data = image_base64
    if image_base64.startswith("data:"):
        img_data = image_base64.split(",", 1)[-1]

    client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    response = await client.chat.completions.create(
        model=VL_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": VL_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}},
            ],
        }],
        temperature=0.1,
    )
    return _parse_json(response.choices[0].message.content or "")


async def _extract_ollama_vl(image_base64: str) -> dict:
    import ollama

    img_data = image_base64
    if image_base64.startswith("data:"):
        img_data = image_base64.split(",", 1)[-1]

    image_bytes = base64.b64decode(img_data)

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{
            "role": "user",
            "content": VL_PROMPT,
            "images": [image_bytes],
        }],
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
