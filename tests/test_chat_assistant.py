import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Proje ana dizinini sys.path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.modules.chat.prompts import HAKKIM_VAR_SYSTEM_PROMPT
from app.modules.chat.schemas import ChatMessageRequest
from app.modules.chat.router import send_chat_message, get_providers_status
from app.modules.chat.providers.base import (
    extract_and_parse_json,
    QuotaExceededError,
    ProviderResult,
)
from app.modules.chat.providers.director import AIDirector


def test_system_prompt():
    """Hakkım Var sistem promptunun kuralları içerdiğini doğrula."""
    assert "Hakkım Var" in HAKKIM_VAR_SYSTEM_PROMPT
    assert "SUMMARY RULES" in HAKKIM_VAR_SYSTEM_PROMPT
    assert "Always return valid JSON" in HAKKIM_VAR_SYSTEM_PROMPT
    print("✓ test_system_prompt başarılı.")


def test_json_extractor():
    """Modelden dönen farklı metin/JSON formatlarının doğru ayrıştırıldığını test et."""
    # 1. Temiz JSON
    raw1 = '{"response": "Tüketici Kanunu m.11 kapsamındadır.", "summary": "Ayıplı mal bildirildi."}'
    p1 = extract_and_parse_json(raw1)
    assert p1["response"] == "Tüketici Kanunu m.11 kapsamındadır."
    assert p1["summary"] == "Ayıplı mal bildirildi."

    # 2. Markdown bloklu JSON (```json ... ```)
    raw2 = '```json\n{"response": "İade hakkınız var.", "summary": "İade talep edildi."}\n```'
    p2 = extract_and_parse_json(raw2)
    assert p2["response"] == "İade hakkınız var."
    assert p2["summary"] == "İade talep edildi."

    # 3. Metin içinde JSON
    raw3 = 'İşte yanıtım:\n{"response": "THH başvurusu yapabilirsiniz.", "summary": "THH bilgisi verildi."}\nİyi günler.'
    p3 = extract_and_parse_json(raw3)
    assert p3["response"] == "THH başvurusu yapabilirsiniz."
    assert p3["summary"] == "THH bilgisi verildi."

    # 4. JSON olmayan düz metin
    raw4 = "Sadece düz metin cevap"
    p4 = extract_and_parse_json(raw4, default_summary="Eski özet")
    assert p4["response"] == "Sadece düz metin cevap"
    assert p4["summary"] == "Eski özet"
    print("✓ test_json_extractor başarılı.")


async def test_director_key_rotation():
    """Gemini'de ilk key kota hatası (429) verdiğinde ikinci key'e geçildiğini test et."""
    director = AIDirector()
    director.key_pools["gemini"] = ["gemini_key_1", "gemini_key_2"]
    director.active_indices["gemini"] = 0

    call_count = 0

    async def mock_gemini_generate(api_key, model, **kwargs):
        nonlocal call_count
        call_count += 1
        if api_key == "gemini_key_1":
            raise QuotaExceededError("Key 1 kotası doldu", provider="gemini", model=model)
        return ProviderResult(
            response_text="Key 2 ile başarıyla yanıt üretildi.",
            summary_text="Özet güncellendi.",
            provider="gemini",
            model=model,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        )

    with patch("app.modules.chat.providers.director.GeminiProvider.generate", side_effect=mock_gemini_generate):
        result, metrics = await director.execute_chat(message="Telefonum bozuldu")
        assert result.response_text == "Key 2 ile başarıyla yanıt üretildi."
        assert metrics.provider == "gemini"
        assert metrics.attempts_count == 2
        assert director.active_indices["gemini"] == 1
    print("✓ test_director_key_rotation başarılı (Kota aşılınca 2. key'e başarıyla geçildi).")


async def test_director_provider_fallback():
    """Tüm Gemini keyleri tükendiğinde Groq sağlayıcısına geçildiğini test et."""
    director = AIDirector()
    director.key_pools["gemini"] = ["gemini_exhausted_key"]
    director.key_pools["groq"] = ["groq_working_key"]

    async def mock_gemini_fail(**kwargs):
        raise QuotaExceededError("Tüm Gemini modelleri ve keyleri tükendi", provider="gemini", model="gemini-flash")

    async def mock_groq_success(api_key, model, **kwargs):
        return ProviderResult(
            response_text="Groq sağlayıcısı devreye girdi ve cevap verdi.",
            summary_text="Groq özeti.",
            provider="groq",
            model=model,
            input_tokens=80,
            output_tokens=40,
            total_tokens=120,
        )

    with patch("app.modules.chat.providers.director.GeminiProvider.generate", side_effect=mock_gemini_fail):
        with patch("app.modules.chat.providers.director.GroqProvider.generate", side_effect=mock_groq_success):
            result, metrics = await director.execute_chat(message="Sözleşmeden dönebilir miyim?")
            assert result.provider == "groq"
            assert result.response_text == "Groq sağlayıcısı devreye girdi ve cevap verdi."
            assert metrics.provider == "groq"
            assert metrics.status == "success"
    print("✓ test_director_provider_fallback başarılı (Gemini tükenince Groq devreye girdi).")


async def test_chat_message_endpoint():
    """POST /api/v1/chat/message endpoint'inin doğruluğunu test et."""
    req = ChatMessageRequest(
        message="Kıyafet aldım 2 gün sonra dikişleri attı, fişim var.",
        summary="Kullanıcı yeni kıyafet almış."
    )
    res = await send_chat_message(req)
    assert res.success is True
    assert len(res.response) > 0
    assert len(res.summary) > 0
    assert res.metrics is not None
    assert res.metrics.status == "success"
    print("✓ test_chat_message_endpoint başarılı.")


def test_providers_status_endpoint():
    """GET /api/v1/chat/providers endpoint'ini test et."""
    status_resp = get_providers_status()
    assert len(status_resp.providers) == 3
    provider_names = [p.provider for p in status_resp.providers]
    assert "gemini" in provider_names
    assert "groq" in provider_names
    assert "openrouter" in provider_names
    print("✓ test_providers_status_endpoint başarılı.")


async def run_all_chat_tests():
    print("=" * 55)
    print("HAKKIM VAR AI ASİSTANI VE ÇOKLU SAĞLAYICI TESTLERİ")
    print("=" * 55)
    test_system_prompt()
    test_json_extractor()
    await test_director_key_rotation()
    await test_director_provider_fallback()
    await test_chat_message_endpoint()
    test_providers_status_endpoint()
    print("=" * 55)
    print("🎉 TÜM CHAT VE YÖNETMEN TESTLERİ BAŞARIYLA GEÇTİ!")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(run_all_chat_tests())
