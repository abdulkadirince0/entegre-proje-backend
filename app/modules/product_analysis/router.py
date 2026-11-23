from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
import httpx

from app.modules.product_analysis.schemas import (
    ProductAnalysisResponse,
    BarcodeAnalysisRequest,
)
from app.modules.product_analysis.service import ProductAnalysisService

router = APIRouter(
    prefix="/products",
    tags=["Ürün ve İçerik Analizi (Barkod Modülü)"],
)


@router.post(
    "/analyze",
    response_model=ProductAnalysisResponse,
    summary="Barkod Göndererek Ürün Analizi (POST)",
    description=(
        "Kamera veya barkod okuyucudan okutulan barkod numarasını alır. "
        "Open Food Facts servisinden ürünü sorgulayarak içindekiler, besin değerleri, "
        "sağlık puanları (Nutri-Score, NOVA), alerjenler ve yüksek çözünürlüklü görselleri temiz veri olarak döner."
    ),
    responses={
        200: {
            "description": "Ürün başarıyla bulundu ve analiz edildi.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Ürün bilgileri başarıyla getirildi ve analiz edildi.",
                        "barcode": "8690504135913",
                        "data": {
                            "barcode": "8690504135913",
                            "product_name": "Ülker Çikolatalı Gofret",
                            "brand": "Ülker",
                            "quantity": "36 g",
                            "images": {
                                "front_url": "https://images.openfoodfacts.org/.../front_tr.81.400.jpg",
                                "ingredients_url": "https://images.openfoodfacts.org/.../ingredients_tr.58.400.jpg",
                                "nutrition_url": "https://images.openfoodfacts.org/.../nutrition_tr.11.400.jpg"
                            },
                            "health_scores": {
                                "nutriscore_grade": "E",
                                "nutriscore_description": "Çok düşük besin kalitesi"
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Verilen barkod ile eşleşen bir ürün bulunamadı.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Bu barkoda ait ürün bulunamadı.",
                        "barcode": "0000000000000",
                        "data": None
                    }
                }
            }
        },
        502: {
            "description": "Dış servis (Open Food Facts) ile iletişim kurulamadı.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Open Food Facts servisine ulaşılamadı.",
                        "barcode": "8690504135913",
                        "data": None
                    }
                }
            }
        },
    },
)
async def analyze_product(request: BarcodeAnalysisRequest):
    barcode = request.barcode.strip()
    if not barcode:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "Barkod numarası boş bırakılamaz.",
                "barcode": "",
                "data": None,
            },
        )

    try:
        product_detail = await ProductAnalysisService.fetch_product_by_barcode(barcode)
    except httpx.RequestError as exc:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "success": False,
                "message": f"Open Food Facts servisine ulaşılamadı: {str(exc)}",
                "barcode": barcode,
                "data": None,
            },
        )
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Ürün analiz edilirken bir hata oluştu: {str(exc)}",
                "barcode": barcode,
                "data": None,
            },
        )

    # Ürün bulunamadıysa HTTP 404 döner ve success: false olur!
    if not product_detail:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": "Bu barkoda ait ürün bulunamadı.",
                "barcode": barcode,
                "data": None,
            },
        )

    return ProductAnalysisResponse(
        success=True,
        message="Ürün bilgileri başarıyla getirildi ve analiz edildi.",
        barcode=barcode,
        data=product_detail,
    )


# Tarayıcıdan hızlı URL testi yapmak isteyenler için GET desteği (Swagger dokümanında kalabalık yapmaz)
@router.get(
    "/{barcode}",
    response_model=ProductAnalysisResponse,
    include_in_schema=False,
)
async def get_product_by_barcode_legacy(barcode: str):
    return await analyze_product(BarcodeAnalysisRequest(barcode=barcode))
