# Set up environment variables FIRST (before any imports that might use them)
import os
from config_manager import get_config

# Load configuration
config = get_config()

# Prowlarr integration defaults (must be set before prowlarr_client imports)
if config.is_prowlarr_enabled():
    prowlarr_config = config.get_prowlarr_config()
    os.environ.setdefault("PROWLARR_API_URL", prowlarr_config['api_url'])
    os.environ.setdefault("PROWLARR_API_KEY", prowlarr_config['api_key'])
    os.environ.setdefault("PROWLARR_TIMEOUT", str(prowlarr_config['timeout']))
else:
    os.environ.setdefault("PROWLARR_API_URL", "http://127.0.0.1:9696")
    os.environ.setdefault("PROWLARR_API_KEY", "")
    os.environ.setdefault("PROWLARR_TIMEOUT", "15")

# Utility: run a function in a new thread
def run_threaded(func, *args, **kwargs):
    t = threading.Thread(target=func, args=args, kwargs=kwargs)
    t.start()
    return t

# Utility: save the schedule to disk
def save_schedule():
    try:
        print(f"DEBUG: Saving {len(scheduled_jobs)} recordings to {SCHEDULE_FILE}")
        # Ensure we only persist serializable dict-based jobs. If any legacy tuple
        # entries (job_obj, description) exist, convert them to a dict form.
        serializable = []
        for entry in scheduled_jobs:
            if isinstance(entry, tuple) and len(entry) == 2:
                # Legacy format: (schedule_job_object, description_string)
                serializable.append({
                    'id': len(serializable) + 1,
                    'type': 'legacy_scheduled',
                    'description': entry[1],
                    'created_at': datetime.now().isoformat()
                })
            elif isinstance(entry, dict):
                # Ensure it has an id
                if 'id' not in entry:
                    entry = {**entry, 'id': len(serializable) + 1}
                serializable.append(entry)
            else:
                # Unknown type, skip with warning
                print(f"WARN: Skipping non-serializable scheduled entry: {type(entry)}")
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(serializable, f, indent=2)
        print(f"DEBUG: Save successful!")
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
    refresh_counter = 0
    while True:
        # TODO: implement actual scheduling logic (trigger ffmpeg at times)
        try:
            # Allow jobs created via /schedule endpoint using `schedule` library to run
            try:
                import schedule as _sched
                _sched.run_pending()
            except Exception:
                pass

            # Trigger recurring_series rules (time-based) when their day/time matches
            now_dt = datetime.now()
            now_hhmm = now_dt.strftime('%H:%M')
            now_day = now_dt.strftime('%A')  # e.g., 'Monday'
            
            # Only check jobs that could potentially match today
            active_jobs = [job for job in scheduled_jobs 
                          if job.get('type') == 'recurring_series' and job.get('status') == 'active']
            
            # Filter jobs to only those scheduled for today
            todays_jobs = []
            for job in active_jobs:
                rec = job.get('recurrence') or {}
                days = rec.get('days') or []
                if days:
                    # Map current day to both formats for matching
                    day_mapping = {
                        'Monday': ['Mon', 'Monday'], 'Tuesday': ['Tue', 'Tuesday'], 'Wednesday': ['Wed', 'Wednesday'],
                        'Thursday': ['Thu', 'Thursday'], 'Friday': ['Fri', 'Friday'], 'Saturday': ['Sat', 'Saturday'], 
                        'Sunday': ['Sun', 'Sunday']
                    }
                    valid_day_names = day_mapping.get(now_day, [now_day])
                    if any(day_name in days for day_name in valid_day_names):
                        todays_jobs.append(job)
                else:
                    # No specific days set, include all days
                    todays_jobs.append(job)
            
            # Only process jobs within 5 minutes of their scheduled time to reduce noise
            for job in todays_jobs:
                job_time = job.get('time') or job.get('recurrence', {}).get('time')
                
                # Convert job_time to 24-hour format if needed for comparison
                normalized_job_time = job_time
                if job_time and ('AM' in job_time or 'PM' in job_time):
                    try:
                        # Convert 12-hour format to 24-hour format
                        parsed_time = datetime.strptime(job_time, '%I:%M %p')
                        normalized_job_time = parsed_time.strftime('%H:%M')
                    except:
                        pass  # Keep original format if parsing fails
                elif job_time and ':' in job_time:
                    # Handle times without AM/PM (e.g., "12:23")
                    try:
                        # If it's already in 24-hour format (00:00-23:59), keep as-is
                        hour, minute = map(int, job_time.split(':'))
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            # For times starting with 12 without AM/PM, check context
                            if hour == 12:
                                # Check if this is likely midnight (00:xx) based on other jobs or context
                                # For now, times like "12:xx" without AM/PM in early morning hours
                                # are assumed to be midnight (00:xx) if current time is also early morning
                                if now_dt.hour < 6:  # Between midnight and 6 AM
                                    normalized_job_time = f"00:{minute:02d}"
                                else:
                                    normalized_job_time = f"{hour:02d}:{minute:02d}"
                            else:
                                normalized_job_time = f"{hour:02d}:{minute:02d}"
                    except:
                        pass  # Keep original format if parsing fails
                
                # Only check jobs within 5 minutes of scheduled time to reduce log noise
                if not normalized_job_time:
                    continue
                    
                try:
                    job_hour, job_minute = map(int, normalized_job_time.split(':'))
                    job_minutes_total = job_hour * 60 + job_minute
                    current_minutes_total = now_dt.hour * 60 + now_dt.minute
                    time_diff = abs(job_minutes_total - current_minutes_total)
                    
                    # Handle wrap-around (e.g., 23:59 vs 00:01)
                    if time_diff > 720:  # 12 hours
                        time_diff = 1440 - time_diff  # 24 hours - diff
                    
                    # Only log and process jobs within 5 minutes of their scheduled time
                    if time_diff > 5:
                        continue
                        
                except Exception:
                    # If time parsing fails, continue with full check for safety
                    pass
                
                # Debug: Log scheduler evaluation (only for jobs being actively checked)
                print(f"[Scheduler] Checking job '{job.get('title')}' - Channel: {job.get('channel_number')}, Time: {job.get('time')}, Days: {job.get('recurrence', {}).get('days', [])}")
                
                # Debug time conversion
                if job_time != normalized_job_time:
                    print(f"[Scheduler DEBUG] Time conversion: '{job_time}' → '{normalized_job_time}' (current: {now_hhmm})")
                if not normalized_job_time or normalized_job_time != now_hhmm:
                    # Debug logging for missed schedules
                    if normalized_job_time and abs((datetime.strptime(normalized_job_time, '%H:%M').time().hour * 60 + datetime.strptime(normalized_job_time, '%H:%M').time().minute) - (now_dt.hour * 60 + now_dt.minute)) <= 2:
                        print(f"[Scheduler DEBUG] Job '{job.get('title')}' time {normalized_job_time} vs current {now_hhmm} - missed by {abs((datetime.strptime(normalized_job_time, '%H:%M').time().hour * 60 + datetime.strptime(normalized_job_time, '%H:%M').time().minute) - (now_dt.hour * 60 + now_dt.minute))} minutes")
                    continue
                # Prevent duplicate triggers within the same minute
                last = job.get('last_started_at')
                if last:
                    try:
                        from datetime import datetime as _dt
                        last_dt = _dt.fromisoformat(last)
                        if (now_dt - last_dt).total_seconds() < 55:
                            continue
                    except Exception:
                        pass
                # Start recording
                try:
                    ch_num = job.get('channel_number')
                    dur_min = int(job.get('duration') or 30)
                    crf = int(job.get('crf') or 23)
                    preset = job.get('preset') or 'fast'
                    fmt = job.get('format') or 'mp4'
                    print(f"[Scheduler] Starting '{job.get('title')}' on {ch_num} for {dur_min} min (rule #{job.get('id')})")
                    started_at_iso = now_dt.isoformat()
                    run_threaded(record_channel, ch_num, dur_min, crf, preset, fmt, started_at=started_at_iso)
                    job['last_started_at'] = started_at_iso
                    save_schedule()
                except Exception as _e:
                    print(f"[Scheduler] Failed to start recording for rule #{job.get('id')}: {_e}")

            # Trigger one-off scheduled episode recordings (those created by NLP/EPG with specific date+time)
            # Criteria: has 'status' == 'scheduled', has explicit 'date' (YYYY-MM-DD) and 'time' (HH:MM), and not already started
            try:
                from datetime import datetime as _dt
                for job in list(scheduled_jobs):
                    if job.get('status') != 'scheduled':
                        continue
                    # Skip rules and other types that don't represent a one-off episode
                    if job.get('type') in ('recurring_series', 'one_time_timeslot'):
                        continue
                    date_str = job.get('date')
                    time_str = job.get('time')
                    ch_num = job.get('channel_number') or job.get('channel')
                    if not (date_str and time_str and ch_num):
                        continue
                    try:
                        dt_obj = _dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    except Exception:
                        continue
                    # Start within the minute it matches, and avoid retriggering
                    if abs((now_dt - dt_obj).total_seconds()) <= 59:
                        if job.get('last_started_at'):
                            continue
                        dur_min = int(job.get('duration') or 30)
                        crf = int(job.get('crf') or 23)
                        preset = job.get('preset') or 'fast'
                        fmt = job.get('format') or 'mp4'
                        print(f"[Scheduler] Starting one-off '{job.get('title')}' on {ch_num} for {dur_min} min at {date_str} {time_str}")
                        started_at_iso = now_dt.isoformat()
                        run_threaded(record_channel, ch_num, dur_min, crf, preset, fmt, started_at=started_at_iso)
                        job['last_started_at'] = started_at_iso
                        job['status'] = 'recording'
                        save_schedule()
            except Exception as _e2:
                print(f"[Scheduler] Error while checking one-off episodes: {_e2}")

            # Show scheduler heartbeat every 10 minutes instead of constant job checking
            if refresh_counter % 10 == 0:
                active_count = len([j for j in scheduled_jobs if j.get('type') == 'recurring_series' and j.get('status') == 'active'])
                print(f"[Scheduler Heartbeat] {active_count} active recording rules")

            time.sleep(60)
        except Exception:
            # Ensure loop keeps running even if an iteration fails
            time.sleep(60)
        refresh_counter += 1
        # Optional: twice weekly EPG refresh (enabled by default)
        try:
            import os as _os_loop
            if _os_loop.getenv('ENABLE_BACKGROUND_EPG_REFRESH','1') in ('1','true','True'):
                if refresh_counter % 30 == 0:
                    try:
                        print("[EPG Auto-Refresh] Starting twice-weekly EPG cache refresh...")
                        # Force refresh of the main EPG cache
                        global EPG_CACHE
                        EPG_CACHE["data"] = None  # Clear cache to force fresh fetch
                        EPG_CACHE["timestamp"] = 0
                        
                        # Get fresh EPG data (this will fetch and cache automatically)
                        epg = get_epg()
                        if not epg:
                            print("[EPG Auto-Refresh] Failed to fetch fresh EPG data")
                            continue
                        
                        print(f"[EPG Auto-Refresh] Successfully refreshed cache with {len(epg)} programs")
                        
                        # Also update job sample episodes for existing recurring rules
                        upcoming_map = {}
                        now = datetime.now()
                        for entry in epg:
                            ch_num = entry.get('channel_number')
                            time_str = entry.get('time')
                            date_str = entry.get('date')
                            if not (ch_num and time_str and date_str):
                                continue
                            try:
                                dt_obj = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                                if dt_obj < now:
                                    continue
                            except Exception:
                                continue
                            key = (ch_num, time_str)
                            upcoming_map.setdefault(key, []).append(entry)
                        
                        updated = 0
                        for job in scheduled_jobs:
                            if job.get('type') == 'recurring_series' and job.get('is_time_based'):
                                key = (job.get('channel_number'), job.get('time'))
                                new_samples = upcoming_map.get(key)
                                if new_samples:
                                    job['sample_episodes'] = new_samples[:10]
                                    job['next_episode'] = new_samples[0]
                                    updated += 1
                        if updated:
                            print(f"[EPG Auto-Refresh] Updated {updated} recurring series with fresh episode data")
                            save_schedule()
                    except Exception:
                        # Ignore transient errors during periodic EPG sampling
                        pass
            else:
                if refresh_counter % 30 == 0:
                    # Keep logs quiet but show a heartbeat occasionally without fetching EPG
                    print("Scheduler heartbeat: recurring rules active; background EPG refresh disabled (set ENABLE_BACKGROUND_EPG_REFRESH=1 to enable)")
        except Exception:
            # Never let the loop crash due to background refresh bookkeeping
            pass
        except Exception as e:
            print(f"EPG refresh block error: {e}")
    # (Unreachable code after loop intentionally removed)

import os  # ensure os imported at top-level for path handling
import re

