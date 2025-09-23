# Utility: run a function in a new thread
def run_threaded(func, *args, **kwargs):
    t = threading.Thread(target=func, args=args, kwargs=kwargs)
    t.start()
    return t

# Utility: save the schedule to disk
def save_schedule():
    try:
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(scheduled_jobs, f, indent=2)
    except Exception as e:
        print(f"Error saving schedule: {e}")

# Utility: load the schedule from disk
def load_schedule():
    global scheduled_jobs
    try:
        if os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, "r") as f:
                scheduled_jobs = json.load(f)
                print(f"Loaded {len(scheduled_jobs)} scheduled recordings")
        else:
            scheduled_jobs = []
    except Exception as e:
        print(f"Error loading schedule: {e}")
        scheduled_jobs = []
def run_schedule_loop():
    import time
    print("Schedule loop started (stub)")
    while True:
        # TODO: implement actual scheduling logic
        time.sleep(60)
import os
import threading
import subprocess
import time
import json
import requests
import socket
import struct
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from epg_zap2it import fetch_zap2it_epg
# --- Global config variables ---
HDHR_IP = "192.168.1.126"
SAVE_DIR = r"F:\TV_Recordings"
FFMPEG_PATH = r"C:\FFMPEG\ffmpeg-2025-08-25-git-1b62f9d3ae-essentials_build\bin\ffmpeg.exe"
SCHEDULE_FILE = os.path.join(SAVE_DIR, "scheduled_jobs.json")

os.makedirs(SAVE_DIR, exist_ok=True)
scheduled_jobs = []
current_process = None
stop_event = threading.Event()

app = Flask(__name__)
from epg_zap2it import fetch_zap2it_epg
import time

# Simple in-memory EPG cache
EPG_CACHE = {"data": None, "timestamp": 0}
EPG_TTL = 60 * 30  # 30 minutes

def get_epg():
    now = time.time()
    if EPG_CACHE["data"] is None or now - EPG_CACHE["timestamp"] > EPG_TTL:
        try:
            EPG_CACHE["data"] = fetch_zap2it_epg()
            EPG_CACHE["timestamp"] = now
        except Exception as e:
            print("EPG fetch failed:", e)
            return None
import schedule
t = time
SCHEDULE_FILE = os.path.join(SAVE_DIR, "scheduled_jobs.json")

os.makedirs(SAVE_DIR, exist_ok=True)
scheduled_jobs = []
current_process = None
stop_event = threading.Event()

app = Flask(__name__)

# === FUNCTIONS ===

def get_hdhr_channels(ip):
    url = f"http://{ip}/lineup.json"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        lineup = r.json()
        channels_dict = {}
        for ch in lineup:
            vch = ch.get("GuideNumber")
            name = ch.get("GuideName")
            if vch and name:
                channels_dict[vch] = name
        return channels_dict
    except Exception as e:
        print(f"Error fetching channel lineup: {e}")
        return {"7.1": "Fox"}  # fallback

channels = get_hdhr_channels(HDHR_IP)
days_list = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def record_channel(channel_key, duration_min, crf=23, preset="fast", record_format="mp4"):
    global current_process, stop_event
    chname = channels[channel_key]
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    ext = ".mp4" if record_format=="mp4" else ".ts"
    filename = f"{chname}_{now}{ext}"
    filepath = os.path.join(SAVE_DIR, filename)
    url = f"http://{HDHR_IP}:5004/auto/v{channel_key}"

    stop_event.clear()

    if record_format == "mp4":
        cmd = [
            FFMPEG_PATH, "-i", url, "-t", str(duration_min*60),
            "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-y", filepath
        ]
    else:
        cmd = [
            FFMPEG_PATH, "-i", url, "-t", str(duration_min*60),
            "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
            "-c:a", "ac3", "-b:a", "192k", "-y", filepath
        ]

    global current_process
    current_process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def stream_output(proc):
        for line in iter(proc.stdout.readline, b''):
            if not line:
                break
            print(line.decode(errors='ignore').strip())
    threading.Thread(target=stream_output, args=(current_process,), daemon=True).start()

    while current_process.poll() is None:
        if stop_event.is_set():
            try:
                current_process.stdin.write(b'q\n')
                current_process.stdin.flush()
            except:
                pass
            break
        t.sleep(1)

    current_process.wait()
    current_process = None

