from processor.cleaner import clean_citizen_data
from processor.resolver import resolve_citizen
from connection.database import citizens_collection
# ... import your drivers

async def run_full_pipeline(file_path, source_type):
    # 1. Extraction
    df = pd.read_csv(file_path)
    
    # 2. Cleaning & Normalization (Requirement: Clean, Standardize)
    df = clean_citizen_data(df)
    
    # 3. Entity Resolution & Graph Construction
    with driver.session() as session:
        for _, row in df.iterrows():
            # A. Update MongoDB (Document Store)
            await citizens_collection.update_one(
                {"cnic": row['cnic']}, {"$set": row.to_dict()}, upsert=True
            )
            
            # B. Neo4j Graph Update (Requirement: Unified Profile)
            session.execute_write(resolve_citizen, row['cnic'], row['name'])
            
            # C. Link specific assets (e.g., Vehicles)
            if 'reg_no' in row:
                session.run("""
                    MATCH (c:Citizen {cnic: $cnic})
                    MERGE (v:Vehicle {reg_no: $reg_no})
                    MERGE (c)-[:OWNS]->(v)
                """, cnic=row['cnic'], reg_no=row['reg_no'])
    
    print(f"✅ Successfully processed {source_type} records.")