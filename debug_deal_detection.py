#!/usr/bin/env python3
"""
Debug script to test deal detection with real Buyee data
"""

import logging
import time
from buyee_scraper import BuyeeScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_deal_detection():
    """Debug the deal detection with real Buyee data"""
    
    scraper = BuyeeScraper(use_llm=False, headless=False)  # Run in visible mode for debugging
    
    try:
        # Test with a simple search term
        search_term = "遊戯王"
        logger.info(f"Testing with search term: {search_term}")
        
        # Navigate to search page
        search_url = f"https://buyee.jp/item/search/query/{search_term}"
        logger.info(f"Navigating to: {search_url}")
        
        scraper.driver.get(search_url)
        time.sleep(5)  # Wait for page to load
        
        # Handle cookie popup if present
        scraper.handle_cookie_popup()
        
        # Get item summaries
        logger.info("Getting item summaries...")
        summaries = scraper.get_item_summaries_from_search_page()
        
        logger.info(f"Found {len(summaries)} item summaries")
        
        # Test each summary
        for i, summary in enumerate(summaries):
            logger.info(f"\n--- Testing Summary {i+1} ---")
            logger.info(f"Title: {summary.get('title', 'N/A')}")
            logger.info(f"Price: {summary.get('price_yen', 'N/A')}")
            logger.info(f"URL: {summary.get('url', 'N/A')}")
            
            # Test the card analysis
            if 'title' in summary:
                card_details = scraper.parse_card_details_from_buyee(
                    summary['title'], 
                    summary.get('description', '')
                )
                
                logger.info(f"Card Analysis Results:")
                logger.info(f"  Is Valuable: {card_details.get('is_valuable', False)}")
                logger.info(f"  Confidence: {card_details.get('confidence_score', 0)}")
                logger.info(f"  Matched Keywords: {card_details.get('matched_keywords', [])}")
                logger.info(f"  Rarity: {card_details.get('rarity', 'N/A')}")
                logger.info(f"  Edition: {card_details.get('edition', 'N/A')}")
        
        # Test a few specific card titles
        test_titles = [
            "遊戯王 ブラック・マジシャン DMG-001 シークレットレア",
            "遊戯王 青眼の白龍 LOB-001 ウルトラレア",
            "遊戯王 デーモンの召喚 GB特典",
            "遊戯王 普通のカード"
        ]
        
        logger.info("\n--- Testing Specific Card Titles ---")
        for title in test_titles:
            logger.info(f"\nTesting: {title}")
            card_details = scraper.parse_card_details_from_buyee(title, "")
            logger.info(f"  Is Valuable: {card_details.get('is_valuable', False)}")
            logger.info(f"  Confidence: {card_details.get('confidence_score', 0)}")
            logger.info(f"  Matched Keywords: {card_details.get('matched_keywords', [])}")
        
    except Exception as e:
        logger.error(f"Error during debugging: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    debug_deal_detection() 