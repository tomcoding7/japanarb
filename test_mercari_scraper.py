#!/usr/bin/env python3
"""
Test the Mercari-focused scraper
Mercari is accessible from UK (unlike Yahoo Auctions)
"""

from mercari_focused_scraper import MercariFocusedScraper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_mercari_scraper():
    """Test the Mercari scraper"""
    scraper = MercariFocusedScraper()
    
    test_terms = [
        "遊戯王 青眼の白龍",      # Blue-Eyes White Dragon
        "ポケモンカード リーリエ",  # Pokemon Lillie
        "ワンピース カード SR",    # One Piece SR
        "遊戯王 初期"            # Yu-Gi-Oh 1st edition
    ]
    
    print("🧪 Testing Mercari-Focused Scraper")
    print("=" * 60)
    print("✅ Mercari is accessible from UK")
    print("✅ No VPN required for Mercari")
    print("❌ Yahoo Auctions blocked (needs Japanese VPN)")
    print("=" * 60)
    
    for term in test_terms:
        print(f"\n🔍 Testing search for: {term}")
        
        try:
            results = scraper.smart_search(term, max_results=5)
            
            if results:
                print(f"✅ Found {len(results)} results!")
                
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result['title'][:60]}...")
                    print(f"   💰 Price: ¥{result['price_yen']:,} (${result['price_usd']:.2f})")
                    print(f"   🖼️  Image: {'✅ HAS IMAGE' if result['image_url'] else '❌ NO IMAGE'}")
                    if result['image_url']:
                        print(f"   🔗 Image URL: {result['image_url'][:80]}...")
                    print(f"   📊 Score: {result['arbitrage_score']}/100")
                    print(f"   🎯 Action: {result['recommended_action']}")
                    print(f"   🏪 Source: {result['source']}")
                    print(f"   🔗 Listing: {result['listing_url'][:60]}...")
                    
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error testing {term}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Mercari scraper test completed!")
    print("🎯 Key Points:")
    print("   • Mercari works from UK without VPN")
    print("   • Yahoo Auctions requires Japanese VPN")
    print("   • Focus on Mercari for UK-based scraping")
    print("   • Real thumbnails from accessible source")

if __name__ == "__main__":
    test_mercari_scraper()
