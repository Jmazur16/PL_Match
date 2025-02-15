import requests
from bs4 import BeautifulSoup
import json
import time
import os
import random
from pathlib import Path
import sys
import re

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

def get_team_name_fifa23(row):
    """Team name extraction for FIFA 23"""
    try:
        team_links = row.select("td.player p.team a")
        for link in team_links:
            # Skip links that contain an image (nationality flag)
            if not link.find('img'):
                team_text = link.text.strip()
                # Skip if it's a league name
                if team_text in ['ENG 1', 'Premier League', 'EPL', 'GER 1', 'Bundesliga', 'ESP 1', 'La Liga', 'FRA 1', 'Ligue 1']:
                    continue
                print(f"\nTeam found: {team_text}")
                return team_text
        
        print("\nWARNING: No valid team found")
        return None
    except Exception as e:
        print(f"Error extracting team name: {e}")
        print(f"Full row HTML: {row}")
        return None

def get_team_name_fifa18_22(row):
    """Team name extraction for FIFA 18-22"""
    try:
        # Try multiple selectors for team name
        selectors = [
            "td.player p.team a:first-child",  # Primary selector
            "td.player p.team",                # Fallback 1: direct team paragraph
            "td:nth-child(4)",                 # Fallback 2: fourth column (like FIFA 10-17)
            "td.player div.team"               # Fallback 3: alternate team div
        ]
        
        for selector in selectors:
            team_element = row.select_one(selector)
            if team_element:
                team_text = team_element.text.strip()
                # Skip if it's a league name
                if team_text in ['ENG 1', 'Premier League', 'EPL', 'GER 1', 'Bundesliga', 
                               'ESP 1', 'La Liga', 'FRA 1', 'Ligue 1', 'ITA 1', 'Serie A']:
                    continue
                # Clean the team name
                team_text = team_text.split('\n')[0].strip()  # Take first line if multiple
                # Remove league suffixes
                team_text = team_text.split('|')[0].strip()  # Remove everything after |
                if team_text:
                    print(f"\nTeam found: {team_text}")
                    return team_text
        
        print("\nWARNING: No valid team found")
        return None
    except Exception as e:
        print(f"Error extracting team name: {e}")
        return None

def get_team_name_fifa10_17(row):
    """Team name extraction for FIFA 10-17"""
    try:
        # Use the correct selector that targets the second anchor tag in the team paragraph
        team_element = row.select_one("td.player p.team a:nth-child(2)")
        if team_element:
            team_text = team_element.text.strip()
            print(f"\nTeam found: {team_text}")
            return team_text
            
        # Fallback to try other selectors if the main one fails
        fallback_selectors = [
            "td.player p.team a:last-child",  # Try last anchor if there are multiple
            "td.player p.team",               # Try the whole team paragraph
            "td:nth-child(4)"                 # Legacy selector as final fallback
        ]
        
        for selector in fallback_selectors:
            team_element = row.select_one(selector)
            if team_element:
                team_text = team_element.text.strip()
                # Skip if it's a league name
                if team_text in ['ENG 1', 'Premier League', 'EPL', 'GER 1', 'Bundesliga', 
                               'ESP 1', 'La Liga', 'FRA 1', 'Ligue 1', 'ITA 1', 'Serie A']:
                    continue
                print(f"\nTeam found (fallback): {team_text}")
                return team_text
        
        print("\nWARNING: No valid team found")
        return None
    except Exception as e:
        print(f"Error extracting team name: {e}")
        print(f"Full row HTML: {row}")
        return None

def get_team_name(row, fifa_version):
    """Get team name based on FIFA version"""
    if int(fifa_version) >= 23:
        return get_team_name_fifa23(row)
    elif int(fifa_version) >= 18:
        return get_team_name_fifa18_22(row)
    else:
        return get_team_name_fifa10_17(row)

