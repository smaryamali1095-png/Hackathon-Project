import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

class Neo4jConnection:
    def __init__(self):
        # 1. Force use of bolt+s (Direct connection, not cluster routing)
        uri = os.getenv("NEO4J_URI").replace("neo4j+s://", "bolt+s://")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        try:
            # 2. Initialize the driver
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            
            # 3. Verify specifically without routing
            self.driver.verify_connectivity()
            print("✅ Successfully connected to Neo4j Aura (Direct)!")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            raise e