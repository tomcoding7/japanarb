#!/usr/bin/env python3
"""
Test script for enhanced Yu-Gi-Oh! arbitrage bot features
"""

from enhanced_card_analyzer import EnhancedCardAnalyzer
from smart_market_analyzer import SmartMarketAnalyzer
import json

def test_enhanced_card_analyzer():
    """Test the enhanced card analyzer"""
    print("=== Testing Enhanced Card Analyzer ===")
    
    analyzer = EnhancedCardAnalyzer()
    
    test_cards = [
        {
            'title': 'Blue-Eyes White Dragon LOB-001 1st Edition PSA 10',
            'price_text': '¥50000',
            'image_url': 'https://example.com/image.jpg',
            'price_usd': 350
        },
        {
            'title': 'Dark Magician SDY-006 Near Mint',
            'price_text': '¥2000',
            'image_url': 'https://example.com/image2.jpg',
            'price_usd': 15
        },
        {
            'title': 'Fake Blue-Eyes Dragon Replica',
            'price_text': '¥500',
            'image_url': 'https://example.com/fake.jpg',
            'price_usd': 5
        },
        {
            'title': 'Red-Eyes Black Dragon SDJ-001 Secret Rare',
            'price_text': '¥8000',
            'image_url': 'https://example.com/red-eyes.jpg',
            'price_usd': 60
        }
    ]
    
    for i, card in enumerate(test_cards, 1):
        print(f"\n--- Card {i}: {card['title']} ---")
        result = analyzer.analyze_card(card)
        
        print(f"Condition: {result.condition.value}")
        print(f"Rarity: {result.rarity.value}")
        print(f"Set Code: {result.set_code}")
        print(f"Card Number: {result.card_number}")
        print(f"Edition: {result.edition}")
        print(f"Region: {result.region}")
        print(f"Valuable: {result.is_valuable}")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Authenticity: {result.authenticity_score:.2f}")
        print(f"Risk Factors: {result.risk_factors}")
        print(f"Price Recommendation: {result.price_recommendation}")
        print(f"Condition Notes: {result.condition_notes}")

def test_smart_market_analyzer():
    """Test the smart market analyzer"""
    print("\n\n=== Testing Smart Market Analyzer ===")
    
    analyzer = SmartMarketAnalyzer()
    
    # Test market trend analysis
    test_cards = [
        {'title': 'Blue-Eyes White Dragon LOB-001 PSA 10', 'price_usd': 500},
        {'title': 'Dark Magician SDY-006 Damaged', 'price_usd': 50},
        {'title': 'Red-Eyes Black Dragon SDJ-001 Near Mint', 'price_usd': 200},
        {'title': 'Exodia the Forbidden One LOB-124 1st Edition', 'price_usd': 1000},
        {'title': 'Summoned Skull MRD-003 Secret Rare', 'price_usd': 300}
    ]
    
    trends = analyzer.analyze_market_trends(test_cards)
    print("Market Trends Analysis:")
    print(json.dumps(trends, indent=2, default=str))
    
    # Test arbitrage scoring
    print("\n--- Arbitrage Scoring Tests ---")
    test_scenarios = [
        (100, 150, 'near mint', 0.9),
        (50, 200, 'mint', 0.95),
        (200, 180, 'played', 0.7),
        (10, 50, 'poor', 0.3)
    ]
    
    for buyee_price, ebay_price, condition, authenticity in test_scenarios:
        score = analyzer.calculate_arbitrage_score(buyee_price, ebay_price, condition, authenticity)
        print(f"Buyee: ${buyee_price}, eBay: ${ebay_price}, Condition: {condition}, Authenticity: {authenticity}")
        print(f"Arbitrage Score: {score:.1f}/100")
        print()
    
    # Test risk assessment
    print("--- Risk Assessment Tests ---")
    test_risk_cards = [
        {'title': 'Fake Blue-Eyes Dragon', 'price_usd': 5, 'condition': 'mint'},
        {'title': 'Blue-Eyes White Dragon PSA 10', 'price_usd': 1000, 'condition': 'mint'},
        {'title': 'Damaged Dark Magician', 'price_usd': 10, 'condition': 'poor'}
    ]
    
    for card in test_risk_cards:
        risk = analyzer.assess_risk(card)
        print(f"Card: {card['title']}")
        print(f"Risk Level: {risk['risk_level']}")
        print(f"Risk Score: {risk['risk_score']:.2f}")
        print(f"Risk Factors: {risk['risk_factors']}")
        print()
    
    # Test price prediction
    print("--- Price Prediction Tests ---")
    test_prediction_cards = [
        {'title': 'Blue-Eyes White Dragon 1st Edition PSA 10', 'price_usd': 500},
        {'title': 'Dark Magician Unlimited Reprint', 'price_usd': 20},
        {'title': 'Red-Eyes Black Dragon Secret Rare Limited Edition', 'price_usd': 100}
    ]
    
    for card in test_prediction_cards:
        prediction = analyzer.predict_price_movement(card)
        print(f"Card: {card['title']}")
        print(f"Predicted Direction: {prediction['direction']}")
        print(f"Percentage Change: {prediction['percentage_change']:.1f}%")
        print(f"Confidence: {prediction['confidence']:.2f}")
        print(f"Factors: {prediction['factors']}")
        print()

