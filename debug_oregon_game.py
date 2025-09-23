#!/usr/bin/env python3
"""
Debug script to see what EPG data is available for Saturday Sept 27
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from epg_zap2it import fetch_gracenote_epg
from datetime import datetime, timedelta

def debug_epg_for_date():
    print("🔍 Debugging EPG data for Saturday September 27, 2025...")
    
    # Get EPG data for the next 7 days
    epg_data = fetch_gracenote_epg(days=7)
    
    target_date = "2025-09-27"
    saturday_shows = [show for show in epg_data if show.get('date') == target_date]
    
    print(f"\n📺 Found {len(saturday_shows)} shows on Saturday {target_date}:")
    print("=" * 80)
    
    # Look for anything with "oregon", "football", "game", or sports-related
    sports_keywords = ['oregon', 'football', 'game', 'sports', 'college', 'ncaa', 'vs', 'at']
    
    for show in saturday_shows:
        title = show.get('title', '').lower()
        
        # Check if this might be a sports show
        is_sports_related = any(keyword in title for keyword in sports_keywords)
        
        if is_sports_related:
            print(f"🏈 SPORTS: {show.get('title')} on {show.get('channel')} at {show.get('time')}")
            if show.get('description'):
                print(f"    Description: {show.get('description')}")
        else:
            print(f"📺 {show.get('title')} on {show.get('channel')} at {show.get('time')}")
    
    # Also check for any shows with "oregon" specifically
    print(f"\n🔍 Searching specifically for 'oregon' in all shows:")
    oregon_shows = [show for show in epg_data if 'oregon' in show.get('title', '').lower()]
    
    for show in oregon_shows:
        print(f"🎯 OREGON: {show.get('title')} on {show.get('channel')} at {show.get('time')} on {show.get('date')}")

if __name__ == "__main__":
    debug_epg_for_date()