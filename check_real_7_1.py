#!/usr/bin/env python3
"""
Check what's ACTUALLY on channel 7.1 on Saturday Sept 27 from the real API
"""

import requests
import json
from datetime import datetime, timezone, timedelta

def check_real_channel_7_1():
    """Check what's actually on channel 7.1 on Saturday Sept 27"""
    print("🔍 Checking REAL data for channel 7.1 on Saturday September 27th...")
    
    # Saturday September 27, 2025 - let's check different times
    times_to_check = [
        ("12:00 PM", 12, 0),  # Noon
        ("3:00 PM", 15, 0),   # 3 PM
        ("6:00 PM", 18, 0),   # 6 PM
        ("6:30 PM", 18, 30),  # 6:30 PM specifically
        ("7:00 PM", 19, 0),   # 7 PM
        ("8:00 PM", 20, 0),   # 8 PM
    ]
    
    url = "https://tvlistings.gracenote.com/api/grid"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://tvlistings.gracenote.com/'
    }
    
    for time_name, hour, minute in times_to_check:
        # Saturday September 27, 2025 at specified time Central
        saturday_time = datetime(2025, 9, 27, hour, minute, 0)
        # Convert to UTC for API (Central Time is UTC-5 in September - Daylight Saving Time)
        saturday_time_utc = saturday_time + timedelta(hours=5)  # Add 5 hours to get UTC
        timestamp = int(saturday_time_utc.timestamp())
        
        print(f"\n📅 Checking {time_name} Central Time (timestamp: {timestamp})...")
        
        params = {
            'lineupId': 'USA-lineupId-DEFAULT',
            'timespan': '2',  # 2 hour window
            'headendId': 'lineupId',
            'country': 'USA',
            'timezone': '',
            'device': '-',
            'postalCode': '78748',
            'isOverride': 'true',
            'time': str(timestamp),
            'pref': '32,256',
            'userId': '-',
            'aid': 'orbebb',
            'languagecode': 'en-us'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Look specifically for channel 7.1
            if 'channels' in data:
                for channel in data['channels']:
                    channel_no = channel.get('channelNo', channel.get('number', 'N/A'))
                    call_sign = channel.get('callSign', '')
                    
                    if channel_no == '7.1':
                        print(f"🎯 Channel 7.1 ({call_sign}) at {time_name}:")
                        
                        if 'events' in channel:
                            for event in channel['events']:
                                program = event.get('program', {})
                                title = program.get('title', 'Unknown')
                                description = program.get('description', '')
                                start_time = event.get('startTime', '')
                                duration = event.get('duration', 0)
                                
                                # Convert timestamp to readable time
                                if start_time:
                                    try:
                                        if 'T' in start_time:
                                            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                        else:
                                            dt = datetime.fromtimestamp(int(start_time))
                                        # Convert to Central Time
                                        central_dt = dt - timedelta(hours=5)  # UTC to Central (during DST)
                                        time_str = central_dt.strftime('%I:%M %p')
                                        date_str = central_dt.strftime('%Y-%m-%d')
                                    except:
                                        time_str = start_time
                                        date_str = 'Unknown'
                                else:
                                    time_str = 'Unknown'
                                    date_str = 'Unknown'
                                
                                print(f"   📺 {title} at {time_str}")
                                if description:
                                    print(f"       Description: {description}")
                                if duration:
                                    print(f"       Duration: {duration} minutes")
                                
                                # Check if this is sports content
                                title_lower = title.lower()
                                desc_lower = description.lower()
                                if ('football' in title_lower or 'football' in desc_lower or
                                    'college' in title_lower or 'college' in desc_lower or
                                    'game' in title_lower or 'sport' in title_lower):
                                    print(f"       🏈 SPORTS CONTENT! ⭐")
                                print()
                        else:
                            print("   No events found")
                        break
                else:
                    print(f"   Channel 7.1 not found in this time window")
                    
        except Exception as e:
            print(f"   ❌ Error checking {time_name}: {e}")

if __name__ == "__main__":
    check_real_channel_7_1()