from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class NutrientLevelDetail(BaseModel):
    """Belirli bir besin öğesinin sağlık risk seviyesi (Düşük / Orta / Yüksek)."""
    raw_level: Optional[str] = Field(None, description="Open Food Facts ham seviyesi: low, moderate, high")
    label_tr: Optional[str] = Field(None, description="Türkçe gösterim: Düşük, Orta, Yüksek")
    color: Optional[str] = Field(None, description="Trafik ışığı renk kodu: green, yellow, red")


class NutrientLevels(BaseModel):
    """Ürünün 4 ana parametredeki besin risk seviyeleri (Trafik Işıkları Sistemi)."""
    fat: Optional[NutrientLevelDetail] = Field(None, description="Yağ seviyesi")
    saturated_fat: Optional[NutrientLevelDetail] = Field(None, description="Doymuş yağ seviyesi")
    sugars: Optional[NutrientLevelDetail] = Field(None, description="Şeker seviyesi")
    salt: Optional[NutrientLevelDetail] = Field(None, description="Tuz seviyesi")


class ProductNutrition(BaseModel):
    """Ürünün 100g ve porsiyon bazında detaylı besin değerleri tablosu."""
    serving_size: Optional[str] = Field(None, description="Porsiyon büyüklüğü (Örn: '1 porsiyon (36 g)')")
    
    # 100 gram/ml değerleri
    energy_kcal_100g: Optional[float] = Field(None, description="100g Enerji (kcal)")
    energy_kj_100g: Optional[float] = Field(None, description="100g Enerji (kJ)")
    fat_100g: Optional[float] = Field(None, description="100g Yağ (g)")
    saturated_fat_100g: Optional[float] = Field(None, description="100g Doymuş Yağ (g)")
    carbohydrates_100g: Optional[float] = Field(None, description="100g Karbonhidrat (g)")
    sugars_100g: Optional[float] = Field(None, description="100g Şekerler (g)")
    fiber_100g: Optional[float] = Field(None, description="100g Lif (g)")
    proteins_100g: Optional[float] = Field(None, description="100g Protein (g)")
    salt_100g: Optional[float] = Field(None, description="100g Tuz (g)")
    sodium_100g: Optional[float] = Field(None, description="100g Sodyum (g)")

    # Porsiyon bazlı değerler
    energy_kcal_serving: Optional[float] = Field(None, description="Porsiyon başına Enerji (kcal)")
    energy_kj_serving: Optional[float] = Field(None, description="Porsiyon başına Enerji (kJ)")
    fat_serving: Optional[float] = Field(None, description="Porsiyon başına Yağ (g)")
    saturated_fat_serving: Optional[float] = Field(None, description="Porsiyon başına Doymuş Yağ (g)")
    carbohydrates_serving: Optional[float] = Field(None, description="Porsiyon başına Karbonhidrat (g)")
    sugars_serving: Optional[float] = Field(None, description="Porsiyon başına Şekerler (g)")
    fiber_serving: Optional[float] = Field(None, description="Porsiyon başına Lif (g)")
    proteins_serving: Optional[float] = Field(None, description="Porsiyon başına Protein (g)")
    salt_serving: Optional[float] = Field(None, description="Porsiyon başına Tuz (g)")
    sodium_serving: Optional[float] = Field(None, description="Porsiyon başına Sodyum (g)")

    levels: Optional[NutrientLevels] = Field(None, description="Besin seviyeleri trafik ışığı (Yağ, şeker, tuz risk durumu)")


class ProductIngredients(BaseModel):
    """Ürünün içindekiler listesi, diyet ve alerjen analizi."""
    raw_text: Optional[str] = Field(None, description="Etiket üzerindeki orijinal içindekiler metni")
    items: List[str] = Field(default_factory=list, description="Ayıklanmış ve temizlenmiş içindekiler listesi")
    has_palm_oil: Optional[bool] = Field(None, description="Palm yağı içeriyor mu? (True/False/None)")
    is_vegan: Optional[bool] = Field(None, description="Vegan mı? (True/False/None)")
    is_vegetarian: Optional[bool] = Field(None, description="Vejetaryen mi? (True/False/None)")


class ProductImages(BaseModel):
    """Ürünün yüksek kaliteli ve optimize edilmiş görselleri."""
    front_url: Optional[str] = Field(None, description="Ürünün ön yüz ambalaj görseli")
    ingredients_url: Optional[str] = Field(None, description="İçindekiler listesi / etiket görseli")
    nutrition_url: Optional[str] = Field(None, description="Besin tablosu görseli")
    packaging_url: Optional[str] = Field(None, description="Ambalaj görseli")
    thumbnail_url: Optional[str] = Field(None, description="Küçük önizleme görseli")