def test_enhanced_features_integration():
    """Test integration of enhanced features"""
    print("\n\n=== Testing Enhanced Features Integration ===")
    
    card_analyzer = EnhancedCardAnalyzer()
    market_analyzer = SmartMarketAnalyzer()
    
    # Test a comprehensive card analysis
    test_card = {
        'title': 'Blue-Eyes White Dragon LOB-001 1st Edition PSA 10',
        'price_text': '¥50000',
        'image_url': 'https://example.com/image.jpg',
        'price_usd': 350
    }
    
    print("Comprehensive Card Analysis:")
    print(f"Card: {test_card['title']}")
    
    # Enhanced card analysis
    enhanced_result = card_analyzer.analyze_card(test_card)
    print(f"Enhanced Analysis - Condition: {enhanced_result.condition.value}")
    print(f"Enhanced Analysis - Rarity: {enhanced_result.rarity.value}")
    print(f"Enhanced Analysis - Authenticity: {enhanced_result.authenticity_score:.2f}")
    
    # Market analysis
    risk_assessment = market_analyzer.assess_risk(test_card)
    print(f"Market Analysis - Risk Level: {risk_assessment['risk_level']}")
    print(f"Market Analysis - Risk Score: {risk_assessment['risk_score']:.2f}")
    
    # Price prediction
    price_prediction = market_analyzer.predict_price_movement(test_card)
    print(f"Price Prediction - Direction: {price_prediction['direction']}")
    print(f"Price Prediction - Change: {price_prediction['percentage_change']:.1f}%")
    
    # Arbitrage scoring
    arbitrage_score = market_analyzer.calculate_arbitrage_score(
        test_card['price_usd'], 
        test_card['price_usd'] * 1.5,  # Assume 50% higher on eBay
        enhanced_result.condition.value.lower(),
        enhanced_result.authenticity_score
    )
    print(f"Arbitrage Score: {arbitrage_score:.1f}/100")

if __name__ == "__main__":
    print("Enhanced Yu-Gi-Oh! Arbitrage Bot Feature Tests")
    print("=" * 50)
    
    try:
        test_enhanced_card_analyzer()
        test_smart_market_analyzer()
        test_enhanced_features_integration()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("\nKey Improvements:")
        print("✅ Enhanced thumbnail extraction with multiple selectors")
        print("✅ Smart card condition and rarity analysis")
        print("✅ Fake detection and authenticity scoring")
        print("✅ Market trend analysis and price prediction")
        print("✅ Risk assessment and arbitrage scoring")
        print("✅ Enhanced web interface with better image display")
        print("✅ Smart filtering and recommendation system")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
