
def resolve_citizen(tx, cnic, name=None, address=None):
    query = """
    MERGE (c:Citizen {cnic: $cnic})
    ON CREATE SET
        c.name = $name,
        c.address = $address,
        c.created_at = timestamp()
    ON MATCH SET
        c.last_seen = timestamp(),
        c.latest_name = $name,
        c.latest_address = $address
    RETURN elementId(c) AS citizen_id
    """

    result = tx.run(
        query,
        cnic=str(cnic),
        name=name,
        address=address
    )

    return result.single()["citizen_id"]