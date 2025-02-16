import json
import requests
import os
from pathlib import Path
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor

# Thread-safe set for tracking downloaded images
downloaded_images = set()
download_lock = threading.Lock()

LEAGUE_FOLDERS = {
    'eng1': 'premier_league',
    'ger1': 'bundesliga',
    'esp1': 'laliga',
    'fra1': 'ligue1',
    'ita1': 'serie_a'
}

def download_image(url, save_path):
    """Download an image with optimized handling."""
    try:
        # Check if we've already downloaded this image
        with download_lock:
            if url in downloaded_images:
                return True
            
        if os.path.exists(save_path):
            with download_lock:
                downloaded_images.add(url)
            return True
            
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save the image
        with open(save_path, 'wb') as f:
            f.write(response.content)
            
        with download_lock:
            downloaded_images.add(url)
            print(f"Downloaded: {os.path.basename(save_path)}")
            
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def download_player_images(players, base_dir):
    """Download player images in parallel."""
    players_dir = base_dir / 'players'
    players_dir.mkdir(parents=True, exist_ok=True)
    
    def download_single_player(player):
        if 'photo_url' not in player or not player['photo_url'].startswith('http'):
            return
        
        photo_filename = os.path.basename(player['photo_url'])
        photo_path = players_dir / photo_filename
        
        if not photo_path.exists():
            download_image(player['photo_url'], photo_path)
    
    # Use ThreadPoolExecutor for parallel downloads
    with ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(download_single_player, players))

def main():
    # Create base directory for images
    base_dir = Path('static/images')
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Track total players and downloads
    total_players = 0
    total_downloads = 0
    
    # Process each league
    for league in LEAGUE_FOLDERS.keys():
        print(f"\nProcessing {league.upper()} league data...")
        data_dir = Path(f'data/{LEAGUE_FOLDERS[league]}')
        
        if not data_dir.exists():
            print(f"No data directory found for {league}")
            continue
        
        # Process FIFA versions in reverse order (23 to 10)
        for fifa_version in range(23, 9, -1):
            json_file = data_dir / f'fifa{fifa_version}_players.json'
            
            if not json_file.exists():
                continue
                
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    players = json.load(f)
                    total_players += len(players)
                    print(f"Loading {len(players)} players from FIFA {fifa_version}")
                    
                    # Download images for this version
                    initial_downloads = len(downloaded_images)
                    download_player_images(players, base_dir)
                    new_downloads = len(downloaded_images) - initial_downloads
                    total_downloads += new_downloads
                    
                    if new_downloads > 0:
                        print(f"Downloaded {new_downloads} new images from FIFA {fifa_version}")
                    
            except Exception as e:
                print(f"Error processing {json_file}: {str(e)}")
                continue
    
    print(f"\nDownload complete!")
    print(f"Total players processed: {total_players}")
    print(f"Total images downloaded: {total_downloads}")
    print(f"Total unique images: {len(downloaded_images)}")

if __name__ == "__main__":
    main() 