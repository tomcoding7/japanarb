#!/usr/bin/env python3
"""
End-to-end test for Yu-Gi-Oh! Arbitrage workflow using real data.
"""

import logging
import time
from card_arbitrage import CardArbitrageTool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_end_to_end_arbitrage():
    """Test the full arbitrage workflow with real data."""
    print("\n🧪 End-to-End Arbitrage Workflow Test")
    print("=" * 60)

    # Step 1: Search Buyee for Yu-Gi-Oh Asian edition
    search_term = "遊戯王 アジア"
    max_results = 10
    tool = CardArbitrageTool()
    try:
        print(f"\n🔍 Searching Buyee for: {search_term}")
        listings = tool.scrape_buyee_listings(search_term, max_results=max_results)
        print(f"📦 Found {len(listings)} listings on Buyee")
        assert len(listings) > 0, "No listings found on Buyee."

        # Step 2: Analyze each listing
        promising_listings = tool.pre_screen_listings(listings)
        print(f"✨ {len(promising_listings)} listings passed pre-screening")
        assert len(promising_listings) > 0, "No promising listings found after pre-screening."

        # Step 3: Analyze promising listings for arbitrage
        analyzed_listings = tool.analyze_listings(promising_listings)
        print(f"💡 {len(analyzed_listings)} listings analyzed for arbitrage potential")
        assert len(analyzed_listings) > 0, "No listings analyzed."

        # Step 4: Print out promising deals
        deals_found = 0
        for listing in analyzed_listings:
            if listing.recommended_action and listing.recommended_action.upper() == "BUY":
                deals_found += 1
                print("\n🚩 Potential Deal:")
                print(f"  Title: {listing.title}")
                print(f"  Condition: {listing.condition}")
                print(f"  Price (Yen): {listing.price_yen}")
                print(f"  Price (USD): {listing.price_usd}")
                print(f"  eBay Prices: {listing.ebay_prices}")
                print(f"  130point Prices: {listing.point130_prices}")
                print(f"  Potential Profit: {listing.potential_profit}")
                print(f"  Profit Margin: {listing.profit_margin}")
                print(f"  Arbitrage Score: {listing.arbitrage_score}")
                print(f"  Listing URL: {listing.listing_url}")
                print(f"  Image URL: {listing.image_url}")
        if deals_found == 0:
            print("\n⚠️  No strong deals found, but analysis completed.")
        else:
            print(f"\n🎉 {deals_found} promising deals found!")

        # Step 5: Save results
        tool.save_results(analyzed_listings, search_term)
        print("\n💾 Results saved to output directory.")

    except Exception as e:
        print(f"❌ Error during end-to-end test: {e}")
        raise
    finally:
        tool.cleanup()
        print("\n🧹 Cleaned up resources.")

if __name__ == "__main__":
    test_end_to_end_arbitrage() 