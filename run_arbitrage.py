#!/usr/bin/env python3
"""
Enhanced Arbitrage Bot Runner
Combines Buyee.jp data with 130point.com/sales and eBay data for arbitrage opportunities
"""

import argparse
import logging
from card_arbitrage import CardArbitrageTool
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the enhanced arbitrage analysis."""
    
    parser = argparse.ArgumentParser(description='Enhanced Yu-Gi-Oh! Arbitrage Bot')
    parser.add_argument('--search', '-s', type=str, required=True,
                       help='Search term (Japanese or English)')
    parser.add_argument('--max-results', '-m', type=int, default=20,
                       help='Maximum number of results to analyze (default: 20)')
    parser.add_argument('--output-dir', '-o', type=str, default='arbitrage_results',
                       help='Output directory for results (default: arbitrage_results)')
    
    args = parser.parse_args()
    
    print("Enhanced Yu-Gi-Oh! Arbitrage Bot")
    print("=" * 50)
    print(f"Search term: {args.search}")
    print(f"Max results: {args.max_results}")
    print(f"Output directory: {args.output_dir}")
    print()
    
    # Create arbitrage tool
    tool = CardArbitrageTool(output_dir=args.output_dir)
    
    try:
        # Run analysis
        tool.run(args.search, args.max_results)
        
        print(f"\nAnalysis complete! Results saved to {args.output_dir}/")
        print("\nThe bot analyzed:")
        print("• Buyee.jp listings for current prices")
        print("• 130point.com/sales for recent eBay sold prices")
        print("• eBay sold listings for additional price data")
        print("• Calculated arbitrage scores and recommendations")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
    except Exception as e:
        logger.error(f"Error in arbitrage analysis: {str(e)}")
    finally:
        tool.cleanup()

if __name__ == "__main__":
    main() 