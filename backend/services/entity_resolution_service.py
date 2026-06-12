from connection.database import db, entity_matches_collection
from processor.entity_resolver import calculate_match_confidence

SOURCE_COLLECTIONS = [
    "vehicles",
    "properties",
    "tax_records",
    "utility_records",
    "travel_records"
]


async def get_all_records():
    records = []

    for collection_name in SOURCE_COLLECTIONS:
        collection = db[collection_name]
        rows = await collection.find().to_list(length=1000)

        for row in rows:
            row["_id"] = str(row["_id"])
            row["source_collection"] = collection_name
            records.append(row)

    return records


async def run_entity_resolution(threshold=75):
    records = await get_all_records()
    matches = []

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            a = records[i]
            b = records[j]

            if a["source_collection"] == b["source_collection"]:
                continue

            score = calculate_match_confidence(a, b)

            if score >= threshold:
                match = {
                    "record_a": a,
                    "record_b": b,
                    "match_confidence": score,
                    "reason": "Matched using CNIC, fuzzy name/address similarity, and multilingual embeddings."
                }

                matches.append(match)

                await entity_matches_collection.update_one(
                    {
                        "record_a_id": a["_id"],
                        "record_b_id": b["_id"]
                    },
                    {
                        "$set": {
                            "record_a_id": a["_id"],
                            "record_b_id": b["_id"],
                            "record_a_source": a["source_collection"],
                            "record_b_source": b["source_collection"],
                            "match_confidence": score,
                            "reason": match["reason"]
                        }
                    },
                    upsert=True
                )

    return matches