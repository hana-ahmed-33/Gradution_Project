#!/usr/bin/env python3
"""
Quick API test script
"""
import requests
import json

def test_health():
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"Health Check: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_text_analysis():
    try:
        data = {
            "text": "دفعت 50 جنيه في كارفور على خضار",
            "language": "ar"
        }
        response = requests.post(
            "http://localhost:8000/analyze", 
            json=data, 
            timeout=10
        )
        print(f"Text Analysis: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return response.status_code == 200
    except Exception as e:
        print(f"Text analysis failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Finance Analyzer API...")
    
    if test_health():
        print("✅ Health check passed")
        if test_text_analysis():
            print("✅ Text analysis passed")
        else:
            print("❌ Text analysis failed")
    else:
        print("❌ Health check failed")