def create_fallback_jeopardy_entry():
    """Create a fallback Jeopardy entry when EPG data is unavailable"""
    return {
        'channel': 'KXAN NBC (36.1)',
        'title': 'Jeopardy!',
        'time': '3:30 PM',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'period': 'Afternoon',
        'is_local': True,
        'call_sign': 'KXAN',
        'channel_number': '36.1',
        'episode_title': 'Daily Episode',
        'season_number': '41',
        'episode_number': '',
        'episode_id': '',
        'original_air_date': datetime.now().strftime('%Y-%m-%d'),
        'description': 'America\'s Favorite Quiz Show airs weekdays at 3:30 PM on KXAN.',
        'genre': 'Game Show',
        'rating': 'TV-G',
        'year': '2025',
        'duration': '30'
    }

def parse_nlp_command(command):
    """Simplified NLP parser that works with any show name."""
    result = {"action": None, "event": None, "series_recording": False}
    cmd = command.lower().strip()
    
    if "record" in cmd:
        result["action"] = "record"
        
        # Check for series recording keywords
        series_keywords = ['all episodes', 'every episode', 'series', 'all shows', 'every show', 'daily', 'weekdays', 'all of', 'every']
        result["series_recording"] = any(keyword in cmd for keyword in series_keywords)
        
        # Extract show name using various patterns
        show_name = None
        
        # Pattern 1: "record [series keywords] SHOW_NAME"
        if result["series_recording"]:
            # Remove "record" and series keywords to get show name
            clean_cmd = cmd.replace("record", "").strip()
            for keyword in series_keywords:
                clean_cmd = clean_cmd.replace(keyword, "").strip()
            # Clean up extra words like "of"
            clean_cmd = clean_cmd.replace(" of ", " ").strip()
            show_name = clean_cmd
        else:
            # Pattern 2: "record SHOW_NAME"
            match = re.search(r'record\s+(.+?)(?:\s+on\s+channel|\s+at\s+|\s*$)', cmd)
            if match:
                show_name = match.group(1).strip()
        
        # Clean up the show name
        if show_name:
            # Remove extra articles and prepositions
            show_name = re.sub(r'\b(the|a|an)\b', '', show_name, flags=re.IGNORECASE).strip()
            show_name = re.sub(r'\s+', ' ', show_name).strip()  # Remove extra spaces
            result["event"] = show_name
            
        print(f"Parsed command: action='{result['action']}', show='{result['event']}', series={result['series_recording']}")
    
    elif "download" in cmd:
        result["action"] = "download"
        m = re.search(r'download (.+)', cmd)
        if m:
            result["query"] = m.group(1).strip()
    elif "organize" in cmd or "move" in cmd:
        result["action"] = "organize"
        m = re.search(r'(?:organize|move) (.+?)(?: to (.+))?', cmd)
        if m:
            result["title"] = m.group(1).strip()
            if m.group(2):
                result["destination"] = m.group(2).strip()
    else:
        result["action"] = "unknown"
        result["query"] = command
    
    return result

def dispatch_agent(parsed):
    action = parsed.get("action")
    if action == "record":
        return agent_record(parsed)
    elif action == "download":
        return agent_download(parsed)
    elif action == "organize":
        return agent_organize(parsed)
    else:
        return agent_unknown(parsed)

def generate_filename(recording_info):
    """Generate a filename with episode info and air date"""
    import re
    
    # Get basic info
    title = recording_info.get('title', 'Unknown Show')
    channel_num = recording_info.get('channel_number', '')
    date = recording_info.get('date', '')
    time_raw = recording_info.get('time', '') or ''
    time = time_raw.replace(':', '')
    
    # Clean title for filename
    clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    
    # Build filename components
    filename_parts = [clean_title]
    
    # Add episode info if available
    episode_id = recording_info.get('episode_id', '')
    episode_title = recording_info.get('episode_title', '')
    
    if episode_id:
        filename_parts.append(episode_id)
    
    if episode_title:
        clean_episode = re.sub(r'[<>:"/\\|?*]', '', episode_title)
        clean_episode = re.sub(r'\s+', ' ', clean_episode).strip()
        if clean_episode and len(clean_episode) < 50:  # Keep episode titles reasonable
            filename_parts.append(clean_episode)
    
    # Add air date if different from recording date
    original_air_date = recording_info.get('original_air_date', '')
    if original_air_date and original_air_date != date:
        filename_parts.append(f"Aired-{original_air_date}")
    
    # Add recording date and time
    if date:
        filename_parts.append(date)
    if time:
        filename_parts.append(time)
    
    # Add channel
    if channel_num:
        filename_parts.append(f"Ch{channel_num}")
    
    # Join with dashes and add extension
    filename = " - ".join(filename_parts) + ".mp4"
    
    # Ensure filename isn't too long (Windows limit is 255 chars)
    if len(filename) > 200:
        # Truncate episode title if needed
        if episode_title and len(filename_parts) > 4:
            filename_parts[2] = filename_parts[2][:30] + "..."
            filename = " - ".join(filename_parts) + ".mp4"
    
    return filename

