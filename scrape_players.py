import requests
from bs4 import BeautifulSoup
import json
import time
import os
from pathlib import Path
import random
import sys
from concurrent.futures import ThreadPoolExecutor
import threading

# Constants for league mappings
LEAGUE_FOLDERS = {
    'eng1': 'premier_league',
    'ger1': 'bundesliga',
    'esp1': 'laliga',
    'fra1': 'ligue1',
    'ita1': 'serie_a'
}

LEAGUE_IDS = {
    'eng1': '13',  # Premier League
    'ger1': '19',  # Bundesliga
    'esp1': '53',  # La Liga
    'fra1': '16',  # Ligue 1
    'ita1': '31'   # Serie A
}

LEAGUE_NAMES = {
    'eng1': 'Premier League',
    'ger1': 'Bundesliga',
    'esp1': 'La Liga',
    'fra1': 'Ligue 1',
    'ita1': 'Serie A'
}

# Thread-safe set for tracking downloaded images
downloaded_images = set()
download_lock = threading.Lock()

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
            
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def download_player_images(players, base_dir):
    """Download player images in parallel."""
    players_dir = base_dir / 'players'
    players_dir.mkdir(parents=True, exist_ok=True)
    
    def download_single_player(player):
        if 'photo_url' not in player:
            return
        
        photo_filename = os.path.basename(player['photo_url'])
        photo_path = players_dir / photo_filename
        
        if not photo_path.exists():
            download_image(player['photo_url'], photo_path)
    
    # Use ThreadPoolExecutor for parallel downloads
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(download_single_player, players)

def get_team_name(row, fifa_version):
    """Get team name with improved error handling."""
    try:
        team_links = row.select("td.player p.team a")
        for link in team_links:
            if not link.find('img'):
                team_text = link.text.strip()
                if team_text not in ['ENG 1', 'Premier League', 'EPL', 'GER 1', 'Bundesliga', 
                                   'ESP 1', 'La Liga', 'FRA 1', 'Ligue 1', 'ITA 1', 'Serie A']:
                    return team_text
        return None
    except Exception as e:
        print(f"Error extracting team name: {e}")
        return None

def get_player_rating(row):
    """Get player rating with improved error handling."""
    try:
        rating_elem = row.select_one("td.ovr")
        if rating_elem:
            rating_text = rating_elem.text.strip()
            rating = int(''.join(filter(str.isdigit, rating_text)))
            if 1 <= rating <= 99:
                return rating
        return None
    except Exception:
        return None

def scrape_players(fifa_version, page, league_id):
    """Scrape players with optimized error handling and reduced delays."""
    url = f"https://www.futwiz.com/en/fifa{fifa_version}/players"
    params = {
        "page": page,
        "release": "nifgold",
        "leagues[]": league_id
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Reduced delay between requests
        time.sleep(random.uniform(0.5, 1.0))
        
        soup = BeautifulSoup(response.text, 'html.parser')
        players = []
        
        table = soup.select_one('div.table-container table')
        if not table:
            return []
            
        player_rows = table.find_all('tr', class_='table-row')
        
        for row in player_rows:
            try:
                name_elem = row.select_one('td.player p.name a b')
                if not name_elem:
                    continue
                    
                player_name = name_elem.text.strip()
                player_img = row.select_one('td.face img.player-img')
                player_img_url = player_img['src'] if player_img else None
                
                nation_img = row.select_one('img.nation')
                nation_img_url = nation_img['src'] if nation_img else None
                if nation_img_url and nation_img_url.startswith('/'):
                    nation_img_url = f"https://cdn.futwiz.com{nation_img_url}"
                
                team = get_team_name(row, fifa_version)
                rating = get_player_rating(row)
                
                if all([player_img_url, player_name, nation_img_url, team, rating]):
                    players.append({
                        'name': player_name,
                        'photo_url': player_img_url,
                        'nationality_flag': nation_img_url,
                        'team': team,
                        'rating': rating,
                        'fifa_version': fifa_version
                    })
                    
            except Exception as e:
                print(f"Error processing player: {str(e)}")
                continue
                
        return players
    
    except requests.exceptions.RequestException as e:
        print(f"Error scraping page {page} of FIFA {fifa_version}: {str(e)}")
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 429:
            time.sleep(30)  # Reduced wait time for rate limiting
        return []

def scrape_fifa_version(fifa_version, data_dir, league_id):
    """Scrape a FIFA version with optimized duplicate handling."""
    players = []
    seen_players = set()
    page = 0
    consecutive_empty_pages = 0
    
    while consecutive_empty_pages < 2:  # Reduced threshold for empty pages
        new_players = scrape_players(fifa_version, page, league_id)
        
        if not new_players:
            consecutive_empty_pages += 1
        else:
            consecutive_empty_pages = 0
            for player in new_players:
                player_key = (player['name'], player['team'], player['photo_url'])
                if player_key not in seen_players:
                    seen_players.add(player_key)
                    players.append(player)
        
        page += 1
    
    # Save this FIFA version's data
    output_file = data_dir / f'fifa{fifa_version}_players.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
    
    return players

def main():
    # Create base directory for images
    base_dir = Path('static/images')
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Process leagues in parallel
    for league in LEAGUE_FOLDERS.keys():
        print(f"\nStarting to scrape {league.upper()} - {LEAGUE_NAMES[league]}")
        
        league_id = LEAGUE_IDS[league]
        data_dir = Path(f'data/{LEAGUE_FOLDERS[league]}')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Scrape FIFA versions in reverse order (23 to 10)
        for fifa_version in range(23, 9, -1):
            print(f"\nScraping FIFA {fifa_version} - {LEAGUE_NAMES[league]}")
            
            version_players = scrape_fifa_version(fifa_version, data_dir, league_id)
            
            # Download images for this version
            download_player_images(version_players, base_dir)
            
            print(f"Scraped {len(version_players)} players for FIFA {fifa_version}")
            
            # Reduced delay between FIFA versions
            if fifa_version > 10:
                time.sleep(random.uniform(1, 2))
        
        # Reduced delay between leagues
        if league != list(LEAGUE_FOLDERS.keys())[-1]:
            time.sleep(random.uniform(2, 3))

if __name__ == "__main__":
    main() 