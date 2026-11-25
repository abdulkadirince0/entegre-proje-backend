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


class GeminiProvider:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

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
        endpoint = f"{cls.BASE_URL}/{model}:generateContent?key={api_key}"

        # Parçaları hazırla
        parts = []

        # Görsel varsa ekle
        if image_base64:
            # Data URI prefix varsa temizle
            b64_clean = image_base64
            mime = "image/jpeg"
            if "," in b64_clean:
                header, b64_clean = b64_clean.split(",", 1)
                if "png" in header:
                    mime = "image/png"
                elif "webp" in header:
                    mime = "image/webp"

            parts.append({
                "inline_data": {
                    "mime_type": mime,
                    "data": b64_clean
                }
            })
        elif image_url:
            parts.append({
                "text": f"[Ekli Görsel URL]: {image_url}"
            })

        user_content_text = f"summary: {summary or ''}\nmessage: {message}"
        parts.append({"text": user_content_text})

        payload = {
            "system_instruction": {
                "parts": [{"text": HAKKIM_VAR_SYSTEM_PROMPT}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": parts
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.3
            }
        }

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            try:
                response = await client.post(endpoint, json=payload)
            except httpx.TimeoutException as exc:
                raise ProviderAPIError(f"Gemini zaman aşımı: {str(exc)}", provider="gemini", model=model, status_code=504)
            except httpx.RequestError as exc:
                raise ProviderAPIError(f"Gemini bağlantı hatası: {str(exc)}", provider="gemini", model=model, status_code=502)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Kota hatası kontrolü (HTTP 429 veya RESOURCE_EXHAUSTED)
        if response.status_code == 429:
            raise QuotaExceededError("Gemini kotası aşıldı (HTTP 429)", provider="gemini", model=model, status_code=429)

        if response.status_code != 200:
            err_text = response.text
            if "RESOURCE_EXHAUSTED" in err_text or "Quota exceeded" in err_text:
                raise QuotaExceededError(f"Gemini kotası doldu: {err_text}", provider="gemini", model=model, status_code=429)
            raise ProviderAPIError(f"Gemini API hatası ({response.status_code}): {err_text}", provider="gemini", model=model, status_code=response.status_code)

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ProviderAPIError("Gemini boş yanıt döndürdü", provider="gemini", model=model)

        raw_text = ""
        candidate_parts = candidates[0].get("content", {}).get("parts", [])
        for p in candidate_parts:
            raw_text += p.get("text", "")

        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount")
        output_tokens = usage.get("candidatesTokenCount")
        total_tokens = usage.get("totalTokenCount")

        parsed = extract_and_parse_json(raw_text, default_summary=summary)

        return ProviderResult(
            response_text=parsed["response"],
            summary_text=parsed["summary"],
            provider="gemini",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
        )
