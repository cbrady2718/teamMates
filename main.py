from flask import Flask, render_template, request, jsonify
import networkx as nx
from flask_cors import CORS
import pickle
import os

app = Flask(__name__)
CORS(app)

with open("teamMateGraph3.pkl", "rb") as f:
    G = pickle.load(f)

game_state = {
    'current_player': None,
    'target_player': None,
    'path': [],
    'wrong_guesses': 0,
    'game_over': False,
    'won': False
}

def best_next_nodes(G, start_id, end_id):
    """Finds the 5 best next nodes from start to end in the shortest path"""
    print('getting neighbors')
    neighbors = list(G.neighbors(start_id))  # Get neighboring node IDs
    if not neighbors:
        return []

    # Compute shortest path lengths from each neighbor to the target
    path_lengths = {}
    for neighbor in neighbors:
        try:
            path_lengths[neighbor] = nx.shortest_path_length(G, source=neighbor, target=end_id)
        except nx.NetworkXNoPath:
            path_lengths[neighbor] = float('inf')  # No path to the target
    # Find the minimum remaining path length
    min_length = min(path_lengths.values()) if path_lengths else float('inf')

    # Find best nodes that reduce the path length
    best_nodes = [neighbor for neighbor, length in path_lengths.items() if length < min_length + 1]

    # Find nodes that maintain the same shortest path
    same_length_nodes = [neighbor for neighbor, length in path_lengths.items() if length == min_length + 1]

    # Select up to 5 nodes (all best_nodes, then fill with random same_length_nodes)
    selected_nodes = best_nodes[:]
    if len(selected_nodes) < 5:
        extra_nodes = same_length_nodes[: 5 - len(selected_nodes)]
        selected_nodes.extend(extra_nodes)

    # Convert selected node IDs back to full node dicts
    print("---------------")
    print(selected_nodes)
    output = []
    for element in selected_nodes:
        card = f"{G.nodes[element]['name']} ({G.nodes[element]['first_season']} → {G.nodes[element]['last_season']})"
        output.append(card)
    
    return output
    #return [node for node in G.nodes(data=True) if node[0] in selected_nodes]
def getImage(player_id):
    file_path = "static/images/"+player_id+".jpg"
    if os.path.exists(file_path):
        return "/static/images/"+player_id+".jpg"
    else:
        return "/static/images/default.jpg"

def format_player2(player_id):
    """Format player info for display"""
    player_data = G.nodes[player_id]
    return {
        "name": player_data['name'],
        "years": f"{player_data['first_season']} → {player_data['last_season']}",
        "image": getImage(player_id)
    }
def format_team_years(team_years_dict):
    result = []
    
    for team, years in team_years_dict.items():
        # Sort the years to ensure they're in chronological order
        sorted_years = sorted([int(year) for year in years])
        
        # Initialize variables for tracking ranges
        ranges = []
        range_start = sorted_years[0]
        prev_year = sorted_years[0]
        
        # Iterate through years to find continuous ranges
        for year in sorted_years[1:]:
            if year == prev_year + 1:
                # Continuous range
                prev_year = year
            else:
                # Gap in the range - end the current range
                if range_start == prev_year:
                    ranges.append(str(range_start))
                else:
                    ranges.append(f"{range_start}->{prev_year}")
                
                # Start a new range
                range_start = year
                prev_year = year
        
        # Add the final range
        if range_start == prev_year:
            ranges.append(str(range_start))
        else:
            ranges.append(f"{range_start}->{prev_year}")
        
        # Create the formatted string for this team
        team_str = f"{team}: {', '.join(ranges)}"
        result.append(team_str)
    
    return "\n".join(result)
def get_edge_info(player1, player2):
    """Get edge data between two players"""
    edge_data = G[player1][player2]
    return format_team_years(edge_data['seasons'])
    print(edge_data)
    #return f"{edge_data.get('team', 'unknown team')} ({edge_data.get('years', 'unknown years')})"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    data = request.json
    start_player = data.get('start_player').split(' (')[0]
    end_player = data.get('end_player').split(' (')[0]
    
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
    print('entering sugs')
    sugs = best_next_nodes(G, start_id, end_id)
    return jsonify({
        'current_player': format_player2(start_id),
        'target_player': format_player2(end_id),
        'path': [format_player2(p) for p in game_state['path']],
        'edges': [],
        'wrong_guesses': 0,
        'sugs' : sugs
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
        sugs = best_next_nodes(G, guess_id, game_state['target_player'])
        game_state['path'].append(guess_id)
        game_state['current_player'] = guess_id
        
        edges = [get_edge_info(game_state['path'][i], game_state['path'][i+1]) 
                for i in range(len(game_state['path'])-1)]
        print(edges)
        if guess_id == game_state['target_player']:
            game_state['game_over'] = True
            game_state['won'] = True
            shortest_path = nx.shortest_path(G, game_state['path'][0], game_state['target_player'])
            shortest_edges = [get_edge_info(shortest_path[i], shortest_path[i+1]) 
                           for i in range(len(shortest_path)-1)]
            return jsonify({
                'correct': True,
                'path': [format_player2(p) for p in game_state['path']],
                'edges': edges,
                'game_over': True,
                'won': True,
                'shortest_path': [format_player2(p) for p in shortest_path],
                'shortest_edges': shortest_edges,
            })
            
        return jsonify({
            'correct': True,
            'path': [format_player2(p) for p in game_state['path']],
            'edges': edges,
            'game_over': False,
            'sugs' : sugs
        })
    else:
        game_state['wrong_guesses'] += 1
        if game_state['wrong_guesses'] >= 3:
            game_state['game_over'] = True
            shortest_path = nx.shortest_path(G, game_state['path'][0], game_state['target_player'])
            shortest_edges = [get_edge_info(shortest_path[i], shortest_path[i+1]) 
                           for i in range(len(shortest_path)-1)]
            return jsonify({
                'correct': False,
                'wrong_guesses': game_state['wrong_guesses'],
                'game_over': True,
                'won': False,
                'shortest_path': [format_player2(p) for p in shortest_path],
                'shortest_edges': shortest_edges
            })
        return jsonify({
            'correct': False,
            'wrong_guesses': game_state['wrong_guesses'],
            'game_over': False
        })

@app.route('/go_back', methods=['POST'])
def go_back():
    if len(game_state['path']) <= 1:
        return jsonify({'error': 'Cannot go back from starting player'}), 400
    
    game_state['path'].pop()
    game_state['current_player'] = game_state['path'][-1]
    edges = [get_edge_info(game_state['path'][i], game_state['path'][i+1]) 
            for i in range(len(game_state['path'])-1)]
    
    return jsonify({
        'path': [format_player2(p) for p in game_state['path']],
        'edges': edges,
        'wrong_guesses': game_state['wrong_guesses']
    })

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    matches = [
        f"{data['name']} ({data['first_season']} → {data['last_season']})"
        for player_id, data in G.nodes(data=True)
        if query in data['name'].lower()
    ][:10]
    return jsonify(matches)

@app.route('/static/<path:filename>')
def serve_image(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    if __name__ == "__main__":
        #port = int(os.environ.get("PORT", 5000))
        #app.run(host="0.0.0.0", port=port)
        app.run()
