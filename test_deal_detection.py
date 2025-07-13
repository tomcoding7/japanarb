#!/usr/bin/env python3
"""
Test script to verify deal detection logic
"""

import logging
from buyee_scraper import BuyeeScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_deal_detection():
    """Test the deal detection logic with sample data"""
    
    # Create scraper instance
    scraper = BuyeeScraper(use_llm=False)
    
    # Test cases with different card titles
    test_cases = [
        {
            'title': '遊戯王 ブラック・マジシャン DMG-001 シークレットレア 1st Edition',
            'description': '【ランク】A 完全美品 未使用状態',
            'price': 5000
        },
        {
            'title': '遊戯王 青眼の白龍 LOB-001 ウルトラレア 初版',
            'description': '【ランク】S 新品同様 美品',
            'price': 8000
        },
        {
            'title': '遊戯王 デーモンの召喚 GB特典 プロモカード',
            'description': '【ランク】B+ ほぼ新品 微傷あり',
            'price': 3000
        },
        {
            'title': '遊戯王 普通のカード ノーマル',
            'description': '【ランク】C 普通品',
            'price': 100
        }
    ]
    
    print("Testing deal detection logic...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Title: {test_case['title']}")
        print(f"Description: {test_case['description']}")
        print(f"Price: ¥{test_case['price']}")
        
        # Parse card details
        card_details = scraper.parse_card_details_from_buyee(
            test_case['title'], 
            test_case['description']
        )
        
        print(f"Valuable: {card_details['is_valuable']}")
        print(f"Confidence: {card_details['confidence_score']}")
        print(f"Matched Keywords: {card_details['matched_keywords']}")
        print(f"Rarity: {card_details['rarity']}")
        print(f"Edition: {card_details['edition']}")
        
        # Test condition analysis
        condition_analysis = scraper.rank_analyzer.analyze_condition(
            test_case['description'], 
            test_case['description']
        )
        
        print(f"Condition: {condition_analysis['condition']}")
        print(f"Condition Confidence: {condition_analysis['confidence']}")
        
        # Test if it would be considered a deal
        is_good_condition = scraper.rank_analyzer.is_good_condition(
            condition_analysis['condition']
        )
        
        would_be_deal = (
            card_details['is_valuable'] and 
            card_details['confidence_score'] >= 0.6 and 
            is_good_condition
        )
        
        print(f"Would be considered a deal: {would_be_deal}")
        print("-" * 30)

if __name__ == "__main__":
    test_deal_detection() 