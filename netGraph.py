import os
import csv
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

def load_csvs(directory_path):
    """
    Load all CSV files from the specified directory.
    Each CSV is expected to have columns: Team, Player_ID, Player_Name
    """
    player_data = []
    for filename in os.listdir(directory_path):
        if filename.endswith('.csv'):
            year = filename.split('.')[0]  # Assuming filename format is YYYY.csv
            with open(os.path.join(directory_path, filename), 'r') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header row
                for row in reader:
                    if len(row) >= 3:
                        team, player_id, player_name = row[0], row[1], row[2]
                        player_data.append({
                            'year': year,
                            'team': team,
                            'player_id': player_id,
                            'player_name': player_name
                        })
        print(str(filename))
    return player_data

def build_graph(player_data):
    """
    Build a graph where:
    - Nodes are players with Player_ID as ID and Player_Name as attribute
    - Edges connect players who played on the same team in the same year
    - Edges have attributes for years and teams played together
    """
    G = nx.Graph()
    
    # Add all players as nodes
    player_ids = set()
    for record in player_data:
        player_id = record['player_id']
        if player_id not in player_ids:
            G.add_node(player_id, name=record['player_name'])
            player_ids.add(player_id)
    
    # Group players by team and year
    team_year_players = defaultdict(list)
    for record in player_data:
        key = (record['team'], record['year'])
        team_year_players[key].append(record['player_id'])
    
    # Create edges for players on the same team
    for (team, year), players in team_year_players.items():
        for i in range(len(players)):
            for j in range(i+1, len(players)):
                player1 = players[i]
                player2 = players[j]
                
                # Check if edge already exists
                if G.has_edge(player1, player2):
                    # Update edge attributes
                    G[player1][player2]['years'].append(year)
                    G[player1][player2]['teams'].append(team)
                else:
                    # Create new edge
                    G.add_edge(player1, player2, years=[year], teams=[team])
    
    return G

def save_graph(G, output_path):
    """
    Save the graph to different formats and visualize
    """
    # Create a copy of the graph for GraphML export
    G_export = G.copy()
    
    # Convert list attributes to strings for GraphML compatibility
    for u, v, data in G_export.edges(data=True):
        if 'years' in data:
            data['years'] = ','.join(data['years'])
        if 'teams' in data:
            data['teams'] = ','.join(data['teams'])
    
    # Save as GraphML for further analysis in other tools
    nx.write_graphml(G_export, f"{output_path}/player_network.graphml")
    
    # Save edge list with attributes
    with open(f"{output_path}/player_edges.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Player1_ID', 'Player2_ID', 'Years', 'Teams'])
        for u, v, data in G.edges(data=True):
            writer.writerow([u, v, ','.join(data['years']), ','.join(data['teams'])])
    
    # Save node list with attributes
    with open(f"{output_path}/player_nodes.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Player_ID', 'Player_Name'])
        for node, data in G.nodes(data=True):
            writer.writerow([node, data['name']])
    
    # Create a basic visualization
    try:
        plt.figure(figsize=(12, 12))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(G, pos, node_size=50, alpha=0.6, edge_color="gray")
        plt.savefig(f"{output_path}/player_network_visualization.png", dpi=300)
        plt.close()
    except Exception as e:
        print(f"Could not create visualization: {e}")

def analyze_graph(G):
    """
    Return basic analysis of the graph
    """
    analysis = {
        'num_players': G.number_of_nodes(),
        'num_connections': G.number_of_edges(),
        'connected_components': nx.number_connected_components(G),
        'avg_connections_per_player': 2 * G.number_of_edges() / G.number_of_nodes()
    }
    
    # Find players with most connections
    player_degrees = sorted(G.degree(), key=lambda x: x[1], reverse=True)
    top_players = []
    
    for player_id, degree in player_degrees[:5]:
        player_name = G.nodes[player_id]['name']
        top_players.append((player_id, player_name, degree))
    
    analysis['top_connected_players'] = top_players
    
    return analysis

def main(input_directory, output_directory):
    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)
    
    # Load all player data from CSVs
    player_data = load_csvs(input_directory)
    print(f"Loaded data for {len(player_data)} player-team records")
    
    # Build the graph
    G = build_graph(player_data)
    print(f"Created graph with {G.number_of_nodes()} players and {G.number_of_edges()} connections")
    
    # Analyze the graph
    analysis = analyze_graph(G)
    print("\nGraph Analysis:")
    print(f"Number of players: {analysis['num_players']}")
    print(f"Number of connections: {analysis['num_connections']}")
    print(f"Number of connected components: {analysis['connected_components']}")
    print(f"Average connections per player: {analysis['avg_connections_per_player']:.2f}")
    
    print("\nPlayers with most connections:")
    for player_id, player_name, degree in analysis['top_connected_players']:
        print(f"{player_name} (ID: {player_id}): {degree} connections")
    
    # Save the graph
    save_graph(G, output_directory)
    print(f"\nGraph files saved to {output_directory}")

if __name__ == "__main__":
    # Replace these with your actual paths
    input_dir = "./historicalRosters"
    output_dir = "./output"
    main(input_dir, output_dir)