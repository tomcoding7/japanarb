import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote
import statistics
import re
import os
import google.generativeai as genai
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RequestHandler:
    """Handles HTTP requests with retry logic and bot detection."""
    
    def __init__(self):
        """Initialize the RequestHandler with default headers and retry settings."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        })
        self.retry_delays = [1, 2, 5, 10, 30]  # Exponential backoff delays
        self.max_retries = 3
        self.timeout = 10
        
    def get_page(self, url: str, max_retries: int = None, timeout: int = None) -> Optional[str]:
        """
        Make a request with retry logic and bot detection.
        
        Args:
            url (str): URL to fetch
            max_retries (int): Maximum number of retries
            timeout (int): Request timeout in seconds
            
        Returns:
            Optional[str]: Page content or None if failed
        """
        retries = max_retries if max_retries is not None else self.max_retries
        timeout = timeout if timeout is not None else self.timeout
        
        for retry in range(retries):
            try:
                # Add random delay between requests
                time.sleep(random.uniform(3, 7))
                
                # Make request with timeout
                response = self.session.get(url, timeout=timeout)
                
                # Handle common error cases
                if response.status_code == 404:
                    logger.warning(f"Item not found (404): {url}")
                    return None
                
                if response.status_code in [403, 429]:
                    logger.warning(f"Bot detection triggered (HTTP {response.status_code})")
                    if retry < retries - 1:
                        delay = self.retry_delays[min(retry, len(self.retry_delays) - 1)]
                        logger.info(f"Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                        continue
                    return None
                
                # Check for Japanese-specific error messages
                if 'このサービスは日本国内からのみご利用いただけます' in response.text:
                    logger.error("Access denied. This service is only available from Japan.")
                    return None
                
                if 'アクセスが集中' in response.text or '一時的なアクセス制限' in response.text:
                    logger.warning("Bot challenge page detected")
                    if retry < retries - 1:
                        delay = self.retry_delays[min(retry, len(self.retry_delays) - 1)]
                        logger.info(f"Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                        continue
                    return None
                
                # Raise for any other HTTP errors
                response.raise_for_status()
                
                # Log successful request
                logger.info(f"Successfully fetched page: {url}")
                return response.text
                
            except requests.RequestException as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                if retry < retries - 1:
                    delay = self.retry_delays[min(retry, len(self.retry_delays) - 1)]
                    logger.info(f"Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                else:
                    logger.error("Max retries reached")
                    return None
        return None

class CardInfoExtractor:
    """Extracts and normalizes card information from titles."""
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = False  # Always disable LLM/AI
        
        # Common set codes and their full names
        self.set_patterns = {
            'SDK': 'Starter Deck Kaiba',
            'LOB': 'Legend of Blue Eyes White Dragon',
            'MRD': 'Metal Raiders',
            'SRL': 'Starter Deck Yugi',
            'PSV': 'Pharaoh\'s Servant',
        }
        # Expanded translation mapping for common Yu-Gi-Oh cards
        self.jp_to_en = {
            "青眼の白龍": "Blue-Eyes White Dragon",
            "ブルーアイズホワイトドラゴン": "Blue-Eyes White Dragon",
            "ブラック・マジシャン": "Dark Magician",
            "真紅眼の黒竜": "Red-Eyes Black Dragon",
            "レッドアイズ・ブラック・ドラゴン": "Red-Eyes Black Dragon",
            "カオス・ソルジャー": "Black Luster Soldier",
            "エクゾディア": "Exodia",
            "サイバー・ドラゴン": "Cyber Dragon",
            "E・HERO ネオス": "Elemental HERO Neos",
            "スターダスト・ドラゴン": "Stardust Dragon",
            "ブラックローズ・ドラゴン": "Black Rose Dragon",
            "混沌の黒魔術師": "Dark Magician of Chaos",
            # Add more as needed
        }
    
    def translate_to_english(self, japanese_text: str) -> str:
        # Use mapping for common cards, fallback to original text
        for jp, en in self.jp_to_en.items():
            if jp in japanese_text:
                return en
        return japanese_text
    
    def extract_card_info(self, title: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Extract card name, set code, and region from title."""
        try:
            set_code = None
            for code in self.set_patterns.keys():
                if code in title.upper():
                    set_code = code
                    break
            card_name = title
            common_words = [
                '遊戯王', 'Yu-Gi-Oh', 'カード', 'card', '1st', 'edition', 'limited',
                'まとめ', 'レア', 'rare', 'セット', 'set', 'パック', 'pack',
                '新品', '未使用', '中古', '使用済み', 'プレイ済み'
            ]
            for word in common_words:
                card_name = card_name.replace(word, '').strip()
            if set_code:
                card_name = card_name.replace(set_code, '').strip()
            card_name = re.sub(r'\s*\d+$', '', card_name).strip()
            # Region/language extraction (simple)
            region = None
            if '日本' in title or '日' in title or 'Japanese' in title:
                region = 'Japanese'
            elif '英' in title or 'English' in title:
                region = 'English'
            # Translate if Japanese
            if any(ord(c) > 127 for c in card_name):
                card_name = self.translate_to_english(card_name)
            return card_name, set_code, region
        except Exception as e:
            logger.error(f"Error extracting card info: {str(e)}")
            return None, None, None

