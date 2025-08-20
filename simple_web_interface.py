#!/usr/bin/env python3
"""
Simple Web Interface - No background threads, clean startup
"""

from flask import Flask, render_template, request, jsonify
import logging
from datetime import datetime
from buyee_cdn_scraper import BuyeeCDNScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Initialize scraper
scraper = BuyeeCDNScraper()

# Simple in-memory storage
results_storage = []

@app.route('/')
def dashboard():
    """Main dashboard"""
    try:
        return render_template('dashboard.html', results=results_storage[-20:])  # Show last 20
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return f"""
        <html>
        <head><title>Japan Arbitrage Bot</title></head>
        <body>
            <h1>🎌 Japan Arbitrage Bot</h1>
            <p>✅ Bot is running with Buyee CDN support!</p>
            <p>🖼️ Real thumbnails from accessible Buyee CDN</p>
            <form action="/search" method="post">
                <input type="text" name="search_term" placeholder="Enter Japanese search term" required>
                <button type="submit">Search</button>
            </form>
            <h3>Recent Results: {len(results_storage)}</h3>
            <ul>
            {''.join([f'<li>{r["title"]} - ¥{r["price_yen"]:,}</li>' for r in results_storage[-10:]])}
            </ul>
        </body>
        </html>
        """

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search page"""
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        if search_term:
            try:
                logger.info(f"Searching for: {search_term}")
                results = scraper.smart_search(search_term, max_results=10)
                
                # Add timestamp and store
                for result in results:
                    result['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    result['search_term'] = search_term
                
                results_storage.extend(results)
                
                logger.info(f"Found {len(results)} results")
                
                return render_template('results.html', 
                                     results=results, 
                                     search_term=search_term)
            except Exception as e:
                logger.error(f"Search error: {e}")
                return f"<h1>Search Error</h1><p>{e}</p><a href='/'>Back</a>"
    
    try:
        return render_template('search.html')
    except Exception as e:
        return f"""
        <html>
        <head><title>Search</title></head>
        <body>
            <h1>🔍 Search Japanese Cards</h1>
            <form action="/search" method="post">
                <input type="text" name="search_term" placeholder="Enter Japanese search term (e.g. 遊戯王 青眼の白龍)" required>
                <button type="submit">Search with Buyee CDN</button>
            </form>
            <h3>Popular Terms:</h3>
            <ul>
                <li>遊戯王 青眼の白龍 (Yu-Gi-Oh Blue-Eyes)</li>
                <li>ポケモンカード リーリエ (Pokemon Lillie)</li>
                <li>ワンピース カード (One Piece Cards)</li>
            </ul>
            <a href="/">Back to Dashboard</a>
        </body>
        </html>
        """

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for search"""
    try:
        data = request.get_json()
        search_term = data.get('search_term', '')
        max_results = data.get('max_results', 10)
        
        if not search_term:
            return jsonify({'error': 'Search term required'}), 400
        
        logger.info(f"API search for: {search_term}")
        results = scraper.smart_search(search_term, max_results)
        
        # Add to storage
        for result in results:
            result['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result['search_term'] = search_term
        
        results_storage.extend(results)
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"API search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def results():
    """Show all results"""
    try:
        return render_template('results.html', 
                             results=results_storage[-50:],  # Last 50 results
                             search_term="All Results")
    except Exception as e:
        return f"""
        <html>
        <head><title>Results</title></head>
        <body>
            <h1>📊 All Results ({len(results_storage)})</h1>
            <ul>
            {''.join([f'''
                <li>
                    <strong>{r["title"]}</strong><br>
                    💰 ¥{r["price_yen"]:,} | 
                    📊 Score: {r["arbitrage_score"]}/100 | 
                    🎯 {r["recommended_action"]} |
                    🖼️ {'✅' if r.get("image_url") else '❌'}
                    {f'<br><img src="{r["image_url"]}" style="max-width:150px">' if r.get("image_url") else ''}
                </li>
            ''' for r in results_storage[-20:]])}
            </ul>
            <a href="/">Back to Dashboard</a>
        </body>
        </html>
        """

if __name__ == '__main__':
    print("🎌 Starting Simple Japan Arbitrage Bot...")
    print("✅ Using Buyee CDN for accessible thumbnails")
    print("🌐 Open your browser to: http://localhost:5000")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Failed to start web interface: {e}")
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")
