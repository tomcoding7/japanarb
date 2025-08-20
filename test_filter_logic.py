#!/usr/bin/env python3
"""
Test Filter Logic
Tests the finished auction filtering logic with sample data
"""

import sys
import os
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_filter_logic():
    """Test the finished auction filtering logic with sample data"""
    print("=" * 60)
    print("Testing Finished Auction Filter Logic")
    print("Testing with sample data to verify filtering works")
    print("=" * 60)
    
    # Sample auction data
    sample_auctions = [
        {
            'title': 'Blue-Eyes White Dragon LOB-001 1st Edition PSA 10',
            'status': 'Active',
            'should_filter': False
        },
        {
            'title': 'Dark Magician SDY-006 Near Mint - Finished',
            'status': 'Finished',
            'should_filter': True
        },
        {
            'title': 'Red-Eyes Black Dragon SDJ-001 Secret Rare',
            'status': 'Active',
            'should_filter': False
        },
        {
            'title': 'Exodia the Forbidden One LOB-124 - Ended',
            'status': 'Ended',
            'should_filter': True
        },
        {
            'title': 'Summoned Skull MRD-003 - 終了',
            'status': '終了',
            'should_filter': True
        },
        {
            'title': 'Blue-Eyes Ultimate Dragon JUMP-EN049',
            'status': 'Active',
            'should_filter': False
        },
        {
            'title': 'Chaos Emperor Dragon IOC-000 - Closed',
            'status': 'Closed',
            'should_filter': True
        },
        {
            'title': 'Black Luster Soldier YMA-EN001',
            'status': 'Active',
            'should_filter': False
        }
    ]
    
    # Test the filtering logic
    from card_arbitrage import CardArbitrageTool
    
    tool = CardArbitrageTool()
    
    print("Testing finished auction detection:")
    print()
    
    filtered_count = 0
    passed_count = 0
    
    for i, auction in enumerate(sample_auctions, 1):
        print(f"Test {i}: {auction['title']}")
        print(f"  Status: {auction['status']}")
        print(f"  Should filter: {auction['should_filter']}")
        
        # Create a mock element with the title text
        class MockElement:
            def __init__(self, text):
                self.text = text
            
            def find_element(self, *args, **kwargs):
                raise Exception("Not implemented")
            
            def find_elements(self, *args, **kwargs):
                return []
        
        mock_element = MockElement(auction['title'])
        
        # Test the filtering logic
        try:
            is_finished = tool.is_finished_auction(mock_element)
            print(f"  Detected as finished: {is_finished}")
            
            if is_finished == auction['should_filter']:
                print(f"  ✓ CORRECT")
                passed_count += 1
            else:
                print(f"  ❌ INCORRECT - Expected {auction['should_filter']}, got {is_finished}")
            
            if is_finished:
                filtered_count += 1
                
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
        
        print()
    
    print("=" * 40)
    print("Filter Logic Test Results:")
    print(f"  Total tests: {len(sample_auctions)}")
    print(f"  Passed: {passed_count}")
    print(f"  Failed: {len(sample_auctions) - passed_count}")
    print(f"  Would be filtered: {filtered_count}")
    print(f"  Would pass through: {len(sample_auctions) - filtered_count}")
    
    if passed_count == len(sample_auctions):
        print("  ✓ All tests passed!")
    else:
        print("  ❌ Some tests failed")
    
    print("=" * 40)
    
    return passed_count == len(sample_auctions)

def test_image_extraction_logic():
    """Test the image extraction logic with sample data"""
    print("\n" + "=" * 60)
    print("Testing Image Extraction Logic")
    print("=" * 60)
    
    # Sample image data
    sample_images = [
        {
            'url': 'https://buyee.jp/item/image/12345.jpg',
            'expected': 'https://buyee.jp/item/image/12345.jpg'
        },
        {
            'url': '//buyee.jp/cdn/image/67890.jpg',
            'expected': 'https://buyee.jp/cdn/image/67890.jpg'
        },
        {
            'url': '/item/image/11111.jpg',
            'expected': 'https://buyee.jp/item/image/11111.jpg'
        },
        {
            'url': 'https://buyee.jp/item/image/22222.jpg',
            'expected': 'https://buyee.jp/cdn/item/image/22222.jpg'
        }
    ]
    
    from card_arbitrage import CardArbitrageTool
    
    tool = CardArbitrageTool()
    
    print("Testing image URL processing:")
    print()
    
    passed_count = 0
    
    for i, image in enumerate(sample_images, 1):
        print(f"Test {i}: {image['url']}")
        
        try:
            processed_url = tool.process_image_url(image['url'])
            print(f"  Processed: {processed_url}")
            print(f"  Expected:  {image['expected']}")
            
            if processed_url == image['expected']:
                print(f"  ✓ CORRECT")
                passed_count += 1
            else:
                print(f"  ❌ INCORRECT")
                
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
        
        print()
    
    print("=" * 40)
    print("Image Processing Test Results:")
    print(f"  Total tests: {len(sample_images)}")
    print(f"  Passed: {passed_count}")
    print(f"  Failed: {len(sample_images) - passed_count}")
    
    if passed_count == len(sample_images):
        print("  ✓ All tests passed!")
    else:
        print("  ❌ Some tests failed")
    
    print("=" * 40)
    
    return passed_count == len(sample_images)

def main():
    """Main test function"""
    print("Filter Logic Test Suite")
    print("Testing finished auction filtering and image processing logic")
    print()
    
    # Test filter logic
    filter_result = test_filter_logic()
    
    # Test image extraction logic
    image_result = test_image_extraction_logic()
    
    if filter_result and image_result:
        print("\n🎉 All logic tests completed successfully!")
        print("The filtering and image processing logic is working correctly.")
        print("The issue may be with the website scraping itself.")
        return 0
    else:
        print("\n❌ Some logic tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())

