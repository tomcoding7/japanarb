#!/usr/bin/env python3
"""
Test the web API to see if the real scraper works
"""

import requests
import json

def test_api():
    """Test the web API."""
    
    print("🧪 Testing Web API")
    print("=" * 50)
    
    try:
        # Test the search API
        url = "http://localhost:5000/api/search"
        data = {
            "search_term": "青眼の白龍",
            "max_results": 5
        }
        
        print(f"🔍 Making API request to: {url}")
        print(f"📝 Search term: {data['search_term']}")
        
        response = requests.post(url, json=data, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('message', 'No message')}")
            print(f"📈 Found {result.get('results_count', 0)} results")
            
            if result.get('results_count', 0) > 0:
                print("🎉 The real scraper is working!")
                print("📱 You can now use the web interface to find real deals!")
            else:
                print("⚠️  No results found - this might be normal if no deals are available")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to web server")
        print("💡 Make sure the web interface is running: python run_web_interface.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_api() 