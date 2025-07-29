#!/usr/bin/env python3
"""
Test script to verify GreenPulse deployment on Railway
"""
import requests
import json
import time
from datetime import datetime

# Railway URLs
BACKEND_URL = "https://greenpulse-backend.up.railway.app"
FRONTEND_URL = "https://greenpulse-frontend.up.railway.app"

def test_endpoint(url, name, timeout=10):
    """Test an endpoint and return result"""
    try:
        print(f"🔍 Testing {name}...")
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == 200:
            print(f"✅ {name}: OK ({response.status_code})")
            try:
                data = response.json()
                if isinstance(data, dict) and 'status' in data:
                    print(f"   Status: {data.get('status', 'unknown')}")
                return True
            except:
                print(f"   Response: {response.text[:100]}")
                return True
        elif response.status_code == 404:
            print(f"❌ {name}: Not Found (404)")
            return False
        else:
            print(f"⚠️  {name}: HTTP {response.status_code}")
            print(f"   Response: {response.text[:100]}")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print(f"⏰ {name}: Connection timeout")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🔌 {name}: Connection error")
        return False
    except Exception as e:
        print(f"💥 {name}: Error - {e}")
        return False

def main():
    """Run deployment tests"""
    print("🚀 GreenPulse Deployment Test")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Test backend endpoints
    print("🔧 Backend API Tests")
    print("-" * 30)
    
    backend_endpoints = [
        (f"{BACKEND_URL}/", "Root endpoint"),
        (f"{BACKEND_URL}/health", "Health check"),
        (f"{BACKEND_URL}/api/buildings", "Buildings API"),
        (f"{BACKEND_URL}/api/energy/campus/overview", "Campus overview"),
    ]
    
    for url, name in backend_endpoints:
        results[name] = test_endpoint(url, name)
        time.sleep(1)  # Rate limiting
    
    print()
    
    # Test frontend
    print("🎨 Frontend Tests")
    print("-" * 30)
    results["Frontend"] = test_endpoint(FRONTEND_URL, "Frontend app")
    
    print()
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Deployment is ready for demo.")
    else:
        print("⚠️  Some tests failed. Check the logs above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)