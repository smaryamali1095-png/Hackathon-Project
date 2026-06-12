import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DATABASE_NAME")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# -----------------------
# Existing collections
# -----------------------
users_collection = db.users
alerts_collection = db.alerts

# -----------------------
# Core Intelligence System Collections
# -----------------------

citizens_collection = db.citizens
vehicles_collection = db.vehicles
properties_collection = db.properties
tax_records_collection = db.tax_records
utility_records_collection = db.utility_records

# Dataset management
datasets_collection = db.datasets

# System audit & tracking
audit_logs_collection = db.audit_logs

# Optional (later for scoring system)
risk_scores_collection = db.risk_scores