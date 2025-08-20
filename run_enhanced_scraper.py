#!/usr/bin/env python3
"""
Enhanced Scraper Runner
Tests the enhanced Buyee scraper with improved image loading and auction filtering
"""

import sys
import os
import time
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function to run the enhanced scraper"""
    print("=" * 60)
    print("Enhanced Yu-Gi-Oh! Arbitrage Scraper")
    print("Improved image loading and auction filtering")
    print("=" * 60)
    
    try:
        from enhanced_buyee_scraper import EnhancedBuyeeScraper
        
        # Test search terms
        test_terms = [
            "Blue-Eyes White Dragon",
            "Dark Magician",
            "Red-Eyes Black Dragon"
        ]
        
        print(f"Starting enhanced scraper at {datetime.now()}")
        print(f"Will test {len(test_terms)} search terms")
        print()
        
        # Initialize the enhanced scraper
        with EnhancedBuyeeScraper(
            output_dir="enhanced_scraped_results",
            max_pages=2,  # Limit to 2 pages for testing
            headless=True,
            use_llm=False
        ) as scraper:
            
            total_results = 0
            
            for i, search_term in enumerate(test_terms, 1):
                print(f"[{i}/{len(test_terms)}] Searching for: {search_term}")
                print("-" * 40)
                
                start_time = time.time()
                
                try:
                    results = scraper.search_items(search_term)
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    print(f"✓ Found {len(results)} valuable items")
                    print(f"✓ Search completed in {duration:.2f} seconds")
                    
                    # Show some details about the results
                    for j, result in enumerate(results[:3], 1):  # Show first 3 results
                        print(f"  {j}. {result.get('title', 'Unknown')}")
                        print(f"     Price: ¥{result.get('price_yen', 0)} (${result.get('price_usd', 0)})")
                        print(f"     Images: {len(result.get('images', []))}")
                        print(f"     Condition: {result.get('condition', 'Unknown')}")
                        print(f"     Score: {result.get('arbitrage_score', 0)}")
                        print()
                    
                    if len(results) > 3:
                        print(f"  ... and {len(results) - 3} more items")
                    
                    total_results += len(results)
                    
                except Exception as e:
                    print(f"✗ Error searching for '{search_term}': {str(e)}")
                
                print()
                time.sleep(2)  # Brief pause between searches
        
        print("=" * 60)
        print(f"Enhanced scraper completed!")
        print(f"Total valuable items found: {total_results}")
        print(f"Results saved to: enhanced_scraped_results/")
        print("=" * 60)
        
        # Optionally start the web interface
        start_web_interface = input("\nWould you like to start the enhanced web interface? (y/n): ").lower().strip()
        
        if start_web_interface in ['y', 'yes']:
            print("Starting enhanced web interface...")
            print("Open your browser to: http://localhost:5001")
            print("Press Ctrl+C to stop")
            
            try:
                from enhanced_web_interface_v2 import app
                app.run(debug=False, host='0.0.0.0', port=5001)
            except KeyboardInterrupt:
                print("\nWeb interface stopped.")
            except Exception as e:
                print(f"Error starting web interface: {str(e)}")
        
    except ImportError as e:
        print(f"Import error: {str(e)}")
        print("Make sure all required modules are installed:")
        print("pip install selenium webdriver-manager selenium-stealth requests pillow")
        return 1
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
