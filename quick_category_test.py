#!/usr/bin/env python3
"""
Quick test of categorization logic
"""
import sys
import os
sys.path.insert(0, 'app')

from app.services.nlp_service import CategoryClassifier

def test_classifier():
    classifier = CategoryClassifier()
    
    test_cases = [
        ("جبت قهوة بعشر جنيه", "Should be طعام وشراب"),
        ("جبت تسكرة قطر بخمسين جنيه", "Should be مواصلات"),
        ("رحت الصيدلية واشتريت دواء", "Should be صحة وجمال"),
        ("دفعت تذكرة قطار", "Should be مواصلات"),
        ("كلت جوه للقطر حاجات", "Should be طعام وشراب (food on train)"),
    ]
    
    print("🧪 Testing Category Classification")
    print("=" * 40)
    
    for text, expected in test_cases:
        category = classifier.classify(text)
        print(f"Text: {text}")
        print(f"Category: {category}")
        print(f"Expected: {expected}")
        print("-" * 30)

if __name__ == "__main__":
    test_classifier()