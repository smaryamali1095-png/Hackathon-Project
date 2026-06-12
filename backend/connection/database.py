import os
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# MongoDB Setup
client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME")]

# Neo4j Config
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB = "82e60242"

# Global variable
_driver = None

def get_driver():
    global _driver  # <--- THIS IS THE CRITICAL LINE
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            connection_timeout=30.0,
            max_connection_lifetime=3600
        )
    return _driver

# Collections
citizens_collection = db.citizens
vehicles_collection = db.vehicles
properties_collection = db.properties
tax_records_collection = db.tax_records
utility_records_collection = db.utility_records
datasets_collection = db.datasets
audit_logs_collection = db.audit_logs
risk_scores_collection = db.risk_scores