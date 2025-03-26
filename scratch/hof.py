import requests
from bs4 import BeautifulSoup
import re
import pickle

# URL of the Pro Football Hall of Fame page
hof_url = 'https://www.basketball-reference.com/awards/hof.html'

# Fetch the page content
response = requests.get(hof_url)
response.raise_for_status()  # Ensure the request was successful

# Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

# Find all player links within the correct table
hof_table = soup.find('table', {'id': 'hof'})
#player_links = hof_table.find_all('a', href=True)  # Find all links within the table
player_links = [a['href'] for a in hof_table.find_all('a', href=True) if "/players/" in a['href']]
player_links = [
    a['href'] for a in hof_table.find_all('a', href=True) 
    if "players" in a['href'] and "www.sports-reference.com" not in a['href']
]
hof_player_ids = []
for element in player_links:
    out = element.split('/')[-1]
    hof_player_ids.append(out[:-5])
    print(out[:-5])
print(hof_player_ids)
# Output the list of player_ids
with open("teamMateGraph3.pkl", "rb") as f:
    G = pickle.load(f)

for player_id in G.nodes:
    G.nodes[player_id]["HOF"] = player_id in hof_player_ids


with open("teamMateGraph4.pkl", "wb") as f:
    pickle.dump(G, f)


check_players = ["piercpa01", "tatumja01"]

# Print their HOF status
for player_id in check_players:
    if player_id in G.nodes:
        print(f"{player_id}: HOF = {G.nodes[player_id]['HOF']}")
    else:
        print(f"{player_id} not found in graph")

        