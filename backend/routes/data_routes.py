from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import shutil
import os
from services.citizen_service import process_csv_file
from processor.entity_resolver import resolve_and_enrich
from services.risk_engine import calculate_risk_score
from services.audit_service import generate_investigation_report
from connection.database import db, get_driver

# Initialize the driver at the module level for the file
driver = get_driver()

router = APIRouter()

@router.post("/upload/{dataset_type}")
async def upload_dataset(
    dataset_type: str, 
    fiscal_year: str = Form(...), 
    file: UploadFile = File(...)
):
    """
    Uploads, validates, cleans, and stores dataset records in MongoDB 
    and updates the Knowledge Graph in Neo4j.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    # Save temporarily
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 1. Process and Clean
        cleaned_data = process_csv_file(temp_path, fiscal_year)
        
        if not cleaned_data:
            raise HTTPException(status_code=400, detail="No valid records found in CSV.")
        
        # 2. Append-Only Store in MongoDB (Preserve History)
        collection = db[f"{dataset_type}_history"]
        collection.insert_many(cleaned_data)
        
        # 3. Update Knowledge Graph
        with driver.session() as session:
            for record in cleaned_data:
                session.execute_write(resolve_and_enrich, record)
            
        return {
            "message": f"Successfully processed {len(cleaned_data)} records into {dataset_type}",
            "fiscal_year": fiscal_year
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/analyze-risk/{cnic}")
async def get_risk_analysis(cnic: str):
    """
    Fulfills Risk Analysis and Explainable AI requirements.
    Queries Neo4j and MongoDB to flag non-compliance.
    """
    try:
        # 1. Calculate Score
        risk_data = await calculate_risk_score(cnic)
        
        # 2. Generate Human-Readable Audit Trail
        report = generate_investigation_report(cnic, risk_data)
        
        return {
            "analysis": risk_data,
            "audit_trail": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis error: {str(e)}")

@router.get("/status")
async def get_system_status():
    """
    Provides dashboard metrics as required by functional specs.
    """
    total_citizens = await db.citizens_history.count_documents({})
    return {
        "total_citizens_processed": total_citizens,
        "status": "Operational",
        "description": "Pipeline ready for risk investigation and analysis."
    }

@router.get("/summary-stats")
async def get_summary_stats():
    # Count total entities in collections
    tax_count = await db.tax_records_history.count_documents({})
    vehicle_count = await db.vehicles_history.count_documents({})
    
    # Query Neo4j for the total number of connected relationships
    with driver.session() as session:
        result = session.run("MATCH ()-[r:OWNS]->() RETURN count(r) as total_links")
        total_links = result.single()["total_links"]
        
    return {
        "stats": {
            "tax_records": tax_count,
            "vehicles": vehicle_count,
            "connected_relationships": total_links
        }
    }