# Changelog

All notable changes to TV Recorder for HDHomeRun will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial public release
- Configuration management system with user-friendly setup
- Interactive setup wizard (`setup.py`)
- Configuration menu system (`config_menu.py`)
- Comprehensive documentation and contributing guidelines
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