class ProductHealthScores(BaseModel):
    """Uluslararası gıda sağlık, işlenmişlik ve çevre etki puanları."""
    nutriscore_grade: Optional[str] = Field(None, description="Nutri-Score Harfi (A, B, C, D, E)")
    nutriscore_score: Optional[int] = Field(None, description="Nutri-Score Sayısal Puanı")
    nutriscore_description: Optional[str] = Field(None, description="Nutri-Score Türkçe açıklaması")
    
    nova_group: Optional[int] = Field(None, description="NOVA İşlenmişlik Derecesi (1: İşlenmemiş, 4: Aşırı İşlenmiş)")
    nova_description: Optional[str] = Field(None, description="NOVA sınıflandırması Türkçe açıklaması")
    
    ecoscore_grade: Optional[str] = Field(None, description="Eco-Score Çevre Puanı Harfi (A, B, C, D, E)")
    ecoscore_score: Optional[int] = Field(None, description="Eco-Score Sayısal Değeri (0-100)")
    ecoscore_description: Optional[str] = Field(None, description="Eco-Score Türkçe açıklaması")


class ProductSafetyAlerts(BaseModel):
    """Tüketici sağlığı için kritik alerjenler, iz miktardakiler ve katkı maddeleri."""
    allergens: List[str] = Field(default_factory=list, description="İçerdiği alerjenler (Örn: Süt, Gluten, Soya)")
    traces: List[str] = Field(default_factory=list, description="Eser miktarda bulunabilecek maddeler (Örn: Fındık, Fıstık)")
    additives: List[str] = Field(default_factory=list, description="İçerdiği katkı maddeleri (E-kodları ve isimleri)")


class ProductCertifications(BaseModel):
    """Ürünün aldığı sertifikalar, kalite standartları ve ambalaj bilgileri."""
    labels: List[str] = Field(default_factory=list, description="Sertifikalar ve etiketler (Örn: TSE, Helal, Organik, vb.)")
    packaging_materials: List[str] = Field(default_factory=list, description="Ambalaj materyalleri (Geri dönüşüm, plastik, karton vb.)")


class ProductDetail(BaseModel):
    """Frontend için temizlenmiş, zenginleştirilmiş ürün detay modeli."""
    barcode: str = Field(..., description="Ürün barkod numarası (EAN-13, EAN-8 vb.)")
    product_name: str = Field(..., description="Ürün adı (Türkçe veya orijinal)")
    brand: Optional[str] = Field(None, description="Marka / Üretici firma adı")
    quantity: Optional[str] = Field(None, description="Net gramaj / miktar (Örn: '36 g', '1000 ml')")
    categories: List[str] = Field(default_factory=list, description="Kategori listesi")
    origin_country: Optional[str] = Field(None, description="Üretim / Menşei ülke")
    manufacturing_places: Optional[str] = Field(None, description="Üretim yeri veya fabrika bilgisi")
    
    images: ProductImages = Field(default_factory=ProductImages, description="Ürün görselleri")
    nutrition: ProductNutrition = Field(default_factory=ProductNutrition, description="Besin değerleri tablosu")
    ingredients: ProductIngredients = Field(default_factory=ProductIngredients, description="İçindekiler ve içerik analizi")
    health_scores: ProductHealthScores = Field(default_factory=ProductHealthScores, description="Sağlık, besleyicilik ve çevre skorları")
    safety_alerts: ProductSafetyAlerts = Field(default_factory=ProductSafetyAlerts, description="Alerjenler ve katkı maddeleri uyarıları")
    certifications: ProductCertifications = Field(default_factory=ProductCertifications, description="Sertifikalar ve kalite etiketleri")


class BarcodeAnalysisRequest(BaseModel):
    """Frontend'den gelen barkod sorgulama isteği."""
    barcode: str = Field(..., examples=["8690504135913"], description="Okutulan barkod numarası (örn: 8690504135913)")


class ProductAnalysisResponse(BaseModel):
    """API'nin frontend'e döndüğü standart yanıt şeması."""
    success: bool = Field(..., description="İşlem başarılı mı?")
    message: str = Field(..., description="Durum mesajı")
    barcode: str = Field(..., description="Sorgulanan barkod numarası")
    data: Optional[ProductDetail] = Field(None, description="Ayıklanmış ve temizlenmiş ürün verisi (Bulunamazsa null)")
