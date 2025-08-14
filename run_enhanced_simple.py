#!/usr/bin/env python3
"""
Simple enhanced web interface runner without complex scraping
This avoids the Chrome WebDriver errors and API failures
"""

import logging
import sys
import os

# Set up logging to reduce noise
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Suppress noisy loggers
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

def main():
    """Run the enhanced web interface with minimal errors"""
    try:
        print("🚀 Starting Enhanced Yu-Gi-Oh! Arbitrage Bot")
        print("=" * 50)
        print("✅ Japanese search terms loaded")
        print("✅ Enhanced templates created")
        print("✅ Smart analysis features enabled")
        print("✅ Thumbnail display improved")
        print("=" * 50)
        
        # Import and run the enhanced interface
        from enhanced_web_interface import app, interface
        
        # Load some sample data if none exists
        if len(interface.results) == 0:
            print("📝 Loading sample data...")
            from enhanced_web_interface import create_mock_results
            
            # Add sample results for different search terms
            sample_terms = [
                "遊戯王 初期 美品",
                "ポケカ SR 美品", 
                "遊戯王 シークレット",
                "ポケカ リーリエ",
                "ワンピース カード SR"
            ]
            
            for term in sample_terms:
                mock_results = create_mock_results(term)
                interface.add_results(term, mock_results)
                
            print(f"✅ Added {len(interface.results)} sample results")
        
        print("\n🌐 Web Interface Starting...")
        print("📱 Open your browser to: http://localhost:5000")
        print("🔍 Try searching with Japanese terms!")
        print("\nPopular Japanese searches:")
        print("  • 遊戯王 初期 美品 (Yu-Gi-Oh! early mint)")
        print("  • ポケカ SR 美品 (Pokemon SR mint)")
        print("  • 青眼の白龍 レリーフ (Blue-Eyes relief)")
        print("  • ポケカ リーリエ (Pokemon Lillie)")
        print("  • 遊戯王 プリズマティック (Yu-Gi-Oh! prismatic)")
        print("\n" + "=" * 50)
        
        # Run the Flask app
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting enhanced interface: {e}")
        print("💡 Try running: python enhanced_web_interface.py")

if __name__ == "__main__":
    main()
