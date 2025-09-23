import requests
import json

# Fetch detailed EPG data to see what metadata is available
url = 'https://tvlistings.gracenote.com/api/grid'
params = {
    'lineupId': 'USA-lineupId-DEFAULT',
    'timespan': '2',
    'headendId': 'lineupId', 
    'country': 'USA',
    'timezone': '',
    'device': '-',
    'postalCode': '78748',
    'isOverride': 'true',
    'time': '1758657600',
    'pref': '32,256',
    'userId': '-',
    'aid': 'orbebb',
    'languagecode': 'en-us'
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://tvlistings.gracenote.com/'
}

try:
    r = requests.get(url, params=params, headers=headers)
    data = r.json()
    
    print("Checking available metadata fields...")
    
    # Look through events to find one with rich metadata
    found_detailed = False
    for channel in data['channels'][:10]:
        channel_no = channel.get('channelNo', 'N/A')
        if channel_no in ['7.1', '18.1', '24.1', '36.1', '42.1']:
            print(f"\nChannel {channel_no} events:")
            
            if 'events' in channel:
                for i, event in enumerate(channel['events'][:3]):
                    print(f"\nEvent {i+1} structure:")
                    print(f"Available top-level keys: {list(event.keys())}")
                    
                    if 'program' in event:
                        program = event['program']
                        print(f"Program keys: {list(program.keys())}")
                        
                        # Print detailed program info
                        for key, value in program.items():
                            if value and str(value).strip():
                                print(f"  {key}: {value}")
                    
                    # Show event-level data too
                    for key, value in event.items():
                        if key != 'program' and value and str(value).strip():
                            print(f"Event {key}: {value}")
                    
                    if i == 0:  # Just show first event detail for each channel
                        found_detailed = True
                        break
            
            if found_detailed:
                break
    
except Exception as e:
    print(f"Error: {e}")