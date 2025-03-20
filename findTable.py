import requests
from bs4 import BeautifulSoup
import json
from time import sleep

# Headers to mimic a browser request and avoid potential blocking
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Function to scrape team abbreviations for a given season
def get_team_abbreviations(season):
    # Format season (e.g., "1947" for 1946-47 season)
    end_year = season.split("-")[1]
    url = f"https://www.basketball-reference.com/leagues/NBA_{end_year}.html"
    
    # Fetch the page content
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch {url} - Status code: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the standings table (Eastern or Western Conference, or combined in early years)
    standings_table = soup.find("table", {"id": "divs_standings_"}) or soup.find("table", {"id": "standings"})
    
    if not standings_table:
        print(f"No standings table found for {season}")
        return []
    
    # Extract team abbreviations from the table
    team_abbrs = []
    for row in standings_table.find_all("tr"):
        team_cell = row.find("th", {"data-stat": "team_name"}) or row.find("td", {"data-stat": "team_name"})
        if team_cell and team_cell.find("a"):
            team_link = team_cell.find("a")["href"]
            # Extract abbreviation from URL (e.g., /teams/BOS/1947.html -> BOS)
            abbr = team_link.split("/")[2]
            if abbr not in team_abbrs:  # Avoid duplicates
                team_abbrs.append(abbr)
    
    return sorted(team_abbrs)


# Generate seasons from 1946-47 to 2024-25
def generate_seasons():
    seasons = []
    for year in range(1946, 2025):
        season = f"{year}-{str(year + 1)[-2:]}"
        seasons.append(season)
    return seasons

# Main function to scrape and save data
def scrape_nba_teams():
    seasons = generate_seasons()
    team_data = {}
    
    for season in seasons:
        print(f"Scraping teams for {season}...")
        teams = get_team_abbreviations(season)
        if teams:
            team_data[season] = teams
        # Sleep to avoid overwhelming the server (respect rate limits)
        sleep(3)  # Basketball-Reference allows ~20 requests/minute, so 3s is safe
    
    # Save to JSON file
    with open("nba_team_abbreviations.json", "w") as f:
        json.dump(team_data, f, indent=4)
    print("Data saved to nba_team_abbreviations.json")

# Run the script
if __name__ == "__main__":
    scrape_nba_teams()