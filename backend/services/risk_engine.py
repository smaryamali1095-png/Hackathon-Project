from connection.database import db, get_driver

# Use it like this:
driver = get_driver()

async def calculate_risk_score(cnic):
    """
    1. Fetches assets from Neo4j (Graph)
    2. Fetches income from MongoDB (Document Store)
    3. Calculates deviation and generates explanation
    """
    # Fetch declared income from MongoDB
    tax_record = await db.tax_records_history.find_one({"cnic": cnic}, sort=[("fiscal_year", -1)])
    declared_income = tax_record.get("income", 0) if tax_record else 0

    # Fetch asset count and estimated values from Neo4j
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Citizen {cnic: $cnic})-[:OWNS]->(asset)
            RETURN count(asset) as asset_count, collect(asset.value) as values
        """, cnic=cnic)
        data = result.single()
        asset_count = data["asset_count"]
        estimated_asset_value = sum(data["values"])

    # Risk Logic (Simple deviation formula)
    # Deviation = Assets - Income
    deviation = estimated_asset_value - declared_income
    risk_score = (deviation / declared_income) * 100 if declared_income > 0 else 100
    
    # Classification
    if risk_score < 20: risk_level = "Low"
    elif risk_score < 50: risk_level = "Medium"
    else: risk_level = "Critical"

    # Explainable AI Output
    explanation = f"Individual flagged as {risk_level} risk. Declared income: {declared_income}. Total observed asset value: {estimated_asset_value} across {asset_count} assets."

    return {
        "cnic": cnic,
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "explanation": explanation
    }