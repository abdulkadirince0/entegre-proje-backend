import time
import httpx
from typing import Optional, Dict, Any

from app.modules.chat.prompts import HAKKIM_VAR_SYSTEM_PROMPT
from app.modules.chat.providers.base import (
    ProviderResult,
    QuotaExceededError,
    ProviderAPIError,
    extract_and_parse_json,
)


class GroqProvider:
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    @classmethod
    async def generate(
        cls,
        api_key: str,
        model: str,
        message: str,
        summary: str = "",
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        timeout_seconds: float = 20.0,
    ) -> ProviderResult:
        start_time = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        user_content = f"summary: {summary or ''}\nmessage: {message}"
        if image_url:
            user_content = f"[Ekli Görsel URL: {image_url}]\n" + user_content
        elif image_base64:
            user_content = "[Kullanıcı bir ürün/kanıt fotoğrafı ekledi]\n" + user_content

        messages = [
            {"role": "system", "content": HAKKIM_VAR_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        payload = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
        }

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            try:
                response = await client.post(cls.BASE_URL, json=payload, headers=headers)
            except httpx.TimeoutException as exc:
                raise ProviderAPIError(f"Groq zaman aşımı: {str(exc)}", provider="groq", model=model, status_code=504)
            except httpx.RequestError as exc:
                raise ProviderAPIError(f"Groq bağlantı hatası: {str(exc)}", provider="groq", model=model, status_code=502)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if response.status_code == 429:
            raise QuotaExceededError("Groq kotası aşıldı (HTTP 429 rate limit)", provider="groq", model=model, status_code=429)

        if response.status_code != 200:
            err_text = response.text
            if "rate_limit_exceeded" in err_text or "quota" in err_text.lower():
                raise QuotaExceededError(f"Groq kotası doldu: {err_text}", provider="groq", model=model, status_code=429)
            raise ProviderAPIError(f"Groq API hatası ({response.status_code}): {err_text}", provider="groq", model=model, status_code=response.status_code)

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise ProviderAPIError("Groq boş yanıt döndürdü", provider="groq", model=model)

        raw_text = choices[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens")
        output_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")

        parsed = extract_and_parse_json(raw_text, default_summary=summary)

        return ProviderResult(
            response_text=parsed["response"],
            summary_text=parsed["summary"],
            provider="groq",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
        )
