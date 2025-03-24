import logging
import os
from time import sleep
from collections import defaultdict
import json

import pandas as pd
import requests
from bs4 import BeautifulSoup
from neo4j import GraphDatabase

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

errors = []

# Neo4j Aura connection details - using your provided credentials
# Use a standard bolt connection with explicit port
URI = "neo4j+ssc://93e35fd5.databases.neo4j.io"  
USERNAME = "neo4j"
PASSWORD = "xtxtt-GfyGYJ9b_0iNW_yex1wdc67NUp21XFPmEZX4c"

class NBAGraphDatabase:
    def __init__(self, uri, username, password):
        # Create a driver with encryption enabled and direct connection
        logger.info(f"Connecting to: {uri}")
        self.driver = GraphDatabase.driver(
            uri, 
            auth=(username, password)
        )
        
    def close(self):
        self.driver.close()
    
    def verify_connectivity(self):
        self.driver.verify_connectivity()
        
    def clear_database(self):
        with self.driver.session(database="neo4j") as session:
            session.run("MATCH (n) DETACH DELETE n")
            
    def create_player(self, player_id, player_name):
        with self.driver.session(database="neo4j") as session:
            session.run(
                """
                MERGE (p:Player {id: $id})
                ON CREATE SET p.name = $name
                """,
                id=player_id, name=player_name
            )
            
    def add_team_to_player(self, player_id, team_name, season):
        with self.driver.session(database="neo4j") as session:
            # Create the team if it doesn't exist
            session.run(
                """
                MERGE (t:Team {name: $team_name, season: $season})
                """,
                team_name=team_name, season=season
            )
            
            # Connect player to team
            session.run(
                """
                MATCH (p:Player {id: $id})
                MATCH (t:Team {name: $team_name, season: $season})
                MERGE (p)-[:PLAYED_FOR]->(t)
                """,
                id=player_id, team_name=team_name, season=season
            )
            
    def create_teammate_relationship(self, player1_id, player2_id, team_name, season):
        with self.driver.session(database="neo4j") as session:
            session.run(
                """
                MATCH (p1:Player {id: $player1_id})
                MATCH (p2:Player {id: $player2_id})
                MERGE (p1)-[r:TEAMMATE_WITH]->(p2)
                ON CREATE SET r.seasons = [$season], r.teams = [$team_name]
                ON MATCH SET r.seasons = CASE 
                    WHEN NOT $season IN r.seasons THEN r.seasons + $season 
                    ELSE r.seasons END,
                    r.teams = CASE
                    WHEN NOT $team_name IN r.teams THEN r.teams + $team_name
                    ELSE r.teams END
                """,
                player1_id=player1_id, player2_id=player2_id, season=season, team_name=team_name
            )

# Base URL for Basketball-Reference team rosters
BASE_URL = "https://www.basketball-reference.com"

# Function to scrape a single team's roster for a given season
def scrape_team_roster(team_abbrev, season_year):
    # Season year is the ending year (e.g., 2023 for 2022-23 season)
    url = f"{BASE_URL}/teams/{team_abbrev}/{season_year}.html"
    logger.info(f"Scraping: {url}")
    
    # Send request with a user-agent to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch {url}: Status {response.status_code}")
        if response.status_code == 429:
            print(response.text)
            print(errors)
            exit(0)
        else:
            errors.append((response.status_code,team_abbrev+":"+str(season_year)))
        return []

    # Parse HTML
    soup = BeautifulSoup(response.content, "html.parser")
    print(soup.text)
    # Find the roster table (id="roster")
    roster_table = soup.find("table", {"id": "roster"})
    if not roster_table:
        logger.error(f"No roster table found for {team_abbrev} in {season_year}")
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

# Function to add team roster to Neo4j graph
def add_team_to_graph(db, team_players, team_name, season):
    # Add players as nodes
    for player in team_players:
        player_id = player["id"]
        player_name = player["name"]
        
        # Create player node if it doesn't exist
        db.create_player(player_id, player_name)
        
        # Add team relationship
        db.add_team_to_player(player_id, team_name, season)
    
    # Add edges between all pairs of players on the team
    for i in range(len(team_players)):
        for j in range(i + 1, len(team_players)):
            player1_id, player2_id = team_players[i]["id"], team_players[j]["id"]
            db.create_teammate_relationship(player1_id, player2_id, team_name, season)
            # Also create the relationship in the opposite direction
            db.create_teammate_relationship(player2_id, player1_id, team_name, season)

    # Try multiple connection URIs
    connection_uris = [
        "neo4j+ssc://93e35fd5.databases.neo4j.io"
    ]
    
    for uri in connection_uris:
        try:
            logger.info(f"Trying connection with: {uri}")
            driver = GraphDatabase.driver(
                uri, 
                auth=(USERNAME, PASSWORD),
            )
            
            # Test connection
            driver.verify_connectivity()
            logger.info(f"✓ Connection successful with {uri}")
            
            # Try a simple query
            with driver.session(database="neo4j") as session:
                result = session.run("RETURN 'Connected!' AS message")
                message = result.single()["message"]
                logger.info(f"Query result: {message}")
            
            driver.close()
            return uri
            
        except Exception as e:
            logger.error(f"× Connection failed with {uri}: {e}")
    
    return None