def save_metadata_file(recording_info, filename):
    """Save detailed metadata to a companion file"""
    import json
    import os
    
    # Create metadata filename
    base_name = os.path.splitext(filename)[0]
    metadata_file = base_name + ".metadata.json"
    
    # Prepare metadata
    metadata = {
        'recording_info': {
            'title': recording_info.get('title'),
            'episode_title': recording_info.get('episode_title'),
            'season_number': recording_info.get('season_number'),
            'episode_number': recording_info.get('episode_number'),
            'original_air_date': recording_info.get('original_air_date'),
            'recording_date': recording_info.get('date'),
            'recording_time': recording_info.get('time'),
            'channel': recording_info.get('channel'),
            'channel_number': recording_info.get('channel_number'),
            'call_sign': recording_info.get('call_sign'),
            'description': recording_info.get('description'),
            'genre': recording_info.get('genre'),
            'rating': recording_info.get('rating'),
            'year': recording_info.get('year'),
            'duration': recording_info.get('duration')
        },
        'technical_info': {
            'filename': filename,
            'scheduled_at': recording_info.get('scheduled_at'),
            'recording_format': 'mp4',
            'source': 'HDHomeRun'
        }
    }
    
    try:
        metadata_path = os.path.join(SAVE_DIR, metadata_file)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"Metadata saved to: {metadata_file}")
        return metadata_file
    except Exception as e:
        print(f"Error saving metadata: {e}")
        return None

def agent_record(parsed):
    """Main recording agent that handles any show name dynamically"""
    show_name = parsed.get('event', '').strip()
    
    if not show_name:
        return {"error": "No show name provided"}
    
    print(f"Recording request for: '{show_name}'")
    
    # Import the new EPG search functions
    from epg_zap2it import search_epg_for_show, analyze_show_pattern, group_episodes_by_series
    
    # Search for the show in EPG data
    matching_episodes = search_epg_for_show(show_name, days=7)
    
    if not matching_episodes:
        return {"error": f"No episodes found for '{show_name}' in the next 7 days"}
    
    # Analyze the pattern to determine recording strategy
    pattern, relevant_episodes = analyze_show_pattern(matching_episodes)
    print(f"Show pattern detected: {pattern}")
    
    # Check if user wants series recording or single episode
    is_series_request = parsed.get('series_recording', False)
    
    if is_series_request or pattern in ['daily-weekdays', 'weekly', 'weekly-weekend'] and len(relevant_episodes) > 1:
        # Handle as series recording
        return handle_dynamic_series_recording(show_name, relevant_episodes, pattern)
    else:
        # Handle as single recording (first available episode)
        return handle_single_episode_recording(show_name, relevant_episodes[0] if relevant_episodes else matching_episodes[0])

def handle_dynamic_series_recording(show_name, episodes, pattern):
    """Handle series recording with recurring rules instead of individual episodes"""
    print(f"Setting up series recording for '{show_name}' - {pattern} pattern")
    
    # Group episodes by recording series (channel + time slot)
    from epg_zap2it import group_episodes_by_series
    series_groups = group_episodes_by_series(episodes)
    
    total_rules_created = 0
    recording_details = []
    
    for series_key, group_episodes in series_groups.items():
        print(f"  Series group: {series_key} ({len(group_episodes)} episodes)")
        
        # Create a single recurring recording rule for this series group
        recording_rule = create_recurring_recording_rule(show_name, group_episodes, pattern, series_key)
        if recording_rule:
            total_rules_created += 1
            recording_details.append(recording_rule)
    
    return {
        "message": f"Series recording scheduled for '{show_name}'",
        "pattern": pattern,
        "recording_rules": total_rules_created,
        "recording_details": recording_details
    }

