#!/usr/bin/env python3
"""
Test the text analysis API with improved categorization
"""
import requests
import json

def test_text_analysis():
    """Test the /analyze endpoint with the user's examples"""
    
    url = "http://localhost:8000/analyze"
    
    # Test cases from user complaints
    test_cases = [
        {
            "name": "User's original complaint",
            "text": "انا رحت كارفور وجبت حاجات بخمسين جنيه وجبت قهوة بعشر جنيه وبعدين رحت جبت تسكرة قطر بخمسين جنيه واركبت القطر وكلت جوه للقطر حاجات بمية جنيه",
            "issues": [
                "Coffee should be 'طعام وشراب', not 'أخرى'",
                "Train ticket should be 'مواصلات', not 'طعام وشراب'",
                "No 'أخرى' category should exist"
            ]
        },
        {
            "name": "Pharmacy test",
            "text": "رحت الصيدلية واشتريت دواء بعشرين جنيه",
            "expected": "صحة وجمال"
        },
        {
            "name": "Train ticket test",
            "text": "دفعت خمسين جنيه تذكرة قطار للإسكندرية",
            "expected": "مواصلات"
        },
        {
            "name": "Coffee test",
            "text": "شربت قهوة في الكافيه بخمسة جنيه",
            "expected": "طعام وشراب"
        }
    ]
    
    print("🧪 Testing Improved Text Analysis API")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['name']}")
        print(f"Text: {test_case['text']}")
        
        try:
            response = requests.post(url, json={
                "text": test_case['text'],
                "language": "ar"
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                analysis = data['data']['analysis']
                
                print(f"✅ Analysis completed!")
                print(f"📊 Found {len(analysis['transactions'])} transactions:")
                
                categories_found = []
                for j, transaction in enumerate(analysis['transactions'], 1):
                    print(f"  {j}. Amount: {transaction['amount']} EGP")
                    print(f"     Category: {transaction['category']}")
                    print(f"     Item: {transaction['item']}")
                    print(f"     Place: {transaction['merchant']}")
                    print(f"     Text: {transaction['extracted_text']}")
                    categories_found.append(transaction['category'])
                    print()
                
                # Check for issues
                if 'أخرى' in categories_found:
                    print("❌ ISSUE: Found 'أخرى' category - should be eliminated!")
                else:
                    print("✅ GOOD: No 'أخرى' category found!")
                
                if test_case.get('expected'):
                    if test_case['expected'] in categories_found:
                        print(f"✅ GOOD: Found expected category '{test_case['expected']}'")
                    else:
                        print(f"❌ ISSUE: Expected '{test_case['expected']}' but got {categories_found}")
                
                print(f"📈 Summary: {analysis['summary']}")
                
            else:
                print(f"❌ ERROR: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_text_analysis()