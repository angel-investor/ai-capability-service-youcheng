"""text_summary capability：调用 DeepSeek API 对长文本进行摘要"""

from __future__ import annotations

from typing import Any

import httpx

from app.capabilities.base import BaseCapability
from app.config import settings
from app.exceptions import InvalidInputError, ModelAPIError
from app.logger import get_logger

logger = get_logger(__name__)


class TextSummaryCapability(BaseCapability):
    """
    将输入文本摘要为不超过 max_length 字的简短内容。

    输入字段：
        text (str, 必填): 需要摘要的原始文本
        max_length (int, 可选, 默认 120): 摘要最大字数
    """

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        text = input_data.get("text")
        if not text or not isinstance(text, str) or not text.strip():
            raise InvalidInputError("Field 'text' is required and must be a non-empty string.")

        max_length: int = input_data.get("max_length", 120)
        if not isinstance(max_length, int) or max_length <= 0:
            raise InvalidInputError("Field 'max_length' must be a positive integer.")

        system_prompt = (
            "You are a professional text summarization assistant. "
            "Summarize the given text concisely and accurately."
        )
        user_prompt = (
            f"Please summarize the following text in no more than {max_length} characters. "
            f"Return only the summary, without any preamble.\n\nText:\n{text}"
        )

        result = await self._call_deepseek(system_prompt, user_prompt)
        logger.info("text_summary completed, result_length=%d", len(result))
        return {"result": result}

    @staticmethod
    async def _call_deepseek(system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.deepseek_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 512,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.deepseek_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

            if response.status_code != 200:
                raise ModelAPIError(
                    message=f"DeepSeek API returned HTTP {response.status_code}.",
                    details={"status_code": response.status_code, "body": response.text[:500]},
                )

            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        except ModelAPIError:
            raise
        except httpx.TimeoutException:
            raise ModelAPIError("Request to DeepSeek API timed out.")
        except Exception as e:
            raise ModelAPIError(f"Failed to call DeepSeek API: {e}")