def get_player_rating_fifa23(row):
    """Rating extraction for FIFA 23"""
    try:
        # FIFA 23 uses a nested div structure
        rating_elem = row.select_one("td.ovr a div div")
        if rating_elem:
            return int(rating_elem.text.strip())
        
        # Fallback to direct td.ovr text
        rating_elem = row.select_one("td.ovr")
        if rating_elem:
            rating_text = rating_elem.text.strip()
            # Extract first number from text
            numbers = re.findall(r'\d+', rating_text)
            if numbers:
                return int(numbers[0])
        return None
    except Exception as e:
        print(f"Error extracting FIFA 23 rating: {e}")
        return None

def get_player_rating_fifa18_22(row):
    """Rating extraction for FIFA 18-22"""
    try:
        # Try nested div structure first
        rating_elem = row.select_one("td.ovr a div div")
        if rating_elem:
            return int(rating_elem.text.strip())
        
        # Try direct td.ovr text
        rating_elem = row.select_one("td.ovr")
        if rating_elem:
            rating_text = rating_elem.text.strip()
            # Extract first number from text
            numbers = re.findall(r'\d+', rating_text)
            if numbers:
                return int(numbers[0])
        return None
    except Exception as e:
        print(f"Error extracting FIFA 18-22 rating: {e}")
        return None

def get_player_rating_fifa10_17(row):
    """Rating extraction for FIFA 10-17"""
    try:
        # Try multiple possible selectors for older FIFA versions
        selectors = [
            "td.ovr a div div",  # Newest format
            "td.ovr div",        # Simpler div structure
            "td.ovr",            # Direct cell
            "td:nth-child(3)"    # Third column (older versions)
        ]
        
        for selector in selectors:
            rating_elem = row.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.text.strip()
                # Extract first number from text
                numbers = re.findall(r'\d+', rating_text)
                if numbers:
                    rating = int(numbers[0])
                    if 1 <= rating <= 99:  # Validate rating is in reasonable range
                        return rating
        
        return None
    except Exception as e:
        print(f"Error extracting FIFA 10-17 rating: {e}")
        return None

def get_player_rating(row, fifa_version):
    """Get player rating based on FIFA version"""
    if int(fifa_version) >= 23:
        rating = get_player_rating_fifa23(row)
    elif int(fifa_version) >= 18:
        rating = get_player_rating_fifa18_22(row)
    else:
        rating = get_player_rating_fifa10_17(row)
    
    # Add validation and debug output
    if rating is None:
        print("\nWARNING: Could not extract rating. Row HTML:")
        print(row.prettify())
    elif not (1 <= rating <= 99):
        print(f"\nWARNING: Invalid rating value ({rating}) found")
        return None
    
    return rating

def validate_fifa_version_data(players, fifa_version, league_id):
    """Check if any players have league names as their team."""
    league_names = {
        '13': ['ENG 1', 'Premier League', 'EPL'],
        '19': ['GER 1', 'Bundesliga'],
        '53': ['ESP 1', 'La Liga'],
        '16': ['FRA 1', 'Ligue 1'],
        '31': ['ITA 1', 'Serie A']
    }
    
    invalid_names = league_names.get(league_id, [])
    invalid_players = [p for p in players if p['team'] in invalid_names]
    
    if invalid_players:
        print(f"\nERROR: Found {len(invalid_players)} players with league names as team in FIFA {fifa_version}")
        print("Example players:")
        for player in invalid_players[:5]:  # Show up to 5 examples
            print(f"- {player['name']} ({player['team']})")
        return False
    return True

