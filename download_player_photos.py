import json
import requests
import os
from pathlib import Path
import time
import random

def download_image(url, save_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save the image
        with open(save_path, 'wb') as f:
            f.write(response.content)
            
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def main():
    # Create directory for player photos
    base_dir = Path('static/images')
    players_dir = base_dir / 'players'
    players_dir.mkdir(parents=True, exist_ok=True)
    
    # Load FIFA 10-23 data
    all_players = []
    data_dir = Path('data/premier_league')
    
    for fifa_version in range(10, 24):
        json_file = data_dir / f'fifa{fifa_version}_players.json'
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    players = json.load(f)
                    all_players.extend(players)
                    print(f"Loaded {len(players)} players from FIFA {fifa_version}")
            except Exception as e:
                print(f"Error loading {json_file}: {str(e)}")
    
    print(f"\nTotal players loaded: {len(all_players)}")
    
    # Track unique photos to avoid downloading duplicates
    downloaded_photos = set()
    
    # Download player photos
    for player in all_players:
        if player['photo_url'] not in downloaded_photos:
            photo_filename = os.path.basename(player['photo_url'])
            photo_path = players_dir / photo_filename
            
            if not photo_path.exists():
                print(f"Downloading photo for {player['name']}...")
                if download_image(player['photo_url'], photo_path):
                    downloaded_photos.add(player['photo_url'])
                    # Add a small delay between downloads
                    time.sleep(random.uniform(0.5, 1.5))
    
    print(f"\nDownloaded {len(downloaded_photos)} unique player photos")

if __name__ == "__main__":
    main() 