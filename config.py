"""
Configuration management for the MAL Twitter Bot
"""

import os
import logging

class Config:
    """Configuration class for bot settings"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        self.logger = logging.getLogger(__name__)
        
        # MyAnimeList Configuration
        self.mal_username = os.getenv('MAL_USERNAME', '')
        self.mal_client_id = os.getenv('MAL_CLIENT_ID', '')
        self.mal_client_secret = os.getenv('MAL_CLIENT_SECRET', '')
        
        if not self.mal_username:
            raise ValueError("MAL_USERNAME environment variable is required")
        if not self.mal_client_id:
            raise ValueError("MAL_CLIENT_ID environment variable is required")
        if not self.mal_client_secret:
            raise ValueError("MAL_CLIENT_SECRET environment variable is required")
        
        # Twitter API Configuration
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '')
        self.twitter_consumer_key = os.getenv('TWITTER_CONSUMER_KEY', '')
        self.twitter_consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET', '')
        self.twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN', '')
        self.twitter_access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')
        
        # Validate Twitter credentials
        twitter_creds = [
            self.twitter_bearer_token,
            self.twitter_consumer_key,
            self.twitter_consumer_secret,
            self.twitter_access_token,
            self.twitter_access_token_secret
        ]
        
        if not all(twitter_creds):
            raise ValueError("All Twitter API credentials are required")
        
        # Bot Configuration
        self.check_interval_minutes = int(os.getenv('CHECK_INTERVAL_MINUTES', '30'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY', '60'))
        
        # Tweet Configuration
        self.include_tags = os.getenv('INCLUDE_TAGS', 'true').lower() == 'true'
        self.custom_hashtags = os.getenv('CUSTOM_HASHTAGS', '#anime #MyAnimeList #completed')
        
        self.logger.info("Configuration loaded successfully")
        self.logger.info(f"MAL Username: {self.mal_username}")
        self.logger.info(f"Check interval: {self.check_interval_minutes} minutes")
