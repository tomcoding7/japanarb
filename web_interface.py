#!/usr/bin/env python3
"""
Web Interface for Yu-Gi-Oh! Arbitrage Bot
Provides a clean, visual interface for viewing search results
"""

from flask import Flask, render_template, request, jsonify
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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variable to store latest results
latest_results = None
search_history = []
SAVED_RESULTS_PATH = "saved_results.json"

class WebArbitrageInterface:
    """Web interface for arbitrage results"""
    
    def __init__(self):
        self.results = []
        self.search_terms = []
        self.load_results()
    
    def add_results(self, search_term: str, results: List[Dict]):
        """Add new search results with enhanced image processing"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        enhanced_results = []
        for result in results:
            # Process images for display
            processed_images = self.process_images_for_display(result.get('image_url', ''))
            
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
                           search_term: str = None) -> List[Dict]:
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
                
            filtered.append(result)
        
        return filtered
    
    def get_stats(self) -> Dict:
        """Get summary statistics"""
        if not self.results:
            return {
                'total_listings': 0,
                'profitable_listings': 0,
                'strong_buys': 0,
                'buys': 0,
                'considers': 0,
                'avg_score': 0,
                'avg_profit_margin': 0,
                'total_profit_potential': 0
            }
        
        df = pd.DataFrame(self.results)
        
        # Convert Decimal to float for calculations
        df['profit_margin'] = df['profit_margin'].astype(float)
        df['arbitrage_score'] = df['arbitrage_score'].astype(float)
        
        return {
            'total_listings': len(df),
            'profitable_listings': len(df[df['profit_margin'] > 0]),
            'strong_buys': len(df[df['recommended_action'] == 'STRONG BUY']),
            'buys': len(df[df['recommended_action'] == 'BUY']),
            'considers': len(df[df['recommended_action'] == 'CONSIDER']),
            'avg_score': round(df['arbitrage_score'].mean(), 2),
            'avg_profit_margin': round(df['profit_margin'].mean(), 2),
            'total_profit_potential': round(df['profit_margin'].sum(), 2)
        }

    def process_images_for_display(self, image_url: str) -> List[Dict[str, Any]]:
        """Process image URL for optimal display in the web interface"""
        processed_images = []
        
        if not image_url or 'noimage' in image_url.lower():
            return processed_images
        
        try:
            # Create processed image info
            processed_img = {
                'url': image_url,
                'index': 0,
                'processed_url': self.process_image_url(image_url),
                'thumbnail_url': self.create_thumbnail_url(image_url),
                'is_valid': True,
                'display_url': self.get_display_url(image_url)
            }
            
            processed_images.append(processed_img)
            
        except Exception as e:
            logger.warning(f"Error processing image {image_url}: {str(e)}")
        
        return processed_images

    def process_image_url(self, url: str) -> str:
        """Process image URL to ensure it's accessible"""
        try:
            # Handle relative URLs
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = 'https://buyee.jp' + url
            
            # Handle Buyee CDN URLs
            if 'buyee.jp' in url and 'cdn' not in url:
                # Try to convert to CDN URL if possible
                url = url.replace('buyee.jp', 'buyee.jp/cdn')
            
            return url
            
        except Exception as e:
            logger.warning(f"Error processing image URL {url}: {str(e)}")
            return url

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
            # Try processed URL first
            processed_url = self.process_image_url(image_url)
            if processed_url != image_url:
                return processed_url
            
            # Fall back to original URL
            return image_url
            
        except Exception as e:
            logger.warning(f"Error getting display URL for {image_url}: {str(e)}")
            return image_url

    def get_best_display_image(self, processed_images: List[Dict[str, Any]]) -> str:
        """Get the best image URL for primary display"""
        try:
            if not processed_images:
                return ""
            
            # Prefer processed URLs
            for img in processed_images:
                if img.get('processed_url') and img['processed_url'] != img.get('url'):
                    return img['processed_url']
            
            # Fall back to first valid image
            return processed_images[0].get('display_url', '')
            
        except Exception as e:
            logger.warning(f"Error getting best display image: {str(e)}")
            return ""

# Global interface instance
interface = WebArbitrageInterface()

def auto_search_loop(interface, interval_minutes=60):
    tool = CardArbitrageTool()
    while True:
        for term in SEARCH_TERMS:
            logger.info(f"[AutoSearch] Searching for: {term}")
            try:
                results = tool.run(term, max_results=20)
                interface.add_results(term, results)
                time.sleep(5)  # Short pause between terms
            except Exception as e:
                logger.error(f"[AutoSearch] Error searching for {term}: {e}")
        logger.info(f"[AutoSearch] Sleeping for {interval_minutes} minutes...")
        time.sleep(interval_minutes * 60)

# Start auto-search in background after interface is created
threading.Thread(target=auto_search_loop, args=(interface, 60), daemon=True).start()

@app.route('/')
def index():
    """Main dashboard page"""
    stats = interface.get_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/search')
def search_page():
    """Search page"""
    return render_template('search.html')

@app.route('/results')
def results_page():
    """Results page with filtering"""
    return render_template('results.html')

@app.route('/result/<result_id>')
def result_detail(result_id):
    """Detailed view for a single result"""
    # Find the result by id
    result = next((r for r in interface.results if r.get('id') == result_id), None)
    if not result:
        return render_template('detail.html', error='Result not found', result=None)
    return render_template('detail.html', result=result)

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for running searches"""
    try:
        data = request.get_json()
        search_term = data.get('search_term', '')
        max_results = data.get('max_results', 20)
        search_all = data.get('search_all', False)

        # Import here to avoid circular imports
        from card_arbitrage import CardArbitrageTool
        from enhanced_buyee_scraper import EnhancedBuyeeScraper
        results = []
        if search_all:
            # Use category-wide search for 'yugioh' (can be expanded)
            scraper = EnhancedBuyeeScraper(output_dir='enhanced_scraped_results', max_pages=5, headless=True, use_llm=False)
            category_urls = scraper.get_category_urls('yugioh')
            for category_url in category_urls:
                results.extend(scraper.search_by_category(category_url))
            # Optionally limit results
            results = results[:max_results]
            scraper.close()
            interface.add_results('ALL_CATEGORY', results)
            return jsonify({
                'success': True,
                'message': f'Found {len(results)} results for category-wide search',
                'results_count': len(results)
            })
        else:
            tool = CardArbitrageTool()
            results = tool.run(search_term, max_results=max_results)
            interface.add_results(search_term, results)
            return jsonify({
                'success': True,
                'message': f'Found {len(results)} results for "{search_term}"',
                'results_count': len(results)
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
        
        results = interface.get_filtered_results(
            min_score=min_score,
            max_price=max_price,
            min_profit=min_profit,
            action_filter=action_filter if action_filter else None,
            search_term=search_term if search_term else None
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
    """API endpoint for getting search terms"""
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

if __name__ == '__main__':
    print("Starting Yu-Gi-Oh! Arbitrage Bot Web Interface...")
    print("Open your browser to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 