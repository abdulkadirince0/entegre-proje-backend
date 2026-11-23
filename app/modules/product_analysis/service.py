import re
import httpx
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.modules.product_analysis.schemas import (
    ProductDetail,
    ProductImages,
    ProductNutrition,
    ProductIngredients,
    ProductHealthScores,
    ProductSafetyAlerts,
    ProductCertifications,
    NutrientLevels,
    NutrientLevelDetail,
)

# Alerjenlerin Türkçe karşılıkları
ALLERGEN_TRANSLATIONS: Dict[str, str] = {
    "gluten": "Gluten",
    "milk": "Süt / Laktoz",
    "eggs": "Yumurta",
    "nuts": "Sert Kabuklu Yemişler",
    "peanuts": "Yer Fıstığı",
    "soybeans": "Soya",
    "fish": "Balık",
    "crustaceans": "Kabuklular",
    "mustard": "Hardal",
    "sesame-seeds": "Susam",
    "celery": "Kereviz",
    "lupin": "Acıbakla",
    "molluscs": "Yumuşakçalar",
    "sulphur-dioxide-and-sulphites": "Kükürt Dioksit ve Sülfitler",
    "nuts-and-peanuts": "Fındık ve Fıstık",
}

NUTRIENT_LEVEL_MAPPING = {
    "low": ("Düşük", "green"),
    "moderate": ("Orta", "yellow"),
    "high": ("Yüksek", "red"),
}

NUTRISCORE_DESCRIPTIONS = {
    "a": "Çok yüksek besin kalitesi (En sağlıklı kategori)",
    "b": "İyi besin kalitesi",
    "c": "Dengeli besin kalitesi",
    "d": "Düşük besin kalitesi",
    "e": "Çok düşük besin kalitesi (Sık veya fazla tüketilmesi önerilmez)",
}

NOVA_DESCRIPTIONS = {
    1: "İşlenmemiş veya minimum işlenmiş gıda (Doğal formunda)",
    2: "İşlenmiş mutfak malzemesi (Tuz, yağ, şeker gibi)",
    3: "İşlenmiş gıda (Konserve, peynir, taze ekmek vb.)",
    4: "Aşırı işlenmiş gıda (Ultra-işlenmiş gıda, endüstriyel katkılar içerir)",
}

ECOSCORE_DESCRIPTIONS = {
    "a": "Çok düşük çevresel etki (Çevre dostu)",
    "b": "Düşük çevresel etki",
    "c": "Orta düzeyde çevresel etki",
    "d": "Yüksek çevresel etki",
    "e": "Çok yüksek çevresel etki (Gezegene maliyeti yüksek)",
}


