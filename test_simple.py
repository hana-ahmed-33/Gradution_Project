#!/usr/bin/env python3
"""
Simple test for the Finance Analyzer API
"""
import json
import urllib.request
import urllib.parse

def test_text_analysis():
    """Test the text analysis endpoint"""
    print("🧪 Testing Finance Analyzer Text Analysis...")
    
    # Test data
    test_data = {
        "text": "دفعت 50 جنيه في كارفور على خضار",
        "language": "ar"
    }
    
    try:
        # Prepare request
        url = "http://localhost:8000/analyze"
        data = json.dumps(test_data).encode('utf-8')
        
        req = urllib.request.Request(
            url, 
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Make request
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            print("\n✅ Text Analysis Success!")
            print("📝 Input:", test_data['text'])
            print("📊 Response:", json.dumps(result, ensure_ascii=False, indent=2))
            return True
            
    except Exception as e:
        print(f"\n❌ Text Analysis Failed: {e}")
        return False

def test_health():
    """Test the health endpoint"""
    print("\n🏥 Testing Health Endpoint...")
    
    try:
        with urllib.request.urlopen("http://localhost:8000/health", timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            print("✅ Health Check Success!")
            print("📊 Status:", result.get('status', 'unknown'))
            return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Finance Analyzer API Test Suite")
    print("=" * 50)
    
    # Test health first
    if test_health():
        # Test text analysis
        test_text_analysis()
    else:
        print("❌ Server not responding. Make sure it's running on localhost:8000")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")