-- ========================================================
-- Tüketici Hakları ve Ürün Analiz Platformu
-- Supabase Veritabanı Şeması (Chats, Messages & AI Logs)
-- ========================================================

-- 1. CHATS TABLOSU (Sohbet Oturumları ve Hafıza Özeti)
CREATE TABLE IF NOT EXISTS public.chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Yeni Danışma',
    summary TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Indexler
CREATE INDEX IF NOT EXISTS idx_chats_user_id ON public.chats(user_id);
CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON public.chats(updated_at DESC);


-- 2. MESSAGES TABLOSU (Sohbet Mesajları)
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES public.chats(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    sequence BIGSERIAL NOT NULL
);

-- Indexler
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON public.messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_sequence ON public.messages(chat_id, sequence ASC);


-- 3. AI_REQUEST_LOGS TABLOSU (Telemetri, Model, Token ve Hata Takibi)
CREATE TABLE IF NOT EXISTS public.ai_request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES public.chats(id) ON DELETE SET NULL,
    provider TEXT NOT NULL,               -- 'gemini', 'groq', 'openrouter'
    model TEXT NOT NULL,                  -- 'gemini-2.0-flash', 'llama-3.3-70b-versatile' vb.
    input_tokens INTEGER,                 -- Giriş token sayısı
    output_tokens INTEGER,                -- Çıkış token sayısı
    total_tokens INTEGER,                 -- Toplam token
    latency_ms NUMERIC(10, 2),            -- İstek süresi (milisaniye)
    status TEXT NOT NULL,                 -- 'success', 'failed'
    error_type TEXT,                      -- 'quota_exceeded_429', 'timeout' vb.
    attempts_count INTEGER DEFAULT 1,     -- Kaç key/sağlayıcı denendi
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ai_logs_created_at ON public.ai_request_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_logs_provider ON public.ai_request_logs(provider, status);


-- 4. OTOMATİK UPDATED_AT TETİKLEYİCİSİ (TRIGGER)
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_chats_updated_at ON public.chats;
CREATE TRIGGER set_chats_updated_at
    BEFORE UPDATE ON public.chats
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- RLS (Row Level Security) - Opsiyonel
ALTER TABLE public.chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_request_logs ENABLE ROW LEVEL SECURITY;

-- Kullanıcılar sadece kendi chatlerini okuyup yazabilir (Örnek politika)
CREATE POLICY "Users can manage their own chats" ON public.chats
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage messages in their chats" ON public.messages
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.chats
            WHERE public.chats.id = public.messages.chat_id
            AND public.chats.user_id = auth.uid()
        )
    );