def create_recurring_recording_rule(show_name, episodes, pattern, series_key):
    """Create a time-based recurring recording rule that will record ongoing"""
    if not episodes:
        return None
    
    # Use the first episode as the template for the recurring rule
    template_episode = episodes[0]
    
    # Determine the recurrence pattern from the episodes
    recurrence_info = analyze_recurrence_pattern(episodes, pattern)
    
    # Create the recurring recording rule - TIME-BASED, not episode-based
    recording_rule = {
        'id': len(scheduled_jobs) + 1,
        'type': 'recurring_series',
        'title': template_episode.get('title', show_name),
        'channel': template_episode.get('channel', 'Unknown Channel'),
        'channel_number': template_episode.get('channel_number', ''),
        'call_sign': template_episode.get('call_sign', ''),
        'time': template_episode.get('time', ''),
        'duration': template_episode.get('duration', '30'),
        'pattern': pattern,
        'recurrence': recurrence_info,
        'series_key': series_key,
        'sample_episodes': episodes,  # Store sample episodes for reference
        'created_at': datetime.now().isoformat(),
        'status': 'active',
        'is_time_based': True,  # Flag to indicate this is ongoing time-based recording
        'next_episode': episodes[0] if episodes else None
    }
    
    # Add to scheduled jobs
    scheduled_jobs.append(recording_rule)
    
    print(f"  Created time-based recurring rule: {recording_rule['title']} - {recurrence_info['description']}")
    print(f"  Will record ongoing at {template_episode.get('time', '')} on {', '.join(recurrence_info.get('days', []))} (not limited to current EPG episodes)")
    
    return recording_rule
    
    return recording_rule

def analyze_recurrence_pattern(episodes, pattern):
    """Analyze episodes to create a human-readable recurrence description"""
    if not episodes:
        return {"description": "No episodes", "days": [], "time": ""}
    
    # Get time from first episode
    time = episodes[0].get('time', '')
    
    # Analyze which days episodes occur
    days_of_week = set()
    for episode in episodes:
        try:
            episode_date = datetime.strptime(episode.get('date', ''), '%Y-%m-%d')
            days_of_week.add(episode_date.strftime('%A'))
        except:
            continue
    
    # Create description based on pattern
    if pattern == "daily-weekdays":
        description = f"Weekdays at {time}"
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    elif pattern == "weekly":
        day_list = list(days_of_week)
        if len(day_list) == 1:
            description = f"{day_list[0]}s at {time}"
        else:
            description = f"Weekly at {time}"
        days = day_list
    elif pattern == "weekly-weekend":
        description = f"Weekends at {time}"
        days = ["Saturday", "Sunday"]
    else:
        day_list = list(days_of_week)
        if day_list:
            if len(day_list) == 1:
                description = f"{day_list[0]}s at {time}"
            else:
                description = f"{', '.join(day_list)} at {time}"
        else:
            description = f"At {time}"
        days = day_list
    
    return {
        "description": description,
        "days": days,
        "time": time,
        "pattern": pattern
    }

def handle_single_episode_recording(show_name, episode):
    """Handle recording a single episode of any show"""
    print(f"Setting up single recording for '{show_name}'")
    
    # Check for duplicates
    if is_duplicate_recording(episode):
        return {"error": f"'{show_name}' is already scheduled for recording"}
    
    # Schedule the recording
    recording_id = schedule_episode_recording(episode)
    
    if recording_id:
        return {
            "message": f"Scheduled recording for '{show_name}'",
            "recording_id": recording_id,
            "episode_details": {
                'title': episode.get('title'),
                'date': episode.get('date'),
                'time': episode.get('time'),
                'channel': episode.get('channel'),
                'duration': episode.get('duration', '30')
            }
        }
    else:
        return {"error": f"Failed to schedule recording for '{show_name}'"}

