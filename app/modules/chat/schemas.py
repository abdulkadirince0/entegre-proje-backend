from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AIExecutionMetrics(BaseModel):
    """Her AI çağrısında toplanan performans ve telemetri metrikleri."""
    provider: str = Field(..., description="Kullanılan AI sağlayıcısı (gemini, groq, openrouter)")
    model: str = Field(..., description="Kullanılan model adı")
    input_tokens: Optional[int] = Field(None, description="Giriş token sayısı")
    output_tokens: Optional[int] = Field(None, description="Çıkış token sayısı")
    total_tokens: Optional[int] = Field(None, description="Toplam token")
    latency_ms: float = Field(..., description="İstek tamamlanma süresi (milisaniye)")
    status: str = Field(..., description="Sonuç durumu: success veya failed")
    error_type: Optional[str] = Field(None, description="Hata türü (quota_exceeded, timeout, auth_error vb.)")
    attempts_count: int = Field(1, description="Başarılı olana kadar yapılan toplam deneme / rotasyon sayısı")


class ChatMessageRequest(BaseModel):
    """Kullanıcıdan gelen mesaj ve sohbet geçmişi özeti."""
    message: str = Field(
        ...,
        examples=["Satın aldığım telefon 3 gün sonra arızalandı, satıcı iade almıyor. Haklarım neler?"],
        description="Kullanıcının gönderdiği son soru veya mesaj"
    )
    summary: Optional[str] = Field(
        "",
        examples=["Kullanıcı 15 Kasım'da faturalı bir telefon almış, 3. gün ekran açılmamış."],
        description="Önceki sohbet geçmişinin özeti (hafıza). İlk mesajda boş olabilir."
    )
    image_base64: Optional[str] = Field(
        None,
        description="Görsel analiz için base64 formatında resim (fatura, arızalı ürün fotoğrafı vb.)"
    )
    image_url: Optional[str] = Field(
        None,
        description="Alternatif olarak görselin internet URL'si"
    )
    chat_id: Optional[str] = Field(
        None,
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
        description="Supabase chats tablosundaki sohbet ID'si (opsiyonel)"
    )


class ChatMessageResponse(BaseModel):
    """Hakkım Var asistanının kullanıcıya yanıtı ve güncellenmiş hafıza."""
    success: bool = Field(True, description="İşlem başarılı mı?")
    response: str = Field(..., description="Kullanıcıya gösterilecek asistan yanıtı")
    summary: str = Field(..., description="Güncellenmiş sohbet özeti (Bir sonraki istekte hafıza olarak gönderilecek)")
    metrics: AIExecutionMetrics = Field(..., description="İstek telemetri ve token metrikleri")
    chat_id: Optional[str] = Field(None, description="İlgili sohbet ID")


class ProviderStatus(BaseModel):
    """Aktif AI sağlayıcılarının durumu ve anahtar havuzları."""
    provider: str
    total_keys: int
    active_key_index: int
    available_models: List[str]
    is_available: bool


class ProviderPoolStatusResponse(BaseModel):
    """Tüm AI sağlayıcı havuzunun anlık durum raporu."""
    active_provider: str
    providers: List[ProviderStatus]