# Dedicated library roots used ONLY for organizing torrent download targets.
# NOTE: Standard OTA recordings via HDHomeRun continue to use SAVE_DIR and are
# NOT redirected to these folders. This segregation applies strictly to
# torrent workflows so user recordings remain untouched.
TV_SHOWS_DIR = str(config.get_tv_shows_dir())
MOVIES_DIR = str(config.get_movies_dir())
# Indexer integration defaults
import os as _os
INDEXER_ENABLED = config.is_indexer_enabled()
def check_indexer_availability():
    """Check if indexer service is available"""
    if not INDEXER_ENABLED:
        return False
        
    try:
        from indexer_manager import IndexerManager
        indexer = IndexerManager()
        return indexer.is_available()
    except Exception as e:
        print(f"Indexer availability check failed: {e}")
        return False

# Unified torrent search function using configured indexer
def unified_torrent_search(query: str, content_type: str = "tv", sort: str = None) -> tuple:
    """
    Unified search function using configured indexer provider.
    
    Args:
        query: Search term
        content_type: "tv" or "movie" for category filtering
        sort: Sort parameter (e.g., 'seeds_desc')
    
    Returns:
        Tuple of (provider_name, list_of_torrents)
    """
    print(f"🔍 Searching for '{query}' (type: {content_type})")
    
    if not INDEXER_ENABLED:
        print("⚠️ Indexer integration is disabled")
        return ("disabled", [])
    
    try:
        from indexer_manager import IndexerManager
        
        indexer = IndexerManager()
        provider = indexer.provider
        
        print(f"📡 Using {provider} indexer for search")
        
        # Map content type to category
        category = None
        if content_type == "tv":
            category = "5000"  # TV category
        elif content_type == "movie":
            category = "2000"  # Movie category
        
        result = indexer.search(query, category=category, limit=50)
        
        if 'error' in result:
            print(f"❌ Indexer search failed: {result['error']}")
            return ("error", [])
        
        results = result.get('results', [])
        print(f"✅ {provider} returned {len(results)} results")
        return (provider, results)
        
    except ImportError as e:
        print(f"❌ Indexer manager not available: {e}")
        return ("error", [])
    except Exception as e:
        print(f"❌ Indexer search failed: {e}")
        return ("error", [])
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
HDHR_IP = config.get_hdhr_ip()
SAVE_DIR = str(config.get_recording_dir())
FFMPEG_PATH = config.get_ffmpeg_path()
SCHEDULE_FILE = os.path.join(SAVE_DIR, "scheduled_jobs.json")

os.makedirs(SAVE_DIR, exist_ok=True)
scheduled_jobs = []
current_process = None
stop_event = threading.Event()

app = Flask(__name__)
from epg_zap2it import fetch_zap2it_epg
import time

# EPG caching with disk persistence
EPG_CACHE = {"data": None, "timestamp": 0}
EPG_TTL = 60 * 60 * 24 * 3.5  # 3.5 days - twice weekly refresh
EPG_CACHE_FILE = os.path.join(SAVE_DIR, "epg_cache.json")

