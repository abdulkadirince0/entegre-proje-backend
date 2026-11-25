import json
import re
from typing import Optional, Dict, Any
from pydantic import BaseModel


class QuotaExceededError(Exception):
    """API kota aşımı veya rate limit (HTTP 429) durumunda fırlatılır."""
    def __init__(self, message: str, provider: str, model: str, status_code: int = 429):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.status_code = status_code


class ProviderAPIError(Exception):
    """Sağlayıcıdan dönen diğer genel API hataları."""
    def __init__(self, message: str, provider: str, model: str, status_code: int = 500):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.status_code = status_code


class ProviderResult(BaseModel):
    """Sağlayıcı çağrısından dönen normalize edilmiş sonuç."""
    response_text: str
    summary_text: str
    provider: str
    model: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: float = 0.0


def extract_and_parse_json(text: str, default_summary: str = "") -> Dict[str, str]:
    """Modelden dönen metni akıllıca JSON olarak ayrıştırır; markdown bloklarını temizler."""
    if not text:
        return {"response": "", "summary": default_summary}

    cleaned = text.strip()
    # Markdown kod bloklarını temizle (```json ... ``` veya ``` ... ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    # 1. Doğrudan JSON ayrıştırma dene
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return {
                "response": str(data.get("response", "")).strip(),
                "summary": str(data.get("summary", default_summary)).strip()
            }
    except Exception:
        pass

    # 2. Metin içinde ilk { ... } bloğunu regex ile bul
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return {
                    "response": str(data.get("response", "")).strip(),
                    "summary": str(data.get("summary", default_summary)).strip()
                }
        except Exception:
            pass

    # 3. Model JSON formatına uymadıysa düz metni cevap olarak kabul et, özeti koru
    return {
        "response": cleaned,
        "summary": default_summary
    }