def schedule_episode_recording(episode):
    """Schedule a single episode recording with real metadata"""
    try:
        # Generate filename using real metadata
        suggested_filename = generate_filename(episode)
        
        # Create recording entry
        recording_info = {
            'id': len(scheduled_jobs) + 1,
            'title': episode.get('title', 'Unknown Show'),
            'channel': episode.get('channel', 'Unknown Channel'),
            'channel_number': episode.get('channel_number', ''),
            'call_sign': episode.get('call_sign', ''),
            'date': episode.get('date', ''),
            'time': episode.get('time', ''),
            'episode_title': episode.get('episode_title', ''),
            'season_number': episode.get('season_number', ''),
            'episode_number': episode.get('episode_number', ''),
            'episode_id': episode.get('episode_id', ''),
            'original_air_date': episode.get('original_air_date', ''),
            'description': episode.get('description', ''),
            'genre': episode.get('genre', ''),
            'rating': episode.get('rating', ''),
            'year': episode.get('year', ''),
            'duration': episode.get('duration', '30'),
            'scheduled_at': datetime.now().isoformat(),
            'filename': suggested_filename,
            'status': 'scheduled'
        }
        
        # Add to scheduled jobs
        scheduled_jobs.append(recording_info)
        
        # Save metadata
        metadata_file = save_metadata_file(recording_info, suggested_filename)
        
        print(f"  Scheduled: {recording_info['title']} on {recording_info['date']} at {recording_info['time']}")
        print(f"  Channel: {recording_info['channel']} ({recording_info['channel_number']})")
        print(f"  Filename: {suggested_filename}")
        
        return recording_info['id']
        
    except Exception as e:
        print(f"Error scheduling recording: {e}")
        import traceback
        traceback.print_exc()
        return None

def handle_series_recording(parsed):
    """Handle recording multiple episodes of a show"""
    epg_matches = parsed.get('epg_matches', [])
    recording_ids = []
    filenames = []
    duplicates_skipped = 0
    
    print(f"Series recording: Processing {len(epg_matches)} episodes")
    
    for i, epg_match in enumerate(epg_matches):
        # Create a comprehensive recording entry with all metadata
        recording_info = {
            'id': len(scheduled_jobs) + 1,  # Simple ID generation
            'title': epg_match.get('title', parsed.get('event', 'Unknown Show')),
            'channel': epg_match.get('channel', parsed.get('channel', 'Unknown Channel')),
            'channel_number': epg_match.get('channel_number', ''),
            'call_sign': epg_match.get('call_sign', ''),
            'date': epg_match.get('date', parsed.get('date', '')),
            'time': epg_match.get('time', parsed.get('time', '')),
            'period': epg_match.get('period', 'Unknown'),
            'scheduled_at': datetime.now().isoformat(),
            'status': 'scheduled',
            'series_recording': True,  # Mark as part of series
            'series_group': parsed.get('event', 'Unknown Show'),  # Group identifier
            # Enhanced metadata from EPG
            'episode_title': epg_match.get('episode_title', ''),
            'season_number': epg_match.get('season_number', ''),
            'episode_number': epg_match.get('episode_number', ''),
            'episode_id': epg_match.get('episode_id', ''),
            'original_air_date': epg_match.get('original_air_date', ''),
            'description': epg_match.get('description', ''),
            'genre': epg_match.get('genre', ''),
            'rating': epg_match.get('rating', ''),
            'year': epg_match.get('year', ''),
            'duration': epg_match.get('duration', '')
        }
        
        # Check for duplicates before adding
        if is_duplicate_recording(recording_info):
            print(f"  Skipping duplicate: {recording_info['title']} on {recording_info['date']} at {recording_info['time']}")
            duplicates_skipped += 1
            continue
        
        # Generate enhanced filename with episode info
        suggested_filename = generate_filename(recording_info)
        recording_info['suggested_filename'] = suggested_filename
        
        # Add to scheduled jobs
        scheduled_jobs.append(recording_info)
        recording_ids.append(recording_info['id'])
        filenames.append(suggested_filename)
        
        # Save metadata file for this recording
        save_metadata_file(recording_info, suggested_filename)
        
        # Enhanced logging
        log_msg = f"  Episode {len(recording_ids)}: {recording_info['title']}"
        if recording_info['episode_id']:
            log_msg += f" {recording_info['episode_id']}"
        if recording_info['episode_title']:
            log_msg += f" - {recording_info['episode_title']}"
        log_msg += f" on {recording_info['date']} at {recording_info['time']}"
        print(log_msg)
    
    # Save to disk
    save_schedule()
    
    series_name = parsed.get('event', 'Unknown Show')
    scheduled_count = len(recording_ids)
    
    print(f"Series recording complete: {scheduled_count} episodes of '{series_name}' scheduled")
    if duplicates_skipped > 0:
        print(f"  {duplicates_skipped} duplicate episodes skipped")
    
    return {
        "status": "series_scheduled", 
        "details": parsed, 
        "recording_ids": recording_ids, 
        "filenames": filenames,
        "episode_count": scheduled_count,
        "duplicates_skipped": duplicates_skipped,
        "series_name": series_name
    }

