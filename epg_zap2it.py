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
        
        # Generate timestamps for better coverage throughout each day
        # Start from current time and cover multiple days with different time periods
        base_date = datetime.now()
        current_time = datetime.now()
        day_timestamps = []
        
        for day_offset in range(days):
            current_date = base_date + timedelta(days=day_offset)
            
            # For each day, fetch multiple time periods to ensure full coverage
            time_periods = [
                (6, "6AM"),    # Morning: 6 AM
                (14, "2PM"),   # Afternoon: 2 PM  
                (20, "8PM")    # Evening/Night: 8 PM
            ]
            
            for hour, label in time_periods:
                time_slot = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                time_slot_end = time_slot + timedelta(hours=6)  # Each window covers 6 hours
                
                # Skip time periods only if the ENTIRE window has already passed
                if day_offset == 0 and time_slot_end <= current_time:
                    continue  # Skip only if the 6-hour window has completely passed
                
                day_timestamps.append(int(time_slot.timestamp()))
        
        # Fetch data for each timestamp period
        for i, timestamp in enumerate(day_timestamps):
            target_date = datetime.fromtimestamp(timestamp)
            
            params = {
                'lineupId': 'USA-lineupId-DEFAULT',
                'timespan': '6',  # 6 hours coverage per fetch
                'headendId': 'lineupId',
                'country': 'USA',
                'timezone': '',  # Leave empty like your example
                'device': '-',
                'postalCode': '78748',  # Austin area - this is the key filter
                'isOverride': 'true',
                'time': str(timestamp),  # Use calculated timestamps
                'pref': '32,256',
                'userId': '-',
                'aid': 'orbebb',
                'languagecode': 'en-us'
            }
            
            print(f"Fetching EPG data for {target_date.strftime('%Y-%m-%d %H:%M')} (6-hour block)...")
            
            try:
                r = requests.get(base_url, params=params, headers=headers, timeout=15)
                r.raise_for_status()
                data = r.json()
                
                # Process this time period's data
                period_results = parse_gracenote_data(data, target_date.strftime('%Y-%m-%d'))
                all_results.extend(period_results)
                
            except Exception as e:
                print(f"  Error fetching {target_date.strftime('%Y-%m-%d %H:%M')}: {e}")
                continue
        
        print(f"Gracenote API: Found {len(all_results)} programs across {len(day_timestamps)} time periods ({days} days)")
        
        # Only use real API data - no fallback data
        return all_results
        
    except Exception as e:
        print(f"Gracenote API error: {e}")
        import traceback
        traceback.print_exc()
        return []  # Return empty list instead of fallback data

