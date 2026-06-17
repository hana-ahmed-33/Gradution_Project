"""
NLP service — transaction extraction and classification.
Supports Arabic (Egyptian dialect + MSA) and English.
"""
import re
import time
import uuid
from typing import List, Optional, Tuple

from app.core.logging import get_logger
from app.utils.text_utils import (
    normalize_arabic_text, extract_amounts_from_text,
    split_text_into_segments, detect_language, ACTION_VERBS, _NUMBER_WORDS,
)
from app.utils.cache import cached_text_analysis
from app.utils.content_filter import content_filter
from app.models.domain import Transaction, TransactionType
from app.models.responses import TransactionDetail, FinancialSummary, AnalysisResult
from app.config import INCOME_KEYWORDS, EXPENSE_KEYWORDS
from app.services.ml_service import smart_predictor
from app.services.database_service import database_service
from app.exceptions import ValidationError, NLPProcessingError

logger = get_logger("nlp_service")


# ══════════════════════════════════════════════════════════════
#  KEYWORD MAPS  (used for both classification & item extraction)
# ══════════════════════════════════════════════════════════════

# Each entry: category → set of keywords (Arabic + English)
# Order matters for RULE 0 — more specific categories come first.

CATEGORY_KEYWORDS: dict = {

    'Clothes & Fashion': {
        'فستان', 'فستين', 'فساتين', 'بلوزة', 'بلوزه', 'بلوز',
        'ملابس', 'هدوم', 'لبس', 'قميص', 'تيشرت', 'تيشيرت',
        'بنطلون', 'بنطال', 'جينز', 'شورت', 'تنورة', 'جيبة',
        'جاكت', 'جاكيت', 'معطف', 'بلوفر', 'سويتر',
        'جزمة', 'حذاء', 'احذية', 'سنيكر', 'شبشب',
        'شنطة', 'حقيبة', 'محفظة',
        'اكسسوار', 'اكسسوارات', 'اكسسورات', 'اكسسواري',
        'ساعة', 'نظارة', 'قبعة',
        'dress', 'blouse', 'shirt', 't-shirt', 'pants', 'jeans',
        'shorts', 'skirt', 'jacket', 'coat', 'sweater',
        'shoes', 'sneakers', 'bag', 'handbag', 'wallet',
        'accessories', 'watch', 'glasses', 'hat', 'clothes', 'fashion',
    },

    'Health & Beauty': {
        'دواء', 'دوا', 'دوه', 'حبوب', 'كبسول', 'شراب دواء',
        'صيدلية', 'صيدليه', 'اجزاخانه',
        'دكتور', 'طبيب', 'كشف', 'عيادة', 'مستشفى', 'مستشفي',
        'تحليل', 'اشعة', 'اشعه', 'سكر', 'ضغط',
        'فيتامين', 'مكمل', 'بروتين',
        'عطر', 'برفان', 'ديو', 'مكياج', 'ميك اب', 'رمش', 'ظل',
        'كريم', 'لوشن', 'سيروم', 'مرطب',
        'شامبو', 'شامبوه', 'بلسم', 'جل شعر',
        'صابون', 'غسيل وجه', 'كلينزر', 'تونر',
        'حلاقة', 'حلق', 'كوافير', 'سبا', 'نيل',
        'medicine', 'drug', 'tablet', 'capsule',
        'doctor', 'clinic', 'hospital', 'pharmacy',
        'vitamin', 'supplement', 'protein',
        'perfume', 'deodorant', 'makeup', 'cream', 'lotion',
        'shampoo', 'conditioner', 'soap', 'skincare',
        'haircut', 'salon', 'spa', 'nail',
    },

    'Bills & Utilities': {
        'كهرباء', 'كهربا', 'كهرباية',
        'مياه', 'ميه', 'مي',
        'غاز', 'اسطوانة', 'اسطوانه',
        'انترنت', 'نت', 'واي فاي', 'راوتر',
        'موبايل', 'تليفون', 'تلفون', 'خط',
        'ايجار', 'إيجار', 'شقة', 'إيجار شقة',
        'قسط', 'اقساط',
        'اشتراك', 'نتفليكس', 'سبوتيفاي', 'يوتيوب برميوم',
        'فاتورة', 'فاتوره',
        'صيانة', 'إصلاح', 'تصليح',
        'تنظيف', 'نضافة', 'كلينينج',
        'electricity', 'water', 'gas', 'internet', 'wifi',
        'mobile', 'phone', 'line', 'subscription',
        'rent', 'bill', 'invoice',
        'maintenance', 'repair', 'cleaning', 'service',
        'netflix', 'spotify',
    },

    'Transportation': {
        'اوبر', 'أوبر', 'uber',
        'كريم', 'careem',
        'تاكسي', 'taxi', 'cab',
        'مترو', 'metro',
        'اتوبيس', 'باص', 'bus',
        'ميكروباص', 'ميني باص',
        'توكتوك',
        'قطار', 'قطر', 'train',
        'بنزين', 'وقود', 'سولار', 'diesel', 'fuel', 'petrol', 'gas station',
        'تذكرة', 'تسكرة', 'ticket',
        'اجرة', 'fare',
    },

    'Food & Drinks': {
        # eating verbs
        'كلت', 'اكلت', 'شربت', 'اتغديت', 'اتعشيت', 'فطرت',
        'ate', 'drank', 'eaten',
        # food items
        'اكل', 'طعام', 'وجبة', 'وجبه',
        'فول', 'طعمية', 'فلافل', 'كشري',
        'شاورما', 'shawarma', 'كباب', 'كفتة',
        'فرخة', 'فراخ', 'دجاج', 'chicken',
        'لحمة', 'لحم', 'meat', 'beef',
        'سمك', 'fish',
        'بيتزا', 'pizza', 'برجر', 'burger', 'سندوتش', 'sandwich',
        'سلطة', 'salad',
        'بطاطس', 'بطاطا', 'chips', 'fries',
        'خضار', 'خضروات', 'vegetables',
        'فاكهة', 'فواكه', 'fruits',
        'لبن', 'حليب', 'milk',
        'جبنة', 'جبن', 'cheese',
        'بيض', 'eggs',
        'عيش', 'خبز', 'bread',
        'رز', 'أرز', 'rice', 'مكرونة', 'pasta',
        'سكر', 'sugar', 'زيت', 'oil',
        'شوكولاتة', 'شوكولاته', 'chocolate',
        'بسكويت', 'cookies', 'كيك', 'cake',
        'شيبس', 'شابسي', 'snacks',
        'حلويات', 'candy', 'sweets',
        # restaurants & fast food chains
        'مطعم', 'restaurant',
        'ماكدونالدز', 'ماكدونالز', 'مكدونلدز', 'مكدونلز', 'ماكدو', 'macdonald', 'mcdonalds', "mcdonald's",
        'كنتاكي', 'kfc',
        'برجر كينج', 'burger king',
        'بيتزا هت', 'pizza hut',
        'دومينوز', 'dominos', "domino's",
        'هارديز', 'hardees', "hardee's",
        'صب واي', 'subway',
        'ليتل سيزارز', 'little caesars',
        'بوباي', 'popeyes',
        'شيلي', 'chilis', "chili's",
        'تشيز كيك فاكتوري', 'cheesecake factory',
        # cafes
        'كافيه', 'كافيه', 'قهوة', 'قهوه', 'coffee', 'cafe',
        'كوستا', 'costa', 'ستارباكس', 'starbucks',
        'تيم هورتونز', 'tim hortons',
        'دانكن', 'dunkin',
        # drinks
        'شاي', 'tea',
        'عصير', 'juice',
        'مشروب', 'drink',
        'مياه معدنية', 'ميه معدنية', 'water',
        'بيبسي', 'pepsi',
        'كوكاكولا', 'كوكا', 'كولا', 'coca', 'cola',
        'سبرايت', 'sprite',
        'فانتا', 'fanta',
        'red bull', 'energy drink',
    },

    'Entertainment': {
        'سينما', 'cinema', 'movie', 'film', 'فيلم',
        'مسرح', 'حفلة', 'حفل', 'كونسيرت', 'concert',
        'جيم', 'gym', 'نادي', 'club',
        'بلايستيشن', 'xbox', 'game', 'لعبة', 'العاب',
        'كتاب', 'book', 'مجلة', 'magazine',
        'رياضة', 'sports', 'ملعب', 'stadium',
        'سفاري', 'zoo', 'حديقة حيوان',
        'ملاهي', 'amusement',
    },

    'Salary & Income': {
        'مرتب', 'راتب', 'معاش',
        'استلمت مرتب', 'استلمت راتب', 'قبضت مرتب', 'قبضت راتب',
        'مكافأة', 'بونص', 'bonus',
        'حافز', 'عمولة', 'commission',
        'ارباح', 'profit',
        'دخل', 'income', 'salary', 'wage',
        'received salary', 'earned',
    },
}

