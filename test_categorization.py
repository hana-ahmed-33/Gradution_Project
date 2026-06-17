#!/usr/bin/env python3
"""
Test the improved categorization logic
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.nlp_service import NLPService

async def test_categorization():
    """Test the improved categorization with the user's examples"""
    
    nlp_service = NLPService()
    
    # Test cases from user complaints
    test_cases = [
        {
            "text": "انا رحت كارفور وجبت حاجات بخمسين جنيه وجبت قهوة بعشر جنيه وبعدين رحت جبت تسكرة قطر بخمسين جنيه واركبت القطر وكلت جوه للقطر حاجات بمية جنيه",
            "expected_issues": [
                "Coffee should be 'طعام وشراب', not 'أخرى'",
                "Train ticket should be 'مواصلات', not 'طعام وشراب'",
                "No 'أخرى' category should exist"
            ]
        },
        {
            "text": "رحت الصيدلية واشتريت دواء بعشرين جنيه",
            "expected": "صحة وجمال"
        },
        {
            "text": "دفعت خمسين جنيه تذكرة قطار للإسكندرية",
            "expected": "مواصلات"
        },
        {
            "text": "شربت قهوة في الكافيه بخمسة جنيه",
            "expected": "طعام وشراب"
        }
    ]
    
    print("🧪 Testing Improved Categorization Logic")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Text: {test_case['text']}")
        
        try:
            result = await nlp_service.analyze_text(test_case['text'])
            
            print(f"✅ Analysis completed!")
            print(f"📊 Found {len(result.transactions)} transactions:")
            
            for j, transaction in enumerate(result.transactions, 1):
                print(f"  {j}. Amount: {transaction.amount} EGP")
                print(f"     Category: {transaction.category}")
                print(f"     Item: {transaction.item}")
                print(f"     Place: {transaction.merchant}")
                print(f"     Text: {transaction.extracted_text}")
                print()
            
            # Check for issues
            categories = [t.category for t in result.transactions]
            if 'أخرى' in categories:
                print("❌ ISSUE: Found 'أخرى' category - should be eliminated!")
            
            if test_case.get('expected'):
                if test_case['expected'] in categories:
                    print(f"✅ GOOD: Found expected category '{test_case['expected']}'")
                else:
                    print(f"❌ ISSUE: Expected '{test_case['expected']}' but got {categories}")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(test_categorization())