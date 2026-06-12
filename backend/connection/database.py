import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# MongoDB Setup
# We pass tlsCAFile directly to avoid custom context parameter restrictions in PyMongo
client = AsyncIOMotorClient(
    os.getenv("MONGO_URI"),
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000
)

db = client[os.getenv("DATABASE_NAME")]

# Neo4j Config
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB = "82e60242"

_driver = None


def get_driver():
    global _driver

    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            connection_timeout=30.0,
            max_connection_lifetime=3600
        )

    return _driver


async def check_mongo_connection():
    try:
        await client.admin.command("ping")
        print("✅ MongoDB connected successfully.")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False


# Collections
citizens_collection = db.citizens
vehicles_collection = db.vehicles
properties_collection = db.properties
tax_records_collection = db.tax_records
utility_records_collection = db.utility_records
travel_records_collection = db.travel_records
datasets_collection = db.datasets
audit_logs_collection = db.audit_logs
risk_scores_collection = db.risk_scores
entity_matches_collection = db.entity_matches