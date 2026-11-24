from typing import Optional, List, Dict, Any
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
    serving_quantity: Optional[float] = Field(None, description="Porsiyon miktarı (sayısal)")
    
    # 100 gram/ml değerleri
    energy_kcal_100g: Optional[float] = Field(None, description="100g Enerji (kcal)")
    energy_kj_100g: Optional[float] = Field(None, description="100g Enerji (kJ)")
    fat_100g: Optional[float] = Field(None, description="100g Yağ (g)")
    saturated_fat_100g: Optional[float] = Field(None, description="100g Doymuş Yağ (g)")
    carbohydrates_100g: Optional[float] = Field(None, description="100g Karbonhidrat (g)")
    sugars_100g: Optional[float] = Field(None, description="100g Şekerler (g)")
    added_sugars_100g: Optional[float] = Field(None, description="100g İlave Şeker (g)")
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
    added_sugars_serving: Optional[float] = Field(None, description="Porsiyon başına İlave Şeker (g)")
    fiber_serving: Optional[float] = Field(None, description="Porsiyon başına Lif (g)")
    proteins_serving: Optional[float] = Field(None, description="Porsiyon başına Protein (g)")
    salt_serving: Optional[float] = Field(None, description="Porsiyon başına Tuz (g)")
    sodium_serving: Optional[float] = Field(None, description="Porsiyon başına Sodyum (g)")

    fruits_vegetables_nuts_estimate_100g: Optional[float] = Field(None, description="Tahmini meyve, sebze, kuruyemiş oranı (%)")
    levels: Optional[NutrientLevels] = Field(None, description="Besin seviyeleri trafik ışığı (Yağ, şeker, tuz risk durumu)")
    additional_nutriments: Dict[str, Any] = Field(default_factory=dict, description="Üründe tespit edilen diğer tüm vitamin, mineral ve ek besin değerleri")


class StructuredIngredient(BaseModel):
    """Ayrıştırılmış detaylı içerik öğesi."""
    text: str = Field(..., description="Malzeme adı")
    id: Optional[str] = Field(None, description="Open Food Facts malzeme kimliği")
    percent_estimate: Optional[float] = Field(None, description="Tahmini yüzde oranı (%)")
    vegan: Optional[str] = Field(None, description="Veganlık durumu: yes, no, maybe")
    vegetarian: Optional[str] = Field(None, description="Vejetaryenlik durumu: yes, no, maybe")
    from_palm_oil: Optional[bool] = Field(None, description="Palm yağından mı üretilmiş?")
    sub_ingredients: List[str] = Field(default_factory=list, description="Alt malzemeler (varsa)")


class ProductIngredients(BaseModel):
    """Ürünün içindekiler listesi, diyet ve alerjen analizi."""
    raw_text: Optional[str] = Field(None, description="Etiket üzerindeki orijinal içindekiler metni")
    items: List[str] = Field(default_factory=list, description="Temizlenmiş içindekiler metin listesi")
    structured: List[StructuredIngredient] = Field(default_factory=list, description="Detaylı ayrıştırılmış içerikler (Yüzdeler, vegan/vejetaryen analizleri ile)")
    has_palm_oil: Optional[bool] = Field(None, description="Palm yağı içeriyor mu? (True/False/None)")
    is_vegan: Optional[bool] = Field(None, description="Vegan mı? (True/False/None)")
    is_vegetarian: Optional[bool] = Field(None, description="Vejetaryen mi? (True/False/None)")
    analysis_tags: List[str] = Field(default_factory=list, description="İçerik analiz etiketleri (Türkçe açıklamalar)")


class ProductImages(BaseModel):
    """Ürünün yüksek kaliteli ve optimize edilmiş görselleri."""
    front_url: Optional[str] = Field(None, description="Ürünün ön yüz ambalaj görseli")
    ingredients_url: Optional[str] = Field(None, description="İçindekiler listesi / etiket görseli")
    nutrition_url: Optional[str] = Field(None, description="Besin tablosu görseli")
    packaging_url: Optional[str] = Field(None, description="Ambalaj görseli")
    thumbnail_url: Optional[str] = Field(None, description="Küçük önizleme görseli")
    all_images: Dict[str, Any] = Field(default_factory=dict, description="Tüm boyutlar ve dillerdeki görsel linkleri haritası")


class NutriScoreBreakdown(BaseModel):
    """Nutri-Score puanlama detayları ve negatif/pozitif bileşenler."""
    score: Optional[int] = Field(None, description="Toplam Nutri-Score sayısal puanı")
    negative_points: Optional[int] = Field(None, description="Negatif puanlar (Kalori, doymuş yağ, şeker, tuz)")
    positive_points: Optional[int] = Field(None, description="Pozitif puanlar (Lif, protein, meyve/sebze oranı)")
    components: Optional[Dict[str, Any]] = Field(None, description="Puan hesaplama bileşenleri listesi")


