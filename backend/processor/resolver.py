from neo4j import GraphDatabase

def resolve_citizen(tx, cnic, name):
    # This logic creates a unique profile or returns the existing one
    query = """
    MERGE (c:Citizen {cnic: $cnic})
    ON CREATE SET c.name = $name, c.created_at = timestamp()
    ON MATCH SET c.last_seen = timestamp()
    RETURN id(c) as citizen_id
    """
    result = tx.run(query, cnic=cnic, name=name)
    return result.single()["citizen_id"]