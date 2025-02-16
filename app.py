from flask import Flask, render_template, request, jsonify, session, send_file
import json
import random
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

app = Flask(__name__)
app.static_folder = 'static'
app.static_url_path = '/static'

app.secret_key = os.urandom(24)  # For session management

if os.environ.get('PYTHONANYWHERE_DOMAIN'):
    # Production settings for PythonAnywhere
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year
else:
    # Development settings
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

LEAGUE_FOLDERS = {
    'eng1': 'premier_league',
    'eng2': 'championship',
    'ger1': 'bundesliga',
    'ger2': 'bundesliga2',
    'esp1': 'laliga',
    'esp2': 'laliga2',
    'fra1': 'ligue1',
    'fra2': 'ligue2'
}

def load_team_config():
    with open('team_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_team_variations(team_name, team_config):
    # Get all possible variations of a team name (standard name, synonyms, and abbreviation)
    for team_data in team_config['teams'].values():
        if team_name.lower() in [name.lower() for name in [team_data['standard_name']] + team_data['synonyms']]:
            return [team_data['standard_name']] + team_data['synonyms'] + [team_data['abbreviation']]
    return [team_name]

def get_last_name(full_name):
    # Split the name and return the last part
    parts = full_name.split()
    return parts[-1] if parts else full_name

def get_player_teams(all_players):
    # Create a mapping of player names to all their teams
    player_teams = defaultdict(set)
    for player in all_players:
        player_teams[player['name']].add(player['team'])
    return player_teams

def load_fifa_data(league='eng1'):
    all_players = []
    league_folder = LEAGUE_FOLDERS.get(league, 'premier_league')
    data_dir = Path('data') / league_folder
    
    if not data_dir.exists():
        return []
    
    for fifa_version in range(10, 24):
        json_file = data_dir / f'fifa{fifa_version}_players.json'
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    players = json.load(f)
                    # Update image paths to use local files
                    for player in players:
                        # Extract the image ID from the original URL and create local path
                        photo_id = os.path.splitext(os.path.basename(player['photo_url']))[0]
                        flag_id = os.path.splitext(os.path.basename(player['nationality_flag']))[0]
                        
                        player['photo_url'] = f"/static/images/players/{photo_id}.png"
                        player['nationality_flag'] = f"/static/images/flags/{flag_id}.png"
                        
                        # Add nationality name based on flag ID
                        player['nationality'] = get_nationality_from_flag_id(flag_id)
                        # Add last name for easier matching
                        player['last_name'] = get_last_name(player['name'])
                    all_players.extend(players)
            except Exception as e:
                print(f"Error loading {json_file}: {str(e)}")
    
    return all_players

def get_nationality_from_flag_id(flag_id):
    # Map flag IDs to nationality names
    nationality_map = {
        '14': 'England',
        '18': 'France',
        '45': 'Spain',
        '54': 'Brazil',
        '21': 'Germany',
        '27': 'Italy',
        '52': 'Argentina',
        '34': 'Netherlands',
        '95': 'United States',
        '108': 'Ivory Coast',
        '117': 'Ghana',
        '51': 'Serbia',
        '40': 'Russia',
        '38': 'Portugal',
        '7': 'Belgium',
        '12': 'Czech Republic',
        '50': 'Wales',
        '13': 'Denmark',
        '36': 'Norway',
        '43': 'Slovakia'
        # Add more mappings as needed
    }
    return nationality_map.get(flag_id, 'Unknown')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fifa')
def fifa_game():
    league = request.args.get('league', 'eng1')
    league_name = {
        'eng1': 'Premier League',
        'eng2': 'Championship',
        'ger1': 'Bundesliga',
        'ger2': '2. Bundesliga',
        'esp1': 'La Liga',
        'esp2': 'La Liga 2',
        'fra1': 'Ligue 1',
        'fra2': 'Ligue 2'
    }.get(league, 'Premier League')
    
    return render_template('game.html', sport='FIFA', league_name=league_name)

@app.route('/get_player')
def get_player():
    try:
        league = request.args.get('league', 'eng1')
        players = load_fifa_data(league)
        if not players:
            return jsonify({'error': 'Unable to load FIFA player data'}), 500
        
        # Select a random player
        player = random.choice(players)
        
        # Get all teams this player has played for
        player_teams = get_player_teams(players)
        all_teams = player_teams[player['name']]
        
        # Store correct answer in session
        session['current_player'] = {
            'name': player['name'],
            'last_name': player['last_name'],
            'teams': list(all_teams),  # Store all teams the player has played for
            'nationality': player['nationality'],
            'nationality_flag': player['nationality_flag'],
            'photo_url': player['photo_url']
        }
        
        return jsonify({
            'headshot_url': player['photo_url'],
            'nationality_flag': player['nationality_flag']
        })
        
    except Exception as e:
        print(f"Error in get_player route: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': 'Server error occurred'}), 500

@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.json
    guess_name = data.get('name', '').lower()
    guess_team = data.get('team', '').lower()
    guess_nationality = data.get('nationality', '').lower()
    
    current_player = session.get('current_player', {})
    correct_name = current_player.get('name', '').lower()
    correct_last_name = current_player.get('last_name', '').lower()
    correct_teams = [team.lower() for team in current_player.get('teams', [])]
    correct_nationality = current_player.get('nationality', '').lower()
    
    # Load team configuration for synonyms
    team_config = load_team_config()
    # Get all valid team variations for each team the player has played for
    all_valid_teams = set()
    for team in correct_teams:
        variations = get_team_variations(team, team_config)
        all_valid_teams.update(v.lower() for v in variations)
    
    # Check if either full name or last name matches
    name_correct = guess_name == correct_name or guess_name == correct_last_name
    # Check if team matches any valid variation
    team_correct = guess_team in all_valid_teams
    nationality_correct = guess_nationality == correct_nationality
    
    return jsonify({
        'nameCorrect': name_correct,
        'teamCorrect': team_correct,
        'nationalityCorrect': nationality_correct,
        'correctName': current_player.get('name'),
        'correctTeam': ' / '.join(current_player.get('teams', [])),  # Show all teams
        'correctNationality': current_player.get('nationality')
    })

@app.route('/get_nationalities')
def get_nationalities():
    # Get unique nationalities from all players
    players = load_fifa_data()
    nationalities = sorted(set(player['nationality'] for player in players if player['nationality'] != 'Unknown'))
    return jsonify(nationalities)

@app.route('/get_player_names')
def get_player_names():
    players = load_fifa_data()
    # Get unique player names and last names
    names = set()
    for player in players:
        names.add(player['name'])
        names.add(player['last_name'])
    return jsonify(sorted(names))

@app.route('/get_teams')
def get_teams():
    team_config = load_team_config()
    # Get all team variations (standard names, synonyms, and abbreviations)
    teams = set()
    for team_data in team_config['teams'].values():
        teams.add(team_data['standard_name'])
        teams.update(team_data['synonyms'])
        teams.add(team_data['abbreviation'])
    return jsonify(sorted(teams))

@app.route('/check_images')
def check_images():
    """Diagnostic route to check image existence"""
    base_path = Path(app.static_folder)
    
    # Check directories
    players_dir = base_path / 'images' / 'players'
    flags_dir = base_path / 'images' / 'flags'
    
    results = {
        'directories': {
            'static_folder_exists': base_path.exists(),
            'players_dir_exists': players_dir.exists(),
            'flags_dir_exists': flags_dir.exists(),
        },
        'sample_files': {
            'players': [],
            'flags': []
        },
        'counts': {
            'players': 0,
            'flags': 0
        }
    }
    
    # Check some sample files
    if players_dir.exists():
        player_files = list(players_dir.glob('*.png'))
        results['counts']['players'] = len(player_files)
        results['sample_files']['players'] = [f.name for f in player_files[:5]]
    
    if flags_dir.exists():
        flag_files = list(flags_dir.glob('*.png'))
        results['counts']['flags'] = len(flag_files)
        results['sample_files']['flags'] = [f.name for f in flag_files[:5]]
    
    return jsonify(results)

if __name__ == '__main__':
    # For local development
    if os.environ.get('PYTHONANYWHERE_DOMAIN') is None:
        app.run(debug=True, port=5001)
    else:
        # For PythonAnywhere deployment
        app.run() 