def handle_single_recording(parsed):
    """Handle recording a single episode"""
    # Add the recording to the scheduled jobs list
    epg_match = parsed.get('epg_match', {})
    
    # Create a comprehensive recording entry with all metadata
    recording_info = {
        'id': len(scheduled_jobs) + 1,  # Simple ID generation
        'title': epg_match.get('title', parsed.get('event', 'Unknown Show')),
        'channel': epg_match.get('channel', parsed.get('channel', 'Unknown Channel')),
        'channel_number': epg_match.get('channel_number', ''),
        'call_sign': epg_match.get('call_sign', ''),
        'date': epg_match.get('date', parsed.get('date', '')),
        'time': epg_match.get('time', parsed.get('time', '')),
        'period': epg_match.get('period', 'Unknown'),
        'scheduled_at': datetime.now().isoformat(),
        'status': 'scheduled',
        'series_recording': False,  # Single episode
        # Enhanced metadata from EPG
        'episode_title': epg_match.get('episode_title', ''),
        'season_number': epg_match.get('season_number', ''),
        'episode_number': epg_match.get('episode_number', ''),
        'episode_id': epg_match.get('episode_id', ''),
        'original_air_date': epg_match.get('original_air_date', ''),
        'description': epg_match.get('description', ''),
        'genre': epg_match.get('genre', ''),
        'rating': epg_match.get('rating', ''),
        'year': epg_match.get('year', ''),
        'duration': epg_match.get('duration', '')
    }
    
    # Check for duplicates before adding
    if is_duplicate_recording(recording_info):
        print(f"Duplicate recording detected: {recording_info['title']} on {recording_info['date']} at {recording_info['time']}")
        return {"status": "duplicate", "details": parsed, "message": "This recording is already scheduled"}
    
    # Generate enhanced filename with episode info
    suggested_filename = generate_filename(recording_info)
    recording_info['suggested_filename'] = suggested_filename
    
    # Add to scheduled jobs
    scheduled_jobs.append(recording_info)
    
    # Save to disk
    save_schedule()
    
    # Save metadata file for this recording
    save_metadata_file(recording_info, suggested_filename)
    
    # Enhanced logging
    log_msg = f"Recording scheduled: {recording_info['title']}"
    if recording_info['episode_id']:
        log_msg += f" {recording_info['episode_id']}"
    if recording_info['episode_title']:
        log_msg += f" - {recording_info['episode_title']}"
    log_msg += f" on {recording_info['channel']} at {recording_info['time']}"
    if recording_info['original_air_date']:
        log_msg += f" (Originally aired: {recording_info['original_air_date']})"
    
    print(log_msg)
    print(f"Suggested filename: {suggested_filename}")
    
    return {"status": "scheduled", "details": parsed, "recording_id": recording_info['id'], "filename": suggested_filename}

