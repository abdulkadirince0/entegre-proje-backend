import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Proje ana dizinini sys.path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app, health_check
from app.modules.product_analysis.router import analyze_product, get_product_by_barcode_legacy
from app.modules.product_analysis.schemas import BarcodeAnalysisRequest
from app.modules.product_analysis.service import ProductAnalysisService

SAMPLE_JSON_PATH = Path(__file__).resolve().parent / "sample_product.json"


def load_sample_product_data():
    with open(SAMPLE_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_health_check():
    """Sağlık kontrolü fonksiyonunun doğruluğunu test et."""
    result = health_check()
    assert result["status"] == "online"
    assert "version" in result
    print("✓ test_health_check başarılı.")


def test_openapi_schema():
    """FastAPI OpenAPI/Swagger şemasının eksiksiz oluşturulduğunu test et."""
    schema = app.openapi()
    assert schema["info"]["title"] is not None
    assert "/api/v1/products/analyze" in schema["paths"]
    assert "ProductAnalysisResponse" in schema["components"]["schemas"]
    assert "ProductDetail" in schema["components"]["schemas"]
    print("✓ test_openapi_schema başarılı.")


def test_clean_and_normalize():
    """Open Food Facts ham verisinin ayıklanmasını test et."""
    raw = load_sample_product_data()
    detail = ProductAnalysisService.clean_and_normalize(raw)
    assert detail is not None
    assert detail.barcode == "8690504135913"
    assert detail.product_name == "ülker çikolata"
    assert detail.brand == "Ülker"
    assert detail.quantity == "36 g"

    # Besin değerleri
    assert detail.nutrition.energy_kcal_100g == 543.0
    assert detail.nutrition.fat_100g == 31.0
    assert detail.nutrition.sugars_100g == 38.0
    assert detail.nutrition.levels.sugars.label_tr == "Yüksek"
    assert detail.nutrition.levels.sugars.color == "red"

    # İçerik ve Alerjenler
    assert detail.ingredients.has_palm_oil is True
    assert "Gluten" in detail.safety_alerts.allergens
    assert "Süt / Laktoz" in detail.safety_alerts.allergens
    assert "Fındık ve Fıstık" in detail.safety_alerts.traces

    # Görseller
    assert detail.images.front_url is not None
    assert detail.images.ingredients_url is not None
    assert detail.images.nutrition_url is not None

    # Sağlık Skorları
    assert detail.health_scores.nutriscore_grade == "E"
    assert "Çok düşük besin kalitesi" in detail.health_scores.nutriscore_description
    assert detail.health_scores.ecoscore_grade == "B"
    assert detail.health_scores.nutriscore_breakdown is not None
    assert detail.health_scores.nutriscore_breakdown.score == 28
    assert detail.health_scores.ecoscore_score == 64

    # Zenginleştirilmiş İçerikler ve Ek Bilgiler
    assert len(detail.ingredients.structured) > 0
    assert detail.ingredients.structured[0].text == "Şeker"
    assert detail.ingredients.structured[0].percent_estimate == 38.0
    assert detail.nutrition.added_sugars_100g == 38.0

    # Ham veri dahil etme testi
    detail_raw = ProductAnalysisService.clean_and_normalize(raw, include_raw=True)
    assert detail_raw.raw_openfoodfacts is not None
    assert len(detail_raw.raw_openfoodfacts.keys()) > 100
    print("✓ test_clean_and_normalize başarılı (Tüm zenginleştirilmiş alanlar doğrulandı).")


async def test_get_product_endpoint():
    """GET /api/v1/products/{barcode} (legacy/browser) endpoint'ini test et."""
    raw = load_sample_product_data()
    mock_detail = ProductAnalysisService.clean_and_normalize(raw)

    with patch(
        "app.modules.product_analysis.router.ProductAnalysisService.fetch_product_by_barcode",
        new_callable=AsyncMock,
        return_value=mock_detail,
    ):
        res = await get_product_by_barcode_legacy("8690504135913")
        assert res.success is True
        assert res.barcode == "8690504135913"
        assert res.data.product_name == "ülker çikolata"
        assert res.data.brand == "Ülker"
        assert res.data.nutrition.sugars_100g == 38.0
    print("✓ test_get_product_endpoint başarılı.")


async def test_post_analyze_endpoint():
    """POST /api/v1/products/analyze endpoint'inin mock yanıtını test et."""
    raw = load_sample_product_data()
    mock_detail = ProductAnalysisService.clean_and_normalize(raw)

    with patch(
        "app.modules.product_analysis.router.ProductAnalysisService.fetch_product_by_barcode",
        new_callable=AsyncMock,
        return_value=mock_detail,
    ):
        req = BarcodeAnalysisRequest(barcode="8690504135913")
        res = await analyze_product(req)
        assert res.success is True
        assert res.barcode == "8690504135913"
        assert res.data.barcode == "8690504135913"
    print("✓ test_post_analyze_endpoint başarılı.")


async def test_product_not_found():
    """Ürün bulunamadığında HTTP 404 dönmeli ve success=False olmalı."""
    with patch(
        "app.modules.product_analysis.router.ProductAnalysisService.fetch_product_by_barcode",
        new_callable=AsyncMock,
        return_value=None,
    ):
        req = BarcodeAnalysisRequest(barcode="0000000000000")
        res = await analyze_product(req)
        assert res.status_code == 404
        body = json.loads(res.body.decode("utf-8"))
        assert body["success"] is False
        assert body["data"] is None
        assert "bulunamadı" in body["message"].lower()
    print("✓ test_product_not_found başarılı (HTTP 404 + success=False doğrulandı).")


async def run_all_tests():
    print("=" * 50)
    print("EN-TEGRE PROJE - BARKOD VE ÜRÜN ANALİZİ TESTLERİ")
    print("=" * 50)
    test_health_check()
    test_openapi_schema()
    test_clean_and_normalize()
    await test_get_product_endpoint()
    await test_post_analyze_endpoint()
    await test_product_not_found()
    print("=" * 50)
    print("🎉 TÜM 6 TEST BAŞARIYLA TAMAMLANDI!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
