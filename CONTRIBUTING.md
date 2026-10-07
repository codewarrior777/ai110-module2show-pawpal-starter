# Contributing to PawPal+

Thanks for your interest in improving PawPal+! This document outlines the
development workflow.

## Development Setup

```bash
# Clone
git clone https://github.com/codewarrior777/PawPal-Plus.git
cd PawPal-Plus

# Create virtualenv
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows

# Install with dev dependencies
pip install -e ".[dev]"
