from neo4j import GraphDatabase

def resolve_and_enrich(tx, record):
    # Requirement: Identify and merge records
    # Requirement: Historical tracking via fiscal_year
    query = """
    MERGE (c:Citizen {cnic: $cnic})
    SET c.name = coalesce(c.name, $name),
        c.last_updated = timestamp()
    
    // Create a historical record of the asset link
    MERGE (asset:Asset {id: $asset_id, type: $asset_type})
    MERGE (c)-[r:OWNS {fiscal_year: $fy}]->(asset)
    SET r.source = $source
    RETURN id(c) as citizen_id
    """
    tx.run(query, 
           cnic=record['cnic'], 
           name=record.get('name', 'N/A'),
           asset_id=record.get('id'), 
           asset_type=record.get('type'),
           fy=record.get('fiscal_year'),
           source=record.get('source', 'CSV_UPLOAD'))