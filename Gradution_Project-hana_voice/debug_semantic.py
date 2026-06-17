#!/usr/bin/env python3
"""
Debug script to test semantic classification
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.nlp_service import CategoryClassifier
from app.utils.text_utils import extract_amounts_from_text

def test_classification():
    classifier = CategoryClassifier()
    
    # Test cases from user's example
    test_cases = [
        "النهارده انا جبت راجري ندفلي التكيف بتاعي وخد مني 4000 جنيه",
        "رحت السوير ماركت وجبت شبسي ب10 جنيه", 
        "رحت السيدالية جبت دوة ب200 جنيه"
    ]
    
    print("🧪 Testing Semantic Classification")
    print("=" * 50)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{i}. Text: {text}")
        
        # Test amount extraction
        amounts = extract_amounts_from_text(text)
        print(f"   Amounts: {[a[0] for a in amounts]}")
        
        # Test classification
        category = classifier.classify(text)
        print(f"   Category: {category}")
        
        # Test semantic analysis
        analysis = classifier._analyze_semantic_meaning(text.lower(), None)
        print(f"   Semantic Analysis:")
        for key, value in analysis.items():
            print(f"     {key}: {value}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_classification()