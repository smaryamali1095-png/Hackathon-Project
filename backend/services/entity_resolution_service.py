from bson import ObjectId
from connection.database import db, entity_matches_collection
from processor.entity_resolver import calculate_match_confidence

SOURCE_COLLECTIONS = [
    "vehicles",
    "properties",
    "tax_records",
    "utility_records",
]


def text(value):
    return str(value or "").strip()


def money(value):
    try:
        return f"PKR {float(value or 0):,.0f}"
    except Exception:
        return "PKR 0"


def get_name(record):
    return (
        record.get("owner_name")
        or record.get("buyer_name")
        or record.get("full_name")
        or record.get("consumer_name")
        or "Unknown Person"
    )


def get_cnic(record):
    return text(record.get("cnic"))


def mask_cnic(cnic):
    cnic = text(cnic)
    if len(cnic) < 6:
        return "Unknown"
    return cnic[:6] + "*****" + cnic[-2:]


def normalize_record(record, source):
    record["_id"] = str(record.get("_id", ""))

    if source == "vehicles":
        return {
            "id": record["_id"],
            "type": "Vehicle",
            "source": "Vehicle Registry Data",
            "name": record.get("owner_name"),
            "cnic": record.get("cnic"),
            "title": record.get("vehicle_make_model"),
            "field1": f"Reg No: {record.get('vehicle_reg_no', 'N/A')}",
            "field2": f"Engine: {record.get('engine_capacity_cc', 'N/A')} CC",
            "field3": f"Year: {record.get('registration_year', 'N/A')}",
            "amount": money(record.get("estimated_vehicle_value_pkr")),
            "address": "N/A",
        }

    if source == "properties":
        return {
            "id": record["_id"],
            "type": "Property",
            "source": "Property Registry Data",
            "name": record.get("buyer_name"),
            "cnic": record.get("cnic"),
            "title": record.get("property_type"),
            "field1": f"Registry No: {record.get('registry_no', 'N/A')}",
            "field2": f"Area: {record.get('area_marla', 'N/A')} Marla",
            "field3": f"Transfer Date: {record.get('transfer_date', 'N/A')}",
            "amount": money(record.get("property_value_pkr")),
            "address": record.get("property_address", "N/A"),
        }

    if source == "tax_records":
        return {
            "id": record["_id"],
            "type": "Tax Record",
            "source": "FBR Official Record",
            "name": record.get("full_name"),
            "cnic": record.get("cnic"),
            "title": record.get("filer_status"),
            "field1": f"FBR ID: {record.get('fbr_id', 'N/A')}",
            "field2": f"Declared Income: {money(record.get('declared_income_pkr'))}",
            "field3": f"Tax Paid: {money(record.get('tax_paid_pkr'))}",
            "amount": money(record.get("declared_income_pkr")),
            "address": "N/A",
        }

    if source == "utility_records":
        return {
            "id": record["_id"],
            "type": "Utility",
            "source": "Utility Consumption Data",
            "name": record.get("consumer_name"),
            "cnic": record.get("cnic"),
            "title": record.get("connection_type"),
            "field1": f"Meter Ref: {record.get('meter_ref_no', 'N/A')}",
            "field2": f"Monthly Bill: {money(record.get('avg_monthly_bill_pkr'))}",
            "field3": "Electricity Distribution Company",
            "amount": money(record.get("avg_monthly_bill_pkr")),
            "address": record.get("installation_address", "N/A"),
        }

    return None


async def get_all_records():
    records = []

    for source in SOURCE_COLLECTIONS:
        rows = await db[source].find().to_list(length=3000)

        for row in rows:
            row["_id"] = str(row["_id"])
            row["source_collection"] = source
            records.append(row)

    return records


