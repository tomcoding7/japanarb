"""
eBay API Integration for Japan Auction Arbitrage Bot

This module provides integration with the eBay Finding API and Shopping API
to fetch sold listings and pricing data for Yu-Gi-Oh! cards.
"""

import os
import logging
import requests
import json
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta
import time
import re

logger = logging.getLogger(__name__)

# Comprehensive card name translations
CARD_TRANSLATIONS = {
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
    "アマダ": "Amada",
    "遊戯王": "Yu-Gi-Oh",
    "ホロ": "holographic",
    "ウルトラレア": "Ultra Rare",
    "スーパーレア": "Super Rare", 
    "シークレット": "Secret Rare",
    "1st": "1st Edition",
    "初版": "1st Edition",
    "無制限": "Unlimited",
    "ミント": "Mint",
    "ニアミント": "Near Mint",
    "エクセレント": "Excellent",
    "グッド": "Good",
    "ライトプレイ": "Light Played",
    "プレイ": "Played",
    "プア": "Poor"
}

class EbayAPI:
    """eBay API integration for fetching sold listings and pricing data."""
    
    def __init__(self):
        """Initialize eBay API with credentials from environment variables."""
        self.environment = os.getenv('EBAY_ENVIRONMENT', 'sandbox')
        
        # Load credentials based on environment
        if self.environment == 'production':
            self.client_id = os.getenv('EBAY_CLIENT_ID')
            self.client_secret = os.getenv('EBAY_CLIENT_SECRET')
            self.dev_id = os.getenv('EBAY_DEV_ID')
            self.base_url = 'https://api.ebay.com'
            self.browse_url = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
            self.finding_url = 'https://svcs.ebay.com/services/search/FindingService/v1'
            self.shopping_url = 'https://open.api.ebay.com/shopping'
        else:
            # Use sandbox credentials
            self.client_id = os.getenv('EBAY_SANDBOX_CLIENT_ID')
            self.client_secret = os.getenv('EBAY_SANDBOX_CLIENT_SECRET')
            self.dev_id = os.getenv('EBAY_SANDBOX_DEV_ID')
            self.base_url = 'https://api.sandbox.ebay.com'
            self.browse_url = 'https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search'
            self.finding_url = 'https://svcs.sandbox.ebay.com/services/search/FindingService/v1'
            self.shopping_url = 'https://open.api.sandbox.ebay.com/shopping'
        
        self.redirect_uri = os.getenv('EBAY_REDIRECT_URI')
        self.access_token = None
        self.token_expires = None
        
        # Validate credentials
        if not all([self.client_id, self.client_secret, self.dev_id]):
            logger.warning(f"eBay API credentials not fully configured for {self.environment} environment. Some features may be limited.")
            logger.warning(f"Missing credentials for environment: {self.environment}")
            if self.environment == 'sandbox':
                logger.warning("Make sure EBAY_SANDBOX_CLIENT_ID, EBAY_SANDBOX_CLIENT_SECRET, and EBAY_SANDBOX_DEV_ID are set")
            else:
                logger.warning("Make sure EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, and EBAY_DEV_ID are set")
    
    def smart_translate_for_ebay(self, japanese_title: str) -> List[str]:
        """
        Create multiple search strategies for Japanese card titles.
        
        Args:
            japanese_title: Japanese card title
            
        Returns:
            List of search queries to try
        """
        search_queries = []
        
        # Strategy 1: Direct Japanese search
        search_queries.append(japanese_title)
        
        # Strategy 2: English translation search
        english_title = self._translate_card_name(japanese_title)
        if english_title != japanese_title:
            search_queries.append(english_title)
            search_queries.append(f"Yu-Gi-Oh {english_title}")
        
        # Strategy 3: Card name extraction + "Yu-Gi-Oh"
        card_name = self._extract_card_name(japanese_title)
        if card_name:
            search_queries.append(f"Yu-Gi-Oh {card_name}")
            search_queries.append(f"Yu-Gi-Oh card {card_name}")
        
        # Strategy 4: Set codes and rarity search
        set_info = self._extract_set_info(japanese_title)
        if set_info:
            search_queries.append(f"Yu-Gi-Oh {set_info}")
        
        # Strategy 5: Generic Yu-Gi-Oh search with key terms
        key_terms = self._extract_key_terms(japanese_title)
        if key_terms:
            search_queries.append(f"Yu-Gi-Oh {' '.join(key_terms)}")
        
        # Remove duplicates and empty strings
        search_queries = list(set([q.strip() for q in search_queries if q.strip()]))
        
        logger.info(f"Generated {len(search_queries)} search queries for: {japanese_title}")
        for i, query in enumerate(search_queries):
            logger.debug(f"  Query {i+1}: {query}")
        
        return search_queries
    
    def _translate_card_name(self, japanese_title: str) -> str:
        """Translate Japanese card name to English using dictionary."""
        translated = japanese_title
        
        # Apply direct translations
        for jp_name, en_name in CARD_TRANSLATIONS.items():
            if jp_name in japanese_title:
                translated = translated.replace(jp_name, en_name)
        
        return translated
    
    def _extract_card_name(self, title: str) -> Optional[str]:
        """Extract card name from title."""
        # Look for common card name patterns
        card_patterns = [
            r'([A-Za-z\s]+)(?:\s*[-・]\s*[A-Za-z\s]+)*',  # English card names
            r'([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+)',  # Japanese characters
        ]
        
        for pattern in card_patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_set_info(self, title: str) -> Optional[str]:
        """Extract set information from title."""
        # Look for set codes like LOB, MRD, etc.
        set_pattern = r'([A-Z]{2,4})[-・]?(\d{3})'
        match = re.search(set_pattern, title)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        return None
    
    def _extract_key_terms(self, title: str) -> List[str]:
        """Extract key terms for search."""
        terms = []
        
        # Extract rarity terms
        rarity_terms = ['ウルトラレア', 'スーパーレア', 'シークレット', 'ホロ', '1st', '初版']
        for term in rarity_terms:
            if term in title:
                terms.append(CARD_TRANSLATIONS.get(term, term))
        
        # Extract condition terms
        condition_terms = ['ミント', 'ニアミント', 'エクセレント', 'グッド']
        for term in condition_terms:
            if term in title:
                terms.append(CARD_TRANSLATIONS.get(term, term))
        
        return terms

    def authenticate(self) -> bool:
        """Authenticate with eBay API using Client Credentials flow."""
        try:
            if not self.client_id or not self.client_secret:
                logger.error("eBay API credentials not configured")
                return False
            
            # Check if we have a valid token
            if self.access_token and self.token_expires and datetime.now() < self.token_expires:
                return True
            
            # Get new access token
            auth_url = f"{self.base_url}/identity/v1/oauth2/token"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {self._get_basic_auth()}'
            }
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope'
            }
            
            response = requests.post(auth_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'] - 300)  # 5 min buffer
            
            logger.info("Successfully authenticated with eBay API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with eBay API: {str(e)}")
            return False
    
    def _get_basic_auth(self) -> str:
        """Get Basic Auth header for eBay API."""
        import base64
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    def search_sold_items_comprehensive(self, japanese_title: str, category_id: str = "31388", max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Comprehensive search for sold items using multiple strategies.
        
        Args:
            japanese_title: Japanese card title
            category_id: eBay category ID (31388 = Trading Cards)
            max_results: Maximum number of results to return
            
        Returns:
            List of sold item data
        """
        if not self.authenticate():
            logger.error("eBay API authentication failed")
            return []
        
        all_items = []
        search_queries = self.smart_translate_for_ebay(japanese_title)
        
        for query in search_queries:
            try:
                logger.info(f"Searching eBay with query: {query}")
                
                # Try Browse API first
                items = self._search_browse_api(query, category_id, max_results)
                
                # If Browse API fails, try Finding API as fallback
                if not items:
                    logger.info(f"Browse API failed for '{query}', trying Finding API fallback")
                    items = self._search_finding_api(query, category_id, max_results)
                
                # If both APIs fail, try web scraping fallback
                if not items:
                    logger.info(f"Both APIs failed for '{query}', trying web scraping fallback")
                    items = self._search_web_scraping(query, max_results)
                
                all_items.extend(items)
                
                # Add delay to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error searching with query '{query}': {str(e)}")
                continue
        
        # Remove duplicates based on item_id
        unique_items = {}
        for item in all_items:
            item_id = item.get('item_id', '')
            if item_id and item_id not in unique_items:
                unique_items[item_id] = item
        
        final_items = list(unique_items.values())
        logger.info(f"Found {len(final_items)} unique sold items for '{japanese_title}'")
        
        return final_items

    def search_sold_items(self, query: str, category_id: str = "31388", max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for sold items using eBay Browse API with fallback to Finding API.
        
        Args:
            query: Search query (card name)
            category_id: eBay category ID (31388 = Trading Cards)
            max_results: Maximum number of results to return
            
        Returns:
            List of sold item data
        """
        if not self.authenticate():
            return []
        
        # Try Browse API first (newer, more reliable)
        items = self._search_browse_api(query, category_id, max_results)
        
        # If Browse API fails, try Finding API as fallback
        if not items:
            logger.info("Browse API failed, trying Finding API fallback")
            items = self._search_finding_api(query, category_id, max_results)
        
        return items
    
    def _search_browse_api(self, query: str, category_id: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Browse API (newer, more reliable)."""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-EBAY-C-MARKETPLACE-ID': 'EBAY-US'
            }
            
            # Build search parameters for Browse API
            params = {
                'q': query,
                'limit': str(max_results),
                'filter': 'soldItems'
            }
            
            response = requests.get(self.browse_url, headers=headers, params=params)
            response.raise_for_status()
            
            # Log response for debugging
            logger.debug(f"Browse API Response Status: {response.status_code}")
            logger.debug(f"Browse API Response Headers: {dict(response.headers)}")
            logger.debug(f"Browse API Response Body: {response.text[:1000]}")
            
            data = response.json()
            items = []
            
            if 'itemSummaries' in data:
                for item in data['itemSummaries']:
                    item_data = {
                        'item_id': item.get('itemId', ''),
                        'title': item.get('title', ''),
                        'price': Decimal(item.get('price', {}).get('value', '0')),
                        'condition': item.get('condition', 'Unknown'),
                        'end_time': item.get('itemEndDate', ''),
                        'currency': item.get('price', {}).get('currency', 'USD')
                    }
                    items.append(item_data)
            
            logger.info(f"Browse API found {len(items)} items for query: {query}")
            return items
            
        except Exception as e:
            logger.warning(f"Browse API failed: {str(e)}")
            return []
    
    def _search_finding_api(self, query: str, category_id: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Finding API."""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/xml'
            }
            
            xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<findCompletedItemsRequest xmlns="http://www.ebay.com/marketplace/search/v1/services">
    <keywords>{query}</keywords>
    <categoryId>{category_id}</categoryId>
    <sortOrder>EndTimeSoonest</sortOrder>
    <paginationInput>
        <entriesPerPage>{max_results}</entriesPerPage>
        <pageNumber>1</pageNumber>
    </paginationInput>
    <itemFilter>
        <name>SoldItemsOnly</name>
        <value>true</value>
    </itemFilter>
</findCompletedItemsRequest>"""
            
            response = requests.post(self.finding_url, headers=headers, data=xml_request)
            response.raise_for_status()
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            items = []
            
            # Parse XML response
            for item_elem in root.findall('.//{http://www.ebay.com/marketplace/search/v1/services}item'):
                item_data = self._parse_item_xml(item_elem)
                if item_data:
                    items.append(item_data)
            
            logger.info(f"Finding API found {len(items)} items for query: {query}")
            return items
            
        except Exception as e:
            logger.warning(f"Finding API failed: {str(e)}")
            return []
    
    def _search_web_scraping(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback web scraping method for eBay searches."""
        try:
            from urllib.parse import quote
            from bs4 import BeautifulSoup
            
            # Construct eBay search URL
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={quote(query)}&_sacat=0&LH_Sold=1&LH_Complete=1"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            items = []
            
            # Find all sold items
            item_elements = soup.find_all('div', class_='s-item__info')
            
            for item_elem in item_elements[:max_results]:
                try:
                    # Extract price
                    price_elem = item_elem.find('span', class_='s-item__price')
                    if not price_elem:
                        continue
                    
                    price_text = price_elem.text.strip()
                    price_match = re.search(r'[\d,]+\.?\d*', price_text)
                    if not price_match:
                        continue
                    
                    price = Decimal(price_match.group().replace(',', ''))
                    
                    # Extract title
                    title_elem = item_elem.find('div', class_='s-item__title')
                    title = title_elem.text.strip() if title_elem else "Unknown"
                    
                    # Extract item ID
                    item_id = ""
                    link_elem = item_elem.find('a', class_='s-item__link')
                    if link_elem and 'href' in link_elem.attrs:
                        href = link_elem['href']
                        id_match = re.search(r'/itm/(\d+)', href)
                        if id_match:
                            item_id = id_match.group(1)
                    
                    item_data = {
                        'item_id': item_id,
                        'title': title,
                        'price': price,
                        'condition': 'Unknown',
                        'end_time': '',
                        'currency': 'USD'
                    }
                    
                    items.append(item_data)
                    
                except Exception as e:
                    logger.debug(f"Error parsing eBay item: {str(e)}")
                    continue
            
            logger.info(f"Web scraping found {len(items)} items for query: {query}")
            return items
            
        except Exception as e:
            logger.warning(f"Web scraping failed: {str(e)}")
            return []

    def _search_shopping_api(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Shopping API."""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/xml'
            }
            
            xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<findItemsAdvancedRequest xmlns="http://www.ebay.com/marketplace/search/v1/services">
    <keywords>{query}</keywords>
    <sortOrder>EndTimeSoonest</sortOrder>
    <paginationInput>
        <entriesPerPage>{max_results}</entriesPerPage>
        <pageNumber>1</pageNumber>
    </paginationInput>
    <itemFilter>
        <name>SoldItemsOnly</name>
        <value>true</value>
    </itemFilter>
</findItemsAdvancedRequest>"""
            
            response = requests.post(self.shopping_url, headers=headers, data=xml_request)
            response.raise_for_status()
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            items = []
            
            # Parse XML response
            for item_elem in root.findall('.//{http://www.ebay.com/marketplace/search/v1/services}item'):
                item_data = self._parse_item_xml(item_elem)
                if item_data:
                    items.append(item_data)
            
            return items
            
        except Exception as e:
            logger.warning(f"Shopping API failed: {str(e)}")
            return []
    
    def _parse_item_xml(self, item_elem) -> Optional[Dict[str, Any]]:
        """Parse item XML element from eBay API response."""
        try:
            item_id = item_elem.find('.//itemId')
            title = item_elem.find('.//title')
            price = item_elem.find('.//sellingStatus//currentPrice')
            condition = item_elem.find('.//condition')
            end_time = item_elem.find('.//listingInfo//endTime')
            
            if not item_id or not title or not price:
                return None
            
            return {
                'item_id': item_id.text,
                'title': title.text,
                'price': Decimal(price.text),
                'condition': condition.text if condition else 'Unknown',
                'end_time': end_time.text if end_time else '',
                'currency': price.get('currencyId', 'USD')
            }
            
        except Exception as e:
            logger.debug(f"Error parsing item XML: {str(e)}")
            return None
    
    def get_item_details(self, item_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed information for specific items."""
        if not self.authenticate():
            return []
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/xml'
            }
            
            # Build XML request for multiple items
            items_xml = ''.join([f'<itemId>{item_id}</itemId>' for item_id in item_ids])
            xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<getMultipleItemsRequest xmlns="http://www.ebay.com/marketplace/search/v1/services">
    <itemId>{items_xml}</itemId>
    <includeSelector>Details</includeSelector>
</getMultipleItemsRequest>"""
            
            response = requests.post(self.shopping_url, headers=headers, data=xml_request)
            response.raise_for_status()
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            items = []
            
            # Parse XML response
            for item_elem in root.findall('.//{http://www.ebay.com/marketplace/search/v1/services}item'):
                item_data = self._parse_detail_xml(item_elem)
                if item_data:
                    items.append(item_data)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting item details: {str(e)}")
            return []
    
    def _parse_detail_xml(self, item_elem) -> Optional[Dict[str, Any]]:
        """Parse detailed item XML element."""
        try:
            item_id = item_elem.find('.//itemId')
            title = item_elem.find('.//title')
            price = item_elem.find('.//currentPrice')
            condition = item_elem.find('.//condition')
            description = item_elem.find('.//description')
            
            if not item_id or not title:
                return None
            
            return {
                'item_id': item_id.text,
                'title': title.text,
                'price': Decimal(price.text) if price else Decimal('0'),
                'condition': condition.text if condition else 'Unknown',
                'description': description.text if description else '',
                'currency': price.get('currencyId', 'USD') if price else 'USD'
            }
            
        except Exception as e:
            logger.debug(f"Error parsing detail XML: {str(e)}")
            return None
    
    def get_card_prices(self, card_name: str, set_code: Optional[str] = None) -> Dict[str, List[Decimal]]:
        """
        Get eBay sold prices for a Yu-Gi-Oh! card using comprehensive search.
        
        Args:
            card_name: Name of the card (can be Japanese)
            set_code: Optional set code (e.g., "LOB", "MRD")
            
        Returns:
            Dictionary with 'raw' and 'psa' price lists
        """
        # Use comprehensive search for Japanese card names
        sold_items = self.search_sold_items_comprehensive(card_name, max_results=100)
        
        raw_prices = []
        psa_prices = []
        
        for item in sold_items:
            price = item['price']
            title = item['title'].lower()
            condition = item['condition'].lower()
            
            # Categorize by condition
            if 'psa' in title or 'graded' in title or 'psa' in condition:
                psa_prices.append(price)
            else:
                raw_prices.append(price)
        
        logger.info(f"Found {len(raw_prices)} raw and {len(psa_prices)} PSA prices for {card_name}")
        
        return {
            'raw': raw_prices,
            'psa': psa_prices
        }
    
    def get_market_data(self, card_name: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive market data for a card.
        
        Args:
            card_name: Name of the card
            days_back: Number of days to look back
            
        Returns:
            Market data including averages, trends, etc.
        """
        prices = self.get_card_prices(card_name)
        
        raw_prices = prices['raw']
        psa_prices = prices['psa']
        
        # Calculate statistics
        avg_raw = sum(raw_prices) / len(raw_prices) if raw_prices else 0
        avg_psa = sum(psa_prices) / len(psa_prices) if psa_prices else 0
        
        min_raw = min(raw_prices) if raw_prices else 0
        max_raw = max(raw_prices) if raw_prices else 0
        
        min_psa = min(psa_prices) if psa_prices else 0
        max_psa = max(psa_prices) if psa_prices else 0
        
        return {
            'card_name': card_name,
            'raw_prices': raw_prices,
            'psa_prices': psa_prices,
            'avg_raw': avg_raw,
            'avg_psa': avg_psa,
            'min_raw': min_raw,
            'max_raw': max_raw,
            'min_psa': min_psa,
            'max_psa': max_psa,
            'total_listings': len(raw_prices) + len(psa_prices),
            'raw_count': len(raw_prices),
            'psa_count': len(psa_prices)
        }


# Example usage
if __name__ == "__main__":
    # Test the eBay API integration
    ebay = EbayAPI()
    
    # Test authentication
    if ebay.authenticate():
        print("✅ eBay API authentication successful")
        
        # Test comprehensive search
        results = ebay.search_sold_items_comprehensive("ブラック・マジシャン", max_results=5)
        print(f"Found {len(results)} sold items")
        
        for item in results:
            print(f"- {item['title']}: ${item['price']} ({item['condition']})")
    else:
        print("❌ eBay API authentication failed") 