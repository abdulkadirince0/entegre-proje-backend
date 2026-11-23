from fastapi import APIRouter, Path, HTTPException, status
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


@router.get(
    "/{barcode}",
    response_model=ProductAnalysisResponse,
    summary="Barkod Numarası ile Ürün Analizi (GET)",
    description=(
        "Kullanıcının kamera veya barkod okuyucuyla okuttuğu barkod numarasını (örn: 8690504135913) alır. "
        "Open Food Facts servisinden ürünü çeker; gereksiz ve karmaşık verileri ayıklayarak "
        "içindekiler, besin değerleri, alerjenler, sağlık puanları (Nutri-Score, NOVA, Eco-Score) "
        "ve yüksek çözünürlüklü görselleri temiz bir şemada döner."
    ),
    responses={
        200: {
            "description": "Ürün başarıyla bulundu ve analiz edildi.",
        },
        404: {
            "description": "Verilen barkod ile eşleşen bir ürün bulunamadı.",
            "model": ProductAnalysisResponse,
        },
        502: {
            "description": "Dış servis (Open Food Facts) ile iletişim kurulamadı.",
        },
    },
)
async def get_product_by_barcode(
    barcode: str = Path(
        ...,
        description="Okutulan barkod numarası (EAN-13, EAN-8 vb.)",
        examples=["8690504135913"],
        min_length=4,
        max_length=20,
    )
):
    try:
        product_detail = await ProductAnalysisService.fetch_product_by_barcode(barcode)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Open Food Facts servisine ulaşılamadı: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ürün analiz edilirken bir hata oluştu: {str(exc)}",
        )

    if not product_detail:
        return ProductAnalysisResponse(
            success=False,
            message="Bu barkoda ait ürün bulunamadı.",
            barcode=barcode,
            data=None,
        )

    return ProductAnalysisResponse(
        success=True,
        message="Ürün bilgileri başarıyla getirildi ve analiz edildi.",
        barcode=barcode,
        data=product_detail,
    )


@router.post(
    "/analyze",
    response_model=ProductAnalysisResponse,
    summary="Barkod Göndererek Ürün Analizi (POST)",
    description=(
        "JSON gövdesinde `barcode` göndererek ürün analizi yapar. "
        "Mobil veya frontend tarafında POST isteği atmak istenirse alternatif olarak kullanılır."
    ),
)
async def analyze_product(request: BarcodeAnalysisRequest):
    return await get_product_by_barcode(barcode=request.barcode)
