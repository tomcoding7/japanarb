#!/usr/bin/env python3
"""
Simplified Deal Finder - Focuses on deal detection logic
"""

import logging
import json
import os
from datetime import datetime
from buyee_scraper import BuyeeScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_deals():
    """Create sample deals for testing"""
    sample_deals = [
        {
            'title': '遊戯王 ブラック・マジシャン DMG-001 シークレットレア 1st Edition',
            'description': '【ランク】A 完全美品 未使用状態 新品同様',
            'price': 5000,
            'url': 'https://buyee.jp/item/yahoo/auction/sample1',
            'seller': 'Sample Seller 1',
            'condition': 'A',
            'images': ['https://example.com/image1.jpg']
        },
        {
            'title': '遊戯王 青眼の白龍 LOB-001 ウルトラレア 初版',
            'description': '【ランク】S 新品同様 美品 完全無傷',
            'price': 8000,
            'url': 'https://buyee.jp/item/yahoo/auction/sample2',
            'seller': 'Sample Seller 2',
            'condition': 'S',
            'images': ['https://example.com/image2.jpg']
        },
        {
            'title': '遊戯王 デーモンの召喚 GB特典 プロモカード',
            'description': '【ランク】B+ ほぼ新品 微傷あり 限定版',
            'price': 3000,
            'url': 'https://buyee.jp/item/yahoo/auction/sample3',
            'seller': 'Sample Seller 3',
            'condition': 'B+',
            'images': ['https://example.com/image3.jpg']
        },
        {
            'title': '遊戯王 真紅眼の黒竜 SDK-001 ウルトラレア',
            'description': '【ランク】A 美品 軽微な傷あり 初版',
            'price': 6000,
            'url': 'https://buyee.jp/item/yahoo/auction/sample4',
            'seller': 'Sample Seller 4',
            'condition': 'A',
            'images': ['https://example.com/image4.jpg']
        },
        {
            'title': '遊戯王 普通のカード ノーマル',
            'description': '【ランク】C 普通品 使用感あり',
            'price': 100,
            'url': 'https://buyee.jp/item/yahoo/auction/sample5',
            'seller': 'Sample Seller 5',
            'condition': 'C',
            'images': ['https://example.com/image5.jpg']
        }
    ]
    return sample_deals

def analyze_deals():
    """Analyze sample deals and save results"""
    
    # Create scraper instance
    scraper = BuyeeScraper(use_llm=False)
    
    # Get sample deals
    sample_deals = create_sample_deals()
    
    print("Analyzing sample deals...")
    print("=" * 50)
    
    valuable_deals = []
    
    for i, deal in enumerate(sample_deals, 1):
        print(f"\nAnalyzing Deal {i}:")
        print(f"Title: {deal['title']}")
        print(f"Price: ¥{deal['price']:,}")
        
        # Parse card details
        card_details = scraper.parse_card_details_from_buyee(
            deal['title'], 
            deal['description']
        )
        
        # Analyze condition
        condition_analysis = scraper.rank_analyzer.analyze_condition(
            deal['description'], 
            deal['description']
        )
        
        # Check if it's a good deal
        is_good_condition = scraper.rank_analyzer.is_good_condition(
            condition_analysis['condition']
        )
        
        is_valuable_deal = (
            card_details['is_valuable'] and 
            card_details['confidence_score'] >= 0.6 and 
            is_good_condition
        )
        
        print(f"Valuable: {card_details['is_valuable']}")
        print(f"Confidence: {card_details['confidence_score']:.2f}")
        print(f"Condition: {condition_analysis['condition']}")
        print(f"Good Condition: {is_good_condition}")
        print(f"Is Valuable Deal: {is_valuable_deal}")
        
        if is_valuable_deal:
            valuable_deals.append({
                'title': deal['title'],
                'price': deal['price'],
                'url': deal['url'],
                'seller': deal['seller'],
                'condition': deal['condition'],
                'images': deal['images'],
                'card_details': card_details,
                'condition_analysis': condition_analysis,
                'confidence_score': card_details['confidence_score'],
                'matched_keywords': card_details['matched_keywords']
            })
            print("✅ FOUND VALUABLE DEAL!")
        else:
            print("❌ Not a valuable deal")
        
        print("-" * 40)
    
    # Save results
    if valuable_deals:
        save_deals_to_files(valuable_deals)
        print(f"\n🎉 Found {len(valuable_deals)} valuable deals!")
    else:
        print("\n😞 No valuable deals found in sample data")

def save_deals_to_files(deals):
    """Save deals to various file formats"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory
    output_dir = "deal_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save as JSON
    json_path = os.path.join(output_dir, f"valuable_deals_{timestamp}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(deals, f, ensure_ascii=False, indent=2, default=str)
    print(f"Saved deals to: {json_path}")
    
    # Save as HTML
    html_path = os.path.join(output_dir, f"valuable_deals_{timestamp}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Valuable Yu-Gi-Oh! Deals Found</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .deal {{ background: white; border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .title {{ font-size: 1.3em; font-weight: bold; color: #333; margin-bottom: 10px; }}
                .price {{ font-size: 1.2em; color: #e44d26; font-weight: bold; margin-bottom: 10px; }}
                .details {{ margin: 10px 0; color: #666; }}
                .confidence {{ color: #28a745; font-weight: bold; }}
                .keywords {{ background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0; }}
                .link {{ color: #007bff; text-decoration: none; }}
                .link:hover {{ text-decoration: underline; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Valuable Yu-Gi-Oh! Deals Found</h1>
                <p>Total Deals: {len(deals)} | Generated: {timestamp}</p>
            </div>
        """)
        
        for deal in deals:
            f.write(f"""
            <div class="deal">
                <div class="title">{deal['title']}</div>
                <div class="price">Price: ¥{deal['price']:,}</div>
                <div class="details">
                    <p><strong>Seller:</strong> {deal['seller']}</p>
                    <p><strong>Condition:</strong> {deal['condition']}</p>
                    <p><strong>Confidence Score:</strong> <span class="confidence">{deal['confidence_score']:.2f}</span></p>
                    <p><strong>Rarity:</strong> {deal['card_details']['rarity']}</p>
                    <p><strong>Edition:</strong> {deal['card_details']['edition']}</p>
                </div>
                <div class="keywords">
                    <strong>Matched Keywords:</strong> {', '.join(deal['matched_keywords'])}
                </div>
                <p><a href="{deal['url']}" class="link" target="_blank">View on Buyee</a></p>
            </div>
            """)
        
        f.write("""
        </body>
        </html>
        """)
    
    print(f"Saved HTML report to: {html_path}")
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"Total deals analyzed: {len(sample_deals)}")
    print(f"Valuable deals found: {len(deals)}")
    print(f"Success rate: {len(deals)/len(sample_deals)*100:.1f}%")

if __name__ == "__main__":
    analyze_deals() 