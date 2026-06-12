from connection.database import get_driver, risk_scores_collection

driver = get_driver()


def classify_deviation(score):
    if score < 25:
        return "Low"
    elif score < 60:
        return "Medium"
    elif score < 85:
        return "High"
    return "Critical"


async def calculate_declaration_gap(cnic, fiscal_year="2026"):
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Citizen {cnic: $cnic})

            OPTIONAL MATCH (c)-[filed:FILED]->(t:TaxRecord)
            WHERE filed.fiscal_year = $fy OR $fy IS NULL

            OPTIONAL MATCH (c)-[ownsVehicle:OWNS]->(v:Vehicle)
            WHERE ownsVehicle.fiscal_year = $fy OR $fy IS NULL

            OPTIONAL MATCH (c)-[ownsProperty:OWNS]->(p:Property)
            WHERE ownsProperty.fiscal_year = $fy OR $fy IS NULL

            OPTIONAL MATCH (c)-[usesUtility:USES]->(u:Utility)
            WHERE usesUtility.fiscal_year = $fy OR $fy IS NULL

            OPTIONAL MATCH (c)-[travelled:TRAVELLED]->(tr:Travel)
            WHERE travelled.fiscal_year = $fy OR $fy IS NULL

            RETURN
                c.cnic AS cnic,
                coalesce(c.latest_name, c.name, "Unknown Citizen") AS name,

                coalesce(max(t.declared_income), 0) AS declared_income,
                coalesce(max(t.tax_paid), 0) AS tax_paid,
                coalesce(max(t.filer_status), "Unknown") AS filer_status,

                collect(DISTINCT {
                    reg_no: v.reg_no,
                    model: v.make_model,
                    value: coalesce(v.value, 0),
                    engine_cc: coalesce(v.engine_cc, 0)
                }) AS vehicles,

                collect(DISTINCT {
                    registry_no: p.registry_no,
                    type: p.type,
                    address: p.address,
                    value: coalesce(p.value, 0)
                }) AS properties,

                collect(DISTINCT {
                    meter_ref: u.meter_ref,
                    avg_bill: coalesce(u.avg_bill, 0),
                    address: u.address
                }) AS utilities,

                collect(DISTINCT {
                    travel_id: tr.travel_id,
                    destination: tr.destination,
                    ticket_class: tr.ticket_class,
                    trip_cost: coalesce(tr.trip_cost, 0)
                }) AS travels
        """, cnic=str(cnic), fy=fiscal_year).single()

    if not result:
        return {
            "found": False,
            "message": "Citizen not found"
        }

    vehicles = [x for x in result["vehicles"] if x.get("reg_no")]
    properties = [x for x in result["properties"] if x.get("registry_no")]
    utilities = [x for x in result["utilities"] if x.get("meter_ref")]
    travels = [x for x in result["travels"] if x.get("travel_id")]

    vehicle_value = sum(int(x.get("value") or 0) for x in vehicles)
    property_value = sum(int(x.get("value") or 0) for x in properties)
    monthly_utility = sum(int(x.get("avg_bill") or 0) for x in utilities)
    annual_utility = monthly_utility * 12
    travel_value = sum(int(x.get("trip_cost") or 0) for x in travels)

    lifestyle_value = vehicle_value + property_value + annual_utility + travel_value

    declared_income = int(result["declared_income"] or 0)
    tax_paid = int(result["tax_paid"] or 0)
    filer_status = result["filer_status"] or "Unknown"

    undeclared_items = []

    if vehicle_value > declared_income * 0.5:
        undeclared_items.append({
            "type": "Vehicle",
            "issue": "Vehicle assets appear high compared to declared income.",
            "value": vehicle_value
        })

    if property_value > declared_income:
        undeclared_items.append({
            "type": "Property",
            "issue": "Property value appears higher than declared income.",
            "value": property_value
        })

    if monthly_utility > 80000:
        undeclared_items.append({
            "type": "Utility",
            "issue": "Monthly utility bill indicates lifestyle beyond reported income.",
            "value": monthly_utility
        })

    if travel_value > 1000000:
        undeclared_items.append({
            "type": "Luxury Travel",
            "issue": "Luxury travel spending detected.",
            "value": travel_value
        })

    score = 0

    if declared_income <= 0 and lifestyle_value > 0:
        score += 50

    if declared_income > 0:
        ratio = lifestyle_value / declared_income

        if ratio > 10:
            score += 50
        elif ratio > 5:
            score += 40
        elif ratio > 3:
            score += 30
        elif ratio > 2:
            score += 20
        elif ratio > 1:
            score += 10

    if str(filer_status).lower() == "non-filer":
        score += 20

    if tax_paid <= 0 and lifestyle_value > 0:
        score += 15

    if monthly_utility > declared_income / 12 and declared_income > 0:
        score += 10

    if any(int(v.get("engine_cc") or 0) >= 2000 for v in vehicles):
        score += 10

    score = min(score, 100)
    level = classify_deviation(score)

    reasons = []

    if str(filer_status).lower() == "non-filer":
        reasons.append("Citizen is marked as non-filer in FBR records.")

    if declared_income <= 0 and lifestyle_value > 0:
        reasons.append("Citizen has lifestyle/assets but zero declared income.")

    if vehicle_value > 0:
        reasons.append(f"Vehicle ownership detected worth PKR {vehicle_value:,}.")

    if property_value > 0:
        reasons.append(f"Property ownership detected worth PKR {property_value:,}.")

    if monthly_utility > 0:
        reasons.append(f"Monthly utility bill detected: PKR {monthly_utility:,}.")

    if travel_value > 0:
        reasons.append(f"Luxury travel spending detected: PKR {travel_value:,}.")

    if not reasons:
        reasons.append("No major deviation found.")

    response = {
        "found": True,
        "cnic": result["cnic"],
        "name": result["name"],
        "fiscal_year": fiscal_year,
        "declared_income": declared_income,
        "tax_paid": tax_paid,
        "filer_status": filer_status,
        "vehicle_value": vehicle_value,
        "property_value": property_value,
        "monthly_utility_bill": monthly_utility,
        "annual_utility_spending": annual_utility,
        "travel_value": travel_value,
        "observed_lifestyle_value": lifestyle_value,
        "deviation_score": score,
        "deviation_level": level,
        "undeclared_items": undeclared_items,
        "vehicles": vehicles,
        "properties": properties,
        "utilities": utilities,
        "travels": travels,
        "reasons": reasons,
        "summary": (
            f"{result['name']} has declared income of PKR {declared_income:,}, "
            f"but observed lifestyle/assets are worth PKR {lifestyle_value:,}. "
            f"Deviation score is {score}/100 and risk level is {level}."
        )
    }

    await risk_scores_collection.update_one(
        {"cnic": str(cnic)},
        {"$set": {"declaration_gap": response}},
        upsert=True
    )

    return response