def load_epg_cache():
    """Load EPG cache from disk if available"""
    try:
        if os.path.exists(EPG_CACHE_FILE):
            with open(EPG_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                EPG_CACHE["data"] = cache_data.get("data")
                EPG_CACHE["timestamp"] = cache_data.get("timestamp", 0)
                cache_age = time.time() - EPG_CACHE["timestamp"]
                print(f"EPG: loaded from disk (age: {cache_age/60:.1f} minutes)")
                return True
    except Exception as e:
        print(f"EPG: failed to load cache from disk: {e}")
    return False

def save_epg_cache():
    """Save EPG cache to disk"""
    try:
        cache_data = {
            "data": EPG_CACHE["data"],
            "timestamp": EPG_CACHE["timestamp"]
        }
        with open(EPG_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print(f"EPG: saved cache to disk ({len(EPG_CACHE['data']) if EPG_CACHE['data'] else 0} programs)")
    except Exception as e:
        print(f"EPG: failed to save cache to disk: {e}")

def get_epg():
    """Return cached EPG; fetch if cache empty or expired."""
    now = time.time()
    
    # Load from disk if memory cache is empty
    if EPG_CACHE["data"] is None:
        load_epg_cache()
    
    cache_age = now - EPG_CACHE["timestamp"]
    
    # Check if we need to fetch: cache empty or expired
    if EPG_CACHE["data"] is None or cache_age > EPG_TTL:
        try:
            if EPG_CACHE["data"] is None:
                print("EPG: fetching fresh data (no cache available)")
            else:
                print(f"EPG: fetching fresh data (cache expired after {cache_age/60:.1f} minutes)")
            
            EPG_CACHE["data"] = fetch_zap2it_epg()
            EPG_CACHE["timestamp"] = now
            
            # Save to disk
            save_epg_cache()
            
            print(f"EPG: fetched and cached {len(EPG_CACHE['data']) if EPG_CACHE['data'] else 0} programs")
        except Exception as e:
            print(f"EPG fetch failed: {e}")
            # Return stale data if available, otherwise None
            return EPG_CACHE["data"]
    else:
        print(f"EPG: using cached data (age: {cache_age/60:.1f} minutes)")
    
    return EPG_CACHE["data"]

def search_cached_epg(query, days=7):
    """Search through cached EPG data instead of fetching fresh data"""
    print(f"Searching cached EPG for: '{query}'")
    
    # Use cached EPG data
    epg_data = get_epg()
    if not epg_data:
        print("No cached EPG data available")
        return []
    
    # Search through cached EPG data for matches
    matching_episodes = []
    query_lower = query.lower()
    query_words = [word.strip() for word in query_lower.split()]
    
    now = datetime.now()
    cutoff = now + timedelta(days=days)
    
    for entry in epg_data:
        try:
            # Check if the show matches our query
            title = (entry.get('title', '') or '').lower()
            description = (entry.get('description', '') or '').lower()
            episode_title = (entry.get('episode_title', '') or '').lower()
            
            # Match against title, description, episode title, or genre
            matches = (
                any(word in title for word in query_words) or
                any(word in description for word in query_words) or
                any(word in episode_title for word in query_words) or
                query_lower in title or 
                query_lower in description or
                query_lower in episode_title or
                any(query_lower in (entry.get('genre', '') or '').lower().split())
            )
            
            if matches:
                # Parse the air time to filter future shows only
                date_str = entry.get('date', '')
                time_str = entry.get('time', '')
                
                if date_str and time_str:
                    try:
                        # Handle both 12-hour and 24-hour formats
                        if 'AM' in time_str or 'PM' in time_str:
                            air_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
                        else:
                            air_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                            
                        if now <= air_datetime <= cutoff:
                            matching_episodes.append(entry)
                    except Exception as e:
                        # If date parsing fails, include it anyway for future dates
                        if date_str >= now.strftime('%Y-%m-%d'):
                            matching_episodes.append(entry)
                else:
                    matching_episodes.append(entry)
                    
        except Exception as e:
            continue  # Skip problematic entries
    
    print(f"Found {len(matching_episodes)} cached matches for '{query}'")
    return matching_episodes

import schedule
t = time
# NOTE: The following block was duplicated earlier in the file which caused the
# schedule to be loaded and then immediately overwritten by resetting
# scheduled_jobs = []. We keep the first initialization near the top of the file
# (where SCHEDULE_FILE, scheduled_jobs, current_process, stop_event, and app are
# already defined) and remove the duplicate to preserve persisted recordings.
# If you need to re-init for tests, do it explicitly rather than on import.

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

def record_channel(channel_key, duration_min, crf=23, preset="fast", record_format="mp4", started_at=None):
    global current_process, stop_event
    chname = channels[channel_key]
    # Use a filesystem-friendly timestamp for the output filename and keep an ISO timestamp for job tracking
    started_at = started_at or datetime.now().isoformat()
    now = datetime.fromisoformat(started_at).strftime("%Y-%m-%d_%H-%M")
    ext = ".mp4" if record_format=="mp4" else ".ts"
    filename = f"{chname}_{now}{ext}"
    filepath = os.path.join(SAVE_DIR, filename)
    url = f"http://{HDHR_IP}:5004/auto/v{channel_key}"

    stop_event.clear()

    # Determine ffmpeg binary: prefer configured path, fallback to system ffmpeg
    ffmpeg_bin = FFMPEG_PATH if os.path.exists(FFMPEG_PATH) else "ffmpeg"

    if record_format == "mp4":
        cmd = [
            ffmpeg_bin, "-i", url, "-t", str(duration_min*60),
            "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-y", filepath
        ]
    else:
        cmd = [
            ffmpeg_bin, "-i", url, "-t", str(duration_min*60),
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
    # Attempt to mark matching scheduled job as completed
    try:
        for job in reversed(scheduled_jobs):  # search latest first
            if job.get('status') == 'recording' and str(job.get('channel_number')) == str(channel_key):
                # Match by start time within a 2-minute window
                try:
                    js = job.get('last_started_at')
                    if js:
                        jdt = datetime.fromisoformat(js)
                        sdt = datetime.fromisoformat(started_at)
                        if abs((jdt - sdt).total_seconds()) <= 120:
                            job['status'] = 'completed'
                            job['completed_at'] = datetime.now().isoformat()
                            job['output_file'] = os.path.basename(filepath)
                            save_schedule()
                            break
                except Exception:
                    pass
    except Exception as _e:
        print(f"WARN: Could not finalize job for channel {channel_key}: {_e}")

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
    """Simplified NLP parser that works with any show name.

    Adds support for explicit weekday phrasing like:
      'record antiques roadshow each monday'
      'record antiques roadshow every tuesday'
      'record antiques roadshow on mondays'
    which will force a weekly recurring rule even if only one future airing is
    currently visible in the EPG.
    """
    result = {"action": None, "event": None, "series_recording": False, "next_only": False}
    cmd = command.lower().strip()

    # Fast-path: option selection commands (must come before generic show extraction)
    opt_recurring_match = re.search(r'record\s+recurring\s+option\s+(\d+)', cmd)
    opt_once_match = re.search(r'record\s+option\s+(\d+)', cmd)
    if opt_recurring_match:
        result['action'] = 'record'
        result['record_recurring_option'] = int(opt_recurring_match.group(1))
        return result
    if opt_once_match:
        result['action'] = 'record'
        result['record_option'] = int(opt_once_match.group(1))
        return result

    # Handle VPN control commands (order matters - more specific patterns first)
    vpn_patterns = [
        (r'(?:disconnect|stop|turn off|disable)\s+(?:the\s+)?vpn', 'disconnect'),
        (r'(?:connect|start|turn on|enable)\s+(?:the\s+)?vpn', 'connect'),
        (r'(?:check|status|show)(?:\s+me)?\s+(?:the\s+)?vpn(?:\s+status)?', 'status'),
        (r'vpn\s+(?:disconnect|stop|off)', 'disconnect'),
        (r'vpn\s+(?:connect|start|on)', 'connect'),
        (r'vpn\s+(?:status|check)', 'status')
    ]
    
    for pattern, action in vpn_patterns:
        if re.search(pattern, cmd):
            result['action'] = 'vpn'
            result['vpn_action'] = action
            return result

    # Handle "show me" queries for EPG browsing
    browse_patterns = [
        r'show me (?:all )?(?:shows? )?(?:this week )?(?:with )?(.+)',
        r'find (?:all )?(?:shows? )?(?:this week )?(?:with )?(.+)', 
        r'search for (?:all )?(?:shows? )?(?:this week )?(?:with )?(.+)',
        r'list (?:all )?(?:shows? )?(?:this week )?(?:with )?(.+)',
        r'what (?:shows? )?(?:are )?(?:on )?(?:this week )?(?:with )?(.+)'
    ]
    
    for pattern in browse_patterns:
        match = re.search(pattern, cmd)
        if match:
            result["action"] = "browse"
            result["query"] = match.group(1).strip()
            return result

    if "record" in cmd:
        result["action"] = "record"
        # Detect explicit "next episode" intent FIRST
        next_episode_keywords = ["next episode", "upcoming episode", "the next one"]
        if any(k in cmd for k in next_episode_keywords):
            result["next_only"] = True

        # Check for series recording keywords (only if not explicitly next-only)
        series_keywords = ['all episodes', 'every episode', 'series', 'all shows', 'every show', 'daily', 'weekdays', 'all of', 'every']
        if not result["next_only"]:
            result["series_recording"] = any(keyword in cmd for keyword in series_keywords)

        # Detect explicit weekday recurrence phrases ("each monday", "every monday", "on monday")
        weekday_pattern = re.compile(r'(?:each|every|on)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)s?')
        weekday_match = weekday_pattern.search(cmd)
        if weekday_match:
            result['series_recording'] = True
            result['explicit_weekday'] = weekday_match.group(1)

        # Expand the alias 'weekdays' (Mon-Fri) if user requested it
        if 'weekdays' in cmd:
            result['series_recording'] = True
            result['explicit_weekdays'] = ['monday','tuesday','wednesday','thursday','friday']

        # Retention: phrases like 'for 6 weeks', 'for 3 week', 'until 2025-12-31'
        retention_weeks_match = re.search(r'for\s+(\d+)\s+weeks?', cmd)
        if retention_weeks_match:
            result['retention_weeks'] = int(retention_weeks_match.group(1))
        retention_until_match = re.search(r'until\s+(\d{4}-\d{2}-\d{2})', cmd)
        if retention_until_match:
            result['retention_until'] = retention_until_match.group(1)

        # Exclusion: "every day except saturday" or "record show every day except sunday"
        exclusion_match = re.search(r'every day except ([a-z,\s]+)', cmd)
        if exclusion_match:
            excluded_fragment = exclusion_match.group(1)
            excluded_days = re.findall(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', excluded_fragment, re.IGNORECASE)
            if excluded_days:
                full_set = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
                result['explicit_weekdays'] = [d for d in full_set if d not in [e.lower() for e in excluded_days]]
                result['series_recording'] = True

        # Multi-day list e.g. "every monday and thursday" or "each tuesday, wednesday"
        multi_day_pattern = re.compile(r'(?:each|every)\s+((?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:[\s,]*(?:and)?\s*)+)', re.IGNORECASE)
        multi_match = multi_day_pattern.search(cmd)
        if multi_match:
            # Extract individual day tokens
            days_fragment = multi_match.group(1)
            day_tokens = re.findall(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', days_fragment, re.IGNORECASE)
            if day_tokens:
                result['series_recording'] = True
                # Store normalized list of distinct lower-case days
                result['explicit_weekdays'] = sorted(set([d.lower() for d in day_tokens]))
                # If one of them previously captured as explicit_weekday keep both forms
                if 'explicit_weekday' in result:
                    if result['explicit_weekday'] not in result['explicit_weekdays']:
                        result['explicit_weekdays'].append(result['explicit_weekday'])

        # Time extraction: phrases like "at 8pm", "at 7:30 pm", "@ 2100"
        time_pattern = re.compile(r'(?:\bat\b|@)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\d{3,4})')
        time_match = time_pattern.search(cmd)
        if time_match:
            raw_time = time_match.group(1).strip()
            norm_time = None
            try:
                # Normalize different formats to HH:MM 24h
                import datetime as _dt
                raw = raw_time.lower().replace(' ', '')
                if re.match(r'^\d{1,2}:\d{2}(am|pm)$', raw):
                    norm_time = _dt.datetime.strptime(raw, '%I:%M%p').strftime('%H:%M')
                elif re.match(r'^\d{1,2}(am|pm)$', raw):
                    norm_time = _dt.datetime.strptime(raw, '%I%p').strftime('%H:%M')
                elif re.match(r'^\d{3,4}$', raw):  # e.g. 2030 or 930
                    if len(raw) == 3:
                        norm_time = f'0{raw[0]}:{raw[1:]}'
                    else:
                        norm_time = f'{raw[0:2]}:{raw[2:]}'
                elif re.match(r'^\d{1,2}:\d{2}$', raw):
                    # Already HH:MM maybe 12h, treat as is
                    parts = raw.split(':')
                    if len(parts[0]) == 1:
                        norm_time = f'0{parts[0]}:{parts[1]}'
                    else:
                        norm_time = raw
                elif re.match(r'^\d{1,2}:\d{2}(?:am|pm)$', raw):
                    norm_time = _dt.datetime.strptime(raw, '%I:%M%p').strftime('%H:%M')
            except Exception:
                pass
            if norm_time:
                result['explicit_time'] = norm_time

        # Extract show name
        show_name = None
        if result["series_recording"]:
            clean_cmd = cmd.replace("record", "").strip()
            for keyword in series_keywords:
                clean_cmd = clean_cmd.replace(keyword, "").strip()
            clean_cmd = clean_cmd.replace(" of ", " ").strip()
            show_name = clean_cmd
        else:
            match = re.search(r'record\s+(.+?)(?:\s+on\s+channel|\s+at\s+|\s*$)', cmd)
            if match:
                show_name = match.group(1).strip()

        if show_name:
            show_name = re.sub(r'\b(the|a|an)\b', '', show_name, flags=re.IGNORECASE).strip()
            show_name = re.sub(r'\s+', ' ', show_name).strip()
            result["event"] = show_name

    # If not a record command, evaluate other high-level intents
    if result["action"] is None and "download" in cmd:
        result["action"] = "download"
        if "magnet:" in cmd:
            magnet_start = cmd.find("magnet:")
            magnet_link = cmd[magnet_start:].strip()
            result["query"] = magnet_link
            result["download_type"] = "direct_magnet"
        elif "http" in cmd and (".torrent" in cmd):
            url_match = re.search(r'(https?://[^\s]+\.torrent)', cmd)
            if url_match:
                result["query"] = url_match.group(1)
                result["download_type"] = "direct_torrent"
        else:
            m = re.search(r'download (.+)', cmd)
            if m:
                query = m.group(1).strip()
                result["query"] = query
                result["download_type"] = "search"
                season_match = re.search(r'season (\d+) of (.+)', query, re.IGNORECASE)
                if season_match:
                    result["season"] = int(season_match.group(1))
                    result["series"] = season_match.group(2).strip()
                    result["download_type"] = "series_season"
                else:
                    season_alt = re.search(r'(.+) season (\d+)', query, re.IGNORECASE)
                    if season_alt:
                        result["series"] = season_alt.group(1).strip()
                        result["season"] = int(season_alt.group(2))
                        result["download_type"] = "series_season"
    elif result["action"] is None and ("organize" in cmd or "move" in cmd):
        result["action"] = "organize"
        m = re.search(r'(?:organize|move) (.+?)(?: to (.+))?', cmd)
        if m:
            result["title"] = m.group(1).strip()
            if m.group(2):
                result["destination"] = m.group(2).strip()
    elif result["action"] is None:
        result["action"] = "unknown"
        result["query"] = command
    # Final debug print AFTER action resolution
    print(f"Parsed command: action='{result['action']}', show='{result['event']}', series={result['series_recording']}, explicit_weekday={result.get('explicit_weekday')}, weekdays_list={result.get('explicit_weekdays')}, time={result.get('explicit_time')}")
    return result

def dispatch_agent(parsed):
    action = parsed.get("action")
    if action == "record":
        return agent_record(parsed)
    elif action == "browse":
        # For browse queries, show all matching episodes without grouping/filtering
        return agent_browse_simple(parsed)
    elif action == "download":
        return agent_download(parsed)
    elif action == "organize":
        return agent_organize(parsed)
    elif action == "vpn":
        return agent_vpn(parsed)
    else:
        return agent_unknown(parsed)

def agent_browse_simple(parsed):
    """Simple browse function that shows all matching episodes without grouping"""
    global LAST_RECORD_CANDIDATES
    query = parsed.get('query', '').strip()
    
    if not query:
        return {"error": "No search query provided"}
    
    print(f"Browsing EPG for shows matching: '{query}'")
    
    # Use cached EPG data instead of fetching fresh data
    epg_data = get_epg()
    if not epg_data:
        return {"error": "No EPG data available. Try refreshing EPG data."}
    
    # Search through cached EPG data for matches
    matching_episodes = []
    query_lower = query.lower()
    
    now = datetime.now()
    cutoff = now + timedelta(days=7)  # Look ahead 7 days
    
    for entry in epg_data:
        try:
            # Check if the show matches our query
            title = (entry.get('title', '') or '').lower()
            description = (entry.get('description', '') or '').lower()
            
            # Match against title, description, or genre
            if (query_lower in title or 
                query_lower in description or 
                any(query_lower in (entry.get('genre', '') or '').lower().split())):
                
                # Parse the air time to filter future shows only
                date_str = entry.get('date', '')
                time_str = entry.get('time', '')
                
                if date_str and time_str:
                    try:
                        air_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
                        if now <= air_datetime <= cutoff:
                            matching_episodes.append(entry)
                    except:
                        # If date parsing fails, include it anyway
                        matching_episodes.append(entry)
                else:
                    matching_episodes.append(entry)
                    
        except Exception as e:
            continue  # Skip problematic entries
    
    if not matching_episodes:
        return {"error": f"No upcoming shows found matching '{query}' in the next 7 days"}
    
    print(f"Found {len(matching_episodes)} matching episodes")
    
    # Sort by date and time
    def sort_key(show):
        try:
            date_str = show.get('date', '9999-12-31')
            time_str = show.get('time', '11:59 PM')
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
        except:
            return datetime.max
    
    matching_episodes.sort(key=sort_key)
    
    # Limit to reasonable number of results (first 15)
    matching_episodes = matching_episodes[:15]
    
    # Create candidate list with all episodes
    candidate_list = []
    for i, episode in enumerate(matching_episodes, 1):
        # Build enhanced title with episode details
        base_title = episode.get('title', 'Unknown Show')
        episode_title = episode.get('episode_title', '')
        
        # For sports, show the specific matchup if available
        display_title = base_title
        if episode_title and episode_title.strip():
            display_title = f"{base_title}: {episode_title}"
        
        # Build description with additional context
        description_parts = []
        if episode.get('description'):
            description_parts.append(episode.get('description'))
        if episode.get('genre'):
            description_parts.append(f"Genre: {episode.get('genre')}")
        if episode.get('rating'):
            description_parts.append(f"Rating: {episode.get('rating')}")
        
        candidate_list.append({
            'option': i,
            'title': display_title,
            'date': episode.get('date', ''),
            'time': episode.get('time', ''),
            'channel': f"{episode.get('call_sign', '')} ({episode.get('channel_number', '')})",
            'duration': f"{episode.get('duration', '30')}min",
            'description': ' | '.join(description_parts) if description_parts else '',
            'genre': episode.get('genre', ''),
            'episode_data': episode  # Store full episode data
        })
    
    # Store for follow-up recording selection
    LAST_RECORD_CANDIDATES = {
        'candidates': matching_episodes,
        'show_name': query,
        'timestamp': time.time()
    }
    
    return {
        'status': 'record_candidates',
        'candidate_type': 'browse_results',
        'message': f"Found {len(candidate_list)} shows matching '{query}'. Use 'record option N' to schedule.",
        'show': query,
        'candidates': candidate_list
    }

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
    global LAST_RECORD_CANDIDATES  # declare once at top to allow assignments later
    
    # Check if this is an option selection command first
    if parsed.get('record_option') or parsed.get('record_recurring_option'):
        # Handle option selection from previous candidates
        if not LAST_RECORD_CANDIDATES or not LAST_RECORD_CANDIDATES.get('candidates'):
            return {"error": "No prior record candidate list available. Issue a 'record <show>' command first."}
        idx = (parsed.get('record_option') or parsed.get('record_recurring_option')) - 1
        candidates = LAST_RECORD_CANDIDATES['candidates']
        if idx < 0 or idx >= len(candidates):
            return {"error": f"Record option out of range. Choose 1-{len(candidates)}"}
        chosen = candidates[idx]
        if parsed.get('record_option'):
            # Single episode schedule
            rec_id = schedule_episode_recording(chosen)
            if rec_id:
                return {"status": "record_scheduled", "message": f"Scheduled '{chosen.get('title')}' {chosen.get('date')} {chosen.get('time')} (option {idx+1})", "recording_id": rec_id}
            return {"error": "Failed to schedule recording"}
        else:
            # Recurring: build episodes with same channel/time slot in the search horizon
            try:
                # Use cached EPG search instead of fresh fetch
                horizon_eps = search_cached_epg(LAST_RECORD_CANDIDATES.get('show_name',''), days=14) or []
            except Exception:
                horizon_eps = []
            slot_eps = []
            target_channel = chosen.get('call_sign', '')
            target_time = chosen.get('time', '')
            for e in horizon_eps:
                if e.get('call_sign') == target_channel and e.get('time') == target_time:
                    slot_eps.append(e)
            if not slot_eps:
                slot_eps = [chosen]  # Fallback to just the selected episode
            rule = create_recurring_recording_rule(LAST_RECORD_CANDIDATES.get('show_name',''), slot_eps, 'weekly', f"{target_channel}_{target_time}")
            if rule:
                return {"status": "recurring_rule_created", "message": f"Created recurring rule from option {idx+1} ({chosen.get('channel')} @ {chosen.get('time')})", "details": rule}
            return {"error": "Failed to create recurring recording rule"}
    
    # Handle regular show name requests
    event = parsed.get('event')
    show_name = event.strip() if event else ''
    
    if not show_name:
        return {"error": "No show name provided"}
    
    print(f"Recording request for: '{show_name}'")
    
    # Import the new EPG search functions
    from epg_zap2it import search_epg_for_show, analyze_show_pattern, group_episodes_by_series

    # --- Sports Event Disambiguation Heuristics ---
    # If the user said something like "record the cowboys game" we do NOT want to
    # latch onto a 30‑minute highlight/postgame show (e.g. "GameNight"). We want the
    # actual live game broadcast (multi‑hour) typically containing " at " or " vs ".
    # We apply a pre-filter here before generic pattern analysis so we can schedule
    # a one‑off single recording instead of an ongoing time-based rule.

    def try_sports_game_resolution(original_query: str, parsed_context=None):
        ql = original_query.lower()
        # If unified team scoring (search_epg_for_show) will already capture team-based
        # NFL games via team_match flag, only keep this path for explicit disambiguation
        # when user says 'game' and provides a team token prior to generic EPG search.
        if 'game' not in ql and 'vs' not in ql and ' at ' not in ql:
            return None
        # Basic list of recognizable NFL team tokens (lowercase singular forms)
        nfl_teams = [
            'cowboys','giants','eagles','commanders','patriots','jets','dolphins','bills','chiefs',
            'chargers','raiders','broncos','steelers','browns','ravens','bengals','jaguars','texans',
            'titans','colts','packers','bears','lions','vikings','saints','falcons','panthers',
            'buccaneers','49ers','niners','rams','seahawks','cardinals']
        tokens = [t for t in re.split(r'[^a-z0-9]+', ql) if t]
        team_tokens = [t for t in tokens if t in nfl_teams]
        if not team_tokens:
            return None
        # If the query is simple like "record the cowboys game" we continue so user sees a focused list.
        # Otherwise let general scoring handle it.
        # Weekday filter (on sunday, on monday, etc.)
        weekday_map = {
            'monday':0,'tuesday':1,'wednesday':2,'thursday':3,'friday':4,'saturday':5,'sunday':6
        }
        requested_weekdays = {weekday_map[t] for t in tokens if t in weekday_map}
        # Optional explicit time narrowing (from NLP parser) e.g. 'at 7:15 pm'. If parser
        # captured explicit_time but user omitted am/pm and hour < 8, we *heuristically*
        # treat prime sports context (NFL evening games) as PM (add 12) unless already 24h.
        target_time_obj = None
        if parsed_context and parsed_context.get('explicit_time'):
            raw_et = parsed_context['explicit_time']  # format HH:MM (24h) from parser
            try:
                h, m = raw_et.split(':')
                h_i = int(h); m_i = int(m)
                # Heuristic disambiguation: if hour <= 8 and original text lacked am/pm but query has 'game'
                if h_i < 8 and ('pm' not in ql and 'am' not in ql):
                    h_i += 12  # treat as evening
                from datetime import time as _time
                target_time_obj = _time(h_i, m_i)
            except Exception:
                target_time_obj = None
        # Pull fresh/full EPG (cached helper)
        epg_data = get_epg()
        if not epg_data:
            return None
        now = datetime.now()
        candidates = []
        exclusion_keywords = ['postgame','pregame','game night','gamenight','show','special','replay','encore','scoreboard','countdown']
        for ch in epg_data:
            ch_num = ch.get('channel_number') or ch.get('channel')
            ch_name = ch.get('channel_name') or ch.get('call_sign') or ''
            for prog in ch.get('programs', []):
                title = (prog.get('title') or '').strip()
                tl = title.lower()
                desc_l = (prog.get('description') or '').lower()
                ep_title_l = (prog.get('episode_title') or '').lower()
                team_in_title = any(tt in tl for tt in team_tokens)
                # Accept generic 'NFL Football' if team appears in description or episode_title
                if not team_in_title:
                    if not ('nfl football' in tl and any(tt in (desc_l + ' ' + ep_title_l) for tt in team_tokens)):
                        continue
                # Matchup indicator can appear in title OR metadata
                combined_meta = ' '.join([tl, desc_l, ep_title_l])
                if not any(x in combined_meta for x in [' vs ',' at ',' vs. ']):
                    # Allow if still a long NFL Football with team in metadata (network may omit matchup early)
                    if 'nfl football' not in tl:
                        continue
                if any(bad in tl for bad in exclusion_keywords):
                    continue
                # Duration filter: need at least 90 minutes (games are usually >=150)
                try:
                    dur = int(prog.get('duration') or 0)
                except Exception:
                    dur = 0
                if dur < 90:
                    continue
                date_str = prog.get('date') or prog.get('airDate')
                time_str = prog.get('time') or prog.get('airTime')
                if not (date_str and time_str):
                    continue
                try:
                    start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                except Exception:
                    continue
                if start_dt < now:
                    continue
                if requested_weekdays and start_dt.weekday() not in requested_weekdays:
                    continue
                # If user supplied a target time, require start within +/- 120 minutes.
                if target_time_obj:
                    try:
                        delta_minutes = abs((start_dt.hour*60 + start_dt.minute) - (target_time_obj.hour*60 + target_time_obj.minute))
                        if delta_minutes > 120:
                            continue
                    except Exception:
                        pass
                # Score ranking: prefer durations >=150, prime evening start times, exact team token at start
                score = 0
                if dur >= 150: score += 30
                if any(k in tl for k in [' at ', ' vs ', ' vs. ']): score += 20
                if any(tt in tl.split(':')[0].split(' vs ')[0] for tt in team_tokens): score += 5
                # Evening weight (6pm-9:30pm local)
                if 18 <= start_dt.hour <= 21:
                    score += 10
                # Slight boost for network channels (heuristic: channel number ends with .1)
                if ch_num and str(ch_num).endswith('.1'): score += 2
                candidates.append({
                    'program': prog,
                    'channel_number': ch_num,
                    'channel': ch_name,
                    'score': score,
                    'date': date_str,
                    'time': time_str,
                    'start_dt': start_dt,
                    'duration': str(dur),
                    'title': title
                })
        if not candidates:
            return None
        # Sort by score then earliest start; always present as record_candidates
        candidates.sort(key=lambda c: (-c['score'], c['start_dt']))
        presented = []
        for idx, c in enumerate(candidates[:10], start=1):
            presented.append({
                'option': idx,
                'title': c['title'],
                'channel': c['channel'],
                'channel_number': c['channel_number'],
                'date': c['date'],
                'time': c['time'],
                'duration': c['duration'],
                'score': c['score'],
                'genre': 'Sports',
                'team_match': True  # NFL sports heuristic always implies a team intent
            })
        return {
            'status': 'record_candidates',
            'candidate_type': 'sports',
            'message': f"Select the live game broadcast (option 1-{len(presented)}). Use 'record option N' or 'record recurring option N'.",
            'candidates': presented,
            'sports_disambiguation': 'list'
        }



    # Sports disambiguation (now returns candidate list instead of auto scheduling)
    sports_candidates = try_sports_game_resolution(show_name, parsed_context=parsed)
    if sports_candidates and sports_candidates.get('status') == 'record_candidates':
        LAST_RECORD_CANDIDATES = {
            'candidates': sports_candidates['candidates'],
            'show_name': show_name,
            'timestamp': time.time() if 'time' in globals() else None
        }
        return sports_candidates
    
    # Search for the show in cached EPG data
    matching_episodes = search_cached_epg(show_name, days=7)
    
    if not matching_episodes:
        return {"error": f"No episodes found for '{show_name}' in the next 7 days"}
    
    # Analyze the pattern to determine recording strategy
    pattern, relevant_episodes = analyze_show_pattern(matching_episodes)
    # If we have a clear single team-based sports match (NFL) we suppress automatic recurring suggestions.
    # Criteria: top episode has team_match flag, only one high-score (>=100) episode, query contains 'game' or NFL team token.
    nfl_team_tokens = ['cowboys','giants','eagles','commanders','patriots','jets','dolphins','bills','chiefs','chargers','raiders','broncos','steelers','browns','ravens','bengals','jaguars','texans','titans','colts','packers','bears','lions','vikings','saints','falcons','panthers','buccaneers','49ers','rams','seahawks','cardinals']
    q_lower = show_name.lower()
    query_has_team = any(t in q_lower for t in nfl_team_tokens)
    high_score_team_eps = [ep for ep in matching_episodes if ep.get('team_match') and ep.get('match_score',0) >= 100]
    suppress_recurring_for_team = False
    if high_score_team_eps:
        # If only one upcoming high-score game or user explicitly said 'game', treat as one-off
        if len(high_score_team_eps) == 1 and ('game' in q_lower or query_has_team):
            suppress_recurring_for_team = True
    if suppress_recurring_for_team:
        pattern = 'one-time'
    print(f"Show pattern detected: {pattern}")
    
    # Check if user wants series recording or single next episode
    if parsed.get('next_only'):
        # Even for next-only, provide candidate list first for consistency
        pass
    is_series_request = parsed.get('series_recording', False)
    
    # If user explicitly specified a weekday (e.g., "each monday"), force a weekly pattern
    explicit_weekday = parsed.get('explicit_weekday')
    explicit_weekdays = parsed.get('explicit_weekdays')
    explicit_time = parsed.get('explicit_time')

    if explicit_weekday or explicit_weekdays:
        desired_days = set()
        if explicit_weekdays:
            desired_days.update([d.lower() for d in explicit_weekdays])
        if explicit_weekday:
            desired_days.add(explicit_weekday.lower())
        chosen_eps = []
        for ep in matching_episodes:
            try:
                dt = datetime.strptime(ep.get('date',''), '%Y-%m-%d')
                if dt.strftime('%A').lower() in desired_days:
                    chosen_eps.append(ep)
            except Exception:
                continue
        if not chosen_eps and matching_episodes:
            # Use first episode as template if none yet visible for requested day(s)
            chosen_eps = [matching_episodes[0]]
        # If explicit time provided, adjust template episodes' time to that (for rule scheduling)
        if explicit_time:
            for ep in chosen_eps:
                ep['time'] = explicit_time
        pattern = 'weekly'
        return handle_dynamic_series_recording(show_name, chosen_eps, pattern, parsed_context=parsed)

    # Build candidate list (first N upcoming episodes) and return for user selection
    # We include at least up to 10 upcoming distinct airings.
    all_candidates = relevant_episodes if relevant_episodes else matching_episodes
    # Deduplicate by date+time+channel_number
    seen_keys = set()
    candidate_list = []
    for ep in sorted(all_candidates, key=lambda e: (e.get('date',''), e.get('time',''))):
        key = (ep.get('date'), ep.get('time'), ep.get('channel_number'))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        candidate_list.append({**ep})
        if len(candidate_list) >= 10:
            break
    # Attach option numbers
    for i, c in enumerate(candidate_list, start=1):
        c['option'] = i
    LAST_RECORD_CANDIDATES = {
        'candidates': candidate_list,
        'show_name': show_name,
        'pattern': pattern,
        'timestamp': time.time() if 'time' in globals() else None
    }
    return {
        'status': 'record_candidates',
        'message': f"Select an airing of '{show_name}' to record (option 1-{len(candidate_list)}). Use 'record option N' or 'record recurring option N'.",
        'show': show_name,
        'pattern_detected': pattern,
        'candidates': candidate_list,
        'series_recommended': False if suppress_recurring_for_team else bool(is_series_request or (pattern in ['daily-weekdays','weekly','weekly-weekend'] and len(relevant_episodes) > 1)),
        'team_match_one_off': suppress_recurring_for_team
    }

def handle_dynamic_series_recording(show_name, episodes, pattern, parsed_context=None):
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
        recording_rule = create_recurring_recording_rule(show_name, group_episodes, pattern, series_key, parsed_context=parsed_context)
        if recording_rule:
            total_rules_created += 1
            recording_details.append(recording_rule)
    
    # Save all the recording rules to disk
    save_schedule()
    
    return {
        "message": f"Series recording scheduled for '{show_name}'",
        "pattern": pattern,
        "recording_rules": total_rules_created,
        "recording_details": recording_details
    }

def is_duplicate_recurring_rule(show_name, series_key, channel_number, time):
    """Check if a recurring recording rule already exists for this show/series"""
    for existing in scheduled_jobs:
        if existing.get('type') == 'recurring_series':
            # Check for same title, series_key, channel, and time
            if (existing.get('title') == show_name and
                existing.get('series_key') == series_key and
                existing.get('channel_number') == channel_number and
                existing.get('time') == time):
                return True
    return False

def create_recurring_recording_rule(show_name, episodes, pattern, series_key, parsed_context=None):
    """Create a time-based recurring recording rule that will record ongoing"""
    if not episodes:
        return None
    
    # Use the first episode as the template for the recurring rule
    template_episode = episodes[0]
    
    # Check for duplicate recurring rule
    if is_duplicate_recurring_rule(show_name, series_key, 
                                 template_episode.get('channel_number', ''), 
                                 template_episode.get('time', '')):
        print(f"  Skipping duplicate recurring rule: {show_name} on {template_episode.get('channel', '')} at {template_episode.get('time', '')}")
        return None
    
    # Determine the recurrence pattern from the episodes
    recurrence_info = analyze_recurrence_pattern(episodes, pattern)
    
    # Create the recurring recording rule - TIME-BASED, not episode-based
    # Timezone offset (basic) for future DST handling
    try:
        from datetime import timezone as _tz
        local_offset_minutes = int((datetime.now() - datetime.utcnow()).total_seconds() // 60)
    except Exception:
        local_offset_minutes = 0
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
        'next_episode': episodes[0] if episodes else None,
        'tz_offset_min': local_offset_minutes
    }
    # Attach retention and explicit weekday/time metadata if provided
    if parsed_context:
        for k in ['explicit_weekday','explicit_weekdays','explicit_time','retention_weeks','retention_until']:
            if k in parsed_context:
                recording_rule[k] = parsed_context[k]
    
    # Add to scheduled jobs
    scheduled_jobs.append(recording_rule)
    save_schedule()  # Save the recording rule to disk
    
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
        
        # Convert time from "7:00 PM" format to "19:00" format for scheduler
        original_time = episode.get('time', '')
        scheduled_time = original_time
        try:
            if original_time and ('AM' in original_time or 'PM' in original_time):
                # Convert from 12-hour to 24-hour format
                time_obj = datetime.strptime(original_time, "%I:%M %p")
                scheduled_time = time_obj.strftime("%H:%M")
        except Exception as e:
            print(f"Warning: Could not convert time '{original_time}': {e}")
            scheduled_time = original_time
        
        # Create recording entry
        recording_info = {
            'id': len(scheduled_jobs) + 1,
            'title': episode.get('title', 'Unknown Show'),
            'channel': episode.get('channel', 'Unknown Channel'),
            'channel_number': episode.get('channel_number', ''),
            'call_sign': episode.get('call_sign', ''),
            'date': episode.get('date', ''),
            'time': scheduled_time,  # Use converted 24-hour format
            'original_time': original_time,  # Keep original for display
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
            # Encoding defaults so the scheduler can invoke ffmpeg consistently
            'crf': int(episode.get('crf', 23)),
            'preset': episode.get('preset', 'fast'),
            'format': episode.get('format', 'mp4'),
            'scheduled_at': datetime.now().isoformat(),
            'filename': suggested_filename,
            'status': 'scheduled'
        }
        
        # Add to scheduled jobs
        scheduled_jobs.append(recording_info)
        save_schedule()  # Save the scheduled recording to disk
        
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

def schedule_next_episode(show_name):
    """Find the next upcoming airing of a show from EPG and schedule only that single episode."""
    try:
        epg = get_epg()
        if not epg:
            return {"error": "EPG unavailable"}
        # Flatten all channel listings
        upcoming = []
        now = datetime.now()
        for ch in epg:
            for prog in ch.get('programs', []):
                title = prog.get('title','').lower().strip()
                if show_name.lower() in title:
                    # Build datetime from date/time fields if available
                    date_str = prog.get('date') or prog.get('airDate') or ''
                    time_str = prog.get('time') or prog.get('airTime') or ''
                    # Basic parse attempts
                    dt_obj = None
                    if date_str and time_str:
                        try:
                            dt_obj = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                        except Exception:
                            pass
                    # Filter out past airings if we got datetime
                    if dt_obj and dt_obj < now:
                        continue
                    # Store candidate
                    upcoming.append({
                        'raw': prog,
                        'channel_number': ch.get('channel_number') or ch.get('channel') or prog.get('channel_number',''),
                        'channel': ch.get('channel_name') or ch.get('call_sign') or prog.get('channel','Unknown Channel'),
                        'date': prog.get('date', date_str),
                        'time': prog.get('time', time_str),
                        'dt': dt_obj or now,  # fallback now to allow sort
                    })
        if not upcoming:
            return {"error": f"No upcoming episode found for '{show_name}'"}
        upcoming.sort(key=lambda x: x['dt'])
        next_ep = upcoming[0]
        # Build recording_info structure similar to single episode scheduling
        recording_info = {
            'id': len(scheduled_jobs) + 1,
            'title': show_name.title(),
            'channel': next_ep['channel'],
            'channel_number': next_ep['channel_number'],
            'date': next_ep['date'],
            'time': next_ep['time'],
            'episode_title': next_ep['raw'].get('episode_title',''),
            'episode_id': next_ep['raw'].get('episode_id',''),
            'original_air_date': next_ep['raw'].get('original_air_date',''),
            'description': next_ep['raw'].get('description',''),
            'duration': next_ep['raw'].get('duration','30'),
            'scheduled_at': datetime.now().isoformat(),
            'status': 'scheduled',
            'single_next': True
        }
        if is_duplicate_recording(recording_info):
            return {"message": "Next episode already scheduled", "recording": recording_info}
        # Generate filename
        recording_info['filename'] = generate_filename(recording_info)
        scheduled_jobs.append(recording_info)
        save_schedule()
        save_metadata_file(recording_info, recording_info['filename'])
        return {"message": "Scheduled next episode", "recording": recording_info}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def search_torrents_for_series(series_name, season_number):
    """Search for all episodes in a TV series season using configured indexer.

    Strategy:
      1. Perform a broad season-level search: "<Series> Sxx" to gather a large pool.
      2. Parse episode identifiers SxxEyy from torrent titles. Keep the highest seeder count per episode.
      3. If few / no episodes found, iterate each episode number (1..24) and run a targeted query
         "<Series> SxxEyy" to try to fill gaps (stop early if we encounter a long miss streak).
      4. Return a normalized list ready for UI consumption (similar shape to prior mock data):
         name (SxxEyy), title (human), size (human readable), seeders, magnet, selected default True.

    Falls back gracefully if indexer unavailable.
    """
    import re
    from math import log
    from datetime import datetime as _dt

    # Use unified search with configured indexer

    season_tag = f"S{season_number:02d}"
    clean_series = re.sub(r"[^\w\s]", " ", series_name).strip()
    base_query = f"{clean_series} {season_tag}".strip()

    print(f"🔍 Season search base query: '{base_query}'")

    # Helper: human readable size from bytes (can accept int/float/None)
    def human_size(num_bytes):
        try:
            b = float(num_bytes)
            if b <= 0:
                return "0 B"
            units = ["B","KB","MB","GB","TB"]
            idx = int(min(len(units)-1, log(b, 1024)))
            return f"{b / (1024 ** idx):.1f} {units[idx]}"
        except Exception:
            return "?"

    # Regex to extract SxxEyy (case-insensitive). Accept forms like S1E2, S01E02 etc.
    ep_pattern = re.compile(rf"\b{season_tag}E(\d{{1,2}})\b", re.IGNORECASE)

    episodes_map = {}  # episode_number(int) -> chosen torrent dict
    attempted_queries = []

    def consider_pool(torrents, tag):
        for t in torrents:
            title = (t.get("title") or "").strip()
            if not title:
                continue
            m = ep_pattern.search(title.replace(' ', '').upper())  # normalize spacing for patterns
            if not m:
                # Try a looser pattern removing punctuation (e.g., S01 E02)
                loose = re.search(rf"{season_tag}[^A-Za-z0-9]?[Ee](\d{{1,2}})", title.replace(' ', ''), re.IGNORECASE)
                if loose:
                    m = loose
            if not m:
                continue
            try:
                ep_no = int(m.group(1))
            except Exception:
                continue
            if ep_no < 1 or ep_no > 40:  # sanity bounds
                continue
            seeders = int(t.get("seeders") or 0)
            existing = episodes_map.get(ep_no)
            # Keep the torrent with highest seeders
            if existing is None or seeders > existing.get("seeders", 0):
                episodes_map[ep_no] = {
                    "name": f"{clean_series} {season_tag}E{ep_no:02d}",
                    "title": f"{clean_series} - Season {season_number} Episode {ep_no}",
                    "size": human_size(t.get("size_bytes")),
                    "seeders": seeders,
                    "magnet": t.get("magnet"),
                    "quality": derive_quality_hint(title),
                    "selected": True,
                    "raw_title": title,
                    "source_tag": tag,
                }

    def derive_quality_hint(title):
        tl = title.lower()
        if '2160' in tl or '4k' in tl:
            return '2160p'
        if '1080' in tl:
            return '1080p'
        if '720' in tl:
            return '720p'
        if '480' in tl:
            return '480p'
        return 'unknown'

    # 1. Broad season query (and a couple variants to loosen constraints)
    broad_variants = [
        base_query,
        f"{clean_series} {season_tag} 1080",  # prefer high quality
        f"{clean_series} {season_tag} 720",
        f"{clean_series} season {season_number}",
    ]
    seen_variant = set()
    for variant in broad_variants:
        v = variant.strip()
        if not v or v.lower() in seen_variant:
            continue
        seen_variant.add(v.lower())
        try:
            _, pool = unified_torrent_search(v, content_type="tv")
            attempted_queries.append(v)
            print(f"Season search variant '{v}' -> {len(pool)} torrents")
            consider_pool(pool, f"broad:{v}")
            # If we have a good number of episodes already (>=8) stop broad variants early
            if len(episodes_map) >= 8:
                break
        except Exception as e:  # noqa: PERF203
            print(f"Variant search error '{v}': {e}")
            attempted_queries.append(f"error:{v}")

    # 2. Targeted per-episode backfill if we have big gaps (< 10 or missing low numbers)
    if len(episodes_map) < 10:
        miss_streak = 0
        for ep_no in range(1, 25):  # search up to 24 episodes
            if ep_no in episodes_map:
                continue
            ep_query = f"{clean_series} {season_tag}E{ep_no:02d}"
            try:
                _, pool = unified_torrent_search(ep_query, content_type="tv")
                attempted_queries.append(ep_query)
                if not pool:
                    miss_streak += 1
                else:
                    miss_streak = 0
                consider_pool(pool, f"ep:{ep_query}")
            except Exception as e:
                print(f"Episode query error '{ep_query}': {e}")
                attempted_queries.append(f"error:{ep_query}")
                miss_streak += 1
            # If we keep missing results, stop early to reduce noise/time
            if miss_streak >= 5:
                break

    # Build ordered episode list (gap episodes omitted)
    ordered_eps = [episodes_map[k] for k in sorted(episodes_map.keys())]

    if ordered_eps:
        print(f"Season search complete: found {len(ordered_eps)} episode torrents for '{series_name}' Season {season_number}")
        return ordered_eps

    # Fallback: no per-episode matches. Offer season pack torrents from the most successful broad variant.
    print("No individual episode torrents found; attempting season pack fallback.")
    season_pack_terms = [
        f"{clean_series} {season_tag} season {season_number}",
        f"{clean_series} season {season_number}",
        f"{clean_series} complete {season_tag}",
        f"{clean_series} S{season_number:02d}",
    ]
    packs = []
    seen_variant.clear()
    for term in season_pack_terms:
        if term.lower() in seen_variant:
            continue
        seen_variant.add(term.lower())
        try:
            _, pool = unified_torrent_search(term, content_type="tv")
        except Exception as e:
            print(f"Season pack query error '{term}': {e}")
            continue
        for t in pool:
            title = (t.get('title') or '').lower()
            # Heuristics: must mention season number, and either 'complete' or season tag or 'sxx'
            if (f"season {season_number}" in title or season_tag.lower() in title) and ("complete" in title or season_tag.lower() in title):
                packs.append(t)
        if packs:
            break  # stop after first variant that yields packs

    if not packs:
        print("Season pack fallback also produced no results.")
        return []

    # Pick top N season packs by seeders
    def pack_seed(t):
        try:
            return int(t.get('seeds') or t.get('seeders') or 0)
        except Exception:
            return 0
    packs.sort(key=pack_seed, reverse=True)
    selected_packs = packs[:5]

    # Present each season pack as a pseudo-episode entry with special flag
    pack_entries = []
    for idx, p in enumerate(selected_packs, start=1):
        seeds = pack_seed(p)
        pack_entries.append({
            'name': f"SeasonPack{idx}",
            'title': (p.get('title') or f"{series_name} Season {season_number} Pack").strip(),
            'size': human_size(p.get('size') or p.get('size_bytes')),  # upstream may use 'size'
            'seeders': seeds,
            'magnet': p.get('magnet'),
            'quality': derive_quality_hint(p.get('title') or ''),
            'selected': True,
            'season_pack': True,
            'raw_title': p.get('title'),
        })

    print(f"Season pack fallback: offering {len(pack_entries)} pack torrents for '{series_name}' Season {season_number}")
    return pack_entries

def agent_download(parsed):
    """Handle torrent download requests via qBittorrent API"""
    import requests
    import urllib.parse
    import re
    global LAST_TORRENT_SEARCH
    if 'LAST_TORRENT_SEARCH' not in globals():
        LAST_TORRENT_SEARCH = {
            'torrents': [],
            'query': None,
            'timestamp': None,
        }
    # Unified search is available globally

    def classify_content(intent):
        """Return ('tv'|'movie', season, episode) based on parsed intent or naming tokens."""
        season = intent.get('season') or None
        episode = intent.get('episode') or None
        show = intent.get('series') or intent.get('title') or intent.get('event') or ''
        raw = (show or '') + ' ' + ' '.join([str(v) for v in intent.values() if isinstance(v, str)])
        raw_l = raw.lower()
        # Detect SxxEyy or 'season' keyword -> tv
        if re.search(r's\d{1,2}e\d{1,2}', raw_l) or 'season' in raw_l or season or episode:
            return 'tv', season, episode
        # Single word + year pattern maybe a movie (heuristic could be extended)
        return 'movie', None, None
    
    content_type, season_token, episode_token = classify_content(parsed)
    # These fields are ONLY for torrent workflows; recordings ignore them
    parsed['content_type'] = content_type
    parsed['target_root'] = TV_SHOWS_DIR if content_type == 'tv' else MOVIES_DIR
    
    download_type = parsed.get('download_type', 'search')
    
    if download_type == 'series_season':
        # Handle series season search
        series = parsed.get('series', '')
        season = parsed.get('season', 1)
        
        if not series:
            return {"error": "No series name provided"}
        
        # Search for episodes
        episodes = search_torrents_for_series(series, season)
        
        if not episodes:
            return {"error": f"No torrents found for {series} Season {season}"}
        
        return {
            "status": "search_results",
            "search_type": "series_season", 
            "series": series,
            "season": season,
            "episodes": episodes,
            "content_type": parsed.get('content_type'),
            "target_root": parsed.get('target_root'),
            "message": f"Found {len(episodes)} episodes for {series} Season {season}"
        }
    
    elif download_type in ['direct_magnet', 'direct_torrent']:
        # Handle direct magnet/torrent links (existing functionality)
        query = parsed.get('query', '').strip()
        if not query:
            return {"error": "No download query provided"}
        
        # Use VPN-protected download function
        return safe_download_with_vpn(add_torrent_to_qbittorrent, query, parsed)
    
    else:
        # Regular search query
        query = parsed.get('query', '').strip()

        # --- Selection follow-up: "download option N" or "option N" ---
        sel_match = re.match(r'^(?:download\s+)?option\s+(\d+)$', query.lower())
        multi_match = re.match(r'^download\s+options\s+([0-9,\s]+)$', query.lower())
        if sel_match and LAST_TORRENT_SEARCH.get('torrents'):
            idx = int(sel_match.group(1)) - 1
            torrents = LAST_TORRENT_SEARCH.get('torrents')
            if 0 <= idx < len(torrents):
                chosen = torrents[idx]
                magnet = chosen.get('magnet')
                if not magnet:
                    return {"error": "Selected entry has no magnet link"}
                
                # Use VPN-protected download
                result = add_magnet_with_vpn(magnet, chosen)
                if result.get('status') == 'success':
                    return {
                        "status": "download_started",
                        "message": f"Started torrent from option {idx+1} - {chosen.get('title')[:120]}",
                        "selected_index": idx + 1,
                        "torrent": {k: chosen.get(k) for k in ('title','seeds','leeches','size_bytes','uploader','category','subcat')},
                        "query": LAST_TORRENT_SEARCH.get('query'),
                    }
                else:
                    return result
                    return {"error": f"Selection add error: {e}"}
            else:
                return {"error": f"Option out of range. Provide 1-{len(torrents)}"}
        elif multi_match and LAST_TORRENT_SEARCH.get('torrents'):
            indices_raw = multi_match.group(1)
            parts = [p.strip() for p in indices_raw.split(',') if p.strip()]
            torrents = LAST_TORRENT_SEARCH.get('torrents')
            added = []
            errors = []
            # Check VPN status first before bulk download
            if not check_vpn_status():
                print("🔐 Starting VPN for secure bulk download (this may take up to 60 seconds)...")
                connect_result = connect_vpn()
                if connect_result == True:
                    print("🔐 VPN connected successfully - bulk download will proceed securely")
                elif connect_result == "GUI_STARTED":
                    return {
                        "error": "VPN Protection Required", 
                        "message": "ProtonVPN started but auto-connect may have failed. Please check the system tray, ensure VPN is connected manually, then retry bulk download."
                    }
                else:
                    return {"error": "Failed to start VPN. Bulk download aborted for security."}
            else:
                print("🔐 VPN is already running for bulk download - downloads will proceed securely")
                
            # Process each torrent with VPN protection
            try:
                for p in parts:
                    if not p.isdigit():
                        errors.append(f"'{p}' not a number")
                        continue
                    idx = int(p) - 1
                    if idx < 0 or idx >= len(torrents):
                        errors.append(f"Index {p} out of range")
                        continue
                    chosen = torrents[idx]
                    magnet = chosen.get('magnet')
                    if not magnet:
                        errors.append(f"Option {p} missing magnet")
                        continue
                    
                    result = add_magnet_with_vpn(magnet, chosen)
                    if result.get('status') == 'success':
                        added.append({
                            'option': idx + 1,
                            'title': chosen.get('title'),
                            'seeds': chosen.get('seeders') or chosen.get('seeds'),
                        })
                    else:
                        errors.append(f"Option {p}: {result.get('error', 'Unknown error')}")
                        
                return {
                    'status': 'bulk_download_result',
                    'added': added,
                    'errors': errors,
                    'count_added': len(added),
                    'count_errors': len(errors),
                    'message': f"Started {len(added)} torrents with VPN protection; {len(errors)} issues." if added else "No torrents started."
                }
            except Exception as e:
                return {"error": f"Multi-selection error: {e}"}

        if not query:
            return {
                "status": "search_needed",
                "message": "Provide a search phrase or magnet link.",
                "example": "download the office season 2"
            }
        # Attempt torrent search using configured indexer
        if 'torrent_provider' not in parsed:  # simple guard to avoid recursion
            try:
                        # --- Progressive fallback query strategy ---
                        def build_variants(q: str):
                            import re
                            base = q.strip()
                            variants = []
                            def add(v):
                                v2 = re.sub(r'\s+', ' ', v.strip())
                                if v2 and v2.lower() not in [x.lower() for x in variants]:
                                    variants.append(v2)
                            add(base)
                            # Remove common quality / codec tokens
                            quality_pattern = re.compile(r'\b(1080p|2160p|720p|480p|4k|x265|x264|h264|hdr|webrip|web-dl|webdl|bluray|blu-ray|brrip|dvdrip|proper|repack)\b', re.I)
                            no_quality = quality_pattern.sub(' ', base)
                            add(no_quality)
                            # Remove year tokens
                            year_pattern = re.compile(r'\b(19|20)\d{2}\b')
                            no_year = year_pattern.sub(' ', no_quality)
                            add(no_year)
                            # Remove leading articles / stop words
                            stop_words = set(['the','a','an','in','of','and','to'])
                            tokens = [t for t in re.split(r'\s+', no_year) if t]
                            no_stops = ' '.join([t for t in tokens if t.lower() not in stop_words])
                            if no_stops:
                                add(no_stops)
                            # First three significant words
                            if len(tokens) > 3:
                                add(' '.join(tokens[:3]))
                            return variants

                        attempted = []
                        first_success = None
                        torrents = []
                        provider_used = "none"
                        for attempt in build_variants(query):
                            attempted.append(attempt)
                            provider_used, results = unified_torrent_search(attempt, content_type=content_type)
                            if results:
                                first_success = attempt
                                torrents = results
                                break
                        if torrents:
                            # Persist last search set (keep trimmed list to avoid bloat)
                            LAST_TORRENT_SEARCH = {
                                'torrents': torrents[:30],
                                'query': query,
                                'timestamp': time.time() if 'time' in globals() else None
                            }
                            # Annotate each with an index for UI convenience
                            enriched = []
                            for i, t in enumerate(LAST_TORRENT_SEARCH['torrents'], start=1):
                                t_copy = dict(t)
                                t_copy['option'] = i
                                enriched.append(t_copy)
                            return {
                                "status": "search_results",
                                "provider": provider_used,
                                "query": query,
                                "used_query": first_success,
                                "attempted_queries": attempted,
                                "count": len(torrents),
                                "torrents": enriched,
                                "content_type": parsed.get('content_type'),
                                "target_root": parsed.get('target_root'),
                                "message": f"Found {len(torrents)} torrent candidates via {provider_used} (after {len(attempted)} attempt(s)) for '{query}'. Reply with 'download option N' to fetch."
                            }
                        else:
                            return {
                                "status": "search_results_empty",
                                "provider": provider_used,
                                "query": query,
                                "attempted_queries": attempted,
                                "message": f"No torrents found for '{query}' after {len(attempted)} variant attempt(s)"
                            }
            except Exception as e:
                return {
                    "status": "search_provider_error",
                    "provider": "unified_search",
                    "query": query,
                    "error": str(e),
                    "fallback": "Provide a direct magnet link or try again later"
                }
        # Fallback guidance
        return {
            "status": "search_needed",
            "message": f"Indexer disabled or no search results. To download '{query}', provide a magnet link/torrent URL or use 'download season X of [series name]'.",
            "example": "download magnet:?xt=... OR download season 3 of abbott elementary"
        }

def detect_content_type(torrent_name):
    """Analyze torrent name to determine if it's a TV show or movie"""
    name_lower = torrent_name.lower()
    
    # TV Show indicators (strong signals)
    tv_indicators = [
        # Season/Episode patterns
        r's\d+e\d+',           # S01E01, S1E1
        r'season\s*\d+',       # Season 1, Season01
        r'\d+x\d+',            # 1x01, 01x01
        r'episode\s*\d+',      # Episode 1, Episode01
        r'ep\s*\d+',           # Ep1, Ep01
        r'e\d{2,}',            # E01, E001
        
        # Season pack patterns
        r'complete\s*season',   # Complete Season
        r'full\s*season',      # Full Season
        r'season\s*pack',      # Season Pack
        r'tv\s*series',        # TV Series
        
        # Episode naming patterns
        r'\b\d{4}\.\d{2}\.\d{2}\b',  # 2024.01.15 (date format)
        r'\b(hdtv|web-dl|webrip).*\d+p\b',  # TV release patterns
    ]
    
    # Movie indicators
    movie_indicators = [
        # Year patterns (movies often have year)
        r'\b(19|20)\d{2}\b',   # 1980-2099
        r'bluray',             # BluRay releases
        r'bdrip',              # BD-Rip
        r'dvdrip',             # DVD-Rip
        r'cam\b',              # CAM releases
        r'ts\b',               # Telesync
        r'r5\b',               # R5 releases
        
        # Movie-specific terms
        r'director.*cut',      # Director's Cut
        r'extended.*cut',      # Extended Cut
        r'unrated',            # Unrated
        r'remastered',         # Remastered
        r'criterion',          # Criterion Collection
    ]
    
    # Check for TV patterns
    tv_score = 0
    for pattern in tv_indicators:
        if re.search(pattern, name_lower):
            tv_score += 1
    
    # Check for movie patterns  
    movie_score = 0
    for pattern in movie_indicators:
        if re.search(pattern, name_lower):
            movie_score += 1
    
    # Decision logic
    if tv_score > 0 and movie_score == 0:
        return "TV"
    elif movie_score > 0 and tv_score == 0:
        return "Movies"
    elif tv_score > movie_score:
        return "TV"
    elif movie_score > tv_score:
        return "Movies"
    else:
        # Fallback: check common TV show naming patterns
        if re.search(r'\b(s\d+|season|episode|ep\d+)\b', name_lower):
            return "TV"
        # Check for year (common in movie titles)
        elif re.search(r'\b(19|20)\d{2}\b', name_lower):
            return "Movies"
        else:
            return "Uncategorized"

def categorize_torrent_with_qb(torrent_hash, category):
    """Set category for a specific torrent using qBittorrent API"""
    QB_HOST = "http://localhost:8080"
    QB_USERNAME = "admin" 
    QB_PASSWORD = ""
    
    try:
        session = requests.Session()
        login_data = {"username": QB_USERNAME, "password": QB_PASSWORD}
        login_response = session.post(f"{QB_HOST}/api/v2/auth/login", data=login_data, timeout=10)
        
        if login_response.status_code != 200:
            return False
        
        # Set category
        category_data = {"hashes": torrent_hash, "category": category}
        cat_response = session.post(f"{QB_HOST}/api/v2/torrents/setCategory", data=category_data, timeout=10)
        
        return cat_response.status_code == 200
        
    except Exception as e:
        print(f"Error setting category for torrent {torrent_hash}: {e}")
        return False

def auto_categorize_torrents():
    """Automatically categorize all uncategorized torrents in qBittorrent"""
    QB_HOST = "http://localhost:8080"
    QB_USERNAME = "admin"
    QB_PASSWORD = ""
    
    try:
        session = requests.Session()
        login_data = {"username": QB_USERNAME, "password": QB_PASSWORD}
        login_response = session.post(f"{QB_HOST}/api/v2/auth/login", data=login_data, timeout=10)
        
        if login_response.status_code != 200:
            print("Failed to login to qBittorrent for auto-categorization")
            return 0
        
        # Get all torrents
        torrents_response = session.get(f"{QB_HOST}/api/v2/torrents/info", timeout=10)
        if torrents_response.status_code != 200:
            return 0
        
        torrents = torrents_response.json()
        categorized_count = 0
        
        for torrent in torrents:
            torrent_hash = torrent.get('hash')
            torrent_name = torrent.get('name', '')
            current_category = torrent.get('category', '')
            
            # Only categorize if not already categorized
            if not current_category or current_category == "":
                detected_category = detect_content_type(torrent_name)
                
                if detected_category != "Uncategorized":
                    # Set the category
                    category_data = {"hashes": torrent_hash, "category": detected_category}
                    cat_response = session.post(f"{QB_HOST}/api/v2/torrents/setCategory", data=category_data, timeout=10)
                    
                    if cat_response.status_code == 200:
                        categorized_count += 1
                        print(f"Auto-categorized: '{torrent_name}' → {detected_category}")
        
        if categorized_count > 0:
            print(f"Auto-categorized {categorized_count} torrents")
        
        return categorized_count
        
    except Exception as e:
        print(f"Error in auto-categorization: {e}")
        return 0

def connect_vpn():
    """Connect to configured VPN provider"""
    try:
        from config_manager import ConfigManager
        from vpn_manager import VPNManager
        
        config_manager = ConfigManager()
        vpn_config = config_manager.get_vpn_config()
        if not vpn_config['enabled']:
            print("❌ VPN is disabled in configuration")
            return False
            
        vpn = VPNManager(vpn_config)
        print(f"🔐 Connecting to {vpn_config['provider']} VPN...")
        
        # Check current status first
        status = vpn.get_status()
        if status == "connected":
            print(f"✅ {vpn_config['provider']} VPN already connected")
            return True
        
        # Attempt connection
        result = vpn.connect()
        if result:
            print(f"✅ Successfully connected to {vpn_config['provider']} VPN")
            return True
        else:
            print(f"❌ Failed to connect to {vpn_config['provider']} VPN")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to VPN: {e}")
        return False

def disconnect_vpn():
    """Disconnect from configured VPN provider"""
    try:
        from config_manager import ConfigManager
        from vpn_manager import VPNManager
        
        config_manager = ConfigManager()
        vpn_config = config_manager.get_vpn_config()
        if not vpn_config['enabled']:
            print("❌ VPN is disabled in configuration")
            return False
            
        vpn = VPNManager(vpn_config)
        print(f"🔓 Disconnecting from {vpn_config['provider']} VPN...")
        
        status = vpn.get_status()
        if status == "disconnected":
            print(f"✅ {vpn_config['provider']} VPN already disconnected")
            return True
        
        result = vpn.disconnect()
        if result:
            print(f"✅ Successfully disconnected from {vpn_config['provider']} VPN")
            return True
        else:
            print(f"❌ Failed to disconnect from {vpn_config['provider']} VPN")
            return False
            
    except Exception as e:
        print(f"❌ Error disconnecting VPN: {e}")
        return False

def check_vpn_status():
    """Check if VPN is currently connected using configured provider"""
    try:
        from config_manager import ConfigManager
        from vpn_manager import VPNManager
        
        config_manager = ConfigManager()
        vpn_config = config_manager.get_vpn_config()
        if not vpn_config['enabled']:
            return False
            
        vpn = VPNManager(vpn_config)
        status = vpn.get_status()
        return status == "connected"

            
    except Exception as e:
        print(f"Error checking VPN status: {e}")
        return False

def safe_download_with_vpn(download_function, *args, **kwargs):
    """Wrapper function that ensures VPN is connected during downloads"""
    try:
        # Check if VPN is running (= connected)
        if not check_vpn_status():
            # VPN not running, try to start it
            print("🔐 Starting VPN for secure download (this may take up to 60 seconds)...")
            connect_result = connect_vpn()
            if connect_result == True:
                print("🔐 VPN connected successfully - download will proceed securely")
            elif connect_result == "GUI_STARTED":
                return {
                    "error": "VPN Protection Required", 
                    "message": "ProtonVPN started but auto-connect may have failed. Please check the system tray, ensure VPN is connected manually, then retry your download."
                }
            else:
                return {"error": "Failed to start VPN. Download aborted for security."}
        else:
            print("🔐 VPN is already running (connected) - download will proceed securely")
        
        # Perform the download with VPN protection
        result = download_function(*args, **kwargs)
        return result
        
    except Exception as e:
        return {"error": f"Download failed: {str(e)}"}

def add_magnet_with_vpn(magnet_url, torrent_info=None):
    """Add magnet link to qBittorrent with VPN protection"""
    def _add_magnet():
        QB_HOST = "http://localhost:8080"
        QB_USERNAME = "admin"
        QB_PASSWORD = ""
        
        session = requests.Session()
        login_data = {"username": QB_USERNAME, "password": QB_PASSWORD}
        login_response = session.post(f"{QB_HOST}/api/v2/auth/login", data=login_data, timeout=10)
        if login_response.status_code != 200:
            return {"error": "Failed to login to qBittorrent"}
        
        add_data = {"urls": magnet_url}
        add_response = session.post(f"{QB_HOST}/api/v2/torrents/add", data=add_data, timeout=30)
        if add_response.status_code == 200:
            return {"status": "success", "torrent_info": torrent_info}
        else:
            return {"error": f"qBittorrent add failed (HTTP {add_response.status_code})"}
    
    return safe_download_with_vpn(_add_magnet)

def add_torrent_to_qbittorrent(query, parsed):
    """Add torrent to qBittorrent without VPN management (used by VPN wrapper)"""
    # qBittorrent configuration  
    QB_HOST = "http://localhost:8080"
    QB_USERNAME = "admin"
    QB_PASSWORD = ""
    
    try:
        session = requests.Session()
        login_data = {"username": QB_USERNAME, "password": QB_PASSWORD}
        login_response = session.post(f"{QB_HOST}/api/v2/auth/login", data=login_data, timeout=10)
        
        if login_response.status_code != 200:
            return {"error": "Failed to login to qBittorrent. Check if WebUI is enabled and credentials are correct."}
        
        add_data = {"urls": query}
        add_response = session.post(f"{QB_HOST}/api/v2/torrents/add", data=add_data, timeout=30)
        
        if add_response.status_code == 200:
            # Auto-categorize the newly added torrent after a brief delay
            import threading
            import time
            def delayed_categorize():
                time.sleep(3)  # Wait for torrent to be processed by qBittorrent
                auto_categorize_torrents()
            
            threading.Thread(target=delayed_categorize, daemon=True).start()
            
            return {
                "status": "download_started", 
                "message": f"Added torrent to qBittorrent via VPN (auto-categorization in progress)",
                "details": parsed
            }
        else:
            return {"error": f"Failed to add torrent to qBittorrent. Status: {add_response.status_code}"}
            
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to qBittorrent. Make sure qBittorrent is running and WebUI is enabled on port 8080."}
    except Exception as e:
        return {"error": f"Error adding torrent: {str(e)}"}

def agent_organize(parsed):
    """Organize torrents by automatically categorizing them"""
    query = parsed.get('query', '').lower()
    
    if 'categorize' in query or 'organize' in query:
        try:
            categorized_count = auto_categorize_torrents()
            if categorized_count > 0:
                return {
                    "status": "torrents_organized",
                    "message": f"Successfully categorized {categorized_count} torrents into Movies and TV categories"
                }
            else:
                return {
                    "status": "torrents_organized", 
                    "message": "All torrents are already categorized or no torrents found"
                }
        except Exception as e:
            return {"error": f"Error organizing torrents: {e}"}
    else:
        # General organize/rename/move media files for Plex/Jellyfin (future feature)
        return {"status": "media organized", "details": parsed}

def agent_vpn(parsed):
    """Handle VPN control commands"""
    vpn_action = parsed.get('vpn_action')
    
    if vpn_action == 'connect':
        result = connect_vpn()
        if result == True:
            return {"status": "vpn_connected", "message": "VPN connected successfully via auto-connect."}
        elif result in ["LIKELY_CONNECTED", "RUNNING_BUT_UNCLEAR"]:
            return {"status": "vpn_likely_connected", "message": f"ProtonVPN started. Status: {result}"}
        elif result == "GUI_STARTED":
            return {"status": "vpn_gui_started", "message": "ProtonVPN started. Please ensure connection is active."}
        else:
            return {"status": "vpn_error", "message": f"Failed to start VPN: {result}"}
            
    elif vpn_action == 'disconnect':
        result = disconnect_vpn()
        if result == True:
            return {"status": "vpn_disconnected", "message": "VPN disconnected successfully."}
        elif result == "MANUAL_DISCONNECT_NEEDED":
            return {"status": "vpn_disconnect_manual", "message": "Please disconnect manually via ProtonVPN GUI."}
        else:
            return {"status": "vpn_error", "message": f"VPN disconnect issue: {result}"}
            
    elif vpn_action == 'status':
        status = check_vpn_status()
        if status == True:
            return {"status": "vpn_connected", "message": "VPN is connected and verified"}
        elif status in ["LIKELY_CONNECTED", "RUNNING_BUT_UNCLEAR"]:
            return {"status": "vpn_unclear", "message": f"ProtonVPN status: {status}"}
        elif status == False:
            return {"status": "vpn_disconnected", "message": "ProtonVPN is not running"}
        else:
            return {"status": "vpn_error", "message": f"VPN status check failed: {status}"}
    
    else:
        return {"status": "vpn_error", "message": "Invalid VPN command. Use 'connect vpn', 'disconnect vpn', or 'vpn status'."}

def agent_unknown(parsed):
    return {"status": "unknown command", "details": parsed}


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

@app.route('/debug/channel_schedule')
def debug_channel_schedule():
    """Debug endpoint: inspect upcoming schedule for a specific virtual channel and optional weekday/time.

    Query params:
      channel=36.1 (required)
      weekday=sunday (optional, case-insensitive)
      time=19:15 (optional 24h, narrows +/-180 minutes window)
      horizon_days=10 (optional, default 10)
    Returns matching program entries plus raw nearby listings to aid sports/NFL disambiguation.
    """
    import math
    ch_param = request.args.get('channel')
    if not ch_param:
        return jsonify({'error': 'channel param required'}), 400
    weekday_param = request.args.get('weekday')
    time_param = request.args.get('time')  # expected HH:MM 24h
    horizon_days = int(request.args.get('horizon_days', '10'))
    epg = get_epg()
    if not epg:
        return jsonify({'error': 'EPG unavailable'}), 503
    weekday_map = {'monday':0,'tuesday':1,'wednesday':2,'thursday':3,'friday':4,'saturday':5,'sunday':6}
    target_wd = None
    if weekday_param and weekday_param.lower() in weekday_map:
        target_wd = weekday_map[weekday_param.lower()]
    target_minutes = None
    if time_param:
        try:
            hh, mm = time_param.split(':')
            target_minutes = int(hh)*60 + int(mm)
        except Exception:
            target_minutes = None
    now = datetime.now()
    window_days = now + timedelta(days=horizon_days)
    entries = []
    raw = []
    for ch in epg:
        ch_num = ch.get('channel_number') or ch.get('channel')
        if str(ch_num) != str(ch_param):
            continue
        for prog in ch.get('programs', []):
            date_str = prog.get('date') or prog.get('airDate')
            time_str = prog.get('time') or prog.get('airTime')
            if not (date_str and time_str):
                continue
            try:
                start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except Exception:
                continue
            if start_dt < now or start_dt > window_days:
                continue
            # Always collect raw channel entries for context
            base_entry = {
                'title': prog.get('title',''),
                'episode_title': prog.get('episode_title',''),
                'description': prog.get('description',''),
                'date': date_str,
                'time': time_str,
                'duration': prog.get('duration',''),
                'weekday': start_dt.strftime('%A'),
                'call_sign': ch.get('call_sign') or ch.get('channel_name') or ''
            }
            raw.append(base_entry)
            if target_wd is not None and start_dt.weekday() != target_wd:
                continue
            if target_minutes is not None:
                start_minutes = start_dt.hour*60 + start_dt.minute
                if abs(start_minutes - target_minutes) > 180:  # 3-hour span
                    continue
            entries.append(base_entry)
    # Heuristic marking for likely NFL game among filtered entries
    for e in entries:
        tl = e['title'].lower()
        meta = f"{e.get('description','').lower()} {e.get('episode_title','').lower()}"
        nfl_tokens = ['nfl','cowboys','giants','eagles','commanders','packers','bears','lions','vikings','patriots','jets','dolphins','bills','chiefs','chargers','raiders','broncos','steelers','browns','ravens','bengals','jaguars','texans','titans','colts','saints','falcons','panthers','buccaneers','49ers','rams','seahawks','cardinals']
        matchup = any(x in tl for x in [' vs ',' at ',' vs. ']) or any(t in tl for t in nfl_tokens) or any(t in meta for t in nfl_tokens)
        long_enough = False
        try:
            if int(e.get('duration') or 0) >= 120:
                long_enough = True
        except Exception:
            pass
        e['nfl_game_candidate'] = bool(matchup and long_enough)
    return jsonify({
        'channel': ch_param,
        'filtered': entries,
        'filtered_count': len(entries),
        'raw_count': len(raw),
        'note': 'entries are those matching weekday/time filters; raw_count is all future programs for channel within horizon',
        'params': {'weekday': weekday_param, 'time': time_param, 'horizon_days': horizon_days}
    })

@app.route('/debug/recurring_status')
def debug_recurring_status():
    """Inspect recurring series rules and their last trigger time."""
    rules = [
        {
            'id': j.get('id'),
            'title': j.get('title'),
            'channel_number': j.get('channel_number'),
            'time': j.get('time'),
            'days': (j.get('recurrence') or {}).get('days'),
            'last_started_at': j.get('last_started_at'),
            'status': j.get('status'),
        }
        for j in scheduled_jobs if j.get('type') == 'recurring_series'
    ]
    return jsonify({'count': len(rules), 'rules': rules})

@app.route('/debug/recent_recordings')
def debug_recent_recordings():
    """List most recent individual episode recordings from the schedule file."""
    entries = [
        j for j in scheduled_jobs
        if j.get('type') != 'recurring_series' and j.get('status') in (None, 'scheduled', 'completed', 'running')
    ]
    # Sort by scheduled_at desc
    try:
        entries.sort(key=lambda x: x.get('scheduled_at',''), reverse=True)
    except Exception:
        pass
    return jsonify({'count': len(entries), 'items': entries[:20]})

# Public aliases for convenience
@app.route('/recent_recordings')
def recent_recordings():
    """Alias for /debug/recent_recordings"""
    return debug_recent_recordings()

@app.route('/recurring_status')
def recurring_status():
    """Alias for /debug/recurring_status"""
    return debug_recurring_status()

@app.route('/open_recordings_folder', methods=['POST','GET'])
def open_recordings_folder():
    """Open the recordings folder (SAVE_DIR) in the system file explorer.

    Windows: uses os.startfile or explorer.exe fallback.
    Returns JSON status.
    """
    try:
        path = SAVE_DIR
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        # Prefer native on Windows
        if hasattr(os, 'startfile'):
            os.startfile(path)
        else:
            # Fallback generic attempt (Windows explorer)
            import subprocess
            subprocess.Popen(['explorer', path])
        return jsonify({'status':'ok','opened': path})
    except Exception as e:
        return jsonify({'status':'error','error': str(e)}), 500

@app.route('/debug/refresh_epg', methods=['POST','GET'])
def refresh_epg_manual():
    """Manual EPG refresh endpoint. Clears cache and fetches fresh data immediately.

    Query param: days (default 7) to expand horizon for this one-shot fetch.
    """
    try:
        days = int(request.args.get('days','7'))
    except Exception:
        days = 7
    from epg_zap2it import fetch_gracenote_epg
    try:
        print(f"EPG: manual refresh requested (days={days})")
        fresh = fetch_gracenote_epg(days=days)
        EPG_CACHE['data'] = fresh
        EPG_CACHE['timestamp'] = time.time()
        return jsonify({'status':'ok','program_count': len(fresh)})
    except Exception as e:
        return jsonify({'status':'error','error': str(e)}), 500

def _extract_opponent(team_token:str, title:str):
    import re
    # Normalize spacing and lowercase copy for pattern work
    t_clean = ' '.join(title.split())
    low = t_clean.lower()
    team_low = team_token.lower()
    # Core separators
    seps = [' at ', ' vs ', ' vs. ', ' @ ']
    for sep in seps:
        if sep in low:
            left, right = low.split(sep, 1)
            # Identify which side contains our team
            if team_low in left and team_low not in right:
                opp_raw = right
            elif team_low in right and team_low not in left:
                opp_raw = left
            else:
                # If appears both sides or neither unique, skip
                continue
            # Strip trailing qualifiers
            opp_raw = re.split(r'\b(live|hd|4k)\b', opp_raw)[0]
            opp_raw = re.sub(r'[^a-z0-9 \-]', ' ', opp_raw)
            opp_raw = re.sub(r'\b(nfl|football|game|week \d+)\b', ' ', opp_raw, flags=re.I)
            opp = ' '.join([w.capitalize() for w in opp_raw.split() if w])
            # Avoid returning the same team
            if opp and opp.lower() != team_low:
                return opp
    return None

@app.route('/debug/nfl_matchup')
def debug_nfl_matchup():
    """Return the detected upcoming NFL matchup for a given team name (e.g. team=cowboys).

    It scans EPG titles and descriptions for patterns like 'X at Y' / 'X vs Y'.
    Query params:
      team=cowboys (required)
      days=7 (optional horizon)
    """
    team = (request.args.get('team') or '').strip()
    if not team:
        return jsonify({'error': 'team param required'}), 400
    try:
        days = int(request.args.get('days','7'))
    except Exception:
        days = 7
    epg = get_epg()
    if not epg:
        return jsonify({'error': 'EPG unavailable'}), 503
    import datetime as _dt
    now = _dt.datetime.now()
    horizon = now + _dt.timedelta(days=days)
    candidates = []
    for ch in epg:
        ch_num = ch.get('channel_number') or ch.get('channel')
        ch_name = ch.get('channel_name') or ch.get('call_sign') or ''
        for prog in ch.get('programs', []):
            title = prog.get('title') or ''
            desc = prog.get('description') or ''
            if not title:
                continue
            if team.lower() not in title.lower() and team.lower() not in desc.lower():
                continue
            date_str = prog.get('date') or prog.get('airDate')
            time_str = prog.get('time') or prog.get('airTime')
            if not (date_str and time_str):
                continue
            try:
                start_dt = _dt.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except Exception:
                continue
            if start_dt < now or start_dt > horizon:
                continue
            opponent = _extract_opponent(team, title)
            if not opponent and desc:
                opponent = _extract_opponent(team, desc)
            dur = prog.get('duration') or ''
            try:
                dur_i = int(dur)
            except Exception:
                dur_i = 0
            is_game_length = dur_i >= 120
            candidates.append({
                'title': title.strip(),
                'channel_number': ch_num,
                'channel': ch_name,
                'date': date_str,
                'time': time_str,
                'duration': dur,
                'opponent': opponent,
                'is_game_length': is_game_length,
            })
    # Prioritize entries that look like real games (matchup extracted + long duration)
    def score(c):
        s = 0
        if c.get('opponent'): s += 50
        if c.get('is_game_length'): s += 30
        # Evening preference
        try:
            hr = int(c.get('time','00:00').split(':')[0])
            if 17 <= hr <= 21: s += 10
        except Exception:
            pass
        return -s
    candidates.sort(key=score)
    best = candidates[0] if candidates else None
    return jsonify({
        'team': team,
        'days_horizon': days,
        'matchup_found': bool(best and best.get('opponent')),
        'opponent': best.get('opponent') if best else None,
        'best_entry': best,
        'all_candidates': candidates[:10]
    })

# (Background schedule loop disabled by default; will only start in __main__ if explicitly enabled.)

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

@app.route("/progress", methods=["GET"])
def progress():
    global current_process
    if current_process and current_process.poll() is None:
        return jsonify({"html": f"<div class='alert alert-info'>Recording in progress... PID: {current_process.pid}</div>"})
    else:
        return jsonify({"html": "<div class='alert alert-secondary'>No active recording</div>"})

@app.route("/auto_categorize", methods=["POST"])
def manual_auto_categorize():
    """Manually trigger auto-categorization of torrents"""
    try:
        categorized_count = auto_categorize_torrents()
        return jsonify({
            "success": True,
            "message": f"Auto-categorized {categorized_count} torrents",
            "count": categorized_count
        })
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Error: {str(e)}"
        }), 500

@app.route("/schedule", methods=["POST"])
def schedule_recording():
    data = request.get_json()
    print(f"Schedule request data: {data}")  # Debug logging
    
    # Validate required fields
    if not data:
        return jsonify({"message": "No data received"}), 400
    
    required_fields = ['channel', 'duration', 'time', 'days']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    
    if not data['days'] or len(data['days']) == 0:
        return jsonify({"message": "No days selected"}), 400
        
    try:
        # Create simple scheduled recording entries (not using schedule library)
        for day in data['days']:
            entry = {
                'id': len(scheduled_jobs) + 1,
                'type': 'recurring_series',
                'title': f"{channels.get(data['channel'], data['channel'])} Recording",
                'channel': channels.get(data['channel'], data['channel']),
                'channel_number': data['channel'],
                'recurrence': {
                    'pattern': 'weekly',
                    'days': [day],
                    'time': data['time'],
                    'description': f"Every {day} at {data['time']}"
                },
                'time': data['time'],
                'duration': data['duration'],
                'preset': data.get('preset', 'fast'),
                'format': data.get('format', 'mp4'),
                'crf': data.get('crf', 23),
                'status': 'active',
                'created_at': datetime.now().isoformat()
            }
            scheduled_jobs.append(entry)
            print(f"Added scheduled recording: {entry['title']} on {day} at {data['time']}")
            
        save_schedule()
        return jsonify({"message": f"Recording scheduled for {len(data['days'])} day(s) successfully."})
        
    except Exception as e:
        print(f"Error scheduling recording: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"Error scheduling: {e}"}), 400

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
    try:
        if isinstance(rule_id, str) and rule_id.isdigit():
            rule_id = int(rule_id)
    except Exception:
        pass

    if rule_id is None:
        return jsonify({"message": "Rule ID required."}), 400
    # Locate the rule
    rule_to_remove = None
    for job in scheduled_jobs:
        if job.get('type') == 'recurring_series' and job.get('id') == rule_id:
            rule_to_remove = job
            break

    if not rule_to_remove:
        return jsonify({"message": "Recurring series rule not found"})

    title = rule_to_remove.get('title', 'Unknown')
    series_key = rule_to_remove.get('series_key')
    # Count episodes/sample episodes for message
    ep_list = rule_to_remove.get('episodes') or rule_to_remove.get('sample_episodes') or []
    episode_count = len(ep_list)

    # Remove the rule itself
    before = len(scheduled_jobs)
    scheduled_jobs[:] = [j for j in scheduled_jobs if j is not rule_to_remove]

    # Also remove any standalone scheduled episodes that belong to same series (heuristic)
    removed_episode_count = 0
    if series_key:
        new_list = []
        for j in scheduled_jobs:
            same = False
            if j.get('series_key') == series_key:
                same = True
            elif j.get('series_group') and j.get('series_group') == title:
                same = True
            if same and j.get('type') != 'recurring_series':
                removed_episode_count += 1
                continue
            new_list.append(j)
        scheduled_jobs[:] = new_list

    save_schedule()
    print(f"Canceled recurring series '{title}' rule_id={rule_id}; rule removed; episodes_in_rule={episode_count}; standalone_removed={removed_episode_count}")
    return jsonify({
        "message": f"Canceled recurring series '{title}' (rule + {episode_count} rule-episodes, {removed_episode_count} standalone removed)",
        "removed_rule_id": rule_id
    })

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

@app.route("/bulk_download", methods=["POST"])
def bulk_download():
    """Handle bulk torrent downloads from episode selection"""
    data = request.get_json()
    
    if not data or 'episodes' not in data:
        return jsonify({"success": False, "message": "No episodes provided"})
    
    episodes = data['episodes']
    selected_episodes = [ep for ep in episodes if ep.get('selected', False)]
    
    if not selected_episodes:
        return jsonify({"success": False, "message": "No episodes selected"})
    
    download_results = []
    
    # Connect to qBittorrent
    try:
        import qbittorrentapi
        qbt_client = qbittorrentapi.Client(
            host='localhost',
            port=8080,
            username='admin',
            password=''
        )
        qbt_client.auth_log_in()
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to connect to qBittorrent: {str(e)}"})
    
    # Download each selected episode
    for episode in selected_episodes:
        try:
            magnet_link = episode.get('magnet')
            episode_title = episode.get('title', 'Unknown Episode')
            
            if not magnet_link:
                download_results.append({
                    "title": episode_title,
                    "success": False,
                    "message": "No magnet link available"
                })
                continue
            
            # Add torrent to qBittorrent
            qbt_client.torrents_add(urls=magnet_link)
            
            download_results.append({
                "title": episode_title,
                "success": True,
                "message": "Added to download queue"
            })
            
        except Exception as e:
            download_results.append({
                "title": episode.get('title', 'Unknown Episode'),
                "success": False,
                "message": f"Download failed: {str(e)}"
            })
    
    # Calculate summary
    successful = len([r for r in download_results if r['success']])
    total = len(download_results)
    
    return jsonify({
        "success": True,
        "message": f"Queued {successful}/{total} episodes for download",
        "results": download_results
    })

if __name__=="__main__":
    # Legal notice
    print("⚠️  LEGAL NOTICE: This software is for legitimate, legal use only.")
    print("   Only record over-the-air content you are legally entitled to receive.")
    print("   Users are responsible for complying with all applicable copyright laws.")
    print()
    
    # Load existing scheduled recordings
    load_schedule()

    import os as _os_main
    # Always start the schedule loop so time-based recurring rules can trigger.
    # The loop will NOT refresh EPG unless ENABLE_BACKGROUND_EPG_REFRESH=1.
    threading.Thread(target=run_schedule_loop, daemon=True).start()
    if _os_main.getenv('ENABLE_BACKGROUND_EPG_REFRESH','0') in ('1','true','True'):
        print("Background EPG refresh loop: EPG auto-refresh ENABLED")
    else:
        epg_refresh_enabled = os.getenv('ENABLE_BACKGROUND_EPG_REFRESH','1') in ('1','true','True')
    if epg_refresh_enabled:
        print("Background EPG refresh loop: EPG auto-refresh ENABLED (twice weekly)")
    else:
        print("Background EPG refresh loop: EPG auto-refresh DISABLED (set ENABLE_BACKGROUND_EPG_REFRESH=1 to enable)")

    # Check indexer availability on startup
    check_indexer_availability()

    # Port configuration from config file
    web_config = config.get_web_config()
    dvr_port = int(_os_main.getenv("DVR_PORT", str(web_config['port'])))
    app.run(host=web_config['host'], port=dvr_port, debug=web_config['debug'])

