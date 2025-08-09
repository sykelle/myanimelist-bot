"""
Twitter API client for posting anime completion tweets
"""

import tweepy
import logging
import os
import time
from typing import Dict, Optional, Any

class TwitterClient:
    """Twitter API client for posting tweets"""
    
    def __init__(self, bearer_token: str, consumer_key: str, consumer_secret: str, 
                 access_token: str, access_token_secret: str):
        """Initialize Twitter client"""
        self.logger = logging.getLogger(__name__)
        
        try:
            # Initialize Twitter API v2 client
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=False  # Handle rate limits manually to prevent loops
            )
            
            # Initialize API v1.1 for media upload
            auth = tweepy.OAuth1UserHandler(
                consumer_key, consumer_secret, access_token, access_token_secret
            )
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=False)
            
            # Skip authentication test to avoid rate limits on startup
            self.logger.info("Twitter client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter client: {str(e)}")
            raise
    
    def post_media_tweet(self, media: Dict[str, Any], image_path: Optional[str] = None) -> bool:
        """Post a tweet about completed anime or manga"""
        # Initialize variables at function scope
        tweet_text = self._format_tweet_text(media)
        media_ids = None
        
        try:
            # Upload media if image exists
            if image_path and os.path.exists(image_path):
                try:
                    media_response = self.api_v1.media_upload(image_path)
                    if media_response and hasattr(media_response, 'media_id_string'):
                        media_ids = [media_response.media_id_string]
                        self.logger.info("Image uploaded successfully")
                    else:
                        self.logger.error("Failed to upload image: No media_id_string in response")
                except Exception as e:
                    self.logger.error(f"Failed to upload image: {str(e)}")
            
            # Post tweet
            response = self.client.create_tweet(
                text=tweet_text,
                media_ids=media_ids
            )
            
            if response and hasattr(response, 'data') and getattr(response, 'data', None):
                try:
                    data = getattr(response, 'data', None)
                    tweet_id = getattr(data, 'id', None) if data else None
                except AttributeError:
                    tweet_id = None
                self.logger.info(f"Tweet posted successfully: {tweet_id}")
                return True
            else:
                self.logger.error("Failed to post tweet: No response data")
                return False
                
        except tweepy.TooManyRequests as e:
            self.logger.warning(f"Twitter rate limit exceeded: {str(e)}")
            # Wait 5 minutes and try once more before giving up
            self.logger.info("Waiting 5 minutes before retry attempt...")
            time.sleep(300)  # 5 minutes
            try:
                # Single retry after waiting
                response = self.client.create_tweet(
                    text=tweet_text,
                    media_ids=media_ids
                )
                
                if response and hasattr(response, 'data') and getattr(response, 'data', None):
                    try:
                        data = getattr(response, 'data', None)
                        tweet_id = getattr(data, 'id', None) if data else None
                    except AttributeError:
                        tweet_id = None
                    self.logger.info(f"Tweet posted successfully after rate limit wait: {tweet_id}")
                    return True
                else:
                    self.logger.error("Failed to post tweet after rate limit wait: No response data")
                    return False
            except Exception as retry_e:
                self.logger.error(f"Failed to post tweet after rate limit retry: {str(retry_e)}")
                return False
        except tweepy.Forbidden as e:
            self.logger.error(f"Twitter API forbidden error: {str(e)}")
            return False
        except tweepy.Unauthorized as e:
            self.logger.error(f"Twitter API unauthorized error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error posting tweet: {str(e)}")
            return False
    
    def _format_tweet_text(self, media: Dict[str, Any]) -> str:
        """Format tweet text for anime/manga completion"""
        title = media['title']
        score = media['score']
        media_type = media.get('type', 'anime')
        
        # Simple format: "finished [anime/manga name]" and "[score]/10 [emoji]" if scored
        if score > 0:
            # Select emoji based on score
            if score >= 9:
                emoji = "🌟"
            elif score >= 8:
                emoji = "😍"
            elif score >= 7:
                emoji = "👍"
            elif score >= 6:
                emoji = "😊"
            elif score >= 5:
                emoji = "😐"
            else:
                emoji = "😔"
            
            tweet = f"finished {title}\n{score}/10 {emoji}"
        else:
            tweet = f"finished {title}"
        
        return tweet
    
    def test_connection(self) -> bool:
        """Test Twitter API connection"""
        try:
            user = self.client.get_me()
            if user and hasattr(user, 'data') and getattr(user, 'data', None):
                try:
                    data = getattr(user, 'data', None)
                    username = getattr(data, 'username', 'Unknown') if data else 'Unknown'
                except AttributeError:
                    username = 'Unknown'
                self.logger.info(f"Connected to Twitter as: @{username}")
                return True
            else:
                self.logger.error("Failed to get user data from Twitter")
                return False
        except tweepy.TooManyRequests:
            self.logger.warning("Rate limit exceeded during connection test")
            return False
        except Exception as e:
            self.logger.error(f"Twitter connection test failed: {str(e)}")
            return False
