#!/usr/bin/env python3
"""
Test Enhanced Features
Tests the improved image loading and auction filtering
"""

import sys
import os
import time
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_scraper():
    """Test the enhanced scraper with image loading and auction filtering"""
    print("=" * 60)
    print("Testing Enhanced Features")
    print("Image loading and auction filtering")
    print("=" * 60)
    
    try:
        from enhanced_buyee_scraper import EnhancedBuyeeScraper
        
        # Test search term
        test_term = "Blue-Eyes White Dragon"
        
        print(f"Testing enhanced scraper with: {test_term}")
        print(f"Time: {datetime.now()}")
        print()
        
        # Initialize the enhanced scraper
        with EnhancedBuyeeScraper(
            output_dir="test_enhanced_results",
            max_pages=1,  # Just test 1 page
            headless=True,
            use_llm=False
        ) as scraper:
            
            start_time = time.time()
            
            try:
                results = scraper.search_items(test_term)
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"✓ Enhanced scraper completed in {duration:.2f} seconds")
                print(f"✓ Found {len(results)} valuable items")
                print()
                
                # Check for images and auction status
                items_with_images = 0
                items_without_images = 0
                
                for i, result in enumerate(results[:5], 1):  # Show first 5 results
                    print(f"Result {i}:")
                    print(f"  Title: {result.get('title', 'Unknown')}")
                    print(f"  Price: ¥{result.get('price_yen', 0)} (${result.get('price_usd', 0)})")
                    
                    # Check images
                    images = result.get('images', [])
                    if images:
                        print(f"  Images: {len(images)} found")
                        print(f"  First image: {images[0] if images else 'None'}")
                        items_with_images += 1
                    else:
                        print(f"  Images: None found")
                        items_without_images += 1
                    
                    # Check condition
                    condition = result.get('condition', 'Unknown')
                    print(f"  Condition: {condition}")
                    
                    # Check if it's a finished auction (should be filtered out)
                    title = result.get('title', '').lower()
                    if any(keyword in title for keyword in ['終了', 'ended', 'finished', 'closed']):
                        print(f"  ⚠️  WARNING: This appears to be a finished auction!")
                    else:
                        print(f"  ✓ Active auction")
                    
                    print()
                
                print(f"Summary:")
                print(f"  Items with images: {items_with_images}")
                print(f"  Items without images: {items_without_images}")
                print(f"  Total items: {len(results)}")
                
                if items_with_images > 0:
                    print(f"  ✓ Image loading is working!")
                else:
                    print(f"  ⚠️  No images found - may need debugging")
                
                if items_without_images == 0:
                    print(f"  ✓ All items have images!")
                else:
                    print(f"  ⚠️  Some items missing images")
                
            except Exception as e:
                print(f"✗ Error during enhanced scraper test: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print("=" * 60)
        print("Enhanced scraper test completed!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"Import error: {str(e)}")
        print("Make sure enhanced_buyee_scraper.py exists and all dependencies are installed")
        return 1
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

def test_card_arbitrage():
    """Test the enhanced card arbitrage tool"""
    print("\n" + "=" * 60)
    print("Testing Enhanced Card Arbitrage")
    print("=" * 60)
    
    try:
        from card_arbitrage import CardArbitrageTool
        
        # Test search term
        test_term = "Dark Magician"
        
        print(f"Testing enhanced card arbitrage with: {test_term}")
        print(f"Time: {datetime.now()}")
        print()
        
        # Initialize the tool
        tool = CardArbitrageTool()
        
        start_time = time.time()
        
        try:
            results = tool.run(test_term, max_results=5)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✓ Card arbitrage completed in {duration:.2f} seconds")
            print(f"✓ Found {len(results)} results")
            print()
            
            # Check for images and auction status
            items_with_images = 0
            items_without_images = 0
            
            for i, result in enumerate(results[:3], 1):  # Show first 3 results
                print(f"Result {i}:")
                print(f"  Title: {result.title}")
                print(f"  Price: ¥{result.price_yen} (${result.price_usd})")
                
                # Check images
                if result.image_url:
                    print(f"  Image: {result.image_url}")
                    items_with_images += 1
                else:
                    print(f"  Image: None")
                    items_without_images += 1
                
                # Check condition
                print(f"  Condition: {result.condition}")
                
                # Check arbitrage score
                if result.arbitrage_score:
                    print(f"  Score: {result.arbitrage_score}")
                    print(f"  Action: {result.recommended_action}")
                
                print()
            
            print(f"Summary:")
            print(f"  Items with images: {items_with_images}")
            print(f"  Items without images: {items_without_images}")
            print(f"  Total items: {len(results)}")
            
            if items_with_images > 0:
                print(f"  ✓ Image loading is working!")
            else:
                print(f"  ⚠️  No images found - may need debugging")
            
        except Exception as e:
            print(f"✗ Error during card arbitrage test: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("=" * 60)
        print("Enhanced card arbitrage test completed!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"Import error: {str(e)}")
        print("Make sure card_arbitrage.py exists and all dependencies are installed")
        return 1
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

def main():
    """Main test function"""
    print("Enhanced Features Test Suite")
    print("Testing image loading and auction filtering improvements")
    print()
    
    # Test enhanced scraper
    result1 = test_enhanced_scraper()
    
    # Test card arbitrage
    result2 = test_card_arbitrage()
    
    if result1 == 0 and result2 == 0:
        print("\n🎉 All tests completed successfully!")
        print("Enhanced features should now be working properly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
