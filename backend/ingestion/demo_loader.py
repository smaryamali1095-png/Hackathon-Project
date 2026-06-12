import pandas as pd
import os
import ssl
from dotenv import load_dotenv
from neo4j import GraphDatabase

from connection.database import (
    citizens_collection,
    vehicles_collection,
    properties_collection,
    tax_records_collection,
    utility_records_collection
)

load_dotenv()

def get_driver():
    # Use bolt:// to permit manual SSL context handling
    uri = os.getenv("NEO4J_URI").replace("neo4j+s://", "bolt://").replace("bolt+s://", "bolt://")
    
    # Create an SSL context that ignores local CA verification 
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    return GraphDatabase.driver(
        uri, 
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
        ssl_context=context
    )

driver = get_driver()

def load_csv(path):
    return pd.read_csv(path)

async def upsert_citizen(cnic, name=None):
    if not cnic: return
    await citizens_collection.update_one(
        {"cnic": cnic},
        {"$setOnInsert": {"cnic": cnic, "name": name}},
        upsert=True
    )

async def insert_vehicles(df):
    for _, row in df.iterrows():
        await upsert_citizen(row["cnic"], row.get("owner_name"))
        await vehicles_collection.update_one(
            {"vehicle_reg_no": row["vehicle_reg_no"]},
            {"$set": row.to_dict()},
            upsert=True
        )
        # Removed database parameter to allow Aura to auto-route
        with driver.session() as session:
            session.run("""
                MERGE (c:Citizen {cnic: $cnic})
                MERGE (v:Vehicle {reg_no: $reg_no})
                MERGE (c)-[:OWNS]->(v)
            """, cnic=row["cnic"], reg_no=row["vehicle_reg_no"])

async def insert_properties(df):
    for _, row in df.iterrows():
        await upsert_citizen(row["cnic"], row.get("buyer_name"))
        await properties_collection.update_one(
            {"registry_no": row["registry_no"]},
            {"$set": row.to_dict()},
            upsert=True
        )
        # Removed database parameter to allow Aura to auto-route
        with driver.session() as session:
            session.run("""
                MERGE (c:Citizen {cnic: $cnic})
                MERGE (p:Property {registry_no: $reg})
                MERGE (c)-[:OWNS]->(p)
            """, cnic=row["cnic"], reg=row["registry_no"])

async def insert_tax_records(df):
    for _, row in df.iterrows():
        await upsert_citizen(row["cnic"], row.get("full_name"))
        await tax_records_collection.update_one(
            {"fbr_id": row["fbr_id"]},
            {"$set": row.to_dict()},
            upsert=True
        )

async def insert_utilities(df):
    for _, row in df.iterrows():
        await upsert_citizen(row["cnic"], row.get("consumer_name"))
        await utility_records_collection.update_one(
            {"meter_ref_no": row["meter_ref_no"]},
            {"$set": row.to_dict()},
            upsert=True
        )

async def run_demo_loader():
    try:
        driver.verify_connectivity()
        print("✅ Neo4j Connection Verified!")
        
        vehicle_df = load_csv("data/demo/excise_vehicles.csv")
        property_df = load_csv("data/demo/property_transfers.csv")
        tax_df = load_csv("data/demo/fbr_tax_records.csv")
        util_df = load_csv("data/demo/disco_consumption.csv")

        await insert_vehicles(vehicle_df)
        await insert_properties(property_df)
        await insert_tax_records(tax_df)
        await insert_utilities(util_df)

        print("✅ Demo dataset loaded successfully")
    except Exception as e:
        print(f"❌ Critical error during data ingestion: {e}")