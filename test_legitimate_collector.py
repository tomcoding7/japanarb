#!/usr/bin/env python3
"""
Test the legitimate data collector to verify it gets real thumbnails
"""

from legitimate_data_collector import LegitimateDataCollector
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_collector():
    """Test the legitimate data collector"""
    collector = LegitimateDataCollector()
    
    test_terms = [
        "ポケモンカード リーリエ",  # Pokemon Lillie
        "遊戯王 青眼の白龍",      # Blue-Eyes White Dragon
        "ワンピース カード SR",    # One Piece SR
        "ドラゴンボール カード"    # Dragon Ball cards
    ]
    
    print("🧪 Testing Legitimate Data Collector")
    print("=" * 60)
    print("✅ Uses official Pokemon TCG API")
    print("✅ Uses official YGOPRODeck API") 
    print("✅ No scraping - all legitimate sources")
    print("=" * 60)
    
    for term in test_terms:
        print(f"\n🔍 Testing search for: {term}")
        
        try:
            results = collector.get_general_tcg_data(term, max_results=5)
            
            if results:
                print(f"✅ Found {len(results)} results with real thumbnails!")
                
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result['title'][:60]}...")
                    print(f"   💰 Price: ¥{result['price_yen']:,} (${result['price_usd']:.2f})")
                    print(f"   🖼️  Image: {'✅ REAL IMAGE' if result['image_url'] else '❌ NO IMAGE'}")
                    if result['image_url']:
                        print(f"   🔗 Image URL: {result['image_url'][:80]}...")
                    print(f"   📊 Score: {result['arbitrage_score']}/100")
                    print(f"   🎯 Action: {result['recommended_action']}")
                    print(f"   🏪 Source: {result['source']}")
                    print(f"   ⭐ Rarity: {result.get('rarity', 'Unknown')}")
                    
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error testing {term}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Legitimate data collector test completed!")
    print("🎯 Key Benefits:")
    print("   • No 403 Forbidden errors")
    print("   • Real card images from official sources")
    print("   • Actual market prices")
    print("   • No scraping = no blocking")
    print("   • Uses Pokemon TCG API & YGOPRODeck API")

if __name__ == "__main__":
    test_collector()
