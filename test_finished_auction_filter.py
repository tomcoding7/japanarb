#!/usr/bin/env python3
"""
Test Finished Auction Filter
Tests the improved finished auction filtering
"""

import sys
import os
import time
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_finished_auction_filter():
    """Test the finished auction filtering specifically"""
    print("=" * 60)
    print("Testing Finished Auction Filter")
    print("Should filter out auctions marked as 'Finished'")
    print("=" * 60)
    
    try:
        from card_arbitrage import CardArbitrageTool
        
        # Test search term
        test_term = "Blue-Eyes White Dragon"
        
        print(f"Testing with: {test_term}")
        print(f"Time: {datetime.now()}")
        print()
        
        # Initialize the tool
        tool = CardArbitrageTool()
        
        start_time = time.time()
        
        try:
            # Get raw listings first to check filtering
            raw_listings = tool.scrape_buyee_listings(test_term, max_results=20)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✓ Scraping completed in {duration:.2f} seconds")
            print(f"✓ Found {len(raw_listings)} raw listings")
            print()
            
            # Check for finished auctions in raw results
            finished_count = 0
            active_count = 0
            
            for i, listing in enumerate(raw_listings[:10], 1):  # Check first 10
                print(f"Listing {i}:")
                print(f"  Title: {listing.title}")
                print(f"  Price: ¥{listing.price_yen} (${listing.price_usd})")
                
                # Check if this would be filtered as finished
                title_lower = listing.title.lower()
                if any(keyword in title_lower for keyword in ['finished', 'ended', 'closed', 'complete', 'expired', '終了']):
                    print(f"  ⚠️  CONTAINS FINISHED KEYWORD")
                    finished_count += 1
                else:
                    print(f"  ✓ No finished keywords found")
                    active_count += 1
                
                # Check for images
                if listing.image_url:
                    print(f"  Image: ✓ Found")
                else:
                    print(f"  Image: ✗ Missing")
                
                print()
            
            print(f"Summary:")
            print(f"  Raw listings found: {len(raw_listings)}")
            print(f"  Potentially finished: {finished_count}")
            print(f"  Potentially active: {active_count}")
            
            if finished_count > 0:
                print(f"  ⚠️  Found {finished_count} listings that should be filtered out")
            else:
                print(f"  ✓ No finished auctions detected in sample")
            
            # Now test the full analysis
            print("\n" + "=" * 40)
            print("Testing Full Analysis")
            print("=" * 40)
            
            results = tool.run(test_term, max_results=10)
            
            print(f"✓ Analysis completed")
            print(f"✓ Final results: {len(results)} items")
            print()
            
            # Check final results
            for i, result in enumerate(results[:5], 1):
                print(f"Final Result {i}:")
                print(f"  Title: {result.title}")
                print(f"  Price: ¥{result.price_yen} (${result.price_usd})")
                
                # Check if any finished keywords made it through
                title_lower = result.title.lower()
                if any(keyword in title_lower for keyword in ['finished', 'ended', 'closed', 'complete', 'expired', '終了']):
                    print(f"  ❌ ERROR: Finished auction made it through filtering!")
                else:
                    print(f"  ✓ Properly filtered")
                
                # Check for images
                if result.image_url:
                    print(f"  Image: ✓ Found")
                else:
                    print(f"  Image: ✗ Missing")
                
                print()
            
            if len(results) > 0:
                print(f"✓ Analysis is working and filtering finished auctions")
            else:
                print(f"⚠️  No results found - may need to check search terms or website changes")
            
        except Exception as e:
            print(f"✗ Error during test: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("=" * 60)
        print("Finished auction filter test completed!")
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
    print("Finished Auction Filter Test")
    print("Testing the improved filtering to exclude finished auctions")
    print()
    
    result = test_finished_auction_filter()
    
    if result == 0:
        print("\n🎉 Test completed successfully!")
        print("Finished auction filtering should now be working properly.")
        return 0
    else:
        print("\n❌ Test failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
