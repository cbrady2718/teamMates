import requests
from bs4 import BeautifulSoup
import re
import pickle
import time
import networkx as nx

# with open("../teamMateGraph4.pkl", "rb") as f:
#     G = pickle.load(f)
# tot = 0
# count = 0
# for player_id in G.nodes:
#     tot += 1
#     if G.nodes[player_id]["HOF"] == True:
#         count += 1

def download_player_photo(player_id):
    # Construct the URL for the player's Basketball Reference page
    url = f"https://www.basketball-reference.com/players/{player_id[0]}/{player_id}.html"
    
    try:
        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Get the page content
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the image in the media-item div
        bling = soup.find("ul", id="bling")
        li_elements = bling.find_all('li')

        # Extract text from each <li>
        text_entries = [li.text.strip() for li in li_elements]
        for element in text_entries:
            
        print(text_entries)
    except:
        print("hi")
download_player_photo("holidjr01")