def scrape_players(fifa_version, page, league_id):
    url = f"https://www.futwiz.com/en/fifa{fifa_version}/players"
    params = {
        "page": page,
        "release": "nifgold",
        "leagues[]": league_id
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    }
    
    try:
        print(f"\nFetching: {url} with params {params}")
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        # Add a random delay between 1-3 seconds
        delay = random.uniform(1, 3)
        time.sleep(delay)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        players = []
        # Find the table container and get all player rows
        table = soup.select_one('div.table-container table')
        if not table:
            print("Could not find the player table")
            return []
            
        player_rows = table.find_all('tr', class_='table-row')
        print(f"Found {len(player_rows)} player rows")
        
        for row in player_rows:
            try:
                # Get player name using the provided selector
                name_elem = row.select_one('td.player p.name a b')
                if not name_elem:
                    continue
                player_name = name_elem.text.strip()
                
                # Get player image
                player_img = row.select_one('td.face img.player-img')
                player_img_url = player_img['src'] if player_img else None
                
                # Get nationality flag
                nation_img = row.select_one('img.nation')
                nation_img_url = nation_img['src'] if nation_img else None
                if nation_img_url and nation_img_url.startswith('/'):
                    nation_img_url = f"https://cdn.futwiz.com{nation_img_url}"
                
                # Get team name with version-specific handling
                team = get_team_name(row, fifa_version)
                
                # Get player rating with version-specific handling
                rating = get_player_rating(row, fifa_version)
                
                if all([player_img_url, player_name, nation_img_url, team, rating]):
                    player_data = {
                        'name': player_name,
                        'photo_url': player_img_url,
                        'nationality_flag': nation_img_url,
                        'team': team,
                        'rating': rating,
                        'fifa_version': fifa_version
                    }
                    players.append(player_data)
                    print(f"Successfully scraped player: {player_name} ({team}) - Rating: {rating}")
                else:
                    missing = []
                    if not player_img_url: missing.append("photo")
                    if not player_name: missing.append("name")
                    if not nation_img_url: missing.append("nationality")
                    if not team: missing.append("team")
                    if not rating: missing.append("rating")
                    print(f"Skipping player due to missing data: {', '.join(missing)}")
                    
            except Exception as e:
                print(f"Error processing player: {str(e)}")
                continue
                
        return players
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:  # Too Many Requests
            print("Rate limited! Waiting 60 seconds...")
            time.sleep(60)
            return []
        print(f"HTTP Error scraping page {page} of FIFA {fifa_version}: {str(e)}")
        return []
    except Exception as e:
        print(f"Error scraping page {page} of FIFA {fifa_version}: {str(e)}")
        return []

def scrape_fifa_version(fifa_version, data_dir, league_id):
    print(f"\n{'='*50}")
    print(f"Starting to scrape FIFA {fifa_version}")
    print(f"{'='*50}")
    
    players = []
    seen_players = set()  # Track unique player records
    page = 0
    consecutive_empty_pages = 0
    
    while consecutive_empty_pages < 3:  # Stop if we get 3 empty pages in a row
        print(f"\nScraping FIFA {fifa_version} page {page}...")
        new_players = scrape_players(fifa_version, page, league_id)
        
        if not new_players:
            consecutive_empty_pages += 1
            print(f"Empty page {page}. Empty pages in a row: {consecutive_empty_pages}")
        else:
            consecutive_empty_pages = 0
            # Only skip if all fields are identical
            for player in new_players:
                player_key = (
                    player['name'],
                    player['team'],
                    player['photo_url'],
                    player['nationality_flag']
                )
                if player_key not in seen_players:
                    seen_players.add(player_key)
                    players.append(player)
                else:
                    print(f"Skipping exact duplicate: {player['name']} ({player['team']})")
        
        # Add a shorter delay between pages (1-3 seconds)
        delay = random.uniform(1, 3)
        time.sleep(delay)
        page += 1
    
    # Save this FIFA version's data
    output_file = data_dir / f'fifa{fifa_version}_players.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
    
    print(f"\nScraped {len(players)} unique players for FIFA {fifa_version}")
    print(f"Data saved to {output_file}")
    
    # Validate the data before continuing
    if not validate_fifa_version_data(players, fifa_version, league_id):
        print(f"\nStopping scraping due to league names found in FIFA {fifa_version}")
        print("Please check the team selector and try again.")
        sys.exit(1)
        
    return players

