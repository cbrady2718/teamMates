import os
import csv
import networkx as nx
import pickle

# Initialize the graph
G = nx.Graph()

def process_nba_rosters(directory_path):
    # Loop through files in the directory
    for filename in os.listdir(directory_path):
        if filename.startswith('nba_rosters_') and filename.endswith('.csv'):
            # Extract year from filename
            year = filename.split('_')[2].split('.')[0]
            season = year  # You can modify this to format season differently if needed
            
            file_path = os.path.join(directory_path, filename)
            
            # Dictionary to store teams and their players
            teams = {}
            
            # Read CSV file
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                # Ensure the CSV has the expected columns
                if not all(col in reader.fieldnames for col in ['Team', 'Player_ID', 'Player_Name']):
                    print(f"Warning: {filename} missing required columns")
                    continue
                
                # Group players by team
                for row in reader:
                    team = row['Team']
                    if team not in teams:
                        teams[team] = []
                    teams[team].append({
                        'id': row['Player_ID'],
                        'name': row['Player_Name']
                    })
            
            # Process each team
            for team_name, team_players in teams.items():
                add_team_to_graph(team_players, team_name, season)
            
            print(f"Processed {filename}")

def add_team_to_graph(team_players, team_name, season):
    # Add players as nodes using their IDs, with name as an attribute
    for player in team_players:
        player_id = player["id"]
        player_name = player["name"]
        team_season = f"{team_name}_{season}"  # Create a unique team-season identifier
        
        if not G.has_node(player_id):
            # Initialize with sets for teams and seasons
            G.add_node(player_id, 
                      name=player_name, 
                      teams={team_season},  # Start with team_season instead of just team_name
                      seasons={season},
                      first_season=season,
                      last_season= season)
        else:
            # Update existing node attributes
            G.nodes[player_id]["teams"].add(team_name)  # Add team_season instead of team_name_season
            G.nodes[player_id]["seasons"].add(season)
            if season < G.nodes[player_id]["first_season"]:
                G.nodes[player_id]["first_season"] = season
            if season > G.nodes[player_id]["last_season"]:
                G.nodes[player_id]["last_season"] = season
    
    # Add edges between all pairs of players on the team using their IDs
    for i in range(len(team_players)):
        for j in range(i + 1, len(team_players)):
            player1_id, player2_id = team_players[i]["id"], team_players[j]["id"]
            G.add_edge(player1_id, player2_id)
            if "seasons" not in G[player1_id][player2_id]:
                G[player1_id][player2_id]["seasons"] = {}
            if team_name not in G[player1_id][player2_id]["seasons"]:
                G[player1_id][player2_id]["seasons"][team_name] = []
            G[player1_id][player2_id]["seasons"][team_name].append(season)
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
if __name__ == "__main__":
    # Replace with your actual directory path
    directory_path = "/Users/chrbrady/Desktop/teamMates/historicalRosters2"
    process_nba_rosters(directory_path)


    analysis = analyze_graph(G)
    print("\nGraph Analysis:")
    print(f"Number of players: {analysis['num_players']}")
    print(f"Number of connections: {analysis['num_connections']}")
    print(f"Number of connected components: {analysis['connected_components']}")
    print(f"Average connections per player: {analysis['avg_connections_per_player']:.2f}")
    
    print("\nPlayers with most connections:")
    for player_id, player_name, degree in analysis['top_connected_players']:
        print(f"{player_name} (ID: {player_id}): {degree} connections")
    #nx.write_gml(G, f"nba_teammate_graph.gml")
    with open("teamMateGraph3.pkl", "wb") as f:
        pickle.dump(G, f)
    #with open("teamMateGraph2.pkl", "rb") as f:
    #    G = pickle.load(f)

# Optional: Print some stats    
    # Optional: Print some stats about the graph
    print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")