import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# 1. Türkçe destekli Arial fontlarını kaydet
pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "C:/Windows/Fonts/arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", "C:/Windows/Fonts/ariali.ttf"))


class NumberedCanvas(canvas.Canvas):
    """Her sayfanın altına otomatik sayfa numarası ve üst bilgi ekleyen canvas."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Arial", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Üst çizgi ve başlık (İlk sayfa hariç)
        if self._pageNumber > 1:
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(40, A4[1] - 35, A4[0] - 40, A4[1] - 35)
            self.drawString(40, A4[1] - 30, "Tüketici Hakları ve Ürün Analiz Platformu — Frontend Entegrasyon Rehberi")

        # Alt çizgi ve sayfa numarası
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(40, 35, A4[0] - 40, 35)
        
        self.drawString(40, 24, "Entegre Proje | Backend & Frontend Entegrasyon Dokümanı")
        page_str = f"Sayfa {self._pageNumber} / {page_count}"
        self.drawRightString(A4[0] - 40, 24, page_str)
        self.restoreState()


def build_pdf(filename="OMER_FRONTEND_ENTEGRASYON_KILAVUZU.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()

    # Özel Tipografi Stilleri
    c_primary = colors.HexColor("#1A365D")
    c_accent = colors.HexColor("#2B6CB0")
    c_dark = colors.HexColor("#2D3748")

    title_style = ParagraphStyle(
        "DocTitle",
        fontName="Arial-Bold",
        fontSize=20,
        leading=25,
        textColor=c_primary,
        alignment=0,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        fontName="Arial",
        fontSize=11,
        leading=16,
        textColor=c_accent,
        spaceAfter=15,
    )
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        fontName="Arial-Bold",
        fontSize=13,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=8,
    )
    h2_style = ParagraphStyle(
        "Heading2_Custom",
        fontName="Arial-Bold",
        fontSize=10.5,
        leading=15,
        textColor=c_accent,
        spaceBefore=10,
        spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        fontName="Arial",
        fontSize=9,
        leading=13.5,
        textColor=c_dark,
        spaceAfter=6,
    )
    body_bold = ParagraphStyle(
        "BodyBold_Custom",
        fontName="Arial-Bold",
        fontSize=9,
        leading=13.5,
        textColor=c_dark,
    )
    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        fontName="Arial",
        fontSize=8.8,
        leading=13,
        textColor=c_dark,
        leftIndent=14,
        spaceAfter=4,
    )
    code_style = ParagraphStyle(
        "Code_Custom",
        fontName="Arial",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=0,
    )
    th_style = ParagraphStyle(
        "TH_Style",
        fontName="Arial-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )
    td_style = ParagraphStyle(
        "TD_Style",
        fontName="Arial",
        fontSize=8,
        leading=11,
        textColor=c_dark,
    )

    story = []

    # BAŞLIK ALANI
    story.append(Paragraph("Tüketici Hakları ve Ürün Analiz Platformu", title_style))
    story.append(Paragraph("<b>1. Modül: Ürün ve İçerik Analizi (Barkod) — Frontend Geliştirici Kılavuzu</b><br/>Hazırlayan: Abdulkadir İnce | Alıcı: Ömer (Frontend Lead)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceAfter=14))

    # GİRİŞ KUTUSU
    intro_p = Paragraph(
        "<b>Merhaba Ömer,</b><br/>"
        "Mobil tarafta tamamladığın barkod okuyucu modülünün backend tarafı hazırlandı! "
        "Open Food Facts API'sinden gelen binlerce satırlık ham JSON karmaşasını ayıkladık. "
        "Backend; ürün fotoğraflarını (ön yüz, içindekiler, besin tablosu), 100g ve porsiyon besin değerlerini, "
        "alerjenleri, Palm yağı/Vegan durumunu ve sağlık puanlarını (Nutri-Score, NOVA, Trafik Işıkları) "
        "temiz, düzenli ve doğrudan ekrana basabileceğin bir formatta sunuyor.",
        body_style
    )
    intro_table = Table([[intro_p]], colWidths=[515])
    intro_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EBF8FF")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#BEE3F8")),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 12))

    # BÖLÜM 1: GITHUB'DAN ÇEKME VE ÇALIŞTIRMA
    story.append(Paragraph("1. Projeyi GitHub'dan İndirme ve Lokalde Çalıştırma", h1_style))
    story.append(Paragraph("Projeyi kendi bilgisayarına çekmek ve yerel ortamında FastAPI backend'ini ayağa kaldırmak için:", body_style))

    clone_code = (
        "# 1. Repoyu bilgisayarına klonla<br/>"
        "git clone https://github.com/abdulkadirince0/entegre-proje-backend.git<br/>"
        "cd entegre-proje-backend<br/><br/>"
        "# 2. Sanal ortam oluştur (isteğe bağlı) ve gereksinimleri yükle<br/>"
        "python -m venv venv<br/>"
        "venv\\Scripts\\activate   # (Mac/Linux için: source venv/bin/activate)<br/>"
        "pip install -r requirements.txt<br/><br/>"
        "# 3. Backend sunucusunu başlat<br/>"
        "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    )
    code_t1 = Table([[Paragraph(clone_code, code_style)]], colWidths=[515])
    code_t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(code_t1)
    story.append(Spacer(1, 8))

    story.append(Paragraph("• <b>Swagger Dokümantasyonu:</b> Tarayıcında <b>http://localhost:8000/docs</b> adresini açarak tüm endpoint'leri canlı olarak deneyebilirsin.", bullet_style))
    story.append(Paragraph("• <b>Testleri Koşmak İçin:</b> <code>python tests/test_product_analysis.py</code> komutunu çalıştırarak 6 birim ve entegrasyon testini doğrulayabilirsin.", bullet_style))
    story.append(Spacer(1, 10))

    # BÖLÜM 2: MOBİL CİHAZ AĞ BAĞLANTISI (ÖNEMLİ İPUCU)
    story.append(Paragraph("2. Mobil Cihaz / Emülatör Bağlantısı (CORS & IP)", h1_style))
    net_info = Paragraph(
        "<b>⚠️ Önemli Bağlantı Notu:</b> Mobil uygulama veya emülatörden backend'e istek atarken <code>localhost</code> çalışmaz. "
        "Aşağıdaki kuralları kullanmalısın:<br/>"
        "• <b>Fiziksel Mobil Cihaz (Wi-Fi):</b> Bilgisayarının yerel IP adresini yaz: <code>http://192.168.1.XX:8000</code><br/>"
        "• <b>Android Emülatör:</b> Bilgisayarın localhost'una bağlanmak için: <code>http://10.0.2.2:8000</code><br/>"
        "• <b>iOS Simülatör:</b> Doğrudan <code>http://localhost:8000</code> adresini kullanabilir.<br/>"
        "<i>* Backend tarafında CORS tüm kaynaklara açık şekilde yapılandırılmıştır (allow_origins=['*']).</i>",
        body_style
    )
    net_table = Table([[net_info]], colWidths=[515])
    net_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFBEB")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#FDE68A")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(net_table)
    story.append(Spacer(1, 12))

    # BÖLÜM 3: ENDPOINT VE İSTEK ATMA
    story.append(Paragraph("3. API İstek Formatı (POST Endpoint)", h1_style))
    story.append(Paragraph("Mobil barkod tarayıcı kameran barkodu okuduğu anda aşağıdaki POST endpoint'ine istek atman yeterlidir:", body_style))

    req_post = (
        "<b>POST</b> https://entegre-proje-backend.onrender.com/api/v1/products/analyze<br/>"
        "<b>Headers:</b> <code>Content-Type: application/json</code><br/>"
        "<b>Body:</b> <code>{\"barcode\": \"8690504135913\", \"include_raw\": false}</code><br/>"
        "<i>* include_raw: true gönderirsen Open Food Facts'in filtrelenmemiş 240+ ham alanının tamamı da 'raw_openfoodfacts' altında gelir!</i>"
    )
    t_post = Table([[Paragraph(req_post, code_style)]], colWidths=[515])
    t_post.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#BBF7D0")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_post)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Dönen Yanıt Durumları:</b>", body_style))
    story.append(Paragraph("• <b>200 OK (Ürün Bulundu):</b> <code>{\"success\": true, \"message\": \"...\", \"data\": { ... }}</code>", bullet_style))
    story.append(Paragraph("• <b>404 Not Found (Ürün Yok):</b> <code>{\"success\": false, \"message\": \"Bu barkoda ait ürün bulunamadı.\", \"data\": null}</code>", bullet_style))
    story.append(Paragraph("• <b>HEAD /health:</b> Render veya uptime izleme servisleri için <code>HEAD</code> istekleri tam desteklenir.", bullet_style))
    story.append(Spacer(1, 8))

    story.append(PageBreak())

    # BÖLÜM 4: MOBİL ARAYÜZ (UI) ALAN EŞLEME TABLOSU
    story.append(Paragraph("4. Mobil UI ve JSON Veri Eşleme Tablosu", h1_style))
    story.append(Paragraph(
        "Gelen yanıttaki <code>data</code> objesindeki alanları mobil tasarımındaki bileşenlerle birebir nasıl eşleştireceğin aşağıda özetlenmiştir:",
        body_style
    ))

    table_data = [
        [
            Paragraph("Mobil Ekran Bölümü", th_style),
            Paragraph("JSON Alanı (data...)", th_style),
            Paragraph("Veri Tipi & Değer", th_style),
            Paragraph("Kullanım & Tasarım Önerisi", th_style)
        ],
        [
            Paragraph("<b>Ürün Başlığı & Marka</b>", td_style),
            Paragraph("<code>product_name</code><br/><code>brand</code>", td_style),
            Paragraph("String<br/>(Örn: 'ülker çikolata')", td_style),
            Paragraph("Detay sayfasının en üstündeki başlık ve marka alt başlığı.", td_style)
        ],
        [
            Paragraph("<b>Gramaj / Miktar</b>", td_style),
            Paragraph("<code>quantity</code>", td_style),
            Paragraph("String (Örn: '36 g')", td_style),
            Paragraph("Ürün adının yanındaki gri küçük etiket (badge).", td_style)
        ],
        [
            Paragraph("<b>Kapak Fotoğrafı</b>", td_style),
            Paragraph("<code>images.front_url</code>", td_style),
            Paragraph("URL (Yüksek çözünürlük)", td_style),
            Paragraph("Ekranın üstündeki ana görsel kartı. Boşsa placeholder koy.", td_style)
        ],
        [
            Paragraph("<b>İçindekiler Fotoğrafı</b>", td_style),
            Paragraph("<code>images.ingredients_url</code>", td_style),
            Paragraph("URL (Etiket fotosu)", td_style),
            Paragraph("'İçindekiler Etiketi' butonuna basınca açılan modal / galeri.", td_style)
        ],
        [
            Paragraph("<b>Besin Tablosu Fotosu</b>", td_style),
            Paragraph("<code>images.nutrition_url</code>", td_style),
            Paragraph("URL (Tablo fotosu)", td_style),
            Paragraph("Orijinal besin değerleri etiket fotoğrafı görünümü.", td_style)
        ],
        [
            Paragraph("<b>Nutri-Score Rozeti</b>", td_style),
            Paragraph("<code>health_scores.<br/>nutriscore_grade</code>", td_style),
            Paragraph("'A', 'B', 'C', 'D', 'E'", td_style),
            Paragraph("Uluslararası gıda kalite harfi. Açıklama: <code>nutriscore_description</code>", td_style)
        ],
        [
            Paragraph("<b>Besin Riskleri<br/>(Trafik Işıkları)</b>", td_style),
            Paragraph("<code>nutrition.levels.<br/>sugars, fat, salt</code>", td_style),
            Paragraph("<code>label_tr</code>: 'Yüksek'<br/><code>color</code>: 'red'", td_style),
            Paragraph("Kırmızı/Sarı/Yeşil renk kodlu chip'ler. Şeker, yağ, tuz risk seviyeleri.", td_style)
        ],
        [
            Paragraph("<b>Alerjen Uyarıları</b>", td_style),
            Paragraph("<code>safety_alerts.<br/>allergens</code>", td_style),
            Paragraph("List[String]<br/>['Gluten', 'Süt']", td_style),
            Paragraph("Kırmızı/Turuncu arka planlı dikkat çekici etiketler.", td_style)
        ],
        [
            Paragraph("<b>Palm Yağı / Vegan</b>", td_style),
            Paragraph("<code>ingredients.<br/>has_palm_oil, is_vegan</code>", td_style),
            Paragraph("Boolean (True / False)", td_style),
            Paragraph("True ise 'Palm Yağı İçerir' uyarısı; Vegan ise yeşil yaprak ikonu.", td_style)
        ],
        [
            Paragraph("<b>100g & Porsiyon Besin Tablosu</b>", td_style),
            Paragraph("<code>nutrition.<br/>energy_kcal_100g,<br/>fat_100g, sugars...</code>", td_style),
            Paragraph("Float (Örn: 543.0, 38.0)", td_style),
            Paragraph("Enerji, Yağ, Doymuş Yağ, Şeker, Protein, Lif ve Tuz tablosu.", td_style)
        ],
    ]

    col_w = [110, 115, 100, 190]
    ui_table = Table(table_data, colWidths=col_w)
    ui_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(ui_table)
    story.append(Spacer(1, 14))

    # BÖLÜM 5: FRONTEND KOD ÖRNEĞİ (BARKOD - DART / FLUTTER)
    story.append(Paragraph("5. Örnek Frontend Kodu (Barkod - Dart / Flutter)", h1_style))
    sample_dart = (
        "// Flutter / Dart POST İstek Fonksiyonu (Barkod Analizi)<br/>"
        "Future&lt;void&gt; fetchProductAnalysis(String barcode) async {<br/>"
        "  final url = Uri.parse('https://entegre-proje-backend.onrender.com/api/v1/products/analyze');<br/>"
        "  final response = await http.post(<br/>"
        "    url,<br/>"
        "    headers: {'Content-Type': 'application/json'},<br/>"
        "    body: json.encode({'barcode': barcode, 'include_raw': false}),<br/>"
        "  );<br/><br/>"
        "  final jsonBody = json.decode(utf8.decode(response.bodyBytes));<br/>"
        "  if (response.statusCode == 200 &amp;&amp; jsonBody['success'] == true) {<br/>"
        "    final product = jsonBody['data'];<br/>"
        "    print('Ürün: ${product['product_name']}');<br/>"
        "    print('Nutri-Score: ${product['health_scores']['nutriscore_grade']}');<br/>"
        "  } else {<br/>"
        "    showErrorDialog(jsonBody['message'] ?? 'Ürün bulunamadı');<br/>"
        "  }<br/>"
        "}"
    )
    code_style_white = ParagraphStyle(
        "CodeWhite",
        fontName="Arial",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#E2E8F0"),
    )
    dart_table = Table([[Paragraph(sample_dart, code_style_white)]], colWidths=[515])
    dart_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#1A202C")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.black),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(dart_table)
    story.append(Spacer(1, 14))

    story.append(PageBreak())

    # BÖLÜM 6: HAKKIM VAR TÜKETİCİ HAKLARI AI ASİSTANI (YENİ MODÜL)
    story.append(Paragraph("6. Yeni Modül: 'Hakkım Var' Tüketici Danışmanı AI Chat", h1_style))
    chat_intro = Paragraph(
        "<b>Ömer'in Tasarladığı Chat & Hafıza Mimarisi:</b><br/>"
        "Tüketici uyuşmazlıkları için sohbet hafızasını <b>'summary' (özet)</b> alanı üzerinden yöneten, "
        "kesintisiz hizmet için <b>Çoklu Sağlayıcı Havuzu (Gemini ➔ Groq ➔ OpenRouter)</b> ve "
        "otomatik <b>Anahtar Rotasyonu (Yönetmen)</b> kullanan AI asistan modülüdür.",
        body_style
    )
    chat_box = Table([[chat_intro]], colWidths=[515])
    chat_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF5FF")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E9D8FD")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(chat_box)
    story.append(Spacer(1, 10))

    story.append(Paragraph("A. Supabase Veritabanı Tabloları", h2_style))
    story.append(Paragraph("Proje kök dizinindeki <code>supabase_schema.sql</code> dosyasını Supabase SQL editöründe çalıştırarak tabloları oluşturabilirsin:", body_style))
    story.append(Paragraph("• <b>chats:</b> <code>id (uuid)</code>, <code>user_id</code>, <code>title</code>, <code>summary (hafıza)</code>, <code>created_at</code>, <code>updated_at</code>", bullet_style))
    story.append(Paragraph("• <b>messages:</b> <code>id (uuid)</code>, <code>chat_id</code>, <code>role ('user'/'assistant')</code>, <code>content</code>, <code>sequence</code>", bullet_style))
    story.append(Paragraph("• <b>ai_request_logs:</b> <code>provider</code>, <code>model</code>, <code>tokens</code>, <code>latency_ms</code>, <code>status</code>, <code>error_type</code>", bullet_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("B. Chat API İstek Formatı (POST)", h2_style))
    chat_req = (
        "<b>POST</b> https://entegre-proje-backend.onrender.com/api/v1/chat/message<br/>"
        "<b>Headers:</b> <code>Content-Type: application/json</code><br/>"
        "<b>Body:</b><br/>"
        "{\n"
        "  \"message\": \"Satıcı bozuk malı geri almıyor, haklarım neler?\",\n"
        "  \"summary\": \"Kullanıcı 15 Kasım'da faturalı telefon almıştı.\",  // Önceki özet (ilk mesajda boş)\n"
        "  \"image_base64\": null,  // Varsa ayıplı ürün / fatura fotoğrafı\n"
        "  \"chat_id\": \"b2c3d4e5-f6a7-...\"\n"
        "}"
    )
    t_chat = Table([[Paragraph(chat_req, code_style)]], colWidths=[515])
    t_chat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#BBF7D0")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_chat)
    story.append(Spacer(1, 8))

    story.append(Paragraph("C. Dönen Yanıt Formatı ve Hafıza Döngüsü", h2_style))
    chat_res = (
        "{\n"
        "  \"success\": true,\n"
        "  \"response\": \"6502 sayılı Tüketici Kanunu m.11 uyarınca 4 seçimlik hakkınız vardır...\",\n"
        "  \"summary\": \"Kullanıcı 15 Kasım'da aldığı telefonun arızası ve iade hakkı konusunda bilgilendirildi.\",\n"
        "  \"metrics\": {\n"
        "    \"provider\": \"gemini\",\n"
        "    \"model\": \"gemini-2.0-flash\",\n"
        "    \"input_tokens\": 142,\n"
        "    \"output_tokens\": 88,\n"
        "    \"latency_ms\": 1120.5,\n"
        "    \"status\": \"success\"\n"
        "  }\n"
        "}"
    )
    t_res = Table([[Paragraph(chat_res, code_style)]], colWidths=[515])
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_res)
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Döngü Kuralı:</b> Dönen <code>summary</code> değerini Supabase'deki ilgili chat kaydına kaydedip, kullanıcının bir sonraki sorusunda body'deki <code>summary</code> alanına koyarak backend'e iletmelisin. Böylece asistan sohbeti asla unutmaz!", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("D. Flutter Chat Gönderim Örneği", h2_style))
    sample_chat_dart = (
        "// Flutter Chat Mesaj Gönderme Örneği<br/>"
        "Future&lt;void&gt; sendHakkimVarMessage(String userMsg, String currentSummary) async {<br/>"
        "  final response = await http.post(<br/>"
        "    Uri.parse('https://entegre-proje-backend.onrender.com/api/v1/chat/message'),<br/>"
        "    headers: {'Content-Type': 'application/json'},<br/>"
        "    body: json.encode({<br/>"
        "      'message': userMsg,<br/>"
        "      'summary': currentSummary,<br/>"
        "    }),<br/>"
        "  );<br/>"
        "  final data = json.decode(utf8.decode(response.bodyBytes));<br/>"
        "  if (data['success'] == true) {<br/>"
        "    String botReply = data['response'];<br/>"
        "    String newSummary = data['summary']; // Supabase chats.summary tablosunu güncelle!<br/>"
        "  }<br/>"
        "}"
    )
    t_cdart = Table([[Paragraph(sample_chat_dart, code_style_white)]], colWidths=[515])
    t_cdart.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#1A202C")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.black),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_cdart)
    story.append(Spacer(1, 14))

    # BİTİŞ & İLETİŞİM NOTU
    closing_p = Paragraph(
        "<b>İyi çalışmalar Ömer!</b> Hem barkod analizi hem de çoklu sağlayıcı rotasyonlu Hakkım Var AI asistanı hazır. "
        "Sorunsuz şekilde test edebilirsin!",
        body_style
    )
    story.append(closing_p)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {filename}")


if __name__ == "__main__":
    build_pdf()