def get_teams_by_year():
    # Base URL
    base_url = "https://www.basketball-reference.com/leagues/"
    
    # Initialize dictionary with defaultdict to handle multiple leagues
    teamsByYear = defaultdict(set)  # Using set to avoid duplicates
    
    # Headers to mimic browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Get the main league index page
    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch main page: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all season links in the table
    table = soup.find('table', {'id': 'stats'})
    if not table:
        print("Could not find leagues table")
        return
    else:
        print(table.contents)    
    
    # Process each row
    print(table.find('tbody').find_all('tr'))
    for row in table.find('tbody').find_all('tr'):
        season_cell = row.find('th')
        if not season_cell or not season_cell.a:
            continue
            
        season_text = season_cell.text.strip()
        # Extract year (e.g., "2024-25" -> 2024)
        try:
            end_year = int(season_text.split('-')[1]) + 2000 if '-' in season_text else int(season_text)
            if end_year < 1947 or end_year > 2024:
                continue
        except (ValueError, IndexError):
            continue
            
        league = row.find('td', {'data-stat': 'lg_id'}).text.strip()
        season_url = base_url + season_cell.a['href'].split('/')[-1]
        
        # Fetch the season page
        season_response = requests.get(season_url, headers=headers)
        if season_response.status_code != 200:
            print(f"Failed to fetch {season_url}: {season_response.status_code}")
            continue
            
        season_soup = BeautifulSoup(season_response.content, 'html.parser')
        
        # Find standings tables (could be multiple for ABA years)
        standings_tables = season_soup.find_all('table', class_='stats_table')
        
        for table in standings_tables:
            # Check if it's a standings table
            if 'standings' in table.get('id', ''):
                for team_row in table.find('tbody').find_all('tr'):
                    team_cell = team_row.find('td', {'data-stat': 'team_name'})
                    if team_cell and team_cell.a:
                        # Get team abbreviation from the URL
                        team_url = team_cell.a['href']
                        team_abbr = team_url.split('/')[-2]
                        # Map to end year (e.g., 2023-24 season maps to 2024)
                        year = end_year
                        teamsByYear[year].add(team_abbr)
        sleep(3)
        print('processed '+year)
    # Convert sets to sorted lists for final output
    teamsByYear_dict = {year: sorted(list(teams)) for year, teams in teamsByYear.items()}
    
    return teamsByYear_dict


def main():
    try:
        logger.info("Testing Neo4j Aura connection...")
        
        
        # Initialize Neo4j database connection
        db = NBAGraphDatabase("neo4j+ssc://93e35fd5.databases.neo4j.io", USERNAME, PASSWORD)
        
        # Optional: Clear existing data (comment out if you want to append instead)
        logger.info("Clearing existing data...")
        #db.clear_database()
        
        # List of NBA team abbreviations (example subset; expand as needed)
        # Full list: https://en.wikipedia.org/wiki/Wikipedia:Basketball_Reference.com_NBA_team_abbreviations
        """
        nba_teams = ["CLE", "BOS", "NYK","MIL", "IND","DET","MIA","ORL","ATL", "CHI","BRK","PHI","TOR","CHO","WAS"
                     ,"OKC","LAL","DEN","MEM","HOU","GSW","MIN","LAC","SAC","DAL","PHO","POR","SAS","NOP","UTA",
                     "NOH", "NJN", "SEA", "CHH", "NOK","NOH","VAN","KCK", "KCO","SDC","WSB"]  # Add more teams here
        nba_teams = ['BOS', 'NYK','WSC','PHW', 'PRO','TRH','CHS','STB','CLR','DTF','PIT','BLB','ROC','MNL','FTW','INJ']"
        """
        # Scrape a single season (e.g., 2023 for 2022-23)
        with open('teamYears1967.json', 'r') as file:
            basketball_data = json.load(file)
        teams_per_year = {}
        team_rosters = {}
        seasons = [2025]
        for season in seasons:#range(2025,2026):
            nba_teams = basketball_data[str(season)]
            team_rosters = {}
            logger.info(f"scraping {season}...")
            for team in nba_teams:
                players = scrape_team_roster(team, season)
                logger.info(f"Found {len(players)} players for {team}")
                if players:
                    team_rosters[team] = players
                    #add_team_to_graph(db, players, team, season)
                sleep(3)  # Polite delay to avoid overwhelming the server
            teams_per_year[season] = (len(team_rosters),list(team_rosters.keys()))
            
        # Close database connection
            
        
        # Optional: Export rosters to CSV for inspection
            roster_data = [(team, player["id"], player["name"]) 
                        for team, players in team_rosters.items() 
                        for player in players]
            roster_df = pd.DataFrame(roster_data, columns=["Team", "Player_ID", "Player_Name"])
            roster_df.to_csv(f"historicalRosters2/nba_rosters_{season}.csv", index=False)
            logger.info(f"Rosters saved to nba_rosters_{season}.csv")
            
        db.close()
        logger.info("All done! Data has been stored in Neo4j Aura.")
        print(errors)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()