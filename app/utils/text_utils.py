"""
Text processing utilities - Simple working version
"""
import re
from typing import List, Tuple
from app.core.logging import get_logger

logger = get_logger("text_utils")


def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic text for better processing"""
    if not text:
        return ""
    
    # Convert Arabic-Indic digits to English
    arabic_indic = '٠١٢٣٤٥٦٧٨٩'
    english = '0123456789'
    
    for arabic, eng in zip(arabic_indic, english):
        text = text.replace(arabic, eng)
    
    # Handle Arabic decimal separators
    text = text.replace('٫', '.').replace('،', ',')
    
    # Normalize Arabic characters
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    
    return text


def extract_amounts_from_text(text: str) -> List[Tuple[float, int]]:
    """Extract all amounts from text with their positions - enhanced for mixed languages"""
    text = normalize_arabic_text(text)
    text_lower = text.lower()
    
    amounts = []
    
    # Arabic number words (enhanced with more variations)
    number_words = {
        'واحد': 1, 'واحدة': 1, 'اتنين': 2, 'اثنين': 2, 'تنين': 2,
        'ثلاثة': 3, 'تلاتة': 3, 'تلاته': 3, 'ثلاث': 3,
        'اربعة': 4, 'اربع': 4, 'أربعة': 4, 'أربع': 4,
        'خمسة': 5, 'خمس': 5, 'خمسه': 5,
        'ستة': 6, 'ست': 6, 'سته': 6,  # Enhanced: ست can be number 6 OR cleaning lady
        'سبعة': 7, 'سبع': 7, 'سبعه': 7,
        'ثمانية': 8, 'تمانية': 8, 'ثمان': 8, 'تمان': 8,
        'تسعة': 9, 'تسع': 9, 'تسعه': 9,
        'عشرة': 10, 'عشر': 10, 'عشره': 10,
        'عشرين': 20, 'عشرون': 20,
        'ثلاثين': 30, 'ثلاثون': 30, 'تلاتين': 30,
        'اربعين': 40, 'اربعون': 40, 'أربعين': 40,
        'خمسين': 50, 'خمسون': 50,
        'ستين': 60, 'ستون': 60,
        'سبعين': 70, 'سبعون': 70,
        'ثمانين': 80, 'ثمانون': 80, 'تمانين': 80,
        'تسعين': 90, 'تسعون': 90,
        'مية': 100, 'ميه': 100, 'مائة': 100, 'مئة': 100,
        'ميتين': 200, 'مئتين': 200, 'مائتين': 200, 'متين': 200,  # إضافة "متين"
        'تلتمية': 300, 'ثلثمائة': 300, 'تلاتمية': 300,
        'اربعمية': 400, 'أربعمائة': 400,
        'خمسمية': 500, 'خمسمائة': 500,
        'ستمية': 600, 'ستمائة': 600,
        'سبعمية': 700, 'سبعمائة': 700,
        'تمنمية': 800, 'ثمانمائة': 800,
        'تسعمية': 900, 'تسعمائة': 900,
        'الف': 1000, 'ألف': 1000,
        'الفين': 2000, 'ألفين': 2000,
        # English number words
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
        'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
        'hundred': 100, 'thousand': 1000, 'two hundred': 200
    }
    
    # Extract from Arabic and English words
    words = text_lower.split()
    current_pos = 0
    
    for i, word in enumerate(words):
        clean_word = re.sub(r'[^\w\s]', '', word)
        
        # Special handling for "ست" - context-dependent
        if clean_word == 'ست':
            # Check if it's followed by cleaning context
            next_words = ' '.join(words[i:i+3]) if i+2 < len(words) else ' '.join(words[i:])
            if any(cleaning_word in next_words for cleaning_word in ['تنضف', 'نظاف', 'تنظيف']):
                # It's "cleaning lady", not number 6 - skip number extraction
                logger.debug(f"Skipping 'ست' as it refers to cleaning lady, not number 6")
                current_pos += len(word) + 1
                continue
        
        # Also try with preposition removed
        if word.startswith(('ب', 'ل', 'ك')):
            clean_word_no_prep = word[1:]
            clean_word_no_prep = re.sub(r'[^\w\s]', '', clean_word_no_prep)
            if clean_word_no_prep in number_words:
                amounts.append((number_words[clean_word_no_prep], current_pos))
                logger.debug(f"Found Arabic number: {clean_word_no_prep} = {number_words[clean_word_no_prep]}")
        
        if clean_word in number_words:
            amounts.append((number_words[clean_word], current_pos))
            logger.debug(f"Found number word: {clean_word} = {number_words[clean_word]}")
        current_pos += len(word) + 1
    
    # Enhanced digit patterns - more comprehensive
    digit_patterns = [
        r'(\d+(?:[,.]?\d+)?)',  # Basic digits
        r'بسعر\s*(\d+)',        # بسعر 200
        r'سعر\s*(\d+)',         # سعر 50
        r'price\s*(\d+)',       # price 200
        r'cost\s*(\d+)',        # cost 50
        r'(\d+)\s*جنيه',        # 200 جنيه
        r'(\d+)\s*pound',       # 200 pound
        r'(\d+)\s*egp',         # 200 EGP
    ]
    
    for pattern in digit_patterns:
        for match in re.finditer(pattern, text_lower):
            try:
                amount_str = match.group(1).replace(',', '').strip()
                if amount_str:
                    amount = float(amount_str)
                    if amount > 0:
                        amounts.append((amount, match.start()))
                        logger.debug(f"Found digit amount: {amount}")
            except (ValueError, IndexError):
                continue
    
    # Remove duplicates and sort by position
    unique_amounts = []
    seen_positions = set()
    
    for amount, pos in sorted(amounts, key=lambda x: x[1]):
        position_key = pos // 5  # Group nearby positions
        if position_key not in seen_positions:
            seen_positions.add(position_key)
            unique_amounts.append((amount, pos))
    
    logger.debug(f"Extracted {len(unique_amounts)} amounts: {[a[0] for a in unique_amounts]}")
    return unique_amounts


def split_text_into_segments(text: str) -> List[str]:
    """Split text into transaction segments - enhanced for mixed languages"""
    # Arabic and English patterns - more comprehensive
    patterns = [
        r'وبعدين\s*',
        r'و\s*(?=جبت|رحت|ركبت|كلت|اشتريت|دفعت|شريت|أحصل|أذهب|نضفت|صلحت)',
        r'بعد\s*كده\s*',
        r'وكمان\s*',
        r'ثم\s*',
        r'بعدها\s*',
        r'و\s*(?=نضفت|صلحت|رممت)',  # Added repair/cleaning actions
        # English patterns
        r'and\s+then\s*',
        r'and\s+(?=i\s+go|i\s+get|i\s+buy|i\s+clean|i\s+fix)',
        r'then\s*',
        r'after\s+that\s*',
        r'next\s*',
        # Mixed patterns
        r'و\s*(?=i\s+go|i\s+get)',
    ]
    
    combined_pattern = '|'.join(patterns)
    segments = re.split(combined_pattern, text, flags=re.IGNORECASE)
    
    transactions = []
    for segment in segments:
        segment = segment.strip()
        if segment and len(segment) > 5:
            # Further split if multiple actions in one segment
            # Look for multiple verbs in Arabic
            if re.search(r'(جبت|رحت|نضفت|صلحت|اشتريت|دفعت).*?(جبت|رحت|نضفت|صلحت|اشتريت|دفعت)', segment):
                # Split on action verbs but keep the verb with its context
                action_splits = re.split(r'(?=جبت|رحت|نضفت|صلحت|اشتريت|دفعت)', segment)
                for split in action_splits:
                    split = split.strip()
                    if split and len(split) > 5:
                        transactions.append(split)
            else:
                transactions.append(segment)
    
    logger.debug(f"Split into {len(transactions)} segments: {transactions}")
    return transactions if transactions else [text]


def detect_language(text: str) -> str:
    """Detect language of text"""
    if not text:
        return "unknown"
    
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    total_chars = len(re.findall(r'[a-zA-Z\u0600-\u06FF]', text))
    
    if total_chars == 0:
        return "unknown"
    
    arabic_ratio = arabic_chars / total_chars
    
    if arabic_ratio > 0.5:
        return "ar"
    elif arabic_ratio < 0.1:
        return "en"
    else:
        return "mixed"