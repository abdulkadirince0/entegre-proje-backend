import logging
from typing import Optional

from app.modules.chat.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ProviderPoolStatusResponse,
)
from app.modules.chat.providers.director import director

logger = logging.getLogger("chat_service")


class ChatService:
    @classmethod
    async def handle_message(cls, request: ChatMessageRequest) -> ChatMessageResponse:
        """Kullanıcı mesajını alır, çoklu sağlayıcı rotasyonundan geçirir ve yanıt üretir."""
        message = request.message.strip()
        summary = (request.summary or "").strip()

        result, metrics = await director.execute_chat(
            message=message,
            summary=summary,
            image_base64=request.image_base64,
            image_url=request.image_url,
        )

        return ChatMessageResponse(
            success=True,
            response=result.response_text,
            summary=result.summary_text,
            metrics=metrics,
            chat_id=request.chat_id,
        )

    @classmethod
    def get_providers_status(cls) -> ProviderPoolStatusResponse:
        """Aktif sağlayıcı havuzlarının durumunu döner."""
        director.reload_keys_from_settings()
        statuses = director.get_provider_status()
        
        active_p = "none"
        for s in statuses:
            if s.is_available:
                active_p = s.provider
                break

        return ProviderPoolStatusResponse(
            active_provider=active_p,
            providers=statuses,
        )
