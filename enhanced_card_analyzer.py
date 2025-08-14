#!/usr/bin/env python3
"""
Enhanced Card Analyzer with AI-powered features
- Better condition assessment
- Fake detection
- Market trend analysis
- Smart pricing recommendations
"""

import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import requests
import json
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class CardCondition(Enum):
    MINT = "Mint"
    NEAR_MINT = "Near Mint"
    EXCELLENT = "Excellent"
    GOOD = "Good"
    LIGHT_PLAYED = "Light Played"
    PLAYED = "Played"
    POOR = "Poor"
    UNKNOWN = "Unknown"

class CardRarity(Enum):
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    SUPER_RARE = "Super Rare"
    ULTRA_RARE = "Ultra Rare"
    SECRET_RARE = "Secret Rare"
    GHOST_RARE = "Ghost Rare"
    STARRARE = "Star Rare"
    PRISMATIC_SECRET_RARE = "Prismatic Secret Rare"
    UNKNOWN = "Unknown"

@dataclass
class EnhancedCardInfo:
    """Enhanced card information with AI analysis"""
    title: str
    condition: CardCondition
    rarity: CardRarity
    set_code: Optional[str]
    card_number: Optional[str]
    edition: Optional[str]
    region: Optional[str]
    is_valuable: bool
    confidence_score: float
    estimated_value_usd: Optional[float]
    market_trend: str  # "rising", "falling", "stable"
    risk_factors: List[str]
    authenticity_score: float  # 0-1, higher is more likely authentic
    condition_notes: List[str]
    price_recommendation: str  # "buy", "hold", "sell", "avoid"

