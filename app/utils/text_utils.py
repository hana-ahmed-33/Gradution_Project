"""
Text processing utilities — Arabic (Egyptian dialect + MSA) and English support.
"""
import re
from typing import List, Tuple
from app.core.logging import get_logger

logger = get_logger("text_utils")

# ─────────────────────────────────────────────
# Shared number-words dictionary (MSA + Egyptian dialect)
# Used by extract_amounts_from_text AND nlp_service item-filter
# ─────────────────────────────────────────────
_NUMBER_WORDS: dict = {
    # 1-9
    'واحد': 1, 'واحده': 1, 'واحدة': 1,
    'اتنين': 2, 'اثنين': 2, 'تنين': 2, 'اثنان': 2,
    'ثلاثة': 3, 'تلاتة': 3, 'تلاته': 3, 'ثلاث': 3, 'تلات': 3,
    'اربعة': 4, 'اربع': 4, 'أربعة': 4, 'أربع': 4, 'اربعه': 4,
    'خمسة': 5, 'خمس': 5, 'خمسه': 5,
    'ستة': 6, 'ست': 6, 'سته': 6,
    'سبعة': 7, 'سبع': 7, 'سبعه': 7,
    'ثمانية': 8, 'تمانية': 8, 'ثمان': 8, 'تمان': 8, 'تمانيه': 8, 'ثمانيه': 8,
    'تسعة': 9, 'تسع': 9, 'تسعه': 9,
    # 10-19
    'عشرة': 10, 'عشر': 10, 'عشره': 10,
    'احدعشر': 11, 'احداشر': 11,
    'اتناشر': 12, 'اثناعشر': 12,
    'تلتاشر': 13, 'ثلاثةعشر': 13,
    'اربعتاشر': 14,
    'خمستاشر': 15,
    'ستاشر': 16,
    'سبعتاشر': 17,
    'تمنتاشر': 18,
    'تسعتاشر': 19,
    # tens
    'عشرين': 20, 'عشرون': 20,
    'ثلاثين': 30, 'ثلاثون': 30, 'تلاتين': 30,
    'اربعين': 40, 'اربعون': 40, 'أربعين': 40, 'ربعين': 40,
    'خمسين': 50, 'خمسون': 50,
    'ستين': 60, 'ستون': 60,
    'سبعين': 70, 'سبعون': 70,
    'ثمانين': 80, 'ثمانون': 80, 'تمانين': 80,
    'تسعين': 90, 'تسعون': 90,
    # hundreds — فصحى + مصري + عامي
    'مية': 100, 'ميه': 100, 'مائة': 100, 'مئة': 100, 'ميت': 100, 'مئت': 100,
    'ميتين': 200, 'مئتين': 200, 'مائتين': 200, 'متين': 200, 'ميتان': 200,
    'تلتمية': 300, 'ثلثمائة': 300, 'تلاتمية': 300, 'تلتميه': 300,
    'تلتميت': 300, 'تلاتميت': 300, 'ثلاثمية': 300, 'ثلثمية': 300,
    'اربعمية': 400, 'أربعمائة': 400, 'اربعميه': 400, 'اربعميت': 400, 'أربعميت': 400,
    'ربعمية': 400, 'ربعميه': 400, 'ربعميت': 400,
    'خمسمية': 500, 'خمسمائة': 500, 'خمسميه': 500, 'خمسميت': 500,
    'ستمية': 600, 'ستمائة': 600, 'ستميه': 600, 'ستميت': 600,
    'سبعمية': 700, 'سبعمائة': 700, 'سبعميه': 700, 'سبعميت': 700,
    'تمنمية': 800, 'ثمانمائة': 800, 'تمنميه': 800, 'تمنميت': 800, 'تمانميت': 800,
    'تسعمية': 900, 'تسعمائة': 900, 'تسعميه': 900, 'تسعميت': 900,
    # thousands
    'الف': 1000, 'ألف': 1000,
    'الفين': 2000, 'ألفين': 2000,
    # English
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
    'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
    'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
    'hundred': 100, 'thousand': 1000,
}

