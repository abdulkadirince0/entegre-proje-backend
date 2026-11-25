from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.modules.chat.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ProviderPoolStatusResponse,
)
from app.modules.chat.service import ChatService

router = APIRouter(
    prefix="/chat",
    tags=["Hakkım Var (Tüketici Hakları AI Asistanı)"],
)


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    summary="Hakkım Var Asistanına Mesaj Gönder (POST)",
    description=(
        "Kullanıcının yazdığı soruyu (`message`) ve varsa önceki sohbet özetini (`summary`) alır. "
        "Yönetmen (Director) mekanizması ile sırasıyla **Gemini -> Groq -> OpenRouter** sağlayıcılarını "
        "ve tanımlı anahtar havuzlarını dener. Kota aşımı durumunda otomatik olarak sonraki anahtara ve modele geçer. "
        "Yanıtta asistanın hukuki rehberliği, güncellenmiş hafıza özeti (`summary`) ve kullanılan model/token telemetrisi döner."
    ),
    responses={
        200: {
            "description": "Asistan başarıyla yanıt üretti ve özet güncellendi.",
        },
        500: {
            "description": "Tüm AI sağlayıcı havuzları tükendi veya genel bir hata oluştu.",
        },
    },
)
async def send_chat_message(request: ChatMessageRequest):
    try:
        response = await ChatService.handle_message(request)
        return response
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "response": "Şu anda tüm yapay zeka sağlayıcılarımızın kotası dolu veya geçici bir kesinti yaşanıyor. Lütfen az sonra tekrar deneyiniz.",
                "summary": request.summary or "",
                "chat_id": request.chat_id,
                "metrics": {
                    "provider": "none",
                    "model": "none",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "latency_ms": 0.0,
                    "status": "failed",
                    "error_type": str(exc),
                    "attempts_count": 0,
                },
            },
        )


@router.get(
    "/providers",
    response_model=ProviderPoolStatusResponse,
    summary="AI Sağlayıcı ve Anahtar Havuzu Durumu (GET)",
    description="Sistemde kayıtlı Gemini, Groq ve OpenRouter sağlayıcılarının, anahtar havuzu büyüklüklerinin ve aktif öncelik durumunun özetini döner.",
)
def get_providers_status():
    return ChatService.get_providers_status()
