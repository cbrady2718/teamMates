import dotenv
import os
from neo4j import GraphDatabase

load_status = dotenv.load_dotenv("Neo4j-93e35fd5-Created-2025-03-06.txt")
if load_status is False:
    raise RuntimeError('Environment variables not loaded.')

URI = "neo4j+ssc://93e35fd5.databases.neo4j.io"
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("Connection established.")