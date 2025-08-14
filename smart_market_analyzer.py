#!/usr/bin/env python3
"""
Smart Market Analyzer for Yu-Gi-Oh! Cards
- Market trend analysis
- Price prediction
- Arbitrage opportunity detection
- Risk assessment
"""

import logging
import requests
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Market data for a card"""
    card_name: str
    set_code: str
    current_price: float
    historical_prices: List[Tuple[datetime, float]]
    volume: int
    trend: str  # "rising", "falling", "stable"
    volatility: float
    market_cap: float
    last_updated: datetime

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity analysis"""
    card_name: str
    buyee_price: float
    ebay_price: float
    profit_margin: float
    profit_amount: float
    risk_score: float
    confidence: float
    market_trend: str
    recommended_action: str
    notes: List[str]

class SmartMarketAnalyzer:
    """Smart market analyzer with advanced features"""
    
    def __init__(self):
        self.market_data = {}
        self.price_history = defaultdict(list)
        self.trend_analysis = {}
        self.risk_factors = {}
        
        # Market trend indicators
        self.trend_indicators = {
            'rising': ['increasing', 'up', 'higher', 'growing', 'bullish'],
            'falling': ['decreasing', 'down', 'lower', 'declining', 'bearish'],
            'stable': ['stable', 'steady', 'consistent', 'flat']
        }
        
        # Risk assessment weights
        self.risk_weights = {
            'price_volatility': 0.3,
            'market_volume': 0.2,
            'condition_uncertainty': 0.2,
            'authenticity_risk': 0.15,
            'market_trend': 0.15
        }
    
    def analyze_market_trends(self, card_data: List[Dict]) -> Dict[str, Any]:
        """Analyze market trends across multiple cards"""
        trends = {
            'overall_trend': 'stable',
            'hot_cards': [],
            'declining_cards': [],
            'stable_cards': [],
            'market_insights': []
        }
        
        # Analyze individual card trends
        for card in card_data:
            card_trend = self._analyze_single_card_trend(card)
            if card_trend['trend'] == 'rising':
                trends['hot_cards'].append({
                    'name': card.get('title', ''),
                    'trend_strength': card_trend['strength'],
                    'price_change': card_trend['price_change']
                })
            elif card_trend['trend'] == 'falling':
                trends['declining_cards'].append({
                    'name': card.get('title', ''),
                    'trend_strength': card_trend['strength'],
                    'price_change': card_trend['price_change']
                })
            else:
                trends['stable_cards'].append({
                    'name': card.get('title', ''),
                    'trend_strength': card_trend['strength']
                })
        
        # Determine overall market trend
        if len(trends['hot_cards']) > len(trends['declining_cards']) * 1.5:
            trends['overall_trend'] = 'rising'
        elif len(trends['declining_cards']) > len(trends['hot_cards']) * 1.5:
            trends['overall_trend'] = 'falling'
        
        # Generate market insights
        trends['market_insights'] = self._generate_market_insights(trends)
        
        return trends
    
    def _analyze_single_card_trend(self, card: Dict) -> Dict[str, Any]:
        """Analyze trend for a single card"""
        title = card.get('title', '')
        price = card.get('price_usd', 0)
        
        # Simple trend analysis based on price and keywords
        trend = 'stable'
        strength = 0.5
        price_change = 0
        
        # Check for trend indicators in title
        title_lower = title.lower()
        
        # Rising indicators
        rising_indicators = ['psa', 'graded', '1st edition', 'limited', 'rare']
        rising_count = sum(1 for indicator in rising_indicators if indicator in title_lower)
        
        # Falling indicators
        falling_indicators = ['damaged', 'poor', 'reprint', 'common']
        falling_count = sum(1 for indicator in falling_indicators if indicator in title_lower)
        
        if rising_count > falling_count:
            trend = 'rising'
            strength = min(0.9, 0.5 + (rising_count * 0.1))
            price_change = rising_count * 5  # Estimated price increase
        elif falling_count > rising_count:
            trend = 'falling'
            strength = min(0.9, 0.5 + (falling_count * 0.1))
            price_change = -falling_count * 3  # Estimated price decrease
        
        return {
            'trend': trend,
            'strength': strength,
            'price_change': price_change
        }
    
    def _generate_market_insights(self, trends: Dict) -> List[str]:
        """Generate market insights based on trends"""
        insights = []
        
        hot_count = len(trends['hot_cards'])
        declining_count = len(trends['declining_cards'])
        stable_count = len(trends['stable_cards'])
        
        if hot_count > 0:
            insights.append(f"Found {hot_count} cards with rising value trends")
            if hot_count > 5:
                insights.append("Strong bullish market sentiment detected")
        
        if declining_count > 0:
            insights.append(f"Found {declining_count} cards with declining value trends")
            if declining_count > 5:
                insights.append("Bearish market sentiment detected")
        
        if stable_count > hot_count + declining_count:
            insights.append("Market appears stable with most cards maintaining value")
        
        # Price range insights
        if trends['hot_cards']:
            avg_hot_price = np.mean([card['price_change'] for card in trends['hot_cards']])
            insights.append(f"Average price increase for hot cards: ${avg_hot_price:.2f}")
        
        if trends['declining_cards']:
            avg_declining_price = np.mean([card['price_change'] for card in trends['declining_cards']])
            insights.append(f"Average price decrease for declining cards: ${abs(avg_declining_price):.2f}")
        
        return insights
    
    def calculate_arbitrage_score(self, buyee_price: float, ebay_price: float, 
                                condition: str, authenticity_score: float) -> float:
        """Calculate arbitrage score (0-100)"""
        if ebay_price <= 0 or buyee_price <= 0:
            return 0
        
        # Base profit margin
        profit_margin = (ebay_price - buyee_price) / buyee_price * 100
        
        # Condition multiplier
        condition_multiplier = self._get_condition_multiplier(condition)
        
        # Authenticity multiplier
        authenticity_multiplier = authenticity_score
        
        # Market trend multiplier
        trend_multiplier = 1.0  # Could be enhanced with actual trend data
        
        # Calculate final score
        base_score = min(profit_margin * 2, 50)  # Max 50 points for profit
        condition_bonus = 20 * condition_multiplier
        authenticity_bonus = 20 * authenticity_multiplier
        trend_bonus = 10 * trend_multiplier
        
        total_score = base_score + condition_bonus + authenticity_bonus + trend_bonus
        
        return min(total_score, 100)
    
    def _get_condition_multiplier(self, condition: str) -> float:
        """Get condition multiplier for scoring"""
        condition_multipliers = {
            'mint': 1.0,
            'near mint': 0.9,
            'excellent': 0.8,
            'good': 0.7,
            'light played': 0.6,
            'played': 0.5,
            'poor': 0.3,
            'unknown': 0.5
        }
        
        condition_lower = condition.lower()
        for key, multiplier in condition_multipliers.items():
            if key in condition_lower:
                return multiplier
        
        return 0.5  # Default for unknown conditions
    
    def assess_risk(self, card_data: Dict, market_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Assess risk factors for a card"""
        risk_factors = []
        risk_score = 0.0
        
        title = card_data.get('title', '')
        price = card_data.get('price_usd', 0)
        condition = card_data.get('condition', 'unknown')
        
        # Price volatility risk
        if price < 10:
            risk_factors.append("Very low price - potential fake")
            risk_score += 0.3
        elif price > 1000:
            risk_factors.append("High value item - increased scrutiny")
            risk_score += 0.1
        
        # Condition risk
        if 'damaged' in condition.lower() or 'poor' in condition.lower():
            risk_factors.append("Poor condition affects resale value")
            risk_score += 0.2
        
        # Authenticity risk
        fake_indicators = ['replica', 'fake', 'proxy', 'custom', 'fan art']
        if any(indicator in title.lower() for indicator in fake_indicators):
            risk_factors.append("Potential fake/replica detected")
            risk_score += 0.4
        
        # Market trend risk
        if market_data and market_data.get('trend') == 'falling':
            risk_factors.append("Declining market trend")
            risk_score += 0.15
        
        # Volume risk
        if market_data and market_data.get('volume', 0) < 5:
            risk_factors.append("Low market volume - hard to resell")
            risk_score += 0.2
        
        return {
            'risk_score': min(risk_score, 1.0),
            'risk_factors': risk_factors,
            'risk_level': self._get_risk_level(risk_score)
        }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score < 0.3:
            return "Low"
        elif risk_score < 0.6:
            return "Medium"
        else:
            return "High"
    
    def predict_price_movement(self, card_data: Dict, timeframe_days: int = 30) -> Dict[str, Any]:
        """Predict price movement for a card"""
        title = card_data.get('title', '')
        current_price = card_data.get('price_usd', 0)
        
        # Simple prediction based on card characteristics
        prediction = {
            'direction': 'stable',
            'percentage_change': 0,
            'confidence': 0.5,
            'factors': []
        }
        
        # Analyze factors that affect price
        factors = []
        
        # Rarity factor
        if any(rarity in title.lower() for rarity in ['secret rare', 'ghost rare', 'prismatic']):
            factors.append(('rarity', 0.1))  # 10% increase
        
        # Condition factor
        if 'mint' in title.lower() or 'psa' in title.lower():
            factors.append(('condition', 0.15))  # 15% increase
        
        # Edition factor
        if '1st edition' in title.lower():
            factors.append(('edition', 0.2))  # 20% increase
        
        # Market trend factor
        if 'limited' in title.lower() or 'promo' in title.lower():
            factors.append(('market_trend', 0.1))  # 10% increase
        
        # Calculate total prediction
        total_change = sum(factor[1] for factor in factors)
        
        if total_change > 0.05:  # More than 5% increase
            prediction['direction'] = 'rising'
            prediction['percentage_change'] = total_change * 100
            prediction['confidence'] = min(0.8, 0.5 + len(factors) * 0.1)
        elif total_change < -0.05:  # More than 5% decrease
            prediction['direction'] = 'falling'
            prediction['percentage_change'] = abs(total_change) * 100
            prediction['confidence'] = min(0.8, 0.5 + len(factors) * 0.1)
        
        prediction['factors'] = [factor[0] for factor in factors]
        
        return prediction
    
    def get_optimal_buying_strategy(self, opportunities: List[ArbitrageOpportunity]) -> Dict[str, Any]:
        """Get optimal buying strategy based on opportunities"""
        if not opportunities:
            return {'strategy': 'wait', 'reason': 'No profitable opportunities found'}
        
        # Sort by profit margin
        sorted_opportunities = sorted(opportunities, key=lambda x: x.profit_margin, reverse=True)
        
        # Calculate portfolio allocation
        total_investment = 1000  # Example budget
        allocation = []
        
        for i, opp in enumerate(sorted_opportunities[:5]):  # Top 5 opportunities
            if opp.risk_score < 0.5:  # Low risk
                allocation_percent = 25 - (i * 5)  # 25%, 20%, 15%, 10%, 5%
                allocation.append({
                    'card': opp.card_name,
                    'percentage': allocation_percent,
                    'amount': total_investment * allocation_percent / 100,
                    'expected_profit': opp.profit_amount * allocation_percent / 100
                })
        
        # Calculate expected return
        total_expected_profit = sum(item['expected_profit'] for item in allocation)
        expected_roi = (total_expected_profit / total_investment) * 100
        
        return {
            'strategy': 'diversified_buy',
            'allocation': allocation,
            'total_investment': total_investment,
            'expected_profit': total_expected_profit,
            'expected_roi': expected_roi,
            'risk_level': 'medium' if any(opp.risk_score > 0.3 for opp in sorted_opportunities[:5]) else 'low'
        }

# Example usage
if __name__ == "__main__":
    analyzer = SmartMarketAnalyzer()
    
    # Test market trend analysis
    test_cards = [
        {'title': 'Blue-Eyes White Dragon LOB-001 PSA 10', 'price_usd': 500},
        {'title': 'Dark Magician SDY-006 Damaged', 'price_usd': 50},
        {'title': 'Red-Eyes Black Dragon SDJ-001 Near Mint', 'price_usd': 200}
    ]
    
    trends = analyzer.analyze_market_trends(test_cards)
    print("Market Trends:")
    print(json.dumps(trends, indent=2, default=str))
    
    # Test arbitrage scoring
    score = analyzer.calculate_arbitrage_score(100, 150, 'near mint', 0.9)
    print(f"\nArbitrage Score: {score:.1f}/100")
    
    # Test risk assessment
    risk = analyzer.assess_risk({'title': 'Fake Blue-Eyes Dragon', 'price_usd': 5, 'condition': 'mint'})
    print(f"\nRisk Assessment: {risk}")
    
    # Test price prediction
    prediction = analyzer.predict_price_movement({'title': 'Blue-Eyes White Dragon 1st Edition PSA 10'})
    print(f"\nPrice Prediction: {prediction}")