# Items with known names — for extract_item()
KNOWN_ITEMS: dict = {
    # Food
    'شاورما': 'Shawarma', 'shawarma': 'Shawarma',
    'بيبسي': 'Pepsi', 'pepsi': 'Pepsi',
    'كوكاكولا': 'Coca-Cola', 'كوكا': 'Coca-Cola', 'كولا': 'Coca-Cola',
    'سبرايت': 'Sprite', 'sprite': 'Sprite',
    'فانتا': 'Fanta', 'fanta': 'Fanta',
    'قهوة': 'Coffee', 'قهوه': 'Coffee', 'coffee': 'Coffee',
    'شاي': 'Tea', 'tea': 'Tea',
    'عصير': 'Juice', 'juice': 'Juice',
    'فول': 'Ful', 'طعمية': 'Falafel', 'كشري': 'Koshari',
    'برجر': 'Burger', 'burger': 'Burger',
    'بيتزا': 'Pizza', 'pizza': 'Pizza',
    'سندوتش': 'Sandwich', 'sandwich': 'Sandwich',
    'خضار': 'Fresh Vegetables', 'خضروات': 'Fresh Vegetables',
    'فاكهة': 'Fresh Fruits', 'فواكه': 'Fresh Fruits',
    'شوكولاتة': 'Chocolate', 'شوكولاته': 'Chocolate', 'chocolate': 'Chocolate',
    'شيبس': 'Chips', 'شابسي': 'Chips', 'chips': 'Chips',
    # Transport
    'اوبر': 'Uber Ride', 'أوبر': 'Uber Ride', 'uber': 'Uber Ride',
    'كريم': 'Careem Ride', 'careem': 'Careem Ride',
    'تاكسي': 'Taxi', 'taxi': 'Taxi',
    'بنزين': 'Fuel', 'وقود': 'Fuel', 'fuel': 'Fuel', 'petrol': 'Fuel',
    'تذكرة': 'Ticket', 'تسكرة': 'Ticket', 'ticket': 'Ticket',
    # Health
    'دواء': 'Medicine', 'دوا': 'Medicine', 'medicine': 'Medicine',
    'فيتامين': 'Vitamins', 'vitamin': 'Vitamins',
    # Bills
    'كهرباء': 'Electricity Bill', 'كهربا': 'Electricity Bill',
    'انترنت': 'Internet Bill', 'internet': 'Internet Bill',
    'مياه': 'Water Bill', 'ميه': 'Water Bill',
    'غاز': 'Gas Bill', 'gas': 'Gas Bill',
    'مكدونلز': 'McDonald\'s', 'مكدونلدز': 'McDonald\'s', 'ماكدونالز': 'McDonald\'s',
    'ماكدونالدز': 'McDonald\'s', 'ماكدو': 'McDonald\'s', 'mcdonalds': 'McDonald\'s',
    'كنتاكي': 'KFC', 'kfc': 'KFC',
    'برجر كينج': 'Burger King', 'burger king': 'Burger King',
    'بيتزا هت': 'Pizza Hut', 'pizza hut': 'Pizza Hut',
    'هارديز': 'Hardee\'s', 'hardees': 'Hardee\'s',
    'صب واي': 'Subway', 'subway': 'Subway',
    'ستارباكس': 'Starbucks', 'starbucks': 'Starbucks',
    'كوستا': 'Costa Coffee', 'costa': 'Costa Coffee',
    'اكسسوارات': 'Accessories', 'اكسسورات': 'Accessories', 'اكسسوار': 'Accessories', 'فستين': 'Dress', 'dress': 'Dress',
    'بلوزة': 'Blouse', 'بلوزه': 'Blouse', 'blouse': 'Blouse',
    'جينز': 'Jeans', 'jeans': 'Jeans',
    'قميص': 'Shirt', 'shirt': 'Shirt',
    'جاكت': 'Jacket', 'jacket': 'Jacket',
    'جزمة': 'Shoes', 'حذاء': 'Shoes', 'shoes': 'Shoes',
    'شنطة': 'Bag', 'حقيبة': 'Bag', 'bag': 'Bag',
    'ساعة': 'Watch', 'watch': 'Watch',
}


