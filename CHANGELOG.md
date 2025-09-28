# Changelog

All notable changes to LineDrive will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-09-28

### Added
- **LineDrive Branding**: Complete rebrand from "TV Recorder" to "LineDrive"
- **Generic VPN Manager**: Support for NordVPN, ExpressVPN, ProtonVPN, Surfshark, and custom providers
- **Generic Indexer Manager**: Support for Prowlarr, Jackett, and Torznab indexers
- **LineDrive Logo**: Professional logo integration in web interface and documentation
- **Trademark Compliance**: Comprehensive legal notices and disclaimers
- **Interactive Setup Wizards**: User-friendly configuration for VPN and indexer providers
- **Configuration Management**: JSON-based configuration system with templates

### Removed
- **BiratePay Integration**: Removed proprietary system in favor of generic indexer support
- **ProtonVPN Hard-coding**: Replaced with provider-agnostic VPN system
- **Test Files**: Cleaned up unnecessary test files and dependencies

### Changed
- **Repository Name**: Updated from TV_Recorder_pub to LineDrive
- **Configuration Directory**: Changed from `.tv_recorder` to `.linedrive`
- **Web Interface**: Updated branding, added logo, improved legal compliance notices
- **Documentation**: Comprehensive updates for new provider-agnostic architecture

## [1.0.0] - Previous

### Added
- Initial TV recording functionality
- HDHomeRun integration
- Basic web interface
- Support for environment-based configuration
- Automatic directory creation during setup
- HDHomeRun device auto-discovery
- FFmpeg installation validation and auto-detection

### Changed
- Removed all hardcoded API keys, IP addresses, and file paths
- Replaced hardcoded values with configuration system
- Improved error handling and user feedback
- Modernized code structure and organization

### Removed
- All test files (`test_*.py`)
- Debug scripts (`debug_*.py`, `check_*.py`)
- Personal configuration data
- Hardcoded credentials and paths

### Security
- Removed exposed API keys from source code
- Implemented secure configuration management
- Added validation for user input and file paths

## [Previous Versions]

Previous versions of this project were private development builds and are not documented in this changelog. The first public release incorporates all major features developed during private development.