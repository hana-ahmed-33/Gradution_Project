import json

# Test data
test_data = {
    "text": "دفعت 50 جنيه في كارفور على خضار",
    "language": "ar"
}

print("Testing Finance Analyzer API...")
print("Test data:", json.dumps(test_data, ensure_ascii=False, indent=2))

try:
    import urllib.request
    import urllib.parse
    
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
        print("\n✅ Success! Response:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
except Exception as e:
    print(f"\n❌ Error: {e}")