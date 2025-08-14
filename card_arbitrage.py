import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import requests
from bs4 import BeautifulSoup
# Translation functionality removed - not critical for core functionality
from dotenv import load_dotenv
import re
import time
from dataclasses import dataclass
from decimal import Decimal
import statistics
from urllib.parse import quote

# Import our existing utilities
from scraper_utils import PriceAnalyzer, CardInfoExtractor
from ebay_api import EbayAPI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arbitrage.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@dataclass
class CardListing:
    """Data class to store card listing information."""
    title: str
    title_en: str
    price_yen: Decimal
    price_usd: Decimal
    condition: str
    image_url: str
    listing_url: str
    description: str
    description_en: str
    card_id: Optional[str] = None
    set_code: Optional[str] = None
    ebay_prices: Optional[Dict[str, List[Decimal]]] = None
    point130_prices: Optional[Dict[str, Any]] = None
    potential_profit: Optional[Decimal] = None
    profit_margin: Optional[float] = None
    arbitrage_score: Optional[float] = None
    recommended_action: Optional[str] = None
    screening_score: Optional[int] = None
    screening_reasons: Optional[List[str]] = None

class CardArbitrageTool:
    """Enhanced arbitrage tool that combines Buyee, eBay, and 130point.com data."""

    def __init__(self, output_dir: str = "arbitrage_results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize analyzers
        self.price_analyzer = PriceAnalyzer()
        self.card_extractor = CardInfoExtractor()
        
        # Initialize eBay API
        self.ebay_api = EbayAPI()
        
        # Setup webdriver
        self.driver = None
        self.setup_driver()
        
        # Initialize translator
        # Translation removed for simplicity
        
        # Exchange rate (should be updated regularly)
        self.yen_to_usd = Decimal('0.0067')
        
        # Arbitrage thresholds
        self.min_profit_margin = 30.0  # Minimum 30% profit margin
        self.min_profit_usd = 50.0     # Minimum $50 profit
        self.max_risk_score = 0.7      # Maximum risk score (0-1)

    def setup_driver(self):
        """Setup Chrome driver for Buyee scraping."""
        try:
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript')
            options.add_argument('--headless')  # Run in background
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Use manually specified 64-bit Chrome driver
            service = Service(r'C:/Users/tochs/.wdm/drivers/chromedriver/win64/138.0.7204.94/chromedriver-win64/chromedriver.exe')
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Chrome WebDriver setup complete for Buyee scraping")
            
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {str(e)}")
            self.driver = None
            logger.warning("WebDriver setup failed - scraping will not work")

    def translate_text(self, text: str) -> str:
        """Simple text translation - returns original text for now."""
        # For now, just return the original text
        # Translation can be added later if needed
        return text

    def extract_card_id(self, title: str) -> Optional[str]:
        """Extract card ID from title."""
        # Common patterns for card IDs
        patterns = [
            r'([A-Z]{2,4}-\d{3})',  # Standard format like "LOB-001"
            r'(\d{3})',             # Just the number
            r'No\.(\d+)',           # Japanese format
            r'番号(\d+)'            # Japanese format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1)
        return None

    def get_ebay_prices(self, card_name: str, set_code: Optional[str] = None) -> Dict[str, List[Decimal]]:
        """Get eBay sold prices for a card using the eBay API."""
        try:
            # Use the eBay API to get card prices
            prices = self.ebay_api.get_card_prices(card_name, set_code)
            
            # Log the results
            raw_count = len(prices['raw'])
            psa_count = len(prices['psa'])
            logger.info(f"eBay API found {raw_count} raw and {psa_count} PSA listings for {card_name}")
            
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching eBay prices via API: {str(e)}")
            # Fallback to web scraping if API fails
            return self._get_ebay_prices_fallback(card_name, set_code)
    
    def _get_ebay_prices_fallback(self, card_name: str, set_code: Optional[str] = None) -> Dict[str, List[Decimal]]:
        """Fallback method using web scraping if eBay API fails."""
        try:
            # Construct search term
            search_term = f"{card_name} {set_code}" if set_code else card_name
            search_term = quote(search_term)
            
            # Construct eBay search URL
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={search_term}&_sacat=0&LH_Sold=1&LH_Complete=1"
            
            # Make request with headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch eBay data: {response.status_code}")
                return {'raw': [], 'psa': []}
            
            # Parse the response
            soup = BeautifulSoup(response.text, 'html.parser')
            prices = {'raw': [], 'psa': []}
            
            # Find all sold items
            items = soup.find_all('div', class_='s-item__info')
            for item in items:
                try:
                    # Get price
                    price_elem = item.find('span', class_='s-item__price')
                    if not price_elem:
                        continue
                    
                    price_text = price_elem.text.strip()
                    price = Decimal(re.sub(r'[^\d.]', '', price_text))
                    
                    # Check if it's a PSA graded card
                    title_elem = item.find('div', class_='s-item__title')
                    if title_elem and 'PSA' in title_elem.text:
                        prices['psa'].append(price)
                    else:
                        prices['raw'].append(price)
                        
                except Exception as e:
                    logger.debug(f"Error parsing eBay item: {str(e)}")
                    continue
            
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching eBay prices via fallback: {str(e)}")
            return {'raw': [], 'psa': []}

    def get_130point_prices(self, card_name: str, set_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get price data from 130point.com."""
        try:
            return self.price_analyzer.get_130point_prices(card_name, set_code)
        except Exception as e:
            logger.error(f"Error getting 130point prices: {str(e)}")
            return None

    def calculate_arbitrage_score(self, buyee_price_usd: Decimal, ebay_prices: Dict[str, List[Decimal]], 
                                point130_prices: Optional[Dict[str, Any]], condition: str) -> tuple:
        """Calculate comprehensive arbitrage score and profit potential."""
        try:
            # Calculate average eBay prices
            avg_raw_ebay = statistics.mean(ebay_prices['raw']) if ebay_prices['raw'] else 0
            avg_psa_ebay = statistics.mean(ebay_prices['psa']) if ebay_prices['psa'] else 0
            
            # Get 130point prices
            avg_raw_130 = point130_prices.get('raw_avg', 0) or 0 if point130_prices else 0
            avg_psa_9_130 = point130_prices.get('psa_9_avg', 0) or 0 if point130_prices else 0
            avg_psa_10_130 = point130_prices.get('psa_10_avg', 0) or 0 if point130_prices else 0
            
            assert avg_raw_130 is not None
            assert avg_psa_9_130 is not None
            assert avg_psa_10_130 is not None
            
            # Determine target price based on condition
            target_price = 0
            condition_multiplier = Decimal('1.0')
            
            # Adjust for condition
            if 'new' in condition.lower() or 'mint' in condition.lower():
                condition_multiplier = Decimal('1.0')
            elif 'used' in condition.lower() or 'played' in condition.lower():
                condition_multiplier = Decimal('0.8')
            elif 'damaged' in condition.lower():
                condition_multiplier = Decimal('0.6')
            
            # Use the best available price data
            if avg_psa_10_130 > 0:
                target_price = avg_psa_10_130
            elif avg_psa_9_130 > 0:
                target_price = avg_psa_9_130
            elif avg_raw_130 > 0:
                target_price = avg_raw_130
            elif avg_psa_ebay > 0:
                target_price = avg_psa_ebay
            elif avg_raw_ebay > 0:
                target_price = avg_raw_ebay
            else:
                # No price data available
                return Decimal('0'), 0.0, 0.0, "No price data available"
            
            # Apply condition multiplier
            target_price = Decimal(str(target_price)) * condition_multiplier
            
            # Calculate fees and costs
            ebay_fees = target_price * Decimal('0.15')  # 15% eBay fees
            shipping_cost = Decimal('5.0')  # Estimated shipping
            total_costs = ebay_fees + shipping_cost
            
            # Calculate profit
            profit = target_price - buyee_price_usd - total_costs
            margin = (profit / buyee_price_usd) * 100 if buyee_price_usd > 0 else 0
            
            # Calculate arbitrage score (0-100)
            score = 0.0
            
            # Profit margin component (40% weight)
            if margin >= 50:
                score += 40
            elif margin >= 30:
                score += 30
            elif margin >= 20:
                score += 20
            elif margin >= 10:
                score += 10
            
            # Absolute profit component (30% weight)
            if profit >= 100:
                score += 30
            elif profit >= 50:
                score += 20
            elif profit >= 25:
                score += 10
            
            # Data reliability component (20% weight)
            data_sources = 0
            if ebay_prices['raw'] or ebay_prices['psa']:
                data_sources += 1
            if point130_prices:
                data_sources += 1
            
            if data_sources >= 2:
                score += 20
            elif data_sources == 1:
                score += 10
            
            # Risk assessment component (10% weight)
            risk_score = 0
            if margin < 0:
                risk_score = 10  # High risk
            elif margin < 10:
                risk_score = 5   # Medium risk
            else:
                risk_score = 0   # Low risk
            
            score += (10 - risk_score)
            
            # Determine recommended action
            if score >= 70 and margin >= 30 and profit >= 50:
                action = "STRONG BUY"
            elif score >= 50 and margin >= 20 and profit >= 25:
                action = "BUY"
            elif score >= 30 and margin >= 10 and profit >= 10:
                action = "CONSIDER"
            else:
                action = "PASS"
            
            return profit, margin, score, action
            
        except Exception as e:
            logger.error(f"Error calculating arbitrage score: {str(e)}")
            raise e

    def pre_screen_listings(self, listings: List[CardListing]) -> List[CardListing]:
        """Pre-screen listings to identify promising candidates for detailed analysis."""
        promising_listings = []
        
        for listing in listings:
            try:
                # Quick screening criteria (like human intuition)
                score = 0
                reasons = []
                
                # 1. Price screening (40% weight)
                price_usd = listing.price_usd
                if price_usd < 5:  # Too cheap, likely junk
                    score -= 20
                    reasons.append("Too cheap (<$5)")
                elif price_usd > 1000:  # Too expensive, high risk
                    score -= 15
                    reasons.append("Too expensive (>$1000)")
                elif 10 <= price_usd <= 200:  # Sweet spot
                    score += 20
                    reasons.append("Good price range ($10-$200)")
                
                # 2. Title quality screening (30% weight)
                title = listing.title.lower()
                title_en = listing.title_en.lower()
                
                # Check for valuable keywords
                valuable_keywords = [
                    'blue-eyes', 'blue eyes', '青眼', 'dark magician', 'ブラック・マジシャン',
                    'red-eyes', 'red eyes', 'レッドアイズ', 'lob', 'mfc', 'psv',
                    '1st', 'first', '初版', 'ultra', 'secret', 'シークレット',
                    'mint', 'new', '新品', 'unused', '未使用'
                ]
                
                keyword_matches = 0
                for keyword in valuable_keywords:
                    if keyword in title or keyword in title_en:
                        keyword_matches += 1
                
                if keyword_matches >= 2:
                    score += 15
                    reasons.append(f"Valuable keywords found ({keyword_matches})")
                elif keyword_matches == 1:
                    score += 8
                    reasons.append("Some valuable keywords")
                else:
                    score -= 10
                    reasons.append("No valuable keywords")
                
                # 3. Condition screening (20% weight)
                condition = listing.condition.lower()
                if any(word in condition for word in ['new', 'mint', '新品', '未使用']):
                    score += 10
                    reasons.append("Good condition")
                elif any(word in condition for word in ['used', '中古', '使用済み']):
                    score += 5
                    reasons.append("Used but acceptable")
                elif any(word in condition for word in ['damaged', 'damage', '傷', '破損']):
                    score -= 15
                    reasons.append("Damaged condition")
                
                # 4. Set code screening (10% weight)
                if listing.set_code:
                    # Check for valuable sets
                    valuable_sets = ['LOB', 'MFC', 'PSV', 'MRD', 'SRL', 'LON']
                    if any(set_code in listing.set_code.upper() for set_code in valuable_sets):
                        score += 10
                        reasons.append("Valuable set code")
                    else:
                        score += 2
                        reasons.append("Has set code")
                else:
                    score -= 5
                    reasons.append("No set code")
                
                # 5. Image quality check (if available)
                if listing.image_url and 'placeholder' not in listing.image_url.lower():
                    score += 5
                    reasons.append("Has real image")
                else:
                    score -= 5
                    reasons.append("No real image")
                
                # Determine if listing is promising
                listing.screening_score = score
                listing.screening_reasons = reasons
                
                # Only proceed with detailed analysis if score is above threshold
                if score >= 15:  # Minimum threshold for detailed analysis
                    promising_listings.append(listing)
                    logger.info(f"PROMISING: {listing.title_en} (Score: {score}) - {', '.join(reasons)}")
                else:
                    logger.debug(f"SKIPPED: {listing.title_en} (Score: {score}) - {', '.join(reasons)}")
                
            except Exception as e:
                logger.error(f"Error pre-screening listing: {str(e)}")
                continue
        
        logger.info(f"Pre-screening complete: {len(promising_listings)}/{len(listings)} listings selected for detailed analysis")
        return promising_listings

    def scrape_buyee_listings(self, keyword: str, max_results: int = 20) -> List[CardListing]:
        """Scrape card listings from Buyee."""
        listings = []
        try:
            # Construct search URL
            search_url = f"https://buyee.jp/item/search/query/{keyword}"
            self.driver.get(search_url)
            
            # Wait for results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.itemCard"))
            )
            
            # Get item cards
            items = self.driver.find_elements(By.CSS_SELECTOR, "li.itemCard")[:max_results]
            
            for item in items:
                try:
                    # Extract basic information
                    title = item.find_element(By.CSS_SELECTOR, "div.itemCard__itemName").text.strip()
                    price_text = item.find_element(By.CSS_SELECTOR, ".itemCard__itemInfo .g-price").text.strip()
                    price_yen = Decimal(re.sub(r'[^\d.]', '', price_text))
                    # Try multiple selectors for image URL
                    image_url = None
                    image_selectors = [
                        "img.lazyLoadV2.g-thumbnail__image",
                        "img.g-thumbnail__image",
                        "img[class*='thumbnail']",
                        "img"
                    ]
                    
                    for selector in image_selectors:
                        try:
                            img_element = item.find_element(By.CSS_SELECTOR, selector)
                            src = img_element.get_attribute("src") or img_element.get_attribute("data-src")
                            if src and 'noimage' not in src.lower() and 'placeholder' not in src.lower():
                                image_url = src
                                break
                        except NoSuchElementException:
                            continue
                    listing_url = item.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    
                    # Get condition if available
                    try:
                        condition = item.find_element(By.CSS_SELECTOR, "div.itemCard__condition").text.strip()
                    except NoSuchElementException:
                        condition = "Unknown"
                    
                    # Translate title
                    title_en = self.translate_text(title)
                    
                    # Extract card info
                    card_name, set_code, region = self.card_extractor.extract_card_info(title)
                    
                    # Create listing object
                    listing = CardListing(
                        title=title,
                        title_en=title_en,
                        price_yen=price_yen,
                        price_usd=price_yen * self.yen_to_usd,
                        condition=condition,
                        image_url=image_url,
                        listing_url=listing_url,
                        description="",  # Will be filled later
                        description_en="",  # Will be filled later
                        card_id=card_name,
                        set_code=set_code
                    )
                    
                    listings.append(listing)
                    
                except Exception as e:
                    logger.error(f"Error processing item: {str(e)}")
                    continue
            
            return listings
            
        except Exception as e:
            logger.error(f"Error scraping Buyee listings: {str(e)}")
            return []

    def analyze_listings(self, listings: List[CardListing]) -> List[CardListing]:
        """Analyze listings and calculate potential profits."""
        analyzed_listings = []
        
        for i, listing in enumerate(listings, 1):
            try:
                logger.info(f"Analyzing listing {i}/{len(listings)}: {listing.title_en}")
                
                if listing.card_id:
                    # Get eBay prices
                    ebay_prices = self.get_ebay_prices(listing.card_id, listing.set_code)
                    listing.ebay_prices = ebay_prices
                    
                    # Get 130point prices
                    point130_prices = self.get_130point_prices(listing.card_id, listing.set_code)
                    listing.point130_prices = point130_prices
                    
                    # Calculate arbitrage score
                    profit, margin, score, action = self.calculate_arbitrage_score(
                        listing.price_usd, ebay_prices, point130_prices, listing.condition
                    )
                    
                    listing.potential_profit = profit
                    listing.profit_margin = margin
                    listing.arbitrage_score = score
                    listing.recommended_action = action
                
                analyzed_listings.append(listing)
                
                # Add delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error analyzing listing: {str(e)}")
                continue
        
        return analyzed_listings

    def save_results(self, listings: List[CardListing], keyword: str):
        """Save results to CSV and JSON files."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Convert to DataFrame
            data = []
            for listing in listings:
                data.append({
                    'title': listing.title,
                    'title_en': listing.title_en,
                    'price_yen': float(listing.price_yen),
                    'price_usd': float(listing.price_usd),
                    'condition': listing.condition,
                    'image_url': listing.image_url,
                    'listing_url': listing.listing_url,
                    'card_id': listing.card_id,
                    'set_code': listing.set_code,
                    'ebay_raw_prices': [float(p) for p in listing.ebay_prices['raw']] if listing.ebay_prices else [],
                    'ebay_psa_prices': [float(p) for p in listing.ebay_prices['psa']] if listing.ebay_prices else [],
                    'point130_raw_avg': listing.point130_prices.get('raw_avg') if listing.point130_prices else None,
                    'point130_psa9_avg': listing.point130_prices.get('psa_9_avg') if listing.point130_prices else None,
                    'point130_psa10_avg': listing.point130_prices.get('psa_10_avg') if listing.point130_prices else None,
                    'potential_profit': float(listing.potential_profit) if listing.potential_profit else None,
                    'profit_margin': listing.profit_margin,
                    'arbitrage_score': listing.arbitrage_score,
                    'recommended_action': listing.recommended_action,
                    'screening_score': listing.screening_score,
                    'screening_reasons': listing.screening_reasons
                })
            
            df = pd.DataFrame(data)
            
            # Sort by arbitrage score (highest first)
            df = df.sort_values('arbitrage_score', ascending=False)
            
            # Save as CSV
            csv_path = os.path.join(self.output_dir, f"arbitrage_{keyword}_{timestamp}.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8')
            logger.info(f"Saved results to {csv_path}")
            
            # Save as JSON
            def decimal_converter(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            json_path = os.path.join(self.output_dir, f"arbitrage_{keyword}_{timestamp}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=decimal_converter)
            logger.info(f"Saved results to {json_path}")
            
            # Print summary
            self.print_summary(df)
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            raise e

    def print_summary(self, df: pd.DataFrame):
        """Print a summary of the arbitrage analysis."""
        print("\n" + "="*60)
        print("ARBITRAGE ANALYSIS SUMMARY")
        print("="*60)
        
        total_listings = len(df)
        profitable_listings = len(df[df['profit_margin'] > 0])
        strong_buys = len(df[df['recommended_action'] == 'STRONG BUY'])
        buys = len(df[df['recommended_action'] == 'BUY'])
        considers = len(df[df['recommended_action'] == 'CONSIDER'])
        
        print(f"Total listings analyzed: {total_listings}")
        print(f"Profitable opportunities: {profitable_listings}")
        print(f"Strong Buy recommendations: {strong_buys}")
        print(f"Buy recommendations: {buys}")
        print(f"Consider recommendations: {considers}")
        
        if not df.empty:
            avg_score = df['arbitrage_score'].mean()
            avg_margin = df['profit_margin'].mean()
            max_profit = df['potential_profit'].max()
            avg_screening = df['screening_score'].mean() if 'screening_score' in df.columns else 0
            
            print(f"\nAverage arbitrage score: {avg_score:.1f}/100")
            print(f"Average profit margin: {avg_margin:.1f}%")
            print(f"Maximum potential profit: ${max_profit:.2f}")
            print(f"Average screening score: {avg_screening:.1f}")
            
            # Show top opportunities
            top_opportunities = df[df['recommended_action'].isin(['STRONG BUY', 'BUY'])].head(5)
            if not top_opportunities.empty:
                print(f"\nTOP OPPORTUNITIES:")
                print("-" * 60)
                for _, row in top_opportunities.iterrows():
                    print(f"• {row['title_en']}")
                    print(f"  Price: ¥{row['price_yen']:,} (${row['price_usd']:.2f})")
                    print(f"  Profit: ${row['potential_profit']:.2f} ({row['profit_margin']:.1f}%)")
                    print(f"  Score: {row['arbitrage_score']:.1f}/100 - {row['recommended_action']}")
                    if 'screening_reasons' in row and row['screening_reasons']:
                        print(f"  Screening: {', '.join(row['screening_reasons'])}")
                    print()

    def run(self, keyword: str, max_results: int = 20):
        """Run the complete arbitrage analysis."""
        try:
            logger.info(f"Starting arbitrage analysis for: {keyword}")
            
            # Scrape Buyee listings
            listings = self.scrape_buyee_listings(keyword, max_results)
            logger.info(f"Found {len(listings)} listings")
            
            if not listings:
                logger.warning("No listings found")
                return []
            
            # Pre-screen listings (like human intuition)
            promising_listings = self.pre_screen_listings(listings)
            
            if not promising_listings:
                logger.warning("No promising listings found after pre-screening")
                return []
            
            # Analyze only promising listings
            analyzed_listings = self.analyze_listings(promising_listings)
            
            # Convert to dictionary format for web interface
            results = []
            for listing in analyzed_listings:
                # Derive Yahoo Auction URL from Buyee listing_url if possible
                yahoo_url = None
                if listing.listing_url:
                    import re
                    match = re.search(r'/([a-z]\d+)(?:\?|$)', listing.listing_url)
                    if match:
                        yahoo_id = match.group(1)
                        yahoo_url = f"https://page.auctions.yahoo.co.jp/jp/auction/{yahoo_id}"

                # Calculate best available average price (130point raw avg > eBay raw avg > 0)
                ebay_avg_price = 0
                if listing.point130_prices and listing.point130_prices.get('raw_avg'):
                    ebay_avg_price = float(listing.point130_prices['raw_avg'])
                elif listing.ebay_prices and listing.ebay_prices.get('raw') and listing.ebay_prices['raw']:
                    import statistics
                    ebay_avg_price = float(statistics.mean(listing.ebay_prices['raw']))
                # else remains 0

                results.append({
                    'title': listing.title,
                    'title_en': listing.title_en,
                    'price_yen': int(listing.price_yen),
                    'price_usd': float(listing.price_usd),
                    'condition': listing.condition,
                    'image_url': listing.image_url,
                    'listing_url': listing.listing_url,  # Buyee link
                    'yahoo_url': yahoo_url,              # Yahoo Auction link
                    'description': listing.description,
                    'description_en': listing.description_en,
                    'card_id': listing.card_id,
                    'set_code': listing.set_code,
                    'ebay_prices': listing.ebay_prices,
                    'point130_prices': listing.point130_prices,
                    'potential_profit': float(listing.potential_profit) if listing.potential_profit else 0,
                    'profit_margin': listing.profit_margin or 0,
                    'arbitrage_score': listing.arbitrage_score or 0,
                    'recommended_action': listing.recommended_action or 'PASS',
                    'screening_score': listing.screening_score or 0,
                    'screening_reasons': listing.screening_reasons or [],
                    'ebay_avg_price': ebay_avg_price,
                    'search_term': keyword
                })
            
            # Save results
            self.save_results(analyzed_listings, keyword)
            
            logger.info("Arbitrage analysis complete")
            return results
            
        except Exception as e:
            logger.error(f"Error in arbitrage analysis: {str(e)}")
            return []

    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()

def main():
    """Example usage of the enhanced arbitrage tool."""
    tool = CardArbitrageTool()
    
    try:
        # Example search terms
        search_terms = [
            "青眼の白龍",  # Blue-Eyes White Dragon
            "ブラック・マジシャン",  # Dark Magician
            "遊戯王 レア",  # Yu-Gi-Oh! Rare cards
        ]
        
        for term in search_terms:
            print(f"\nAnalyzing: {term}")
            tool.run(term, max_results=10)
            time.sleep(5)  # Delay between searches
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
    finally:
        tool.cleanup()

if __name__ == "__main__":
    main() 