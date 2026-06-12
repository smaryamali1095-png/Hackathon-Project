# services/graph_service.py
from ingestion.data_loader import driver

def update_citizen_relationship(cnic, target_id, rel_type, label):
    """Generic helper to create relationships in Neo4j."""
    with driver.session() as session:
        session.run(f"""
            MERGE (c:Citizen {{cnic: $cnic}})
            MERGE (t:{label} {{id: $target_id}})
            MERGE (c)-[:{rel_type}]->(t)
        """, cnic=cnic, target_id=target_id)