async def run_entity_resolution(threshold=60):
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
                doc = {
                    "record_a_id": a["_id"],
                    "record_b_id": b["_id"],
                    "record_a_source": a["source_collection"],
                    "record_b_source": b["source_collection"],
                    "record_a_name": get_name(a),
                    "record_b_name": get_name(b),
                    "record_a_cnic": get_cnic(a),
                    "record_b_cnic": get_cnic(b),
                    "match_confidence": score,
                    "status": "pending",
                    "reason": "Matched using CNIC, name, address, vehicle, property, utility and tax signals."
                }

                await entity_matches_collection.update_one(
                    {
                        "record_a_id": a["_id"],
                        "record_b_id": b["_id"],
                    },
                    {"$set": doc},
                    upsert=True,
                )

                matches.append(doc)

    return matches


async def search_entity_matches(q=""):
    q = text(q)

    if not q:
        return []

    query = {
        "$or": [
            {"record_a_name": {"$regex": q, "$options": "i"}},
            {"record_b_name": {"$regex": q, "$options": "i"}},
            {"record_a_cnic": {"$regex": q, "$options": "i"}},
            {"record_b_cnic": {"$regex": q, "$options": "i"}},
        ]
    }

    rows = await entity_matches_collection.find(query).sort(
        "match_confidence", -1
    ).to_list(length=300)

    grouped = {}

    for row in rows:
        cnic = row.get("record_a_cnic") or row.get("record_b_cnic")

        if not cnic:
            continue

        name = (
            row.get("record_a_name")
            or row.get("record_b_name")
            or "Unknown Person"
        )

        if cnic not in grouped:
            grouped[cnic] = {
                "match_id": str(row["_id"]),
                "display_name": name,
                "match_score": round(float(row.get("match_confidence", 0))),
                "masked_cnic": mask_cnic(cnic),
                "sources": set(),
                "status": row.get("status", "pending"),
            }

        grouped[cnic]["sources"].add(row.get("record_a_source"))
        grouped[cnic]["sources"].add(row.get("record_b_source"))

        grouped[cnic]["match_score"] = max(
            grouped[cnic]["match_score"],
            round(float(row.get("match_confidence", 0)))
        )

    result = []

    for item in grouped.values():
        item["sources"] = [s for s in item["sources"] if s]
        result.append(item)

    return result

async def get_record(source, record_id):
    try:
        return await db[source].find_one({"_id": ObjectId(record_id)})
    except Exception:
        return await db[source].find_one({"_id": record_id})


async def get_all_cards_by_cnic(cnic):
    cards = []

    if not cnic:
        return cards

    for source in SOURCE_COLLECTIONS:
        rows = await db[source].find({"cnic": cnic}).to_list(length=100)

        for row in rows:
            card = normalize_record(row, source)
            if card:
                cards.append(card)

    return cards


async def get_entity_comparison(match_id):
    match = await entity_matches_collection.find_one({"_id": ObjectId(match_id)})

    if not match:
        return None

    cnic = match.get("record_a_cnic") or match.get("record_b_cnic")

    cards = await get_all_cards_by_cnic(cnic)

    return {
        "match_id": str(match["_id"]),
        "record_cards": cards,
        "conflict_matrix": {
            "name_spelling": "Partial",
            "name_score": round(float(match.get("match_confidence", 0))),
            "cnic_alignment": "Exact",
            "cnic_score": 100,
            "address_proximity": "Partial",
            "address_score": 60,
        },
        "ai_logic": {
            "record_a_label": match.get("record_a_name"),
            "record_b_label": match.get("record_b_name"),
            "confidence_score": round(float(match.get("match_confidence", 0))),
            "reason": match.get("reason", ""),
        },
        "shared_nodes": len(cards),
    }


async def merge_entity_match(match_id):
    result = await entity_matches_collection.update_one(
        {"_id": ObjectId(match_id)},
        {"$set": {"status": "merged"}},
    )
    return {"success": result.modified_count > 0}


async def flag_entity_match(match_id):
    result = await entity_matches_collection.update_one(
        {"_id": ObjectId(match_id)},
        {"$set": {"status": "flagged_for_review"}},
    )
    return {"success": result.modified_count > 0}