class ProductHealthScores(BaseModel):
    """Uluslararası gıda sağlık, işlenmişlik ve çevre etki puanları."""
    nutriscore_grade: Optional[str] = Field(None, description="Nutri-Score Harfi (A, B, C, D, E)")
    nutriscore_score: Optional[int] = Field(None, description="Nutri-Score Sayısal Puanı")
    nutriscore_description: Optional[str] = Field(None, description="Nutri-Score Türkçe açıklaması")
    nutriscore_breakdown: Optional[NutriScoreBreakdown] = Field(None, description="Nutri-Score detaylı puanlama kırılımı")
    
    nova_group: Optional[int] = Field(None, description="NOVA İşlenmişlik Derecesi (1: İşlenmemiş, 4: Aşırı İşlenmiş)")
    nova_description: Optional[str] = Field(None, description="NOVA sınıflandırması Türkçe açıklaması")
    
    ecoscore_grade: Optional[str] = Field(None, description="Eco-Score Çevre Puanı Harfi (A, B, C, D, E)")
    ecoscore_score: Optional[int] = Field(None, description="Eco-Score Sayısal Değeri (0-100)")
    ecoscore_description: Optional[str] = Field(None, description="Eco-Score Türkçe açıklaması")
    ecoscore_data: Optional[Dict[str, Any]] = Field(None, description="Çevresel etki ve karbon ayak izi detayları")


class ProductSafetyAlerts(BaseModel):
    """Tüketici sağlığı için kritik alerjenler, iz miktardakiler ve katkı maddeleri."""
    allergens: List[str] = Field(default_factory=list, description="İçerdiği alerjenler (Örn: Süt, Gluten, Soya)")
    traces: List[str] = Field(default_factory=list, description="Eser miktarda bulunabilecek maddeler (Örn: Fındık, Fıstık)")
    additives: List[str] = Field(default_factory=list, description="İçerdiği katkı maddeleri (E-kodları ve isimleri)")
    additives_count: int = Field(0, description="Katkı maddesi sayısı")


class ProductCertifications(BaseModel):
    """Ürünün aldığı sertifikalar, kalite standartları ve ambalaj bilgileri."""
    labels: List[str] = Field(default_factory=list, description="Sertifikalar ve etiketler (Örn: TSE, Helal, Organik, vb.)")
    packaging_materials: List[str] = Field(default_factory=list, description="Ambalaj materyalleri (Geri dönüşüm, plastik, karton vb.)")
    packagings: List[Dict[str, Any]] = Field(default_factory=list, description="Ambalaj detayları ve parçaları")
    emb_codes: Optional[str] = Field(None, description="Paketleme ve fabrika kodları")


class ProductDetail(BaseModel):
    """Frontend için temizlenmiş, zenginleştirilmiş ürün detay modeli."""
    barcode: str = Field(..., description="Ürün barkod numarası (EAN-13, EAN-8 vb.)")
    product_name: str = Field(..., description="Ürün adı (Türkçe veya orijinal)")
    generic_name: Optional[str] = Field(None, description="Genel ürün tanımı")
    brand: Optional[str] = Field(None, description="Marka adı")
    brand_owner: Optional[str] = Field(None, description="Markanın sahibi / tescilli şirket")
    quantity: Optional[str] = Field(None, description="Net gramaj / miktar (Örn: '36 g', '1000 ml')")
    categories: List[str] = Field(default_factory=list, description="Kategori listesi")
    categories_hierarchy: List[str] = Field(default_factory=list, description="Kategori hiyerarşi etiketleri")
    origin_country: Optional[str] = Field(None, description="Üretim / Menşei ülke")
    origins: Optional[str] = Field(None, description="Hammadde menşei")
    manufacturing_places: Optional[str] = Field(None, description="Üretim yeri veya fabrika bilgisi")
    stores: List[str] = Field(default_factory=list, description="Satıldığı mağazalar veya market zincirleri")
    
    images: ProductImages = Field(default_factory=ProductImages, description="Ürün görselleri")
    nutrition: ProductNutrition = Field(default_factory=ProductNutrition, description="Besin değerleri tablosu")
    ingredients: ProductIngredients = Field(default_factory=ProductIngredients, description="İçindekiler ve içerik analizi")
    health_scores: ProductHealthScores = Field(default_factory=ProductHealthScores, description="Sağlık, besleyicilik ve çevre skorları")
    safety_alerts: ProductSafetyAlerts = Field(default_factory=ProductSafetyAlerts, description="Alerjenler ve katkı maddeleri uyarıları")
    certifications: ProductCertifications = Field(default_factory=ProductCertifications, description="Sertifikalar ve kalite etiketleri")
    
    raw_openfoodfacts: Optional[Dict[str, Any]] = Field(None, description="İstendiği takdirde Open Food Facts'in tüm filtrelenmemiş 240+ ham alanını içeren obje")


class BarcodeAnalysisRequest(BaseModel):
    """Frontend'den gelen barkod sorgulama isteği."""
    barcode: str = Field(..., examples=["8690504135913"], description="Okutulan barkod numarası (örn: 8690504135913)")
    include_raw: bool = Field(False, description="Open Food Facts'in tüm filtrelenmemiş ham JSON verisini de yanıta dahil et (true/false)")


class ProductAnalysisResponse(BaseModel):
    """API'nin frontend'e döndüğü standart yanıt şeması."""
    success: bool = Field(..., description="İşlem başarılı mı?")
    message: str = Field(..., description="Durum mesajı")
    barcode: str = Field(..., description="Sorgulanan barkod numarası")
    data: Optional[ProductDetail] = Field(None, description="Ayıklanmış ve temizlenmiş ürün verisi (Bulunamazsa null)")
