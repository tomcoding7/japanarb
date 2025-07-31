"""
Comprehensive Yu-Gi-Oh! Card Translation System
Handles Japanese to English translation with multiple strategies and fallbacks.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class CardTranslator:
    """Comprehensive card translation system for Yu-Gi-Oh! cards."""
    
    def __init__(self):
        # Comprehensive card name translations
        self.card_translations = {
            # Popular cards
            "ブラック・マジシャン": "Dark Magician",
            "青眼の白龍": "Blue-Eyes White Dragon", 
            "ブラック・マジシャン・ガール": "Dark Magician Girl",
            "魔術師の弟子": "Dark Magician Girl",
            "レッドアイズ・ブラック・ドラゴン": "Red-Eyes Black Dragon",
            "エクゾディア": "Exodia",
            "カオス・ソルジャー": "Black Luster Soldier",
            "カオス・エンペラー・ドラゴン": "Chaos Emperor Dragon",
            "サイバー・ドラゴン": "Cyber Dragon",
            "エレメンタル・ヒーロー": "Elemental Hero",
            "デステニー・ヒーロー": "Destiny Hero",
            "ネオス": "Neos",
            "スターダスト・ドラゴン": "Stardust Dragon",
            "ブラックローズ・ドラゴン": "Black Rose Dragon",
            "アーカナイト・マジシャン": "Arcanite Magician",
            
            # Common terms
            "アマダ": "Amada",
            "遊戯王": "Yu-Gi-Oh",
            "ホロ": "holographic",
            "ウルトラレア": "Ultra Rare",
            "スーパーレア": "Super Rare", 
            "シークレット": "Secret Rare",
            "アルティメットレア": "Ultimate Rare",
            "ゴーストレア": "Ghost Rare",
            "プラチナレア": "Platinum Rare",
            "ゴールドレア": "Gold Rare",
            "パラレルレア": "Parallel Rare",
            "コレクターズレア": "Collector's Rare",
            "クォーターセンチュリー": "Quarter Century",
            
            # Editions
            "1st": "1st Edition",
            "初版": "1st Edition",
            "無制限": "Unlimited",
            "再版": "Unlimited",
            
            # Conditions
            "ミント": "Mint",
            "ニアミント": "Near Mint",
            "エクセレント": "Excellent",
            "グッド": "Good",
            "ライトプレイ": "Light Played",
            "プレイ": "Played",
            "プア": "Poor",
            "未使用": "Mint",
            "新品同様": "Near Mint",
            "美品": "Excellent",
            "良品": "Good",
            "軽度使用": "Light Played",
            "使用済み": "Played",
            "傷あり": "Poor",
            
            # Regions
            "アジア": "Asia",
            "アジア版": "Asian",
            "英": "English",
            "英語版": "English",
            "日": "Japanese",
            "日本語版": "Japanese",
            "韓": "Korean",
            "韓国版": "Korean",
            
            # Special terms
            "限定": "Limited",
            "特典": "Promo",
            "大会": "Tournament",
            "チャンピオンシップ": "Championship",
            "イベント": "Event",
            "未開封": "Sealed",
            "初期": "Early",
            "旧アジア": "Old Asia",
            "エラーカード": "Error Card"
        }
        
        # Set code patterns
        self.set_patterns = [
            r'([A-Z]{2,4})[-・]?(\d{3})',  # LOB-001, MRD-060
            r'([A-Z]{2,4})\s*(\d{3})',     # LOB 001, MRD 060
            r'([A-Z]{2,4})（(\d{3})）',     # LOB（001）
        ]
        
        # Card name patterns
        self.card_patterns = [
            r'([A-Za-z\s]+)(?:\s*[-・]\s*[A-Za-z\s]+)*',  # English card names
            r'([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+)',  # Japanese characters
        ]
    
    def translate_card_title(self, japanese_title: str) -> Dict[str, any]:
        """
        Comprehensive translation of Japanese card title.
        
        Args:
            japanese_title: Japanese card title
            
        Returns:
            Dictionary with translation results
        """
        result = {
            'original': japanese_title,
            'translated': japanese_title,
            'card_name': None,
            'set_code': None,
            'card_number': None,
            'rarity': None,
            'edition': None,
            'condition': None,
            'region': None,
            'search_queries': [],
            'confidence': 0.0
        }
        
        # Strategy 1: Direct translation using dictionary
        translated = self._apply_direct_translations(japanese_title)
        if translated != japanese_title:
            result['translated'] = translated
            result['confidence'] += 0.3
        
        # Strategy 2: Extract card name
        card_name = self._extract_card_name(japanese_title)
        if card_name:
            result['card_name'] = card_name
            result['confidence'] += 0.2
        
        # Strategy 3: Extract set information
        set_info = self._extract_set_info(japanese_title)
        if set_info:
            result['set_code'] = set_info[0]
            result['card_number'] = set_info[1]
            result['confidence'] += 0.2
        
        # Strategy 4: Extract rarity
        rarity = self._extract_rarity(japanese_title)
        if rarity:
            result['rarity'] = rarity
            result['confidence'] += 0.1
        
        # Strategy 5: Extract edition
        edition = self._extract_edition(japanese_title)
        if edition:
            result['edition'] = edition
            result['confidence'] += 0.1
        
        # Strategy 6: Extract condition
        condition = self._extract_condition(japanese_title)
        if condition:
            result['condition'] = condition
            result['confidence'] += 0.1
        
        # Strategy 7: Extract region
        region = self._extract_region(japanese_title)
        if region:
            result['region'] = region
            result['confidence'] += 0.1
        
        # Generate search queries
        result['search_queries'] = self._generate_search_queries(result)
        
        return result
    
    def _apply_direct_translations(self, text: str) -> str:
        """Apply direct translations from dictionary."""
        translated = text
        
        for jp_term, en_term in self.card_translations.items():
            if jp_term in text:
                translated = translated.replace(jp_term, en_term)
        
        return translated
    
    def _extract_card_name(self, title: str) -> Optional[str]:
        """Extract card name from title."""
        # Try to find the main card name
        for pattern in self.card_patterns:
            matches = re.findall(pattern, title)
            if matches:
                # Take the longest match as the card name
                card_name = max(matches, key=len).strip()
                if len(card_name) > 2:  # Filter out very short matches
                    return card_name
        
        return None
    
    def _extract_set_info(self, title: str) -> Optional[Tuple[str, str]]:
        """Extract set code and card number."""
        for pattern in self.set_patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1), match.group(2)
        
        return None
    
    def _extract_rarity(self, title: str) -> Optional[str]:
        """Extract rarity information."""
        rarity_terms = [
            'ウルトラレア', 'スーパーレア', 'シークレット', 'アルティメットレア',
            'ゴーストレア', 'プラチナレア', 'ゴールドレア', 'パラレルレア',
            'コレクターズレア', 'クォーターセンチュリー', 'ホロ'
        ]
        
        for term in rarity_terms:
            if term in title:
                return self.card_translations.get(term, term)
        
        return None
    
    def _extract_edition(self, title: str) -> Optional[str]:
        """Extract edition information."""
        edition_terms = ['1st', '初版', '無制限', '再版']
        
        for term in edition_terms:
            if term in title:
                return self.card_translations.get(term, term)
        
        return None
    
    def _extract_condition(self, title: str) -> Optional[str]:
        """Extract condition information."""
        condition_terms = [
            'ミント', 'ニアミント', 'エクセレント', 'グッド',
            'ライトプレイ', 'プレイ', 'プア', '未使用', '新品同様',
            '美品', '良品', '軽度使用', '使用済み', '傷あり'
        ]
        
        for term in condition_terms:
            if term in title:
                return self.card_translations.get(term, term)
        
        return None
    
    def _extract_region(self, title: str) -> Optional[str]:
        """Extract region/language information."""
        region_terms = ['アジア', 'アジア版', '英', '英語版', '日', '日本語版', '韓', '韓国版']
        
        for term in region_terms:
            if term in title:
                return self.card_translations.get(term, term)
        
        return None
    
    def _generate_search_queries(self, result: Dict[str, any]) -> List[str]:
        """Generate multiple search queries for eBay."""
        queries = []
        
        # Query 1: Original Japanese title
        queries.append(result['original'])
        
        # Query 2: Translated title
        if result['translated'] != result['original']:
            queries.append(result['translated'])
        
        # Query 3: Card name + Yu-Gi-Oh
        if result['card_name']:
            queries.append(f"Yu-Gi-Oh {result['card_name']}")
            queries.append(f"Yu-Gi-Oh card {result['card_name']}")
        
        # Query 4: Card name + set code
        if result['card_name'] and result['set_code']:
            queries.append(f"Yu-Gi-Oh {result['card_name']} {result['set_code']}")
        
        # Query 5: Card name + rarity
        if result['card_name'] and result['rarity']:
            queries.append(f"Yu-Gi-Oh {result['card_name']} {result['rarity']}")
        
        # Query 6: Set code + card number
        if result['set_code'] and result['card_number']:
            queries.append(f"Yu-Gi-Oh {result['set_code']} {result['card_number']}")
        
        # Query 7: Generic Yu-Gi-Oh search with key terms
        key_terms = []
        if result['rarity']:
            key_terms.append(result['rarity'])
        if result['edition']:
            key_terms.append(result['edition'])
        if result['condition']:
            key_terms.append(result['condition'])
        
        if key_terms:
            queries.append(f"Yu-Gi-Oh {' '.join(key_terms)}")
        
        # Remove duplicates and empty strings
        unique_queries = list(set([q.strip() for q in queries if q.strip()]))
        
        return unique_queries
    
    def translate_for_ebay_search(self, japanese_title: str) -> List[str]:
        """
        Generate eBay search queries for Japanese card title.
        
        Args:
            japanese_title: Japanese card title
            
        Returns:
            List of search queries to try
        """
        translation_result = self.translate_card_title(japanese_title)
        return translation_result['search_queries']
    
    def get_english_card_name(self, japanese_title: str) -> Optional[str]:
        """
        Get English card name from Japanese title.
        
        Args:
            japanese_title: Japanese card title
            
        Returns:
            English card name or None
        """
        translation_result = self.translate_card_title(japanese_title)
        return translation_result['card_name']
    
    def get_set_info(self, japanese_title: str) -> Optional[Tuple[str, str]]:
        """
        Get set code and card number from Japanese title.
        
        Args:
            japanese_title: Japanese card title
            
        Returns:
            Tuple of (set_code, card_number) or None
        """
        translation_result = self.translate_card_title(japanese_title)
        if translation_result['set_code'] and translation_result['card_number']:
            return (translation_result['set_code'], translation_result['card_number'])
        return None


# Example usage
if __name__ == "__main__":
    translator = CardTranslator()
    
    # Test cases
    test_cases = [
        "ブラック・マジシャン ウルトラレア 1st",
        "青眼の白龍 スーパーレア 初版",
        "遊戯王 英語　ホロ　ブラックマジシャン",
        "魔術師の弟子－ブラック・マジシャン・ガール",
        "アマダ 遊戯王",
        "LOB-001 ブラック・マジシャン ウルトラレア",
        "MRD-060 青眼の白龍 スーパーレア ミント"
    ]
    
    for test_case in test_cases:
        print(f"\nOriginal: {test_case}")
        result = translator.translate_card_title(test_case)
        print(f"Translated: {result['translated']}")
        print(f"Card Name: {result['card_name']}")
        print(f"Set Code: {result['set_code']}")
        print(f"Card Number: {result['card_number']}")
        print(f"Rarity: {result['rarity']}")
        print(f"Edition: {result['edition']}")
        print(f"Condition: {result['condition']}")
        print(f"Search Queries: {result['search_queries']}")
        print(f"Confidence: {result['confidence']}") 