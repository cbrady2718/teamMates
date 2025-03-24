import requests
from bs4 import BeautifulSoup
from time import sleep
import json

def get_team_abbreviations(year):
    leagues = []
    if int(year) < 1950:
        leagues = ['BAA']
    elif int(year) < 1977 and int(year) > 1967:
        leagues = ['NBA','ABA']
    else:
        leagues = ['NBA']
    print(year)
    print(leagues)
    #f"https://www.basketball-reference.com/leagues/NBA_{year}.html"
    teams = set()
    for league in leagues:
        sleep(3)
        url = f"https://www.basketball-reference.com/leagues/{league}_{year}.html"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Failed to retrieve data for {year}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all tables that contain standings
        for table in soup.find_all("table"):
            for row in table.find_all("tr")[1:]:  # Skip header row
                team_link = row.find("a")
                if team_link:
                    # Extract team abbreviation from URL
                    team_abbr = team_link["href"].split("/")[-2].upper()
                    teams.add(team_abbr)
    return list(sorted(teams))

if __name__ == "__main__":
    diction = {}
    for element in range(1920,2025):
        teams = []
        teams = get_team_abbreviations(element)
        print(teams)
        diction[element] = teams
    print(diction)
    with open("teamYears.json", "w") as file:
        json.dump(diction, file, indent=4)

#1967
