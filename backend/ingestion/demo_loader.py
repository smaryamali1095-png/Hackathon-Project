import pandas as pd
from connection.database import (
    get_driver, NEO4J_DB,
    citizens_collection, vehicles_collection,
    properties_collection, tax_records_collection, utility_records_collection
)

def load_csv(path):
    return pd.read_csv(path)

async def upsert_citizen(cnic, name=None):
    if not cnic: return
    await citizens_collection.update_one(
        {"cnic": str(cnic)},
        {"$setOnInsert": {"cnic": str(cnic), "name": name}},
        upsert=True
    )

async def insert_vehicles(df):
    driver = get_driver()
    for _, row in df.iterrows():
        await upsert_citizen(row["cnic"], row.get("owner_name"))
        await vehicles_collection.update_one({"vehicle_reg_no": row["vehicle_reg_no"]}, {"$set": row.to_dict()}, upsert=True)
        with driver.session(database=NEO4J_DB) as session:
            session.run("""
                MERGE (c:Citizen {cnic: $cnic})
                MERGE (v:Vehicle {reg_no: $reg_no})
                SET v.make_model = $model, v.engine_cc = $cc
                MERGE (c)-[:OWNS]->(v)
            """, cnic=str(row["cnic"]), reg_no=str(row["vehicle_reg_no"]), model=row["vehicle_make_model"], cc=row["engine_capacity_cc"])

async def insert_properties(df):
    driver = get_driver()
    for _, row in df.iterrows():
        await upsert_citizen(row["cnic"], row.get("buyer_name"))
        await properties_collection.update_one({"registry_no": row["registry_no"]}, {"$set": row.to_dict()}, upsert=True)
        with driver.session(database=NEO4J_DB) as session:
            session.run("""
                MERGE (c:Citizen {cnic: $cnic})
                MERGE (p:Property {registry_no: $reg})
                SET p.address = $addr, p.value = $val, p.type = $type
                MERGE (c)-[:OWNS]->(p)
            """, cnic=str(row["cnic"]), reg=str(row["registry_no"]), addr=row["property_address"], val=row["property_value_pkr"], type=row["property_type"])

async def insert_tax_records(df):
    driver = get_driver()
    for _, row in df.iterrows():
        await upsert_citizen(row["cnic"], row.get("full_name"))
        await tax_records_collection.update_one({"fbr_id": row["fbr_id"]}, {"$set": row.to_dict()}, upsert=True)
        with driver.session(database=NEO4J_DB) as session:
            session.run("""
                MERGE (c:Citizen {cnic: $cnic})
                SET c.tax_status = $status, c.declared_income = $income
            """, cnic=str(row["cnic"]), status=row["filter_status"], income=row["declared_income_pkr"])

async def insert_utilities(df):
    driver = get_driver()
    for _, row in df.iterrows():
        await upsert_citizen(row["cnic"], row.get("consumer_name"))
        await utility_records_collection.update_one({"meter_ref_no": row["meter_ref_no"]}, {"$set": row.to_dict()}, upsert=True)
        with driver.session(database=NEO4J_DB) as session:
            session.run("""
                MERGE (c:Citizen {cnic: $cnic})
                MERGE (u:Utility {meter_ref: $meter})
                SET u.type = $type, u.avg_bill = $bill
                MERGE (c)-[:USES]->(u)
            """, cnic=str(row["cnic"]), meter=str(row["meter_ref_no"]), type=row["connection_type"], bill=row["avg_monthly_bill_pkr"])
async def run_demo_loader():
    # Load the files
    vehicle_df = load_csv("data/demo/excise_vehicles.csv")
    property_df = load_csv("data/demo/property_transfers.csv")
    tax_df = load_csv("data/demo/fbr_tax_records.csv")
    util_df = load_csv("data/demo/disco_consumption.csv")

    # Execute inserts - The driver connects automatically here
    await insert_vehicles(vehicle_df)
    await insert_properties(property_df)
    await insert_tax_records(tax_df)
    await insert_utilities(util_df)

    print("✅ Demo dataset loaded successfully")