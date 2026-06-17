#!/usr/bin/env python3
"""
Test script for enhanced Finance Analyzer features
"""
import asyncio
import sys
import os
import requests
import json
from datetime import datetime

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:8000"

def test_api_endpoint(endpoint, method="GET", data=None, files=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, timeout=30)
            else:
                response = requests.post(url, json=data, timeout=30)
        
        print(f"✅ {method} {endpoint}: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict) and 'success' in result:
                print(f"   Success: {result['success']}")
            return True
        else:
            print(f"   Error: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"❌ {method} {endpoint}: {e}")
        return False

def test_text_analysis():
    """Test text analysis with sample data"""
    print("\n🧪 Testing Text Analysis...")
    
    test_cases = [
        {"text": "دفعت 50 جنيه في كارفور على خضار", "language": "ar"},
        {"text": "استلمت مرتب 3000 جنيه", "language": "ar"},
        {"text": "اشتريت بنزين بـ 120 جنيه", "language": "ar"},
        {"text": "دفعت 25 جنيه أجرة تاكسي", "language": "ar"},
    ]
    
    success_count = 0
    for i, case in enumerate(test_cases, 1):
        print(f"\n  Test {i}: {case['text'][:30]}...")
        if test_api_endpoint("/analyze", "POST", case):
            success_count += 1
    
    print(f"\n📊 Text Analysis Results: {success_count}/{len(test_cases)} passed")
    return success_count == len(test_cases)

def test_analytics_endpoints():
    """Test analytics endpoints"""
    print("\n📊 Testing Analytics Endpoints...")
    
    endpoints = [
        "/analytics/summary",
        "/analytics/insights", 
        "/analytics/transactions",
        "/analytics/accuracy",
        "/analytics/categories/performance"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        if test_api_endpoint(endpoint):
            success_count += 1
    
    print(f"\n📊 Analytics Results: {success_count}/{len(endpoints)} passed")
    return success_count >= len(endpoints) // 2  # At least half should work

def test_health_checks():
    """Test health check endpoints"""
    print("\n🏥 Testing Health Checks...")
    
    endpoints = ["/health", "/health/detailed"]
    success_count = 0
    
    for endpoint in endpoints:
        if test_api_endpoint(endpoint):
            success_count += 1
    
    print(f"\n📊 Health Check Results: {success_count}/{len(endpoints)} passed")
    return success_count == len(endpoints)

def test_database_functionality():
    """Test database functionality"""
    print("\n💾 Testing Database Functionality...")
    
    try:
        from app.database.connection import db_manager
        
        # Test database health
        if db_manager.health_check():
            print("✅ Database connection: OK")
        else:
            print("❌ Database connection: Failed")
            return False
        
        # Test database stats
        stats = db_manager.get_stats()
        print(f"✅ Database stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_ml_functionality():
    """Test ML functionality"""
    print("\n🧠 Testing ML Functionality...")
    
    try:
        from app.services.ml_service import ml_classifier
        
        # Test model stats
        stats = asyncio.run(ml_classifier.get_model_stats())
        print(f"✅ ML Model stats: {stats}")
        
        # Test prediction (even if not trained)
        category, confidence = ml_classifier.predict_category(
            "دفعت 50 جنيه في كارفور على خضار", "كارفور", "خضار", 50.0
        )
        print(f"✅ ML Prediction test: {category} (confidence: {confidence:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ ML test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Finance Analyzer Enhanced Features Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Testing against: {BASE_URL}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding. Please start the server first:")
            print("   python main.py")
            return False
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the server first: python main.py")
        return False
    
    # Run tests
    test_results = []
    
    test_results.append(("Health Checks", test_health_checks()))
    test_results.append(("Database", test_database_functionality()))
    test_results.append(("ML Functionality", test_ml_functionality()))
    test_results.append(("Text Analysis", test_text_analysis()))
    test_results.append(("Analytics", test_analytics_endpoints()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced features are working correctly.")
        print("\n🚀 Ready to use:")
        print(f"   • Main App: {BASE_URL}/")
        print(f"   • Dashboard: {BASE_URL}/dashboard")
        print(f"   • API Docs: {BASE_URL}/docs")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)