def search_epg_for_show(show_name, days=7):
    """Search EPG data for any show name and return all matching episodes with smart sports matching"""
    print(f"Searching EPG for show: '{show_name}' over next {days} days...")
    
    # Get all EPG data for the specified number of days
    all_epg_data = fetch_gracenote_epg(days)
    
    # Search for matching shows with improved logic
    matching_episodes = []
    show_name_lower = show_name.lower()
    
    # Extract key terms for smarter matching
    show_words = [word.strip() for word in show_name_lower.split()]
    
    # Sports-specific logic with comprehensive team names
    sports_terms = ['football', 'game', 'basketball', 'baseball', 'soccer', 'hockey', 'tennis', 'golf', 'match', 'vs', 'at']
    
    # Comprehensive college team mappings (team name -> possible variations)
    college_teams = {
        'utah': ['utah', 'utes'],
        'west virginia': ['west virginia', 'wvu', 'mountaineers'],
        'texas': ['texas', 'ut', 'longhorns', 'hook em'],
        'oklahoma': ['oklahoma', 'ou', 'sooners'],
        'alabama': ['alabama', 'bama', 'crimson tide'],
        'georgia': ['georgia', 'uga', 'bulldogs', 'dawgs'],
        'michigan': ['michigan', 'wolverines'],
        'ohio state': ['ohio state', 'osu', 'buckeyes'],
        'notre dame': ['notre dame', 'fighting irish'],
        'clemson': ['clemson', 'tigers'],
        'florida': ['florida', 'gators'],
        'lsu': ['lsu', 'tigers'],
        'tennessee': ['tennessee', 'vols', 'volunteers'],
        'auburn': ['auburn', 'tigers'],
        'penn state': ['penn state', 'nittany lions'],
        'wisconsin': ['wisconsin', 'badgers'],
        'oregon': ['oregon', 'ducks'],
        'stanford': ['stanford', 'cardinal'],
        'usc': ['usc', 'trojans', 'southern cal'],
        'ucla': ['ucla', 'bruins'],
        'washington': ['washington', 'huskies'],
        'miami': ['miami', 'hurricanes'],
        'florida state': ['florida state', 'fsu', 'seminoles'],
        'virginia tech': ['virginia tech', 'vt', 'hokies'],
        'nc state': ['nc state', 'wolfpack'],
        'duke': ['duke', 'blue devils'],
        'north carolina': ['north carolina', 'unc', 'tar heels'],
        'kansas': ['kansas', 'jayhawks'],
        'nebraska': ['nebraska', 'cornhuskers'],
        'iowa': ['iowa', 'hawkeyes'],
        'minnesota': ['minnesota', 'gophers'],
        'purdue': ['purdue', 'boilermakers'],
        'illinois': ['illinois', 'fighting illini'],
        'northwestern': ['northwestern', 'wildcats'],
        'indiana': ['indiana', 'hoosiers'],
        'maryland': ['maryland', 'terrapins'],
        'rutgers': ['rutgers', 'scarlet knights'],
        'michigan state': ['michigan state', 'msu', 'spartans'],
        'baylor': ['baylor', 'bears'],
        'tcu': ['tcu', 'horned frogs'],
        'texas tech': ['texas tech', 'red raiders'],
        'oklahoma state': ['oklahoma state', 'cowboys'],
        'kansas state': ['kansas state', 'wildcats'],
        'iowa state': ['iowa state', 'cyclones'],
        'west virginia': ['west virginia', 'wvu', 'mountaineers']
    }
    
    # Flatten team variations for easier searching
    all_team_variations = []
    for variations in college_teams.values():
        all_team_variations.extend(variations)
    
    is_sports_query = any(term in show_name_lower for term in sports_terms)
    is_team_query = any(team in show_name_lower for team in all_team_variations)
    
    for program in all_epg_data:
        title = program.get('title', '').lower()
        description = program.get('description', '').lower()
        genre = program.get('genre', '').lower()
        
        # Scoring system for match quality
        match_score = 0
        
        # Exact title match (highest score)
        if show_name_lower == title:
            match_score = 100
        
        # Partial title matches
        elif show_name_lower in title or title in show_name_lower:
            match_score = 80
            
        # Word-based matching
        else:
            title_words = title.split()
            matching_words = sum(1 for word in show_words if any(word in title_word for title_word in title_words))
            if matching_words > 0:
                match_score = (matching_words / len(show_words)) * 60
        
        # Enhanced description matching
        description_words = description.split() if description else []
        desc_matching_words = sum(1 for word in show_words if any(word in desc_word for desc_word in description_words))
        if desc_matching_words > 0:
            match_score += (desc_matching_words / len(show_words)) * 50
        
        # Enhanced sports and team matching
        if is_sports_query or is_team_query:
            # Look for sports genre
            if 'sport' in genre:
                match_score += 20
            
            # DETECT preview/analysis shows vs actual games
            preview_show_indicators = [
                'gameday', 'game day', 'preview', 'analysis', 'wrap up', 'wrap-up', 
                'post game', 'postgame', 'highlights', 'recap', 'roundup', 'tonight',
                'weekly', 'show', 'talk', 'discussion'
            ]
            
            is_preview_show = any(indicator in title.lower() or indicator in description.lower() 
                                for indicator in preview_show_indicators)
            
            # PRIORITIZE actual games over preview shows
            actual_game_indicators = [
                'vs', 'at', ' v ', 'versus'  # These indicate actual matchups
            ]
            
            is_actual_game = any(indicator in title.lower() or indicator in description.lower() 
                               for indicator in actual_game_indicators)
            
            # Enhanced team matching - check if any team from query appears in title/description
            for team_name, variations in college_teams.items():
                # Check if any variation of this team is mentioned in the search query
                query_mentions_team = any(variation in show_name_lower for variation in variations)
                
                if query_mentions_team:
                    # Check if this team appears in the program title or description
                    program_mentions_team = any(variation in title.lower() or variation in description.lower() for variation in variations)
                    
                    if program_mentions_team:
                        if is_actual_game:
                            match_score += 100  # Very high score for actual team games
                        elif is_preview_show:
                            match_score += 5    # Very low score for preview shows
                        else:
                            match_score += 50   # Medium score for team-related content
                        break
            
            # Generic sports content matching
            if 'football' in show_name_lower:
                if 'football' in title.lower() and 'college' in title.lower():
                    if is_actual_game:
                        match_score += 75   # High score for actual college football games
                    elif is_preview_show:
                        match_score += 2    # Minimal score for preview shows
                    else:
                        match_score += 25   # Medium score for other football content
                        
                if 'football' in description.lower():
                    if is_actual_game:
                        match_score += 50
                    elif is_preview_show:
                        match_score += 2    # Minimal score for preview shows
                    else:
                        match_score += 20
            
            # Apply FINAL PENALTY for preview shows - this ensures they stay below 50
            if is_preview_show:
                match_score = min(match_score, 40)  # Cap preview shows at 40 max
            
            # Generic game/match terms
            if any(term in show_name_lower for term in ['game', 'match', 'vs']):
                if any(term in title for term in ['vs', 'at', 'game']):
                    match_score += 15
        
        # Accept matches with score > 30
        if match_score > 30:
            program['match_score'] = match_score
            matching_episodes.append(program)
            print(f"  Found: {program.get('title')} on {program.get('channel')} at {program.get('time')} on {program.get('date')} (score: {match_score:.1f})")
    
    # Sort by match score (best matches first)
    matching_episodes.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    
    print(f"Found {len(matching_episodes)} episodes of '{show_name}'")
    return matching_episodes
    
