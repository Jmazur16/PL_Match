import json
from pathlib import Path
from collections import defaultdict

def analyze_teams():
    all_players = []
    data_dir = Path('data/premier_league')
    
    # Dictionary to track teams by FIFA version
    teams_by_version = defaultdict(set)
    
    # Load all FIFA version data
    for fifa_version in range(10, 24):
        json_file = data_dir / f'fifa{fifa_version}_players.json'
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    players = json.load(f)
                    for player in players:
                        teams_by_version[fifa_version].add(player['team'])
                    all_players.extend(players)
                    print(f"Loaded {len(players)} players from FIFA {fifa_version}")
            except Exception as e:
                print(f"Error loading {json_file}: {str(e)}")
    
    # Get all unique teams across all versions
    all_teams = sorted(set(player['team'] for player in all_players))
    
    print("\nAll unique teams across all FIFA versions:")
    print("=" * 50)
    for team in all_teams:
        print(team)
    
    print("\nTeams by FIFA version:")
    print("=" * 50)
    for version in sorted(teams_by_version.keys()):
        print(f"\nFIFA {version} Teams:")
        for team in sorted(teams_by_version[version]):
            print(f"  - {team}")
    
    # Print some statistics
    print("\nStatistics:")
    print("=" * 50)
    print(f"Total unique teams: {len(all_teams)}")
    print(f"Total players: {len(all_players)}")
    
    # Check for potential data issues
    print("\nPotential data issues:")
    print("=" * 50)
    suspicious_teams = [team for team in all_teams if any([
        team.startswith('ENG'),
        team.startswith('GER'),
        team.startswith('ESP'),
        team.startswith('FRA'),
        team.isdigit(),
        len(team) <= 2
    ])]
    
    if suspicious_teams:
        print("Found suspicious team names that might need correction:")
        for team in suspicious_teams:
            # Find example players with this team
            examples = [p for p in all_players if p['team'] == team][:3]
            print(f"\n{team}:")
            for player in examples:
                print(f"  - {player['name']} (FIFA {player['fifa_version']})")

if __name__ == "__main__":
    analyze_teams() 