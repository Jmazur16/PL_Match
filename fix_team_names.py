import json
from pathlib import Path

def load_team_config():
    with open('team_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def create_team_mapping(team_config):
    # Create a mapping from any valid team name to its standard name
    mapping = {}
    for team_data in team_config['teams'].values():
        standard_name = team_data['standard_name']
        # Add standard name to mapping
        mapping[standard_name.lower()] = standard_name
        # Add all synonyms to mapping
        for synonym in team_data['synonyms']:
            mapping[synonym.lower()] = standard_name
    return mapping

def standardize_team_name(team_name, team_mapping):
    # Handle the "ENG 1" case
    if team_name == "ENG 1":
        return None  # This indicates we need to look up the correct team
    
    # Try to find a standard name for this team
    return team_mapping.get(team_name.lower())

def is_premier_league_team(team_name, team_config):
    # Check if the team is in our configuration
    return any(
        team_name == data['standard_name']
        for data in team_config['teams'].values()
    )

def fix_team_names():
    team_config = load_team_config()
    team_mapping = create_team_mapping(team_config)
    
    # Process each FIFA version
    data_dir = Path('data/premier_league')
    total_fixes = 0
    eng1_fixes = 0
    non_pl_removals = 0
    
    for fifa_version in range(10, 24):
        json_file = data_dir / f'fifa{fifa_version}_players.json'
        if not json_file.exists():
            continue
            
        print(f"\nProcessing FIFA {fifa_version}...")
        
        # Load the data
        with open(json_file, 'r', encoding='utf-8') as f:
            players = json.load(f)
        
        # Keep track of changes
        original_count = len(players)
        fixed_players = []
        
        for player in players:
            original_team = player['team']
            standardized_team = standardize_team_name(original_team, team_mapping)
            
            # Handle "ENG 1" cases - we'll need to look these up
            if original_team == "ENG 1":
                eng1_fixes += 1
                # For now, we'll keep these players but mark them for later fixing
                player['team_needs_verification'] = True
                fixed_players.append(player)
                continue
            
            # If we found a standard name and it's a Premier League team
            if standardized_team and is_premier_league_team(standardized_team, team_config):
                if original_team != standardized_team:
                    total_fixes += 1
                    print(f"Fixed: {original_team} -> {standardized_team}")
                player['team'] = standardized_team
                fixed_players.append(player)
            else:
                # This is a non-Premier League team
                non_pl_removals += 1
                print(f"Removed non-PL team: {original_team}")
        
        # Save the updated data
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_players, f, indent=2, ensure_ascii=False)
        
        print(f"FIFA {fifa_version} summary:")
        print(f"  Original players: {original_count}")
        print(f"  Final players: {len(fixed_players)}")
        print(f"  Players removed: {original_count - len(fixed_players)}")
    
    print("\nOverall summary:")
    print(f"Total team name fixes: {total_fixes}")
    print(f"'ENG 1' cases to verify: {eng1_fixes}")
    print(f"Non-PL teams removed: {non_pl_removals}")

if __name__ == "__main__":
    fix_team_names() 