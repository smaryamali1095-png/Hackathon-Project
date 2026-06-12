from difflib import SequenceMatcher
from services.embedding_service import get_embedding, embedding_similarity


def clean_text(value):
    if value is None:
        return ""

    value = str(value).strip()
    value = value.replace("مالک:", "")
    value = value.replace("جناب", "")
    value = value.replace("Mr.", "")
    value = value.replace("Sahib", "")
    return " ".join(value.split())


def fuzzy_similarity(a, b):
    a = clean_text(a).lower()
    b = clean_text(b).lower()

    if not a or not b:
        return 0

    return round(SequenceMatcher(None, a, b).ratio() * 100, 2)


def get_name_from_record(record):
    for field in ["full_name", "owner_name", "consumer_name", "buyer_name", "name"]:
        if record.get(field):
            return record[field]
    return ""


def get_address_from_record(record):
    for field in [
        "reported_address",
        "owner_address",
        "installation_address",
        "property_address",
        "address"
    ]:
        if record.get(field):
            return record[field]
    return ""


def calculate_match_confidence(record_a, record_b):
    cnic_a = str(record_a.get("cnic", "")).replace("-", "").strip()
    cnic_b = str(record_b.get("cnic", "")).replace("-", "").strip()

    if cnic_a and cnic_b and cnic_a == cnic_b:
        return 100

    name_a = get_name_from_record(record_a)
    name_b = get_name_from_record(record_b)

    address_a = get_address_from_record(record_a)
    address_b = get_address_from_record(record_b)

    fuzzy_name = fuzzy_similarity(name_a, name_b)
    fuzzy_address = fuzzy_similarity(address_a, address_b)

    embedding_name = embedding_similarity(name_a, name_b)
    embedding_address = embedding_similarity(address_a, address_b)

    confidence = (
        fuzzy_name * 0.25 +
        fuzzy_address * 0.15 +
        embedding_name * 0.40 +
        embedding_address * 0.20
    )

    return round(confidence, 2)


def resolve_and_enrich(tx, record):
    cnic = str(record.get("cnic", "")).strip()
    name = get_name_from_record(record)
    address = get_address_from_record(record)

    fiscal_year = record.get("fiscal_year", "2026")
    source = record.get("source", "CSV_UPLOAD")

    tx.run("""
        MERGE (c:Citizen {cnic: $cnic})
        ON CREATE SET
            c.name = $name,
            c.address = $address,
            c.created_at = timestamp()
        ON MATCH SET
            c.latest_name = $name,
            c.latest_address = $address,
            c.last_updated = timestamp()
        SET c.name_embedding = $name_embedding,
            c.address_embedding = $address_embedding
    """,
    cnic=cnic,
    name=name,
    address=address,
    name_embedding=get_embedding(name),
    address_embedding=get_embedding(address))

    if "vehicle_reg_no" in record:
        tx.run("""
            MERGE (c:Citizen {cnic: $cnic})
            MERGE (v:Vehicle {reg_no: $reg_no})
            SET v.owner_name = $name,
                v.make_model = $model,
                v.engine_cc = toInteger($cc),
                v.registration_year = toInteger($year),
                v.value = toInteger($value)

            MERGE (d:ExciseDepartment {name: 'Provincial Excise Department'})

            MERGE (c)-[:OWNS {fiscal_year: $fy, source: $source}]->(v)
            MERGE (v)-[:REGISTERED_AT]->(d)
        """,
        cnic=cnic,
        reg_no=str(record.get("vehicle_reg_no")),
        name=name,
        model=record.get("vehicle_make_model"),
        cc=record.get("engine_capacity_cc"),
        year=record.get("registration_year"),
        value=record.get("estimated_vehicle_value_pkr", 0),
        fy=fiscal_year,
        source=source)

    elif "registry_no" in record:
        tx.run("""
            MERGE (c:Citizen {cnic: $cnic})
            MERGE (p:Property {registry_no: $registry_no})
            SET p.buyer_name = $name,
                p.address = $address,
                p.value = toInteger($value),
                p.area_marla = toInteger($area),
                p.type = $type,
                p.transfer_date = $transfer_date

            MERGE (r:PropertyRegistry {name: 'Property Registry'})

            MERGE (c)-[:OWNS {fiscal_year: $fy, source: $source}]->(p)
            MERGE (p)-[:REGISTERED_AT]->(r)
        """,
        cnic=cnic,
        registry_no=str(record.get("registry_no")),
        name=name,
        address=record.get("property_address"),
        value=record.get("property_value_pkr"),
        area=record.get("area_marla"),
        type=record.get("property_type"),
        transfer_date=record.get("transfer_date"),
        fy=fiscal_year,
        source=source)

    elif "fbr_id" in record:
        tx.run("""
            MERGE (c:Citizen {cnic: $cnic})
            MERGE (t:TaxRecord {fbr_id: $fbr_id})
            SET t.full_name = $name,
                t.declared_income = toInteger($income),
                t.tax_paid = toInteger($tax),
                t.filer_status = $status

            MERGE (f:FBR {name: 'Federal Board of Revenue'})

            MERGE (c)-[:FILED {fiscal_year: $fy, source: $source}]->(t)
            MERGE (t)-[:DECLARED_AT]->(f)
        """,
        cnic=cnic,
        fbr_id=str(record.get("fbr_id")),
        name=name,
        income=record.get("declared_income_pkr"),
        tax=record.get("tax_paid_pkr"),
        status=record.get("filer_status"),
        fy=fiscal_year,
        source=source)

    elif "meter_ref_no" in record:
        tx.run("""
            MERGE (c:Citizen {cnic: $cnic})
            MERGE (u:Utility {meter_ref: $meter})
            SET u.consumer_name = $name,
                u.avg_bill = toInteger($bill),
                u.type = $type,
                u.address = $address

            MERGE (d:DISCO {name: 'Electricity Distribution Company'})

            MERGE (c)-[:USES {fiscal_year: $fy, source: $source}]->(u)
            MERGE (u)-[:PROVIDED_BY]->(d)
        """,
        cnic=cnic,
        meter=str(record.get("meter_ref_no")),
        name=name,
        bill=record.get("avg_monthly_bill_pkr"),
        type=record.get("connection_type"),
        address=record.get("installation_address"),
        fy=fiscal_year,
        source=source)