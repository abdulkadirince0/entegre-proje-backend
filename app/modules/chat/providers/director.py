import logging
import time
from typing import Optional, List, Dict, Tuple, Any

from app.core.config import settings
from app.modules.chat.schemas import AIExecutionMetrics, ProviderStatus
from app.modules.chat.providers.base import (
    ProviderResult,
    QuotaExceededError,
    ProviderAPIError,
)
from app.modules.chat.providers.gemini import GeminiProvider
from app.modules.chat.providers.groq import GroqProvider
from app.modules.chat.providers.openrouter import OpenRouterProvider

logger = logging.getLogger("ai_director")


class AIDirector:
    """Çoklu AI sağlayıcı ve anahtar rotasyon yöneticisi (Yönetmen).
    
    Öncelik Sırası:
    1. Gemini (Havuzdaki tüm keyler, ardından model rotasyonu)
    2. Groq (Gemini kotası dolduğunda otomatik devreye girer)
    3. OpenRouter (Groq da tükenirse ücretsiz model havuzuna geçer)
    """

    def __init__(self):
        # Sağlayıcı anahtar havuzları ve aktif indeksleri
        self.key_pools: Dict[str, List[str]] = {
            "gemini": list(settings.GEMINI_API_KEYS),
            "groq": list(settings.GROQ_API_KEYS),
            "openrouter": list(settings.OPENROUTER_API_KEYS),
        }
        self.active_indices: Dict[str, int] = {
            "gemini": 0,
            "groq": 0,
            "openrouter": 0,
        }
        self.models_map: Dict[str, List[str]] = {
            "gemini": list(settings.GEMINI_MODELS),
            "groq": list(settings.GROQ_MODELS),
            "openrouter": list(settings.OPENROUTER_MODELS),
        }
        self.priority_order = ["gemini", "groq", "openrouter"]

    def reload_keys_from_settings(self):
        """Çevre değişkenlerinden yeni anahtarları yükler."""
        self.key_pools["gemini"] = list(settings.GEMINI_API_KEYS)
        self.key_pools["groq"] = list(settings.GROQ_API_KEYS)
        self.key_pools["openrouter"] = list(settings.OPENROUTER_API_KEYS)

    def get_provider_status(self) -> List[ProviderStatus]:
        """Tüm sağlayıcıların aktif anahtar ve model durumunu döner."""
        statuses = []
        for p in self.priority_order:
            keys = self.key_pools.get(p, [])
            models = self.models_map.get(p, [])
            idx = self.active_indices.get(p, 0)
            statuses.append(
                ProviderStatus(
                    provider=p,
                    total_keys=len(keys),
                    active_key_index=idx if keys else 0,
                    available_models=models,
                    is_available=len(keys) > 0,
                )
            )
        return statuses

    async def execute_chat(
        self,
        message: str,
        summary: str = "",
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Tuple[ProviderResult, AIExecutionMetrics]:
        """Tüm sağlayıcılar ve anahtarlar arasında akıllı rotasyon yaparak yanıt üretir."""
        total_start = time.perf_counter()
        attempts = 0
        last_error_type = "none"
        last_exception_msg = ""

        # 1. Öncelik sırasına göre sağlayıcıları gez
        for provider_name in self.priority_order:
            keys = self.key_pools.get(provider_name, [])
            if not keys:
                continue

            models = self.models_map.get(provider_name, [])
            start_key_idx = self.active_indices.get(provider_name, 0)
            total_keys = len(keys)

            # Modelleri sırayla dene
            for model_name in models:
                # O model için tüm keyleri sırayla dene
                for k_step in range(total_keys):
                    current_idx = (start_key_idx + k_step) % total_keys
                    api_key = keys[current_idx]
                    attempts += 1

                    try:
                        logger.info(
                            f"[Yönetmen] İstek başlatılıyor -> Sağlayıcı: {provider_name}, "
                            f"Model: {model_name}, Key #{current_idx + 1}/{total_keys}"
                        )

                        if provider_name == "gemini":
                            result = await GeminiProvider.generate(
                                api_key=api_key,
                                model=model_name,
                                message=message,
                                summary=summary,
                                image_base64=image_base64,
                                image_url=image_url,
                            )
                        elif provider_name == "groq":
                            result = await GroqProvider.generate(
                                api_key=api_key,
                                model=model_name,
                                message=message,
                                summary=summary,
                                image_base64=image_base64,
                                image_url=image_url,
                            )
                        elif provider_name == "openrouter":
                            result = await OpenRouterProvider.generate(
                                api_key=api_key,
                                model=model_name,
                                message=message,
                                summary=summary,
                                image_base64=image_base64,
                                image_url=image_url,
                            )
                        else:
                            continue

                        # Başarılı olduysa aktif key indeksini bu keyde tut
                        self.active_indices[provider_name] = current_idx
                        total_latency = round((time.perf_counter() - total_start) * 1000, 2)

                        metrics = AIExecutionMetrics(
                            provider=provider_name,
                            model=model_name,
                            input_tokens=result.input_tokens,
                            output_tokens=result.output_tokens,
                            total_tokens=result.total_tokens,
                            latency_ms=total_latency,
                            status="success",
                            error_type=None,
                            attempts_count=attempts,
                        )
                        logger.info(f"[Yönetmen] Başarılı yanıt alındı! ({provider_name} - {model_name})")
                        return result, metrics

                    except QuotaExceededError as q_err:
                        last_error_type = "quota_exceeded"
                        last_exception_msg = str(q_err)
                        logger.warning(
                            f"[Yönetmen Kota Uyarısı] {provider_name} Key #{current_idx + 1} kotası doldu! "
                            f"Sonraki anahtara geçiliyor... ({str(q_err)})"
                        )
                        # Bir sonraki key'i aktif yap
                        self.active_indices[provider_name] = (current_idx + 1) % total_keys
                        continue

                    except ProviderAPIError as api_err:
                        last_error_type = f"api_error_{api_err.status_code}"
                        last_exception_msg = str(api_err)
                        logger.warning(
                            f"[Yönetmen API Hatası] {provider_name} ({model_name}) hata verdi: {str(api_err)}. "
                            "Sonraki seçenek deneniyor..."
                        )
                        continue

                    except Exception as unk_err:
                        last_error_type = "unexpected_error"
                        last_exception_msg = str(unk_err)
                        logger.error(f"[Yönetmen Beklenmeyen Hata] {provider_name}: {str(unk_err)}")
                        continue

        # 2. Eğer hiçbir sağlayıcıda anahtar yoksa veya hepsi tükendiyse:
        total_latency = round((time.perf_counter() - total_start) * 1000, 2)
        
        # Test / Geliştirme ortamı için simülasyon yanıtı (Eğer API key girilmemişse)
        has_any_keys = any(len(k) > 0 for k in self.key_pools.values())
        if not has_any_keys:
            logger.info("[Yönetmen] Çevre değişkenlerinde API anahtarı tanımlanmadığı için akıllı simülasyon yanıtı üretiliyor.")
            mock_res, mock_summary = self._generate_development_mock(message, summary)
            res = ProviderResult(
                response_text=mock_res,
                summary_text=mock_summary,
                provider="demo_mode",
                model="tuketici-kanunu-v1",
                input_tokens=len(message) // 4,
                output_tokens=len(mock_res) // 4,
                total_tokens=(len(message) + len(mock_res)) // 4,
                latency_ms=total_latency,
            )
            metrics = AIExecutionMetrics(
                provider="demo_mode",
                model="tuketici-kanunu-v1",
                input_tokens=res.input_tokens,
                output_tokens=res.output_tokens,
                total_tokens=res.total_tokens,
                latency_ms=total_latency,
                status="success",
                error_type="no_api_keys_configured (demo_mode)",
                attempts_count=attempts or 1,
            )
            return res, metrics

        # Tüm sağlayıcılar ve anahtarlar gerçekten tükendiyse
        metrics = AIExecutionMetrics(
            provider="none",
            model="none",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            latency_ms=total_latency,
            status="failed",
            error_type=last_error_type or "all_providers_exhausted",
            attempts_count=attempts,
        )
        raise RuntimeError(
            f"Tüm AI sağlayıcı havuzları ve anahtarları tükendi. Son hata: {last_exception_msg or last_error_type}"
        )

    @staticmethod
    def _generate_development_mock(message: str, summary: str) -> Tuple[str, str]:
        """API key tanımlanmadığında testlerin ve lokal geliştirmenin aksamaması için örnek yanıt döner."""
        msg_l = message.lower()
        if "iade" in msg_l or "bozuk" in msg_l or "ayıp" in msg_l:
            resp = (
                "6502 sayılı Tüketicinin Korunması Hakkında Kanun'un 11. maddesi uyarınca, "
                "ayıplı mal tesliminde tüketicinin 4 seçimlik hakkı bulunmaktadır:\n"
                "1. Bedel iadesini de içeren sözleşmeden dönme,\n"
                "2. Ayıp oranında satış bedelinden indirim isteme,\n"
                "3. Aşırı bir masraf gerektirmediği takdirde ücretsiz onarım isteme,\n"
                "4. İmkân varsa malın ayıpsız misli ile değiştirilmesini isteme.\n\n"
                "Satıcı bu haklardan tüketicinin tercih ettiğini yerine getirmekle yükümlüdür. "
                "Satıcınız talebinizi reddederse faturanızla birlikte ikamet ettiğiniz yerdeki "
                "Tüketici Hakem Heyetine e-Devlet (TÜBİS) üzerinden ücretsiz başvurabilirsiniz."
            )
            new_summary = "Kullanıcı ayıplı ürün iadesi ve 6502 sayılı kanun m.11 kapsamındaki seçimlik hakları hakkında bilgilendirildi."
        else:
            resp = (
                "Merhaba, ben 'Hakkım Var' tüketici hakları asistanınız. Yaşadığınız alışveriş, "
                "ayıplı ürün/hizmet, garanti süresi, mesafeli sözleşme veya cayma hakkı gibi "
                "tüm tüketici uyuşmazlıklarında size mevzuat çerçevesinde rehberlik edebilirim. "
                "Lütfen ürünün ne zaman alındığını ve satıcıyla olan durumu detaylandırır mısınız?"
            )
            new_summary = summary or "Kullanıcı tüketici danışmanlığı başlattı."
        return resp, new_summary


director = AIDirector()
