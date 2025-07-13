#!/usr/bin/env python3
"""
Simplified Arbitrage Tool - Focuses on filtering and analysis
Uses sample data to demonstrate the intelligent screening logic
"""

import logging
import json
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal
import pandas as pd
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SimpleCardListing:
    """Simplified card listing data class."""
    title: str
    price_yen: int
    price_usd: float
    condition: str
    url: str
    description: str
    screening_score: int = 0
    screening_reasons: List[str] = None
    arbitrage_score: float = 0.0
    profit_margin: float = 0.0
    recommended_action: str = "PASS"

class SimpleArbitrageTool:
    """Simplified arbitrage tool focusing on filtering logic."""
    
    def __init__(self):
        self.yen_to_usd = 0.0067
        self.sample_data = self._load_sample_data()
    
    def _load_sample_data(self) -> List[Dict]:
        """Load sample card data for demonstration."""
        return [
            {
                "title": "青眼の白龍 LOB-001 1st Edition Ultra Rare",
                "price_yen": 15000,
                "condition": "新品",
                "description": "Legend of Blue Eyes White Dragon, 1st Edition, Ultra Rare, Mint Condition"
            },
            {
                "title": "ブラック・マジシャン MFC-000 1st Edition Secret Rare",
                "price_yen": 25000,
                "condition": "未使用",
                "description": "Magic Force, 1st Edition, Secret Rare, Near Mint"
            },
            {
                "title": "レッドアイズ・ブラック・ドラゴン LOB-000 1st Edition",
                "price_yen": 8000,
                "condition": "新品",
                "description": "Legend of Blue Eyes, 1st Edition, Ultra Rare"
            },
            {
                "title": "Blue-Eyes Ultimate Dragon LOB-000 1st Edition",
                "price_yen": 45000,
                "condition": "新品",
                "description": "Legend of Blue Eyes, 1st Edition, Ultra Rare, Mint"
            },
            {
                "title": "Dark Magician Girl MFC-000 1st Edition Secret",
                "price_yen": 35000,
                "condition": "未使用",
                "description": "Magic Force, 1st Edition, Secret Rare, Near Mint"
            },
            {
                "title": "普通のカード 100円",
                "price_yen": 100,
                "condition": "使用済み",
                "description": "Common card, used condition"
            },
            {
                "title": "高価なカード 100000円",
                "price_yen": 100000,
                "condition": "新品",
                "description": "Very expensive card, new condition"
            }
        ]
    
    def pre_screen_listings(self, listings: List[SimpleCardListing]) -> List[SimpleCardListing]:
        """Pre-screen listings using intelligent filtering (like human intuition)."""
        promising_listings = []
        
        for listing in listings:
            score = 0
            reasons = []
            
            # 1. Price screening (40% weight)
            price_usd = listing.price_usd
            if price_usd < 5:
                score -= 20
                reasons.append("Too cheap (<$5)")
            elif price_usd > 1000:
                score -= 15
                reasons.append("Too expensive (>$1000)")
            elif 10 <= price_usd <= 200:
                score += 20
                reasons.append("Good price range")
            
            # 2. Title keyword analysis (30% weight)
            title_lower = listing.title.lower()
            valuable_cards = ['青眼', 'blue-eyes', 'dark magician', 'ブラック・マジシャン', 
                            'red-eyes', 'レッドアイズ', 'ultimate dragon', 'magician girl']
            valuable_sets = ['lob', 'mfc', 'psv', 'mrd', 'srl', 'lon', '1st', 'ultra', 'secret']
            quality_indicators = ['1st', 'ultra', 'secret', 'mint', 'new', '新品', '未使用']
            
            # Check for valuable cards
            for card in valuable_cards:
                if card in title_lower:
                    score += 15
                    reasons.append(f"Valuable card: {card}")
                    break
            
            # Check for valuable sets
            for set_code in valuable_sets:
                if set_code in title_lower:
                    score += 10
                    reasons.append(f"Valuable set: {set_code}")
                    break
            
            # Check for quality indicators
            for indicator in quality_indicators:
                if indicator in title_lower:
                    score += 5
                    reasons.append(f"Quality indicator: {indicator}")
                    break
            
            # 3. Condition screening (20% weight)
            condition_lower = listing.condition.lower()
            good_conditions = ['新品', '未使用', 'new', 'mint', 'near mint']
            bad_conditions = ['使用済み', 'damaged', 'poor', 'used']
            
            for good_cond in good_conditions:
                if good_cond in condition_lower:
                    score += 10
                    reasons.append(f"Good condition: {good_cond}")
                    break
            
            for bad_cond in bad_conditions:
                if bad_cond in condition_lower:
                    score -= 10
                    reasons.append(f"Bad condition: {bad_cond}")
                    break
            
            # 4. Description analysis (10% weight)
            desc_lower = listing.description.lower()
            if any(word in desc_lower for word in ['mint', 'new', '1st', 'ultra', 'secret']):
                score += 5
                reasons.append("Good description indicators")
            
            # Store screening results
            listing.screening_score = score
            listing.screening_reasons = reasons
            
            # Only include promising listings (score > 0)
            if score > 0:
                promising_listings.append(listing)
                logger.info(f"✅ Promising: {listing.title} (Score: {score})")
            else:
                logger.info(f"❌ Skipped: {listing.title} (Score: {score}, Reasons: {reasons})")
        
        return promising_listings
    
    def calculate_arbitrage_score(self, listing: SimpleCardListing) -> None:
        """Calculate arbitrage score and recommendation."""
        # Simulate eBay price (in real app, this would come from actual data)
        ebay_prices = {
            "青眼の白龍": 80.0,
            "ブラック・マジシャン": 120.0,
            "レッドアイズ・ブラック・ドラゴン": 45.0,
            "Blue-Eyes Ultimate Dragon": 200.0,
            "Dark Magician Girl": 150.0
        }
        
        # Find matching eBay price
        ebay_price = 0
        for card_name, price in ebay_prices.items():
            if card_name.lower() in listing.title.lower():
                ebay_price = price
                break
        
        if ebay_price == 0:
            ebay_price = listing.price_usd * 1.2  # Assume 20% markup
        
        # Calculate profit margin
        profit_margin = ((ebay_price - listing.price_usd) / listing.price_usd) * 100
        listing.profit_margin = profit_margin
        
        # Calculate arbitrage score (0-100)
        score = 0
        
        # Profit margin component (40%)
        if profit_margin > 50:
            score += 40
        elif profit_margin > 30:
            score += 30
        elif profit_margin > 20:
            score += 20
        elif profit_margin > 10:
            score += 10
        
        # Screening score component (30%)
        score += min(listing.screening_score * 0.3, 30)
        
        # Price range component (20%)
        if 10 <= listing.price_usd <= 200:
            score += 20
        elif 5 <= listing.price_usd <= 500:
            score += 10
        
        # Condition component (10%)
        if any(word in listing.condition.lower() for word in ['新品', 'new', 'mint']):
            score += 10
        
        listing.arbitrage_score = min(score, 100)
        
        # Determine recommendation
        if listing.arbitrage_score >= 70:
            listing.recommended_action = "STRONG BUY"
        elif listing.arbitrage_score >= 50:
            listing.recommended_action = "BUY"
        elif listing.arbitrage_score >= 30:
            listing.recommended_action = "CONSIDER"
        else:
            listing.recommended_action = "PASS"
    
    def run(self, search_term: str, max_results: int = 20) -> List[Dict]:
        """Run the simplified arbitrage analysis."""
        logger.info(f"🔍 Searching for: {search_term}")
        
        # Convert sample data to listings
        listings = []
        for item in self.sample_data:
            listing = SimpleCardListing(
                title=item['title'],
                price_yen=item['price_yen'],
                price_usd=item['price_yen'] * self.yen_to_usd,
                condition=item['condition'],
                url=f"https://buyee.jp/sample/{len(listings)}",
                description=item['description']
            )
            listings.append(listing)
        
        logger.info(f"📊 Found {len(listings)} total listings")
        
        # Pre-screen listings (like human intuition)
        promising_listings = self.pre_screen_listings(listings)
        logger.info(f"🎯 Found {len(promising_listings)} promising listings")
        
        # Analyze promising listings
        for listing in promising_listings:
            self.calculate_arbitrage_score(listing)
        
        # Convert to dictionary format for web interface
        results = []
        for listing in promising_listings:
            results.append({
                'title': listing.title,
                'price_yen': listing.price_yen,
                'price_usd': round(listing.price_usd, 2),
                'condition': listing.condition,
                'url': listing.url,
                'description': listing.description,
                'screening_score': listing.screening_score,
                'screening_reasons': listing.screening_reasons,
                'arbitrage_score': round(listing.arbitrage_score, 1),
                'profit_margin': round(listing.profit_margin, 1),
                'recommended_action': listing.recommended_action,
                'ebay_avg_price': 0,  # Would be calculated from real data
                'search_term': search_term
            })
        
        return results

def main():
    """Test the simplified arbitrage tool."""
    tool = SimpleArbitrageTool()
    
    # Test with different search terms
    search_terms = ["青眼の白龍", "Blue-Eyes", "Dark Magician"]
    
    for term in search_terms:
        print(f"\n{'='*50}")
        print(f"🔍 Testing: {term}")
        print(f"{'='*50}")
        
        results = tool.run(term, max_results=10)
        
        print(f"\n📊 Results Summary:")
        print(f"Total promising listings: {len(results)}")
        
        if results:
            print(f"\n🎯 Top Recommendations:")
            for i, result in enumerate(results[:3], 1):
                print(f"{i}. {result['title']}")
                print(f"   Price: ¥{result['price_yen']} (${result['price_usd']})")
                print(f"   Score: {result['arbitrage_score']} | Action: {result['recommended_action']}")
                print(f"   Profit: {result['profit_margin']}%")
                print()
        else:
            print("❌ No promising listings found")

if __name__ == '__main__':
    main() 