# Words that must NOT be extracted as numbers (ambiguous or item names)
_NUMBER_WORDS_MIN_LEN = 3   # only treat as number if stripped word >= 3 chars


def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic text — digits, hamza variants, ta marbuta."""
    if not text:
        return ""
    # Arabic-Indic → ASCII digits
    for ar, en in zip('٠١٢٣٤٥٦٧٨٩', '0123456789'):
        text = text.replace(ar, en)
    text = text.replace('٫', '.').replace('،', ',')
    # Hamza normalization
    for variant in ('أ', 'إ', 'آ', 'ٱ'):
        text = text.replace(variant, 'ا')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    return text


def extract_amounts_from_text(text: str) -> List[Tuple[float, int]]:
    """
    Extract monetary amounts from text (Arabic word-numbers + digits).
    Handles compound numbers like مية وخمسين = 150, الف وميتين = 1200.
    Returns list of (amount, char_position) sorted by position.
    """
    text = normalize_arabic_text(text)
    text_lower = text.lower()
    amounts: list = []

    # ── PASS 1: Compound word-numbers ──
    # Handles: مية وخمسين=150, الف وميتين=1200, الف وخمسميت=1500, بمية وخمسين=150
    # Also handles: ثلاثة الاف=3000, خمسة آلاف=5000, عشرة آلاف=10000
    norm_nw = {normalize_arabic_text(k): v for k, v in _NUMBER_WORDS.items()}

    # Multiplier words (thousands, millions)
    _MULTIPLIERS = {
        normalize_arabic_text(k): v for k, v in {
            'الف': 1000, 'ألف': 1000, 'آلاف': 1000, 'الاف': 1000, 'ألاف': 1000,
            'مليون': 1_000_000, 'مليار': 1_000_000_000,
        }.items()
    }

    compound_spans: list = []
    _words = text_lower.split()
    _pos_map = []
    _p = 0
    for _w in _words:
        _pos_map.append((_w, _p))
        _p += len(_w) + 1

    _i = 0
    while _i < len(_pos_map):
        _w1, _pos1 = _pos_map[_i]
        # strip leading preposition from w1
        _w1c = _w1
        for _pfx in ('وب', 'فب', 'ب', 'ل', 'ك'):
            if _w1.startswith(_pfx) and len(_w1) > len(_pfx) + 1:
                _w1c = _w1[len(_pfx):]
                break
        _w1c = re.sub(r'[^\w]', '', _w1c)
        _v1 = norm_nw.get(_w1c, 0)

        if _v1 > 0 and _i + 1 < len(_pos_map):
            _w2_raw, _pos2 = _pos_map[_i + 1]
            _w2c = re.sub(r'[^\w]', '', _w2_raw)
            # Case M: next word is a multiplier (ثلاثة الاف = 3000)
            mult = _MULTIPLIERS.get(_w2c, 0)
            if mult > 0:
                total = float(_v1 * mult)
                # Check for remainder: ثلاثة آلاف وخمسمية = 3500
                end_pos = _pos2 + len(_w2_raw)
                remainder = 0.0
                skip_extra = 0
                if _i + 2 < len(_pos_map):
                    _w3_raw, _pos3 = _pos_map[_i + 2]
                    _w3c = re.sub(r'[^\w]', '', _w3_raw)
                    if _w3c == 'و' and _i + 3 < len(_pos_map):
                        _w4_raw, _pos4 = _pos_map[_i + 3]
                        _w4c = re.sub(r'[^\w]', '', _w4_raw)
                        _r = norm_nw.get(_w4c, 0)
                        if _r > 0:
                            remainder = float(_r)
                            end_pos = _pos4 + len(_w4_raw)
                            skip_extra = 2
                    elif _w3c.startswith('و') and len(_w3c) > 1:
                        _r = norm_nw.get(_w3c[1:], 0)
                        if _r > 0:
                            remainder = float(_r)
                            end_pos = _pos3 + len(_w3_raw)
                            skip_extra = 1
                amounts.append((total + remainder, _pos1))
                compound_spans.append((_pos1, end_pos))
                logger.debug(f"Multiplier: {_w1c}({_v1})×{_w2c}({mult})+{remainder}={total+remainder}")
                _i += 2 + skip_extra
                continue
            # Case A: next word is standalone 'و'
            if _w2c == 'و' and _i + 2 < len(_pos_map):
                _w3_raw, _pos3 = _pos_map[_i + 2]
                _w3c = re.sub(r'[^\w]', '', _w3_raw)
                _v2 = norm_nw.get(_w3c, 0)
                if _v2 > 0:
                    amounts.append((float(_v1 + _v2), _pos1))
                    compound_spans.append((_pos1, _pos3 + len(_w3_raw)))
                    logger.debug(f"Compound A: {_w1c}({_v1})+{_w3c}({_v2})={_v1+_v2}")
                    _i += 3
                    continue
            # Case B: next word starts with glued 'و' (e.g. وخمسين)
            elif _w2c.startswith('و') and len(_w2c) > 1:
                _num_part = _w2c[1:]
                _v2 = norm_nw.get(_num_part, 0)
                if _v2 > 0:
                    amounts.append((float(_v1 + _v2), _pos1))
                    compound_spans.append((_pos1, _pos2 + len(_w2_raw)))
                    logger.debug(f"Compound B: {_w1c}({_v1})+{_num_part}({_v2})={_v1+_v2}")
                    _i += 2
                    continue
        # Also handle standalone multiplier with glued number: آلاف handled as الف(1000) already in dict
        # Handle standalone 'الف'/'ألف' without preceding number = 1000
        if _w1c in _MULTIPLIERS and _v1 == 0:
            mult_val = _MULTIPLIERS[_w1c]
            # standalone 'الف' by itself means 1000
            amounts.append((float(mult_val), _pos1))
            compound_spans.append((_pos1, _pos1 + len(_w1)))
            logger.debug(f"Standalone multiplier: {_w1c}={mult_val}")
        _i += 1

    # ── PASS 2: Single word-numbers ──
    words = text_lower.split()
    current_pos = 0

    for i, word in enumerate(words):
        clean = re.sub(r'[^\w]', '', word)

        # Context guard for 'ست' (cleaning lady vs number 6)
        if clean == 'ست':
            window = ' '.join(words[i:i + 4])
            if any(w in window for w in ('تنضف', 'نظاف', 'تنظيف', 'تنضيف')):
                current_pos += len(word) + 1
                continue

        # Skip words that are part of an already-matched compound
        in_compound = any(start <= current_pos < end for start, end in compound_spans)

        # Strip genuine prepositions only (ب، ل، ك، وب، فب) — NOT و or ف alone
        for pfx in ('وب', 'فب', 'ب', 'ل', 'ك'):
            if word.startswith(pfx) and len(word) > len(pfx) + 1:
                stripped = re.sub(r'[^\w]', '', word[len(pfx):])
                if stripped in norm_nw and len(stripped) >= _NUMBER_WORDS_MIN_LEN and not in_compound:
                    amounts.append((norm_nw[stripped], current_pos))
                    logger.debug(f"prefix '{pfx}' → {stripped}={norm_nw[stripped]}")
                    break

        if clean in norm_nw and len(clean) >= _NUMBER_WORDS_MIN_LEN and not in_compound:
            amounts.append((norm_nw[clean], current_pos))
            logger.debug(f"word '{clean}'={norm_nw[clean]}")

        current_pos += len(word) + 1

    # ── PASS 3: Digit patterns ──
    for pattern in (
        r'(\d+(?:[.,]\d+)?)\s*(?:جنيه|جنيهات|جنيها)',
        r'(\d+(?:[.,]\d+)?)\s*(?:ريال|ريالات)',
        r'(\d+(?:[.,]\d+)?)\s*(?:دولار|دولارات)',
        r'(\d+(?:[.,]\d+)?)\s*(?:pound|egp|usd|sar)',
        r'(?:بـ?|ب)\s*(\d+)',
        r'(\d+(?:[.,]\d+)?)',
    ):
        for m in re.finditer(pattern, text_lower, re.IGNORECASE):
            try:
                val = float(m.group(1).replace(',', '').replace('.', ''))
                if val > 0:
                    amounts.append((val, m.start()))
            except (ValueError, IndexError):
                pass

    # ── Deduplicate by position bucket ──
    unique: list = []
    seen: set = set()
    for amount, pos in sorted(amounts, key=lambda x: x[1]):
        bucket = pos // 6
        if bucket not in seen:
            seen.add(bucket)
            unique.append((amount, pos))

    logger.debug(f"Amounts: {[a[0] for a in unique]}")
    return unique


# ─────────────────────────────────────────────
# Action verbs — used by segmentation AND NLPService
# ─────────────────────────────────────────────
ACTION_VERBS: tuple = (
    # buying / getting
    'اشتريت', 'شتريت', 'شريت', 'جبت', 'اخدت', 'حجزت', 'طلبت',
    # paying
    'دفعت', 'صرفت', 'سددت', 'دفع',
    # eating / drinking
    'كلت', 'اكلت', 'شربت', 'اتغديت', 'اتعشيت', 'فطرت',
    # moving / commuting
    'رحت', 'روحت', 'ذهبت', 'مشيت', 'ركبت', 'اتقلت',
    # maintenance
    'نضفت', 'صلحت', 'رممت', 'غيرت',
    # income
    'استلمت', 'قبضت', 'حصلت', 'اخدت',
    # English
    'bought', 'paid', 'spent', 'ate', 'drank', 'went', 'took', 'got',
    'ordered', 'booked', 'received', 'earned',
)


def split_text_into_segments(text: str) -> List[str]:
    """
    Split compound Arabic/English text into individual transaction segments.
    Handles:
      - Verb-led splits: و + action verb
      - Price-led splits: و after amount/جنيه (for lists like "فستان ب100 وبلوزة ب50")
      - Explicit connectors: وبعدين، بعد كده، وكمان، ثم، بعدها
    """
    verbs_la = '|'.join(ACTION_VERBS)

    patterns = [
        # Explicit connectors first (highest priority)
        r'وبعدين\s*',
        r'بعد\s*كده\s*',
        r'وكمان\s*',
        r'بعدها\s*',
        r'وبعد\s*كده\s*',
        r'ثم\s+',
        # و before an action verb
        rf'و\s*(?={verbs_la})',
        # و after a number / currency word (price-list pattern)
        r'(?<=\d)\s*و\s*(?=[\u0600-\u06FF])',
        r'(?<=جنيه)\s*و\s*(?=[\u0600-\u06FF])',
        r'(?<=ريال)\s*و\s*(?=[\u0600-\u06FF])',
        r'(?<=دولار)\s*و\s*(?=[\u0600-\u06FF])',
        # English connectors
        r'\band\s+then\s+',
        r'\bafter\s+that\s+',
        r'\bthen\s+(?=i\s)',
        r'\band\s+(?=(?:i\s+)?(?:bought|paid|ate|drank|went|took|got|ordered))',
    ]

    combined = '|'.join(patterns)
    raw_segments = re.split(combined, text, flags=re.IGNORECASE)

    segments: list = []
    for seg in raw_segments:
        seg = seg.strip()
        if not seg or len(seg) < 3:
            continue

        # Secondary split: if a segment still contains multiple action verbs
        multi = rf'(?<!\w)(?={verbs_la})'
        if re.search(rf'({verbs_la}).+?({verbs_la})', seg, re.IGNORECASE):
            sub_parts = re.split(multi, seg, flags=re.IGNORECASE)
            for sp in sub_parts:
                sp = sp.strip()
                if sp and len(sp) >= 3:
                    segments.append(sp)
        else:
            segments.append(seg)

    logger.debug(f"Segments ({len(segments)}): {segments}")
    return segments if segments else [text]


def detect_language(text: str) -> str:
    """Detect primary language: ar / en / mixed."""
    if not text:
        return 'unknown'
    arabic = len(re.findall(r'[\u0600-\u06FF]', text))
    latin  = len(re.findall(r'[a-zA-Z]', text))
    total  = arabic + latin
    if total == 0:
        return 'unknown'
    ratio = arabic / total
    if ratio > 0.6:
        return 'ar'
    if ratio < 0.2:
        return 'en'
    return 'mixed'
