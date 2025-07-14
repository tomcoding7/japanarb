#!/usr/bin/env python3
"""
Simple test to verify the arbitrage tool works without translation
"""

import logging
from card_arbitrage import CardArbitrageTool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_arbitrage():
    """Test the arbitrage tool with a simple search."""
    
    print("🧪 Testing Arbitrage Tool (No Translation)")
    print("=" * 50)
    
    try:
        # Create arbitrage tool
        tool = CardArbitrageTool()
        
        # Test translation method
        test_text = "青眼の白龍"  # Blue-Eyes White Dragon in Japanese
        translated = tool.translate_text(test_text)
        print(f"✅ Translation test: '{test_text}' -> '{translated}'")
        
        # Test with a simple search
        search_term = "Blue-Eyes White Dragon"
        print(f"\n🔍 Testing search: {search_term}")
        
        # Run a quick test (limited results)
        results = tool.run(search_term, max_results=5)
        
        print(f"✅ Search completed! Found {len(results)} results")
        
        # Clean up
        tool.cleanup()
        
        print("\n🎉 All tests passed! The arbitrage tool is working correctly.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = test_simple_arbitrage()
    if success:
        print("\n🚀 You can now use the web interface!")
        print("📱 Open your browser to: http://localhost:5001")
    else:
        print("\n⚠️  There are still some issues to resolve.") 