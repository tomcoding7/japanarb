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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variable to store latest results
latest_results = None
search_history = []

class WebArbitrageInterface:
    """Web interface for arbitrage results"""
    
    def __init__(self):
        self.results = []
        self.search_terms = []
    
    def add_results(self, search_term: str, results: List[Dict]):
        """Add new search results"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for result in results:
            result['search_term'] = search_term
            result['timestamp'] = timestamp
            result['id'] = f"{search_term}_{len(self.results)}"
        
        self.results.extend(results)
        if search_term not in self.search_terms:
            self.search_terms.append(search_term)
    
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

# Global interface instance
interface = WebArbitrageInterface()

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

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for running searches"""
    try:
        data = request.get_json()
        search_term = data.get('search_term', '')
        max_results = data.get('max_results', 20)
        
        # Import here to avoid circular imports
        from card_arbitrage import CardArbitrageTool
        tool = CardArbitrageTool()
        results = tool.run(search_term, max_results=max_results)
        
        # Add to interface
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