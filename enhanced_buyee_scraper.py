#!/usr/bin/env python3
"""
Enhanced Buyee Scraper with Improved Image Loading and Auction Status Filtering
Fixes image loading issues and excludes finished auctions
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import pandas as pd
import time
import json
import os
from datetime import datetime
import logging
from urllib.parse import urljoin, quote
from search_terms import SEARCH_TERMS
import csv
import traceback
from typing import Dict, List, Optional, Any, Tuple
from scraper_utils import RequestHandler, CardInfoExtractor, PriceAnalyzer, ConditionAnalyzer
from dotenv import load_dotenv
import re
import socket
import requests.exceptions
import urllib3
import argparse
import statistics
from image_analyzer import ImageAnalyzer
import glob
from src.card_analyzer2 import CardAnalyzer
from rank_analyzer import RankAnalyzer, CardCondition
import requests
from PIL import Image
import io
import base64

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    logger.error("OPENAI_API_KEY not found. Please check your .env file and its location.")
    import sys
    sys.exit(1)

class EnhancedBuyeeScraper:
    def __init__(self, output_dir: str = "enhanced_scraped_results", max_pages: int = 5, headless: bool = True, use_llm: bool = False):
        """
        Initialize the Enhanced Buyee Scraper with improved image handling and auction filtering.
        
        Args:
            output_dir (str): Directory to save scraped data
            max_pages (int): Maximum number of pages to scrape per search
            headless (bool): Run Chrome in headless mode
            use_llm (bool): Enable LLM analysis (requires OpenAI API key)
        """
        self.base_url = "https://buyee.jp"
        self.output_dir = output_dir
        self.max_pages = max_pages
        self.headless = headless
        self.use_llm = use_llm
        self.driver = None
        self.request_handler = RequestHandler()
        self.card_analyzer = CardAnalyzer(use_llm=use_llm)
        self.rank_analyzer = RankAnalyzer()
        
        os.makedirs(self.output_dir, exist_ok=True)
        self.setup_driver()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        
    def cleanup(self):
        """Clean up resources and close the driver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error during driver cleanup: {str(e)}")
            self.driver = None
            
    def setup_driver(self):
        """Set up and configure Chrome WebDriver with stealth mode."""
        try:
            # Try undetected-chromedriver first
            try:
                import undetected_chromedriver as uc
                logger.info("Using undetected-chromedriver for better stealth")
                
                options = uc.ChromeOptions()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                # Add additional stealth options
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                try:
                    self.driver = uc.Chrome(options=options)
                except Exception as uc_error:
                    logger.warning(f"undetected-chromedriver failed: {str(uc_error)}")
                    logger.info("Falling back to regular selenium")
                    raise ImportError("undetected-chromedriver failed")
                
                # Apply stealth settings
                stealth(self.driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                )
                
            except ImportError:
                logger.info("undetected-chromedriver not available or failed, using regular selenium")
                
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                # Add stealth options
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                try:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                except Exception as selenium_error:
                    logger.error(f"Regular selenium also failed: {str(selenium_error)}")
                    raise
                
                # Apply stealth settings
                stealth(self.driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                )
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            logger.info("WebDriver setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {str(e)}")
            raise

    def is_driver_valid(self):
        """Check if the driver is still valid and responsive."""
        try:
            if not self.driver:
                return False
            # Try to get current URL to test if driver is responsive
            self.driver.current_url
            return True
        except Exception:
            return False

    def wait_for_page_ready(self, timeout: int = 30) -> bool:
        """Wait for page to be fully loaded and ready."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            logger.warning(f"Page load timeout after {timeout} seconds")
            return False

    def handle_cookie_popup(self):
        """Handle cookie consent popup if present."""
        try:
            cookie_selectors = [
                "button[data-testid='cookie-accept']",
                "button.accept-cookies",
                "button.cookie-accept",
                "button[class*='cookie']",
                "button[class*='accept']",
                "button[class*='consent']"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    logger.info("Cookie popup handled")
                    time.sleep(2)
                    break
                except TimeoutException:
                    continue
        except Exception as e:
            logger.debug(f"No cookie popup found or error handling it: {str(e)}")

    def search_items(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for items with enhanced filtering and image handling."""
        try:
            logger.info(f"Starting search for: {search_term}")
            
            # Construct search URL
            search_url = f"{self.base_url}/item/search?keyword={quote(search_term)}&translationType=1"
            
            if not self.is_driver_valid():
                self.setup_driver()
            
            self.driver.get(search_url)
            
            if not self.wait_for_page_ready(timeout=30):
                raise TimeoutException("Search page failed to load")
            
            self.handle_cookie_popup()
            
            all_items = []
            promising_items = []
            page = 1
            
            while page <= self.max_pages:
                logger.info(f"Processing page {page} for search term: {search_term}")
                
                # Get item summaries from current page
                summaries = self.get_item_summaries_from_search_page(page)
                
                if not summaries:
                    logger.info(f"No items found on page {page}")
                    break
                
                logger.info(f"Found {len(summaries)} items on page {page}")
                
                # Process each item with enhanced detail scraping
                for summary in summaries:
                    try:
                        logger.info(f"Processing item: {summary.get('title', 'Unknown')}")
                        
                        # Check if auction is finished
                        if self.is_auction_finished(summary):
                            logger.info(f"Skipping finished auction: {summary.get('title', 'Unknown')}")
                            continue
                        
                        # Scrape detailed information
                        detailed_info = self.scrape_item_detail_page(summary['url'])
                        
                        if not detailed_info:
                            logger.warning(f"Failed to get detailed info for: {summary.get('title', 'Unknown')}")
                            continue
                        
                        # Enhanced image processing
                        detailed_info['images'] = self.process_images(detailed_info.get('images', []))
                        detailed_info['thumbnail_url'] = self.get_best_thumbnail(detailed_info.get('images', []))
                        
                        # Merge summary and detailed info
                        merged_info = {**summary, **detailed_info}
                        
                        # Check if item is valuable
                        is_valuable = (
                            detailed_info['card_details'].get('is_valuable', False) and
                            detailed_info['card_details'].get('confidence_score', 0) >= 0.3
                        )
                        
                        if is_valuable:
                            logger.info(f"Found valuable item: {detailed_info['title']}")
                            all_items.append(merged_info)
                            promising_items.append(merged_info)
                        
                    except Exception as e:
                        logger.error(f"Error processing item {summary['url']}: {str(e)}")
                        logger.error(traceback.format_exc())
                        continue
                
                # Check for next page
                if not self.has_next_page():
                    break
                    
                # Go to next page
                if not self.go_to_next_page():
                    break
                    
                page += 1
            
            # Save all results
            if all_items:
                self.save_results(all_items, search_term)
                logger.info(f"Found {len(all_items)} valuable items for {search_term}")
            
            # Save promising items to bookmarks
            if promising_items:
                self.save_promising_items(promising_items, search_term)
                logger.info(f"Bookmarked {len(promising_items)} promising items for {search_term}")
            else:
                logger.info(f"No promising items found for {search_term}")
            
            return all_items
            
        except Exception as e:
            logger.error(f"Error during search for {search_term}: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def is_auction_finished(self, item_summary: Dict) -> bool:
        """Check if an auction is finished/ended."""
        try:
            # Check for finished auction indicators in the summary
            title = item_summary.get('title', '').lower()
            description = item_summary.get('description', '').lower()
            
            # Keywords that indicate finished auctions
            finished_keywords = [
                '終了', 'ended', 'finished', 'closed', 'sold', '落札', '落札済み',
                'auction ended', 'auction closed', 'auction finished',
                'このオークションは終了しました', 'this auction has ended'
            ]
            
            for keyword in finished_keywords:
                if keyword in title or keyword in description:
                    return True
            
            # Check for specific HTML elements that indicate finished auctions
            if 'url' in item_summary:
                try:
                    # Quick check of the item page for finished indicators
                    response = requests.get(item_summary['url'], timeout=10)
                    if response.status_code == 200:
                        content = response.text.lower()
                        for keyword in finished_keywords:
                            if keyword in content:
                                return True
                except Exception:
                    pass
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking auction status: {str(e)}")
            return False

    def process_images(self, image_urls: List[str]) -> List[Dict[str, Any]]:
        """Process and enhance image information."""
        processed_images = []
        
        for i, url in enumerate(image_urls):
            try:
                if not url or 'noimage' in url.lower() or 'placeholder' in url.lower():
                    continue
                
                # Try to get image metadata
                image_info = {
                    'url': url,
                    'index': i,
                    'processed_url': self.process_image_url(url),
                    'thumbnail_url': self.create_thumbnail_url(url),
                    'is_valid': True
                }
                
                # Try to validate image by downloading a small portion
                try:
                    response = requests.head(url, timeout=5)
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'image' in content_type:
                            image_info['content_type'] = content_type
                            image_info['size'] = response.headers.get('content-length')
                        else:
                            image_info['is_valid'] = False
                except Exception:
                    image_info['is_valid'] = False
                
                processed_images.append(image_info)
                
            except Exception as e:
                logger.warning(f"Error processing image {url}: {str(e)}")
                continue
        
        return processed_images

    def process_image_url(self, url: str) -> str:
        """Process image URL to ensure it's accessible."""
        try:
            # Handle relative URLs
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = self.base_url + url
            
            # Handle Buyee CDN URLs
            if 'buyee.jp' in url and 'cdn' not in url:
                # Try to convert to CDN URL if possible
                url = url.replace('buyee.jp', 'buyee.jp/cdn')
            
            return url
            
        except Exception as e:
            logger.warning(f"Error processing image URL {url}: {str(e)}")
            return url

    def create_thumbnail_url(self, url: str) -> str:
        """Create a thumbnail URL for the image."""
        try:
            # For Buyee images, try to get thumbnail version
            if 'buyee.jp' in url:
                # Try different thumbnail patterns
                thumbnail_patterns = [
                    url.replace('/original/', '/thumbnail/'),
                    url.replace('/large/', '/thumbnail/'),
                    url + '?size=thumbnail',
                    url + '&size=thumbnail'
                ]
                
                for pattern in thumbnail_patterns:
                    try:
                        response = requests.head(pattern, timeout=3)
                        if response.status_code == 200:
                            return pattern
                    except Exception:
                        continue
            
            return url
            
        except Exception as e:
            logger.warning(f"Error creating thumbnail URL for {url}: {str(e)}")
            return url

    def get_best_thumbnail(self, images: List[Dict[str, Any]]) -> str:
        """Get the best thumbnail URL from processed images."""
        try:
            # Filter valid images
            valid_images = [img for img in images if img.get('is_valid', False)]
            
            if not valid_images:
                return ""
            
            # Prefer thumbnail URLs
            for img in valid_images:
                if img.get('thumbnail_url') and img['thumbnail_url'] != img.get('url'):
                    return img['thumbnail_url']
            
            # Fall back to first valid image
            return valid_images[0].get('processed_url', valid_images[0].get('url', ''))
            
        except Exception as e:
            logger.warning(f"Error getting best thumbnail: {str(e)}")
            return ""

    def scrape_item_detail_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape detailed information from an item's page with improved image handling."""
        max_retries = 3
        retry_delay = 5
        current_retry = 0
        
        while current_retry < max_retries:
            try:
                if not self.is_driver_valid():
                    self.setup_driver()
                
                logger.info(f"Attempting to scrape item detail page: {url}")
                self.driver.get(url)
                
                # Wait for page to be fully loaded
                if not self.wait_for_page_ready(timeout=30):
                    raise TimeoutException("Page failed to load properly")
                
                # Handle cookie popup if present
                self.handle_cookie_popup()
                
                # Check if auction is finished on detail page
                if self.is_detail_page_finished():
                    logger.info(f"Auction is finished on detail page: {url}")
                    return None
                
                # Wait for main content to be visible
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.itemDetail"))
                )
                
                # Extract basic information with explicit waits
                title = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.itemName"))
                ).text.strip()
                
                price_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.price"))
                )
                price = self.clean_price(price_element.text)
                
                # Extract description with fallback
                try:
                    description_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.itemDescription"))
                    )
                    description = description_element.text.strip()
                except TimeoutException:
                    description = "No description available"
                    logger.warning(f"No description found for item: {url}")
                
                # Enhanced image extraction
                images = self.extract_images_enhanced()
                
                # Extract seller information
                try:
                    seller_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.sellerName"))
                    )
                    seller = seller_element.text.strip()
                except TimeoutException:
                    seller = "Unknown"
                    logger.warning(f"No seller information found for item: {url}")
                
                # Extract condition information
                try:
                    condition_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.itemCondition"))
                    )
                    condition = condition_element.text.strip()
                except TimeoutException:
                    condition = "Unknown"
                    logger.warning(f"No condition information found for item: {url}")
                
                # Parse card details
                card_details = self.parse_card_details_from_buyee(title, description)
                
                # Combine all information
                item_data = {
                    'url': url,
                    'title': title,
                    'price': price,
                    'description': description,
                    'images': images,
                    'seller': seller,
                    'condition': condition,
                    'card_details': card_details,
                    'scraped_at': datetime.now().isoformat()
                }
                
                logger.info(f"Successfully scraped item: {title}")
                return item_data
                
            except TimeoutException as e:
                current_retry += 1
                logger.warning(f"Timeout while scraping {url} (Attempt {current_retry}/{max_retries}): {str(e)}")
                if current_retry < max_retries:
                    time.sleep(retry_delay)
                    continue
                self.save_debug_info(url, "timeout", self.driver.page_source)
                return None
                
            except WebDriverException as e:
                current_retry += 1
                logger.error(f"WebDriver error while scraping {url} (Attempt {current_retry}/{max_retries}): {str(e)}")
                if current_retry < max_retries:
                    time.sleep(retry_delay)
                    self.setup_driver()  # Reset driver on WebDriverException
                    continue
                self.save_debug_info(url, "webdriver_error", self.driver.page_source)
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error while scraping {url}: {str(e)}")
                self.save_debug_info(url, "unexpected_error", self.driver.page_source)
                return None
        
        logger.error(f"Failed to scrape {url} after {max_retries} attempts")
        return None

    def is_detail_page_finished(self) -> bool:
        """Check if the detail page shows a finished auction."""
        try:
            # Look for finished auction indicators on the detail page
            finished_indicators = [
                "このオークションは終了しました",
                "auction ended",
                "auction closed",
                "auction finished",
                "終了",
                "ended",
                "finished",
                "closed"
            ]
            
            page_text = self.driver.page_source.lower()
            for indicator in finished_indicators:
                if indicator.lower() in page_text:
                    return True
            
            # Check for specific elements that indicate finished auctions
            finished_selectors = [
                "div.auction-ended",
                "div.auction-closed",
                "div.finished-auction",
                "span.auction-status[data-status='ended']",
                "div[class*='ended']",
                "div[class*='finished']"
            ]
            
            for selector in finished_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking detail page finished status: {str(e)}")
            return False

    def extract_images_enhanced(self) -> List[str]:
        """Extract images with enhanced selectors and fallbacks."""
        images = []
        
        # Multiple selectors for images
        image_selectors = [
            "div.itemImage img",
            "div.item-images img",
            "div.product-images img",
            "div.auction-images img",
            "div.gallery img",
            "img[class*='item-image']",
            "img[class*='product-image']",
            "img[class*='auction-image']",
            "img[class*='main-image']",
            "img[class*='thumbnail']",
            "img[class*='photo']",
            "img[class*='picture']",
            "img[data-src]",
            "img[data-original]",
            "img[data-lazy]"
        ]
        
        for selector in image_selectors:
            try:
                image_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for img in image_elements:
                    # Try multiple attributes for image URL
                    src = img.get_attribute('src')
                    data_src = img.get_attribute('data-src')
                    data_original = img.get_attribute('data-original')
                    data_lazy = img.get_attribute('data-lazy')
                    
                    # Use the first valid URL found
                    image_url = src or data_src or data_original or data_lazy
                    
                    if image_url and 'noimage' not in image_url.lower() and 'placeholder' not in image_url.lower():
                        # Process the URL
                        processed_url = self.process_image_url(image_url)
                        if processed_url not in images:
                            images.append(processed_url)
                            logger.info(f"Found image: {processed_url}")
                
                if images:
                    break  # Found images with this selector, no need to try others
                    
            except Exception as e:
                logger.warning(f"Error with image selector '{selector}': {str(e)}")
                continue
        
        # If no images found, try JavaScript to get all images
        if not images:
            try:
                js_images = self.driver.execute_script("""
                    return Array.from(document.querySelectorAll('img')).map(img => {
                        return img.src || img.dataset.src || img.dataset.original || img.dataset.lazy;
                    }).filter(src => src && !src.includes('noimage') && !src.includes('placeholder'));
                """)
                
                for img_url in js_images:
                    if img_url and img_url not in images:
                        processed_url = self.process_image_url(img_url)
                        images.append(processed_url)
                        logger.info(f"Found image via JavaScript: {processed_url}")
                        
            except Exception as e:
                logger.warning(f"Error extracting images via JavaScript: {str(e)}")
        
        logger.info(f"Extracted {len(images)} images")
        return images

    def get_item_summaries_from_search_page(self, page_number: int = 1) -> List[Dict]:
        """Extract item summaries from the current search results page with auction status filtering."""
        summaries = []
        debug_dir = os.path.join(self.output_dir, "debug")
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # First, verify we're on a search results page
            current_url = self.driver.current_url
            if "item/search" not in current_url:
                logger.error(f"Not on a search results page. Current URL: {current_url}")
                self.save_debug_info(f"search_page_{timestamp}", "wrong_page", self.driver.page_source)
                return []
            
            # Save initial page state for debugging
            with open(os.path.join(debug_dir, f"search_page_initial_{timestamp}.html"), 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # Try multiple selectors for item cards
            item_card_selectors = [
                "li.itemCard",
                "div[data-testid='item-card']",
                "div.item-card",
                "div.search-result-item",
                "div.auction-item",
                "div.product-item"
            ]
            
            card_elements = []
            used_selector = None
            
            # Try each selector in sequence
            for selector in item_card_selectors:
                try:
                    logger.info(f"Attempting to find item cards with selector: '{selector}'")
                    card_elements = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if card_elements:
                        used_selector = selector
                        logger.info(f"Successfully found {len(card_elements)} item cards using selector: '{selector}'")
                        break
                except TimeoutException:
                    logger.warning(f"Timeout waiting for item cards with selector: '{selector}'")
                    continue
                except Exception as e:
                    logger.warning(f"Error with selector '{selector}': {str(e)}")
                    continue
            
            if not card_elements:
                logger.error("No item cards found with any selector")
                self.save_debug_info(f"search_page_{timestamp}", "no_cards_found", self.driver.page_source)
                return []
            
            # Process each card with robust error handling
            for i, card in enumerate(card_elements):
                try:
                    # Check if this card represents a finished auction
                    if self.is_card_finished_auction(card):
                        logger.info(f"Skipping finished auction card {i+1}")
                        continue
                    
                    # Try multiple selectors for each element
                    title_selectors = [
                        "h3[data-testid='item-card-title']",
                        "div.itemCard__itemName a",
                        "div.item-title a",
                        "a.item-title",
                        "h3.item-name",
                        "div.auction-title a"
                    ]
                    
                    price_selectors = [
                        "span[data-testid='item-card-price']",
                        "div.g-priceDetails span.g-price",
                        "div.item-price",
                        "span.price",
                        "div.auction-price",
                        "span.current-price"
                    ]
                    
                    # Extract title and URL
                    title = None
                    url = None
                    for selector in title_selectors:
                        try:
                            title_element = card.find_element(By.CSS_SELECTOR, selector)
                            title = title_element.text.strip()
                            url = title_element.get_attribute('href')
                            if title and url:
                                break
                        except NoSuchElementException:
                            continue
                    
                    if not title or not url:
                        logger.warning(f"Could not extract title/URL for card {i+1}")
                        continue
                    
                    # Extract price
                    price_text = None
                    for selector in price_selectors:
                        try:
                            price_element = card.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_element.text.strip()
                            if price_text:
                                break
                        except NoSuchElementException:
                            continue
                    
                    if not price_text:
                        logger.warning(f"Could not extract price for card {i+1}: {title}")
                        continue
                    
                    price_yen = self.clean_price(price_text)
                    
                    # Enhanced thumbnail extraction
                    thumbnail_url = self.extract_thumbnail_enhanced(card)
                    
                    # Log basic info
                    logger.info(f"Item {i+1}/{len(card_elements)}:")
                    logger.info(f"  Title: {title}")
                    logger.info(f"  Price: {price_yen} yen")
                    logger.info(f"  URL: {url}")
                    logger.info(f"  Thumbnail: {thumbnail_url}")
                    
                    # Analyze the card
                    try:
                        card_info = self.card_analyzer.analyze_card({
                            'title': title,
                            'price_text': price_text,
                            'url': url,
                            'thumbnail_url': thumbnail_url
                        })
                        
                        # Convert CardInfo to dictionary for logging and storage
                        preliminary_analysis = {
                            'is_valuable': card_info.is_valuable,
                            'confidence_score': card_info.confidence_score,
                            'condition': str(card_info.condition.value) if card_info.condition else None,
                            'rarity': card_info.rarity,
                            'set_code': card_info.set_code,
                            'card_number': card_info.card_number,
                            'edition': card_info.edition,
                            'region': card_info.region
                        }
                        
                        # Log analysis results
                        logger.info(f"  Analysis Results:")
                        for key, value in preliminary_analysis.items():
                            logger.info(f"    {key.replace('_', ' ').title()}: {value}")
                        
                        # Create card info dictionary
                        card_info_dict = {
                            'title': title,
                            'price_text': price_text,
                            'price_yen': price_yen,
                            'url': url,
                            'thumbnail_url': thumbnail_url,
                            'preliminary_analysis': preliminary_analysis
                        }
                        
                        # Add to summaries if it's promising
                        if preliminary_analysis['is_valuable'] and preliminary_analysis['confidence_score'] >= 0.3:
                            summaries.append(card_info_dict)
                            logger.info(f"  Added promising item to summaries")
                        else:
                            logger.debug(f"  Skipped item at initial filter")
                        
                    except Exception as analysis_error:
                        logger.error(f"Error during card analysis for '{title}': {str(analysis_error)}")
                        logger.error(traceback.format_exc())
                        continue
                    
                except StaleElementReferenceException:
                    logger.warning(f"StaleElementReferenceException while processing card {i+1}. Page might have updated.")
                    self.save_debug_info(f"search_page_stale_{timestamp}", "stale_element", self.driver.page_source)
                    break
                    
                except Exception as card_error:
                    logger.error(f"Error processing card {i+1}: {str(card_error)}")
                    logger.error(traceback.format_exc())
                    continue
            
            # Save successful scrape info
            if summaries:
                success_info = {
                    'timestamp': timestamp,
                    'page_number': page_number,
                    'total_cards_found': len(card_elements),
                    'promising_items': len(summaries),
                    'used_selector': used_selector
                }
                success_path = os.path.join(debug_dir, f"search_page_success_{timestamp}.json")
                with open(success_path, 'w', encoding='utf-8') as f:
                    json.dump(success_info, f, ensure_ascii=False, indent=2)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error getting item summaries: {str(e)}")
            logger.error(traceback.format_exc())
            self.save_debug_info(f"search_page_error_{timestamp}", "error", self.driver.page_source)
            return []

    def is_card_finished_auction(self, card_element) -> bool:
        """Check if a card element represents a finished auction."""
        try:
            # Get the card's text content
            card_text = card_element.text.lower()
            
            # Keywords that indicate finished auctions
            finished_keywords = [
                '終了', 'ended', 'finished', 'closed', 'sold', '落札', '落札済み',
                'auction ended', 'auction closed', 'auction finished'
            ]
            
            for keyword in finished_keywords:
                if keyword in card_text:
                    return True
            
            # Check for specific elements within the card
            finished_selectors = [
                "span.auction-ended",
                "div.finished-auction",
                "span[class*='ended']",
                "div[class*='finished']",
                "span[class*='closed']"
            ]
            
            for selector in finished_selectors:
                try:
                    element = card_element.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking card finished status: {str(e)}")
            return False

    def extract_thumbnail_enhanced(self, card_element) -> str:
        """Extract thumbnail URL with enhanced selectors."""
        thumbnail_selectors = [
            "img.lazyLoadV2.g-thumbnail__image",
            "img[data-testid='item-card-image']",
            "div.itemCard__image img",
            "div.item-image img",
            "img.item-image",
            "img.g-thumbnail__image",
            "img[class*='thumbnail']",
            "img[class*='thumb']",
            "img[class*='photo']",
            "img[class*='picture']",
            "img[data-src]",
            "img[data-original]",
            "img[data-lazy]"
        ]
        
        for selector in thumbnail_selectors:
            try:
                img_element = card_element.find_element(By.CSS_SELECTOR, selector)
                
                # Try multiple attributes for image URL
                src = img_element.get_attribute('src')
                data_src = img_element.get_attribute('data-src')
                data_original = img_element.get_attribute('data-original')
                data_lazy = img_element.get_attribute('data-lazy')
                
                # Use the first valid URL found
                thumbnail_url = src or data_src or data_original or data_lazy
                
                if thumbnail_url and 'noimage' not in thumbnail_url.lower() and 'placeholder' not in thumbnail_url.lower():
                    # Process the URL
                    processed_url = self.process_image_url(thumbnail_url)
                    logger.info(f"Found thumbnail: {processed_url}")
                    return processed_url
                    
            except NoSuchElementException:
                continue
            except Exception as e:
                logger.warning(f"Error with thumbnail selector '{selector}': {str(e)}")
                continue
        
        # If no thumbnail found, try to find any image in the card
        try:
            all_images = card_element.find_elements(By.CSS_SELECTOR, "img")
            for img in all_images:
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if src and 'noimage' not in src.lower() and 'placeholder' not in src.lower():
                    processed_url = self.process_image_url(src)
                    logger.info(f"Found fallback image: {processed_url}")
                    return processed_url
        except Exception:
            pass
        
        return ""

    def clean_price(self, price_text: str) -> float:
        """Clean and extract price from text."""
        try:
            # Remove currency symbols and non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d.,]', '', price_text)
            
            # Handle different decimal separators
            if ',' in cleaned and '.' in cleaned:
                # If both comma and dot exist, assume comma is thousands separator
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # If only comma exists, check if it's decimal or thousands separator
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Likely decimal separator
                    cleaned = cleaned.replace(',', '.')
                else:
                    # Likely thousands separator
                    cleaned = cleaned.replace(',', '')
            
            return float(cleaned) if cleaned else 0.0
            
        except Exception as e:
            logger.warning(f"Error cleaning price '{price_text}': {str(e)}")
            return 0.0

    def parse_card_details_from_buyee(self, title: str, description: str) -> Dict[str, Any]:
        """Parse card details from Buyee title and description."""
        try:
            # Use the card analyzer to extract details
            card_info = self.card_analyzer.analyze_card({
                'title': title,
                'description': description
            })
            
            return {
                'is_valuable': card_info.is_valuable,
                'confidence_score': card_info.confidence_score,
                'condition': str(card_info.condition.value) if card_info.condition else None,
                'rarity': card_info.rarity,
                'set_code': card_info.set_code,
                'card_number': card_info.card_number,
                'edition': card_info.edition,
                'region': card_info.region
            }
            
        except Exception as e:
            logger.error(f"Error parsing card details: {str(e)}")
            return {
                'is_valuable': False,
                'confidence_score': 0.0,
                'condition': None,
                'rarity': None,
                'set_code': None,
                'card_number': None,
                'edition': None,
                'region': None
            }

    def has_next_page(self) -> bool:
        """Check if there's a next page available."""
        try:
            next_selectors = [
                "a[class*='next']",
                "a[class*='pagination']",
                "button[class*='next']",
                "a[aria-label*='next']",
                "a[aria-label*='Next']",
                "a[title*='next']",
                "a[title*='Next']"
            ]
            
            for selector in next_selectors:
                try:
                    next_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_element.is_displayed() and next_element.is_enabled():
                        return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for next page: {str(e)}")
            return False

    def go_to_next_page(self) -> bool:
        """Navigate to the next page."""
        try:
            next_selectors = [
                "a[class*='next']",
                "a[class*='pagination']",
                "button[class*='next']",
                "a[aria-label*='next']",
                "a[aria-label*='Next']",
                "a[title*='next']",
                "a[title*='Next']"
            ]
            
            for selector in next_selectors:
                try:
                    next_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_element.is_displayed() and next_element.is_enabled():
                        next_element.click()
                        time.sleep(3)  # Wait for page to load
                        return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error going to next page: {str(e)}")
            return False

    def save_results(self, results: List[Dict[str, Any]], search_term: str) -> None:
        """Save results to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_results_{search_term}_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(results)} results to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")

    def save_promising_items(self, items: List[Dict[str, Any]], search_term: str) -> None:
        """Save promising items to a separate file for easy access."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"promising_items_{search_term}_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(items)} promising items to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving promising items: {str(e)}")

    def save_debug_info(self, identifier: str, error_type: str, page_source: str) -> None:
        """Save debug information for troubleshooting."""
        try:
            debug_dir = os.path.join(self.output_dir, "debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{identifier}_{error_type}_{timestamp}.html"
            filepath = os.path.join(debug_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            logger.info(f"Saved debug info to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving debug info: {str(e)}")

def main():
    """Main function to run the enhanced scraper."""
    parser = argparse.ArgumentParser(description='Enhanced Buyee Scraper with improved image handling')
    parser.add_argument('--search-term', type=str, help='Search term to use')
    parser.add_argument('--max-pages', type=int, default=5, help='Maximum pages to scrape')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--use-llm', action='store_true', help='Enable LLM analysis')
    parser.add_argument('--output-dir', type=str, default='enhanced_scraped_results', help='Output directory')
    
    args = parser.parse_args()
    
    # Use provided search term or default from SEARCH_TERMS
    search_term = args.search_term or SEARCH_TERMS[0] if SEARCH_TERMS else "Yu-Gi-Oh! card"
    
    with EnhancedBuyeeScraper(
        output_dir=args.output_dir,
        max_pages=args.max_pages,
        headless=args.headless,
        use_llm=args.use_llm
    ) as scraper:
        results = scraper.search_items(search_term)
        print(f"Found {len(results)} valuable items for '{search_term}'")

if __name__ == "__main__":
    main()
