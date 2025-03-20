from flask import Flask, render_template, request, jsonify
import networkx as nx
from flask_cors import CORS
import pickle

app = Flask(__name__)
CORS(app)

with open("teamMateGraph.pkl", "rb") as f:
    G = pickle.load(f)

game_state = {
    'current_player': None,
    'target_player': None,
    'path': [],
    'wrong_guesses': 0,
    'game_over': False,
    'won': False
}
def format_player2(player_id):
    """Format player info for display"""
    player_data = G.nodes[player_id]
    return {
        "name": player_data['name'],
        "years": f"{player_data['first_season']} → {player_data['last_season']}",
        "image": player_data.get('image', 'https://www.basketball-reference.com/req/202106291/images/headshots/jamesle01.jpg')  # Fallback image if not available
    }
def format_player(player_id):
    """Format player info for display"""
    player_data = G.nodes[player_id]
    return f"{player_data['name']} ({player_data['first_season']} → {player_data['last_season']})"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    data = request.json
    start_player = data.get('start_player').split(' (')[0]  # Extract name from formatted string
    end_player = data.get('end_player').split(' (')[0]
    
    # Find matching player IDs by name
    start_id = next((n for n, d in G.nodes(data=True) if d['name'] == start_player), None)
    end_id = next((n for n, d in G.nodes(data=True) if d['name'] == end_player), None)
    
    if not start_id or not end_id:
        return jsonify({'error': 'One or both players not found'}), 400
    
    game_state['current_player'] = start_id
    game_state['target_player'] = end_id
    game_state['path'] = [start_id]
    game_state['wrong_guesses'] = 0
    game_state['game_over'] = False
    game_state['won'] = False
    
    return jsonify({
        'current_player': format_player2(start_id),
        'target_player': format_player2(end_id),
        'path': [format_player2(p) for p in game_state['path']],
        'wrong_guesses': 0
    })

@app.route('/guess', methods=['POST'])
def make_guess():
    if game_state['game_over']:
        return jsonify({'error': 'Game is over'}), 400
        
    data = request.json
    guess_name = data.get('guess').split(' (')[0]
    guess_id = next((n for n, d in G.nodes(data=True) if d['name'] == guess_name), None)
    
    if not guess_id:
        return jsonify({'error': 'Player not found'}), 400
    
    if guess_id in G.neighbors(game_state['current_player']):
        game_state['path'].append(guess_id)
        game_state['current_player'] = guess_id
        
        if guess_id == game_state['target_player']:
            game_state['game_over'] = True
            game_state['won'] = True
            shortest_path = nx.shortest_path(G, game_state['path'][0], game_state['target_player'])
            return jsonify({
                'correct': True,
                'path': [format_player(p) for p in game_state['path']],
                'game_over': True,
                'won': True,
                'shortest_path': [format_player(p) for p in shortest_path]
            })
            
        return jsonify({
            'correct': True,
            'path': [format_player(p) for p in game_state['path']],
            'game_over': False
        })
    else:
        game_state['wrong_guesses'] += 1
        if game_state['wrong_guesses'] >= 3:
            game_state['game_over'] = True
            shortest_path = nx.shortest_path(G, game_state['path'][0], game_state['target_player'])
            return jsonify({
                'correct': False,
                'wrong_guesses': game_state['wrong_guesses'],
                'game_over': True,
                'won': False,
                'shortest_path': [format_player(p) for p in shortest_path]
            })
        return jsonify({
            'correct': False,
            'wrong_guesses': game_state['wrong_guesses'],
            'game_over': False
        })

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    matches = [
        format_player(player_id)
        for player_id, data in G.nodes(data=True)
        if query in data['name'].lower()
    ][:10]  # Limit to 10 suggestions
    return jsonify(matches)

if __name__ == '__main__':
    app.run(debug=True)