def analyze_show_pattern(episodes):
    """Analyze episodes to determine if show is daily, weekly, or one-time"""
    if len(episodes) < 2:
        return "one-time", episodes
    
    # Group episodes by day of week and time
    from collections import defaultdict
    by_day_time = defaultdict(list)
    
    for episode in episodes:
        try:
            date_obj = datetime.strptime(episode['date'], '%Y-%m-%d')
            day_of_week = date_obj.weekday()  # Monday=0, Sunday=6
            time_slot = episode.get('time', 'Unknown')
            key = f"{day_of_week}_{time_slot}"
            by_day_time[key].append(episode)
        except:
            continue
    
    # Analyze patterns
    weekday_slots = []  # Monday-Friday
    weekend_slots = []  # Saturday-Sunday
    
    for key, eps in by_day_time.items():
        if len(eps) >= 2:  # Show appears multiple times in this slot
            day_num = int(key.split('_')[0])
            if day_num < 5:  # Monday-Friday
                weekday_slots.extend(eps)
            else:  # Saturday-Sunday
                weekend_slots.extend(eps)
    
    # Determine pattern
    if len(weekday_slots) >= 4:  # Appears on multiple weekdays
        pattern = "daily-weekdays"
        return pattern, weekday_slots
    elif len(weekend_slots) >= 2:  # Weekend show
        pattern = "weekly-weekend"
        return pattern, weekend_slots
    elif len(episodes) >= 3:  # Multiple episodes but not clearly daily
        pattern = "weekly"
        return pattern, episodes
    else:
        pattern = "limited-series"
        return pattern, episodes

def group_episodes_by_series(episodes):
    """Group episodes into recording series based on channel and time patterns"""
    from collections import defaultdict
    series_groups = defaultdict(list)
    
    for episode in episodes:
        # Create a key based on channel, day pattern, and time
        try:
            date_obj = datetime.strptime(episode['date'], '%Y-%m-%d')
            day_of_week = date_obj.weekday()
            
            # Group weekdays together, weekends separately
            if day_of_week < 5:
                day_group = "weekdays"
            else:
                day_group = "weekend"
            
            channel = episode.get('channel_number', episode.get('channel', 'Unknown'))
            time_slot = episode.get('time', 'Unknown')
            
            series_key = f"{channel}_{day_group}_{time_slot}"
            series_groups[series_key].append(episode)
        except:
            # If date parsing fails, put in a general group
            series_groups['general'].append(episode)
    
    return dict(series_groups)

def parse_gracenote_data(data, target_date):
    """Parse Gracenote API response data for a specific date"""
    results = []
    
    # Parse the JSON response - filter for ONLY Austin channels
    austin_channels = ['7.1', '18.1', '24.1', '36.1', '42.1']  # Only these channels
    
    if 'channels' in data:
        for channel in data['channels']:
            # Get channel information from the API response
            call_sign = channel.get('callSign', '')
            affiliate_name = channel.get('affiliateName', '')
            channel_no = channel.get('channelNo', channel.get('number', 'N/A'))
            channel_name = channel.get('name', call_sign or 'Unknown')
            
            # ONLY process if it's one of the Austin channels we want
            if channel_no not in austin_channels:
                continue
            
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
                                
                                # Commented out verbose timezone logging
                                # print(f"Timezone conversion: {start_time} -> {dt_central.strftime('%I:%M %p')} Central Time")
                                
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

# FALLBACK DATA DISABLED - Using only real API data
# def get_fallback_epg_data():
#     """Fallback EPG data disabled - using only real Gracenote API data"""
#     return []

# Legacy function for backward compatibility
def fetch_zap2it_epg():
    """Legacy function - redirects to Gracenote"""
    return fetch_gracenote_epg()