def is_duplicate_recording(new_recording):
    """Check if a recording is already scheduled"""
    for existing in scheduled_jobs:
        # Skip recurring recording rules (they have a different structure)
        if existing.get('type') == 'recurring_series':
            continue
            
        # Only check individual episode recordings that have the expected fields
        if not all(key in existing for key in ['title', 'date', 'time', 'channel_number']):
            continue
            
        # Check for exact match on title, date, and time
        if (existing['title'] == new_recording['title'] and
            existing['date'] == new_recording['date'] and
            existing['time'] == new_recording['time'] and
            existing['channel_number'] == new_recording['channel_number']):
            return True
        
        # Check for same episode ID if available
        if (new_recording.get('episode_id') and existing.get('episode_id') and
            existing['episode_id'] == new_recording['episode_id'] and
            existing['title'] == new_recording['title']):
            return True
            
        # Check for same original air date (avoid recording reruns)
        if (new_recording.get('original_air_date') and existing.get('original_air_date') and
            existing['original_air_date'] == new_recording['original_air_date'] and
            existing['title'] == new_recording['title']):
            return True
    
    return False
    
    # Create a comprehensive recording entry with all metadata
    recording_info = {
        'id': len(scheduled_jobs) + 1,  # Simple ID generation
        'title': epg_match.get('title', parsed.get('event', 'Unknown Show')),
        'channel': epg_match.get('channel', parsed.get('channel', 'Unknown Channel')),
        'channel_number': epg_match.get('channel_number', ''),
        'call_sign': epg_match.get('call_sign', ''),
        'date': epg_match.get('date', parsed.get('date', '')),
        'time': epg_match.get('time', parsed.get('time', '')),
        'period': epg_match.get('period', 'Unknown'),
        'scheduled_at': datetime.now().isoformat(),
        'status': 'scheduled',
        # Enhanced metadata from EPG
        'episode_title': epg_match.get('episode_title', ''),
        'season_number': epg_match.get('season_number', ''),
        'episode_number': epg_match.get('episode_number', ''),
        'episode_id': epg_match.get('episode_id', ''),
        'original_air_date': epg_match.get('original_air_date', ''),
        'description': epg_match.get('description', ''),
        'genre': epg_match.get('genre', ''),
        'rating': epg_match.get('rating', ''),
        'year': epg_match.get('year', ''),
        'duration': epg_match.get('duration', '')
    }
    
    # Generate enhanced filename with episode info
    suggested_filename = generate_filename(recording_info)
    recording_info['suggested_filename'] = suggested_filename
    
    # Add to scheduled jobs
    scheduled_jobs.append(recording_info)
    
    # Save to disk
    save_schedule()
    
    # Save metadata file for this recording
    save_metadata_file(recording_info, suggested_filename)
    
    # Enhanced logging
    log_msg = f"Recording scheduled: {recording_info['title']}"
    if recording_info['episode_id']:
        log_msg += f" {recording_info['episode_id']}"
    if recording_info['episode_title']:
        log_msg += f" - {recording_info['episode_title']}"
    log_msg += f" on {recording_info['channel']} at {recording_info['time']}"
    if recording_info['original_air_date']:
        log_msg += f" (Originally aired: {recording_info['original_air_date']})"
    
    print(log_msg)
    print(f"Suggested filename: {suggested_filename}")
    
    return {"status": "scheduled", "details": parsed, "recording_id": recording_info['id'], "filename": suggested_filename}
def agent_download(parsed):
    # Integrate with qBittorrent/libtorrent here
    # For now, just return a stub response
    return {"status": "download started", "details": parsed}

def agent_organize(parsed):
    # Organize/rename/move media files for Plex/Jellyfin
    # For now, just return a stub response
    return {"status": "media organized", "details": parsed}

def agent_unknown(parsed):
    return {"status": "unknown command", "details": parsed}

def dispatch_agent(parsed):
    action = parsed.get("action")
    if action == "record":
        return agent_record(parsed)
    elif action == "download":
        return agent_download(parsed)
    elif action == "organize":
        return agent_organize(parsed)
    else:
        return agent_unknown(parsed)


