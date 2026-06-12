from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import FileResponse
import shutil
import os

from dependencies.auth_dependency import require_admin
from services.citizen_service import process_csv_file
from processor.entity_resolver import resolve_and_enrich
from services.risk_engine import calculate_risk_score
from services.audit_service import generate_investigation_report, create_pdf_report
from services.evaluation_service import calculate_precision_recall
from connection.database import db, get_driver
from services.gnn_anomaly_service import run_gnn_anomaly_detection
from services.entity_resolution_service import run_entity_resolution
from services.knowledge_graph_service import (
    search_citizens_service,
    build_person_knowledge_graph
)
from services.deviation_service import calculate_declaration_gap
router = APIRouter()


def get_neo4j_session():
    driver = get_driver()
    return driver.session()


@router.post("/upload/{dataset_type}")
async def upload_dataset(
    dataset_type: str,
    fiscal_year: str = Form(...),
    file: UploadFile = File(...),
    admin=Depends(require_admin)
):
    allowed = ["vehicles", "properties", "tax_records", "utilities"]

    if dataset_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Allowed types: {allowed}")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    temp_path = f"temp_{file.filename}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        cleaned_data = process_csv_file(temp_path, fiscal_year)

        if not cleaned_data:
            raise HTTPException(status_code=400, detail="No valid records found")

        await db[f"{dataset_type}_history"].insert_many(cleaned_data)

        with get_neo4j_session() as session:
            for record in cleaned_data:
                session.execute_write(resolve_and_enrich, record)

        return {
            "message": "Dataset uploaded, cleaned, stored, and graph updated",
            "dataset_type": dataset_type,
            "records": len(cleaned_data),
            "fiscal_year": fiscal_year
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/analyze-risk/{cnic}")
async def analyze_risk(cnic: str):
    risk_data = await calculate_risk_score(cnic)
    report = generate_investigation_report(cnic, risk_data)

    return {
        "analysis": risk_data,
        "audit_trail": report
    }
@router.get("/declaration-gap/{cnic}")
async def declaration_gap(cnic: str, fiscal_year: str = "2026"):
    result = await calculate_declaration_gap(cnic, fiscal_year)
    return result

@router.get("/download-report/{cnic}")
async def download_report(cnic: str):
    risk_data = await calculate_risk_score(cnic)
    path = create_pdf_report(cnic, risk_data)

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"investigation_report_{cnic}.pdf"
    )


@router.get("/risk-ranking")
async def risk_ranking():
    records = await db.risk_scores.find().sort("risk_score", -1).to_list(length=100)

    if not records:
        citizens = await db.citizens.find().to_list(length=50)

        for citizen in citizens:
            cnic = citizen.get("cnic")
            if cnic:
                try:
                    await calculate_risk_score(cnic)
                except Exception as e:
                    print(f"Risk calculation skipped for {cnic}: {e}")

        records = await db.risk_scores.find().sort("risk_score", -1).to_list(length=100)

    for r in records:
        r["_id"] = str(r["_id"])

    return {"ranking": records}

@router.get("/citizens/search")
async def search_citizens(q: str = ""):
    citizens = await search_citizens_service(q)
    return {"citizens": citizens}


@router.get("/knowledge-graph/{cnic}")
async def knowledge_graph(cnic: str, fiscal_year: str | None = None):
    graph_data = await build_person_knowledge_graph(cnic, fiscal_year)
    return graph_data
@router.get("/graph-ai/anomalies")
async def graph_ai_anomalies():
    records = await db.risk_scores.find().sort("risk_score", -1).to_list(length=100)

    results = []

    for r in records:
        results.append({
            "cnic": r.get("cnic"),
            "graph_anomaly_score": r.get("risk_score", 0),
            "vehicle_count": len(r.get("vehicles", [])),
            "property_count": len(r.get("properties", [])),
            "utility_count": len(r.get("utilities", [])),
            "lifestyle_value": r.get("observed_lifestyle_value", 0)
        })

    return {"graph_ai_anomalies": results}


@router.post("/evaluate")
async def evaluate_entity_resolution(
    true_matches: list,
    predicted_matches: list
):
    return calculate_precision_recall(true_matches, predicted_matches)


