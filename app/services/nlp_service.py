"""
NLP service for text analysis and transaction extraction
"""
import re
import time
import uuid
from typing import List, Dict, Any, Optional
from app.core.logging import get_logger
from app.utils.text_utils import (
    normalize_arabic_text, extract_amounts_from_text, 
    split_text_into_segments, detect_language
)
from app.utils.cache import cached_text_analysis
from app.utils.content_filter import content_filter
from app.models.domain import Transaction, TransactionType
from app.models.responses import TransactionDetail, FinancialSummary, AnalysisResult
from app.config import INCOME_KEYWORDS, EXPENSE_KEYWORDS
from app.exceptions import NLPProcessingError, ValidationError

logger = get_logger("nlp_service")


class CategoryClassifier:
    """Classify transactions into fixed English categories regardless of language"""
    
    def __init__(self):
        # Fixed English categories with multilingual keywords
        self.categories = {
            'Food & Drinks': {
                'keywords': [
                    # Arabic keywords
                    'طعام', 'أكل', 'اكل', 'خضار', 'خضروات', 'فواكه', 'فاكهة', 'لحم', 'لحمة', 
                    'فراخ', 'فرخة', 'دجاج', 'سمك', 'عيش', 'خبز', 'جبنة', 'جبن', 'لبن', 'حليب',
                    'بيض', 'زيت', 'سكر', 'رز', 'أرز', 'مكرونة', 'معكرونة', 'بطاطس',
                    'مطعم', 'كشري', 'فول', 'طعمية', 'قهوة', 'كافيه', 'كافي',
                    'شاي', 'عصير', 'مشروب', 'كوكاكولا', 'بيبسي', 'ماء', 'مياه معدنية',
                    'شوكولاتة', 'شوكولاته', 'حلويات', 'بسكويت', 'كيك', 'شابسي', 'شيبس',
                    # English keywords
                    'food', 'grocery', 'vegetables', 'fruits', 'meat', 'chicken', 'fish', 'coffee', 'tea',
                    'chocolate', 'candy', 'snacks', 'chips', 'cookies', 'cake', 'restaurant', 'cafe',
                    'bread', 'milk', 'cheese', 'eggs', 'rice', 'pasta', 'sugar', 'oil'
                ],
                'places': ['كارفور', 'carrefour', 'سبينس', 'spinneys', 'ميترو', 'metro', 'كافيه', 'مطعم', 'مول', 'mall', 'restaurant', 'cafe']
            },
            'Transportation': {
                'keywords': [
                    # Arabic keywords - enhanced
                    'مواصلات', 'بنزين', 'وقود', 'سولار', 'تاكسي', 'أوبر', 'اوبر', 'كريم', 'مترو', 
                    'اتوبيس', 'ميكروباص', 'توكتوك', 'اجرة', 'عربية', 'سيارة', 'قطر', 'قطار',
                    'تذكرة', 'تسكرة', 'ركبت', 'ركوب', 'سفر', 'رحلة', 'محطة', 'للقطر', 'جوه للقطر',
                    'باس تاكيت', 'تاكيت', 'قوبر', 'بقوبر', 'باوبر', 'بالاوبر', 'بالقوبر',
                    # Transportation methods with prepositions
                    'بالباص', 'بالاتوبيس', 'بالمترو', 'بالقطار', 'بالتاكسي', 'بالعربية', 'بقوبر', 'بكريم',
                    'رحت بالباص', 'رحت بالاتوبيس', 'رحت بالمترو', 'رحت بالقطار', 'رحت بقوبر',
                    # English keywords
                    'transport', 'gas', 'fuel', 'taxi', 'uber', 'careem', 'bus', 'metro', 'car', 'train', 
                    'ticket', 'bus ticket', 'train ticket', 'metro ticket', 'travel', 'trip',
                    'by bus', 'by train', 'by metro', 'by taxi', 'took bus', 'took train', 'by uber', 'by careem'
                ],
                'places': ['محطة', 'مترو', 'قطار', 'للقطر', 'station', 'bus stop', 'metro station']
            },
            'Shopping': {
                'keywords': [
                    # Arabic keywords
                    'محل', 'سوبر ماركت', 'بقالة', 'بقال', 'جمعية', 'حاجات',
                    'تسوق', 'مشتريات', 'اشتريت', 'جبت', 'شريت',
                    # English keywords
                    'shopping', 'mall', 'store', 'shop', 'bought', 'purchase', 'buy', 'get', 'supermarket'
                ],
                'places': ['كارفور', 'carrefour', 'سبينس', 'spinneys', 'ميترو', 'metro', 'مول', 'mall']
            },
            'Salary & Income': {
                'keywords': [
                    # Arabic keywords
                    'مرتب', 'راتب', 'معاش', 'قبضت', 'استلمت مرتب', 
                    'مكافأة', 'بونص', 'حافز', 'عمولة', 'ارباح', 'دخل',
                    # English keywords
                    'salary', 'wage', 'income', 'bonus', 'commission', 'profit', 'received', 'earned'
                ],
                'places': []
            },
            'Clothes & Fashion': {
                'keywords': [
                    # Arabic keywords
                    'ملابس', 'هدوم', 'لبس', 'جزمة', 'شنطة', 'حذاء', 'بنطلون', 'قميص',
                    'فستان', 'جاكت', 'بلوفر', 'جينز', 'اكسسوار', 'ساعة', 'نظارة',
                    # English keywords
                    'clothes', 'fashion', 'shoes', 'bag', 'shirt', 'pants', 'dress', 'jacket', 'jeans', 'watch'
                ],
                'places': ['مول', 'mall', 'سيتي ستارز', 'مول العرب', 'زارا', 'zara', 'h&m']
            },
            'Health & Beauty': {
                'keywords': [
                    # Arabic keywords
                    'دواء', 'طبيب', 'صيدلية', 'دكتور', 'علاج', 'مستشفى', 'عيادة', 'تحليل', 
                    'اشعة', 'كشف', 'عملية', 'روشتة', 'فيتامين', 'مسكن', 'مضاد حيوي',
                    'عطر', 'مكياج', 'كريم', 'شامبو', 'صابون', 'معجون أسنان',
                    # English keywords
                    'medicine', 'doctor', 'pharmacy', 'health', 'hospital', 'clinic', 'medical',
                    'cosmetics', 'perfume', 'makeup', 'cream', 'shampoo', 'soap'
                ],
                'places': ['صيدلية', 'pharmacy', 'عيادة', 'clinic', 'مستشفى', 'hospital']
            },
            'Bills & Utilities': {
                'keywords': [
                    # Arabic keywords
                    'فاتورة', 'كهرباء', 'كهربا', 'مياه', 'ميه', 'انترنت', 'نت', 'موبايل', 
                    'تليفون', 'غاز', 'تلفون', 'خط', 'باقة', 'اشتراك', 'ايجار', 'قسط',
                    'نظاف', 'تنظيف', 'ستة نظاف', 'صيانة', 'إصلاح', 'تصليح',
                    # English keywords
                    'bill', 'electricity', 'water', 'internet', 'mobile', 'phone', 'gas', 'subscription', 'rent',
                    'cleaning', 'maintenance', 'repair', 'service'
                ],
                'places': []
            },
            'Entertainment': {
                'keywords': [
                    # Arabic keywords
                    'سينما', 'فيلم', 'ترفيه', 'مسرح', 'حفلة', 'حفل', 'كونسرت', 'نادي', 'جيم',
                    'لعبة', 'العاب', 'كتاب', 'مجلة', 'موسيقى', 'رياضة',
                    # English keywords
                    'cinema', 'movie', 'entertainment', 'film', 'concert', 'gym', 'club', 'games', 'book', 'music'
                ],
                'places': ['سينما', 'cinema', 'نادي', 'club', 'جيم', 'gym']
            }
        }
    
    def classify(self, text: str, place: Optional[str] = None) -> str:
        """Classify transaction using semantic understanding and context analysis"""
        text_lower = normalize_arabic_text(text.lower())
        
        logger.debug(f"🧠 Semantic analysis for: {text_lower[:50]}...")
        
        # SEMANTIC ANALYSIS: Understand the meaning, not just keywords
        semantic_analysis = self._analyze_semantic_meaning(text_lower, place)
        
        # Make decision based on semantic understanding
        category = self._make_semantic_decision(semantic_analysis, text_lower)
        
        logger.debug(f"🎯 Semantic classification result: {category}")
        return category
    
    def _analyze_semantic_meaning(self, text: str, place: Optional[str]) -> dict:
        """Analyze the semantic meaning of the transaction"""
        analysis = {
            'action_type': None,
            'service_type': None,
            'item_nature': None,
            'location_context': None,
            'payment_context': None,
            'confidence': 0.0
        }
        
        # ANALYZE ACTION TYPE (what is being done?)
        if self._indicates_service_hiring(text):
            analysis['action_type'] = 'service_hiring'
            analysis['confidence'] += 0.3
        elif self._indicates_movement_with_cost(text):
            analysis['action_type'] = 'transportation'
            analysis['confidence'] += 0.3
        elif self._indicates_purchase(text):
            analysis['action_type'] = 'purchase'
            analysis['confidence'] += 0.2
        elif self._indicates_payment(text):
            analysis['action_type'] = 'payment'
            analysis['confidence'] += 0.2
        
        # ANALYZE SERVICE TYPE (what kind of service?)
        if self._indicates_repair_maintenance(text):
            analysis['service_type'] = 'repair_maintenance'
            analysis['confidence'] += 0.3
        elif self._indicates_health_service(text):
            analysis['service_type'] = 'health_service'
            analysis['confidence'] += 0.3
        elif self._indicates_transport_service(text):
            analysis['service_type'] = 'transport_service'
            analysis['confidence'] += 0.3
        
        # ANALYZE ITEM NATURE (what is the item/service about?)
        if self._indicates_consumable_item(text):
            analysis['item_nature'] = 'consumable'
            analysis['confidence'] += 0.2
        elif self._indicates_medical_item(text):
            analysis['item_nature'] = 'medical'
            analysis['confidence'] += 0.3
        elif self._indicates_utility_service(text):
            analysis['item_nature'] = 'utility'
            analysis['confidence'] += 0.2
        
        # ANALYZE LOCATION CONTEXT
        analysis['location_context'] = self._analyze_location_semantics(text, place)
        
        return analysis
    
    def _indicates_service_hiring(self, text: str) -> bool:
        """Detect if someone is hiring a service person"""
        patterns = [
            r'جبت\s+راجل',  # جبت راجل
            r'جبت\s+راجري',  # جبت راجري  
            r'جبت\s+ست',   # جبت ست (cleaning lady)
            r'جبت\s+.*?\s+نظاف',  # جبت ستة نظاف
            r'جبت\s+.*?\s+تنضف',  # جبت ست تنضف
            r'استدعيت\s+',   # استدعيت
            r'طلبت\s+راجل',  # طلبت راجل
            r'called\s+a\s+guy',
            r'hired\s+someone',
            r'got\s+a\s+man',
            r'got\s+.*?\s+clean'
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _indicates_repair_maintenance(self, text: str) -> bool:
        """Detect repair/maintenance context"""
        # Look for repair actions and appliances
        repair_actions = ['يدفلي', 'ينضفلي', 'يصلح', 'يرمم', 'صيانة', 'إصلاح', 'نظاف', 'تنظيف', 'نضفت', 'صلحت', 'repair', 'fix', 'clean', 'maintain']
        appliances = ['تكيف', 'تكييف', 'غسالة', 'ثلاجة', 'تليفزيون', 'كمبيوتر', 'سيارة', 'موتور', 'مكينة', 'شقة', 'بيت', 'منزل', 'راوتر', 'router']
        
        has_repair_action = any(action in text for action in repair_actions)
        has_appliance = any(appliance in text for appliance in appliances)
        
        # Also check for cleaning service patterns
        cleaning_patterns = [
            r'ست\s+تنضف',   # ست تنضف
            r'ستة\s+نظاف',  # ستة نظاف
            r'للشقة',       # للشقة
            r'للبيت',       # للبيت
            r'نضفت\s+.*?(تكييف|راوتر)',  # نضفت التكييف
            r'صلحت\s+.*?(راوتر|تكييف)',  # صلحت الراوتر
            r'cleaning\s+lady',
            r'house\s+cleaning'
        ]
        has_cleaning_pattern = any(re.search(pattern, text) for pattern in cleaning_patterns)
        
        return has_repair_action or has_appliance or has_cleaning_pattern
    
    def _indicates_movement_with_cost(self, text: str) -> bool:
        """Detect movement that costs money (transportation)"""
        movement_patterns = [
            r'رحت\s+.*?\s+ب(الباص|الاتوبيس|المترو|القطار|التاكسي|العربية|قوبر|اوبر|كريم)',
            r'went\s+.*?\s+by\s+(bus|train|metro|taxi|car|uber|careem)',
            r'ركبت\s+(باص|اتوبيس|مترو|قطار|تاكسي|اوبر|قوبر|كريم)',
            r'took\s+(bus|train|metro|taxi|uber|careem)',
            r'بقوبر|باوبر|بكريم|بالاوبر|بالقوبر|بالكريم',  # Direct Uber/Careem patterns
            r'by\s+uber|by\s+careem'
        ]
        return any(re.search(pattern, text) for pattern in movement_patterns)
    
    def _indicates_health_service(self, text: str) -> bool:
        """Detect health-related services or items"""
        health_contexts = [
            r'رحت\s+.*?(صيدلية|سيدالية|دكتور|طبيب|مستشفى|عيادة)',
            r'went\s+to\s+.*?(pharmacy|doctor|hospital|clinic)',
            r'جبت\s+.*?(دواء|دوة|علاج|مسكن)',
            r'bought\s+.*?(medicine|drug|medication)'
        ]
        return any(re.search(pattern, text) for pattern in health_contexts)
    
    def _indicates_consumable_item(self, text: str) -> bool:
        """Detect consumable items (food, drinks, etc.)"""
        # Look for eating/drinking actions or food-related contexts
        consumption_patterns = [
            r'جبت\s+.*?(جبنة|لحمة|خضار|فاكهة|شبسي|شيبس|قهوة|شاي|شوكولاته|شوكولاتة|شاورما)',
            r'bought\s+.*?(cheese|meat|vegetables|chips|coffee|tea|chocolate|shawarma)',
            r'اشتريت\s+.*?(طعام|أكل)',
            r'من\s+(السوبرماركت|سوبر\s*ماركت|السوير\s*ماركت|سوبر\s+ماركت)',
            r'from\s+(supermarket|grocery)',
            r'شاورما\s+مجمدة',  # شاورما مجمدة
            r'frozen\s+.*?(food|meat|shawarma)'
        ]
        return any(re.search(pattern, text) for pattern in consumption_patterns)
    
    def _indicates_medical_item(self, text: str) -> bool:
        """Detect medical items or pharmacy visits"""
        medical_patterns = [
            r'من\s+(الصيدلية|السيدالية)',
            r'from\s+(pharmacy)',
            r'جبت\s+.*?(دواء|دوة|اسبرين|مسكن|علاج)',
            r'bought\s+.*?(medicine|aspirin|medication|drug)'
        ]
        return any(re.search(pattern, text) for pattern in medical_patterns)
    
    def _indicates_transport_service(self, text: str) -> bool:
        """Detect transportation services"""
        return self._indicates_movement_with_cost(text)
    
    def _indicates_utility_service(self, text: str) -> bool:
        """Detect utility or maintenance services"""
        return self._indicates_repair_maintenance(text)
    
    def _indicates_purchase(self, text: str) -> bool:
        """Detect purchase actions"""
        purchase_verbs = ['جبت', 'اشتريت', 'شريت', 'bought', 'purchased', 'got']
        return any(verb in text for verb in purchase_verbs)
    
    def _indicates_payment(self, text: str) -> bool:
        """Detect payment actions"""
        payment_verbs = ['دفعت', 'صرفت', 'خد مني', 'paid', 'cost']
        return any(verb in text for verb in payment_verbs)
    
    def _analyze_location_semantics(self, text: str, place: Optional[str]) -> str:
        """Analyze location context semantically"""
        full_context = f"{text} {place or ''}".lower()
        
        # Health locations
        if any(loc in full_context for loc in ['صيدلية', 'سيدالية', 'pharmacy', 'دكتور', 'طبيب', 'مستشفى']):
            return 'health_location'
        
        # Food locations - enhanced patterns
        if any(loc in full_context for loc in ['سوبرماركت', 'سوير ماركت', 'سوبر ماركت', 'supermarket', 'مطعم', 'restaurant']):
            return 'food_location'
        
        # Service locations (home, workplace)
        if any(loc in full_context for loc in ['البيت', 'المنزل', 'الشقة', 'للشقة', 'للبيت', 'home', 'house', 'apartment']):
            return 'service_location'
        
        # Destination locations (school, work)
        if any(loc in full_context for loc in ['مدرسة', 'جامعة', 'شغل', 'مكتب', 'school', 'university', 'work', 'office']):
            return 'destination_location'
        
        return 'unknown_location'
    
    def _make_semantic_decision(self, analysis: dict, text: str) -> str:
        """Make classification decision based on semantic analysis"""
        
        # RULE 1: Service hiring for repair/maintenance/cleaning = Bills & Utilities
        if (analysis['action_type'] == 'service_hiring' and 
            (analysis['service_type'] == 'repair_maintenance' or 
             analysis['item_nature'] == 'utility' or
             analysis['location_context'] == 'service_location')):
            logger.debug(f"🔧 Bills & Utilities: Service hiring for repair/maintenance/cleaning")
            return 'Bills & Utilities'
        
        # RULE 2: Transportation service or movement with cost = Transportation
        if (analysis['action_type'] == 'transportation' or 
            analysis['service_type'] == 'transport_service'):
            logger.debug(f"🚂 Transportation: Movement or transport service")
            return 'Transportation'
        
        # RULE 3: Health service or medical items = Health & Beauty
        if (analysis['service_type'] == 'health_service' or 
            analysis['item_nature'] == 'medical' or 
            analysis['location_context'] == 'health_location'):
            logger.debug(f"💊 Health & Beauty: Health service or medical item")
            return 'Health & Beauty'
        
        # RULE 4: Consumable items or food locations = Food & Drinks
        if (analysis['item_nature'] == 'consumable' or 
            analysis['location_context'] == 'food_location'):
            logger.debug(f"🍽️ Food & Drinks: Consumable item or food location")
            return 'Food & Drinks'
        
        # RULE 5: Repair/maintenance context = Bills & Utilities
        if analysis['service_type'] == 'repair_maintenance':
            logger.debug(f"🔧 Bills & Utilities: Repair/maintenance service")
            return 'Bills & Utilities'
        
        # RULE 6: Payment without clear service context = Bills & Utilities
        if (analysis['action_type'] == 'payment' and 
            not analysis['service_type'] and 
            not analysis['item_nature']):
            logger.debug(f"💰 Bills & Utilities: Payment without clear context")
            return 'Bills & Utilities'
        
        # RULE 7: Purchase action = Shopping (default)
        if analysis['action_type'] == 'purchase':
            logger.debug(f"🛒 Shopping: Purchase action")
            return 'Shopping'
        
        # DEFAULT: Shopping
        logger.debug(f"🛒 Shopping: Default classification")
        return 'Shopping'


class TransactionExtractor:
    """Extract transaction details from text segments"""
    
    def __init__(self):
        self.classifier = CategoryClassifier()
        self.places_map = {
            'كارفور': ['كارفور', 'carrefour'],
            'سبينس': ['سبينس', 'spinneys'],
            'ميترو': ['metro', 'ميترو'],
            'خير زمان': ['خير زمان'],
            'العثيم': ['العثيم'],
            'بنده': ['بنده', 'panda'],
            'هايبر': ['هايبر', 'hyper'],
            'لولو': ['لولو', 'lulu'],
            'فتح الله': ['فتح الله', 'fathalla'],
            'كازيون': ['كازيون', 'kazyon'],
            'سيتي ستارز': ['سيتي ستارز', 'city stars'],
            'مول العرب': ['مول العرب', 'mall of arabia'],
        }
    
    def extract_place(self, text: str) -> Optional[str]:
        """Extract place/merchant from text with enhanced detection"""
        text_lower = text.lower()
        
        # Enhanced place detection with transportation focus
        enhanced_places = {
            'كارفور': ['كارفور', 'carrefour'],
            'سبينس': ['سبينس', 'spinneys'],
            'ميترو ماركت': ['metro', 'ميترو'],
            'محطة القطار': ['قطار', 'قطر', 'للقطر', 'جوه للقطر', 'محطة قطار'],
            'محطة المترو': ['محطة مترو', 'مترو'],
            'كافيه': ['كافيه', 'مقهى', 'كوستا', 'ستارباكس', 'كافي شوب'],
            'مطعم': ['مطعم', 'restaurant'],
            'صيدلية': ['صيدلية', 'pharmacy', 'صيدليه'],
            'تاكسي': ['تاكسي', 'أوبر', 'اوبر', 'كريم', 'careem', 'uber'],
            'محطة وقود': ['محطة وقود', 'بنزينة', 'محطة بنزين'],
        }
        
        # Check enhanced places first (with priority for transportation)
        for place_name, keywords in enhanced_places.items():
            if any(kw in text_lower for kw in keywords):
                logger.debug(f"📍 Enhanced place detected: {place_name}")
                return place_name
        
        # Original places map for shopping locations
        for place_name, keywords in self.places_map.items():
            if any(kw in text_lower for kw in keywords):
                logger.debug(f"📍 Standard place detected: {place_name}")
                return place_name
        
        # Context-based place detection
        if 'سوبر ماركت' in text_lower or 'supermarket' in text_lower:
            return 'سوبر ماركت'
        elif 'مول' in text_lower or 'mall' in text_lower:
            return 'مركز تجاري'
        elif 'بقالة' in text_lower or 'بقال' in text_lower:
            return 'بقالة'
        
        return None
    
    def extract_item(self, text: str, category: str) -> Optional[str]:
        """Extract item from text based on fixed English category"""
        text_lower = text.lower()
        
        # Enhanced item detection with fixed English categories
        if 'قهوة' in text_lower or 'coffee' in text_lower:
            return 'Coffee'
        elif 'تذكرة' in text_lower or 'تسكرة' in text_lower or 'ticket' in text_lower:
            if 'قطار' in text_lower or 'قطر' in text_lower or 'train' in text_lower:
                return 'Train Ticket'
            elif 'مترو' in text_lower or 'metro' in text_lower:
                return 'Metro Ticket'
            elif 'اتوبيس' in text_lower or 'bus' in text_lower or 'باس' in text_lower:
                return 'Bus Ticket'
            else:
                return 'Transportation Ticket'
        elif 'خضار' in text_lower or 'vegetables' in text_lower:
            return 'Fresh Vegetables'
        elif 'فاكهة' in text_lower or 'فواكه' in text_lower or 'fruits' in text_lower:
            return 'Fresh Fruits'
        elif 'شوكولاتة' in text_lower or 'شوكولاته' in text_lower or 'chocolate' in text_lower:
            return 'Chocolate'
        elif 'شابسي' in text_lower or 'شيبس' in text_lower or 'chips' in text_lower:
            return 'Chips & Snacks'
        elif 'دواء' in text_lower or 'صيدلية' in text_lower or 'medicine' in text_lower:
            return 'Medicine & Medical Supplies'
        elif 'بنزين' in text_lower or 'وقود' in text_lower or 'gas' in text_lower or 'fuel' in text_lower:
            return 'Fuel & Gas'
        elif 'حاجات' in text_lower or 'stuff' in text_lower or 'things' in text_lower:
            # Be more specific based on category
            if category == 'Food & Drinks':
                if 'كارفور' in text_lower or 'carrefour' in text_lower or 'سبينس' in text_lower:
                    return 'Various Groceries'
                else:
                    return 'Food & Beverages'
            elif category == 'Transportation':
                if 'قطر' in text_lower or 'قطار' in text_lower or 'train' in text_lower:
                    return 'Train Travel Expenses'
                else:
                    return 'Transportation Expenses'
            elif category == 'Health & Beauty':
                return 'Health & Beauty Items'
            elif category == 'Clothes & Fashion':
                return 'Clothes & Personal Items'
            else:
                return 'Various Purchases'
        
        # Enhanced pattern-based extraction
        item_patterns = [
            (r'(?:على|علي)\s+(\w+)', 'على'),           # على خضار
            (r'(?:من|في)\s+(\w+)', 'من'),              # من اللحم  
            (r'(?:اشتريت|شريت|جبت|اخدت)\s+(\w+)', 'اشتريت'),  # اشتريت خضار
            (r'(?:كلت|شربت)\s+(\w+)', 'كلت'),           # كلت حاجات
            (r'(?:دفعت|صرفت).*?(?:على|علي|في)\s+(\w+)', 'دفعت'),  # دفعت على خضار
            # English patterns
            (r'(?:bought|got|purchased)\s+(\w+)', 'bought'),  # bought chocolate
            (r'(?:for|on)\s+(\w+)', 'for'),                   # for chocolate
        ]
        
        for pattern, context in item_patterns:
            match = re.search(pattern, text_lower)
            if match:
                potential_item = match.group(1)
                # Filter out common words and places
                excluded = ['في', 'من', 'على', 'ال', 'the', 'a', 'an', 'كارفور', 'ميترو', 
                           'حاجة', 'جوه', 'للقطر', 'قطر', 'قطار', 'حاجات', 'سبينس', 'mall', 'مول']
                if potential_item not in excluded and len(potential_item) > 2:
                    # Make it more descriptive based on category
                    if category == 'Food & Drinks' and potential_item in ['خضار', 'فاكهة', 'لحمة']:
                        return f"Fresh {potential_item}"
                    return potential_item.title()  # Capitalize for English
        
        # Category-based defaults (fixed English)
        category_defaults = {
            'Food & Drinks': 'Food Items',
            'Transportation': 'Transportation Expenses', 
            'Shopping': 'General Shopping',
            'Health & Beauty': 'Health Items',
            'Clothes & Fashion': 'Clothing & Accessories',
            'Bills & Utilities': 'Bills & Utilities',
            'Entertainment': 'Entertainment Activities',
            'Salary & Income': 'Income & Salary'
        }
        
        return category_defaults.get(category, 'Various Items')
    
    def determine_transaction_type(self, text: str) -> TransactionType:
        """Determine if transaction is income or expense"""
        text_lower = text.lower()
        
        is_income = any(keyword in text_lower for keyword in INCOME_KEYWORDS)
        return TransactionType.INCOME if is_income else TransactionType.EXPENSE
    
    def extract_transaction(self, text: str, amount: Optional[float] = None) -> Transaction:
        """Extract complete transaction from text segment with fixed English categories"""
        # If no amount provided, try to extract it
        if amount is None:
            amounts = extract_amounts_from_text(text)
            amount = amounts[0][0] if amounts else None
        
        # Extract components with fixed English categories
        place = self.extract_place(text)
        transaction_type = self.determine_transaction_type(text)
        category = self.classifier.classify(text, place)  # Always returns English category
        item = self.extract_item(text, category)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(text, amount, place, item)
        
        return Transaction(
            id=str(uuid.uuid4()),
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            item=item,
            merchant=place,
            confidence_score=confidence,
            extracted_from=text
        )
    
    def _calculate_confidence(self, text: str, amount: Optional[float], 
                            place: Optional[str], item: Optional[str]) -> float:
        """Calculate confidence score for extraction"""
        score = 0.5  # Base score
        
        # Amount found
        if amount is not None:
            score += 0.3
        
        # Place found
        if place:
            score += 0.1
        
        # Item found
        if item:
            score += 0.1
        
        # Contains action verbs
        action_verbs = ['دفعت', 'اشتريت', 'جبت', 'استلمت', 'قبضت']
        if any(verb in text.lower() for verb in action_verbs):
            score += 0.1
        
        return min(score, 1.0)


class NLPService:
    """Main NLP service for financial text analysis"""
    
    def __init__(self):
        self.extractor = TransactionExtractor()
    
    @cached_text_analysis(ttl=3600)  # Cache for 1 hour
    async def analyze_text(self, text: str, language: str = "ar") -> AnalysisResult:
        """Analyze text and extract financial information"""
        start_time = time.time()
        
        try:
            logger.info(f"Analyzing text: {text[:50]}...")
            
            # CRITICAL: Filter content for prohibited material only
            try:
                content_filter.filter_text(text)
            except ValidationError as e:
                # Only block truly prohibited content, not just non-financial content
                if "prohibited" in str(e).lower() or "illegal" in str(e).lower():
                    raise
                else:
                    logger.warning(f"Content filter warning (proceeding): {e}")
            
            # More lenient financial content check - just warn, don't block
            if not content_filter.is_financial_content(text):
                logger.warning("Content may not be financial, but proceeding with analysis")
            
            
            # Normalize text
            normalized_text = normalize_arabic_text(text)
            
            # Detect language if auto
            if language == "auto":
                language = detect_language(text)
            
            # Extract all amounts
            all_amounts = extract_amounts_from_text(text)
            logger.debug(f"Found {len(all_amounts)} amounts: {[a[0] for a in all_amounts]}")
            
            # Split into segments
            segments = split_text_into_segments(text)
            logger.debug(f"Split into {len(segments)} segments")
            
            # Extract transactions
            transactions = []
            used_amounts = set()
            
            for segment in segments:
                # Filter each segment as well
                try:
                    content_filter.filter_text(segment)
                except ValidationError:
                    logger.warning(f"Skipping prohibited segment: {segment[:30]}...")
                    continue
                
                # Skip segments that don't represent transactions
                if not self._is_transaction_segment(segment):
                    continue
                
                # Find amount for this segment
                # Extract transaction amounts for this segment
                segment_amounts = extract_amounts_from_text(segment)
                amount = None
                
                if segment_amounts:
                    # Use the first amount found in this segment
                    amount = segment_amounts[0][0]
                    used_amounts.add(amount)
                    logger.debug(f"Found amount {amount} in segment: {segment[:50]}...")
                else:
                    # Try to assign unused amount if this looks like a spending action
                    if self._indicates_spending(segment):
                        for amt, pos in all_amounts:
                            if amt not in used_amounts:
                                amount = amt
                                used_amounts.add(amt)
                                logger.debug(f"Assigned unused amount {amount} to segment: {segment[:50]}...")
                                break
                
                # Extract transaction with fixed English categories
                transaction = self.extractor.extract_transaction(segment, amount)
                
                # Only include meaningful transactions
                if self._is_meaningful_transaction(transaction):
                    transactions.append(transaction)
            
            # If no valid transactions found after filtering, return empty result
            if not transactions:
                logger.info("No valid financial transactions found after content filtering")
                return AnalysisResult(
                    transactions=[],
                    summary=FinancialSummary(
                        total_transactions=0,
                        total_income=0,
                        total_expenses=0,
                        net_amount=0,
                        categories={}
                    ),
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    language_detected=language
                )
            
            # Calculate summary
            summary = self._calculate_summary(transactions)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Convert to response format
            transaction_details = [
                TransactionDetail(**transaction.to_response_model())
                for transaction in transactions
            ]
            
            result = AnalysisResult(
                transactions=transaction_details,
                summary=summary,
                processing_time_ms=processing_time,
                language_detected=language
            )
            
            logger.info(f"Analysis completed: {len(transactions)} transactions, {processing_time}ms")
            return result
            
        except ValidationError:
            # Re-raise validation errors (including content filtering)
            raise
        except Exception as e:
            logger.error(f"NLP analysis failed: {e}", exc_info=True)
            raise NLPProcessingError(f"Failed to analyze text: {str(e)}")
    
    def _is_transaction_segment(self, segment: str) -> bool:
        """Check if segment represents a transaction"""
        segment_lower = segment.lower()
        
        # Must contain action verbs or amounts
        action_verbs = ['دفعت', 'اشتريت', 'جبت', 'استلمت', 'قبضت', 'صرفت', 'كلت', 'شربت', 'نضفت', 'صلحت', 'رحت']
        has_action = any(verb in segment_lower for verb in action_verbs)
        has_amount = bool(extract_amounts_from_text(segment))
        
        return has_action or has_amount
    
    def _indicates_spending(self, segment: str) -> bool:
        """Check if segment indicates spending"""
        spending_verbs = ['دفعت', 'اشتريت', 'جبت', 'صرفت', 'كلت', 'شربت', 'خلصت']
        return any(verb in segment.lower() for verb in spending_verbs)
    
    def _is_meaningful_transaction(self, transaction: Transaction) -> bool:
        """Check if transaction is meaningful enough to include"""
        # Must have amount or clear merchant/item
        has_amount = transaction.amount is not None
        has_context = transaction.merchant or transaction.item
        
        # Must not be just movement without spending
        return has_amount or has_context
    
    def _calculate_summary(self, transactions: List[Transaction]) -> FinancialSummary:
        """Calculate financial summary"""
        total_income = sum(
            t.amount for t in transactions 
            if t.transaction_type == TransactionType.INCOME and t.amount
        )
        
        total_expenses = sum(
            t.amount for t in transactions 
            if t.transaction_type == TransactionType.EXPENSE and t.amount
        )
        
        # Calculate categories
        categories = {}
        for transaction in transactions:
            if transaction.amount and transaction.category:
                categories[transaction.category] = categories.get(transaction.category, 0) + transaction.amount
        
        return FinancialSummary(
            total_transactions=len(transactions),
            total_income=total_income,
            total_expenses=total_expenses,
            net_amount=total_income - total_expenses,
            categories=categories
        )