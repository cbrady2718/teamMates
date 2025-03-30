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


def get_player_score(player_id):
    time.sleep(3)
    # Construct the URL for the player's Basketball Reference page
    url = f"https://www.basketball-reference.com/players/{player_id[0]}/{player_id}.html"
    # Set headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    print(url)
        # Get the page content
    response = requests.get(url, headers=headers)
    response.raise_for_status()
        # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find("table", {"id": "advanced"})
    if not table:
        print("Advanced stats table not found.")
        return {}
    score = 0
    ws = []
    for row in table.find("tbody").find_all("tr", class_=lambda x: x != "thead"):
        season = row.find("th").text.strip()
        ws_cell = row.find("td", {"data-stat": "ws"})
        if ws_cell and ws_cell.text.strip():
            ws.append(float(ws_cell.text.strip()))
    maxws = float(.41568)*max(ws)
    print(f'max win share: {maxws}')
    score += float(.41568)*max(ws)

        # Find the image in the media-item div
    bling = soup.find("ul", id="bling")
    if bling:
        li_elements = bling.find_all('li')

            # Extract text from each <li>
        text_entries = [li.text.strip() for li in li_elements]
        for element in text_entries:
            element = str(element)
            if "BA Champ" in element:
                if "x" in element.lower():
                    var = float(element.split("x")[0])
                    print(f'{var} championships')
                    score += float(.80573)*float(element.split("x")[0])
                else:
                    print('1 championship')
                    score += float(.80573)
            else:
                print('no championships')
            if "all star" in element.lower():
                var = int(element.split("x")[0])
                if "X" in element.lower():
                    print(f'{var} all star appearances')
                    score += float(1.0244)*int(element.split("x")[0])
                else:
                    print("1 all star appearance")
                    score += float(1.0244)
            else:
                print('no all stars')
        
    else:
        print('no championships')
        print("no all stars")
    return score
if __name__ == "__main__":
    with open("../teamMateGraph4.pkl", "rb") as f:
        G = pickle.load(f)
    player_ids = list(G.nodes()) 
    scores = {}
    with open("player_scores.txt", "a") as file_a:
        file_a.write(f"player_id, score\n")
        i = 0
        for player in player_ids:
            if i > 4:
                top_5 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
                for element in top_5:
                    print(f'{element[0]}: {element[1]}')
            i += 1
            val = get_player_score(player)
            print(f'final score: {val}')
            scores[str(G.nodes[player]["name"])] = val
            file_a.write(f"{player},{val}\n")