from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.product_analysis.router import router as product_router

tags_metadata = [
    {
        "name": "Ürün ve İçerik Analizi (Barkod Modülü)",
        "description": (
            "Barkod okuyucudan gelen numarayı alarak Open Food Facts üzerinden "
            "içerik, alerjen, besin tablosu ve sağlık puanlarını (Nutri-Score, NOVA vb.) analiz eden modül."
        ),
    },
    {
        "name": "Sistem / Sağlık Kontrolü",
        "description": "API sunucusunun çalışma durumunu ve versiyonunu kontrol eden uç noktalar.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware (Mobil uygulama ve web arayüzleri için tam erişim)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modüllerin Router'larını Bağla
app.include_router(product_router, prefix="/api/v1")


@app.get(
    "/health",
    tags=["Sistem / Sağlık Kontrolü"],
    summary="API Sağlık Kontrolü",
)
def health_check():
    """Backend sunucusunun aktif ve erişilebilir olup olmadığını doğrular."""
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "module": "Ürün ve İçerik Analizi (Barkod)",
    }


@app.head("/health", include_in_schema=False)
def health_check_head():
    """HEAD istekleri için sağlık kontrolü (Render ve izleme servisleri için)."""
    return health_check()


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def root():
    return {
        "message": f"{settings.APP_NAME} çalışıyor. Dokümantasyon için /docs adresini ziyaret edin.",
        "docs": "/docs",
    }