# --- Flask Routes ---
@app.route('/nlp_command', methods=['POST'])
def nlp_command():
    try:
        data = request.get_json()
        if not data or "command" not in data:
            return jsonify({"error": "Missing 'command' field"}), 400
        command = data["command"]
        parsed = parse_nlp_command(command)
        # If channel is provided explicitly, use it as fallback/override
        if "channel" in data and data["channel"]:
            parsed["channel"] = data["channel"]
        result = dispatch_agent(parsed)
        return jsonify({"parsed": parsed, "result": result})
    except Exception as e:
        import traceback
        print("/nlp_command error:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# API Routes for external access
@app.route('/api/record', methods=['POST'])
def api_record():
    """API endpoint for recording commands"""
    return nlp_command()  # Use the same logic as nlp_command

@app.route('/api/scheduled_recordings', methods=['GET'])
def api_scheduled_recordings():
    """API endpoint to get scheduled recordings"""
    return jsonify(scheduled_jobs)

threading.Thread(target=run_schedule_loop, daemon=True).start()

# === Flask Routes ===

@app.route("/")
def index():
    # scheduled_jobs now contains dictionaries with recording info
    scheduled = scheduled_jobs  # Pass the full list of recording dictionaries
    return render_template("index.html", channels=channels.keys(), scheduled=scheduled, days=days_list)

@app.route("/record_now", methods=["POST"])
def record_now():
    data = request.get_json()
    run_threaded(record_channel, data['channel'], int(data['duration']),
                 int(data['crf']), data['preset'], data['format'])
    return jsonify({"message": f"Recording {data['channel']} started."})

@app.route("/stop_recording", methods=["POST"])
def stop_recording():
    global stop_event
    stop_event.set()
    return jsonify({"message":"Stop signal sent."})

@app.route("/schedule", methods=["POST"])
def schedule_recording():
    data = request.get_json()
    try:
        for day in data['days']:
            job = getattr(schedule.every(), day.lower()).at(data['time']).do(
                run_threaded, record_channel, data['channel'], int(data['duration']),
                int(data['crf']), data['preset'], data['format']
            )
            scheduled_jobs.append((job, f"{channels[data['channel']]} - {day} at {data['time']} for {data['duration']} min"))
        save_schedule()
        return jsonify({"message":"Recording(s) scheduled successfully."})
    except Exception as e:
        return jsonify({"message":f"Error scheduling: {e}"}), 400

@app.route("/cancel", methods=["POST"])
def cancel():
    data = request.get_json()
    idx = int(data['idx'])
    if 0 <= idx < len(scheduled_jobs):
        # Remove the recording from the list
        removed_recording = scheduled_jobs.pop(idx)
        save_schedule()
        print(f"Canceled recording: {removed_recording['title']} on {removed_recording['channel']}")
        return jsonify({"message": f"Canceled recording: {removed_recording['title']}"})
    return jsonify({"message":"Invalid index."}), 400

@app.route("/cancel_series", methods=["POST"])
def cancel_series():
    data = request.get_json()
    series_name = data.get('series_name', '')
    
    if not series_name:
        return jsonify({"message": "Series name required."}), 400
    
    # Find all recordings that belong to this series
    original_count = len(scheduled_jobs)
    scheduled_jobs[:] = [job for job in scheduled_jobs 
                        if not (job.get('series_recording') and 
                               (job.get('series_group') == series_name or job.get('title') == series_name))]
    
    canceled_count = original_count - len(scheduled_jobs)
    
    if canceled_count > 0:
        save_schedule()
        print(f"Canceled {canceled_count} episodes of series: {series_name}")
        return jsonify({"message": f"Canceled {canceled_count} episodes of '{series_name}'"})
    else:
        return jsonify({"message": f"No episodes found for series '{series_name}'"})

@app.route("/cancel_recurring", methods=["POST"])
def cancel_recurring():
    data = request.get_json()
    rule_id = data.get('rule_id')
    
    if rule_id is None:
        return jsonify({"message": "Rule ID required."}), 400
    
    # Find and remove the recurring rule
    rule_to_remove = None
    
    for i, job in enumerate(scheduled_jobs):
        if job.get('type') == 'recurring_series' and job.get('id') == rule_id:
            rule_to_remove = scheduled_jobs.pop(i)
            break
    
    if rule_to_remove:
        save_schedule()
        episode_count = len(rule_to_remove.get('episodes', []))
        print(f"Canceled recurring series: {rule_to_remove['title']} ({episode_count} episodes)")
        return jsonify({"message": f"Canceled recurring series '{rule_to_remove['title']}' ({episode_count} episodes)"})
    else:
        return jsonify({"message": "Recurring series rule not found"})

@app.route("/cancel_next_episode", methods=["POST"])
def cancel_next_episode():
    data = request.get_json()
    rule_id = data.get('rule_id')
    
    if rule_id is None:
        return jsonify({"message": "Rule ID required."}), 400
    
    # Find the recurring rule and remove the next episode
    for job in scheduled_jobs:
        if job.get('type') == 'recurring_series' and job.get('id') == rule_id:
            episodes = job.get('episodes', [])
            if episodes:
                next_episode = episodes.pop(0)  # Remove the first (next) episode
                
                # Update the next episode pointer
                if episodes:
                    job['next_episode'] = episodes[0]
                else:
                    job['next_episode'] = None
                    job['status'] = 'completed'  # No more episodes
                
                save_schedule()
                episode_info = f"{next_episode.get('date')} at {next_episode.get('time')}"
                if next_episode.get('episode_id'):
                    episode_info += f" ({next_episode['episode_id']})"
                
                print(f"Canceled next episode of {job['title']}: {episode_info}")
                return jsonify({"message": f"Canceled next episode: {episode_info}"})
            else:
                return jsonify({"message": "No episodes remaining for this series"})
    
    return jsonify({"message": "Recurring series rule not found"})

if __name__=="__main__":
    # Load existing scheduled recordings
    load_schedule()
    
    # Start the schedule loop in a background thread
    threading.Thread(target=run_schedule_loop, daemon=True).start()
    
    app.run(host="0.0.0.0", port=5000)

