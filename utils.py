"""
Utility functions for the MAL Twitter Bot
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any

def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    log_filename = f"logs/mal_bot_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Set specific loggers to WARNING to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('tweepy').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)

def load_state() -> Dict[str, Any]:
    """Load bot state from JSON file"""
    state_file = 'state.json'
    
    try:
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
                return state
        else:
            # Return default state
            return {
                'completed_anime_ids': [],
                'completed_manga_ids': [],
                'tweeted_anime_ids': [],
                'tweeted_manga_ids': [],
                'last_check': None,
                'version': '1.0',
                'initialized': False,
                'initialization_date': None
            }
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to load state: {str(e)}")
        return {
            'completed_anime_ids': [],
            'last_check': None,
            'version': '1.0'
        }

def save_state(state: Dict[str, Any]):
    """Save bot state to JSON file"""
    state_file = 'state.json'
    
    try:
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        logging.getLogger(__name__).info("State saved successfully")
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save state: {str(e)}")

def format_duration(minutes: int) -> str:
    """Format duration in minutes to human readable format"""
    if minutes < 60:
        return f"{minutes} minute(s)"
    elif minutes < 1440:  # Less than a day
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours} hour(s)"
        else:
            return f"{hours} hour(s) {remaining_minutes} minute(s)"
    else:
        days = minutes // 1440
        remaining_hours = (minutes % 1440) // 60
        if remaining_hours == 0:
            return f"{days} day(s)"
        else:
            return f"{days} day(s) {remaining_hours} hour(s)"

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with default"""
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default

def create_directory_if_not_exists(directory: str):
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to create directory {directory}: {str(e)}")

def cleanup_temp_files():
    """Clean up temporary files"""
    temp_dir = 'temp'
    if os.path.exists(temp_dir):
        try:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            logging.getLogger(__name__).info("Temporary files cleaned up")
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to cleanup temp files: {str(e)}")

def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = [
        'MAL_USERNAME',
        'TWITTER_BEARER_TOKEN',
        'TWITTER_CONSUMER_KEY',
        'TWITTER_CONSUMER_SECRET',
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True
