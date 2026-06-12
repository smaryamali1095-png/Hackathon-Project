import sys
import os
import asyncio

# Allow imports from backend root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from connection.database import (
    get_driver,
    citizens_collection,
    vehicles_collection,
    properties_collection,
    tax_records_collection,
    utility_records_collection
)


def valid(value):
    return (
        value is not None
        and str(value).strip() != ""
        and str(value).lower() != "nan"
    )


async def update_mongo_citizen(cnic, name=None, address=None):
    if not valid(cnic):
        return

    update_data = {
        "cnic": str(cnic)
    }

    if valid(name):
        update_data["name"] = str(name)

    if valid(address):
        update_data["address"] = str(address)
        update_data["latest_address"] = str(address)

    await citizens_collection.update_one(
        {"cnic": str(cnic)},
        {"$set": update_data},
        upsert=True
    )


def update_neo4j_citizen(session, cnic, name=None, address=None):
    if not valid(cnic):
        return

    session.run(
        """
        MERGE (c:Citizen {cnic: $cnic})
        SET c.name = coalesce(c.name, $name),
            c.address = coalesce(c.address, $address),
            c.latest_address = coalesce($address, c.latest_address)
        """,
        cnic=str(cnic),
        name=str(name) if valid(name) else None,
        address=str(address) if valid(address) else None
    )


async def fix_existing_addresses():
    driver = get_driver()
    updated = 0

    with driver.session() as session:

        async for row in vehicles_collection.find({}):
            cnic = row.get("cnic")
            name = row.get("owner_name")
            address = row.get("owner_address")

            if valid(address):
                await update_mongo_citizen(cnic, name, address)
                update_neo4j_citizen(session, cnic, name, address)
                updated += 1

        async for row in properties_collection.find({}):
            cnic = row.get("cnic")
            name = row.get("buyer_name")
            address = row.get("property_address")

            if valid(address):
                await update_mongo_citizen(cnic, name, address)
                update_neo4j_citizen(session, cnic, name, address)
                updated += 1

        async for row in tax_records_collection.find({}):
            cnic = row.get("cnic")
            name = row.get("full_name")
            address = row.get("reported_address")

            if valid(address):
                await update_mongo_citizen(cnic, name, address)
                update_neo4j_citizen(session, cnic, name, address)
                updated += 1

        async for row in utility_records_collection.find({}):
            cnic = row.get("cnic")
            name = row.get("consumer_name")
            address = row.get("installation_address")

            if valid(address):
                await update_mongo_citizen(cnic, name, address)
                update_neo4j_citizen(session, cnic, name, address)
                updated += 1

    print(f"✅ Existing citizen addresses fixed successfully.")
    print(f"✅ Total address updates applied: {updated}")


if __name__ == "__main__":
    asyncio.run(fix_existing_addresses())