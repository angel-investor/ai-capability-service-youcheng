"""sentiment_analysis capability：调用 DeepSeek API 对文本进行情感分析（加分项）"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.capabilities.base import BaseCapability
from app.config import settings
from app.exceptions import InvalidInputError, ModelAPIError
from app.logger import get_logger

logger = get_logger(__name__)


class SentimentAnalysisCapability(BaseCapability):
    """
    对输入文本进行情感分析，返回情感标签和置信度。

    输入字段：
        text (str, 必填): 需要分析的文本

    输出字段：
        sentiment (str): positive / negative / neutral
        confidence (float): 置信度 0.0 ~ 1.0
        reason (str): 简要分析理由
    """

    SYSTEM_PROMPT = (
        "You are a sentiment analysis assistant. "
        "Analyze the sentiment of the given text and respond ONLY with a JSON object "
        "in the following format (no markdown, no extra text):\n"
        '{"sentiment": "positive"|"negative"|"neutral", "confidence": 0.0-1.0, "reason": "brief explanation"}'
    )

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        text = input_data.get("text")
        if not text or not isinstance(text, str) or not text.strip():
            raise InvalidInputError("Field 'text' is required and must be a non-empty string.")

        user_prompt = f"Analyze the sentiment of the following text:\n\n{text}"
        raw = await self._call_deepseek(self.SYSTEM_PROMPT, user_prompt)

        try:
            # 兼容模型可能包裹 markdown 代码块的情况
            json_str = re.sub(r"```(?:json)?|```", "", raw).strip()
            parsed = json.loads(json_str)
            sentiment = parsed.get("sentiment", "neutral")
            confidence = float(parsed.get("confidence", 0.5))
            reason = parsed.get("reason", "")
        except Exception:
            logger.warning("Failed to parse DeepSeek response as JSON, raw=%s", raw[:200])
            raise ModelAPIError("Unexpected response format from model API.")

        if sentiment not in ("positive", "negative", "neutral"):
            sentiment = "neutral"

        confidence = max(0.0, min(1.0, confidence))

        logger.info("sentiment_analysis completed, sentiment=%s, confidence=%.2f", sentiment, confidence)
        return {
            "result": {
                "sentiment": sentiment,
                "confidence": confidence,
                "reason": reason,
            }
        }

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
            "temperature": 0.1,
            "max_tokens": 256,
            "response_format": {"type": "json_object"},
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
