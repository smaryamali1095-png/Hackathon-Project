import pandas as pd
from connection.database import (
    get_driver,
    citizens_collection,
    vehicles_collection,
    properties_collection,
    tax_records_collection,
    utility_records_collection,
    datasets_collection
)
from services.citizen_service import process_csv_file

def load_csv(path):
    return pd.read_csv(path, encoding="utf-8-sig")


def clean_row(row):
    data = row.to_dict()
    return {k: None if pd.isna(v) else v for k, v in data.items()}


def estimate_vehicle_value(model, engine_cc, year):
    model = str(model).lower()

    if any(x in model for x in ["land cruiser", "prado", "bmw", "audi", "mercedes", "range rover"]):
        base = 30000000
    elif any(x in model for x in ["civic", "sportage", "tucson", "corolla"]):
        base = 8000000
    else:
        base = 2500000

    age_factor = max(0.45, 1 - ((2026 - int(year)) * 0.05))
    cc_factor = max(1, int(engine_cc) / 1000)

    return int(base * age_factor * cc_factor)


def neo4j_dataset_has_data(dataset_name):
    driver = get_driver()

    queries = {
        "vehicles": "MATCH (v:Vehicle) RETURN count(v) AS count",
        "properties": "MATCH (p:Property) RETURN count(p) AS count",
        "tax": "MATCH (t:TaxRecord) RETURN count(t) AS count",
        "utilities": "MATCH (u:Utility) RETURN count(u) AS count"
    }

    with driver.session() as session:
        result = session.run(queries[dataset_name]).single()
        return result["count"] > 0


async def should_skip_dataset(dataset_name):
    existing = await datasets_collection.find_one({
        "name": dataset_name,
        "status": "loaded"
    })

    neo4j_has_data = neo4j_dataset_has_data(dataset_name)

    if existing and neo4j_has_data:
        return True

    return False


async def mark_dataset_loaded(dataset_name, path, records_count):
    await datasets_collection.update_one(
        {"name": dataset_name},
        {
            "$set": {
                "name": dataset_name,
                "status": "loaded",
                "path": path,
                "records_count": records_count,
                "loaded_at": pd.Timestamp.utcnow()
            }
        },
        upsert=True
    )


async def mark_dataset_failed(dataset_name, path, error):
    await datasets_collection.update_one(
        {"name": dataset_name},
        {
            "$set": {
                "name": dataset_name,
                "status": "failed",
                "path": path,
                "error": str(error),
                "failed_at": pd.Timestamp.utcnow()
            }
        },
        upsert=True
    )


async def upsert_citizen(cnic, name=None):
    if not cnic:
        return

    await citizens_collection.update_one(
        {"cnic": str(cnic)},
        {"$set": {"cnic": str(cnic), "name": name}},
        upsert=True
    )


async def insert_vehicles(df):
    driver = get_driver()

    for _, row in df.iterrows():
        row_data = clean_row(row)

        vehicle_value = estimate_vehicle_value(
            row_data["vehicle_make_model"],
            row_data["engine_capacity_cc"],
            row_data["registration_year"]
        )

        row_data["estimated_vehicle_value_pkr"] = vehicle_value

        await upsert_citizen(row_data["cnic"], row_data.get("owner_name"))

        await vehicles_collection.update_one(
            {"vehicle_reg_no": row_data["vehicle_reg_no"]},
            {"$set": row_data},
            upsert=True
        )

        with driver.session() as session:
            session.run("""
                MERGE (c:Citizen {cnic: $cnic})
                SET c.name = coalesce(c.name, $name)

                MERGE (v:Vehicle {reg_no: $reg_no})
                SET v.owner_name = $owner_name,
                    v.make_model = $model,
                    v.engine_cc = $cc,
                    v.registration_year = $year,
                    v.value = $value

                MERGE (d:ExciseDepartment {name: 'Provincial Excise Department'})

                MERGE (c)-[:OWNS]->(v)
                MERGE (v)-[:REGISTERED_AT]->(d)
            """,
            cnic=str(row_data["cnic"]),
            name=row_data.get("owner_name"),
            owner_name=row_data.get("owner_name"),
            reg_no=str(row_data["vehicle_reg_no"]),
            model=row_data["vehicle_make_model"],
            cc=int(row_data["engine_capacity_cc"]),
            year=int(row_data["registration_year"]),
            value=int(vehicle_value))


