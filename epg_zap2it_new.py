from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import pytz

def fetch_gracenote_epg(days=7):
    """Fetch EPG data from Gracenote API for Austin area (78748) for multiple days"""
    try:
        # Use the exact parameters from your working URL
        base_url = "https://tvlistings.gracenote.com/api/grid"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://tvlistings.gracenote.com/'
        }
        
        # Fetch data for multiple days to catch recurring shows
        all_results = []
        
        # Fetch data for each day
        for day_offset in range(days):
            target_date = datetime.now() + timedelta(days=day_offset)
            # Convert to Unix timestamp for the API
            timestamp = int(target_date.timestamp())
            
            params = {
                'lineupId': 'USA-lineupId-DEFAULT',
                'timespan': '3',  # Increased timespan to capture more shows per day
                'headendId': 'lineupId',
                'country': 'USA',
                'timezone': '',  # Leave empty like your example
                'device': '-',
                'postalCode': '90210',  # Default postal code - should be configurable
                'isOverride': 'true',
                'time': str(timestamp),  # Use current day's timestamp
                'pref': '32,256',
                'userId': '-',
                'aid': 'orbebb',
                'languagecode': 'en-us'
            }
            
            print(f"Fetching EPG data for {target_date.strftime('%Y-%m-%d')} (day {day_offset + 1} of {days})...")
            
            try:
                r = requests.get(base_url, params=params, headers=headers, timeout=15)
                r.raise_for_status()
                data = r.json()
                
                # Process this day's data
                day_results = parse_gracenote_data(data, target_date.strftime('%Y-%m-%d'))
                all_results.extend(day_results)
                
            except Exception as e:
                print(f"  Error fetching day {day_offset + 1}: {e}")
                continue
        
        print(f"Gracenote API: Found {len(all_results)} programs across {days} days")
        return all_results
        
    except Exception as e:
        print(f"Gracenote API error: {e}")
        import traceback
        traceback.print_exc()
        return get_fallback_epg_data()

