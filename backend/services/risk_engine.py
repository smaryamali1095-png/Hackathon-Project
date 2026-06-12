from connection.database import get_driver, risk_scores_collection

driver = get_driver()


def classify_risk(score):
    if score < 25:
        return "Low"
    elif score < 60:
        return "Medium"
    elif score < 85:
        return "High"
    return "Critical"


async def calculate_risk_score(cnic):
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Citizen {cnic: $cnic})
            OPTIONAL MATCH (c)-[:FILED]->(t:TaxRecord)
            OPTIONAL MATCH (c)-[:OWNS]->(v:Vehicle)
            OPTIONAL MATCH (c)-[:OWNS]->(p:Property)
            OPTIONAL MATCH (c)-[:USES]->(u:Utility)
            RETURN
                c.name AS name,
                coalesce(t.declared_income, 0) AS declared_income,
                coalesce(t.tax_paid, 0) AS tax_paid,
                coalesce(t.filer_status, 'Unknown') AS filer_status,

                collect(DISTINCT {
                    reg_no: v.reg_no,
                    model: v.make_model,
                    engine_cc: v.engine_cc,
                    value: coalesce(v.value, 0)
                }) AS vehicles,

                collect(DISTINCT {
                    registry_no: p.registry_no,
                    type: p.type,
                    address: p.address,
                    value: coalesce(p.value, 0)
                }) AS properties,

                collect(DISTINCT {
                    meter_ref: u.meter_ref,
                    type: u.type,
                    avg_bill: coalesce(u.avg_bill, 0),
                    address: u.address
                }) AS utilities
        """, cnic=str(cnic)).single()

    if not result:
        return {
            "cnic": str(cnic),
            "risk_score": 0,
            "risk_level": "Unknown",
            "explanation": "Citizen not found."
        }

    declared_income = int(result["declared_income"] or 0)
    tax_paid = int(result["tax_paid"] or 0)
    filer_status = result["filer_status"] or "Unknown"

    vehicles = [v for v in result["vehicles"] if v.get("reg_no")]
    properties = [p for p in result["properties"] if p.get("registry_no")]
    utilities = [u for u in result["utilities"] if u.get("meter_ref")]

    vehicle_value = sum(int(v.get("value") or 0) for v in vehicles)
    property_value = sum(int(p.get("value") or 0) for p in properties)
    monthly_utility_bill = sum(int(u.get("avg_bill") or 0) for u in utilities)
    annual_utility_spending = monthly_utility_bill * 12

    observed_lifestyle_value = (
        vehicle_value +
        property_value +
        annual_utility_spending
    )

    deviation_amount = max(observed_lifestyle_value - declared_income, 0)

    if declared_income > 0:
        deviation_percentage = (deviation_amount / declared_income) * 100
        tax_ratio = tax_paid / declared_income
    else:
        deviation_percentage = 0
        tax_ratio = 0

    risk_score = 0

    if declared_income <= 0 and observed_lifestyle_value > 0:
        risk_score += 45
    elif declared_income > 0:
        if deviation_percentage > 500:
            risk_score += 45
        elif deviation_percentage > 250:
            risk_score += 35
        elif deviation_percentage > 100:
            risk_score += 25
        elif deviation_percentage > 50:
            risk_score += 15
        elif deviation_percentage > 20:
            risk_score += 8

    if filer_status.lower() == "non-filer":
        risk_score += 20

    if declared_income > 0 and tax_ratio < 0.01:
        risk_score += 12

    if monthly_utility_bill > 300000:
        risk_score += 12
    elif monthly_utility_bill > 150000:
        risk_score += 8
    elif monthly_utility_bill > 80000:
        risk_score += 4

    luxury_vehicles = [
        v for v in vehicles
        if int(v.get("engine_cc") or 0) >= 2000
    ]

    if luxury_vehicles:
        risk_score += 10

    if property_value > 50000000:
        risk_score += 12
    elif property_value > 25000000:
        risk_score += 8
    elif property_value > 10000000:
        risk_score += 4

    risk_score = min(round(risk_score, 2), 100)
    risk_level = classify_risk(risk_score)

    explanation = (
        f"Declared income is PKR {declared_income:,}. "
        f"Observed lifestyle value is PKR {observed_lifestyle_value:,}. "
        f"Vehicles value: PKR {vehicle_value:,}. "
        f"Property value: PKR {property_value:,}. "
        f"Annual utility spending: PKR {annual_utility_spending:,}. "
        f"Deviation amount is PKR {deviation_amount:,}, "
        f"which is {round(deviation_percentage, 2)}% above declared income. "
        f"Final risk level is {risk_level}."
    )

    result_data = {
        "cnic": str(cnic),
        "name": result["name"],
        "declared_income": declared_income,
        "tax_paid": tax_paid,
        "filer_status": filer_status,
        "vehicle_value": vehicle_value,
        "property_value": property_value,
        "monthly_utility_bill": monthly_utility_bill,
        "annual_utility_spending": annual_utility_spending,
        "observed_lifestyle_value": observed_lifestyle_value,
        "deviation_amount": deviation_amount,
        "deviation_percentage": round(deviation_percentage, 2),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "vehicles": vehicles,
        "properties": properties,
        "utilities": utilities,
        "explanation": explanation
    }

    await risk_scores_collection.update_one(
        {"cnic": str(cnic)},
        {"$set": result_data},
        upsert=True
    )

    return result_data