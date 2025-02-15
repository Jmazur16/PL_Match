import json
from pathlib import Path

def merge_player_data():
    data_dir = Path('data/premier_league')
    
    # Load fifa18_23_players.json
    fifa18_23_file = data_dir / 'fifa18_23_players.json'
    with open(fifa18_23_file, 'r', encoding='utf-8') as f:
        fifa18_23_players = json.load(f)
    print(f"Loaded {len(fifa18_23_players)} players from fifa18_23_players.json")
    
    # Load existing all_players.json if it exists
    all_players_file = data_dir / 'all_players.json'
    existing_players = []
    if all_players_file.exists():
        with open(all_players_file, 'r', encoding='utf-8') as f:
            existing_players = json.load(f)
        print(f"Loaded {len(existing_players)} players from all_players.json")
    
    # Create a set of unique player identifiers from existing data
    existing_player_keys = {
        (player['name'], player['team'], player['fifa_version'])
        for player in existing_players
    }
    
    # Add new players that don't exist in the current data
    new_players_added = 0
    for player in fifa18_23_players:
        player_key = (player['name'], player['team'], player['fifa_version'])
        if player_key not in existing_player_keys:
            existing_players.append(player)
            existing_player_keys.add(player_key)
            new_players_added += 1
    
    # Sort players by FIFA version and then by name
    existing_players.sort(key=lambda x: (x['fifa_version'], x['name']))
    
    # Save the merged data
    with open(all_players_file, 'w', encoding='utf-8') as f:
        json.dump(existing_players, f, indent=2, ensure_ascii=False)
    
    print(f"\nMerge complete:")
    print(f"New players added: {new_players_added}")
    print(f"Total players in merged file: {len(existing_players)}")

if __name__ == "__main__":
    merge_player_data() 