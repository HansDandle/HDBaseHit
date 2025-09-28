# Contributing to LineDrive

Thank you for your interest in contributing to LineDrive! This document provides guidelines for contributing to the project.

## Getting Started

### Development Environment

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/HansDandle/LineDrive.git
   cd LineDrive
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the setup wizard** to configure for testing:
   ```bash
   python setup.py
   ```

### Running the Application

- **Web Interface**: `python dvr_web.py`
- **GUI Application**: `python Recordtv.py`
- **Configuration Menu**: `python config_menu.py`

## How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Include detailed information**:
   - Operating system and version
   - Python version
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages or logs
   - Configuration details (remove sensitive info)

### Suggesting Features

1. **Check existing feature requests** first
2. **Use the feature request template**
3. **Describe the problem** your feature would solve
4. **Provide detailed specifications** for the proposed solution
5. **Consider implementation complexity** and user impact

### Code Contributions

#### Before You Start

1. **Create an issue** to discuss major changes
2. **Check the roadmap** to align with project direction
3. **Review existing code** to understand patterns and conventions

#### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation as needed
   - Add tests if applicable

3. **Test your changes**:
   - Run the application with your changes
   - Test different configuration scenarios
   - Verify no existing functionality is broken

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Use the PR template
   - Link related issues
   - Describe changes in detail
   - Include testing instructions

#### Commit Message Guidelines

Use conventional commit format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Formatting, no code change
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

Examples:
- `feat: add automatic EPG refresh scheduling`
- `fix: resolve HDHomeRun connection timeout`
- `docs: update installation instructions`

### Code Style Guidelines

#### Python Code Style

- **Follow PEP 8** with some exceptions:
  - Line length: 100 characters (not 79)
  - Use double quotes for strings
  - Use type hints where appropriate

- **Naming conventions**:
  - Functions: `snake_case`
  - Variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`

- **Documentation**:
  - Use docstrings for all functions and classes
  - Include parameter and return type descriptions
  - Add inline comments for complex logic

#### Example Code Structure

```python
def record_channel(channel: str, duration_minutes: int, quality: str = "medium") -> bool:
    """Record a TV channel for specified duration.
    
    Args:
        channel: HDHomeRun channel identifier (e.g., "2.1")
        duration_minutes: Recording duration in minutes
        quality: Recording quality setting ("low", "medium", "high")
        
    Returns:
        True if recording started successfully, False otherwise
        
    Raises:
        ValueError: If channel format is invalid
        ConnectionError: If HDHomeRun device is unreachable
    """
    # Implementation here
    pass
```

#### Configuration Management

- **Always use the config system** for user settings
- **Never hardcode** paths, IPs, or credentials
- **Provide sensible defaults** in config templates
- **Document new config options** in README and templates

#### Error Handling

- **Use try-catch blocks** for external operations
- **Provide meaningful error messages** to users
- **Log detailed errors** for debugging
- **Fail gracefully** when possible

### Testing

#### Manual Testing

Test your changes with different scenarios:

1. **Fresh installation** (new user experience)
2. **Existing configuration** (upgrade scenarios)
3. **Different platforms** (Windows/Linux/macOS if possible)
4. **Various HDHomeRun models** if available
5. **Network connectivity issues** (timeouts, unreachable devices)

#### Integration Testing

- Test with real HDHomeRun devices when possible
- Verify EPG data fetching and parsing
- Test recording functionality end-to-end
- Check web interface responsiveness

### Documentation

#### Code Documentation

- **Update docstrings** for modified functions
- **Add comments** for complex algorithms
- **Document configuration options** in config templates

#### User Documentation

- **Update README.md** for new features
- **Add troubleshooting entries** for known issues
- **Include setup instructions** for new dependencies
- **Update API documentation** for endpoint changes

### Security Considerations

#### Sensitive Data

- **Never commit** API keys, passwords, or personal paths
- **Use environment variables** or config files for secrets
- **Sanitize user input** in web interfaces
- **Validate file paths** to prevent directory traversal

#### Network Security

- **Validate external URLs** before making requests
- **Use timeouts** for all network operations
- **Handle SSL/TLS properly** for secure connections

### Performance Guidelines

- **Minimize resource usage** for background operations
- **Use threading carefully** to avoid race conditions
- **Cache frequently accessed data** when appropriate
- **Optimize database/file I/O** operations

### Platform Compatibility

#### Windows
- Use `os.path.join()` or `pathlib.Path` for file paths
- Handle Windows service integration properly
- Test with Windows-specific features

#### Linux/macOS
- Ensure file permissions are handled correctly
- Test daemon/service functionality
- Handle case-sensitive file systems

### Release Process

#### Version Numbering

We use Semantic Versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes (backward compatible)

#### Release Checklist

1. Update version numbers in relevant files
2. Update CHANGELOG.md with new features and fixes
3. Test installation and upgrade procedures
4. Update documentation for new features
5. Create release notes
6. Tag the release in Git

### Community Guidelines

#### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Acknowledge contributions from others

#### Communication

- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code discussions and reviews
- **Discussions**: General questions and ideas

### Getting Help

If you need help contributing:

1. **Check the documentation** first
2. **Search existing issues** for similar questions
3. **Create a new discussion** for general questions
4. **Join our community** channels (if available)

### Recognition

Contributors are recognized in:
- GitHub contributor lists
- Release notes
- Project documentation
- Special thanks in major releases

Thank you for contributing to LineDrive!