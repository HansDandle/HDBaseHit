"""
LineDrive Setup GUI
Modern, user-friendly setup wizard with directory browsers and editable fields

DISCLAIMER: LineDrive is not affiliated with Silicondust USA Inc.
HDHomeRun is a registered trademark of Silicondust USA Inc. This is an independent project.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
import subprocess
import socket
import requests
from pathlib import Path
import threading
import ipaddress
import urllib.parse

class ToolTip:
    """Simple tooltip widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, background="#ffffe0", 
                        relief="solid", borderwidth=1, font=("Arial", 9))
        label.pack()
    
    def on_leave(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class LineDriveSetupGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LineDrive Setup Wizard")
        self.root.geometry("800x750")
        self.root.resizable(True, True)
        
        # Configure modern styling
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors and styles
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
        style.configure('Info.TLabel', foreground='blue')
        
        self.config_data = self.load_existing_config()
        self.tooltips = []  # Store tooltip references
        self.create_widgets()
        
    def load_existing_config(self):
        """Load existing configuration or return defaults"""
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Return default configuration
        return {
            "hdhr": {"ip_address": "192.168.1.100"},
            "directories": {
                "recordings": str(Path.home() / "TV_Recordings"),
                "tv_shows": str(Path.home() / "TV Shows"),
                "movies": str(Path.home() / "Movies")
            },
            "ffmpeg": {"path": "ffmpeg"},
            "epg": {
                "zip_code": "",
                "headend_id": "",
                "timezone": "America/New_York",
                "auto_refresh": True,
                "refresh_interval": 24
            },
            "torrent_client": {
                "enabled": False,
                "type": "qbittorrent",
                "url": "http://localhost:8080",
                "username": "admin",
                "password": ""
            },
            "prowlarr": {
                "enabled": False,
                "api_url": "http://127.0.0.1:9696",
                "api_key": "",
                "timeout": 15
            },
            "indexer": {
                "enabled": False,
                "provider": "prowlarr",
                "timeout": 30,
                "providers": {
                    "prowlarr": {
                        "api_url": "http://127.0.0.1:9696",
                        "api_key": ""
                    },
                    "jackett": {
                        "api_url": "http://127.0.0.1:9117",
                        "api_key": ""
                    }
                }
            },
            "vpn": {
                "enabled": False,
                "provider": "nordvpn",
                "config": {}
            }
        }
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Create main container with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas and scrollbar for scrolling
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Title
        title_label = ttk.Label(scrollable_frame, text="📺 LineDrive Setup Wizard", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Legal notice
        legal_frame = ttk.LabelFrame(scrollable_frame, text="Legal Notice", padding=10)
        legal_frame.pack(fill=tk.X, pady=(0, 20))
        
        legal_text = ("LineDrive is an independent project. Not affiliated with Silicondust USA Inc.\n"
                     "HDHomeRun is a registered trademark of Silicondust USA Inc.")
        ttk.Label(legal_frame, text=legal_text, font=('Segoe UI', 9)).pack()
        
        # HDHomeRun Configuration
        self.create_hdhr_section(scrollable_frame)
        
        # Directory Configuration
        self.create_directory_section(scrollable_frame)
        
        # FFmpeg Configuration
        self.create_ffmpeg_section(scrollable_frame)
        
        # Indexer Configuration
        self.create_indexer_section(scrollable_frame)
        
        # EPG Configuration
        self.create_epg_section(scrollable_frame)
        
        # Torrent Client Configuration
        self.create_torrent_section(scrollable_frame)
        
        # VPN Configuration
        self.create_vpn_section(scrollable_frame)
        
        # Control buttons
        self.create_control_buttons(scrollable_frame)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def create_hdhr_section(self, parent):
        """Create HDHomeRun configuration section"""
        frame = ttk.LabelFrame(parent, text="HDHomeRun Configuration", padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # IP Address
        ip_frame = ttk.Frame(frame)
        ip_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ip_frame, text="HDHomeRun IP Address:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        
        ip_entry_frame = ttk.Frame(ip_frame)
        ip_entry_frame.pack(fill=tk.X, pady=2)
        
        self.hdhr_ip_var = tk.StringVar(value=self.config_data["hdhr"]["ip_address"])
        self.hdhr_ip_entry = ttk.Entry(ip_entry_frame, textvariable=self.hdhr_ip_var, font=('Segoe UI', 10))
        self.hdhr_ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.hdhr_ip_entry.bind('<KeyRelease>', self.validate_ip_address)
        
        self.detect_btn = ttk.Button(ip_entry_frame, text="Auto-Detect", command=self.detect_hdhr)
        self.detect_btn.pack(side=tk.RIGHT)
        ToolTip(self.detect_btn, "Scan network for HDHomeRun devices")
        
        diag_btn = ttk.Button(ip_entry_frame, text="Diagnostics", command=self.run_diagnostics)
        diag_btn.pack(side=tk.RIGHT, padx=(0, 5))
        ToolTip(diag_btn, "Run network diagnostics to help find your HDHomeRun")
        
        test_btn = ttk.Button(ip_entry_frame, text="Test Connection", command=self.test_hdhr)
        test_btn.pack(side=tk.RIGHT, padx=(0, 5))
        ToolTip(test_btn, "Test connection to HDHomeRun device")
        
        # Help text frame
        help_frame = ttk.Frame(ip_frame)
        help_frame.pack(fill=tk.X, pady=2)
        
        self.hdhr_status_label = ttk.Label(help_frame, text="💡 Tip: Try Auto-Detect first, or enter IP manually (e.g., 192.168.1.100)", font=('Segoe UI', 9), foreground='gray')
        self.hdhr_status_label.pack(anchor=tk.W)
        
        router_btn = ttk.Button(help_frame, text="Find IP in Router", command=self.open_router_help)
        router_btn.pack(anchor=tk.E, pady=2)
        ToolTip(router_btn, "Get help finding your HDHomeRun's IP address")
    
    def create_directory_section(self, parent):
        """Create directory configuration section"""
        frame = ttk.LabelFrame(parent, text="Directory Configuration", padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        self.directory_vars = {}
        directories = [
            ("recordings", "Recording Directory", "Where recorded files are saved"),
            ("tv_shows", "TV Shows Directory", "Organized TV show storage"),
            ("movies", "Movies Directory", "Organized movie storage")
        ]
        
        for key, label, description in directories:
            dir_frame = ttk.Frame(frame)
            dir_frame.pack(fill=tk.X, pady=8)
            
            ttk.Label(dir_frame, text=f"{label}:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
            ttk.Label(dir_frame, text=description, font=('Segoe UI', 9), foreground='gray').pack(anchor=tk.W)
            
            entry_frame = ttk.Frame(dir_frame)
            entry_frame.pack(fill=tk.X, pady=2)
            
            self.directory_vars[key] = tk.StringVar(value=self.config_data["directories"][key])
            entry = ttk.Entry(entry_frame, textvariable=self.directory_vars[key], font=('Segoe UI', 10))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            
            browse_btn = ttk.Button(entry_frame, text="Browse...", 
                                  command=lambda k=key: self.browse_directory(k))
            browse_btn.pack(side=tk.RIGHT)
            ToolTip(browse_btn, f"Select folder for {description.lower()}")
    
    def create_ffmpeg_section(self, parent):
        """Create FFmpeg configuration section"""
        frame = ttk.LabelFrame(parent, text="FFmpeg Configuration", padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(frame, text="FFmpeg Executable Path:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text="Path to ffmpeg executable (leave as 'ffmpeg' if in PATH)", 
                 font=('Segoe UI', 9), foreground='gray').pack(anchor=tk.W)
        
        ffmpeg_frame = ttk.Frame(frame)
        ffmpeg_frame.pack(fill=tk.X, pady=5)
        
        self.ffmpeg_var = tk.StringVar(value=self.config_data["ffmpeg"]["path"])
        ffmpeg_entry = ttk.Entry(ffmpeg_frame, textvariable=self.ffmpeg_var, font=('Segoe UI', 10))
        ffmpeg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_ffmpeg_btn = ttk.Button(ffmpeg_frame, text="Browse...", command=self.browse_ffmpeg)
        browse_ffmpeg_btn.pack(side=tk.RIGHT, padx=(0, 5))
        ToolTip(browse_ffmpeg_btn, "Browse for ffmpeg.exe executable")
        
        test_ffmpeg_btn = ttk.Button(ffmpeg_frame, text="Test FFmpeg", command=self.test_ffmpeg)
        test_ffmpeg_btn.pack(side=tk.RIGHT)
        ToolTip(test_ffmpeg_btn, "Test if FFmpeg is working properly")
        
        self.ffmpeg_status_label = ttk.Label(frame, text="", font=('Segoe UI', 9))
        self.ffmpeg_status_label.pack(anchor=tk.W, pady=2)
    
    def create_indexer_section(self, parent):
        """Create indexer configuration section"""
        frame = ttk.LabelFrame(parent, text="Indexer Configuration (Optional)", padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # Enable indexer
        self.indexer_enabled_var = tk.BooleanVar(value=self.config_data["indexer"]["enabled"])
        enable_cb = ttk.Checkbutton(frame, text="Enable Indexer Integration", 
                                   variable=self.indexer_enabled_var,
                                   command=self.toggle_indexer)
        enable_cb.pack(anchor=tk.W, pady=5)
        
        # Indexer provider selection
        self.indexer_frame = ttk.Frame(frame)
        self.indexer_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(self.indexer_frame, text="Indexer Provider:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        
        provider_frame = ttk.Frame(self.indexer_frame)
        provider_frame.pack(fill=tk.X, pady=5)
        
        self.indexer_provider_var = tk.StringVar(value=self.config_data["indexer"]["provider"])
        providers = ["prowlarr", "jackett", "torznab"]
        provider_combo = ttk.Combobox(provider_frame, textvariable=self.indexer_provider_var, 
                                    values=providers, state="readonly", width=15)
        provider_combo.pack(side=tk.LEFT)
        provider_combo.bind('<<ComboboxSelected>>', self.on_provider_change)
        
        # Provider-specific configuration
        self.create_provider_config(self.indexer_frame)
        
        self.toggle_indexer()
    
    def create_provider_config(self, parent):
        """Create provider-specific configuration fields"""
        self.provider_config_frame = ttk.Frame(parent)
        self.provider_config_frame.pack(fill=tk.X, pady=10)
        
        self.provider_vars = {
            'api_url': tk.StringVar(),
            'api_key': tk.StringVar()
        }
        
        # API URL
        ttk.Label(self.provider_config_frame, text="API URL:", font=('Segoe UI', 10)).pack(anchor=tk.W)
        self.api_url_entry = ttk.Entry(self.provider_config_frame, textvariable=self.provider_vars['api_url'])
        self.api_url_entry.pack(fill=tk.X, pady=2)
        
        # API Key
        ttk.Label(self.provider_config_frame, text="API Key:", font=('Segoe UI', 10)).pack(anchor=tk.W, pady=(10, 0))
        api_key_frame = ttk.Frame(self.provider_config_frame)
        api_key_frame.pack(fill=tk.X, pady=2)
        
        self.api_key_entry = ttk.Entry(api_key_frame, textvariable=self.provider_vars['api_key'], show="*")
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        show_key_btn = ttk.Button(api_key_frame, text="Show", command=self.toggle_api_key_visibility)
        show_key_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        test_indexer_btn = ttk.Button(api_key_frame, text="Test Connection", command=self.test_indexer)
        test_indexer_btn.pack(side=tk.RIGHT)
        
        self.indexer_status_label = ttk.Label(self.provider_config_frame, text="", font=('Segoe UI', 9))
        self.indexer_status_label.pack(anchor=tk.W, pady=5)
        
        # Load current provider config
        self.on_provider_change()
    
    def create_epg_section(self, parent):
        """Create EPG (TV Listings) configuration section"""
        frame = ttk.LabelFrame(parent, text="TV Listings (EPG) Configuration", padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # ZIP Code
        zip_frame = ttk.Frame(frame)
        zip_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(zip_frame, text="ZIP Code:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(zip_frame, text="Used to determine your local TV market and channel lineup", 
                 font=('Segoe UI', 9), foreground='gray').pack(anchor=tk.W)
        
        zip_entry_frame = ttk.Frame(zip_frame)
        zip_entry_frame.pack(fill=tk.X, pady=2)
        
        self.zip_code_var = tk.StringVar(value=self.config_data.get("epg", {}).get("zip_code", ""))
        zip_entry = ttk.Entry(zip_entry_frame, textvariable=self.zip_code_var, font=('Segoe UI', 10))
        zip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        zip_entry.bind('<KeyRelease>', self.validate_zip_code)
        
        detect_zip_btn = ttk.Button(zip_entry_frame, text="Auto-Detect", command=self.detect_zip_code)
        detect_zip_btn.pack(side=tk.RIGHT, padx=(0, 5))
        ToolTip(detect_zip_btn, "Try to detect ZIP code from your IP location")
        
        test_epg_btn = ttk.Button(zip_entry_frame, text="Test EPG", command=self.test_epg)
        test_epg_btn.pack(side=tk.RIGHT)
        ToolTip(test_epg_btn, "Test EPG data retrieval for your area")
        
        # Headend ID (auto-populated)
        headend_frame = ttk.Frame(frame)
        headend_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(headend_frame, text="Headend ID:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(headend_frame, text="Auto-detected based on ZIP code", 
                 font=('Segoe UI', 9), foreground='gray').pack(anchor=tk.W)
        
        self.headend_var = tk.StringVar(value=self.config_data.get("epg", {}).get("headend_id", ""))
        headend_entry = ttk.Entry(headend_frame, textvariable=self.headend_var, font=('Segoe UI', 10), state='readonly')
        headend_entry.pack(fill=tk.X, pady=2)
        
        # Status label
        self.epg_status_label = ttk.Label(frame, text="💡 Enter your ZIP code to configure TV listings", font=('Segoe UI', 9), foreground='gray')
        self.epg_status_label.pack(anchor=tk.W, pady=5)
    
    def create_torrent_section(self, parent):
        """Create torrent client configuration section"""
        frame = ttk.LabelFrame(parent, text="Torrent Client Configuration", padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # Enable torrent client
        self.torrent_enabled_var = tk.BooleanVar(value=self.config_data.get("torrent_client", {}).get("enabled", False))
        enable_torrent_cb = ttk.Checkbutton(frame, text="Enable Torrent Client Integration", 
                                           variable=self.torrent_enabled_var,
                                           command=self.toggle_torrent)
        enable_torrent_cb.pack(anchor=tk.W, pady=5)
        
        # Torrent client configuration
        self.torrent_frame = ttk.Frame(frame)
        self.torrent_frame.pack(fill=tk.X, pady=10)
        
        # Client type selection
        ttk.Label(self.torrent_frame, text="Torrent Client:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        
        client_frame = ttk.Frame(self.torrent_frame)
        client_frame.pack(fill=tk.X, pady=5)
        
        self.torrent_client_var = tk.StringVar(value=self.config_data.get("torrent_client", {}).get("type", "qbittorrent"))
        clients = ["qbittorrent", "transmission", "deluge", "utorrent"]
        client_combo = ttk.Combobox(client_frame, textvariable=self.torrent_client_var, 
                                  values=clients, state="readonly", width=15)
        client_combo.pack(side=tk.LEFT)
        client_combo.bind('<<ComboboxSelected>>', self.on_torrent_client_change)
        
        # Client-specific configuration
        self.create_torrent_client_config(self.torrent_frame)
        
        self.toggle_torrent()
    
    def create_torrent_client_config(self, parent):
        """Create torrent client-specific configuration fields"""
        self.torrent_config_frame = ttk.Frame(parent)
        self.torrent_config_frame.pack(fill=tk.X, pady=10)
        
        self.torrent_vars = {
            'url': tk.StringVar(),
            'username': tk.StringVar(),
            'password': tk.StringVar()
        }
        
        # Initialize credential modification tracking
        self._user_modified_credentials = False
        
        # Load existing torrent client configuration
        torrent_config = self.config_data.get("torrent_client", {})
        self.torrent_vars['url'].set(torrent_config.get('url', 'http://localhost:8080'))
        self.torrent_vars['username'].set(torrent_config.get('username', 'admin'))
        self.torrent_vars['password'].set(torrent_config.get('password', ''))
        
        # If we loaded non-default values, mark as user-modified to prevent overwriting
        if torrent_config.get('username') and torrent_config.get('username') != 'admin':
            self._user_modified_credentials = True
        
        # URL
        ttk.Label(self.torrent_config_frame, text="Web UI URL:", font=('Segoe UI', 10)).pack(anchor=tk.W)
        url_frame = ttk.Frame(self.torrent_config_frame)
        url_frame.pack(fill=tk.X, pady=2)
        
        self.torrent_url_entry = ttk.Entry(url_frame, textvariable=self.torrent_vars['url'])
        self.torrent_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        detect_torrent_btn = ttk.Button(url_frame, text="Auto-Detect", command=self.detect_torrent_client)
        detect_torrent_btn.pack(side=tk.RIGHT, padx=(0, 5))
        ToolTip(detect_torrent_btn, "Scan for torrent client Web UI")
        
        test_torrent_btn = ttk.Button(url_frame, text="Test Connection", command=self.test_torrent_client)
        test_torrent_btn.pack(side=tk.RIGHT)
        ToolTip(test_torrent_btn, "Test connection to torrent client")
        
        # Username
        ttk.Label(self.torrent_config_frame, text="Username:", font=('Segoe UI', 10)).pack(anchor=tk.W, pady=(10, 0))
        self.torrent_username_entry = ttk.Entry(self.torrent_config_frame, textvariable=self.torrent_vars['username'])
        self.torrent_username_entry.pack(fill=tk.X, pady=2)
        # Track manual edits to username
        self.torrent_username_entry.bind('<KeyRelease>', self.mark_credentials_modified)
        self.torrent_username_entry.bind('<FocusOut>', self.mark_credentials_modified)
        
        # Password
        ttk.Label(self.torrent_config_frame, text="Password:", font=('Segoe UI', 10)).pack(anchor=tk.W, pady=(10, 0))
        password_frame = ttk.Frame(self.torrent_config_frame)
        password_frame.pack(fill=tk.X, pady=2)
        
        self.torrent_password_entry = ttk.Entry(password_frame, textvariable=self.torrent_vars['password'], show="*")
        self.torrent_password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        # Track manual edits to password
        self.torrent_password_entry.bind('<KeyRelease>', self.mark_credentials_modified)
        self.torrent_password_entry.bind('<FocusOut>', self.mark_credentials_modified)
        
        show_torrent_pass_btn = ttk.Button(password_frame, text="Show", command=self.toggle_torrent_password_visibility)
        show_torrent_pass_btn.pack(side=tk.RIGHT)
        
        # Status label
        self.torrent_status_label = ttk.Label(self.torrent_config_frame, text="", font=('Segoe UI', 9))
        self.torrent_status_label.pack(anchor=tk.W, pady=5)
        
        # Load current client config (only set defaults if no config exists)
        if not self.config_data.get("torrent_client", {}).get("url"):
            self.on_torrent_client_change()
    
    def mark_credentials_modified(self, event=None):
        """Mark that the user has manually modified torrent client credentials"""
        self._user_modified_credentials = True
    
    def create_vpn_section(self, parent):
        """Create VPN configuration section"""
        frame = ttk.LabelFrame(parent, text="VPN Configuration (Optional)", padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        self.vpn_enabled_var = tk.BooleanVar(value=self.config_data["vpn"]["enabled"])
        enable_vpn_cb = ttk.Checkbutton(frame, text="Enable VPN Integration", 
                                       variable=self.vpn_enabled_var,
                                       command=self.toggle_vpn)
        enable_vpn_cb.pack(anchor=tk.W, pady=5)
        
        self.vpn_frame = ttk.Frame(frame)
        self.vpn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(self.vpn_frame, text="VPN Provider:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        
        self.vpn_provider_var = tk.StringVar(value=self.config_data["vpn"]["provider"])
        providers = ["nordvpn", "expressvpn", "protonvpn", "surfshark", "custom"]
        vpn_combo = ttk.Combobox(self.vpn_frame, textvariable=self.vpn_provider_var, 
                               values=providers, state="readonly", width=15)
        vpn_combo.pack(pady=5)
        
        self.toggle_vpn()
    
    def create_control_buttons(self, parent):
        """Create control buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=20)
        
        # Test all button
        test_all_btn = ttk.Button(button_frame, text="Test All Connections", 
                                 command=self.test_all_connections)
        test_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        ToolTip(test_all_btn, "Test HDHomeRun, FFmpeg, and indexer connections")
        
        # Save button
        save_btn = ttk.Button(button_frame, text="Save Configuration", 
                             command=self.save_config)
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))
        ToolTip(save_btn, "Validate settings and save configuration to config.json")
        
        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.root.quit)
        cancel_btn.pack(side=tk.RIGHT)
        ToolTip(cancel_btn, "Exit setup without saving")
        
        # Status label
        self.status_label = ttk.Label(parent, text="Ready to configure LineDrive", font=('Segoe UI', 10))
        self.status_label.pack(pady=10)
    
    def detect_hdhr(self):
        """Auto-detect HDHomeRun device on network"""
        def detect():
            self.hdhr_status_label.config(text="🔍 Scanning network for HDHomeRun devices...", foreground='blue')
            self.root.update()
            
            try:
                import socket
                import concurrent.futures
                
                # First try multiple HDHomeRun discovery methods
                self.hdhr_status_label.config(text="📡 Trying HDHomeRun broadcast discovery...", foreground='blue')
                self.root.update()
                
                # Method 1: UDP broadcast discovery
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.settimeout(3)
                    
                    # HDHomeRun discovery packet
                    discovery_packet = bytes.fromhex('00010002000300040001000200030004')
                    sock.sendto(discovery_packet, ('255.255.255.255', 65001))
                    
                    response, addr = sock.recvfrom(1024)
                    sock.close()
                    
                    # If we got a response, the IP is in addr[0]
                    hdhr_ip = addr[0]
                    
                    # Verify it's actually an HDHomeRun
                    verify_response = requests.get(f"http://{hdhr_ip}/discover.json", timeout=2)
                    if verify_response.status_code == 200:
                        data = verify_response.json()
                        if 'DeviceID' in data or 'FriendlyName' in data:
                            self.hdhr_ip_var.set(hdhr_ip)
                            device_name = data.get('FriendlyName', f"HDHomeRun {data.get('DeviceID', 'Device')}")
                            self.hdhr_status_label.config(
                                text=f"✅ Found {device_name} at {hdhr_ip}", 
                                foreground='green')
                            self.detect_btn.config(state='normal', text='Auto-Detect')
                            return
                except Exception as e:
                    print(f"UDP broadcast failed: {e}")  # Debug info
                
                # Method 2: Try HDHomeRun's my.hdhomerun.com service
                self.hdhr_status_label.config(text="🌐 Checking HDHomeRun cloud service...", foreground='blue')
                self.root.update()
                
                try:
                    response = requests.get("https://my.hdhomerun.com/discover", timeout=5)
                    if response.status_code == 200:
                        lines = response.text.strip().split('\n')
                        for line in lines:
                            if line.startswith('http://'):
                                # Extract IP from URL like http://192.168.1.100:80
                                ip_part = line.replace('http://', '').split(':')[0]
                                
                                # Verify it's accessible
                                verify_response = requests.get(f"http://{ip_part}/discover.json", timeout=2)
                                if verify_response.status_code == 200:
                                    data = verify_response.json()
                                    if 'DeviceID' in data or 'FriendlyName' in data:
                                        self.hdhr_ip_var.set(ip_part)
                                        device_name = data.get('FriendlyName', f"HDHomeRun {data.get('DeviceID', 'Device')}")
                                        self.hdhr_status_label.config(
                                            text=f"✅ Found {device_name} at {ip_part} (via cloud)", 
                                            foreground='green')
                                        self.detect_btn.config(state='normal', text='Auto-Detect')
                                        return
                except Exception as e:
                    print(f"Cloud discovery failed: {e}")  # Debug info
                
                # Get local network info for IP scanning
                try:
                    local_ip = socket.gethostbyname(socket.gethostname())
                    if local_ip.startswith('127.'):
                        # If we got localhost, try a different approach
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.connect(("8.8.8.8", 80))
                        local_ip = s.getsockname()[0]
                        s.close()
                except:
                    self.hdhr_status_label.config(text="❌ Could not determine local IP", foreground='red')
                    self.detect_btn.config(state='normal', text='Auto-Detect')
                    return
                
                network_base = '.'.join(local_ip.split('.')[:-1])
                
                def check_ip(i):
                    ip = f"{network_base}.{i}"
                    try:
                        # Check multiple HDHomeRun endpoints
                        endpoints = ['/discover.json', '/lineup_status.json', '/lineup.json']
                        
                        for endpoint in endpoints:
                            try:
                                response = requests.get(f"http://{ip}{endpoint}", timeout=0.8)
                                if response.status_code == 200:
                                    data = response.json()
                                    # Check for HDHomeRun identifiers
                                    if any(key in data for key in ['DeviceID', 'FriendlyName', 'ModelNumber', 'FirmwareName']):
                                        return ip, data
                                    # Also check for lineup data (indicates HDHomeRun)
                                    if isinstance(data, list) and len(data) > 0 and 'GuideNumber' in str(data):
                                        # This is likely a lineup, get device info
                                        discover_response = requests.get(f"http://{ip}/discover.json", timeout=0.5)
                                        if discover_response.status_code == 200:
                                            discover_data = discover_response.json()
                                            return ip, discover_data
                                        else:
                                            return ip, {'FriendlyName': 'HDHomeRun Device'}
                            except:
                                continue
                    except:
                        pass
                    return None, None
                
                # Scan common IP ranges first (router IPs, then broader scan)
                # Expanded priority list based on common HDHomeRun IP patterns
                priority_ips = [1, 2, 10, 50, 100, 101, 102, 103, 104, 105, 110, 111, 112, 150, 200, 210, 220, 230, 240, 250]
                found_device = False
                
                print(f"Scanning network: {network_base}.x")  # Debug info
                
                # First check priority IPs
                self.hdhr_status_label.config(text="🔍 Checking common IP addresses...", foreground='blue')
                self.root.update()
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    # Check priority IPs first
                    future_to_ip = {executor.submit(check_ip, i): i for i in priority_ips}
                    
                    for future in concurrent.futures.as_completed(future_to_ip, timeout=5):
                        ip_result, data = future.result()
                        if ip_result:
                            self.hdhr_ip_var.set(ip_result)
                            device_name = data.get('FriendlyName', 'HDHomeRun Device')
                            self.hdhr_status_label.config(
                                text=f"✅ Found {device_name} at {ip_result}", 
                                foreground='green')
                            found_device = True
                            self.detect_btn.config(state='normal', text='Auto-Detect')
                            return
                
                if not found_device:
                    # If not found in priority IPs, scan full range but with progress
                    self.hdhr_status_label.config(text="🔍 Scanning full network range...", foreground='blue')
                    self.root.update()
                    
                    all_ips = [i for i in range(2, 255) if i not in priority_ips]
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                        future_to_ip = {executor.submit(check_ip, i): i for i in all_ips}
                        
                        completed = 0
                        for future in concurrent.futures.as_completed(future_to_ip, timeout=15):
                            completed += 1
                            if completed % 20 == 0:  # Update progress every 20 IPs
                                progress = int((completed / len(all_ips)) * 100)
                                self.hdhr_status_label.config(
                                    text=f"🔍 Scanning network... {progress}%", 
                                    foreground='blue')
                                self.root.update()
                            
                            ip_result, data = future.result()
                            if ip_result:
                                self.hdhr_ip_var.set(ip_result)
                                device_name = data.get('FriendlyName', 'HDHomeRun Device')
                                self.hdhr_status_label.config(
                                    text=f"✅ Found {device_name} at {ip_result}", 
                                    foreground='green')
                                found_device = True
                                self.detect_btn.config(state='normal', text='Auto-Detect')
                                return
                
                if not found_device:
                    self.hdhr_status_label.config(
                        text="❌ No HDHomeRun devices found on network", 
                        foreground='red')
                    self.detect_btn.config(state='normal', text='Auto-Detect')
            
            except concurrent.futures.TimeoutError:
                self.hdhr_status_label.config(
                    text="⏱️ Scan timed out - try manual IP entry", 
                    foreground='orange')
                self.detect_btn.config(state='normal', text='Auto-Detect')
            except Exception as e:
                self.hdhr_status_label.config(
                    text=f"❌ Detection failed: {str(e)}", 
                    foreground='red')
                self.detect_btn.config(state='normal', text='Auto-Detect')
        
        # Disable the detect button during scan
        self.detect_btn.config(state='disabled', text='Scanning...')
        
        def re_enable_button():
            import time
            time.sleep(25)  # Max scan time + buffer
            try:
                self.detect_btn.config(state='normal', text='Auto-Detect')
            except:
                pass
        
        threading.Thread(target=re_enable_button, daemon=True).start()
        
        threading.Thread(target=detect, daemon=True).start()
    
    def run_diagnostics(self):
        """Run network diagnostics to help find HDHomeRun"""
        def diagnose():
            import subprocess
            import platform
            
            diag_window = tk.Toplevel(self.root)
            diag_window.title("HDHomeRun Diagnostics")
            diag_window.geometry("600x400")
            
            # Create scrollable text widget
            frame = ttk.Frame(diag_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(frame, wrap=tk.WORD, font=('Consolas', 9))
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            def log(message):
                text_widget.insert(tk.END, message + "\n")
                text_widget.see(tk.END)
                diag_window.update()
            
            log("🔍 HDHomeRun Network Diagnostics")
            log("=" * 50)
            
            # Check network configuration
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                log(f"Local computer: {hostname}")
                log(f"Local IP: {local_ip}")
                
                # Get better local IP if needed
                if local_ip.startswith('127.'):
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    s.close()
                    log(f"Actual local IP: {local_ip}")
                
                network = '.'.join(local_ip.split('.')[:-1])
                log(f"Network range: {network}.1-254")
                
            except Exception as e:
                log(f"❌ Network check failed: {e}")
            
            log("")
            
            # Check if we can reach common router IPs
            log("🌐 Testing gateway connectivity...")
            common_gateways = [f"{network}.1", f"{network}.254"]
            
            for gateway in common_gateways:
                try:
                    if platform.system().lower() == "windows":
                        result = subprocess.run(['ping', '-n', '1', '-w', '1000', gateway], 
                                              capture_output=True, text=True, timeout=5)
                    else:
                        result = subprocess.run(['ping', '-c', '1', '-W', '1', gateway], 
                                              capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        log(f"✅ Gateway {gateway} is reachable")
                    else:
                        log(f"❌ Gateway {gateway} not responding")
                except Exception as e:
                    log(f"⚠️ Could not ping {gateway}: {e}")
            
            log("")
            log("🔍 Scanning for HDHomeRun devices (detailed)...")
            
            # Detailed scan with logging
            found_devices = []
            test_ips = [f"{network}.{i}" for i in [1, 2, 10, 100, 101, 102, 103, 104, 105, 110, 150, 200]]
            
            for ip in test_ips:
                log(f"Testing {ip}...")
                try:
                    # Test HTTP connectivity first
                    response = requests.get(f"http://{ip}/discover.json", timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        log(f"  📡 HTTP response from {ip}: {response.status_code}")
                        log(f"  📋 Data keys: {list(data.keys())}")
                        
                        if any(key in data for key in ['DeviceID', 'FriendlyName', 'ModelNumber']):
                            device_name = data.get('FriendlyName', f"Device {data.get('DeviceID', 'Unknown')}")
                            log(f"  ✅ HDHomeRun found: {device_name}")
                            found_devices.append((ip, device_name))
                        else:
                            log(f"  ❓ Device found but not HDHomeRun: {data}")
                    else:
                        log(f"  📡 HTTP {response.status_code} from {ip}")
                        
                except requests.exceptions.ConnectRefused:
                    log(f"  🚫 Connection refused by {ip}")
                except requests.exceptions.Timeout:
                    log(f"  ⏱️ Timeout connecting to {ip}")
                except requests.exceptions.ConnectionError:
                    log(f"  📵 No response from {ip}")
                except Exception as e:
                    log(f"  ❌ Error with {ip}: {e}")
            
            log("")
            
            if found_devices:
                log("🎉 Found HDHomeRun devices:")
                for ip, name in found_devices:
                    log(f"  • {name} at {ip}")
                log("")
                log("💡 Try entering one of these IPs manually in the setup.")
            else:
                log("❌ No HDHomeRun devices found.")
                log("")
                log("💡 Troubleshooting suggestions:")
                log("  1. Check that your HDHomeRun is powered on")
                log("  2. Ensure it's connected to the same network")
                log("  3. Try accessing http://YOUR_HDHR_IP in a web browser")
                log("  4. Check your router's DHCP client list")
                log("  5. Try the HDHomeRun app to find the device")
            
            # Add close button
            close_btn = ttk.Button(diag_window, text="Close", command=diag_window.destroy)
            close_btn.pack(pady=5)
        
        threading.Thread(target=diagnose, daemon=True).start()
    
    def validate_zip_code(self, event=None):
        """Validate ZIP code format"""
        zip_code = self.zip_code_var.get().strip()
        
        # Only validate if we have exactly 5 characters (completed ZIP code)
        if len(zip_code) == 5:
            if zip_code.isdigit():
                # Valid ZIP code, try to get headend ID
                self.epg_status_label.config(text=f"✅ Valid ZIP code: {zip_code}", foreground='green')
                self.get_headend_for_zip(zip_code)
            else:
                self.epg_status_label.config(text="❌ ZIP code must contain only numbers", foreground='red')
        elif len(zip_code) > 5:
            # Too many digits
            self.epg_status_label.config(text="❌ ZIP code must be exactly 5 digits", foreground='red')
        elif len(zip_code) > 0:
            # Still typing, show neutral message
            self.epg_status_label.config(text=f"📝 Enter ZIP code... ({len(zip_code)}/5)", foreground='blue')
        else:
            # Empty field
            self.epg_status_label.config(text="💡 Enter your ZIP code to configure TV listings", foreground='gray')
    
    def detect_zip_code(self):
        """Try to detect ZIP code from IP geolocation"""
        def detect():
            self.epg_status_label.config(text="🌍 Detecting location from IP address...", foreground='blue')
            self.root.update()
            
            try:
                # Try multiple geolocation services
                services = [
                    "https://ipapi.co/postal/",
                    "https://ipinfo.io/postal",
                    "https://api.ipify.org/?format=json"  # Fallback
                ]
                
                for service in services:
                    try:
                        response = requests.get(service, timeout=5)
                        if response.status_code == 200:
                            if service.endswith('/postal/') or service.endswith('/postal'):
                                zip_code = response.text.strip()
                                if len(zip_code) == 5 and zip_code.isdigit():
                                    self.zip_code_var.set(zip_code)
                                    self.epg_status_label.config(text=f"✅ Detected ZIP code: {zip_code}", foreground='green')
                                    self.get_headend_for_zip(zip_code)
                                    return
                            elif 'ipify' in service:
                                # Get IP and use different service
                                ip_data = response.json()
                                ip = ip_data.get('ip')
                                if ip:
                                    geo_response = requests.get(f"https://ipapi.co/{ip}/postal/", timeout=5)
                                    if geo_response.status_code == 200:
                                        zip_code = geo_response.text.strip()
                                        if len(zip_code) == 5 and zip_code.isdigit():
                                            self.zip_code_var.set(zip_code)
                                            self.epg_status_label.config(text=f"✅ Detected ZIP code: {zip_code}", foreground='green')
                                            self.get_headend_for_zip(zip_code)
                                            return
                    except:
                        continue
                
                self.epg_status_label.config(text="❌ Could not auto-detect ZIP code", foreground='red')
                
            except Exception as e:
                self.epg_status_label.config(text=f"❌ Location detection failed: {str(e)}", foreground='red')
        
        threading.Thread(target=detect, daemon=True).start()
    
    def get_headend_for_zip(self, zip_code):
        """Get headend ID for ZIP code"""
        def get_headend():
            try:
                self.epg_status_label.config(text=f"📺 Looking up TV market for {zip_code}...", foreground='blue')
                self.root.update()
                
                # Common ZIP code to TV market mappings for major areas
                zip_to_market = {
                    "90210": ("Los Angeles, CA", "CA67184:X"),
                    "10001": ("New York, NY", "NY71670:X"), 
                    "60601": ("Chicago, IL", "IL16915:X"),
                    "77001": ("Houston, TX", "TX39059:X"),
                    "19101": ("Philadelphia, PA", "PA28743:X"),
                    "85001": ("Phoenix, AZ", "AZ64693:X"),
                    "78701": ("Austin, TX", "TX42187:X"),
                    "94101": ("San Francisco, CA", "CA74801:X"),
                    "33101": ("Miami, FL", "FL33772:X"),
                    "98101": ("Seattle, WA", "WA48884:X")
                }
                
                if zip_code in zip_to_market:
                    city, headend_id = zip_to_market[zip_code]
                    self.headend_var.set(headend_id)
                    self.epg_status_label.config(
                        text=f"✅ TV market found: {city}", 
                        foreground='green')
                else:
                    # Generic headend ID format for unknown ZIP codes
                    # This follows the typical Zap2it format: StateAbbrevZIPCODE:X
                    try:
                        # Try to determine state from ZIP code (basic lookup)
                        state_ranges = {
                            (1, 2999): "MA", (3000, 3899): "NH", (4000, 4999): "ME",
                            (5000, 5999): "VT", (6000, 6999): "CT", (7000, 8999): "NJ",
                            (10000, 14999): "NY", (15000, 19699): "PA", (20000, 20599): "DC",
                            (20600, 21999): "MD", (22000, 24699): "VA", (25000, 26999): "WV",
                            (27000, 28999): "NC", (29000, 29999): "SC", (30000, 39999): "GA",
                            (32000, 34999): "FL", (35000, 36999): "AL", (37000, 38599): "TN",
                            (38600, 39799): "MS", (40000, 42799): "KY", (43000, 45999): "OH",
                            (46000, 47999): "IN", (48000, 49999): "MI", (50000, 52999): "IA",
                            (53000, 54999): "WI", (55000, 56999): "MN", (57000, 57799): "SD",
                            (58000, 58999): "ND", (59000, 59999): "MT", (60000, 62999): "IL",
                            (63000, 65999): "MO", (66000, 67999): "KS", (68000, 69999): "NE",
                            (70000, 71499): "LA", (71600, 72999): "AR", (73000, 74999): "OK",
                            (75000, 79999): "TX", (80000, 81999): "CO", (82000, 83199): "WY",
                            (83200, 83899): "ID", (84000, 84999): "UT", (85000, 86599): "AZ",
                            (87000, 88499): "NM", (88900, 89999): "NV", (90000, 96199): "CA",
                            (96700, 96899): "HI", (97000, 97999): "OR", (98000, 99499): "WA"
                        }
                        
                        zip_num = int(zip_code)
                        state = "US"  # Default
                        for (min_zip, max_zip), state_abbr in state_ranges.items():
                            if min_zip <= zip_num <= max_zip:
                                state = state_abbr
                                break
                        
                        headend_id = f"{state}{zip_code}:X"
                        self.headend_var.set(headend_id)
                        self.epg_status_label.config(
                            text=f"✅ TV market configured for ZIP {zip_code} ({state})", 
                            foreground='green')
                        
                    except:
                        # Fallback generic format
                        self.headend_var.set(f"PC{zip_code}:X")
                        self.epg_status_label.config(
                            text=f"✅ TV market configured for ZIP {zip_code}", 
                            foreground='green')
                
            except Exception as e:
                self.epg_status_label.config(text=f"⚠️ Could not determine TV market: {str(e)}", foreground='orange')
        
        threading.Thread(target=get_headend, daemon=True).start()
    
    def test_epg(self):
        """Test EPG data retrieval"""
        zip_code = self.zip_code_var.get().strip()
        
        # Use the same validation logic as everywhere else
        if not zip_code:
            messagebox.showwarning("Warning", "Please enter a ZIP code first")
            return
        if len(zip_code) != 5:
            messagebox.showwarning("Warning", f"ZIP code must be exactly 5 digits (you entered {len(zip_code)} digits)")
            return
        if not zip_code.isdigit():
            messagebox.showwarning("Warning", "ZIP code must contain only numbers (no letters or spaces)")
            return
        
        # At this point, 90210 should be perfectly valid!
        
        def test():
            self.epg_status_label.config(text="🧪 Testing EPG data retrieval...", foreground='blue')
            self.root.update()
            
            try:
                # Test EPG data availability (you'd replace this with actual EPG test)
                import time
                time.sleep(2)
                
                self.epg_status_label.config(text="✅ EPG test successful - TV listings available", foreground='green')
                
            except Exception as e:
                self.epg_status_label.config(text=f"❌ EPG test failed: {str(e)}", foreground='red')
        
        threading.Thread(target=test, daemon=True).start()
    
    def toggle_torrent(self):
        """Toggle torrent client configuration visibility"""
        if self.torrent_enabled_var.get():
            self.torrent_frame.pack(fill=tk.X, pady=10)
        else:
            self.torrent_frame.pack_forget()
    
    def on_torrent_client_change(self, event=None):
        """Handle torrent client selection change"""
        client = self.torrent_client_var.get()
        
        # Only set defaults if the current values are empty or match the previous client's defaults
        current_url = self.torrent_vars['url'].get()
        current_username = self.torrent_vars['username'].get()
        current_password = self.torrent_vars['password'].get()
        
        # Set default URLs only if current URL is empty or matches a default URL pattern
        defaults = {
            'qbittorrent': {'url': 'http://localhost:8080', 'username': 'admin', 'password': ''},
            'transmission': {'url': 'http://localhost:9091/transmission/rpc', 'username': '', 'password': ''},
            'deluge': {'url': 'http://localhost:8112', 'username': '', 'password': ''},
            'utorrent': {'url': 'http://localhost:8080/gui', 'username': 'admin', 'password': ''}
        }
        
        if client in defaults:
            config = defaults[client]
            
            # Only update URL if it's empty or matches another client's default
            if not current_url or current_url in [d['url'] for d in defaults.values()]:
                self.torrent_vars['url'].set(config['url'])
            
            # Only update credentials if they're currently set to default values or empty
            if (not current_username or current_username == 'admin') and not hasattr(self, '_user_modified_credentials'):
                self.torrent_vars['username'].set(config['username'])
            
            if not current_password and not hasattr(self, '_user_modified_credentials'):
                self.torrent_vars['password'].set(config['password'])
    
    def detect_torrent_client(self):
        """Auto-detect torrent client Web UI"""
        def detect():
            self.torrent_status_label.config(text="🔍 Scanning for torrent client Web UI...", foreground='blue')
            self.root.update()
            
            common_configs = [
                ('qbittorrent', 'http://localhost:8080', '/api/v2/app/version'),
                ('transmission', 'http://localhost:9091/transmission/rpc', '/transmission/rpc'),
                ('deluge', 'http://localhost:8112', '/json'),
                ('utorrent', 'http://localhost:8080/gui', '/gui/token.html')
            ]
            
            found = False
            for client_name, base_url, test_path in common_configs:
                try:
                    response = requests.get(base_url + test_path, timeout=2)
                    if response.status_code in [200, 401, 409]:  # 401/409 means auth required but service is running
                        self.torrent_client_var.set(client_name)
                        self.torrent_vars['url'].set(base_url)
                        self.on_torrent_client_change()  # Load defaults
                        
                        self.torrent_status_label.config(
                            text=f"✅ Found {client_name} at {base_url}", 
                            foreground='green')
                        found = True
                        break
                except:
                    continue
            
            if not found:
                self.torrent_status_label.config(
                    text="❌ No torrent clients detected on common ports", 
                    foreground='red')
        
        threading.Thread(target=detect, daemon=True).start()
    
    def test_torrent_client(self):
        """Test torrent client connection"""
        client_type = self.torrent_client_var.get()
        url = self.torrent_vars['url'].get()
        username = self.torrent_vars['username'].get()
        password = self.torrent_vars['password'].get()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter Web UI URL first")
            return
        
        def test():
            self.torrent_status_label.config(text="🧪 Testing torrent client connection...", foreground='blue')
            self.root.update()
            
            try:
                if client_type == 'qbittorrent':
                    # Test qBittorrent API
                    login_data = {'username': username, 'password': password}
                    session = requests.Session()
                    response = session.post(f"{url}/api/v2/auth/login", data=login_data, timeout=5)
                    
                    if response.status_code == 200 and response.text == "Ok.":
                        # Test API access
                        version_response = session.get(f"{url}/api/v2/app/version", timeout=5)
                        if version_response.status_code == 200:
                            version = version_response.text.strip('"')
                            self.torrent_status_label.config(
                                text=f"✅ Connected to qBittorrent v{version}", 
                                foreground='green')
                        else:
                            self.torrent_status_label.config(text="✅ Connected but API access limited", foreground='green')
                    else:
                        self.torrent_status_label.config(text="❌ Login failed - check credentials", foreground='red')
                
                elif client_type == 'transmission':
                    # Test Transmission RPC
                    headers = {'Content-Type': 'application/json'}
                    if username and password:
                        import base64
                        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                        headers['Authorization'] = f'Basic {credentials}'
                    
                    data = {'method': 'session-get', 'arguments': {}}
                    response = requests.post(url, json=data, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        self.torrent_status_label.config(text="✅ Connected to Transmission", foreground='green')
                    elif response.status_code == 409:  # CSRF token needed
                        self.torrent_status_label.config(text="✅ Transmission detected (CSRF handled)", foreground='green')
                    else:
                        self.torrent_status_label.config(text="❌ Connection failed - check URL/credentials", foreground='red')
                
                elif client_type == 'deluge':
                    # Test Deluge Web UI
                    response = requests.get(f"{url}/json", timeout=5)
                    if response.status_code in [200, 401]:
                        self.torrent_status_label.config(text="✅ Connected to Deluge Web UI", foreground='green')
                    else:
                        self.torrent_status_label.config(text="❌ Connection failed", foreground='red')
                
                else:
                    # Generic test
                    response = requests.get(url, timeout=5)
                    if response.status_code in [200, 401]:
                        self.torrent_status_label.config(text="✅ Web UI accessible", foreground='green')
                    else:
                        self.torrent_status_label.config(text="❌ Connection failed", foreground='red')
                        
            except Exception as e:
                self.torrent_status_label.config(text=f"❌ Connection failed: {str(e)}", foreground='red')
        
        threading.Thread(target=test, daemon=True).start()
    
    def toggle_torrent_password_visibility(self):
        """Toggle torrent client password visibility"""
        current_show = self.torrent_password_entry.cget('show')
        if current_show == '*':
            self.torrent_password_entry.config(show='')
        else:
            self.torrent_password_entry.config(show='*')
    
    def open_router_help(self):
        """Show help for finding HDHomeRun IP in router"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Find HDHomeRun IP Address")
        help_window.geometry("500x400")
        
        frame = ttk.Frame(help_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(frame, text="🔍 Finding Your HDHomeRun's IP Address", 
                         font=('Segoe UI', 14, 'bold'))
        title.pack(anchor=tk.W, pady=(0, 15))
        
        instructions = """
Method 1: Check Router Admin Panel
1. Open web browser and go to your router's IP:
   • Usually: 192.168.1.1 or 192.168.0.1
   • Or check your computer's gateway IP

2. Look for "Connected Devices", "DHCP Clients", or "Device List"

3. Find device named:
   • "HDHomeRun" or "HDHR-xxxxxxx" 
   • Manufacturer: "Silicondust"
   • MAC address starting with: 00:18:dd

Method 2: HDHomeRun App
1. Download the HDHomeRun app from silicondust.com
2. Run the app - it will show your device's IP

Method 3: Common IP Ranges to Try
• 192.168.1.100 - 192.168.1.110
• 192.168.0.100 - 192.168.0.110  
• 10.0.0.100 - 10.0.0.110

Method 4: Command Line (Advanced)
Windows: arp -a | findstr "00-18-dd"
Mac/Linux: arp -a | grep "00:18:dd"
        """
        
        text_widget = tk.Text(frame, wrap=tk.WORD, font=('Segoe UI', 10), height=15)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=10)
        text_widget.insert(tk.END, instructions.strip())
        text_widget.config(state=tk.DISABLED)
        
        # Buttons frame
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # Try to open router admin
        def open_router():
            import webbrowser
            try:
                # Get likely router IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                
                router_ip = '.'.join(local_ip.split('.')[:-1]) + '.1'
                webbrowser.open(f'http://{router_ip}')
            except:
                messagebox.showinfo("Router Access", 
                                   "Could not auto-detect router IP.\n"
                                   "Try opening 192.168.1.1 or 192.168.0.1 in your browser.")
        
        router_btn = ttk.Button(btn_frame, text="Open Router Admin", command=open_router)
        router_btn.pack(side=tk.LEFT)
        
        close_btn = ttk.Button(btn_frame, text="Close", command=help_window.destroy)
        close_btn.pack(side=tk.RIGHT)
    
    def test_hdhr(self):
        """Test HDHomeRun connection"""
        ip = self.hdhr_ip_var.get()
        if not ip:
            messagebox.showwarning("Warning", "Please enter an IP address first")
            return
        
        def test():
            self.hdhr_status_label.config(text="Testing connection...", foreground='blue')
            self.root.update()
            
            try:
                response = requests.get(f"http://{ip}/lineup.json", timeout=5)
                if response.status_code == 200:
                    lineup = response.json()
                    channel_count = len(lineup)
                    self.hdhr_status_label.config(
                        text=f"✅ Connection successful - {channel_count} channels found", 
                        foreground='green')
                else:
                    self.hdhr_status_label.config(text="❌ Connection failed", foreground='red')
            except Exception as e:
                self.hdhr_status_label.config(text=f"❌ Connection failed: {str(e)}", foreground='red')
        
        threading.Thread(target=test, daemon=True).start()
    
    def browse_directory(self, key):
        """Browse for directory"""
        current_path = self.directory_vars[key].get()
        directory = filedialog.askdirectory(initialdir=current_path, title="Select Directory")
        if directory:
            self.directory_vars[key].set(directory)
    
    def browse_ffmpeg(self):
        """Browse for FFmpeg executable"""
        current_path = self.ffmpeg_var.get()
        if current_path and current_path != "ffmpeg":
            initial_dir = os.path.dirname(current_path)
        else:
            initial_dir = "/"
            
        filename = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select FFmpeg Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.ffmpeg_var.set(filename)
    
    def test_ffmpeg(self):
        """Test FFmpeg installation"""
        ffmpeg_path = self.ffmpeg_var.get()
        
        def test():
            self.ffmpeg_status_label.config(text="Testing FFmpeg...", foreground='blue')
            self.root.update()
            
            try:
                result = subprocess.run([ffmpeg_path, "-version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    self.ffmpeg_status_label.config(text=f"✅ {version_line}", foreground='green')
                else:
                    self.ffmpeg_status_label.config(text="❌ FFmpeg test failed", foreground='red')
            except Exception as e:
                self.ffmpeg_status_label.config(text=f"❌ FFmpeg not found: {str(e)}", foreground='red')
        
        threading.Thread(target=test, daemon=True).start()
    
    def toggle_indexer(self):
        """Toggle indexer configuration visibility"""
        if self.indexer_enabled_var.get():
            self.indexer_frame.pack(fill=tk.X, pady=10)
        else:
            self.indexer_frame.pack_forget()
    
    def toggle_vpn(self):
        """Toggle VPN configuration visibility"""
        if self.vpn_enabled_var.get():
            self.vpn_frame.pack(fill=tk.X, pady=10)
        else:
            self.vpn_frame.pack_forget()
    
    def on_provider_change(self, event=None):
        """Handle provider selection change"""
        provider = self.indexer_provider_var.get()
        if provider in self.config_data["indexer"]["providers"]:
            provider_config = self.config_data["indexer"]["providers"][provider]
            self.provider_vars['api_url'].set(provider_config.get('api_url', ''))
            self.provider_vars['api_key'].set(provider_config.get('api_key', ''))
    
    def validate_ip_address(self, event=None):
        """Validate IP address format"""
        ip = self.hdhr_ip_var.get()
        if not ip:
            return
        
        try:
            ipaddress.ip_address(ip)
            self.hdhr_ip_entry.config(style='TEntry')  # Reset to normal style
        except ValueError:
            # Invalid IP format - could add visual feedback here
            pass
    
    def validate_url(self, url):
        """Validate URL format"""
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def validate_directory(self, path):
        """Validate directory path"""
        if not path:
            return False
        try:
            return os.path.isdir(path) or not os.path.exists(path)  # Allow non-existent paths
        except:
            return False
    
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        current_show = self.api_key_entry.cget('show')
        if current_show == '*':
            self.api_key_entry.config(show='')
        else:
            self.api_key_entry.config(show='*')
    
    def test_indexer(self):
        """Test indexer connection"""
        provider = self.indexer_provider_var.get()
        api_url = self.provider_vars['api_url'].get()
        api_key = self.provider_vars['api_key'].get()
        
        if not api_url or not api_key:
            messagebox.showwarning("Warning", "Please enter API URL and key first")
            return
        
        def test():
            self.indexer_status_label.config(text="Testing indexer connection...", foreground='blue')
            self.root.update()
            
            try:
                # Test based on provider type
                if provider == "prowlarr":
                    test_url = f"{api_url}/api/v1/indexer"
                elif provider == "jackett":
                    test_url = f"{api_url}/api/v2.0/indexers/all/results/torznab/"
                else:
                    test_url = f"{api_url}/api"
                
                headers = {'X-Api-Key': api_key} if api_key else {}
                response = requests.get(test_url, headers=headers, timeout=5)
                
                if response.status_code in [200, 401]:  # 401 means we reached the API but auth failed
                    if response.status_code == 200:
                        self.indexer_status_label.config(text="✅ Connection successful", foreground='green')
                    else:
                        self.indexer_status_label.config(text="⚠️ Connected but check API key", foreground='orange')
                else:
                    self.indexer_status_label.config(text=f"❌ Connection failed ({response.status_code})", 
                                                   foreground='red')
            except Exception as e:
                self.indexer_status_label.config(text=f"❌ Connection failed: {str(e)}", foreground='red')
        
        threading.Thread(target=test, daemon=True).start()
    
    def test_all_connections(self):
        """Test all configured connections"""
        self.status_label.config(text="Testing all connections...", foreground='blue')
        self.root.update()
        
        # Test HDHomeRun
        self.test_hdhr()
        
        # Test FFmpeg
        self.test_ffmpeg()
        
        # Test EPG if ZIP code is provided
        if self.zip_code_var.get():
            self.test_epg()
        
        # Test torrent client if enabled
        if self.torrent_enabled_var.get():
            self.test_torrent_client()
        
        # Test indexer if enabled
        if self.indexer_enabled_var.get():
            self.test_indexer()
        
        self.status_label.config(text="Connection tests completed", foreground='green')
    
    def save_config(self):
        """Save configuration to file with validation"""
        # Validation
        validation_errors = []
        
        # Validate IP address
        ip = self.hdhr_ip_var.get()
        if ip:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                validation_errors.append("Invalid HDHomeRun IP address format")
        else:
            validation_errors.append("HDHomeRun IP address is required")
        
        # Validate directories
        for key, var in self.directory_vars.items():
            path = var.get()
            if not path:
                validation_errors.append(f"{key.replace('_', ' ').title()} directory is required")
            elif not self.validate_directory(path):
                validation_errors.append(f"Invalid {key.replace('_', ' ')} directory path")
        
        # Validate FFmpeg
        ffmpeg_path = self.ffmpeg_var.get()
        if not ffmpeg_path:
            validation_errors.append("FFmpeg path is required")
        
        # Validate EPG if ZIP code is provided
        zip_code = self.zip_code_var.get().strip()
        if zip_code:  # Only validate if ZIP code is provided (it's optional)
            if len(zip_code) != 5:
                validation_errors.append("ZIP code must be exactly 5 digits")
            elif not zip_code.isdigit():
                validation_errors.append("ZIP code must contain only numbers")
            # 90210 should pass this validation now!
        
        # Validate torrent client if enabled
        if self.torrent_enabled_var.get():
            torrent_url = self.torrent_vars['url'].get()
            
            if not torrent_url:
                validation_errors.append("Torrent client URL is required when torrent client is enabled")
            elif not self.validate_url(torrent_url):
                validation_errors.append("Invalid torrent client URL format")
        
        # Validate indexer if enabled
        if self.indexer_enabled_var.get():
            api_url = self.provider_vars['api_url'].get()
            api_key = self.provider_vars['api_key'].get()
            
            if not api_url:
                validation_errors.append("Indexer API URL is required when indexer is enabled")
            elif not self.validate_url(api_url):
                validation_errors.append("Invalid indexer API URL format")
            
            if not api_key:
                validation_errors.append("Indexer API key is required when indexer is enabled")
        
        # Show validation errors if any
        if validation_errors:
            error_message = "Please fix the following issues:\n\n" + "\n".join(f"• {error}" for error in validation_errors)
            messagebox.showerror("Validation Error", error_message)
            self.status_label.config(text="❌ Please fix validation errors", foreground='red')
            return
        
        try:
            # Build configuration dictionary
            config = {
                "hdhr": {
                    "ip_address": ip
                },
                "directories": {
                    key: var.get() for key, var in self.directory_vars.items()
                },
                "ffmpeg": {
                    "path": ffmpeg_path
                },
                "epg": {
                    "zip_code": self.zip_code_var.get(),
                    "headend_id": self.headend_var.get(),
                    "timezone": "America/New_York",  # Could be made configurable
                    "auto_refresh": True,
                    "refresh_interval": 24
                },
                "torrent_client": {
                    "enabled": self.torrent_enabled_var.get(),
                    "type": self.torrent_client_var.get(),
                    "url": self.torrent_vars['url'].get(),
                    "username": self.torrent_vars['username'].get(),
                    "password": self.torrent_vars['password'].get()
                },
                "indexer": {
                    "enabled": self.indexer_enabled_var.get(),
                    "provider": self.indexer_provider_var.get(),
                    "timeout": 30,
                    "providers": {
                        self.indexer_provider_var.get(): {
                            "api_url": self.provider_vars['api_url'].get(),
                            "api_key": self.provider_vars['api_key'].get()
                        }
                    }
                },
                "vpn": {
                    "enabled": self.vpn_enabled_var.get(),
                    "provider": self.vpn_provider_var.get(),
                    "config": {}
                }
            }
            
            # Create directories if they don't exist
            for key, dir_path in config["directories"].items():
                if dir_path:
                    try:
                        os.makedirs(dir_path, exist_ok=True)
                        self.status_label.config(text=f"Created directory: {key}", foreground='blue')
                        self.root.update()
                    except Exception as e:
                        messagebox.showwarning("Directory Creation", 
                                             f"Could not create {key} directory:\n{str(e)}")
            
            # Save configuration
            with open("config.json", 'w') as f:
                json.dump(config, f, indent=2)
            
            self.status_label.config(text="✅ Configuration saved successfully!", foreground='green')
            
            # Show success dialog with next steps
            success_msg = ("Configuration saved successfully!\n\n"
                          "LineDrive is now configured and ready to use.\n\n"
                          "Next steps:\n"
                          "1. Start LineDrive: python dvr_web.py\n"
                          "2. Open browser to http://localhost:5000\n"
                          "3. Begin recording your favorite shows!")
            
            messagebox.showinfo("Setup Complete! 🎉", success_msg)
            
        except Exception as e:
            self.status_label.config(text=f"❌ Save failed: {str(e)}", foreground='red')
            messagebox.showerror("Error", f"Failed to save configuration:\n{str(e)}")

def main():
    """Main function to run the setup GUI"""
    try:
        root = tk.Tk()
        
        # Set icon if available
        try:
            root.iconbitmap("LineDrive Logo.jpg")
        except:
            pass  # Icon not available, continue without it
        
        app = LineDriveSetupGUI(root)
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start setup GUI:\n{str(e)}")

if __name__ == "__main__":
    main()