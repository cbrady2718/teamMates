import requests
from bs4 import BeautifulSoup

def get_win_shares(player_url):
    """
    Scrapes the single-season Win Shares (WS) from a Basketball-Reference player page.
    
    Args:
        player_url (str): The relative URL of the player's page (e.g., "/players/j/jordami01.html")

    Returns:
        dict: A dictionary with seasons as keys and WS as values.
    """
    base_url = "https://www.basketball-reference.com"
    url = base_url + player_url

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve data: {response.status_code}")
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the advanced stats table
    table = soup.find("table", {"id": "advanced"})
    if not table:
        print("Advanced stats table not found.")
        return {}

    win_shares = {}
    for row in table.find("tbody").find_all("tr", class_=lambda x: x != "thead"):
        season = row.find("th").text.strip()
        ws_cell = row.find("td", {"data-stat": "ws"})
        
        if ws_cell and ws_cell.text.strip():
            win_shares[season] = float(ws_cell.text.strip())

    return win_shares

# Example usage: Michael Jordan's page
player_url = "/players/j/jordami01.html"
win_shares = get_win_shares(player_url)
print(win_shares)