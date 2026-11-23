import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "Tüketici Hakları ve Entegre Analiz API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Tüketici Hakları & Ürün Analiz Sistemi Backend Servisi. "
        "Mobil ve web arayüzleri için barkod tarama, ürün içeriği, besin değerleri, "
        "alerjen ve sağlık analizleri sunar."
    )
    
    # Open Food Facts Ayarları
    OPENFOODFACTS_BASE_URL: str = "https://world.openfoodfacts.org/api/v2/product"
    OPENFOODFACTS_USER_AGENT: str = "EntegreProje - Android/iOS/Web Backend - Version 1.0"
    REQUEST_TIMEOUT_SECONDS: float = 12.0
    
    # CORS Ayarları (Mobil ve Web testleri için)
    ALLOWED_ORIGINS: list[str] = ["*"]

settings = Settings()