async def insert_properties(df):
    driver = get_driver()

    for _, row in df.iterrows():
        row_data = clean_row(row)

        await upsert_citizen(row_data["cnic"], row_data.get("buyer_name"))

        await properties_collection.update_one(
            {"registry_no": row_data["registry_no"]},
            {"$set": row_data},
            upsert=True
        )

        with driver.session() as session:
            session.run("""
                MERGE (c:Citizen {cnic: $cnic})
                SET c.name = coalesce(c.name, $name)

                MERGE (p:Property {registry_no: $reg})
                SET p.buyer_name = $buyer_name,
                    p.address = $addr,
                    p.value = $val,
                    p.area_marla = $area,
                    p.type = $type,
                    p.transfer_date = $transfer_date

                MERGE (r:PropertyRegistry {name: 'Property Registry'})

                MERGE (c)-[:OWNS]->(p)
                MERGE (p)-[:REGISTERED_AT]->(r)
            """,
            cnic=str(row_data["cnic"]),
            name=row_data.get("buyer_name"),
            buyer_name=row_data.get("buyer_name"),
            reg=str(row_data["registry_no"]),
            addr=row_data["property_address"],
            val=int(row_data["property_value_pkr"]),
            area=int(row_data["area_marla"]),
            type=row_data["property_type"],
            transfer_date=str(row_data["transfer_date"]))


async def insert_tax_records(df):
    driver = get_driver()

    for _, row in df.iterrows():
        row_data = clean_row(row)

        await upsert_citizen(row_data["cnic"], row_data.get("full_name"))

        await tax_records_collection.update_one(
            {"fbr_id": row_data["fbr_id"]},
            {"$set": row_data},
            upsert=True
        )

        with driver.session() as session:
            session.run("""
                MERGE (c:Citizen {cnic: $cnic})
                SET c.name = coalesce(c.name, $name),
                    c.tax_status = $status,
                    c.declared_income = $income,
                    c.tax_paid = $tax_paid

                MERGE (t:TaxRecord {fbr_id: $fbr_id})
                SET t.full_name = $name,
                    t.declared_income = $income,
                    t.tax_paid = $tax_paid,
                    t.filer_status = $status

                MERGE (f:FBR {name: 'Federal Board of Revenue'})

                MERGE (c)-[:FILED]->(t)
                MERGE (t)-[:DECLARED_AT]->(f)
            """,
            cnic=str(row_data["cnic"]),
            fbr_id=str(row_data["fbr_id"]),
            name=row_data.get("full_name"),
            status=row_data["filer_status"],
            income=int(row_data["declared_income_pkr"]),
            tax_paid=int(row_data["tax_paid_pkr"]))


async def insert_utilities(df):
    driver = get_driver()

    for _, row in df.iterrows():
        row_data = clean_row(row)

        await upsert_citizen(row_data["cnic"], row_data.get("consumer_name"))

        await utility_records_collection.update_one(
            {"meter_ref_no": row_data["meter_ref_no"]},
            {"$set": row_data},
            upsert=True
        )

        with driver.session() as session:
            session.run("""
                MERGE (c:Citizen {cnic: $cnic})
                SET c.name = coalesce(c.name, $name)

                MERGE (u:Utility {meter_ref: $meter})
                SET u.consumer_name = $consumer_name,
                    u.type = $type,
                    u.avg_bill = $bill,
                    u.address = $address

                MERGE (d:DISCO {name: 'Electricity Distribution Company'})

                MERGE (c)-[:USES]->(u)
                MERGE (u)-[:PROVIDED_BY]->(d)
            """,
            cnic=str(row_data["cnic"]),
            name=row_data.get("consumer_name"),
            consumer_name=row_data.get("consumer_name"),
            meter=str(row_data["meter_ref_no"]),
            type=row_data["connection_type"],
            bill=int(row_data["avg_monthly_bill_pkr"]),
            address=row_data["installation_address"])


async def reset_dataset_status():
    await datasets_collection.delete_many({})
    print("🧹 Dataset loading history cleared.")


async def run_demo_loader(force_reload=False):
    datasets = [
        {"name": "vehicles", "path": "data/demo/exercise_vehicles.csv", "func": insert_vehicles},
        {"name": "properties", "path": "data/demo/property_transfers.csv", "func": insert_properties},
        {"name": "tax", "path": "data/demo/fbr_tax_records.csv", "func": insert_tax_records},
        {"name": "utilities", "path": "data/demo/disco_consumption.csv", "func": insert_utilities}
    ]

    for ds in datasets:
        if not force_reload:
            skip = await should_skip_dataset(ds["name"])

            if skip:
                print(f"⏩ Skipping {ds['name']} because it is already loaded in MongoDB and Neo4j.")
                continue

        try:
            print(f"🚀 Loading {ds['name']}...")

            cleaned_records = process_csv_file(ds["path"], fiscal_year="2026")
            df = pd.DataFrame(cleaned_records)
            await ds["func"](df)

            await mark_dataset_loaded(
                dataset_name=ds["name"],
                path=ds["path"],
                records_count=len(df)
            )

            print(f"✅ Finished loading {ds['name']} with {len(df)} records.")

        except Exception as e:
            await mark_dataset_failed(ds["name"], ds["path"], e)
            print(f"❌ Error loading {ds['name']}: {e}")

    print("🏁 All pending demo datasets processed.")