#!/usr/bin/env python3
"""
MyAnimeList to Twitter Bot
Monitors MAL profile for completed anime and posts tweets automatically.
"""

import logging
import schedule
import time
import json
import os
import threading
from datetime import datetime
from flask import Flask, jsonify

from config import Config
from mal_monitor import MALMonitor
from twitter_client import TwitterClient
from utils import setup_logging, load_state, save_state

# Create Flask app for health checks
app = Flask(__name__)

# Global variables for monitoring bot status
bot_status = {
    'status': 'starting',
    'last_check': None,
    'completed_anime_count': 0,
    'completed_manga_count': 0,
    'error_message': None
}

# Global variables for bot components
mal_monitor = None
twitter_client = None
config = None
logger = None

@app.route('/')
def health_check():
    """Health check endpoint that triggers bot check"""
    # Trigger a bot check when pinged
    if bot_status['status'] == 'idle':
        threading.Thread(target=trigger_bot_check, daemon=True).start()
    
    return jsonify({
        'status': 'healthy',
        'service': 'MAL Twitter Bot',
        'bot_status': bot_status['status'],
        'last_check': bot_status['last_check'],
        'completed_anime': bot_status['completed_anime_count'],
        'completed_manga': bot_status['completed_manga_count'],
        'message': 'Bot check triggered by ping'
    })

@app.route('/status')
def status():
    """Detailed status endpoint"""
    return jsonify(bot_status)

def trigger_bot_check():
    """Trigger a bot check when pinged"""
    global bot_status, mal_monitor, twitter_client, logger
    
    if not mal_monitor:
        if logger:
            logger.warning("Bot components not initialized yet")
        return
    
    try:
        logger.info("Bot check triggered by external ping")
        bot_status['status'] = 'checking'
        
        # Load previous state
        state = load_state()
        
        # Get current completed anime and manga
        completed_anime = mal_monitor.get_completed_anime()
        completed_manga = mal_monitor.get_completed_manga()
        
        # Update status with counts
        bot_status['completed_anime_count'] = len(completed_anime) if completed_anime else 0
        bot_status['completed_manga_count'] = len(completed_manga) if completed_manga else 0
        
        # Check for new completions
        new_anime = []
        new_manga = []
        
        if completed_anime:
            previous_anime_ids = set(state.get('posted_anime', []))
            new_anime = [anime for anime in completed_anime if anime['mal_id'] not in previous_anime_ids]
        
        if completed_manga:
            previous_manga_ids = set(state.get('posted_manga', []))
            new_manga = [manga for manga in completed_manga if manga['mal_id'] not in previous_manga_ids]
        
        # Post tweets for new completions
        posted_count = 0
        if new_anime and twitter_client:
            for anime in new_anime:
                # Download anime image
                image_path = mal_monitor.download_media_image(anime)
                if twitter_client.post_media_tweet(anime, image_path):
                    state.setdefault('posted_anime', []).append(anime['mal_id'])
                    posted_count += 1
                # Clean up image file
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)
                time.sleep(2)  # Rate limiting
        
        if new_manga and twitter_client:
            for manga in new_manga:
                # Download manga image  
                image_path = mal_monitor.download_media_image(manga)
                if twitter_client.post_media_tweet(manga, image_path):
                    state.setdefault('posted_manga', []).append(manga['mal_id'])
                    posted_count += 1
                # Clean up image file
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)
                time.sleep(2)  # Rate limiting
        
        # Save state and update status
        state['last_check'] = datetime.now().isoformat()
        save_state(state)
        
        bot_status['last_check'] = state['last_check']
        bot_status['status'] = 'idle'
        
        if posted_count > 0:
            logger.info(f"Posted {posted_count} new tweets")
        else:
            logger.info("No new completed anime or manga found")
            
    except Exception as e:
        logger.error(f"Error during bot check: {str(e)}")
        bot_status['error_message'] = str(e)
        bot_status['status'] = 'error'

def run_web_server():
    """Run the Flask web server"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def run_bot():
    """Main bot execution function"""
    global bot_status, mal_monitor, twitter_client, config, logger
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting MyAnimeList Twitter Bot (Ping-based mode)...")
    bot_status['status'] = 'initializing'
    
    # Load configuration
    config = Config()
    
    # Initialize components
    mal_monitor = MALMonitor(config.mal_username, config.mal_client_id, config.mal_client_secret)
    
    # Initialize Twitter client with error handling and rate limit handling
    try:
        # Add a small delay to help prevent rate limiting on startup
        time.sleep(2)
        twitter_client = TwitterClient(
            bearer_token=config.twitter_bearer_token,
            consumer_key=config.twitter_consumer_key,
            consumer_secret=config.twitter_consumer_secret,
            access_token=config.twitter_access_token,
            access_token_secret=config.twitter_access_token_secret
        )
    except Exception as e:
        logger.error(f"Failed to initialize Twitter client: {str(e)}")
        if "429" in str(e) or "Too Many Requests" in str(e):
            logger.info("Rate limit encountered during initialization. Waiting before retry...")
            time.sleep(60)  # Wait 1 minute for rate limit reset
            try:
                twitter_client = TwitterClient(
                    bearer_token=config.twitter_bearer_token,
                    consumer_key=config.twitter_consumer_key,
                    consumer_secret=config.twitter_consumer_secret,
                    access_token=config.twitter_access_token,
                    access_token_secret=config.twitter_access_token_secret
                )
            except Exception as retry_e:
                logger.error(f"Failed to initialize Twitter client on retry: {str(retry_e)}")
                logger.info("Bot will continue without Twitter functionality")
                twitter_client = None
        else:
            logger.info("Bot will continue without Twitter functionality")
            twitter_client = None
    
    # Initial setup and status check only
    logger.info(f"Bot initialized. Monitoring user: {config.mal_username}")
    bot_status['status'] = 'idle'
    bot_status['last_check'] = None
    
    # Get initial counts
    try:
        completed_anime = mal_monitor.get_completed_anime()
        completed_manga = mal_monitor.get_completed_manga()
        bot_status['completed_anime_count'] = len(completed_anime) if completed_anime else 0
        bot_status['completed_manga_count'] = len(completed_manga) if completed_manga else 0
        logger.info(f"Found {bot_status['completed_anime_count']} completed anime and {bot_status['completed_manga_count']} completed manga")
    except Exception as e:
        logger.error(f"Failed to get initial counts: {str(e)}")
    
    logger.info("Bot is ready. Waiting for ping to trigger checks...")
    
    # Keep the web server running (no more scheduled tasks)
    try:
        while True:
            time.sleep(60)  # Keep the process alive
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {str(e)}")
        raise

def main():
    """Main function that starts both web server and bot"""
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting MAL Twitter Bot with web server...")
    
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    logger.info("Web server started on port 5000")
    
    # Start bot in main thread
    run_bot()

if __name__ == "__main__":
    # Add restart loop for better reliability
    while True:
        try:
            main()
        except Exception as e:
            print(f"Bot failed to start: {str(e)}")
            print("Restarting in 60 seconds...")
            time.sleep(60)
