import json
from pathlib import Path
import os

def main():
    # Get list of downloaded photos
    photos_dir = Path('static/images/players')
    downloaded_photos = {f.stem for f in photos_dir.glob('*.png')}
    
    # Load all player data
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
    print(f"Total photos downloaded: {len(downloaded_photos)}")
    
    # Check for missing photos
    missing_photos = []
    for player in all_players:
        photo_id = os.path.splitext(os.path.basename(player['photo_url']))[0]
        if photo_id not in downloaded_photos:
            missing_photos.append({
                'name': player['name'],
                'team': player['team'],
                'fifa_version': player['fifa_version'],
                'photo_url': player['photo_url']
            })
    
    print(f"\nPlayers missing photos: {len(missing_photos)}")
    if missing_photos:
        print("\nFirst 10 players with missing photos:")
        for player in missing_photos[:10]:
            print(f"- {player['name']} ({player['team']}, FIFA {player['fifa_version']})")
            print(f"  Photo URL: {player['photo_url']}")

if __name__ == "__main__":
    main() 