"""
Configuration management for TV Recorder
Handles loading and validation of user configuration
"""
import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path=None):
        if config_path is None:
            # Look for config in several locations
            possible_locations = [
                Path.cwd() / "config.json",
                Path.home() / ".tv_recorder" / "config.json",
                Path(__file__).parent / "config.json"
            ]
            
            for location in possible_locations:
                if location.exists():
                    config_path = location
                    break
            else:
                # No config found, use default location
                config_path = Path.cwd() / "config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from file or create default"""
        if not self.config_path.exists():
            return self._create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return self._validate_and_fix_config(config)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading config: {e}")
            return self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration"""
        template_path = Path(__file__).parent / "config_template.json"
        if template_path.exists():
            with open(template_path, 'r') as f:
                default_config = json.load(f)
        else:
            default_config = {
                "hdhr": {"ip_address": "192.168.1.100"},
                "directories": {
                    "recordings": "~/TV_Recordings",
                    "tv_shows": "~/TV Shows", 
                    "movies": "~/Movies"
                },
                "ffmpeg": {"path": "ffmpeg"},
                "prowlarr": {"enabled": False, "api_url": "http://127.0.0.1:9696", "api_key": "", "timeout": 15},
                "biratepay": {"enabled": False, "port": 5055},
                "web_interface": {"host": "0.0.0.0", "port": 5000, "debug": False}
            }
        
        return default_config
    
    def _validate_and_fix_config(self, config):
        """Validate and fix configuration with defaults"""
        defaults = self._create_default_config()
        
        def merge_dicts(default, user):
            result = default.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            return result
        
        return merge_dicts(defaults, config)
    
    def save_config(self):
        """Save current configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, section, key=None, default=None):
        """Get configuration value"""
        if key is None:
            return self.config.get(section, default)
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section, key, value):
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def expand_path(self, path_str):
        """Expand path with home directory and environment variables"""
        if not path_str:
            return None
            
        # Expand ~ to home directory
        if path_str.startswith('~/'):
            path_str = str(Path.home() / path_str[2:])
        
        # Expand environment variables
        path_str = os.path.expandvars(path_str)
        
        return Path(path_str)
    
    def get_recording_dir(self):
        """Get expanded recordings directory path"""
        recordings_dir = self.get('directories', 'recordings', '~/TV_Recordings')
        return self.expand_path(recordings_dir)
    
    def get_tv_shows_dir(self):
        """Get expanded TV shows directory path"""
        tv_dir = self.get('directories', 'tv_shows', '~/TV Shows')
        return self.expand_path(tv_dir)
    
    def get_movies_dir(self):
        """Get expanded movies directory path"""
        movies_dir = self.get('directories', 'movies', '~/Movies')
        return self.expand_path(movies_dir)
    
    def get_ffmpeg_path(self):
        """Get ffmpeg executable path"""
        return self.get('ffmpeg', 'path', 'ffmpeg')
    
    def get_hdhr_ip(self):
        """Get HDHomeRun IP address"""
        return self.get('hdhr', 'ip_address', '192.168.1.100')
    
    def is_prowlarr_enabled(self):
        """Check if Prowlarr integration is enabled"""
        return self.get('prowlarr', 'enabled', False)
    
    def get_prowlarr_config(self):
        """Get Prowlarr configuration"""
        return {
            'api_url': self.get('prowlarr', 'api_url', 'http://127.0.0.1:9696'),
            'api_key': self.get('prowlarr', 'api_key', ''),
            'timeout': self.get('prowlarr', 'timeout', 15)
        }
    
    def is_biratepay_enabled(self):
        """Check if BiratePayment integration is enabled"""
        return self.get('biratepay', 'enabled', False)
    
    def get_web_config(self):
        """Get web interface configuration"""
        return {
            'host': self.get('web_interface', 'host', '0.0.0.0'),
            'port': self.get('web_interface', 'port', 5000),
            'debug': self.get('web_interface', 'debug', False)
        }
    
    def get_epg_config(self):
        """Get EPG configuration"""
        return {
            'zip_code': self.get('epg', 'zip_code', '78748'),
            'headend_id': self.get('epg', 'headend_id', ''),
            'timezone': self.get('epg', 'timezone', 'America/Chicago'),
            'auto_refresh': self.get('epg', 'auto_refresh', False),
            'refresh_hours': self.get('epg', 'refresh_hours', [6, 14, 22])
        }

# Global config instance
config = None

def get_config():
    """Get global configuration instance"""
    global config
    if config is None:
        config = ConfigManager()
    return config

def reload_config():
    """Reload configuration from file"""
    global config
    config = ConfigManager()
    return config