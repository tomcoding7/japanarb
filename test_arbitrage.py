#!/usr/bin/env python3
"""
Test script for the enhanced arbitrage tool with 130point.com integration
"""

import logging
import time
from card_arbitrage import CardArbitrageTool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_arbitrage_analysis():
    """Test the enhanced arbitrage analysis with sample data."""
    
    print("Testing Enhanced Arbitrage Analysis")
    print("=" * 50)
    
    # Create arbitrage tool
    tool = CardArbitrageTool()
    
    try:
        # Test with a popular card
        search_term = "青眼の白龍"  # Blue-Eyes White Dragon
        print(f"\nAnalyzing: {search_term}")
        
        # Run analysis
        tool.run(search_term, max_results=5)
        
        print("\nAnalysis complete! Check the arbitrage_results folder for detailed results.")
        
    except Exception as e:
        logger.error(f"Error in arbitrage test: {str(e)}")
        raise e
    finally:
        tool.cleanup()

def test_price_comparison():
    """Test the price comparison functionality."""
    
    print("\nTesting Price Comparison")
    print("=" * 30)
    
    from scraper_utils import PriceAnalyzer
    
    price_analyzer = PriceAnalyzer()
    
    # Test cards
    test_cards = [
        ("Blue-Eyes White Dragon", "LOB-001"),
        ("Dark Magician", "LOB-005"),
        ("Red-Eyes Black Dragon", "LOB-006")
    ]
    
    for card_name, set_code in test_cards:
        print(f"\nTesting: {card_name} ({set_code})")
        
        try:
            # Get 130point prices
            prices = price_analyzer.get_130point_prices(card_name, set_code)
            
            if prices:
                print(f"  130point.com prices:")
                if prices.get('raw_avg'):
                    print(f"    Raw average: ${prices['raw_avg']:.2f} ({prices['raw_count']} sales)")
                if prices.get('psa_9_avg'):
                    print(f"    PSA 9 average: ${prices['psa_9_avg']:.2f} ({prices['psa_9_count']} sales)")
                if prices.get('psa_10_avg'):
                    print(f"    PSA 10 average: ${prices['psa_10_avg']:.2f} ({prices['psa_10_count']} sales)")
            else:
                print("  No 130point.com data available")
                
        except Exception as e:
            print(f"  Error: {str(e)}")
        
        time.sleep(2)  # Delay between requests

def main():
    """Run the arbitrage tests."""
    
    print("Enhanced Arbitrage Bot Test")
    print("=" * 40)
    print("This test will:")
    print("1. Test price comparison with 130point.com")
    print("2. Run a full arbitrage analysis")
    print()
    
    # Test price comparison first
    test_price_comparison()
    
    # Test full arbitrage analysis
    test_arbitrage_analysis()
    
    print("\nTest completed!")

if __name__ == "__main__":
    main() 