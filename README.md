# Entegre Tüketici Hakları ve Ürün Analiz Platformu - Backend API

Bu proje, tüketicilerin hak arama süreçlerini kolaylaştıran ve gıda/tüketim ürünlerinin içeriklerini analiz eden entegre mobil/web uygulamasının backend servisidir.

FastAPI ile modüler bir mimaride geliştirilmiştir. Gelecekte eklenecek tüm modüller (Görsel Kusur Analizi, Hak ve Mevzuat Analizi, Dilekçe Paketi vb.) bu yapı üzerine kolayca entegre edilecektir.

---

## 📱 Proje Modülleri Yol Haritası

| Modül | Durum | Açıklama |
| :--- | :---: | :--- |
| **Ürün ve İçerik Analizi (Barkod)** | ✅ **Tamamlandı** | Kamera/barkod ile okutulan ürünün Open Food Facts üzerinden besin, içerik, alerjen ve sağlık skorlarını analiz eder. |
| **Görsel Kusur Analizi** | ⏳ Sırada | Ürün fotoğrafındaki kırık, çatlak ve fiziksel kusurları yapay zeka ile tespit eder. |
| **Hak ve Mevzuat Analizi** | ⏳ Planlandı | Yaşanan tüketici mağduriyetine göre ilgili tüketici kanun ve maddelerini analiz eder. |
| **Dilekçe ve Kanıt Paketi** | ⏳ Planlandı | Tüketici Hakem Heyeti için başvuru dilekçesi ve kanıt dosyasını PDF olarak üretir. |
| **Firma Bilgileri ve Ön İhtar** | ⏳ Planlandı | Faturadan firma bilgilerini okuyarak noter/mail ön ihtar metni hazırlar. |
| **TÜBİS Başvuru Rehberi** | ⏳ Planlandı | E-devlet TÜBİS sistemine adım adım başvuru kılavuzu sunar. |

---

## 🚀 Kurulum ve Çalıştırma

### 1. Gereksinimleri Yükleme
```bash
pip install -r requirements.txt
```

### 2. Sunucuyu Başlatma
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
> Mobil cihazdan test ediyorsanız bilgisayarınızın yerel IP adresini kullanabilirsiniz (Örn: `http://192.168.1.XX:8000`).

### 3. Swagger Dokümantasyon Arayüzü
Sunucuyu başlattıktan sonra tarayıcınızdan interaktif API dökümanına ulaşabilirsiniz:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 Frontend (Mobil) Entegrasyon Kılavuzu

### 1. Barkod Analizi Endpoint'i (POST)

Mobil taraf yalnızca okunan barkod numarasını POST gövdesinde gönderir:

```http
POST /api/v1/products/analyze
Content-Type: application/json

{
  "barcode": "8690504135913",
  "include_raw": false
}
```

> **İpucu:** Eğer Open Food Facts'in 240+ ham alanının hiçbir filtreden geçmemiş orijinal halini de görmek isterseniz `"include_raw": true` gönderebilirsiniz. Bu durumda tüm orijinal veri `data.raw_openfoodfacts` altında gelecektir.

#### Yanıt Durum Kodları:
- **`200 OK`**: Ürün bulundu ve başarıyla analiz edildi (`success: true`).
- **`404 Not Found`**: Bu barkoda ait ürün bulunamadı (`success: false`).
- **`502 Bad Gateway`**: Dış servis (Open Food Facts) yanıt vermedi (`success: false`).

---

### 2. Sağlık Kontrolü (HEAD & GET)
- **`GET /health`** ve **`HEAD /health`**: Uptime/Render servis kontrolleri için her iki HTTP metodunu da destekler.

---

### 2. Örnek JSON Yanıtı ve Frontend Kullanımı

