import torch
import numpy as np
from torch import nn
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
from sklearn.preprocessing import StandardScaler

from connection.database import get_driver, risk_scores_collection

driver = get_driver()


class GCNEncoder(nn.Module):
    def __init__(self, input_dim, hidden_dim=32, embedding_dim=16):
        super().__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, embedding_dim)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        z = self.conv2(x, edge_index)
        return z


class GraphAutoEncoder(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.encoder = GCNEncoder(input_dim)
        self.decoder = nn.Linear(16, input_dim)

    def forward(self, x, edge_index):
        z = self.encoder(x, edge_index)
        reconstructed = self.decoder(z)
        return reconstructed, z


def classify(score):
    if score < 25:
        return "Low"
    elif score < 60:
        return "Medium"
    elif score < 85:
        return "High"
    return "Critical"


def normalize_score(errors):
    min_e = float(errors.min())
    max_e = float(errors.max())

    if max_e - min_e == 0:
        return np.ones_like(errors) * 50

    return ((errors - min_e) / (max_e - min_e)) * 100


async def run_gnn_anomaly_detection():
    citizens = []
    node_index = {}
    edges = []

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Citizen)
            OPTIONAL MATCH (c)-[:OWNS]->(v:Vehicle)
            OPTIONAL MATCH (c)-[:OWNS]->(p:Property)
            OPTIONAL MATCH (c)-[:USES]->(u:Utility)
            OPTIONAL MATCH (c)-[:FILED]->(t:TaxRecord)
            OPTIONAL MATCH (c)-[r]-()
            RETURN
                c.cnic AS cnic,
                c.name AS name,
                count(DISTINCT v) AS vehicle_count,
                count(DISTINCT p) AS property_count,
                count(DISTINCT u) AS utility_count,
                count(DISTINCT t) AS tax_record_count,
                count(DISTINCT r) AS graph_degree,
                coalesce(sum(DISTINCT v.value), 0) AS vehicle_value,
                coalesce(sum(DISTINCT p.value), 0) AS property_value,
                coalesce(sum(DISTINCT u.avg_bill), 0) AS monthly_bill,
                coalesce(max(t.declared_income), 0) AS declared_income,
                coalesce(max(t.tax_paid), 0) AS tax_paid,
                coalesce(max(t.filer_status), 'Unknown') AS filer_status
        """)

        for i, row in enumerate(result):
            cnic = row["cnic"]
            if not cnic:
                continue

            node_index[cnic] = i

            declared_income = int(row["declared_income"] or 0)
            tax_paid = int(row["tax_paid"] or 0)
            vehicle_value = int(row["vehicle_value"] or 0)
            property_value = int(row["property_value"] or 0)
            monthly_bill = int(row["monthly_bill"] or 0)
            annual_bill = monthly_bill * 12
            lifestyle_value = vehicle_value + property_value + annual_bill

            ratio = lifestyle_value / declared_income if declared_income > 0 else 0
            tax_ratio = tax_paid / declared_income if declared_income > 0 else 0

            citizens.append({
                "cnic": cnic,
                "name": row["name"],
                "vehicle_count": int(row["vehicle_count"] or 0),
                "property_count": int(row["property_count"] or 0),
                "utility_count": int(row["utility_count"] or 0),
                "tax_record_count": int(row["tax_record_count"] or 0),
                "graph_degree": int(row["graph_degree"] or 0),
                "vehicle_value": vehicle_value,
                "property_value": property_value,
                "monthly_bill": monthly_bill,
                "annual_bill": annual_bill,
                "declared_income": declared_income,
                "tax_paid": tax_paid,
                "filer_status": row["filer_status"],
                "lifestyle_value": lifestyle_value,
                "lifestyle_income_ratio": ratio,
                "tax_income_ratio": tax_ratio
            })

        rels = session.run("""
            MATCH (a:Citizen)-[*1..2]-(b:Citizen)
            WHERE a.cnic IS NOT NULL AND b.cnic IS NOT NULL AND a.cnic <> b.cnic
            RETURN DISTINCT a.cnic AS source, b.cnic AS target
            LIMIT 10000
        """)

        for row in rels:
            s = row["source"]
            t = row["target"]

            if s in node_index and t in node_index:
                edges.append([node_index[s], node_index[t]])
                edges.append([node_index[t], node_index[s]])

    if len(citizens) < 2:
        return []

    features = []

    for c in citizens:
        features.append([
            c["vehicle_count"],
            c["property_count"],
            c["utility_count"],
            c["tax_record_count"],
            c["graph_degree"],
            c["vehicle_value"],
            c["property_value"],
            c["monthly_bill"],
            c["annual_bill"],
            c["declared_income"],
            c["tax_paid"],
            c["lifestyle_value"],
            c["lifestyle_income_ratio"],
            c["tax_income_ratio"],
            1 if str(c["filer_status"]).lower() == "non-filer" else 0
        ])

    scaler = StandardScaler()
    x_np = scaler.fit_transform(np.array(features, dtype=np.float32))

    x = torch.tensor(x_np, dtype=torch.float)

    if not edges:
        edges = [[i, i] for i in range(len(citizens))]

    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()

    data = Data(x=x, edge_index=edge_index)

    model = GraphAutoEncoder(input_dim=x.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=1e-4)
    loss_fn = nn.MSELoss()

    model.train()

    for epoch in range(200):
        optimizer.zero_grad()
        reconstructed, _ = model(data.x, data.edge_index)
        loss = loss_fn(reconstructed, data.x)
        loss.backward()
        optimizer.step()

    model.eval()

    with torch.no_grad():
        reconstructed, embeddings = model(data.x, data.edge_index)
        reconstruction_error = torch.mean((data.x - reconstructed) ** 2, dim=1)
        errors = reconstruction_error.cpu().numpy()
        scores = normalize_score(errors)

    results = []

    for i, c in enumerate(citizens):
        score = round(float(scores[i]), 2)

        reasons = []

        if c["lifestyle_income_ratio"] > 5:
            reasons.append("Lifestyle value is much higher than declared income")

        if str(c["filer_status"]).lower() == "non-filer":
            reasons.append("Non-filer detected")

        if c["vehicle_value"] > 10000000:
            reasons.append("High-value vehicle ownership")

        if c["property_value"] > 20000000:
            reasons.append("High-value property ownership")

        if c["monthly_bill"] > 150000:
            reasons.append("High monthly utility consumption")

        if c["graph_degree"] >= 4:
            reasons.append("Multiple graph relationships detected")

        if not reasons:
            reasons.append("Anomaly detected from GNN reconstruction error")

        result = {
            "cnic": c["cnic"],
            "name": c["name"],
            "gnn_anomaly_score": score,
            "graph_anomaly_score": score,
            "graph_risk_level": classify(score),
            "vehicle_count": c["vehicle_count"],
            "property_count": c["property_count"],
            "utility_count": c["utility_count"],
            "tax_record_count": c["tax_record_count"],
            "graph_degree": c["graph_degree"],
            "vehicle_value": c["vehicle_value"],
            "property_value": c["property_value"],
            "monthly_utility_bill": c["monthly_bill"],
            "declared_income": c["declared_income"],
            "tax_paid": c["tax_paid"],
            "filer_status": c["filer_status"],
            "lifestyle_value": c["lifestyle_value"],
            "embedding": embeddings[i].cpu().numpy().tolist(),
            "reasons": reasons,
            "model": "GCN Graph AutoEncoder"
        }

        results.append(result)

        await risk_scores_collection.update_one(
            {"cnic": c["cnic"]},
            {
                "$set": {
                    "gnn_ai": result,
                    "gnn_anomaly_score": score,
                    "graph_anomaly_score": score,
                    "graph_risk_level": classify(score)
                }
            },
            upsert=True
        )

    return sorted(results, key=lambda x: x["gnn_anomaly_score"], reverse=True)