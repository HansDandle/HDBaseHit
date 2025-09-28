# LineDrive - TV Recording Software

<p align="center">
  <img src="LineDrive Logo.jpg" alt="LineDrive Logo" width="200">
</p>

A comprehensive TV recording solution for HDHomeRun network tuners with web interface, scheduling, and indexer integration.

## Trademark Notice

**LineDrive** is an independent, open-source project and is not affiliated with, endorsed by, or sponsored by Silicondust USA Inc. **HDHomeRun** is a registered trademark of Silicondust USA Inc. This software is designed to work with HDHomeRun devices but is not an official product of Silicondust USA Inc.

📋 **[Complete Trademark Notices & Legal Disclaimers](TRADEMARK_NOTICE.md)**

## Features

- **Live TV Recording**: Record from HDHomeRun network tuners
- **Web Interface**: Modern, responsive web UI for managing recordings
- **Smart Scheduling**: Schedule recordings with recurring series support
- **EPG Integration**: Electronic Program Guide support via Zap2it (configurable by zip code)
- **VPN Support**: Generic VPN integration (NordVPN, ExpressVPN, ProtonVPN, Surfshark, custom)
- **Indexer Integration**: Support for multiple torrent/usenet indexers (Prowlarr, Jackett, Torznab)
- **Multi-format Support**: Record in MP4 or TS formats
- **Background Service**: Run as Windows service for always-on operation
- **Mobile-Friendly**: Progressive Web App (PWA) support

## Quick Start

### Prerequisites

- **HDHomeRun** network tuner device
- **Python 3.7+** installed on your system
- **FFmpeg** for video processing
- **Windows** (primary support) or Linux/macOS (experimental)

### Installation

1. **Download the latest release** or clone this repository:
   ```bash
   git clone https://github.com/HansDandle/LineDrive.git
   cd LineDrive
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the setup wizard**:
   ```bash
   python setup.py
   ```
   
   The setup wizard will help you:
   - Find your HDHomeRun device
   - Configure recording directories
   - Set up FFmpeg
   - Configure optional integrations

4. **Start the application**:
   ```bash
   python dvr_web.py
   ```

5. **Open your browser** to `http://localhost:5000`

## Configuration

### First-Time Setup

Run the interactive setup wizard:
```bash
python setup.py
```

This will create a `config.json` file with your settings.

### ⚠️ Important: Replace Placeholder Values

LineDrive includes placeholder values that **must be customized** for your setup:

- **API Keys**: Replace `your_prowlarr_api_key_here` with your actual Prowlarr API key
- **IP Addresses**: Replace `YOUR_PC_IP_HERE` with your computer's actual IP address  
- **Network Settings**: Update HDHomeRun IP and other network configurations

Use the **Settings (⚙️) button** in the web interface or run the setup wizard to configure these values.

### Manual Configuration

You can also manually edit the `config.json` file or use the built-in configuration menu:

```bash
python config_menu.py
```

### Configuration Options

The configuration file (`config.json`) contains the following sections:

#### HDHomeRun Settings
```json
{
  "hdhr": {
    "ip_address": "192.168.1.100",
    "comment": "IP address of your HDHomeRun tuner device"
  }
}
```

#### Directory Settings
```json
{
  "directories": {
    "recordings": "~/TV_Recordings",
    "tv_shows": "~/TV Shows",
    "movies": "~/Movies",
    "comment": "Directory paths for storing recordings and media"
  }
}
```

#### FFmpeg Settings
```json
{
  "ffmpeg": {
    "path": "ffmpeg",
    "comment": "Path to ffmpeg executable"
  }
}
```

#### EPG (Electronic Program Guide) Settings
```json
{
  "epg": {
    "zip_code": "78748",
    "headend_id": "",
    "timezone": "America/Chicago",
    "auto_refresh": false,
    "refresh_hours": [6, 14, 22],
    "comment": "TV listings configuration. zip_code determines your TV market area."
  }
}
```

**Important**: Your zip code determines which TV stations and program schedules are available. The setup wizard will auto-detect your headend ID based on your zip code.

#### VPN Settings (Optional)
```json
{
  "vpn": {
    "enabled": false,
    "provider": "nordvpn",
    "auto_connect": false,
    "required_for_torrents": true,
    "disconnect_on_exit": false,
    "connection_check_url": "https://ipinfo.io/json",
    "comment": "VPN configuration for secure connections"
  }
}
```