```json
{
  "success": true,
  "message": "Ürün bilgileri başarıyla getirildi ve analiz edildi.",
  "barcode": "8690504135913",
  "data": {
    "barcode": "8690504135913",
    "product_name": "ülker çikolata",
    "brand": "Ülker",
    "quantity": "36 g",
    "categories": [
      "Stuffed Wafers",
      "Candy Chocolate Bars",
      "Chocolate Biscuity Bars"
    ],
    "origin_country": "Türkiye",
    "manufacturing_places": null,
    "images": {
      "front_url": "https://images.openfoodfacts.org/images/products/869/050/413/5913/front_tr.81.400.jpg",
      "ingredients_url": "https://images.openfoodfacts.org/images/products/869/050/413/5913/ingredients_tr.58.400.jpg",
      "nutrition_url": "https://images.openfoodfacts.org/images/products/869/050/413/5913/nutrition_tr.11.400.jpg",
      "packaging_url": null,
      "thumbnail_url": null
    },
    "nutrition": {
      "serving_size": "1 serving (36 g)",
      "energy_kcal_100g": 543.0,
      "energy_kcal_serving": 195.0,
      "fat_100g": 31.0,
      "fat_serving": 11.2,
      "saturated_fat_100g": 14.0,
      "saturated_fat_serving": 5.04,
      "carbohydrates_100g": 58.0,
      "carbohydrates_serving": 20.9,
      "sugars_100g": 38.0,
      "sugars_serving": 13.7,
      "fiber_100g": 2.4,
      "fiber_serving": 0.864,
      "proteins_100g": 6.5,
      "proteins_serving": 2.34,
      "salt_100g": 0.26,
      "salt_serving": 0.0936,
      "sodium_100g": 0.104,
      "levels": {
        "fat": { "raw_level": "high", "label_tr": "Yüksek", "color": "red" },
        "saturated_fat": { "raw_level": "high", "label_tr": "Yüksek", "color": "red" },
        "sugars": { "raw_level": "high", "label_tr": "Yüksek", "color": "red" },
        "salt": { "raw_level": "low", "label_tr": "Düşük", "color": "green" }
      }
    },
    "ingredients": {
      "raw_text": "Şeker, Buğday unu, bitkisel yağlar...",
      "items": [
        "Şeker",
        "Buğday unu",
        "bitkisel yağlar (palm",
        "tam hidrojenize palm",
        "fındık püresi (%10)",
        "süt tozu"
      ],
      "has_palm_oil": true,
      "is_vegan": false,
      "is_vegetarian": null
    },
    "health_scores": {
      "nutriscore_grade": "E",
      "nutriscore_score": null,
      "nutriscore_description": "Çok düşük besin kalitesi (Sık veya fazla tüketilmesi önerilmez)",
      "nova_group": 4,
      "nova_description": "Aşırı işlenmiş gıda (Ultra-işlenmiş gıda, endüstriyel katkılar içerir)",
      "ecoscore_grade": "B",
      "ecoscore_score": null,
      "ecoscore_description": "Düşük çevresel etki"
    },
    "safety_alerts": {
      "allergens": [
        "Gluten",
        "Süt / Laktoz"
      ],
      "traces": [
        "Fındık ve Fıstık"
      ],
      "additives": []
    },
    "certifications": {
      "labels": [
        "Pure Cocoa Butter"
      ],
      "packaging_materials": []
    }
  }
}
```

---

### 3. Mobil UI İçin Eşleme Tablosu

| Mobil Ekran Öğesi | Backend Alanı | Açıklama |
| :--- | :--- | :--- |
| **Ürün Başlığı & Marka** | `data.product_name` / `data.brand` | Ürünün adı ve üreticisi |
| **Kapak Fotoğrafı** | `data.images.front_url` | Ön yüz yüksek kaliteli fotoğraf |
| **İçindekiler Fotoğrafı** | `data.images.ingredients_url` | Etiket/içerik fotoğrafı (modal veya galeri) |
| **Besin Tablosu Fotoğrafı** | `data.images.nutrition_url` | Orijinal besin tablosu fotoğrafı |
| **Nutri-Score Rozeti** | `data.health_scores.nutriscore_grade` | 'A', 'B', 'C', 'D', 'E' harfli badge |
| **Trafik Işıkları (Riskler)** | `data.nutrition.levels` | Şeker, Tuz, Yağ için `color` ('red', 'yellow', 'green') ve `label_tr` |
| **Alerjen Uyarı Kutucukları** | `data.safety_alerts.allergens` | Süt, Gluten vb. kırmızı chip'ler |
| **Palm Yağı / Vegan Uyarıları** | `data.ingredients.has_palm_oil` / `is_vegan` | Boolean değerlerine göre ikon/uyarı rozeti |

---

## 🧪 Testleri Çalıştırma
```bash
python tests/test_product_analysis.py
```
Tüm birim testlerini, veri modelleme doğrulamalarını ve mock endpoint testlerini çalıştırır.
