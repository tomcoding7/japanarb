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

logger = logging.getLogger(__name__)

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
            for item in root.findall('.//{http://www.ebay.com/marketplace/search/v1/services}item'):
                item_data = self._parse_item_xml(item)
                if item_data:
                    items.append(item_data)
            
            logger.info(f"Finding API found {len(items)} items for query: {query}")
            return items
            
        except Exception as e:
            logger.warning(f"Finding API failed: {str(e)}")
            return []
    
    def _search_shopping_api(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Shopping API as fallback."""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Use Shopping API to search for items
            params = {
                'callname': 'FindItems',
                'responseformat': 'JSON',
                'keywords': query,
                'categoryId': '31388',  # Trading Cards
                'sortOrder': 'EndTimeSoonest',
                'paginationInput.entriesPerPage': max_results,
                'paginationInput.pageNumber': '1',
                'itemFilter(0).name': 'SoldItemsOnly',
                'itemFilter(0).value': 'true'
            }
            
            response = requests.get(self.shopping_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            items = []
            
            if 'findItemsAdvancedResponse' in data:
                search_result = data['findItemsAdvancedResponse'][0]
                if 'searchResult' in search_result and search_result['searchResult']:
                    for item in search_result['searchResult'][0].get('item', []):
                        item_data = {
                            'item_id': item.get('itemId', ''),
                            'title': item.get('title', ''),
                            'price': Decimal(item.get('sellingStatus', [{}])[0].get('currentPrice', [{}])[0].get('__value__', '0')),
                            'condition': item.get('condition', [{}])[0].get('conditionDisplayName', 'Unknown'),
                            'end_time': item.get('listingInfo', [{}])[0].get('endTime', ''),
                            'currency': 'USD'
                        }
                        items.append(item_data)
            
            logger.info(f"Shopping API found {len(items)} items for query: {query}")
            return items
            
        except Exception as e:
            logger.warning(f"Shopping API failed: {str(e)}")
            return []
    
    def _parse_item_xml(self, item_elem) -> Optional[Dict[str, Any]]:
        """Parse individual item XML element."""
        try:
            namespace = '{http://www.ebay.com/marketplace/search/v1/services}'
            
            item_id = item_elem.find(f'{namespace}itemId')
            title = item_elem.find(f'{namespace}title')
            current_price = item_elem.find(f'{namespace}sellingStatus/{namespace}currentPrice')
            condition = item_elem.find(f'{namespace}condition/{namespace}conditionDisplayName')
            end_time = item_elem.find(f'{namespace}listingInfo/{namespace}endTime')
            
            if not item_id or not current_price:
                return None
            
            return {
                'item_id': item_id.text,
                'title': title.text if title is not None else '',
                'price': Decimal(current_price.text),
                'condition': condition.text if condition is not None else 'Unknown',
                'end_time': end_time.text if end_time is not None else '',
                'currency': current_price.get('currencyId', 'USD')
            }
            
        except Exception as e:
            logger.debug(f"Error parsing item XML: {str(e)}")
            return None
    
    def get_item_details(self, item_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get detailed information for specific items using Shopping API.
        
        Args:
            item_ids: List of eBay item IDs
            
        Returns:
            List of detailed item information
        """
        if not self.authenticate():
            return []
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/xml'
            }
            
            # Build XML request
            item_ids_str = ','.join(item_ids)
            xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<GetMultipleItemsRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <ItemID>{item_ids_str}</ItemID>
    <DetailLevel>ReturnAll</DetailLevel>
</GetMultipleItemsRequest>"""
            
            response = requests.post(self.shopping_url, headers=headers, data=xml_request)
            response.raise_for_status()
            
            # Parse response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            items = []
            for item in root.findall('.//{urn:ebay:apis:eBLBaseComponents}Item'):
                item_data = self._parse_detail_xml(item)
                if item_data:
                    items.append(item_data)
            
            return items
            
        except Exception as e:
            logger.error(f"Failed to get item details: {str(e)}")
            return []
    
    def _parse_detail_xml(self, item_elem) -> Optional[Dict[str, Any]]:
        """Parse detailed item XML element."""
        try:
            namespace = '{urn:ebay:apis:eBLBaseComponents}'
            
            item_id = item_elem.find(f'{namespace}ItemID')
            title = item_elem.find(f'{namespace}Title')
            condition = item_elem.find(f'{namespace}ConditionDisplayName')
            price = item_elem.find(f'{namespace}ConvertedCurrentPrice')
            
            if not item_id:
                return None
            
            return {
                'item_id': item_id.text,
                'title': title.text if title is not None else '',
                'condition': condition.text if condition is not None else 'Unknown',
                'price': Decimal(price.text) if price is not None else Decimal('0'),
                'currency': price.get('currencyID', 'USD') if price is not None else 'USD'
            }
            
        except Exception as e:
            logger.debug(f"Error parsing detail XML: {str(e)}")
            return None
    
    def get_card_prices(self, card_name: str, set_code: Optional[str] = None) -> Dict[str, List[Decimal]]:
        """
        Get eBay sold prices for a Yu-Gi-Oh! card.
        
        Args:
            card_name: Name of the card
            set_code: Optional set code (e.g., "LOB", "MRD")
            
        Returns:
            Dictionary with 'raw' and 'psa' price lists
        """
        # Build search query
        search_query = card_name
        if set_code:
            search_query += f" {set_code}"
        
        # Add Yu-Gi-Oh! context
        search_query += " Yu-Gi-Oh!"
        
        # Search for sold items
        sold_items = self.search_sold_items(search_query, max_results=100)
        
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
        
        # Test search
        results = ebay.search_sold_items("Blue-Eyes White Dragon", max_results=5)
        print(f"Found {len(results)} sold items")
        
        for item in results:
            print(f"- {item['title']}: ${item['price']} ({item['condition']})")
    else:
        print("❌ eBay API authentication failed") 