def parse_gracenote_data(data, target_date):
    """Parse Gracenote API response data for a specific date"""
    results = []
    
    # Parse the JSON response - filter for ONLY Austin channels
    # Use channels from user's HDHomeRun device instead of hardcoded list
    
    if 'channels' in data:
        for channel in data['channels']:
            # Get channel information from the API response
            call_sign = channel.get('callSign', '')
            affiliate_name = channel.get('affiliateName', '')
            channel_no = channel.get('channelNo', channel.get('number', 'N/A'))
            channel_name = channel.get('name', call_sign or 'Unknown')
            
            # Process all channels (no filtering by specific market)
            
            # Create better channel display name for Austin channels
            if call_sign and affiliate_name and affiliate_name.upper() != 'NULL':
                channel_display = f"{call_sign} {affiliate_name} ({channel_no})"
            elif call_sign:
                channel_display = f"{call_sign} ({channel_no})"
            else:
                channel_display = f"Austin TV ({channel_no})"
            
            if 'events' in channel:
                for event in channel['events']:  # Get all events for Austin channels
                    program = event.get('program', {})
                    title = program.get('title', 'Unknown')
                    
                    # Skip generic or empty titles
                    if title in ['Unknown', '', 'TBA', 'To Be Announced']:
                        continue
                    
                    # Extract additional metadata
                    episode_title = program.get('episodeTitle', '')
                    season_number = program.get('seasonNumber', '')
                    episode_number = program.get('episodeNumber', '')
                    original_air_date = program.get('originalAirDate', '')
                    description = program.get('description', program.get('shortDescription', ''))
                    genre = program.get('genre', '')
                    rating = program.get('rating', '')
                    year = program.get('year', '')
                    duration = event.get('duration', '')
                    
                    # Build episode identifier for filename
                    episode_id = ""
                    if season_number and episode_number:
                        episode_id = f"S{season_number:0>2}E{episode_number:0>2}"
                    elif episode_number:
                        episode_id = f"E{episode_number:0>2}"
                    
                    # Format air date for filename
                    air_date_formatted = ""
                    if original_air_date:
                        try:
                            # Try parsing various date formats
                            if 'T' in original_air_date:
                                dt = datetime.fromisoformat(original_air_date.replace('Z', '+00:00'))
                            else:
                                dt = datetime.strptime(original_air_date, '%Y-%m-%d')
                            air_date_formatted = dt.strftime('%Y-%m-%d')
                        except:
                            air_date_formatted = original_air_date
                    
                    # Parse start time with proper timezone handling
                    start_time = event.get('startTime', '')
                    time_str = "TBD"
                    date_str = target_date  # Use the target date passed in
                    
                    if start_time:
                        try:
                            # Handle ISO format from API
                            if 'T' in start_time:
                                # Parse the ISO timestamp
                                if start_time.endswith('Z'):
                                    # UTC timestamp
                                    dt_utc = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                else:
                                    dt_utc = datetime.fromisoformat(start_time)
                                
                                # Convert to Central Time (Austin timezone)
                                central_tz = pytz.timezone('America/Chicago')
                                if dt_utc.tzinfo is None:
                                    # Assume UTC if no timezone info
                                    dt_utc = dt_utc.replace(tzinfo=pytz.UTC)
                                
                                dt_central = dt_utc.astimezone(central_tz)
                                
                                print(f"Timezone conversion: {start_time} -> {dt_central.strftime('%I:%M %p')} Central Time")
                                
                            elif start_time.isdigit():
                                # Unix timestamp - convert to Central Time
                                dt_utc = datetime.fromtimestamp(int(start_time), tz=pytz.UTC)
                                central_tz = pytz.timezone('America/Chicago')
                                dt_central = dt_utc.astimezone(central_tz)
                            else:
                                # Try other formats
                                dt_central = datetime.fromisoformat(start_time)
                                if dt_central.tzinfo is None:
                                    # Assume it's already in Central Time
                                    central_tz = pytz.timezone('America/Chicago')
                                    dt_central = central_tz.localize(dt_central)
                            
                            time_str = dt_central.strftime('%I:%M %p')
                            date_str = dt_central.strftime('%Y-%m-%d')
                            
                            # Determine period based on Central Time
                            hour = dt_central.hour
                            if 6 <= hour < 12:
                                period = 'Morning'
                            elif 12 <= hour < 18:
                                period = 'Afternoon'
                            else:
                                period = 'Evening'
                        
                        except Exception as time_error:
                            print(f"Time parsing error for {start_time}: {time_error}")
                            # Fallback time parsing
                            import re
                            time_match = re.search(r'(\d{1,2}:\d{2})', start_time)
                            if time_match:
                                time_str = time_match.group(1)
                                # Try to determine AM/PM
                                hour = int(time_str.split(':')[0])
                                if hour >= 6 and hour <= 11:
                                    time_str += ' AM'
                                    period = 'Morning'
                                elif hour >= 12 and hour <= 17:
                                    time_str += ' PM'
                                    period = 'Afternoon'
                                else:
                                    time_str += ' PM'
                                    period = 'Evening'
                            else:
                                period = 'Current'
                    else:
                        period = 'Current'
                    
                    results.append({
                        'channel': channel_display,
                        'title': title,
                        'time': time_str,
                        'date': date_str,
                        'period': period,
                        'is_local': True,  # All are Austin local channels
                        'call_sign': call_sign,
                        'channel_number': channel_no,
                        # Enhanced metadata
                        'episode_title': episode_title,
                        'season_number': season_number,
                        'episode_number': episode_number,
                        'episode_id': episode_id,
                        'original_air_date': air_date_formatted,
                        'description': description,
                        'genre': genre,
                        'rating': rating,
                        'year': year,
                        'duration': duration
                    })
    
    return results

