"""
LinkedIn Job Scraper Configuration
Application-wide configuration settings
"""

import os
from pathlib import Path

# Application Information
APP_NAME = "LinkedIn Job Scraper"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Job Scraper Tools"

# Project Paths
PROJECT_ROOT = Path(__file__).parent
UI_DIR = PROJECT_ROOT / "ui"
SCRAPING_DIR = PROJECT_ROOT / "scraping"
DATA_DIR = PROJECT_ROOT / "data"
UTILITIES_DIR = PROJECT_ROOT / "utilities"

# Application Settings
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 1024
MIN_WINDOW_HEIGHT = 768

# Scraping Configuration
DEFAULT_REQUEST_DELAY = 3  # seconds between requests
MAX_REQUEST_DELAY = 5      # maximum delay for randomization
PAGE_LOAD_TIMEOUT = 30     # seconds to wait for page load
MAX_RETRY_ATTEMPTS = 3     # number of retry attempts for failed requests

# LinkedIn URLs
LINKEDIN_JOBS_BASE_URL = "https://www.linkedin.com/jobs/search"

# User Agent Strings
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Export Settings
DEFAULT_EXPORT_FORMAT = "csv"
CSV_DELIMITER = ","
CSV_ENCODING = "utf-8"

# UI Color Scheme (LinkedIn-inspired)
COLORS = {
    'primary': '#0077B5',      # LinkedIn Blue
    'secondary': '#FFFFFF',    # White
    'accent': '#00A0DC',       # Light Blue
    'text': '#2D2D2D',         # Dark Gray
    'success': '#057642',      # Green
    'warning': '#F5A623',      # Orange
    'error': '#D0021B',        # Red
    'background': '#F3F2EF',   # Light Gray
    'border': '#E0E0E0'        # Border Gray
}

# Job Status Options
JOB_STATUS_OPTIONS = [
    "Not Reviewed",
    "Interested", 
    "Applied",
    "Not Interested"
]

# Filter Options
JOB_TYPE_OPTIONS = [
    "All",
    "Full-time",
    "Part-time", 
    "Contract",
    "Internship"
]

EXPERIENCE_LEVEL_OPTIONS = [
    "All",
    "Entry Level",
    "Mid Level",
    "Senior Level", 
    "Executive"
]