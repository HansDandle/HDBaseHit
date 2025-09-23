#!/usr/bin/env python3
"""
Check detailed metadata for the College Football game at 2:30 PM on Saturday Sept 27
"""

import requests
import json
from datetime import datetime, timedelta

def check_football_metadata():
    """Check what metadata is available for the 2:30 PM football game"""
    print("🔍 Checking detailed metadata for College Football at 2:30 PM on Saturday Sept 27...")
    
    # Saturday September 27, 2025 at 2:30 PM Central Time
    saturday_2_30pm = datetime(2025, 9, 27, 14, 30, 0)  # 2:30 PM Central
    # Convert to UTC for API (Central Time is UTC-5 in September - Daylight Saving Time)
    saturday_2_30pm_utc = saturday_2_30pm + timedelta(hours=5)  # Add 5 hours to get UTC
    timestamp = int(saturday_2_30pm_utc.timestamp())
    
    print(f"Checking timestamp: {timestamp} (Saturday 2:30 PM Central = {saturday_2_30pm_utc} UTC)")
    
    url = "https://tvlistings.gracenote.com/api/grid"
    params = {
        'lineupId': 'USA-lineupId-DEFAULT',
        'timespan': '4',  # 4 hour window to capture the full game
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
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://tvlistings.gracenote.com/'
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
                    print(f"\n🎯 Channel 7.1 ({call_sign}) detailed analysis:")
                    print("=" * 80)
                    
                    if 'events' in channel:
                        for event in channel['events']:
                            program = event.get('program', {})
                            title = program.get('title', 'Unknown')
                            
                            # Convert timestamp to readable time
                            start_time = event.get('startTime', '')
                            if start_time:
                                try:
                                    if 'T' in start_time:
                                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                    else:
                                        dt = datetime.fromtimestamp(int(start_time))
                                    # Convert to Central Time
                                    central_dt = dt - timedelta(hours=5)  # UTC to Central (during DST)
                                    time_str = central_dt.strftime('%I:%M %p')
                                    
                                    # Check if this is around 2:30 PM
                                    if central_dt.hour == 14 and abs(central_dt.minute - 30) <= 15:  # Within 15 minutes of 2:30 PM
                                        print(f"🏈 FOUND FOOTBALL GAME at {time_str}!")
                                        print("📋 Complete Metadata:")
                                        print(f"   Title: {title}")
                                        
                                        # Extract ALL available metadata
                                        metadata_fields = [
                                            'description', 'shortDescription', 'longDescription',
                                            'episodeTitle', 'seasonNumber', 'episodeNumber',
                                            'originalAirDate', 'genre', 'subGenre', 'rating',
                                            'year', 'cast', 'crew', 'directors', 'producers',
                                            'writers', 'network', 'callLetters', 'affiliateName'
                                        ]
                                        
                                        for field in metadata_fields:
                                            value = program.get(field, '')
                                            if value and value != 'NULL' and value != '':
                                                print(f"   {field}: {value}")
                                        
                                        # Event-level metadata
                                        event_fields = ['duration', 'live', 'new', 'premiere', 'finale']
                                        print(f"   Event Metadata:")
                                        for field in event_fields:
                                            value = event.get(field, '')
                                            if value and value != 'NULL' and value != '':
                                                print(f"     {field}: {value}")
                                        
                                        # Raw data dump for debugging
                                        print(f"\n📊 Raw Program Data:")
                                        for key, value in program.items():
                                            if value and value != 'NULL' and value != '':
                                                print(f"     {key}: {value}")
                                        
                                        print(f"\n📊 Raw Event Data:")
                                        for key, value in event.items():
                                            if key != 'program' and value and value != 'NULL' and value != '':
                                                print(f"     {key}: {value}")
                                        
                                        break
                                except Exception as e:
                                    print(f"   Error parsing time {start_time}: {e}")
                    else:
                        print("   No events found")
                    break
            else:
                print("❌ Channel 7.1 not found")
        else:
            print("❌ No channels found in API response")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_football_metadata()