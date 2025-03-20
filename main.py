from flask import Flask, render_template, request, jsonify
import networkx as nx
from flask_cors import CORS
import pickle

app = Flask(__name__)
CORS(app)

# Assuming G is your existing NetworkX graph with player nodes
# You'll need to load/import your graph here
#G = nx.read_gml("nba_teammate_graph_2023.gml")
with open("teamMateGraph.pkl", "rb") as f:
    G = pickle.load(f)
# Game state storage (in a real app, you'd want this in a database or session)
game_state = {
    'current_player': None,
    'target_player': None,
    'path': [],
    'wrong_guesses': 0,
    'game_over': False,
    'won': False
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    data = request.json
    start_player = data.get('start_player')
    end_player = data.get('end_player')
    
    if start_player not in G.nodes or end_player not in G.nodes:
        return jsonify({'error': 'One or both players not found'}), 400
    
    # Reset game state
    game_state['current_player'] = start_player
    game_state['target_player'] = end_player
    game_state['path'] = [start_player]
    game_state['wrong_guesses'] = 0
    game_state['game_over'] = False
    game_state['won'] = False
    
    return jsonify({
        'current_player': start_player,
        'target_player': end_player,
        'path': game_state['path'],
        'wrong_guesses': 0
    })

@app.route('/guess', methods=['POST'])
def make_guess():
    if game_state['game_over']:
        return jsonify({'error': 'Game is over'}), 400
        
    data = request.json
    guess = data.get('guess')
    
    if guess not in G.nodes:
        return jsonify({'error': 'Player not found'}), 400
    
    # Check if guess is a teammate of current player
    if guess in G.neighbors(game_state['current_player']):
        game_state['path'].append(guess)
        game_state['current_player'] = guess
        
        if guess == game_state['target_player']:
            game_state['game_over'] = True
            game_state['won'] = True
            shortest_path = nx.shortest_path(G, 
                                          game_state['path'][0], 
                                          game_state['target_player'])
            return jsonify({
                'correct': True,
                'path': game_state['path'],
                'game_over': True,
                'won': True,
                'shortest_path': shortest_path
            })
            
        return jsonify({
            'correct': True,
            'path': game_state['path'],
            'game_over': False
        })
    else:
        game_state['wrong_guesses'] += 1
        if game_state['wrong_guesses'] >= 3:
            game_state['game_over'] = True
            shortest_path = nx.shortest_path(G, 
                                          game_state['path'][0], 
                                          game_state['target_player'])
            return jsonify({
                'correct': False,
                'wrong_guesses': game_state['wrong_guesses'],
                'game_over': True,
                'won': False,
                'shortest_path': shortest_path
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
    
    # Get all players that match the query
    matches = [player for player in G.nodes 
              if query in player.lower()][:10]  # Limit to 10 suggestions
    return jsonify(matches)
if __name__ == '__main__':
    app.run(debug=True)