from connection.database import get_driver, risk_scores_collection

driver = get_driver()


def safe_number(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def risk_level(score):
    if score >= 70:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def calculate_deviation_score(declared_income, observed_lifestyle_value, tax_paid):
    gap = max(observed_lifestyle_value - declared_income, 0)

    if declared_income > 0:
        deviation_percentage = min((gap / declared_income) * 100, 500)
    elif observed_lifestyle_value > 0:
        deviation_percentage = 500
    else:
        deviation_percentage = 0

    base_score = min(round(deviation_percentage / 5), 100)
    tax_penalty = 10 if observed_lifestyle_value > 0 and tax_paid <= 10000 else 0
    final_score = min(base_score + tax_penalty, 100)

    return final_score, deviation_percentage, gap, tax_penalty


async def calculate_year_score(cnic, fiscal_year):
    cnic_str = str(cnic)
    fy = str(fiscal_year)

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Citizen {cnic: $cnic})

            OPTIONAL MATCH (c)-[:FILED]->(t:TaxRecord)
            WHERE toString(coalesce(t.fiscal_year, $fy)) = $fy

            OPTIONAL MATCH (c)-[:OWNS]->(v:Vehicle)
            WHERE toString(coalesce(v.fiscal_year, $fy)) = $fy

            OPTIONAL MATCH (c)-[:OWNS]->(p:Property)
            WHERE toString(coalesce(p.fiscal_year, $fy)) = $fy

            OPTIONAL MATCH (c)-[:USES]->(u:Utility)
            WHERE toString(coalesce(u.fiscal_year, $fy)) = $fy

            RETURN
                c.name AS name,
                sum(DISTINCT coalesce(t.declared_income, 0)) AS declared_income,
                sum(DISTINCT coalesce(t.tax_paid, 0)) AS tax_paid,
                sum(DISTINCT coalesce(v.value, 0)) AS vehicle_value,
                sum(DISTINCT coalesce(p.value, 0)) AS property_value,
                sum(DISTINCT coalesce(u.avg_bill, 0)) AS monthly_utility_bill
        """, cnic=cnic_str, fy=fy).single()

    declared_income = safe_number(result["declared_income"] if result else 0)
    tax_paid = safe_number(result["tax_paid"] if result else 0)
    vehicle_value = safe_number(result["vehicle_value"] if result else 0)
    property_value = safe_number(result["property_value"] if result else 0)
    monthly_utility_bill = safe_number(result["monthly_utility_bill"] if result else 0)

    yearly_utility_value = monthly_utility_bill * 12

    observed_lifestyle_value = (
        (vehicle_value * 0.10)
        + (property_value * 0.10)
        + yearly_utility_value
    )

    score, deviation_percentage, gap, tax_penalty = calculate_deviation_score(
        declared_income,
        observed_lifestyle_value,
        tax_paid
    )

    audit_trail = [
        f"Declared income for fiscal year {fy}: PKR {declared_income:,.0f}.",
        f"Vehicle lifestyle proxy: 10% of PKR {vehicle_value:,.0f} = PKR {(vehicle_value * 0.10):,.0f}.",
        f"Property lifestyle proxy: 10% of PKR {property_value:,.0f} = PKR {(property_value * 0.10):,.0f}.",
        f"Annual utility value: PKR {monthly_utility_bill:,.0f} × 12 = PKR {yearly_utility_value:,.0f}.",
        f"Observed lifestyle value: PKR {observed_lifestyle_value:,.0f}.",
        f"Income-lifestyle gap: PKR {gap:,.0f}.",
        f"Deviation percentage: {deviation_percentage:.2f}%.",
        f"Base risk score: {min(round(deviation_percentage / 5), 100)}/100."
    ]

    if tax_penalty > 0:
        audit_trail.append(
            f"Low tax paid penalty added: +{tax_penalty} because tax paid is PKR {tax_paid:,.0f}."
        )

    audit_trail.append(f"Final risk score: {score}/100.")
    audit_trail.append(f"Risk level: {risk_level(score)}.")

    result_data = {
        "cnic": cnic_str,
        "fiscal_year": fy,
        "name": result["name"] if result else None,
        "declared_income": round(declared_income, 2),
        "tax_paid": round(tax_paid, 2),
        "vehicle_value": round(vehicle_value, 2),
        "property_value": round(property_value, 2),
        "monthly_utility_bill": round(monthly_utility_bill, 2),
        "yearly_utility_value": round(yearly_utility_value, 2),
        "observed_lifestyle_value": round(observed_lifestyle_value, 2),
        "income_lifestyle_gap": round(gap, 2),
        "deviation_percentage": round(deviation_percentage, 2),
        "risk_score": score,
        "deviation_score": score,
        "risk_level": risk_level(score),
        "audit_trail": audit_trail
    }

    await risk_scores_collection.update_one(
        {"cnic": cnic_str, "fiscal_year": fy},
        {"$set": result_data},
        upsert=True
    )

    print(f"[MONGO SAVED] CNIC={cnic_str} YEAR={fy} SCORE={score} RISK={risk_level(score)}")

    return result_data


async def get_available_years(cnic):
    with driver.session() as session:
        rows = session.run("""
            MATCH (c:Citizen {cnic: $cnic})

            OPTIONAL MATCH (c)-[:FILED]->(t:TaxRecord)
            OPTIONAL MATCH (c)-[:OWNS]->(v:Vehicle)
            OPTIONAL MATCH (c)-[:OWNS]->(p:Property)
            OPTIONAL MATCH (c)-[:USES]->(u:Utility)

            WITH
                collect(DISTINCT t.fiscal_year) +
                collect(DISTINCT v.fiscal_year) +
                collect(DISTINCT p.fiscal_year) +
                collect(DISTINCT u.fiscal_year) AS years

            UNWIND years AS year
            WITH DISTINCT year
            WHERE year IS NOT NULL
            RETURN toString(year) AS fiscal_year
            ORDER BY fiscal_year
        """, cnic=str(cnic))

        return [row["fiscal_year"] for row in rows]


async def calculate_risk_score(cnic, fiscal_year="All", force_recalculate=False):
    cnic_str = str(cnic)
    fy = "All" if fiscal_year in [None, "", "All", "all"] else str(fiscal_year)

    if not force_recalculate:
        existing = await risk_scores_collection.find_one(
            {"cnic": cnic_str, "fiscal_year": fy}
        )

        if existing:
            existing["_id"] = str(existing["_id"])
            print(f"[SKIPPED] Existing score found CNIC={cnic_str} YEAR={fy}")
            return existing

    if fy != "All":
        return await calculate_year_score(cnic_str, fy)

    years = await get_available_years(cnic_str)

    if not years:
        years = ["2026"]

    yearly_scores = []

    for year in years:
        score = await calculate_year_score(cnic_str, year)
        yearly_scores.append(score)

    count = len(yearly_scores)

    avg_income = sum(x["declared_income"] for x in yearly_scores) / count
    avg_tax_paid = sum(x["tax_paid"] for x in yearly_scores) / count
    avg_vehicle_value = sum(x["vehicle_value"] for x in yearly_scores) / count
    avg_property_value = sum(x["property_value"] for x in yearly_scores) / count
    avg_monthly_utility_bill = sum(x["monthly_utility_bill"] for x in yearly_scores) / count
    avg_lifestyle = sum(x["observed_lifestyle_value"] for x in yearly_scores) / count
    avg_gap = sum(x["income_lifestyle_gap"] for x in yearly_scores) / count
    avg_deviation = sum(x["deviation_percentage"] for x in yearly_scores) / count
    avg_score = round(sum(x["risk_score"] for x in yearly_scores) / count)

    result_data = {
        "cnic": cnic_str,
        "fiscal_year": "All",
        "name": yearly_scores[0].get("name"),
        "years_used": years,
        "years_count": count,
        "declared_income": round(avg_income, 2),
        "tax_paid": round(avg_tax_paid, 2),
        "vehicle_value": round(avg_vehicle_value, 2),
        "property_value": round(avg_property_value, 2),
        "monthly_utility_bill": round(avg_monthly_utility_bill, 2),
        "observed_lifestyle_value": round(avg_lifestyle, 2),
        "income_lifestyle_gap": round(avg_gap, 2),
        "deviation_percentage": round(avg_deviation, 2),
        "risk_score": avg_score,
        "deviation_score": avg_score,
        "risk_level": risk_level(avg_score),
        "audit_trail": [
            f"All years selected: average calculated from {count} fiscal year(s).",
            f"Years used: {', '.join(years)}.",
            f"Average declared income: PKR {avg_income:,.0f}.",
            f"Average tax paid: PKR {avg_tax_paid:,.0f}.",
            f"Average observed lifestyle value: PKR {avg_lifestyle:,.0f}.",
            f"Average income-lifestyle gap: PKR {avg_gap:,.0f}.",
            f"Average deviation percentage: {avg_deviation:.2f}%.",
            f"Final average risk score: {avg_score}/100.",
            f"Risk level: {risk_level(avg_score)}."
        ]
    }

    await risk_scores_collection.update_one(
        {"cnic": cnic_str, "fiscal_year": "All"},
        {"$set": result_data},
        upsert=True
    )

    print(f"[MONGO SAVED] CNIC={cnic_str} YEAR=All SCORE={avg_score} RISK={risk_level(avg_score)}")

    return result_data


async def get_all_citizen_cnics():
    with driver.session() as session:
        rows = session.run("""
            MATCH (c:Citizen)
            WHERE c.cnic IS NOT NULL
            RETURN DISTINCT c.cnic AS cnic
            ORDER BY c.cnic
        """)

        return [str(row["cnic"]) for row in rows]


async def calculate_all_risk_scores(force_recalculate=False):
    existing_count = await risk_scores_collection.count_documents(
        {"fiscal_year": "All", "cnic": {"$exists": True}}
    )

    if existing_count > 0 and not force_recalculate:
        print(f"[SKIPPED BULK] {existing_count} scores already exist in MongoDB.")

        return {
            "message": "Risk scores already exist in MongoDB. Bulk calculation skipped.",
            "already_saved": existing_count,
            "calculated": False
        }

    cnics = await get_all_citizen_cnics()

    results = []
    success_count = 0
    failed_count = 0

    for cnic in cnics:
        try:
            score_data = await calculate_risk_score(
                cnic,
                "All",
                force_recalculate=force_recalculate
            )
            results.append(score_data)
            success_count += 1

        except Exception as e:
            failed_count += 1
            results.append({
                "cnic": str(cnic),
                "status": "failed",
                "error": str(e)
            })

    summary = {
        "message": "All citizen risk scores calculated and stored successfully",
        "mode": "ALL_YEARS",
        "total_citizens": len(cnics),
        "success_count": success_count,
        "failed_count": failed_count,
        "calculated": True
    }

    await risk_scores_collection.update_one(
        {"type": "bulk_summary", "mode": "ALL_YEARS"},
        {"$set": summary},
        upsert=True
    )

    print("[BULK COMPLETED] Risk scores saved in MongoDB.")

    return summary