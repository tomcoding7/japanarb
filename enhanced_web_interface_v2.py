#!/usr/bin/env python3
"""
Enhanced Web Interface v2 for Yu-Gi-Oh! Arbitrage Bot
Provides a superior experience compared to searching Buyee manually
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import json
import logging
from datetime import datetime
import os
from typing import List, Dict, Any
import decimal
import threading
import time
from card_arbitrage import CardArbitrageTool
from search_terms import SEARCH_TERMS
import requests
from PIL import Image
import io
import base64
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variables
latest_results = None
search_history = []
SAVED_RESULTS_PATH = "enhanced_v2_saved_results.json"
CACHE_DIR = "image_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

class EnhancedWebArbitrageInterfaceV2:
    """Enhanced web interface with superior image handling and display"""
    
    def __init__(self):
        self.results = []
        self.search_terms = []
        self.load_results()
    
    def add_results(self, search_term: str, results: List[Dict]):
        """Add new search results with enhanced processing"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        enhanced_results = []
        for result in results:
            # Process images
            processed_images = self.process_images_for_display(result.get('images', []))
            
            # Enhanced result with processed images
            enhanced_result = {
                **result,
                'search_term': search_term,
                'timestamp': timestamp,
                'id': f"{search_term}_{len(self.results)}",
                'processed_images': processed_images,
                'display_image': self.get_best_display_image(processed_images),
                'image_count': len(processed_images),
                'has_images': len(processed_images) > 0
            }
            
            enhanced_results.append(enhanced_result)
        
        self.results.extend(enhanced_results)
        if search_term not in self.search_terms:
            self.search_terms.append(search_term)
        self.save_results()
    
    def process_images_for_display(self, images: List[Any]) -> List[Dict[str, Any]]:
        """Process images for optimal display in the web interface"""
        processed_images = []
        
        for i, img in enumerate(images):
            try:
                if isinstance(img, str):
                    # Handle string URLs
                    img_url = img
                    img_data = {'url': img_url}
                elif isinstance(img, dict):
                    # Handle dictionary image data
                    img_url = img.get('url', img.get('processed_url', ''))
                    img_data = img
                else:
                    continue
                
                if not img_url or 'noimage' in img_url.lower():
                    continue
                
                # Create processed image info
                processed_img = {
                    'url': img_url,
                    'index': i,
                    'cached_url': self.cache_image(img_url),
                    'thumbnail_url': self.create_thumbnail_url(img_url),
                    'is_valid': True,
                    'display_url': self.get_display_url(img_url)
                }
                
                processed_images.append(processed_img)
                
            except Exception as e:
                logger.warning(f"Error processing image {i}: {str(e)}")
                continue
        
        return processed_images
    
    def cache_image(self, image_url: str) -> str:
        """Cache an image locally and return the cached path"""
        try:
            # Create a hash of the URL for the filename
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            file_extension = self.get_file_extension(image_url)
            cache_filename = f"{url_hash}{file_extension}"
            cache_path = os.path.join(CACHE_DIR, cache_filename)
            
            # Check if already cached
            if os.path.exists(cache_path):
                return f"/cache/{cache_filename}"
            
            # Download and cache the image
            response = requests.get(image_url, timeout=10, stream=True)
            if response.status_code == 200:
                with open(cache_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return f"/cache/{cache_filename}"
            
            return image_url
            
        except Exception as e:
            logger.warning(f"Error caching image {image_url}: {str(e)}")
            return image_url
    
    def get_file_extension(self, url: str) -> str:
        """Get file extension from URL"""
        try:
            # Try to get extension from URL
            if '.' in url:
                ext = url.split('.')[-1].split('?')[0].split('#')[0]
                if ext.lower() in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    return f".{ext.lower()}"
            
            # Default to .jpg
            return ".jpg"
        except Exception:
            return ".jpg"
    
    def create_thumbnail_url(self, image_url: str) -> str:
        """Create a thumbnail URL for the image"""
        try:
            # For Buyee images, try to get thumbnail version
            if 'buyee.jp' in image_url:
                # Try different thumbnail patterns
                thumbnail_patterns = [
                    image_url.replace('/original/', '/thumbnail/'),
                    image_url.replace('/large/', '/thumbnail/'),
                    image_url + '?size=thumbnail',
                    image_url + '&size=thumbnail'
                ]
                
                for pattern in thumbnail_patterns:
                    try:
                        response = requests.head(pattern, timeout=3)
                        if response.status_code == 200:
                            return pattern
                    except Exception:
                        continue
            
            return image_url
            
        except Exception as e:
            logger.warning(f"Error creating thumbnail URL for {image_url}: {str(e)}")
            return image_url
    
    def get_display_url(self, image_url: str) -> str:
        """Get the best URL for display"""
        try:
            # Try cached version first
            cached_url = self.cache_image(image_url)
            if cached_url.startswith('/cache/'):
                return cached_url
            
            # Fall back to original URL
            return image_url
            
        except Exception as e:
            logger.warning(f"Error getting display URL for {image_url}: {str(e)}")
            return image_url
    
    def get_best_display_image(self, processed_images: List[Dict[str, Any]]) -> str:
        """Get the best image for display"""
        try:
            if not processed_images:
                return ""
            
            # Prefer cached images
            for img in processed_images:
                if img.get('cached_url', '').startswith('/cache/'):
                    return img['cached_url']
            
            # Fall back to first valid image
            return processed_images[0].get('display_url', '')
            
        except Exception as e:
            logger.warning(f"Error getting best display image: {str(e)}")
            return ""

    def save_results(self):
        def convert(obj):
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert(i) for i in obj]
            return obj
        try:
            with open(SAVED_RESULTS_PATH, 'w', encoding='utf-8') as f:
                json.dump(convert(self.results), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving results to disk: {e}")

    def load_results(self):
        def convert(obj):
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert(i) for i in obj]
            if isinstance(obj, str) and obj.replace('.', '').replace('-', '').isdigit():
                try:
                    return float(obj)
                except:
                    return obj
            return obj
            
        try:
            if os.path.exists(SAVED_RESULTS_PATH):
                with open(SAVED_RESULTS_PATH, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                self.results = convert(loaded_data)
                logger.info(f"Loaded {len(self.results)} results from disk.")
        except Exception as e:
            logger.error(f"Error loading results from disk: {e}")
    
    def get_filtered_results(self, 
                           min_score: float = 0,
                           max_price: float = None,
                           min_profit: float = 0,
                           action_filter: str = None,
                           search_term: str = None,
                           has_images: bool = None,
                           condition_filter: str = None) -> List[Dict]:
        """Get filtered results based on criteria"""
        filtered = []
        
        for result in self.results:
            # Score filter
            if result.get('arbitrage_score', 0) < min_score:
                continue
                
            # Price filter
            if max_price and result.get('price_usd', 0) > max_price:
                continue
                
            # Profit filter
            if result.get('profit_margin', 0) < min_profit:
                continue
                
            # Action filter
            if action_filter and result.get('recommended_action') != action_filter:
                continue
                
            # Search term filter
            if search_term and result.get('search_term') != search_term:
                continue
            
            # Image filter
            if has_images is not None:
                if has_images and not result.get('has_images', False):
                    continue
                if not has_images and result.get('has_images', False):
                    continue
            
            # Condition filter
            if condition_filter and result.get('condition', '').lower() != condition_filter.lower():
                continue
                
            filtered.append(result)
        
        return filtered
    
    def get_stats(self) -> Dict:
        """Get summary statistics"""
        if not self.results:
            return {
                'total_listings': 0,
                'profitable_listings': 0,
                'strong_buys': 0,
                'avg_score': 0,
                'avg_profit_margin': 0,
                'total_value': 0,
                'items_with_images': 0
            }
        
        profitable = [r for r in self.results if r.get('profit_margin', 0) > 0]
        strong_buys = [r for r in self.results if r.get('recommended_action') == 'STRONG BUY']
        items_with_images = [r for r in self.results if r.get('has_images', False)]
        
        return {
            'total_listings': len(self.results),
            'profitable_listings': len(profitable),
            'strong_buys': len(strong_buys),
            'avg_score': round(sum(r.get('arbitrage_score', 0) for r in self.results) / len(self.results), 1),
            'avg_profit_margin': round(sum(r.get('profit_margin', 0) for r in self.results) / len(self.results), 1),
            'total_value': sum(r.get('price_usd', 0) for r in self.results),
            'items_with_images': len(items_with_images)
        }

# Initialize interface
interface = EnhancedWebArbitrageInterfaceV2()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('enhanced_dashboard_v2.html')

@app.route('/cache/<path:filename>')
def cached_image(filename):
    """Serve cached images"""
    return send_from_directory(CACHE_DIR, filename)

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for starting a new search"""
    try:
        data = request.get_json()
        search_term = data.get('search_term', '')
        
        if not search_term:
            return jsonify({
                'success': False,
                'message': 'Search term is required'
            }), 400
        
        # Start search in background thread
        def run_search():
            try:
                from enhanced_buyee_scraper import EnhancedBuyeeScraper
                
                with EnhancedBuyeeScraper(headless=True, use_llm=False) as scraper:
                    results = scraper.search_items(search_term)
                    interface.add_results(search_term, results)
                    
            except Exception as e:
                logger.error(f"Search error: {e}")
        
        thread = threading.Thread(target=run_search)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Search started for "{search_term}"'
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/results')
def api_results():
    """API endpoint for getting filtered results"""
    try:
        min_score = float(request.args.get('min_score', 0))
        max_price = float(request.args.get('max_price', 0)) if request.args.get('max_price') else None
        min_profit = float(request.args.get('min_profit', 0))
        action_filter = request.args.get('action_filter', '')
        search_term = request.args.get('search_term', '')
        has_images = request.args.get('has_images')
        condition_filter = request.args.get('condition_filter', '')
        
        # Convert has_images string to boolean
        has_images_bool = None
        if has_images == 'true':
            has_images_bool = True
        elif has_images == 'false':
            has_images_bool = False
        
        results = interface.get_filtered_results(
            min_score=min_score,
            max_price=max_price,
            min_profit=min_profit,
            action_filter=action_filter if action_filter else None,
            search_term=search_term if search_term else None,
            has_images=has_images_bool,
            condition_filter=condition_filter if condition_filter else None
        )
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"Results error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for getting statistics"""
    try:
        stats = interface.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/search_terms')
def api_search_terms():
    """API endpoint for getting available search terms"""
    try:
        return jsonify({
            'success': True,
            'search_terms': interface.search_terms
        })
    except Exception as e:
        logger.error(f"Search terms error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/result/<result_id>')
def result_detail(result_id):
    """Detail page for a specific result"""
    try:
        # Find the result by ID
        result = None
        for r in interface.results:
            if r.get('id') == result_id:
                result = r
                break
        
        if not result:
            return "Result not found", 404
        
        return render_template('enhanced_detail_v2.html', result=result)
        
    except Exception as e:
        logger.error(f"Detail page error: {e}")
        return "Error loading result", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