class EnhancedCardAnalyzer:
    """Enhanced card analyzer with AI-powered features"""
    
    def __init__(self, use_ai: bool = True):
        self.use_ai = use_ai
        self.condition_keywords = {
            CardCondition.MINT: ["mint", "perfect", "gem", "psa 10", "bgs 10", "未使用", "新品"],
            CardCondition.NEAR_MINT: ["near mint", "nm", "excellent", "like new", "美品", "ほぼ新品"],
            CardCondition.EXCELLENT: ["excellent", "ex", "very good", "良品"],
            CardCondition.GOOD: ["good", "gd", "light wear", "軽い使用感"],
            CardCondition.LIGHT_PLAYED: ["light played", "lp", "minor wear", "軽い傷"],
            CardCondition.PLAYED: ["played", "p", "moderate wear", "使用感あり"],
            CardCondition.POOR: ["poor", "damaged", "heavy wear", "傷あり", "破損"]
        }
        
        self.rarity_keywords = {
            CardRarity.COMMON: ["common", "c", "コモン"],
            CardRarity.UNCOMMON: ["uncommon", "uc", "アンコモン"],
            CardRarity.RARE: ["rare", "r", "レア"],
            CardRarity.SUPER_RARE: ["super rare", "sr", "スーパーレア", "ultra rare", "ur"],
            CardRarity.ULTRA_RARE: ["ultra rare", "ur", "ウルトラレア"],
            CardRarity.SECRET_RARE: ["secret rare", "scr", "シークレットレア"],
            CardRarity.GHOST_RARE: ["ghost rare", "gr", "ゴーストレア"],
            CardRarity.STARRARE: ["star rare", "star", "スター"],
            CardRarity.PRISMATIC_SECRET_RARE: ["prismatic", "prismatic secret", "プリズマティック"]
        }
        
        # Valuable card patterns
        self.valuable_patterns = [
            r"1st edition|first edition|初版",
            r"psa \d+|bgs \d+",
            r"graded|グレード",
            r"limited edition|限定版",
            r"promo|promotional|プロモ",
            r"tournament|championship|大会",
            r"misprint|error|エラー",
            r"test print|test card|テスト",
            r"prototype|プロトタイプ"
        ]
        
        # Fake detection patterns
        self.fake_indicators = [
            r"replica|reproduction|複製",
            r"fake|counterfeit|偽物",
            r"proxy|proxy card|プロキシ",
            r"custom|homemade|手作り",
            r"fan art|fan made|ファンアート"
        ]
    
    def analyze_card(self, card_data: Dict[str, Any]) -> EnhancedCardInfo:
        """Analyze a card with enhanced AI features"""
        title = card_data.get('title', '')
        price_text = card_data.get('price_text', '')
        image_url = card_data.get('image_url', '')
        
        # Basic analysis
        condition = self._analyze_condition(title, price_text)
        rarity = self._analyze_rarity(title)
        set_code, card_number, edition, region = self._extract_card_details(title)
        
        # Enhanced analysis
        is_valuable = self._assess_value(title, condition, rarity)
        confidence_score = self._calculate_confidence(title, condition, rarity)
        estimated_value = self._estimate_value(title, condition, rarity)
        market_trend = self._analyze_market_trend(title)
        risk_factors = self._identify_risk_factors(title, price_text)
        authenticity_score = self._assess_authenticity(title, image_url)
        condition_notes = self._generate_condition_notes(title, condition)
        price_recommendation = self._generate_price_recommendation(
            estimated_value, card_data.get('price_usd', 0), risk_factors
        )
        
        return EnhancedCardInfo(
            title=title,
            condition=condition,
            rarity=rarity,
            set_code=set_code,
            card_number=card_number,
            edition=edition,
            region=region,
            is_valuable=is_valuable,
            confidence_score=confidence_score,
            estimated_value_usd=estimated_value,
            market_trend=market_trend,
            risk_factors=risk_factors,
            authenticity_score=authenticity_score,
            condition_notes=condition_notes,
            price_recommendation=price_recommendation
        )
    
    def _analyze_condition(self, title: str, price_text: str) -> CardCondition:
        """Enhanced condition analysis"""
        text = f"{title} {price_text}".lower()
        
        # Check for specific condition indicators
        for condition, keywords in self.condition_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return condition
        
        # Check for Japanese condition indicators
        japanese_conditions = {
            "新品": CardCondition.MINT,
            "未使用": CardCondition.MINT,
            "美品": CardCondition.NEAR_MINT,
            "ほぼ新品": CardCondition.NEAR_MINT,
            "良品": CardCondition.EXCELLENT,
            "軽い使用感": CardCondition.GOOD,
            "軽い傷": CardCondition.LIGHT_PLAYED,
            "使用感あり": CardCondition.PLAYED,
            "傷あり": CardCondition.POOR,
            "破損": CardCondition.POOR
        }
        
        for jp_condition, condition_enum in japanese_conditions.items():
            if jp_condition in text:
                return condition_enum
        
        return CardCondition.UNKNOWN
    
    def _analyze_rarity(self, title: str) -> CardRarity:
        """Enhanced rarity analysis"""
        text = title.lower()
        
        for rarity, keywords in self.rarity_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return rarity
        
        return CardRarity.UNKNOWN
    
    def _extract_card_details(self, title: str) -> tuple:
        """Extract card details from title"""
        set_code = None
        card_number = None
        edition = None
        region = None
        
        # Extract set code (e.g., LOB-001, 1ST-EN001)
        set_pattern = r'([A-Z]{2,4})-(\d{3,4})'
        match = re.search(set_pattern, title.upper())
        if match:
            set_code = match.group(1)
            card_number = match.group(2)
        
        # Extract edition
        if re.search(r'1st|first|初版', title, re.IGNORECASE):
            edition = "1st Edition"
        elif re.search(r'unlimited|無制限', title, re.IGNORECASE):
            edition = "Unlimited"
        
        # Extract region
        if re.search(r'asia|asian|アジア', title, re.IGNORECASE):
            region = "Asian"
        elif re.search(r'europe|eu|欧州', title, re.IGNORECASE):
            region = "European"
        elif re.search(r'japan|jp|日本', title, re.IGNORECASE):
            region = "Japanese"
        else:
            region = "International"
        
        return set_code, card_number, edition, region
    
    def _assess_value(self, title: str, condition: CardCondition, rarity: CardRarity) -> bool:
        """Assess if a card is valuable"""
        text = title.lower()
        
        # Check for valuable patterns
        for pattern in self.valuable_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check for high rarity
        if rarity in [CardRarity.SECRET_RARE, CardRarity.GHOST_RARE, CardRarity.PRISMATIC_SECRET_RARE]:
            return True
        
        # Check for mint condition
        if condition in [CardCondition.MINT, CardCondition.NEAR_MINT]:
            return True
        
        return False
    
    def _calculate_confidence(self, title: str, condition: CardCondition, rarity: CardRarity) -> float:
        """Calculate confidence score for analysis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on clear indicators
        if condition != CardCondition.UNKNOWN:
            confidence += 0.2
        if rarity != CardRarity.UNKNOWN:
            confidence += 0.2
        if any(re.search(pattern, title, re.IGNORECASE) for pattern in self.valuable_patterns):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _estimate_value(self, title: str, condition: CardCondition, rarity: CardRarity) -> Optional[float]:
        """Estimate card value based on various factors"""
        # This would ideally connect to a pricing API
        # For now, return None to indicate no estimate available
        return None
    
    def _analyze_market_trend(self, title: str) -> str:
        """Analyze market trend for the card"""
        # This would ideally connect to market data APIs
        # For now, return stable as default
        return "stable"
    
    def _identify_risk_factors(self, title: str, price_text: str) -> List[str]:
        """Identify potential risk factors"""
        risks = []
        text = f"{title} {price_text}".lower()
        
        # Check for fake indicators
        for pattern in self.fake_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                risks.append("Potential fake/replica")
                break
        
        # Check for suspiciously low prices
        try:
            price_match = re.search(r'(\d+)', price_text)
            if price_match:
                price = int(price_match.group(1))
                if price < 100:  # Very low price might indicate fake
                    risks.append("Suspiciously low price")
        except:
            pass
        
        # Check for poor condition
        if "damaged" in text or "破損" in text:
            risks.append("Damaged condition")
        
        return risks
    
    def _assess_authenticity(self, title: str, image_url: str) -> float:
        """Assess authenticity score (0-1)"""
        text = title.lower()
        authenticity = 0.8  # Base authenticity score
        
        # Reduce score for suspicious indicators
        for pattern in self.fake_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                authenticity -= 0.5
                break
        
        # Increase score for legitimate indicators
        if re.search(r'psa|bgs|graded', text, re.IGNORECASE):
            authenticity += 0.1
        
        return max(0.0, min(1.0, authenticity))
    
    def _generate_condition_notes(self, title: str, condition: CardCondition) -> List[str]:
        """Generate detailed condition notes"""
        notes = []
        text = title.lower()
        
        if condition == CardCondition.MINT:
            notes.append("Perfect condition, no visible wear")
        elif condition == CardCondition.NEAR_MINT:
            notes.append("Minimal wear, excellent condition")
        elif condition == CardCondition.PLAYED:
            notes.append("Visible wear, may affect value")
        elif condition == CardCondition.POOR:
            notes.append("Significant damage, low value")
        
        # Add specific condition details
        if "corner" in text and ("bend" in text or "damage" in text):
            notes.append("Corner damage noted")
        if "edge" in text and ("wear" in text or "damage" in text):
            notes.append("Edge wear noted")
        if "surface" in text and ("scratch" in text or "mark" in text):
            notes.append("Surface marks noted")
        
        return notes
    
    def _generate_price_recommendation(self, estimated_value: Optional[float], 
                                     current_price: float, risk_factors: List[str]) -> str:
        """Generate price recommendation"""
        if not estimated_value:
            return "hold"  # No estimate available
        
        if risk_factors:
            return "avoid"  # Risk factors present
        
        price_ratio = current_price / estimated_value if estimated_value > 0 else 1
        
        if price_ratio < 0.7:
            return "buy"  # Good deal
        elif price_ratio < 0.9:
            return "consider"  # Fair price
        elif price_ratio > 1.2:
            return "sell"  # Overpriced
        else:
            return "hold"  # Market price

# Example usage
if __name__ == "__main__":
    analyzer = EnhancedCardAnalyzer()
    
    test_cards = [
        {
            'title': 'Blue-Eyes White Dragon LOB-001 1st Edition PSA 10',
            'price_text': '¥50000',
            'image_url': 'https://example.com/image.jpg'
        },
        {
            'title': 'Dark Magician SDY-006 Near Mint',
            'price_text': '¥2000',
            'image_url': 'https://example.com/image2.jpg'
        }
    ]
    
    for card in test_cards:
        result = analyzer.analyze_card(card)
        print(f"Card: {result.title}")
        print(f"Condition: {result.condition.value}")
        print(f"Rarity: {result.rarity.value}")
        print(f"Valuable: {result.is_valuable}")
        print(f"Confidence: {result.confidence_score}")
        print(f"Authenticity: {result.authenticity_score}")
        print(f"Risk Factors: {result.risk_factors}")
        print(f"Recommendation: {result.price_recommendation}")
        print("-" * 50)