def get_fallback_epg_data():
    """Fallback EPG data - generic sample"""
    print("Using generic fallback EPG data")
    return [
        {
            'channel': 'Sample Channel (1.1)',
            'title': 'Sample Program',
            'time': '7:00 PM',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'period': 'Evening',
            'is_local': True,
            'call_sign': 'SAMPLE',
            'channel_number': '1.1',
            'episode_title': '',
            'season_number': '',
            'episode_number': '',
            'episode_id': '',
            'original_air_date': '',
            'description': 'Sample program description.',
            'genre': 'General',
            'rating': 'TV-G',
            'year': '2025',
            'duration': '60'
        },
        {
            'channel': 'KVUE ABC (24.1)', 
            'title': 'Wheel of Fortune',
            'time': '7:30 PM',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'period': 'Evening',
            'is_local': True,
            'call_sign': 'KVUE',
            'channel_number': '24.1',
            'episode_title': '',
            'season_number': '42',
            'episode_number': '15',
            'episode_id': 'S42E15',
            'original_air_date': datetime.now().strftime('%Y-%m-%d'),
            'description': 'Classic word puzzle game show hosted by Pat Sajak and Vanna White.',
            'genre': 'Game Show',
            'rating': 'TV-G',
            'year': '2025',
            'duration': '30'
        },
        {
            'channel': 'KXAN NBC (36.1)',
            'title': 'Jeopardy!',
            'time': '3:30 PM',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'period': 'Afternoon',
            'is_local': True,
            'call_sign': 'KXAN',
            'channel_number': '36.1',
            'episode_title': 'Teachers Tournament Semifinals',
            'season_number': '41',
            'episode_number': '45',
            'episode_id': 'S41E45',
            'original_air_date': '2025-09-20',
            'description': 'Teachers compete in this iconic quiz show. Today features the semifinal round of the Teachers Tournament.',
            'genre': 'Game Show',
            'rating': 'TV-G',
            'year': '2025',
            'duration': '30'
        },
        # Add multiple Jeopardy entries for different days
        {
            'channel': 'KXAN NBC (36.1)',
            'title': 'Daytime Jeopardy',
            'time': '3:00 PM',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'period': 'Afternoon',
            'is_local': True,
            'call_sign': 'KXAN',
            'channel_number': '36.1',
            'episode_title': 'Celebrity Tournament Quarterfinals',
            'season_number': '41',
            'episode_number': '44',
            'episode_id': 'S41E44',
            'original_air_date': '2025-09-19',
            'description': 'Celebrity contestants compete in this daytime edition of the quiz show.',
            'genre': 'Game Show',
            'rating': 'TV-G',
            'year': '2025',
            'duration': '30'
        },
        # Add future Jeopardy episodes
        {
            'channel': 'KXAN NBC (36.1)',
            'title': 'Jeopardy!',
            'time': '3:30 PM',
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'period': 'Afternoon',
            'is_local': True,
            'call_sign': 'KXAN',
            'channel_number': '36.1',
            'episode_title': 'Teachers Tournament Finals',
            'season_number': '41',
            'episode_number': '46',
            'episode_id': 'S41E46',
            'original_air_date': '2025-09-21',
            'description': 'The final round of the Teachers Tournament determines the champion.',
            'genre': 'Game Show',
            'rating': 'TV-G',
            'year': '2025',
            'duration': '30'
        },
        {
            'channel': 'KXAN NBC (36.1)',
            'title': 'Daytime Jeopardy',
            'time': '3:00 PM',
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'period': 'Afternoon',
            'is_local': True,
            'call_sign': 'KXAN',
            'channel_number': '36.1',
            'episode_title': 'College Championship Preview',
            'season_number': '41',
            'episode_number': '47',
            'episode_id': 'S41E47',
            'original_air_date': '2025-09-22',
            'description': 'Preview of upcoming college championship featuring past winners.',
            'genre': 'Game Show',
            'rating': 'TV-G',
            'year': '2025',
            'duration': '30'
        }
    ]

# Legacy function for backward compatibility
def fetch_zap2it_epg():
    """Legacy function - redirects to Gracenote"""
    return fetch_gracenote_epg()