"""
MyAnimeList profile monitoring functionality
"""

import requests
import logging
import time
import os
from typing import List, Dict, Optional
from PIL import Image
import io

class MALMonitor:
    """Monitors MyAnimeList profile for completed anime"""
    
    def __init__(self, username: str, client_id: str, client_secret: str):
        """Initialize MAL monitor"""
        self.username = username
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.myanimelist.net/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MAL-Twitter-Bot/1.0',
            'X-MAL-CLIENT-ID': client_id
        })
        self.access_token = None
        
    def get_completed_anime(self) -> Optional[List[Dict]]:
        """Get list of completed anime from user's MAL profile using official API"""
        try:
            # Get user's completed anime list using public endpoint
            url = f"{self.base_url}/users/{self.username}/animelist"
            params = {
                'status': 'completed',
                'fields': 'list_status,node_id,title,main_picture,start_season,genres,num_episodes',
                'limit': 1000  # Get up to 1000 entries
            }
            
            self.logger.info(f"Fetching completed anime for user: {self.username}")
            
            # For the official API, we need to authenticate using client credentials
            # Since we can't do full OAuth flow in this context, we'll use public data access
            headers = {
                'X-MAL-CLIENT-ID': self.client_id,
                'User-Agent': 'MAL-Twitter-Bot/1.0'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 401:
                self.logger.error("Authentication failed - invalid client credentials")
                return None
            elif response.status_code == 403:
                self.logger.error("Access forbidden - check API permissions")
                return None
            elif response.status_code != 200:
                self.logger.error(f"Failed to fetch anime list: HTTP {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return None
                
            data = response.json()
            
            if 'data' not in data:
                self.logger.error("Invalid response format from MAL API")
                return None
            
            anime_list = []
            for entry in data['data']:
                node = entry['node']
                list_status = entry.get('list_status', {})
                
                # Get the highest quality image available
                image_url = None
                if 'main_picture' in node:
                    pictures = node['main_picture']
                    # Official API provides 'large' and 'medium'
                    image_url = pictures.get('large') or pictures.get('medium')
                
                anime_info = {
                    'mal_id': node['id'],
                    'title': node['title'],
                    'score': list_status.get('score', 0),
                    'image_url': image_url,
                    'finished_date': list_status.get('finish_date'),
                    'episodes': node.get('num_episodes', 0),
                    'year': node.get('start_season', {}).get('year') if node.get('start_season') else None,
                    'genres': [genre['name'] for genre in node.get('genres', [])]
                }
                anime_list.append(anime_info)
            
            self.logger.info(f"Found {len(anime_list)} completed anime")
            return anime_list
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error while fetching anime list: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching anime list: {str(e)}")
            return None
    
    def get_completed_manga(self) -> Optional[List[Dict]]:
        """Get list of completed manga from user's MAL profile using official API"""
        try:
            # Get user's completed manga list using public endpoint
            url = f"{self.base_url}/users/{self.username}/mangalist"
            params = {
                'status': 'completed',
                'fields': 'list_status,node_id,title,main_picture,start_date,genres,num_volumes,num_chapters',
                'limit': 1000  # Get up to 1000 entries
            }
            
            self.logger.info(f"Fetching completed manga for user: {self.username}")
            
            # For the official API, we need to authenticate using client credentials
            headers = {
                'X-MAL-CLIENT-ID': self.client_id,
                'User-Agent': 'MAL-Twitter-Bot/1.0'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 401:
                self.logger.error("Authentication failed - invalid client credentials")
                return None
            elif response.status_code == 403:
                self.logger.error("Access forbidden - check API permissions")
                return None
            elif response.status_code != 200:
                self.logger.error(f"Failed to fetch manga list: HTTP {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return None
                
            data = response.json()
            
            if 'data' not in data:
                self.logger.error("Invalid response format from MAL API")
                return None
            
            manga_list = []
            for entry in data['data']:
                node = entry['node']
                list_status = entry.get('list_status', {})
                
                # Get the highest quality image available
                image_url = None
                if 'main_picture' in node:
                    pictures = node['main_picture']
                    # Official API provides 'large' and 'medium'
                    image_url = pictures.get('large') or pictures.get('medium')
                
                manga_info = {
                    'mal_id': node['id'],
                    'title': node['title'],
                    'score': list_status.get('score', 0),
                    'image_url': image_url,
                    'finished_date': list_status.get('finish_date'),
                    'volumes': node.get('num_volumes', 0),
                    'chapters': node.get('num_chapters', 0),
                    'start_year': node.get('start_date', '').split('-')[0] if node.get('start_date') else None,
                    'genres': [genre['name'] for genre in node.get('genres', [])],
                    'type': 'manga'  # Add type identifier
                }
                manga_list.append(manga_info)
            
            self.logger.info(f"Found {len(manga_list)} completed manga")
            return manga_list
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error while fetching manga list: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching manga list: {str(e)}")
            return None
    
    def download_media_image(self, media: Dict) -> Optional[str]:
        """Download anime/manga cover image and return local path"""
        if not media.get('image_url'):
            media_type = media.get('type', 'anime')
            self.logger.warning(f"No image URL for {media_type}: {media['title']}")
            return None
        
        try:
            media_type = media.get('type', 'anime')
            self.logger.info(f"Downloading image for: {media['title']}")
            
            response = self.session.get(media['image_url'], timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to download image: HTTP {response.status_code}")
                return None
            
            # Create temp directory if it doesn't exist
            os.makedirs('temp', exist_ok=True)
            
            # Save image with media type and ID as filename
            image_filename = f"temp/{media_type}_{media['mal_id']}.jpg"
            
            # Process image with Pillow to ensure it's in the right format
            image = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary (removes transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Ensure minimum quality (720p) and resize if needed
            min_width, min_height = 720, 720
            max_width, max_height = 1920, 1080  # Twitter's max recommended size
            
            current_width, current_height = image.size
            
            # If image is smaller than 720p, upscale it to maintain quality
            if current_width < min_width or current_height < min_height:
                scale_factor = max(min_width / current_width, min_height / current_height)
                new_width = int(current_width * scale_factor)
                new_height = int(current_height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.logger.info(f"Upscaled image from {current_width}x{current_height} to {new_width}x{new_height}")
            
            # If image is too large, downscale while maintaining aspect ratio
            elif current_width > max_width or current_height > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                self.logger.info(f"Downscaled image to {image.size[0]}x{image.size[1]}")
            
            # Save as high-quality JPEG
            image.save(image_filename, 'JPEG', quality=98, optimize=True)
            
            self.logger.info(f"Image saved: {image_filename}")
            return image_filename
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error while downloading image: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing image for {media['title']}: {str(e)}")
            return None
    
    def get_anime_details(self, mal_id: int) -> Optional[Dict]:
        """Get detailed information about a specific anime"""
        try:
            url = f"{self.base_url}/anime/{mal_id}"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 429:
                self.logger.warning("Rate limited by Jikan API, waiting...")
                time.sleep(60)
                response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch anime details: HTTP {response.status_code}")
                return None
                
            data = response.json()
            
            if 'data' not in data:
                self.logger.error("Invalid response format from Jikan API")
                return None
            
            return data['data']
            
        except Exception as e:
            self.logger.error(f"Error fetching anime details for ID {mal_id}: {str(e)}")
            return None
