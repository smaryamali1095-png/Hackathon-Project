from neo4j import GraphDatabase

# Using bolt+s forces the driver to bypass the routing discovery phase
# and connect directly to the primary server.
uri = "bolt+s://82e60242.databases.neo4j.io:7687"
user = "82e60242"
password = "cZkZQ_Q1W3dHR10yn7f5kMeoONd3vyAAE4oCZ1B0RRA"

try:
    print("Attempting DIRECT connection (no routing)...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    print("✅ Direct connection successful! Your ISP is blocking the 'neo4j+s' routing handshake.")
except Exception as e:
    print(f"❌ Direct connection failed: {e}")