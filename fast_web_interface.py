#!/usr/bin/env python3
"""
Fast Web Interface for Ultra-Fast Arbitrage Bot
Focuses on speed and real value - what you can't do manually
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import logging
import time
import threading
from datetime import datetime
import os
from typing import List, Dict
from ultra_fast_arbitrage import UltraFastArbitrage, ArbitrageOpportunity

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variables
arbitrage_bot = UltraFastArbitrage()
latest_opportunities = []
search_history = []

class FastArbitrageInterface:
    """Fast interface for arbitrage opportunities"""
    
    def __init__(self):
        self.opportunities = []
        self.search_terms = []
        self.last_update = None
        
    def add_opportunities(self, opportunities: List[ArbitrageOpportunity]):
        """Add new opportunities"""
        self.opportunities.extend(opportunities)
        self.last_update = datetime.now()
        
    def get_filtered_opportunities(self, 
                                 min_profit: float = 0,
                                 max_risk: float = 1.0,
                                 min_price: float = 0,
                                 source_filter: str = None) -> List[Dict]:
        """Get filtered opportunities"""
        filtered = []
        
        for opp in self.opportunities:
            # Profit filter
            if opp.profit_margin < min_profit:
                continue
                
            # Risk filter
            if opp.risk_score > max_risk:
                continue
                
            # Price filter
            if opp.international_price < min_price:
                continue
                
            # Source filter
            if source_filter and source_filter not in opp.source_url:
                continue
                
            # Convert to dict for JSON serialization
            opp_dict = {
                'title': opp.title,
                'japanese_price': opp.japanese_price,
                'international_price': opp.international_price,
                'profit_margin': opp.profit_margin,
                'risk_score': opp.risk_score,
                'image_url': opp.image_url,
                'source_url': opp.source_url,
                'condition': opp.condition,
                'rarity': opp.rarity,
                'confidence': opp.confidence,
                'time_to_expire': opp.time_to_expire,
                'seller_rating': opp.seller_rating,
                'shipping_cost': opp.shipping_cost,
                'import_tax': opp.import_tax,
                'total_cost': opp.japanese_price * 0.0067 + opp.shipping_cost + opp.import_tax,
                'net_profit': opp.international_price - (opp.japanese_price * 0.0067 + opp.shipping_cost + opp.import_tax)
            }
            
            filtered.append(opp_dict)
        
        # Sort by profit margin (highest first)
        filtered.sort(key=lambda x: x['profit_margin'], reverse=True)
        
        return filtered
    
    def get_stats(self) -> Dict:
        """Get summary statistics"""
        if not self.opportunities:
            return {
                'total_opportunities': 0,
                'high_profit_opportunities': 0,
                'avg_profit_margin': 0,
                'total_profit_potential': 0,
                'urgent_opportunities': 0
            }
        
        high_profit = [opp for opp in self.opportunities if opp.profit_margin > 50]
        urgent = [opp for opp in self.opportunities if opp.time_to_expire and opp.time_to_expire < 3600]
        
        total_profit_potential = sum(
            opp.international_price - (opp.japanese_price * 0.0067 + opp.shipping_cost + opp.import_tax)
            for opp in self.opportunities
        )
        
        return {
            'total_opportunities': len(self.opportunities),
            'high_profit_opportunities': len(high_profit),
            'avg_profit_margin': sum(opp.profit_margin for opp in self.opportunities) / len(self.opportunities),
            'total_profit_potential': total_profit_potential,
            'urgent_opportunities': len(urgent),
            'last_update': self.last_update.isoformat() if self.last_update else None
        }

# Global interface instance
interface = FastArbitrageInterface()

def background_search_loop():
    """Background search loop for continuous monitoring"""
    search_terms = [
        '青眼の白龍 シークレット',
        'ブラック・マジシャン ウルトラ',
        'エクゾディア 1st',
        '真紅眼の黒竜 レリーフ',
        '千年パズル ゴースト',
        '遊戯王 初期 美品',
        'ポケモン シャドウレス チャリザード',
        'ワンピース ルフィ SEC'
    ]
    
    while True:
        try:
            logger.info("Starting background search...")
            opportunities = arbitrage_bot.ultra_fast_search(search_terms, max_results=30)
            interface.add_opportunities(opportunities)
            logger.info(f"Background search completed: {len(opportunities)} opportunities found")
            
            # Wait 5 minutes before next search
            time.sleep(300)
            
        except Exception as e:
            logger.error(f"Background search error: {e}")
            time.sleep(60)

# Start background search
threading.Thread(target=background_search_loop, daemon=True).start()

@app.route('/')
def index():
    """Main dashboard"""
    stats = interface.get_stats()
    return render_template('fast_dashboard.html', stats=stats)

@app.route('/opportunities')
def opportunities_page():
    """Opportunities page"""
    return render_template('fast_opportunities.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for manual search"""
    try:
        data = request.get_json()
        search_terms = data.get('search_terms', [])
        
        if not search_terms:
            return jsonify({
                'success': False,
                'message': 'Search terms are required'
            }), 400
        
        logger.info(f"Manual search for: {search_terms}")
        
        # Perform ultra-fast search
        opportunities = arbitrage_bot.ultra_fast_search(search_terms, max_results=20)
        interface.add_opportunities(opportunities)
        
        return jsonify({
            'success': True,
            'message': f'Found {len(opportunities)} opportunities',
            'opportunities_count': len(opportunities)
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/opportunities')
def api_opportunities():
    """API endpoint for getting opportunities"""
    try:
        min_profit = float(request.args.get('min_profit', 0))
        max_risk = float(request.args.get('max_risk', 1.0))
        min_price = float(request.args.get('min_price', 0))
        source_filter = request.args.get('source_filter', '')
        
        opportunities = interface.get_filtered_opportunities(
            min_profit=min_profit,
            max_risk=max_risk,
            min_price=min_price,
            source_filter=source_filter if source_filter else None
        )
        
        return jsonify({
            'success': True,
            'opportunities': opportunities,
            'total': len(opportunities)
        })
        
    except Exception as e:
        logger.error(f"Opportunities error: {e}")
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

@app.route('/api/urgent')
def api_urgent():
    """API endpoint for urgent opportunities"""
    try:
        urgent = [opp for opp in interface.opportunities if opp.time_to_expire and opp.time_to_expire < 3600]
        
        urgent_dicts = []
        for opp in urgent:
            opp_dict = {
                'title': opp.title,
                'japanese_price': opp.japanese_price,
                'international_price': opp.international_price,
                'profit_margin': opp.profit_margin,
                'time_to_expire': opp.time_to_expire,
                'source_url': opp.source_url,
                'image_url': opp.image_url
            }
            urgent_dicts.append(opp_dict)
        
        return jsonify({
            'success': True,
            'urgent': urgent_dicts,
            'count': len(urgent_dicts)
        })
        
    except Exception as e:
        logger.error(f"Urgent error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Ultra-Fast Arbitrage Bot Web Interface...")
    print("⚡ Optimized for speed and real value")
    print("🌐 Open your browser to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

