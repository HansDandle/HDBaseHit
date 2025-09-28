#!/usr/bin/env python3
"""
Test EPG functionality for different zip codes
Run this to verify EPG configuration works for your area
"""

import sys
from epg_zap2it import fetch_gracenote_epg, detect_headend_id
from config_manager import get_config

def test_epg_for_zip(zip_code):
    """Test EPG functionality for a specific zip code"""
    print(f"\n=== Testing EPG for zip code: {zip_code} ===")
    
    # Test headend detection
    print("1. Testing headend ID detection...")
    headend_id = detect_headend_id(zip_code)
    if headend_id:
        print(f"   ✓ Detected headend ID: {headend_id}")
    else:
        print("   ✗ Could not detect headend ID")
        return False
    
    # Test EPG data fetch
    print("2. Testing EPG data fetch...")
    try:
        results = fetch_gracenote_epg(days=1, zip_code=zip_code, headend_id=headend_id)
        if results and len(results) > 0:
            print(f"   ✓ Retrieved {len(results)} program entries")
            
            # Show some sample data
            print("   Sample listings:")
            for i, entry in enumerate(results[:5]):
                title = entry.get('title', 'Unknown')
                channel = entry.get('channel', 'Unknown')
                start_time = entry.get('start_time', 'Unknown')
                print(f"     {channel}: {title} ({start_time})")
                
            return True
        else:
            print("   ✗ No EPG data retrieved")
            return False
            
    except Exception as e:
        print(f"   ✗ EPG fetch failed: {e}")
        return False

def main():
    """Main test function"""
    print("TV Recorder EPG Test Utility")
    print("=" * 40)
    
    # Test with current configuration
    config = get_config()
    current_zip = config.get_epg_config()['zip_code']
    
    print(f"Testing with configured zip code: {current_zip}")
    success = test_epg_for_zip(current_zip)
    
    if success:
        print(f"\n✓ EPG is working correctly for zip code {current_zip}!")
    else:
        print(f"\n✗ EPG test failed for zip code {current_zip}")
        print("Try running the setup wizard: python setup.py")
    
    # Test with user-provided zip codes
    while True:
        print("\nTest another zip code? (or press Enter to exit)")
        test_zip = input("Enter zip code: ").strip()
        
        if not test_zip:
            break
            
        if len(test_zip) == 5 and test_zip.isdigit():
            test_epg_for_zip(test_zip)
        else:
            print("Please enter a valid 5-digit zip code")
    
    print("\nEPG test complete!")

if __name__ == "__main__":
    main()