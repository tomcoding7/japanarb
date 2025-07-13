#!/usr/bin/env python3
"""
Simple script to run the Yu-Gi-Oh! Arbitrage Bot Web Interface
"""

import sys
import os

def main():
    """Run the web interface"""
    
    print("🚀 Starting Yu-Gi-Oh! Arbitrage Bot Web Interface...")
    print("=" * 60)
    
    # Check if required files exist
    if not os.path.exists('web_interface.py'):
        print("❌ Error: web_interface.py not found!")
        print("Make sure you're in the correct directory.")
        return
    
    if not os.path.exists('templates'):
        print("❌ Error: templates directory not found!")
        print("Make sure the templates directory exists.")
        return
    
    # Try to import required modules
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError:
        print("❌ Error: Flask not installed!")
        print("Run: pip install flask")
        return
    
    try:
        import pandas
        print("✅ Pandas imported successfully")
    except ImportError:
        print("❌ Error: Pandas not installed!")
        print("Run: pip install pandas")
        return
    
    # Try to import the arbitrage tool
    try:
        from card_arbitrage import CardArbitrageTool
        print("✅ Arbitrage tool imported successfully")
    except ImportError as e:
        print(f"⚠️  Warning: Could not import arbitrage tool: {e}")
        print("The web interface will work but searches may fail.")
    
    print("\n🌐 Starting web server...")
    print("📱 Open your browser to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Import and run the web interface
        from web_interface import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("Check that all dependencies are installed:")
        print("pip install -r requirements.txt")

if __name__ == '__main__':
    main() 