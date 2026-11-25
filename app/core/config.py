import os
from typing import List
from pydantic import BaseModel, Field


def _parse_keys(env_name: str, fallback_single: str = "") -> List[str]:
    """Virgülle ayrılmış veya tekil çevre değişkenlerinden anahtar listesini döner."""
    raw = os.getenv(env_name, "")
    if not raw and fallback_single:
        raw = os.getenv(fallback_single, "")
    if not raw:
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]


class Settings(BaseModel):
    APP_NAME: str = "Tüketici Hakları ve Entegre Analiz API"
    APP_VERSION: str = "1.1.0"
    APP_DESCRIPTION: str = (
        "Tüketici Hakları & Ürün Analiz Sistemi Backend Servisi. "
        "Barkod tarama, ürün içeriği, besin tablosu ve yapay zeka destekli "
        "'Hakkım Var' tüketici danışmanlık sohbet modülünü sunar."
    )
    
    # Open Food Facts Ayarları
    OPENFOODFACTS_BASE_URL: str = "https://world.openfoodfacts.org/api/v2/product"
    OPENFOODFACTS_USER_AGENT: str = "EntegreProje - Android/iOS/Web Backend - Version 1.1"
    REQUEST_TIMEOUT_SECONDS: float = 15.0
    
    # CORS Ayarları (Mobil ve Web testleri için)
    ALLOWED_ORIGINS: List[str] = ["*"]

    # AI Sağlayıcı API Anahtarları (Virgülle birden fazla key verilebilir)
    GEMINI_API_KEYS: List[str] = Field(default_factory=lambda: _parse_keys("GEMINI_API_KEYS", "GEMINI_API_KEY"))
    GROQ_API_KEYS: List[str] = Field(default_factory=lambda: _parse_keys("GROQ_API_KEYS", "GROQ_API_KEY"))
    OPENROUTER_API_KEYS: List[str] = Field(default_factory=lambda: _parse_keys("OPENROUTER_API_KEYS", "OPENROUTER_API_KEY"))

    # Tercih Edilen Model Havuzları (Öncelik Sırasıyla)
    GEMINI_MODELS: List[str] = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    GROQ_MODELS: List[str] = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    OPENROUTER_MODELS: List[str] = ["google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.3-70b-instruct:free"]

    # Supabase (Opsiyonel backend doğrudan veritabanı bağlantısı)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")


settings = Settings()
