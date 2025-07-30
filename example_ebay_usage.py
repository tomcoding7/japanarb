#!/usr/bin/env python3
"""
Example usage of eBay API integration.

This script demonstrates how to use the eBay API with your arbitrage bot.
"""

import os
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from ebay_api import EbayAPI
from card_arbitrage import CardArbitrageTool

def example_basic_usage():
    """Example of basic eBay API usage."""
    print("🔍 Example: Basic eBay API Usage")
    print("=" * 40)
    
    # Initialize eBay API
    ebay = EbayAPI()
    
    # Test authentication
    if not ebay.authenticate():
        print("❌ Authentication failed. Check your credentials.")
        return
    
    # Get prices for a specific card
    card_name = "Blue-Eyes White Dragon"
    set_code = "LOB"
    
    print(f"Searching for: {card_name} ({set_code})")
    
    # Get card prices
    prices = ebay.get_card_prices(card_name, set_code)
    
    print(f"\nResults:")
    print(f"  Raw cards found: {len(prices['raw'])}")
    print(f"  PSA graded cards found: {len(prices['psa'])}")
    
    if prices['raw']:
        avg_raw = sum(prices['raw']) / len(prices['raw'])
        print(f"  Average raw price: ${avg_raw:.2f}")
    
    if prices['psa']:
        avg_psa = sum(prices['psa']) / len(prices['psa'])
        print(f"  Average PSA price: ${avg_psa:.2f}")

def example_arbitrage_analysis():
    """Example of using eBay API with arbitrage analysis."""
    print("\n💰 Example: Arbitrage Analysis with eBay API")
    print("=" * 40)
    
    # Create arbitrage tool (now uses eBay API automatically)
    tool = CardArbitrageTool()
    
    # Example: Analyze a potential deal
    buyee_price_usd = Decimal('25.00')  # Price from Buyee
    card_name = "Blue-Eyes White Dragon"
    set_code = "LOB"
    condition = "New"
    
    print(f"Analyzing potential deal:")
    print(f"  Card: {card_name} ({set_code})")
    print(f"  Buyee price: ${buyee_price_usd}")
    print(f"  Condition: {condition}")
    
    # Get eBay prices using the API
    ebay_prices = tool.get_ebay_prices(card_name, set_code)
    
    # Get 130point prices (if available)
    point130_prices = tool.get_130point_prices(card_name, set_code)
    
    # Calculate arbitrage score
    score, profit, margin, action = tool.calculate_arbitrage_score(
        buyee_price_usd, ebay_prices, point130_prices, condition
    )
    
    print(f"\nArbitrage Analysis:")
    print(f"  Score: {score:.1f}/100")
    print(f"  Potential profit: ${profit:.2f}")
    print(f"  Profit margin: {margin:.1f}%")
    print(f"  Recommendation: {action}")
    
    # Clean up
    tool.cleanup()

def example_market_research():
    """Example of market research using eBay API."""
    print("\n📊 Example: Market Research")
    print("=" * 40)
    
    ebay = EbayAPI()
    
    # Get comprehensive market data
    card_name = "Blue-Eyes White Dragon"
    market_data = ebay.get_market_data(card_name)
    
    print(f"Market data for: {card_name}")
    print(f"  Total listings analyzed: {market_data['total_listings']}")
    print(f"  Raw cards: {market_data['raw_count']}")
    print(f"  PSA graded: {market_data['psa_count']}")
    print(f"  Average raw price: ${market_data['avg_raw']:.2f}")
    print(f"  Average PSA price: ${market_data['avg_psa']:.2f}")
    print(f"  Price range (raw): ${market_data['min_raw']:.2f} - ${market_data['max_raw']:.2f}")
    print(f"  Price range (PSA): ${market_data['min_psa']:.2f} - ${market_data['max_psa']:.2f}")

def example_search_specific_items():
    """Example of searching for specific sold items."""
    print("\n🔎 Example: Search Specific Sold Items")
    print("=" * 40)
    
    ebay = EbayAPI()
    
    # Search for specific sold items
    query = "Yu-Gi-Oh! LOB Legend of Blue Eyes"
    sold_items = ebay.search_sold_items(query, max_results=10)
    
    print(f"Recent sold items for: {query}")
    print(f"Found {len(sold_items)} items")
    
    for i, item in enumerate(sold_items[:5], 1):
        print(f"  {i}. {item['title'][:60]}...")
        print(f"     Price: ${item['price']} | Condition: {item['condition']}")

def main():
    """Run all examples."""
    print("🚀 eBay API Integration Examples")
    print("=" * 50)
    
    # Check if credentials are available
    if not all([os.getenv('EBAY_CLIENT_ID'), os.getenv('EBAY_CLIENT_SECRET'), os.getenv('EBAY_DEV_ID')]):
        print("❌ eBay API credentials not found!")
        print("Please set the following environment variables:")
        print("  - EBAY_CLIENT_ID")
        print("  - EBAY_CLIENT_SECRET") 
        print("  - EBAY_DEV_ID")
        print("  - EBAY_ENVIRONMENT (optional, defaults to 'sandbox')")
        return
    
    try:
        # Run examples
        example_basic_usage()
        example_arbitrage_analysis()
        example_market_research()
        example_search_specific_items()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running examples: {str(e)}")
        print("Make sure your eBay API credentials are correct and the API is accessible.")

if __name__ == "__main__":
    main() 