class ProductAnalysisService:
    @staticmethod
    def _clean_tag(tag: str) -> str:
        """'en:pure-cocoa-butter' veya 'tr:fındık' gibi tag'leri temizler."""
        if not tag:
            return ""
        # Kontrol karakterlerini temizle (\x1f vb.)
        cleaned = re.sub(r"[\x00-\x1f]", "", tag.strip())
        # Tekrarlanan dil ön eklerini temizle (örn: en:en:Nuts-and-peanuts -> Nuts-and-peanuts)
        cleaned = re.sub(r"^(?:[a-z]{2}:)+", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace("-", " ").strip()
        return cleaned.title()

    @classmethod
    def _translate_tag(cls, tag: str, translation_dict: Dict[str, str]) -> str:
        """Tag'i sözlükte varsa Türkçeye çevirir, yoksa temiz halini döner."""
        raw_key = re.sub(r"[\x00-\x1f]", "", tag.strip().lower())
        raw_key = re.sub(r"^(?:[a-z]{2}:)+", "", raw_key).strip()
        if raw_key in translation_dict:
            return translation_dict[raw_key]
        return cls._clean_tag(tag)

    @staticmethod
    def _extract_image_url(selected_images: dict, key: str, fallback_url: Optional[str]) -> Optional[str]:
        """Dil önceliğine göre görsel linkini çeker (Önce TR, sonra EN, sonra fallback)."""
        if selected_images and key in selected_images:
            displays = selected_images[key].get("display", {})
            if "tr" in displays:
                return displays["tr"]
            if "en" in displays:
                return displays["en"]
            for lang, url in displays.items():
                if url:
                    return url
        return fallback_url

    @staticmethod
    def _parse_ingredients_list(raw_text: Optional[str]) -> List[str]:
        """İçindekiler metnini temizleyip madde madde listeye ayırır."""
        if not raw_text:
            return []
        # Parantez içi virgüllerle bölmeyi engellemek için akıllı temizlik
        # Temel ayrıştırma virgül ve noktalı virgüllere göre
        items = re.split(r",|\.", raw_text)
        cleaned_items = []
        for it in items:
            t = it.strip(" ()*[]")
            if t and len(t) > 1 and not t.isdigit():
                cleaned_items.append(t)
        return cleaned_items

    @classmethod
    def clean_and_normalize(cls, raw_data: Dict[str, Any]) -> Optional[ProductDetail]:
        """Open Food Facts'in devasa ham JSON çıktısını temizleyip standart modele dönüştürür."""
        if not raw_data or raw_data.get("status") != 1:
            return None

        p = raw_data.get("product", {})
        if not p:
            return None

        barcode = p.get("code") or raw_data.get("code") or ""
        
        # Ürün adı (Türkçe öncelikli)
        product_name = (
            p.get("product_name_tr")
            or p.get("product_name")
            or p.get("generic_name_tr")
            or p.get("generic_name")
            or "İsimsiz Ürün"
        ).strip()

        brand = p.get("brands") or p.get("brand_owner") or None
        quantity = p.get("quantity") or None
        serving_size = p.get("serving_size") or None
        
        # Kategoriler
        categories = []
        raw_cats = p.get("categories_tags") or []
        for cat in raw_cats[:6]:  # Çok uzamaması için en belirgin 6 kategori
            categories.append(cls._clean_tag(cat))

        # Ülke / Menşei
        origin_country = p.get("countries") or None
        manufacturing_places = p.get("manufacturing_places") or None

        # 1. Görseller
        selected_images = p.get("selected_images", {})
        images = ProductImages(
            front_url=cls._extract_image_url(selected_images, "front", p.get("image_front_url") or p.get("image_url")),
            ingredients_url=cls._extract_image_url(selected_images, "ingredients", p.get("image_ingredients_url")),
            nutrition_url=cls._extract_image_url(selected_images, "nutrition", p.get("image_nutrition_url")),
            packaging_url=cls._extract_image_url(selected_images, "packaging", p.get("image_packaging_url")),
            thumbnail_url=p.get("image_front_small_url") or p.get("image_small_url") or None,
        )

        # 2. Besin Seviyeleri (Trafik Işıkları)
        raw_levels = p.get("nutrient_levels", {})
        def make_level_detail(level_key: str) -> Optional[NutrientLevelDetail]:
            val = raw_levels.get(level_key)
            if val and val in NUTRIENT_LEVEL_MAPPING:
                lbl, col = NUTRIENT_LEVEL_MAPPING[val]
                return NutrientLevelDetail(raw_level=val, label_tr=lbl, color=col)
            return None

        levels = NutrientLevels(
            fat=make_level_detail("fat"),
            saturated_fat=make_level_detail("saturated-fat"),
            sugars=make_level_detail("sugars"),
            salt=make_level_detail("salt"),
        )

        # 3. Besin Değerleri Tablosu
        nutriments = p.get("nutriments", {})
        nutrition = ProductNutrition(
            serving_size=serving_size,
            # 100g
            energy_kcal_100g=nutriments.get("energy-kcal_100g"),
            energy_kj_100g=nutriments.get("energy-kj_100g"),
            fat_100g=nutriments.get("fat_100g"),
            saturated_fat_100g=nutriments.get("saturated-fat_100g"),
            carbohydrates_100g=nutriments.get("carbohydrates_100g"),
            sugars_100g=nutriments.get("sugars_100g"),
            fiber_100g=nutriments.get("fiber_100g"),
            proteins_100g=nutriments.get("proteins_100g"),
            salt_100g=nutriments.get("salt_100g"),
            sodium_100g=nutriments.get("sodium_100g"),
            # Porsiyon
            energy_kcal_serving=nutriments.get("energy-kcal_serving"),
            energy_kj_serving=nutriments.get("energy-kj_serving"),
            fat_serving=nutriments.get("fat_serving"),
            saturated_fat_serving=nutriments.get("saturated-fat_serving"),
            carbohydrates_serving=nutriments.get("carbohydrates_serving"),
            sugars_serving=nutriments.get("sugars_serving"),
            fiber_serving=nutriments.get("fiber_serving"),
            proteins_serving=nutriments.get("proteins_serving"),
            salt_serving=nutriments.get("salt_serving"),
            sodium_serving=nutriments.get("sodium_serving"),
            levels=levels,
        )

        # 4. İçindekiler
        ingredients_raw = (
            p.get("ingredients_text_tr")
            or p.get("ingredients_text")
            or None
        )
        ingredients_items = cls._parse_ingredients_list(ingredients_raw)

        # Palm yağı, vegan, vejetaryen analizi
        analysis_tags = p.get("ingredients_analysis_tags", [])
        has_palm = None
        if "en:palm-oil" in analysis_tags:
            has_palm = True
        elif "en:palm-oil-free" in analysis_tags:
            has_palm = False
        elif ingredients_raw and "palm" in ingredients_raw.lower():
            has_palm = True

        is_vegan = None
        if "en:vegan" in analysis_tags:
            is_vegan = True
        elif "en:non-vegan" in analysis_tags:
            is_vegan = False

        is_veg = None
        if "en:vegetarian" in analysis_tags:
            is_veg = True
        elif "en:non-vegetarian" in analysis_tags:
            is_veg = False

        ingredients = ProductIngredients(
            raw_text=ingredients_raw,
            items=ingredients_items,
            has_palm_oil=has_palm,
            is_vegan=is_vegan,
            is_vegetarian=is_veg,
        )

        # 5. Sağlık ve Kalite Skorları
        nutriscore_grade = p.get("nutriscore_grade")
        if nutriscore_grade and isinstance(nutriscore_grade, str):
            nutriscore_grade = nutriscore_grade.lower()
        nutriscore_score = p.get("nutriscore_score")
        nutriscore_desc = NUTRISCORE_DESCRIPTIONS.get(nutriscore_grade) if nutriscore_grade else None

        nova_group = p.get("nova_group")
        if nova_group is not None:
            try:
                nova_group = int(nova_group)
            except (ValueError, TypeError):
                nova_group = None
        nova_desc = NOVA_DESCRIPTIONS.get(nova_group) if nova_group else None

        ecoscore_grade = p.get("ecoscore_grade")
        if ecoscore_grade and isinstance(ecoscore_grade, str):
            ecoscore_grade = ecoscore_grade.lower()
        ecoscore_score = p.get("ecoscore_score")
        ecoscore_desc = ECOSCORE_DESCRIPTIONS.get(ecoscore_grade) if ecoscore_grade else None

        health_scores = ProductHealthScores(
            nutriscore_grade=nutriscore_grade.upper() if nutriscore_grade else None,
            nutriscore_score=nutriscore_score,
            nutriscore_description=nutriscore_desc,
            nova_group=nova_group,
            nova_description=nova_desc,
            ecoscore_grade=ecoscore_grade.upper() if ecoscore_grade else None,
            ecoscore_score=ecoscore_score,
            ecoscore_description=ecoscore_desc,
        )

        # 6. Alerjenler ve Katkı Maddeleri
        allergens = []
        for tag in p.get("allergens_tags", []):
            clean_name = cls._translate_tag(tag, ALLERGEN_TRANSLATIONS)
            if clean_name and clean_name not in allergens:
                allergens.append(clean_name)

        traces = []
        for tag in p.get("traces_tags", []):
            clean_name = cls._translate_tag(tag, ALLERGEN_TRANSLATIONS)
            if clean_name and clean_name not in traces:
                traces.append(clean_name)

        additives = []
        for tag in p.get("additives_tags", []):
            clean_add = cls._clean_tag(tag)
            if clean_add and clean_add not in additives:
                additives.append(clean_add)

        safety_alerts = ProductSafetyAlerts(
            allergens=allergens,
            traces=traces,
            additives=additives,
        )

        # 7. Sertifikalar ve Kalite Etiketleri
        labels = []
        for tag in p.get("labels_tags", []):
            clean_label = cls._clean_tag(tag)
            if clean_label and clean_label not in labels:
                labels.append(clean_label)

        packaging_materials = []
        for tag in p.get("packaging_tags", []):
            clean_pkg = cls._clean_tag(tag)
            if clean_pkg and clean_pkg not in packaging_materials:
                packaging_materials.append(clean_pkg)

        certifications = ProductCertifications(
            labels=labels,
            packaging_materials=packaging_materials,
        )

        return ProductDetail(
            barcode=str(barcode),
            product_name=product_name,
            brand=brand,
            quantity=quantity,
            categories=categories,
            origin_country=origin_country,
            manufacturing_places=manufacturing_places,
            images=images,
            nutrition=nutrition,
            ingredients=ingredients,
            health_scores=health_scores,
            safety_alerts=safety_alerts,
            certifications=certifications,
        )

    @classmethod
    async def fetch_product_by_barcode(cls, barcode: str) -> Optional[ProductDetail]:
        """Open Food Facts API üzerinden barkod sorgular ve temizlenmiş ürün nesnesi döner."""
        clean_barcode = barcode.strip().replace(" ", "")
        url = f"{settings.OPENFOODFACTS_BASE_URL}/{clean_barcode}.json"
        headers = {"User-Agent": settings.OPENFOODFACTS_USER_AGENT}

        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            return cls.clean_and_normalize(data)