class PriceAnalyzer:
    """Analyzes card prices from 130point.com."""
    
    def __init__(self):
        self.request_handler = RequestHandler()
    
    def get_130point_prices(self, card_name: str, set_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get price data from 130point.com using the correct API endpoint. Falls back to Selenium if needed."""
        # Try requests-based method first
        try:
            # Combine card name and set code for search
            search_term = f"{card_name} {set_code}" if set_code else card_name
            
            # API endpoint
            url = "https://back.130point.com/sales/"
            
            # Prepare form data as per the XHR request
            form_data = {
                'query': search_term,
                'type': '2',      # Type 2 seems to be for card searches
                'subcat': '-1'    # -1 for all subcategories
            }
            
            # Headers to match the XHR request
            headers = {
                'Accept': '*/*',
                'Referer': 'https://130point.com/',
                'Origin': 'https://130point.com',
            }
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(2, 4))
            
            # Make POST request
            try:
                # Percent encode form data
                encoded_data = {
                    'query': quote(form_data['query'], safe=''),
                    'type': form_data['type'],
                    'subcat': form_data['subcat']
                }
                
                response = self.request_handler.session.post(
                    url, 
                    data=encoded_data, 
                    headers=headers, 
                    timeout=self.request_handler.timeout,
                )
                response.raise_for_status()
                
                # Since the response is HTML, not JSON, we need to parse it
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract the data from the HTML structure
                data = {'sales': []}
                
                # Look for sale items in the HTML
                sale_items = soup.select('.sale-item') or soup.select('.item') or soup.select('tr#rowsold_dataTable')
                
                for item in sale_items:
                    try:
                        price_elem = item.select_one('.bidLink') or item.select_one('[data-price]')
                        condition_elem = item.select_one('.condition') or item.select_one('.grade')
                        
                        if price_elem:
                            price_text = price_elem.text.strip() if price_elem.text else str(price_elem.get('data-price', ''))
                            condition = condition_elem.text.strip() if condition_elem else ''
                            
                            # Clean the price text to remove currency symbols and text
                            cleaned_price = re.sub(r'[^\d.]', '', price_text).strip()
                            
                            if cleaned_price:  # Only add if we have a valid price
                                data['sales'].append({
                                    'price': cleaned_price,
                                    'condition': condition
                                })
                    except Exception as e:
                        logger.warning(f"Failed to parse HTML item: {str(e)}")
                        continue
                
                logger.info(f"Parsed {len(data['sales'])} items from HTML response")
                
            except requests.RequestException as e:
                logger.error(f"Error making request to 130point API: {str(e)}")
                raise e
                return None
            
            # Parse the JSON response
            raw_prices = []
            psa_9_prices = []
            psa_10_prices = []
            
            # The exact structure depends on the API response format
            # This is a best guess - may need adjustment based on actual response
            sales_data = data.get('sales', []) or data.get('results', []) or data.get('data', [])
            
            if isinstance(sales_data, list):
                for sale in sales_data:
                    try:
                        # Extract price - adjust field names based on actual API response
                        price = None
                        for price_field in ['price', 'sale_price', 'amount', 'cost']:
                            if price_field in sale:
                                price_str = str(sale[price_field])
                                # Remove currency symbols and text, keep only numbers and decimal points
                                price_str = re.sub(r'[^\d.]', '', price_str).strip()
                                if price_str:  # Only try to convert if we have a valid string
                                    price = float(price_str)
                                    break
                        
                        if price is None:
                            continue
                        
                        # Extract condition - adjust field names based on actual API response
                        condition = ''
                        for condition_field in ['condition', 'grade', 'state', 'quality']:
                            if condition_field in sale:
                                condition = str(sale[condition_field]).lower()
                                break
                        
                        # Categorize based on condition
                        if 'psa 10' in condition or 'psa10' in condition:
                            psa_10_prices.append(price)
                        elif 'psa 9' in condition or 'psa9' in condition:
                            psa_9_prices.append(price)
                        else:
                            raw_prices.append(price)
                            
                    except (ValueError, TypeError, KeyError) as e:
                        logger.warning(f"Error parsing sale entry: {str(e)}")
                        continue
            
            logger.info(f"130point search for '{search_term}': found {len(raw_prices)} raw, {len(psa_9_prices)} PSA 9, {len(psa_10_prices)} PSA 10 prices")
            
            # If we got results, return them
            if raw_prices or psa_9_prices or psa_10_prices:
                return {
                    'raw_avg': statistics.mean(raw_prices) if raw_prices else None,
                    'psa_9_avg': statistics.mean(psa_9_prices) if psa_9_prices else None,
                    'psa_10_avg': statistics.mean(psa_10_prices) if psa_10_prices else None,
                    'raw_count': len(raw_prices),
                    'psa_9_count': len(psa_9_prices),
                    'psa_10_count': len(psa_10_prices)
                }
        except Exception as e:
            logger.error(f"Error getting 130point prices (requests): {str(e)}")
            # Continue to Selenium fallback
        # If requests-based failed or returned no results, try Selenium
        return self._get_130point_prices_selenium(card_name, set_code)

    def _get_130point_prices_selenium(self, card_name: str, set_code: Optional[str] = None, headless: bool = True) -> Optional[Dict[str, Any]]:
        """Scrape 130point.com/sales using Selenium to get actual sale prices from the search bar results.
        Uses translated, shortened English search terms for best results.
        """
        try:
            # Use CardInfoExtractor to get best search term
            extractor = CardInfoExtractor()
            # Compose a pseudo-title for extraction
            pseudo_title = card_name
            if set_code:
                pseudo_title += f" {set_code}"
            card_name_en, set_code_extracted, region = extractor.extract_card_info(pseudo_title)
            # Build search term: English card name, set code if present, and 'Japanese' if region is Japanese
            search_term = card_name_en or card_name
            if set_code_extracted:
                search_term += f" {set_code_extracted}"
            if region == 'Japanese':
                search_term += " Japanese"
            # Set up Selenium options
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)
            driver.get("https://130point.com/sales/")
            # Find the search bar and enter the search term
            search_bar = driver.find_element(By.CSS_SELECTOR, 'input[type="text"][name="searchBar"][id="searchBar"]')
            search_bar.send_keys(search_term)
            search_bar.send_keys(Keys.RETURN)
            # Wait for results to load (look for price inputs)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="submit"][value*="USD"], input[type="submit"][value*="GBP"], input[type="submit"][value*="EUR"]'))
            )
            # Extract all price inputs
            price_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="submit"][value]')
            raw_prices = []
            psa_9_prices = []
            psa_10_prices = []
            for inp in price_inputs:
                value = inp.get_attribute('value')
                match = re.match(r'([\d,.]+)\s*([A-Z]{3})', value)
                if match:
                    price = float(match.group(1).replace(',', ''))
                    currency = match.group(2)
                    if currency == 'USD':
                        # Try to categorize by PSA if possible (not always available)
                        # For now, treat all as raw
                        raw_prices.append(price)
            driver.quit()
            logger.info(f"[Selenium] 130point search for '{search_term}': found {len(raw_prices)} USD prices")
            if raw_prices or psa_9_prices or psa_10_prices:
                return {
                    'raw_avg': statistics.mean(raw_prices) if raw_prices else None,
                    'psa_9_avg': statistics.mean(psa_9_prices) if psa_9_prices else None,
                    'psa_10_avg': statistics.mean(psa_10_prices) if psa_10_prices else None,
                    'raw_count': len(raw_prices),
                    'psa_9_count': len(psa_9_prices),
                    'psa_10_count': len(psa_10_prices)
                }
            else:
                return None
        except Exception as e:
            logger.error(f"[Selenium] Error scraping 130point.com/sales: {str(e)}")
            return None

class ConditionAnalyzer:
    """Analyzes card condition from text and images."""
    
    def __init__(self):
        self.japanese_grade_patterns = {
            'SS': r'SSランク|新品未使用|完全美品',
            'S': r'Sランク|未使用.*初期傷.*微妙',
            'A': r'Aランク|未使用.*凹み.*初期傷.*目立つレベルではない',
            'B+': r'B\+ランク|未使用品.*凹み.*初期傷.*目立つ傷',
            'B': r'Bランク|中古品.*使用感あり.*初期傷.*プレイ時の傷',
            'C': r'Cランク|中古品.*使用感あり.*目立つレベルの傷',
            'D': r'Dランク|中古品.*ボロボロ',
            'E': r'Eランク|ジャンク品'
        }
        
        self.condition_terms = {
            'new': [
                '新品', '未使用', 'SSランク', 'Sランク', '完全美品',
                'new', 'mint', 'unused', 'sealed'
            ],
            'used': [
                '中古', '使用済み', '使用感あり', 'プレイ済み',
                'used', 'played', 'second-hand'
            ],
            'damaged': [
                '傷あり', '凹み', '白欠け', 'スレ', '初期傷',
                'damaged', 'scratched', 'dented', 'wear'
            ]
        }
    
    def analyze_condition(self, title: str, description: str, image_analysis: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze the condition of an item based on title, description, and optional image analysis."""
        # Combine title and description for analysis
        full_text = f"{title} {description}"
        
        # Initialize condition info
        condition_info = {
            'is_new': False,
            'is_used': False,
            'is_unopened': False,
            'is_played': False,
            'is_scratched': False,
            'is_damaged': False,
            'condition_notes': [],
            'condition_summary': 'Unknown',
            'damage_flags': [],
            'image_text_discrepancy': False,
            'japanese_grade': None
        }
        
        # Check for Japanese grading system
        for grade, pattern in self.japanese_grade_patterns.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                condition_info['japanese_grade'] = grade
                condition_info['condition_summary'] = f"Grade {grade}"
                
                # Set condition flags based on grade
                if grade in ['SS', 'S']:
                    condition_info['is_new'] = True
                    condition_info['is_unopened'] = True
                elif grade in ['A', 'B+']:
                    condition_info['is_new'] = True
                    condition_info['is_scratched'] = True
                elif grade in ['B', 'C']:
                    condition_info['is_used'] = True
                    condition_info['is_played'] = True
                    condition_info['is_scratched'] = True
                elif grade in ['D', 'E']:
                    condition_info['is_used'] = True
                    condition_info['is_damaged'] = True
                
                break
        
        # If no Japanese grade found, fall back to standard analysis
        if not condition_info['japanese_grade']:
            # Check for condition terms
            for condition_type, terms in self.condition_terms.items():
                for term in terms:
                    if term.lower() in full_text.lower():
                        if condition_type == 'new':
                            condition_info['is_new'] = True
                            condition_info['is_unopened'] = True
                        elif condition_type == 'used':
                            condition_info['is_used'] = True
                            condition_info['is_played'] = True
                        elif condition_type == 'damaged':
                            condition_info['is_damaged'] = True
                            condition_info['is_scratched'] = True
                        
                        condition_info['condition_notes'].append(f"Found {condition_type} indicator: {term}")
            
            # Set condition summary
            if condition_info['is_new']:
                condition_info['condition_summary'] = 'New'
            elif condition_info['is_used']:
                if condition_info['is_damaged']:
                    condition_info['condition_summary'] = 'Used - Damaged'
                elif condition_info['is_scratched']:
                    condition_info['condition_summary'] = 'Used - Scratched'
                else:
                    condition_info['condition_summary'] = 'Used'
        
        # Add image analysis if available
        if image_analysis:
            image_condition = image_analysis.get('condition', {}).get('summary', '').lower()
            
            # Check for discrepancies between text and image analysis
            if condition_info['is_new'] and 'damaged' in image_condition:
                condition_info['image_text_discrepancy'] = True
                condition_info['damage_flags'].append('Image shows damage but listed as new')
            elif condition_info['is_used'] and 'mint' in image_condition:
                condition_info['image_text_discrepancy'] = True
                condition_info['damage_flags'].append('Image shows mint condition but listed as used')
        
        return condition_info 