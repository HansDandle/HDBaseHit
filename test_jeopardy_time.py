import requests
import json

# Test the NLP command endpoint with the updated logic
try:
    url = "http://localhost:5000/nlp_command"
    data = {"command": "record jeopardy"}
    
    print("Testing 'record jeopardy' command with updated logic...")
    response = requests.post(url, json=data)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        # Check the scheduled time
        epg_match = result.get('result', {}).get('details', {}).get('epg_match', {})
        if epg_match:
            print(f"Scheduled Show: {epg_match.get('title')}")
            print(f"Channel: {epg_match.get('channel')}")
            print(f"Time: {epg_match.get('time')}")
            print(f"Date: {epg_match.get('date')}")
            
            if epg_match.get('time') == '3:30 PM':
                print("✅ SUCCESS: Correctly scheduled for 3:30 PM!")
            else:
                print(f"❌ ERROR: Still showing {epg_match.get('time')} instead of 3:30 PM")
        else:
            print("No EPG match found in response")
        
        print(f"\nFull response:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Connection error: {e}")
    print("Make sure the server is running at localhost:5000")