**Supported VPN Providers**:
- **nordvpn**: NordVPN (uses `nordvpn` CLI)
- **expressvpn**: ExpressVPN (uses `expressvpn` CLI)  
- **protonvpn**: ProtonVPN (uses `protonvpn-cli`)
- **surfshark**: Surfshark (uses `surfshark` CLI)
- **generic**: Custom provider (requires manual command configuration)

**VPN Options**:
- `enabled`: Enable/disable VPN integration
- `provider`: Which VPN service to use
- `auto_connect`: Automatically connect VPN when needed
- `required_for_torrents`: Require VPN for torrent operations
- `disconnect_on_exit`: Disconnect VPN when application exits

#### Indexer Integration (Optional)
```json
{
  "indexer": {
    "enabled": false,
    "provider": "prowlarr",
    "timeout": 30,
    "comment": "Torrent/Usenet indexer configuration",
    "providers": {
      "prowlarr": {
        "api_url": "http://127.0.0.1:9696",
        "api_key": "",
        "name": "Prowlarr"
      },
      "jackett": {
        "api_url": "http://127.0.0.1:9117",
        "api_key": "",
        "indexers": "all",
        "name": "Jackett"
      },
      "torznab": {
        "api_url": "",
        "api_key": "",
        "name": "Custom Torznab"
      }
    }
  }
}
```

**Supported Indexer Providers**:
- **prowlarr**: Prowlarr indexer management (recommended)
- **jackett**: Jackett torrent proxy
- **torznab**: Custom Torznab-compatible indexer

**Indexer Options**:
- `enabled`: Enable/disable indexer integration
- `provider`: Which indexer service to use
- `timeout`: API request timeout in seconds
- Provider-specific settings for API URL, key, etc.

## Usage

### Web Interface

Once started, access the web interface at `http://localhost:5000` to:

- **Browse Channels**: View available HDHomeRun channels
- **Schedule Recordings**: Set up one-time or recurring recordings
- **Manage Library**: Browse and organize recorded content
- **Search Content**: Find shows using EPG data and optional indexer integration
- **Monitor System**: View recording status and system health

### GUI Application

For a desktop GUI experience:
```bash
python Recordtv.py
```

### Command Line Operations

#### Recording Commands
```bash
# Record channel 2.1 for 30 minutes
python -c "from dvr_web import record_channel; record_channel('2.1', 30)"

# List available channels
python -c "from dvr_web import get_hdhr_channels; print(get_hdhr_channels())"
```

#### Configuration Management
```bash
# Open configuration menu
python config_menu.py

# Run setup wizard again
python setup.py
```

## Advanced Features

### Windows Service Installation

To run LineDrive as a Windows service:

1. **Install the service**:
   ```cmd
   python dvr_service.py install
   ```

2. **Start the service**:
   ```cmd
   python dvr_service.py start
   ```

3. **Set to auto-start**:
   ```cmd
   sc config TVRecorderDVR start= auto
   ```

### Prowlarr Integration

Prowlarr integration enables torrent-based content discovery:

1. **Install Prowlarr** from [prowlarr.com](https://prowlarr.com)

2. **Configure in LineDrive**:
   ```bash
   python config_menu.py
   # Navigate to Prowlarr Integration
   # Enable and enter your API key
   ```

3. **Benefits**:
   - Search for shows across multiple torrent indexers
   - Automatic quality selection
   - Integration with download clients

### EPG (Electronic Program Guide)

LineDrive supports EPG data via Zap2it:

1. **Configure EPG refresh**:
   - Set `ENABLE_BACKGROUND_EPG_REFRESH=1` environment variable
   - EPG data refreshes automatically in the background

2. **Manual EPG refresh**:
   ```bash
   python epg_zap2it.py
   ```

### Remote Control

Enable remote control via webhook:

1. **Start webhook server**:
   ```bash
   python dvr_remote_webhook.py
   ```

2. **Send commands via HTTP**:
   ```bash
   curl -X POST http://localhost:8080/restart -H "Authorization: Bearer your-secret-token"
   ```

## File Structure

```
LineDrive/
├── dvr_web.py              # Main web application
├── Recordtv.py             # GUI application
├── config_manager.py       # Configuration management
├── config_menu.py          # Interactive configuration
├── setup.py                # Initial setup wizard
├── config_template.json    # Configuration template
├── dvr_service.py          # Windows service wrapper
├── dvr_watchdog.py         # Process monitoring
├── prowlarr_client.py      # Prowlarr integration
├── biratepay_client.py     # Alternative search client
├── epg_zap2it.py          # EPG data fetching
├── web_control.py          # Web API endpoints
├── wake_pc.py              # Wake-on-LAN support
├── static/                 # Web interface assets
├── templates/              # HTML templates
└── requirements.txt        # Python dependencies
```

## API Reference

### REST Endpoints

The web interface exposes a REST API:

#### Recording Control
- `POST /record` - Start recording
- `POST /stop` - Stop current recording
- `GET /status` - Get recording status

#### Channel Management
- `GET /channels` - List available channels
- `GET /lineup` - Get HDHomeRun lineup

#### EPG Data
- `GET /epg` - Get program guide data
- `POST /epg/refresh` - Refresh EPG data

#### Configuration
- `GET /config` - Get current configuration
- `POST /config` - Update configuration

### WebSocket Events

Real-time updates via WebSocket:
- `recording_started` - Recording began
- `recording_stopped` - Recording ended
- `epg_updated` - Program guide refreshed
- `error` - Error occurred

## Troubleshooting

### Common Issues

#### FFmpeg Not Found
```
Error: FFmpeg not found
```
**Solution**: Install FFmpeg and add to PATH, or specify full path in configuration.

#### HDHomeRun Connection Failed
```
Error: Could not connect to HDHomeRun
```
**Solutions**:
- Verify HDHomeRun IP address in configuration
- Check network connectivity
- Ensure HDHomeRun is powered on

#### Permission Denied (Directories)
```
Error: Permission denied creating directory
```
**Solutions**:
- Run as administrator (Windows) or use `sudo` (Linux/macOS)
- Choose directories where you have write permission
- Create directories manually first

#### Port Already in Use
```
Error: Address already in use
```
**Solutions**:
- Change port in web interface configuration
- Stop other applications using the port
- Use `netstat` to identify conflicting applications

### Debug Mode

Enable debug logging:
```bash
# Set debug mode in config
python config_menu.py
# Navigate to Web Interface Settings > Toggle Debug Mode

# Or set environment variable
export DEBUG=1
python dvr_web.py
```

### Log Files

Check log files for detailed error information:
- Application logs: Console output
- Service logs: Windows Event Viewer (if running as service)
- Web server logs: Built into Flask output

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. **Fork the repository**
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\\Scripts\\activate     # Windows
   ```
3. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. **Run tests**:
   ```bash
   python -m pytest
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [HDHomeRun](https://www.silicondust.com/) for network tuner technology
- [FFmpeg](https://ffmpeg.org/) for video processing
- [Prowlarr](https://prowlarr.com/) for indexer management
- [Zap2it](https://www.zap2it.com/) for EPG data

## Legal Disclaimer

**⚠️ IMPORTANT LEGAL NOTICE ⚠️**

This software is intended for **legitimate, legal use only**. Users are responsible for complying with all applicable laws and regulations.

### Permitted Uses
- Recording **over-the-air broadcast television** that you are legally entitled to receive
- Recording content from **your own HDHomeRun tuner device**
- Personal time-shifting of broadcast content for **private, non-commercial use**
- Managing and organizing **your own legally recorded content**

### Prohibited Uses
- **DO NOT** use this software to download, distribute, or share copyrighted materials without permission
- **DO NOT** use torrent integration features to download copyrighted content illegally
- **DO NOT** circumvent copy protection or access controls
- **DO NOT** distribute recorded content beyond personal/household use

### User Responsibility
- **You are solely responsible** for ensuring your use complies with copyright law
- **You are responsible** for understanding and following your local broadcasting and copyright regulations
- **The developers assume no liability** for misuse of this software

### Torrent Integration Notice
The optional Prowlarr integration is provided for legitimate content discovery only. Users must ensure any content accessed through these features complies with applicable copyright laws.

**By using this software, you acknowledge that you understand and will comply with all applicable laws.**\n\n📋 **For detailed legal terms and guidelines, see [LEGAL.md](LEGAL.md)**

## Support

- **Issues**: [GitHub Issues](https://github.com/HansDandle/LineDrive/issues)
- **Documentation**: This README and inline code comments
- **Community**: [Discussions](https://github.com/HansDandle/LineDrive/discussions)

## Roadmap

- [ ] Docker containerization
- [ ] Linux/macOS native packaging
- [ ] Mobile apps (Android/iOS)
- [ ] Cloud storage integration
- [ ] Advanced scheduling rules
- [ ] Multi-tuner management
- [ ] Automated commercial detection
- [ ] Streaming server functionality