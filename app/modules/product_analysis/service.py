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
    StructuredIngredient,
    NutriScoreBreakdown,
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

ANALYSIS_TAG_TRANSLATIONS = {
    "en:palm-oil": "Palm yağı içerir",
    "en:palm-oil-free": "Palm yağı içermez",
    "en:palm-oil-content-unknown": "Palm yağı içeriği belirsiz",
    "en:vegan": "Vegan",
    "en:non-vegan": "Vegan değil",
    "en:vegan-status-unknown": "Veganlık durumu belirsiz",
    "en:vegetarian": "Vejetaryen",
    "en:non-vegetarian": "Vejetaryen değil",
    "en:vegetarian-status-unknown": "Vejetaryenlik durumu belirsiz",
}

STANDARD_NUTRIMENT_PREFIXES = {
    "energy", "energy-kcal", "energy-kj", "fat", "saturated-fat",
    "carbohydrates", "sugars", "added-sugars", "fiber", "proteins",
    "salt", "sodium", "fruits-vegetables-nuts-estimate-from-ingredients",
    "fruits-vegetables-legumes-estimate-from-ingredients"
}


class ProductAnalysisService:
    @staticmethod
    def _clean_tag(tag: str) -> str:
        """'en:pure-cocoa-butter' veya 'tr:fındık' gibi tag'leri temizler."""
        if not tag:
            return ""
        cleaned = re.sub(r"[\x00-\x1f]", "", tag.strip())
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
            if "tr" in displays and displays["tr"]:
                return displays["tr"]
            if "en" in displays and displays["en"]:
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
        items = re.split(r",|\.", raw_text)
        cleaned_items = []
        for it in items:
            t = it.strip(" ()*[]")
            if t and len(t) > 1 and not t.isdigit():
                cleaned_items.append(t)
        return cleaned_items

    @classmethod
    def clean_and_normalize(cls, raw_data: Dict[str, Any], include_raw: bool = False) -> Optional[ProductDetail]:
        """Open Food Facts verisini tüm detaylarıyla zenginleştirip standart modele dönüştürür."""
        if not raw_data or raw_data.get("status") != 1:
            return None

        p = raw_data.get("product", {})
        if not p:
            return None

        barcode = p.get("code") or raw_data.get("code") or ""
        
        # Ürün adı ve genel tanım
        raw_name = (
            p.get("product_name_tr")
            or p.get("product_name")
            or p.get("generic_name_tr")
            or p.get("generic_name")
        )
        nutriments = p.get("nutriments", {})
        if not raw_name and not p.get("ingredients_text") and not nutriments:
            return None

        product_name = (raw_name or "İsimsiz Ürün").strip()
        generic_name = p.get("generic_name_tr") or p.get("generic_name") or None
        brand = p.get("brands") or None
        brand_owner = p.get("brand_owner") or p.get("brand_owner_imported") or None
        quantity = p.get("quantity") or None
        serving_size = p.get("serving_size") or None
        serving_qty = None
        if p.get("serving_quantity") is not None:
            try:
                serving_qty = float(p.get("serving_quantity"))
            except (ValueError, TypeError):
                pass
        
        # Kategoriler (Tüm kategorileri ve hiyerarşi etiketlerini al)
        categories = []
        raw_cats = p.get("categories_tags") or []
        for cat in raw_cats:
            clean_c = cls._clean_tag(cat)
            if clean_c and clean_c not in categories:
                categories.append(clean_c)

        categories_hierarchy = p.get("categories_hierarchy") or []

        # Ülke / Menşei / Mağazalar
        origin_country = p.get("countries") or None
        origins = p.get("origins") or None
        manufacturing_places = p.get("manufacturing_places") or None
        
        stores = []
        if p.get("stores"):
            stores = [s.strip() for s in p.get("stores").split(",") if s.strip()]
        elif p.get("stores_tags"):
            stores = [cls._clean_tag(s) for s in p.get("stores_tags")]

        # 1. Görseller
        selected_images = p.get("selected_images", {})
        images = ProductImages(
            front_url=cls._extract_image_url(selected_images, "front", p.get("image_front_url") or p.get("image_url")),
            ingredients_url=cls._extract_image_url(selected_images, "ingredients", p.get("image_ingredients_url")),
            nutrition_url=cls._extract_image_url(selected_images, "nutrition", p.get("image_nutrition_url")),
            packaging_url=cls._extract_image_url(selected_images, "packaging", p.get("image_packaging_url")),
            thumbnail_url=p.get("image_front_small_url") or p.get("image_small_url") or None,
            all_images=selected_images or {},
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

        # 3. Ek Besin Değerleri (Hiçbir besin değeri dışarıda kalmasın)
        additional_nutriments = {}
        for nk, nv in nutriments.items():
            if not isinstance(nv, (int, float)):
                continue
            # Temel besinler haricindeki ek değerleri topla
            base_k = re.sub(r"_(100g|serving|unit|value|modifier)$", "", nk)
            if base_k not in STANDARD_NUTRIMENT_PREFIXES and not nk.endswith(("_unit", "_modifier", "_value")):
                additional_nutriments[nk] = nv

        nutrition = ProductNutrition(
            serving_size=serving_size,
            serving_quantity=serving_qty,
            # 100g
            energy_kcal_100g=nutriments.get("energy-kcal_100g"),
            energy_kj_100g=nutriments.get("energy-kj_100g"),
            fat_100g=nutriments.get("fat_100g"),
            saturated_fat_100g=nutriments.get("saturated-fat_100g"),
            carbohydrates_100g=nutriments.get("carbohydrates_100g"),
            sugars_100g=nutriments.get("sugars_100g"),
            added_sugars_100g=nutriments.get("added-sugars_100g"),
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
            added_sugars_serving=nutriments.get("added-sugars_serving"),
            fiber_serving=nutriments.get("fiber_serving"),
            proteins_serving=nutriments.get("proteins_serving"),
            salt_serving=nutriments.get("salt_serving"),
            sodium_serving=nutriments.get("sodium_serving"),
            fruits_vegetables_nuts_estimate_100g=nutriments.get("fruits-vegetables-nuts-estimate-from-ingredients_100g"),
            levels=levels,
            additional_nutriments=additional_nutriments,
        )

        # 4. İçindekiler (Hem metin hem zengin yapısal liste)
        ingredients_raw = (
            p.get("ingredients_text_tr")
            or p.get("ingredients_text")
            or None
        )
        ingredients_items = cls._parse_ingredients_list(ingredients_raw)

        structured_ingredients = []
        for ing in p.get("ingredients", []):
            if not isinstance(ing, dict) or not ing.get("text"):
                continue
            pct = ing.get("percent_estimate")
            if pct is not None:
                try:
                    pct = round(float(pct), 2)
                except (ValueError, TypeError):
                    pct = None
            
            sub_ings = []
            for sub in ing.get("ingredients", []):
                if isinstance(sub, dict) and sub.get("text"):
                    sub_ings.append(sub.get("text"))

            is_from_palm = None
            if ing.get("from_palm_oil") == "yes":
                is_from_palm = True
            elif ing.get("from_palm_oil") == "no":
                is_from_palm = False

            structured_ingredients.append(
                StructuredIngredient(
                    text=ing.get("text", "").strip(),
                    id=ing.get("id"),
                    percent_estimate=pct,
                    vegan=ing.get("vegan"),
                    vegetarian=ing.get("vegetarian"),
                    from_palm_oil=is_from_palm,
                    sub_ingredients=sub_ings,
                )
            )

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

        analysis_tags_tr = [
            ANALYSIS_TAG_TRANSLATIONS.get(t, cls._clean_tag(t))
            for t in analysis_tags
        ]

        ingredients = ProductIngredients(
            raw_text=ingredients_raw,
            items=ingredients_items,
            structured=structured_ingredients,
            has_palm_oil=has_palm,
            is_vegan=is_vegan,
            is_vegetarian=is_veg,
            analysis_tags=analysis_tags_tr,
        )

        # 5. Sağlık ve Kalite Skorları (Nutri-Score puan kırılımı dahil)
        nutriscore_grade = p.get("nutriscore_grade")
        if nutriscore_grade and isinstance(nutriscore_grade, str):
            nutriscore_grade = nutriscore_grade.lower()
        nutriscore_score = p.get("nutriscore_score")
        nutriscore_desc = NUTRISCORE_DESCRIPTIONS.get(nutriscore_grade) if nutriscore_grade else None

        nutriscore_breakdown = None
        nd = p.get("nutriscore_data")
        if nd and isinstance(nd, dict):
            nutriscore_breakdown = NutriScoreBreakdown(
                score=nd.get("score"),
                negative_points=nd.get("negative_points"),
                positive_points=nd.get("positive_points"),
                components=nd.get("components"),
            )

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
            nutriscore_breakdown=nutriscore_breakdown,
            nova_group=nova_group,
            nova_description=nova_desc,
            ecoscore_grade=ecoscore_grade.upper() if ecoscore_grade else None,
            ecoscore_score=ecoscore_score,
            ecoscore_description=ecoscore_desc,
            ecoscore_data=p.get("ecoscore_data"),
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
            additives_count=len(additives),
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

        packagings = p.get("packagings") or []

        certifications = ProductCertifications(
            labels=labels,
            packaging_materials=packaging_materials,
            packagings=packagings if isinstance(packagings, list) else [],
            emb_codes=p.get("emb_codes") or None,
        )

        # 8. Ham Veri (İstendiğinde tam orijinal Open Food Facts JSON'u)
        raw_off = p if include_raw else None

        return ProductDetail(
            barcode=str(barcode),
            product_name=product_name,
            generic_name=generic_name,
            brand=brand,
            brand_owner=brand_owner,
            quantity=quantity,
            categories=categories,
            categories_hierarchy=categories_hierarchy,
            origin_country=origin_country,
            origins=origins,
            manufacturing_places=manufacturing_places,
            stores=stores,
            images=images,
            nutrition=nutrition,
            ingredients=ingredients,
            health_scores=health_scores,
            safety_alerts=safety_alerts,
            certifications=certifications,
            raw_openfoodfacts=raw_off,
        )

    @classmethod
    async def fetch_product_by_barcode(cls, barcode: str, include_raw: bool = False) -> Optional[ProductDetail]:
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
            return cls.clean_and_normalize(data, include_raw=include_raw)
