#!/usr/bin/env python3
"""
Robust scraper configuration to reduce errors and improve reliability
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import random

logger = logging.getLogger(__name__)

class RobustWebDriver:
    """A more robust WebDriver configuration with better error handling"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with robust configuration"""
        try:
            chrome_options = Options()
            
            # Essential options to reduce errors
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # Faster loading
            chrome_options.add_argument('--disable-javascript')  # Reduce errors
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-translate')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            
            # Logging options to reduce console spam
            chrome_options.add_argument('--log-level=3')  # Only fatal errors
            chrome_options.add_argument('--silent')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-gpu-logging')
            
            # Memory and performance optimizations
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=4096')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            
            # User agent to appear more legitimate
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            if self.headless:
                chrome_options.add_argument('--headless=new')  # Use new headless mode
            
            # Prefs to disable more features
            prefs = {
                "profile.default_content_setting_values": {
                    "images": 2,  # Block images
                    "plugins": 2,  # Block plugins
                    "popups": 2,  # Block popups
                    "geolocation": 2,  # Block location sharing
                    "notifications": 2,  # Block notifications
                    "media_stream": 2,  # Block media stream
                },
                "profile.managed_default_content_settings": {
                    "images": 2
                }
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Disable logging
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Create driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(10)
            
            logger.info("Robust Chrome WebDriver setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise
    
    def safe_get(self, url: str, max_retries: int = 3) -> bool:
        """Safely navigate to a URL with retries"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to {url} (attempt {attempt + 1})")
                self.driver.get(url)
                
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Random delay to appear more human
                time.sleep(random.uniform(2, 5))
                return True
                
            except TimeoutException:
                logger.warning(f"Timeout loading {url} on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                    
            except WebDriverException as e:
                logger.error(f"WebDriver error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                    
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
        
        logger.error(f"Failed to load {url} after {max_retries} attempts")
        return False
    
    def safe_find_elements(self, by, value, timeout: int = 10):
        """Safely find elements with timeout"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            elements = wait.until(EC.presence_of_all_elements_located((by, value)))
            return elements
        except TimeoutException:
            logger.warning(f"Timeout finding elements by {by}={value}")
            return []
        except Exception as e:
            logger.error(f"Error finding elements: {e}")
            return []
    
    def safe_find_element(self, by, value, timeout: int = 10):
        """Safely find a single element with timeout"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            logger.warning(f"Timeout finding element by {by}={value}")
            return None
        except Exception as e:
            logger.error(f"Error finding element: {e}")
            return None
    
    def close(self):
        """Safely close the driver"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
        except Exception as e:
            logger.error(f"Error closing WebDriver: {e}")

# Configuration for different sites
SITE_CONFIGS = {
    'buyee': {
        'base_url': 'https://buyee.jp/item/search/query',
        'search_param': 'keyword',
        'item_selector': 'li.itemCard',
        'title_selector': 'div.itemCard__itemName',
        'price_selector': 'div.g-price',
        'image_selector': 'img.lazyLoadV2.g-thumbnail__image',
        'link_selector': 'a',
        'max_pages': 3,
        'delay_between_pages': 3
    },
    'yahoo_auctions': {
        'base_url': 'https://auctions.yahoo.co.jp/search/search',
        'search_param': 'p',
        'item_selector': 'li.Product',
        'title_selector': 'h3.Product__title',
        'price_selector': 'span.Product__price',
        'image_selector': 'img.Product__image',
        'link_selector': 'a.Product__titleLink',
        'max_pages': 2,
        'delay_between_pages': 4
    }
}

def create_robust_driver(headless: bool = True) -> RobustWebDriver:
    """Factory function to create a robust WebDriver"""
    return RobustWebDriver(headless=headless)

if __name__ == "__main__":
    # Test the robust driver
    driver = create_robust_driver(headless=False)
    
    try:
        success = driver.safe_get("https://buyee.jp")
        if success:
            print("Successfully loaded Buyee homepage")
        else:
            print("Failed to load Buyee homepage")
    finally:
        driver.close()