@router.get("/summary-stats")
async def summary_stats():
    citizens = await db.citizens.count_documents({})
    tax = await db.tax_records.count_documents({})
    vehicles = await db.vehicles.count_documents({})
    properties = await db.properties.count_documents({})
    utilities = await db.utility_records.count_documents({})
    risks = await db.risk_scores.count_documents({})

    relationships = []

    try:
        with get_neo4j_session() as session:
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS relationship, count(r) AS count
            """)

            relationships = [
                {"relationship": row["relationship"], "count": row["count"]}
                for row in result
            ]
    except Exception as e:
        print(f"Neo4j relationship stats skipped: {e}")

    return {
        "citizens": citizens,
        "tax_records": tax,
        "vehicles": vehicles,
        "properties": properties,
        "utilities": utilities,
        "risk_scores": risks,
        "relationships": relationships
    }


@router.get("/search")
async def search(q: str):
    data = []

    try:
        with get_neo4j_session() as session:
            result = session.run("""
                MATCH (n)
                WHERE any(k IN keys(n) WHERE toString(n[k]) CONTAINS $q)
                RETURN labels(n) AS labels, properties(n) AS data
                LIMIT 50
            """, q=q)

            data = [
                {"labels": row["labels"], "data": row["data"]}
                for row in result
            ]
    except Exception as e:
        print(f"Neo4j search failed: {e}")

    return {"results": data}


@router.get("/graph/{cnic}")
async def graph(cnic: str):
    paths = []

    try:
        with get_neo4j_session() as session:
            result = session.run("""
                MATCH path = (c:Citizen {cnic: $cnic})-[*1..2]-(n)
                RETURN path
                LIMIT 100
            """, cnic=cnic)

            paths = [str(row["path"]) for row in result]
    except Exception as e:
        print(f"Neo4j graph failed: {e}")

    return {
        "cnic": cnic,
        "paths": paths
    }


@router.get("/regional-compliance")
async def regional_compliance():
    regions = {
        "Punjab": ["Lahore", "Rawalpindi", "Faisalabad", "Multan", "Gujranwala"],
        "Sindh": ["Karachi", "Hyderabad", "Sukkur"],
        "KPK": ["Peshawar", "Abbottabad"],
        "Balochistan": ["Quetta"],
        "Islamabad": ["Islamabad"]
    }

    response = []

    for region, cities in regions.items():
        try:
            with get_neo4j_session() as session:
                result = session.run("""
                    MATCH (c:Citizen)
                    OPTIONAL MATCH (c)-[:OWNS]->(p:Property)
                    OPTIONAL MATCH (c)-[:USES]->(u:Utility)
                    OPTIONAL MATCH (c)-[:OWNS]->(v:Vehicle)
                    OPTIONAL MATCH (c)-[:FILED]->(t:TaxRecord)

                    WITH c, p, u, v, t,
                    coalesce(c.address, '') + ' ' +
                    coalesce(c.latest_address, '') + ' ' +
                    coalesce(p.address, '') + ' ' +
                    coalesce(u.address, '') AS combined_address

                    WHERE any(city IN $cities WHERE
                        toLower(combined_address) CONTAINS toLower(city)
                    )

                    RETURN
                        count(DISTINCT c) AS citizens,
                        count(DISTINCT v) AS vehicles,
                        count(DISTINCT p) AS properties,
                        count(DISTINCT u) AS utilities,
                        sum(DISTINCT coalesce(t.declared_income, 0)) AS income,
                        sum(DISTINCT coalesce(t.tax_paid, 0)) AS tax_paid,
                        sum(DISTINCT coalesce(v.value, 0)) AS vehicle_value,
                        sum(DISTINCT coalesce(p.value, 0)) AS property_value,
                        sum(DISTINCT coalesce(u.avg_bill, 0)) AS monthly_bill
                """, cities=cities).single()

                citizens = result["citizens"] or 0
                income = result["income"] or 0
                tax_paid = result["tax_paid"] or 0
                vehicle_value = result["vehicle_value"] or 0
                property_value = result["property_value"] or 0
                monthly_bill = result["monthly_bill"] or 0

                lifestyle_value = vehicle_value + property_value + (monthly_bill * 12)

                compliance = round((tax_paid / income) * 100, 2) if income > 0 else 0

                if income > 0:
                    risk_score = round(min((lifestyle_value / income) * 10, 100), 2)
                else:
                    risk_score = 0

                response.append({
                    "region": region,
                    "citizens": citizens,
                    "vehicles": result["vehicles"] or 0,
                    "properties": result["properties"] or 0,
                    "utilities": result["utilities"] or 0,
                    "declared_income": income,
                    "tax_paid": tax_paid,
                    "lifestyle_value": lifestyle_value,
                    "compliance": compliance,
                    "risk_score": risk_score
                })

        except Exception as e:
            print(f"Regional compliance failed for {region}: {e}")

            response.append({
                "region": region,
                "citizens": 0,
                "vehicles": 0,
                "properties": 0,
                "utilities": 0,
                "declared_income": 0,
                "tax_paid": 0,
                "lifestyle_value": 0,
                "compliance": 0,
                "risk_score": 0
            })

    return {"regions": response}
@router.get("/entity-resolution")
async def entity_resolution(threshold: float = 75):
    matches = await run_entity_resolution(threshold)
    return {
        "threshold": threshold,
        "matches_found": len(matches),
        "matches": matches
    }


@router.get("/gnn-anomalies")
async def gnn_anomalies():
    results = await run_gnn_anomaly_detection()
    return {
        "model": "GCN Graph AutoEncoder",
        "results": results
    }


@router.get("/audit-trail/{cnic}")
async def audit_trail(cnic: str):
    risk_data = await calculate_risk_score(cnic)
    report = generate_investigation_report(cnic, risk_data)

    return {
        "cnic": cnic,
        "risk_data": risk_data,
        "audit_trail": report
    }
@router.get("/status")
async def status():
    return {"status": "Operational"}