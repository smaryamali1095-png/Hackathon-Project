import numpy as np
from sklearn.ensemble import IsolationForest

from connection.database import get_driver, risk_scores_collection

driver = get_driver()


def classify_graph_risk(score):
    if score < 25:
        return "Low"
    elif score < 60:
        return "Medium"
    elif score < 85:
        return "High"
    return "Critical"


async def graph_anomaly_detection():
    """
    Graph-AI / GNN-inspired anomaly detection.

    It extracts graph features from Neo4j:
    - vehicle count
    - property count
    - utility count
    - declared income
    - tax paid
    - vehicle value
    - property value
    - utility spending
    - node degree / relationship count

    Then IsolationForest detects abnormal citizen profiles.
    """

    graph_rows = []

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Citizen)

            OPTIONAL MATCH (c)-[:OWNS]->(v:Vehicle)
            OPTIONAL MATCH (c)-[:OWNS]->(p:Property)
            OPTIONAL MATCH (c)-[:USES]->(u:Utility)
            OPTIONAL MATCH (c)-[:FILED]->(t:TaxRecord)

            OPTIONAL MATCH (c)-[rel]-()
            
            RETURN
                c.cnic AS cnic,
                c.name AS name,

                count(DISTINCT v) AS vehicle_count,
                count(DISTINCT p) AS property_count,
                count(DISTINCT u) AS utility_count,
                count(DISTINCT t) AS tax_record_count,
                count(DISTINCT rel) AS graph_degree,

                coalesce(sum(DISTINCT v.value), 0) AS vehicle_value,
                coalesce(sum(DISTINCT p.value), 0) AS property_value,
                coalesce(sum(DISTINCT u.avg_bill), 0) AS monthly_utility_bill,

                coalesce(max(t.declared_income), 0) AS declared_income,
                coalesce(max(t.tax_paid), 0) AS tax_paid,
                coalesce(max(t.filer_status), 'Unknown') AS filer_status
        """)

        for row in result:
            declared_income = int(row["declared_income"] or 0)
            tax_paid = int(row["tax_paid"] or 0)
            vehicle_value = int(row["vehicle_value"] or 0)
            property_value = int(row["property_value"] or 0)
            monthly_utility_bill = int(row["monthly_utility_bill"] or 0)

            annual_utility_spending = monthly_utility_bill * 12
            lifestyle_value = (
                vehicle_value +
                property_value +
                annual_utility_spending
            )

            if declared_income > 0:
                lifestyle_income_ratio = lifestyle_value / declared_income
                tax_income_ratio = tax_paid / declared_income
            else:
                lifestyle_income_ratio = 0
                tax_income_ratio = 0

            graph_rows.append({
                "cnic": row["cnic"],
                "name": row["name"],
                "vehicle_count": int(row["vehicle_count"] or 0),
                "property_count": int(row["property_count"] or 0),
                "utility_count": int(row["utility_count"] or 0),
                "tax_record_count": int(row["tax_record_count"] or 0),
                "graph_degree": int(row["graph_degree"] or 0),

                "vehicle_value": vehicle_value,
                "property_value": property_value,
                "monthly_utility_bill": monthly_utility_bill,
                "annual_utility_spending": annual_utility_spending,
                "declared_income": declared_income,
                "tax_paid": tax_paid,
                "filer_status": row["filer_status"],

                "lifestyle_value": lifestyle_value,
                "lifestyle_income_ratio": lifestyle_income_ratio,
                "tax_income_ratio": tax_income_ratio
            })

    if not graph_rows:
        return []

    features = []

    for row in graph_rows:
        features.append([
            row["vehicle_count"],
            row["property_count"],
            row["utility_count"],
            row["tax_record_count"],
            row["graph_degree"],
            row["vehicle_value"],
            row["property_value"],
            row["monthly_utility_bill"],
            row["annual_utility_spending"],
            row["declared_income"],
            row["tax_paid"],
            row["lifestyle_value"],
            row["lifestyle_income_ratio"],
            row["tax_income_ratio"]
        ])

    X = np.array(features, dtype=float)

    model = IsolationForest(
        n_estimators=150,
        contamination=0.15,
        random_state=42
    )

    model.fit(X)

    raw_scores = model.decision_function(X)
    predictions = model.predict(X)

    min_score = raw_scores.min()
    max_score = raw_scores.max()

    results = []

    for index, row in enumerate(graph_rows):
        raw = raw_scores[index]

        if max_score - min_score == 0:
            normalized_score = 50
        else:
            normalized_score = 100 - (
                ((raw - min_score) / (max_score - min_score)) * 100
            )

        graph_anomaly_score = round(float(normalized_score), 2)

        if predictions[index] == -1:
            graph_anomaly_score = min(graph_anomaly_score + 15, 100)

        graph_risk_level = classify_graph_risk(graph_anomaly_score)

        reasons = []

        if row["lifestyle_income_ratio"] > 5:
            reasons.append("Lifestyle value is much higher than declared income")

        if row["filer_status"].lower() == "non-filer":
            reasons.append("Citizen is marked as non-filer")

        if row["monthly_utility_bill"] > 150000:
            reasons.append("High monthly utility consumption detected")

        if row["vehicle_value"] > 10000000:
            reasons.append("High-value vehicle ownership detected")

        if row["property_value"] > 20000000:
            reasons.append("High-value property ownership detected")

        if row["graph_degree"] >= 4:
            reasons.append("Citizen has multiple linked graph relationships")

        if not reasons:
            reasons.append("Graph structure is within normal range")

        result = {
            "cnic": row["cnic"],
            "name": row["name"],
            "graph_anomaly_score": graph_anomaly_score,
            "graph_risk_level": graph_risk_level,
            "is_anomaly": predictions[index] == -1,

            "vehicle_count": row["vehicle_count"],
            "property_count": row["property_count"],
            "utility_count": row["utility_count"],
            "tax_record_count": row["tax_record_count"],
            "graph_degree": row["graph_degree"],

            "vehicle_value": row["vehicle_value"],
            "property_value": row["property_value"],
            "monthly_utility_bill": row["monthly_utility_bill"],
            "annual_utility_spending": row["annual_utility_spending"],
            "declared_income": row["declared_income"],
            "tax_paid": row["tax_paid"],
            "filer_status": row["filer_status"],
            "lifestyle_value": row["lifestyle_value"],

            "reasons": reasons,
            "model": "IsolationForest graph-feature anomaly detector"
        }

        results.append(result)

        await risk_scores_collection.update_one(
            {"cnic": row["cnic"]},
            {
                "$set": {
                    "graph_ai": result,
                    "graph_anomaly_score": graph_anomaly_score,
                    "graph_risk_level": graph_risk_level
                }
            },
            upsert=True
        )

    return sorted(
        results,
        key=lambda x: x["graph_anomaly_score"],
        reverse=True
    )