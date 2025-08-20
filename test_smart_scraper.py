#!/usr/bin/env python3
"""
Test the smart Japanese scraper to verify it gets real thumbnails
"""

from smart_japanese_scraper import SmartJapaneseScraper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_scraper():
    """Test the smart scraper with real Japanese terms"""
    scraper = SmartJapaneseScraper()
    
    test_terms = [
        "遊戯王 青眼の白龍",  # Blue-Eyes White Dragon
        "ポケモンカード リーリエ",  # Pokemon Lillie
        "遊戯王 シークレット"  # Yu-Gi-Oh Secret Rare
    ]
    
    print("🧪 Testing Smart Japanese Scraper")
    print("=" * 50)
    
    for term in test_terms:
        print(f"\n🔍 Testing search for: {term}")
        
        try:
            results = scraper.smart_search(term, max_results=5)
            
            if results:
                print(f"✅ Found {len(results)} results!")
                
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result['title'][:60]}...")
                    print(f"   💰 Price: ¥{result['price_yen']:,} (${result['price_usd']:.2f})")
                    print(f"   🖼️  Image: {'✅ YES' if result['image_url'] else '❌ NO'}")
                    if result['image_url']:
                        print(f"   🔗 Image URL: {result['image_url'][:80]}...")
                    print(f"   📊 Score: {result['arbitrage_score']:.1f}/100")
                    print(f"   🎯 Action: {result['recommended_action']}")
                    print(f"   🏪 Source: {result['source']}")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error testing {term}: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Smart scraper test completed!")

if __name__ == "__main__":
    test_scraper()
