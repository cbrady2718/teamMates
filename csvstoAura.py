import glob

import pandas as pd
from neo4j import GraphDatabase

# Neo4j Connection Details
URI = "neo4j+ssc://93e35fd5.databases.neo4j.io"  
USERNAME = "neo4j"
PASSWORD = "xtxtt-GfyGYJ9b_0iNW_yex1wdc67NUp21XFPmEZX4c"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
def create_constraints(tx):
    """Create indexes and constraints to speed up operations."""
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Player) REQUIRE p.id IS UNIQUE")

def batch_insert_players(tx, players):
    """Batch insert player nodes."""
    query = """
    UNWIND $players AS player
    MERGE (p:Player {id: player.id})
    SET p.name = player.name
    """
    tx.run(query, players=players)

def batch_insert_teammates(tx, relationships):
    """Batch insert or update teammate relationships."""
    query = """
    UNWIND $relationships AS rel
    MATCH (p1:Player {id: rel.player1})
    MATCH (p2:Player {id: rel.player2})
    MERGE (p1)-[r:teamMatesWith]-(p2)
    ON CREATE SET r.teams = [rel.team], r.years = [rel.year]
    ON MATCH SET r.teams = CASE 
        WHEN NOT rel.team IN r.teams THEN r.teams + rel.team 
        ELSE r.teams 
    END,
    r.years = CASE 
        WHEN NOT rel.year IN r.years THEN r.years + rel.year 
        ELSE r.years 
    END
    """
    tx.run(query, relationships=relationships)

def process_csv_files():
    """Reads all roster CSVs and efficiently loads the graph."""
    with driver.session() as session:
        session.execute_write(create_constraints)  # Create constraints once

        for file in glob.glob("historicalRosters/nba_rosters_*.csv"):
            year = file.split("_")[-1].split(".")[0]  # Extract year
            df = pd.read_csv(file)

            # Group players by team
            team_groups = df.groupby("Team")["Player_ID", "Player_Name"].apply(lambda x: x.values.tolist())

            players = set()  # To store unique players
            relationships = []  # To store teammate relationships

            for team, roster in team_groups.items():
                # Collect player nodes
                for player_id, player_name in roster:
                    players.add((player_id, player_name))

                # Collect teammate relationships (avoid duplicates)
                for i in range(len(roster)):
                    for j in range(i + 1, len(roster)):  # Only unique pairs
                        p1_id, _ = roster[i]
                        p2_id, _ = roster[j]
                        relationships.append({"player1": p1_id, "player2": p2_id, "team": team, "year": year})
            print(players)
            # Batch insert players
            session.execute_write(batch_insert_players, [{"id": p[0], "name": p[1]} for p in players])

            # Batch insert relationships in chunks (to prevent memory overload)
            chunk_size = 5000
            for i in range(0, len(relationships), chunk_size):
                session.execute_write(batch_insert_teammates, relationships[i:i+chunk_size])

if __name__ == "__main__":
    process_csv_files()
    print("Optimized graph creation complete!")

driver.close()