def test_scrape():
    """Test scraping one page from each league for different FIFA version groups"""
    # Use the global league mappings
    TEST_LEAGUES = {
        code: (LEAGUE_IDS[code], LEAGUE_NAMES[code])
        for code in LEAGUE_IDS.keys()
    }
    
    # FIFA version groups to test
    VERSION_GROUPS = [
        (10, "FIFA 10-17"),
        (18, "FIFA 18-22"),
        (23, "FIFA 23")
    ]
    
    for league_code, (league_id, league_name) in TEST_LEAGUES.items():
        print(f"\n{'='*70}")
        print(f"Testing {league_name} (ID: {league_id})")
        print(f"{'='*70}")
        
        # Create data directory for this league
        data_dir = Path(f'data/{LEAGUE_FOLDERS[league_code]}')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        for version, group_name in VERSION_GROUPS:
            print(f"\n{'-'*50}")
            print(f"Testing {group_name}")
            print(f"{'-'*50}")
            
            # Test one page
            players = scrape_players(version, 0, league_id)
            
            if players:
                print(f"\nSuccessfully scraped {len(players)} players")
                print("\nExample players:")
                for player in players[:3]:  # Show first 3 players
                    print(f"- {player['name']} ({player['team']}) - Rating: {player['rating']}")
                
                # Save test data to appropriate league folder
                output_file = data_dir / f'fifa{version}_test_players.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(players, f, indent=2, ensure_ascii=False)
                print(f"\nTest data saved to {output_file}")
                
                # Print full HTML of first row for debugging if needed
                if not players[0].get('rating'):
                    print("\nWARNING: Rating not found. Debugging first row:")
                    table = BeautifulSoup(response.text, 'html.parser').select_one('div.table-container table')
                    if table:
                        first_row = table.find('tr', class_='table-row')
                        if first_row:
                            print(first_row.prettify())
            else:
                print(f"WARNING: No players found for {league_name} in {group_name}")
            
            # Add delay between tests
            time.sleep(random.uniform(3, 5))
        
        # Add longer delay between leagues
        if league_code != list(TEST_LEAGUES.keys())[-1]:
            delay = random.uniform(8, 10)
            print(f"\nWaiting {delay:.1f} seconds before testing next league...")
            time.sleep(delay)

def main():
    # Use only the specified leagues
    LEAGUES_TO_SCRAPE = ['eng1', 'fra1', 'ger1', 'esp1', 'ita1']
    
    # Get FIFA version range from command line arguments or default to 10-17 range
    start_version = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    end_version = int(sys.argv[2]) if len(sys.argv) > 2 else 17
    
    for league in LEAGUES_TO_SCRAPE:
        print(f"\n{'='*50}")
        print(f"Starting to scrape {league.upper()} - {LEAGUE_NAMES[league]}")
        print(f"{'='*50}")
        
        league_id = LEAGUE_IDS[league]
        
        # Create data directory for this league
        data_dir = Path(f'data/{LEAGUE_FOLDERS[league]}')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Scrape each FIFA version for this league
        for fifa_version in range(start_version, end_version + 1):
            print(f"\n{'='*50}")
            print(f"Starting to scrape FIFA {fifa_version} - {LEAGUE_NAMES[league]}")
            print(f"{'='*50}")
            
            version_players = scrape_fifa_version(fifa_version, data_dir, league_id)
            
            # Save version data
            output_file = data_dir / f'fifa{fifa_version}_players.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(version_players, f, indent=2, ensure_ascii=False)
            
            print(f"\nScraped {len(version_players)} players for FIFA {fifa_version} - {LEAGUE_NAMES[league]}")
            print(f"Data saved to {output_file}")
            
            # Add a longer delay between FIFA versions (3-5 seconds)
            if fifa_version < end_version:
                delay = random.uniform(3, 5)
                time.sleep(delay)
        
        # Add an even longer delay between leagues (10-15 seconds)
        if league != LEAGUES_TO_SCRAPE[-1]:
            delay = random.uniform(10, 15)
            print(f"\nWaiting {delay:.1f} seconds before starting next league...")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_scrape()
    else:
        main() 