def _classify_by_keywords(text: str) -> Optional[str]:
    """
    Fast keyword-based classification.
    Returns the first matching category or None.
    Priority order matches CATEGORY_KEYWORDS insertion order.
    """
    t = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return category
    return None


def _extract_known_item(text: str) -> Optional[str]:
    """Return a clean English item name if a known item keyword is found."""
    t = normalize_arabic_text(text).lower()
    for kw, item_name in KNOWN_ITEMS.items():
        if kw in t:
            return item_name
    return None


class CategoryClassifier:
    """Classify transactions into 8 fixed English categories."""

    def classify(self, text: str, place: Optional[str] = None) -> str:
        norm = normalize_arabic_text(text.lower())
        full = f"{norm} {(place or '').lower()}"

        # ── PASS 1: direct keyword match (fastest, highest precision) ──
        cat = _classify_by_keywords(full)
        if cat:
            logger.debug(f"Keyword → {cat}")
            return cat

        # ── PASS 2: semantic / pattern rules ──
        cat = self._semantic_classify(norm, place)
        logger.debug(f"Semantic → {cat}")

        # ── PASS 3: ML hybrid (optional, may not be trained) ──
        try:
            ml_cat, ml_conf = smart_predictor.predict_category(
                text, place, None, None, cat
            )
            if ml_cat and ml_conf >= 0.65:
                logger.debug(f"ML ({ml_conf:.2f}) → {ml_cat}")
                return ml_cat
        except Exception:
            pass

        return cat

    def _semantic_classify(self, text: str, place: Optional[str]) -> str:
        """Rule-based semantic classification fallback."""

        # Income — check before everything else
        income_signals = ('مرتب', 'راتب', 'معاش', 'salary', 'income', 'wage', 'earned', 'مكافأة', 'بونص')
        if any(k in text for k in income_signals):
            return 'Salary & Income'

        # Movement + transport service
        if self._is_transport(text):
            return 'Transportation'

        # Eating / drinking verb
        if any(v in text for v in ('كلت', 'اكلت', 'شربت', 'ate', 'drank', 'eaten')):
            return 'Food & Drinks'

        # Health signals
        if self._is_health(text):
            return 'Health & Beauty'

        # Repair / maintenance / cleaning
        if self._is_maintenance(text):
            return 'Bills & Utilities'

        # Purchase verb → default Shopping
        if any(v in text for v in ('اشتريت', 'شتريت', 'شريت', 'جبت', 'bought', 'purchased')):
            return 'Shopping'

        # Payment verb without clear item → Bills & Utilities
        if any(v in text for v in ('دفعت', 'صرفت', 'paid', 'spent')):
            return 'Bills & Utilities'

        return 'Shopping'

    def _is_transport(self, text: str) -> bool:
        patterns = [
            r'(رحت|روحت|ذهبت|مشيت|ركبت)\s+.{0,20}?(اوبر|أوبر|كريم|تاكسي|مترو|اتوبيس|باص|قطار)',
            r'(رحت|روحت|ذهبت)\s+.{0,20}?ب(اوبر|أوبر|كريم|تاكسي)',
            r'ب(اوبر|أوبر|كريم|تاكسي|المترو|الباص|القطار)',
            r'(took|took a|went by|by)\s+(uber|careem|taxi|bus|metro|train)',
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_health(self, text: str) -> bool:
        patterns = [
            r'(رحت|روحت|ذهبت)\s+.{0,15}?(صيدلية|دكتور|طبيب|مستشفى|عيادة)',
            r'(went|visited)\s+.{0,15}?(pharmacy|doctor|hospital|clinic)',
        ]
        return any(re.search(p, text) for p in patterns)

    def _is_maintenance(self, text: str) -> bool:
        signals = ('صيانة', 'إصلاح', 'تصليح', 'نضفت', 'صلحت', 'maintenance', 'repair', 'fix')
        return any(s in text for s in signals)


class TransactionExtractor:
    """Extract all fields of a single transaction from a text segment."""

    def __init__(self):
        self.classifier = CategoryClassifier()

    # ── Places ──────────────────────────────────────
    _PLACES: dict = {
        'Uber':           ['اوبر', 'أوبر', 'uber'],
        'Careem':         ['كريم', 'careem'],
        'Taxi':           ['تاكسي', 'taxi'],
        'Metro':          ['مترو', 'metro station', 'محطة مترو'],
        'Train Station':  ['قطار', 'محطة قطار', 'قطر', 'train'],
        'Bus':            ['اتوبيس', 'باص', 'bus'],
        'Carrefour':      ['كارفور', 'carrefour'],
        'Spinneys':       ['سبينس', 'spinneys'],
        'Metro Market':   ['ميترو ماركت', 'metro market'],
        'Hypermarket':    ['هايبر', 'hyper', 'هايبر ماركت'],
        'Lulu':           ['لولو', 'lulu'],
        'Panda':          ['بنده', 'panda'],
        'Kazyon':         ['كازيون', 'kazyon'],
        'Khair Zaman':    ['خير زمان'],
        'Al-Othaim':      ['العثيم'],
        'Fathalla':       ['فتح الله', 'fathalla'],
        'Supermarket':    ['سوبر ماركت', 'supermarket', 'سوبر'],
        'Mall':           ['مول', 'mall', 'سيتي ستارز', 'مول العرب', 'city stars'],
        'Pharmacy':       ['صيدلية', 'pharmacy', 'صيدليه', 'اجزاخانه'],
        'Clinic':         ['عيادة', 'clinic'],
        'Hospital':       ['مستشفى', 'hospital'],
        'Restaurant':     ['مطعم', 'restaurant'],
        'Cafe':           ['كافيه', 'cafe', 'coffee shop', 'كوستا', 'ستارباكس'],
        'Gas Station':    ['محطة وقود', 'بنزينة', 'gas station', 'petrol station'],
        'Bakery':         ['بقالة', 'بقال', 'grocery'],
        'Cinema':         ['سينما', 'cinema'],
        'Gym':            ['جيم', 'gym'],
    }

    def extract_place(self, text: str) -> Optional[str]:
        t = text.lower()
        for name, keywords in self._PLACES.items():
            if any(kw in t for kw in keywords):
                return name
        return None

    def extract_item(self, text: str, category: str) -> str:
        # Try known items first
        item = _extract_known_item(text)
        if item:
            return item

        t_norm = normalize_arabic_text(text.lower())

        # Pattern-based extraction for unlisted items
        item_patterns = [
            r'(?:اشتريت|شتريت|شريت|جبت|اخدت)\s+([\u0600-\u06FF]+)',
            r'(?:bought|got|ordered|purchased)\s+([a-z]+)',
            r'(?:كلت|اكلت|شربت|ate|drank)\s+([\u0600-\u06FFa-z]+)',
            r'(?:على|علي)\s+([\u0600-\u06FF]+)',
            r'(?:for|on)\s+([a-z]+)',
        ]
        _EXCLUDED = _NUMBER_WORDS.keys() | {
            'في', 'من', 'على', 'ال', 'the', 'a', 'an', 'and',
            'مول', 'mall', 'كارفور', 'carrefour', 'ميترو',
            'حاجه', 'حاجات', 'سبينس', 'جوه', 'القطر', 'قطر',
        }
        for pat in item_patterns:
            m = re.search(pat, t_norm)
            if m:
                word = m.group(1).strip()
                # strip leading prepositions
                for pfx in ('وب', 'فب', 'ب', 'ل', 'ك'):
                    if word.startswith(pfx) and len(word) > len(pfx) + 1:
                        word = word[len(pfx):]
                        break
                if (word not in _EXCLUDED
                        and word not in _NUMBER_WORDS
                        and len(word) > 2
                        and not re.match(r'^\d+$', word)):
                    return word.capitalize()

        # Category defaults
        return {
            'Food & Drinks':     'Food & Beverages',
            'Transportation':    'Transportation',
            'Shopping':          'General Shopping',
            'Health & Beauty':   'Health & Beauty Items',
            'Clothes & Fashion': 'Clothing & Accessories',
            'Bills & Utilities': 'Bills & Utilities',
            'Entertainment':     'Entertainment',
            'Salary & Income':   'Income',
        }.get(category, 'Various Items')

    def determine_type(self, text: str) -> TransactionType:
        t = text.lower()
        if any(kw in t for kw in INCOME_KEYWORDS):
            return TransactionType.INCOME
        return TransactionType.EXPENSE

    def extract(self, text: str, amount: Optional[float] = None) -> Transaction:
        if amount is None:
            amounts = extract_amounts_from_text(text)
            amount = amounts[0][0] if amounts else None

        place    = self.extract_place(text)
        t_type   = self.determine_type(text)
        category = self.classifier.classify(text, place)
        item     = self.extract_item(text, category)
        conf     = self._confidence(amount, place, item, text)

        return Transaction(
            id=str(uuid.uuid4()),
            amount=amount,
            transaction_type=t_type,
            category=category,
            item=item,
            merchant=place,
            confidence_score=conf,
            extracted_from=text,
        )

    def _confidence(self, amount, place, item, text) -> float:
        score = 0.5
        if amount is not None: score += 0.25
        if place:              score += 0.10
        if item and item not in ('General Shopping', 'Various Items'): score += 0.10
        if any(v in text.lower() for v in ACTION_VERBS): score += 0.05
        return min(round(score, 2), 1.0)


# ══════════════════════════════════════════════════════════════
#  NLP SERVICE
# ══════════════════════════════════════════════════════════════

class NLPService:
    """Main entry point for text and voice financial analysis."""

    def __init__(self):
        self.extractor = TransactionExtractor()

    @cached_text_analysis(ttl=3600)
    async def analyze_text(self, text: str, language: str = 'ar') -> AnalysisResult:
        start = time.time()
        try:
            logger.info(f"Analyzing: {text[:60]}…")

            # Content safety check
            try:
                content_filter.filter_text(text)
            except ValidationError as e:
                if any(w in str(e).lower() for w in ('prohibited', 'illegal', 'harmful')):
                    raise
                logger.warning(f"Content filter warning (proceeding): {e}")

            normalized = normalize_arabic_text(text)
            if language == 'auto':
                language = detect_language(text)

            all_amounts = extract_amounts_from_text(text)
            segments    = split_text_into_segments(text)
            logger.debug(f"{len(segments)} segments, {len(all_amounts)} amounts")

            transactions: list = []
            used_amounts: set  = set()
            last_verb: str     = ''     # carried context for verb-less segments

            for seg in segments:
                try:
                    content_filter.filter_text(seg)
                except ValidationError:
                    logger.warning(f"Skipping prohibited segment: {seg[:40]}")
                    continue

                seg_lower = seg.lower()

                # Determine effective segment (add inherited verb if needed)
                has_verb = any(v in seg_lower for v in ACTION_VERBS)
                if has_verb:
                    for v in ACTION_VERBS:
                        if v in seg_lower:
                            last_verb = v
                            break
                    effective = seg
                else:
                    effective = f"{last_verb} {seg}".strip() if last_verb else seg

                if not self._is_transaction(effective):
                    continue

                # Amount assignment
                seg_amounts = extract_amounts_from_text(effective)
                amount = None
                if seg_amounts:
                    amount = seg_amounts[0][0]
                    used_amounts.add(amount)
                else:
                    if self._is_spending(effective):
                        for amt, _ in all_amounts:
                            if amt not in used_amounts:
                                amount = amt
                                used_amounts.add(amt)
                                break

                transaction = self.extractor.extract(effective, amount)
                transaction.extracted_from = seg   # keep original text for display

                if self._is_meaningful(transaction):
                    transactions.append(transaction)

            if not transactions:
                logger.info("No financial transactions found.")
                return AnalysisResult(
                    transactions=[],
                    summary=FinancialSummary(
                        total_transactions=0, total_income=0,
                        total_expenses=0, net_amount=0, categories={},
                    ),
                    processing_time_ms=int((time.time() - start) * 1000),
                    language_detected=language,
                )

            summary  = self._summarize(transactions)
            details  = [TransactionDetail(**t.to_response_model()) for t in transactions]
            proc_ms  = int((time.time() - start) * 1000)
            result   = AnalysisResult(
                transactions=details, summary=summary,
                processing_time_ms=proc_ms, language_detected=language,
            )

            try:
                await database_service.save_analysis_result(result, 'text', text, text)
            except Exception as e:
                logger.warning(f"DB save failed: {e}")

            logger.info(f"Done — {len(transactions)} transactions in {proc_ms}ms")
            return result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"NLP error: {e}", exc_info=True)
            raise NLPProcessingError(f"Analysis failed: {e}")

    # ── helpers ──────────────────────────────────────────────

    def _is_transaction(self, seg: str) -> bool:
        sl = seg.lower()
        return (
            any(v in sl for v in ACTION_VERBS)
            or bool(extract_amounts_from_text(seg))
        )

    def _is_spending(self, seg: str) -> bool:
        return any(v in seg.lower() for v in (
            'دفعت', 'اشتريت', 'شتريت', 'شريت', 'جبت', 'صرفت',
            'paid', 'bought', 'spent', 'purchased',
        ))

    def _is_meaningful(self, t: Transaction) -> bool:
        return t.amount is not None or bool(t.merchant) or bool(t.item)

    def _summarize(self, transactions: list) -> FinancialSummary:
        income   = sum(t.amount for t in transactions
                       if t.transaction_type == TransactionType.INCOME and t.amount)
        expenses = sum(t.amount for t in transactions
                       if t.transaction_type == TransactionType.EXPENSE and t.amount)
        cats: dict = {}
        for t in transactions:
            if t.amount and t.category:
                cats[t.category] = round(cats.get(t.category, 0) + t.amount, 2)
        return FinancialSummary(
            total_transactions=len(transactions),
            total_income=round(income, 2),
            total_expenses=round(expenses, 2),
            net_amount=round(income - expenses, 2),
            categories=cats,
        )
