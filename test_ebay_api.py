#!/usr/bin/env python3
"""
Test script for eBay API integration.

This script tests the eBay API functionality and provides examples
of how to use it in your arbitrage bot.
"""

import os
import sys
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ebay_api import EbayAPI

def test_ebay_api():
    """Test the eBay API integration."""
    print("🧪 Testing eBay API Integration")
    print("=" * 50)
    
    # Initialize eBay API
    ebay = EbayAPI()
    
    # Test 1: Authentication
    print("\n1. Testing Authentication...")
    if ebay.authenticate():
        print("✅ Authentication successful!")
    else:
        print("❌ Authentication failed!")
        print("   Make sure your eBay API credentials are set in environment variables:")
        print("   - EBAY_CLIENT_ID")
        print("   - EBAY_CLIENT_SECRET") 
        print("   - EBAY_DEV_ID")
        print("   - EBAY_ENVIRONMENT (sandbox/production)")
        return False
    
    # Test 2: Search for sold items
    print("\n2. Testing Search for Sold Items...")
    test_query = "Blue-Eyes White Dragon"
    sold_items = ebay.search_sold_items(test_query, max_results=5)
    
    if sold_items:
        print(f"✅ Found {len(sold_items)} sold items for '{test_query}'")
        for i, item in enumerate(sold_items[:3], 1):
            print(f"   {i}. {item['title'][:50]}... - ${item['price']} ({item['condition']})")
    else:
        print("❌ No sold items found")
    
    # Test 3: Get card prices
    print("\n3. Testing Card Price Analysis...")
    card_prices = ebay.get_card_prices("Blue-Eyes White Dragon", "LOB")
    
    raw_prices = card_prices['raw']
    psa_prices = card_prices['psa']
    
    print(f"✅ Found {len(raw_prices)} raw card prices and {len(psa_prices)} PSA graded prices")
    
    if raw_prices:
        avg_raw = sum(raw_prices) / len(raw_prices)
        print(f"   Raw card average: ${avg_raw:.2f}")
        print(f"   Raw card range: ${min(raw_prices):.2f} - ${max(raw_prices):.2f}")
    
    if psa_prices:
        avg_psa = sum(psa_prices) / len(psa_prices)
        print(f"   PSA graded average: ${avg_psa:.2f}")
        print(f"   PSA graded range: ${min(psa_prices):.2f} - ${max(psa_prices):.2f}")
    
    # Test 4: Get market data
    print("\n4. Testing Market Data Analysis...")
    market_data = ebay.get_market_data("Blue-Eyes White Dragon")
    
    print(f"✅ Market data retrieved:")
    print(f"   Total listings: {market_data['total_listings']}")
    print(f"   Raw cards: {market_data['raw_count']}")
    print(f"   PSA graded: {market_data['psa_count']}")
    print(f"   Average raw price: ${market_data['avg_raw']:.2f}")
    print(f"   Average PSA price: ${market_data['avg_psa']:.2f}")
    
    # Test 5: Integration with arbitrage tool
    print("\n5. Testing Integration with Arbitrage Tool...")
    try:
        from card_arbitrage import CardArbitrageTool
        
        # Create a test listing
        test_listing = {
            'title': 'Blue-Eyes White Dragon LOB-001',
            'price_yen': 5000,
            'price_usd': 33.50,  # 5000 * 0.0067
            'condition': 'New',
            'card_id': 'Blue-Eyes White Dragon',
            'set_code': 'LOB'
        }
        
        # Test eBay price fetching
        arbitrage_tool = CardArbitrageTool()
        ebay_prices = arbitrage_tool.get_ebay_prices("Blue-Eyes White Dragon", "LOB")
        
        print(f"✅ Arbitrage tool integration successful!")
        print(f"   Raw prices found: {len(ebay_prices['raw'])}")
        print(f"   PSA prices found: {len(ebay_prices['psa'])}")
        
        # Clean up
        arbitrage_tool.cleanup()
        
    except Exception as e:
        print(f"❌ Arbitrage tool integration failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 eBay API testing completed!")
    
    return True

def show_usage_examples():
    """Show examples of how to use the eBay API."""
    print("\n📚 Usage Examples")
    print("=" * 50)
    
    print("""
# Basic usage in your arbitrage bot:

from ebay_api import EbayAPI

# Initialize the API
ebay = EbayAPI()

# Get prices for a specific card
prices = ebay.get_card_prices("Blue-Eyes White Dragon", "LOB")
raw_prices = prices['raw']      # List of raw card prices
psa_prices = prices['psa']      # List of PSA graded prices

# Get comprehensive market data
market_data = ebay.get_market_data("Blue-Eyes White Dragon")
print(f"Average raw price: ${market_data['avg_raw']:.2f}")
print(f"Average PSA price: ${market_data['avg_psa']:.2f}")

# Search for specific sold items
sold_items = ebay.search_sold_items("Yu-Gi-Oh! LOB", max_results=20)
for item in sold_items:
    print(f"{item['title']}: ${item['price']}")

# Integration with your existing arbitrage tool:
from card_arbitrage import CardArbitrageTool

tool = CardArbitrageTool()
# The tool now automatically uses the eBay API
# when calling get_ebay_prices()
""")

def main():
    """Main test function."""
    print("🚀 eBay API Integration Test")
    print("=" * 50)
    
    # Check if credentials are set
    required_vars = ['EBAY_CLIENT_ID', 'EBAY_CLIENT_SECRET', 'EBAY_DEV_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment:")
        print("EBAY_CLIENT_ID=your_app_id_here")
        print("EBAY_CLIENT_SECRET=your_cert_id_here") 
        print("EBAY_DEV_ID=your_dev_id_here")
        print("EBAY_ENVIRONMENT=sandbox")
        return False
    
    # Run tests
    success = test_ebay_api()
    
    if success:
        show_usage_examples()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 