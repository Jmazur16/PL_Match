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

def get_flag_url(flag_id):
    # Map flag IDs to country codes
    country_codes = {
        '14': 'gb-eng',  # England
        '18': 'fr',      # France
        '45': 'es',      # Spain
        '54': 'br',      # Brazil
        '21': 'de',      # Germany
        '27': 'it',      # Italy
        '52': 'ar',      # Argentina
        '34': 'nl',      # Netherlands
        '95': 'us',      # USA
        '108': 'ci',     # Ivory Coast
        '117': 'gh',     # Ghana
        '51': 'rs',      # Serbia
        '40': 'ru',      # Russia
        '38': 'pt',      # Portugal
        '7': 'be',       # Belgium
        '12': 'cz',      # Czech Republic
        '50': 'gb-wls',  # Wales
        '13': 'dk',      # Denmark
        '36': 'no',      # Norway
        '43': 'sk',      # Slovakia
        # Add more mappings as needed
    }
    
    if flag_id in country_codes:
        return f"https://flagcdn.com/w80/{country_codes[flag_id]}.png"
    return None

def main():
    # Create directory for flags
    base_dir = Path('static/images')
    flags_dir = base_dir / 'flags'
    flags_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    # Track unique flags to avoid downloading duplicates
    downloaded_flags = set()
    
    # Download nationality flags
    for player in all_players:
        # Get flag ID from the original URL
        flag_id = os.path.splitext(os.path.basename(player['nationality_flag']))[0]
        new_flag_url = get_flag_url(flag_id)
        
        if new_flag_url and new_flag_url not in downloaded_flags:
            flag_filename = f"{flag_id}.png"
            flag_path = flags_dir / flag_filename
            
            if not flag_path.exists():
                print(f"Downloading flag for {player['name']} (ID: {flag_id})...")
                if download_image(new_flag_url, flag_path):
                    downloaded_flags.add(new_flag_url)
                    # Update the player's nationality_flag URL in the JSON
                    player['nationality_flag'] = f"/static/images/flags/{flag_filename}"
                    # Add a small delay between downloads
                    time.sleep(random.uniform(0.5, 1.5))
    
    # Save the updated player data with new flag paths
    for fifa_version in range(10, 24):
        json_file = data_dir / f'fifa{fifa_version}_players.json'
        version_players = [p for p in all_players if p['fifa_version'] == fifa_version]
        if version_players:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(version_players, f, indent=2, ensure_ascii=False)
    
    print(f"\nDownloaded {len(downloaded_flags)} unique nationality flags")

if __name__ == "__main__":
    main() 