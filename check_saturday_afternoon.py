#!/usr/bin/env python3
"""
Check what's actually on channel 7.1 throughout Saturday afternoon
"""

import requests
import json
from datetime import datetime, timedelta

def check_saturday_afternoon():
    """Check what's on channel 7.1 throughout Saturday afternoon"""
    print("🔍 Checking what's actually on channel 7.1 throughout Saturday afternoon...")
    
    # Check multiple time windows throughout Saturday afternoon
    times_to_check = [
        ("12:00 PM", 12, 0),
        ("1:00 PM", 13, 0),
        ("2:00 PM", 14, 0),
        ("2:30 PM", 14, 30),
        ("3:00 PM", 15, 0),
        ("4:00 PM", 16, 0),
        ("5:00 PM", 17, 0),
        ("6:00 PM", 18, 0),
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
            
            print(f"\n⏰ {time_name} Central Time:")
            print("-" * 40)
            
            # Look specifically for channel 7.1
            if 'channels' in data:
                found_7_1 = False
                for channel in data['channels']:
                    channel_no = channel.get('channelNo', channel.get('number', 'N/A'))
                    call_sign = channel.get('callSign', '')
                    
                    if channel_no == '7.1':
                        found_7_1 = True
                        if 'events' in channel:
                            for event in channel['events']:
                                program = event.get('program', {})
                                title = program.get('title', 'Unknown')
                                description = program.get('description', program.get('shortDescription', ''))
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
                                    except:
                                        time_str = start_time
                                else:
                                    time_str = 'Unknown'
                                
                                print(f"📺 {title} at {time_str}")
                                if description:
                                    print(f"    📝 {description}")
                                if duration:
                                    print(f"    ⏱️  {duration} minutes")
                                
                                # Check if this is football
                                if 'football' in title.lower() or 'football' in description.lower():
                                    print(f"    🏈 FOOTBALL CONTENT!")
                                    
                                    # Show all available metadata for football content
                                    print(f"    📋 Full metadata:")
                                    for key, value in program.items():
                                        if value and str(value).strip() and value != 'NULL':
                                            print(f"       {key}: {value}")
                                
                                print()
                        else:
                            print("No events found")
                        break
                
                if not found_7_1:
                    print("Channel 7.1 not found in this time window")
            else:
                print("No channels found")
                
        except Exception as e:
            print(f"Error checking {time_name}: {e}")

if __name__ == "__main__":
    check_saturday_afternoon()