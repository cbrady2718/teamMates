import requests
from bs4 import BeautifulSoup
import networkx as nx
import pandas as pd
from time import sleep


skipped = []
errors = []
# Initialize the graph
G = nx.Graph()

# Base URL for Basketball-Reference team rosters
BASE_URL = "https://www.basketball-reference.com"

# Function to scrape a single team's roster for a given season
def scrape_team_roster(team_abbrev, season_year):
    # Season year is the ending year (e.g., 2023 for 2022-23 season)
    url = f"{BASE_URL}/teams/{team_abbrev}/{season_year}.html"
    print(f"Scraping: {url}")
    
    # Send request with a user-agent to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch {url}: Status {response.status_code}")
        if response.status_code == 429:
            skipped.append(url)
        else:
            errors.append((url,response.status_code))
        return []

    # Parse HTML
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find the roster table (id="roster")
    roster_table = soup.find("table", {"id": "roster"})
    if not roster_table:
        print(f"No roster table found for {team_abbrev} in {season_year}")
        return []

    # Extract player IDs and names from the table
    players = []
    for row in roster_table.find("tbody").find_all("tr"):
        player_cell = row.find("td", {"data-stat": "player"})
        if player_cell and player_cell.find("a"):
            # Get the player's URL and extract the ID (e.g., "/players/j/jordami01.html" -> "jordami01")
            player_url = player_cell.find("a")["href"]
            player_id = player_url.split("/")[-1].replace(".html", "")
            player_name = player_cell.text.strip()
            players.append({"id": player_id, "name": player_name})
    
    return players

# Function to add team roster to graph
def add_team_to_graph(team_players, team_name, season):
    # Add players as nodes using their IDs, with name as an attribute
    for player in team_players:
        player_id = player["id"]
        player_name = player["name"]
        if not G.has_node(player_id):
            G.add_node(player_id, name=player_name, teams={f"{team_name}"}, seasons={season})
        else:
            # Update attributes for existing nodes
            G.nodes[player_id]["teams"].add(f"{team_name}_{season}")
            G.nodes[player_id]["seasons"].add(season)
    
    # Add edges between all pairs of players on the team using their IDs
    for i in range(len(team_players)):
        for j in range(i + 1, len(team_players)):
            player1_id, player2_id = team_players[i]["id"], team_players[j]["id"]
            G.add_edge(player1_id, player2_id)
            # Optionally add edge attributes (e.g., seasons they were teammates)
            if "seasons" not in G[player1_id][player2_id]:
                G[player1_id][player2_id]["seasons"] = set()
            G[player1_id][player2_id]["seasons"].add(season)

# List of NBA team abbreviations (example subset; expand as needed)
# Full list: https://en.wikipedia.org/wiki/Wikipedia:Basketball_Reference.com_NBA_team_abbreviations
nba_teams = ["CHI", "BOS", "LAL", "NYK", "GSW"]  # Add more teams here

# Scrape a single season (e.g., 2023 for 2022-23)
season = 2023
team_rosters = {}

for team in nba_teams:
    players = scrape_team_roster(team, season)
    print(players)
    if players:
        team_rosters[team] = players
        add_team_to_graph(players, team, season)
    sleep(2)  # Polite delay to avoid overwhelming the server

# Save the graph to a file
nx.write_gml(G, f"nba_teammate_graph_{season}.gml")


# Optional: Print some stats
print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

# Optional: Export rosters to CSV for inspection
roster_data = [(team, player["id"], player["name"]) 
               for team, players in team_rosters.items() 
               for player in players]
roster_df = pd.DataFrame(roster_data, columns=["Team", "Player_ID", "Player_Name"])
roster_df.to_csv(f"nba_rosters_{season}.csv", index=False)
print(f"Rosters saved to nba_rosters_{season}.csv")