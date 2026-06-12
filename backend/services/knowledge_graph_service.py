from services.risk_engine import calculate_risk_score
from connection.database import get_driver


def add_node(nodes, node_id, label, node_type, data=None):
    if node_id and node_id not in nodes:
        nodes[node_id] = {
            "id": node_id,
            "label": str(label or node_type),
            "type": node_type,
            "data": data or {}
        }


def add_edge(edges, source, target, label):
    if source and target:
        exists = any(
            e["source"] == source and e["target"] == target and e["label"] == label
            for e in edges
        )

        if not exists:
            edges.append({
                "source": source,
                "target": target,
                "label": label
            })


async def search_citizens_service(q=""):
    driver = get_driver()

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Citizen)
            WITH
                c,
                coalesce(c.name, "Unknown Citizen") AS display_name,
                coalesce(c.address, "") AS display_address
            WHERE
                $q = "" OR
                toLower(display_name) CONTAINS toLower($q) OR
                toString(c.cnic) CONTAINS $q
            RETURN
                c.cnic AS cnic,
                display_name AS name,
                display_address AS address
            ORDER BY name
            LIMIT 100
        """, q=q)

        return [
            {
                "cnic": row["cnic"],
                "name": row["name"],
                "address": row["address"]
            }
            for row in result
            if row["cnic"]
        ]


async def build_person_knowledge_graph(cnic, fiscal_year=None):
    driver = get_driver()
    fy = None if fiscal_year in [None, "", "All", "all"] else str(fiscal_year)

    risk_data = await calculate_risk_score(cnic)

    nodes = {}
    edges = []

    with driver.session() as session:
        citizen = session.run("""
            MATCH (c:Citizen {cnic: $cnic})
            RETURN
                c.cnic AS cnic,
                coalesce(c.name, "Unknown Citizen") AS name,
                coalesce(c.address, "") AS address
        """, cnic=str(cnic)).single()

        if not citizen:
            return {
                "found": False,
                "message": "Citizen not found",
                "nodes": [],
                "edges": [],
                "risk": risk_data,
                "fiscal_year": fy or "All"
            }

        person_id = f"person-{citizen['cnic']}"

        add_node(
            nodes,
            person_id,
            citizen["name"],
            "Person",
            {
                "cnic": citizen["cnic"],
                "address": citizen["address"]
            }
        )

        vehicles = session.run("""
            MATCH (c:Citizen {cnic: $cnic})-[r:OWNS]->(v:Vehicle)
            WHERE $fy IS NULL OR r.fiscal_year = $fy OR r.fiscal_year IS NULL
            RETURN DISTINCT
                v.reg_no AS reg_no,
                v.make_model AS model,
                v.engine_cc AS engine_cc,
                v.value AS value,
                r.fiscal_year AS fiscal_year
        """, cnic=str(cnic), fy=fy)

        for row in vehicles:
            if not row["reg_no"]:
                continue

            node_id = f"vehicle-{row['reg_no']}"

            add_node(
                nodes,
                node_id,
                row["model"] or row["reg_no"],
                "Vehicle",
                {
                    "reg_no": row["reg_no"],
                    "model": row["model"],
                    "engine_cc": row["engine_cc"],
                    "value": row["value"],
                    "fiscal_year": row["fiscal_year"]
                }
            )

            add_edge(edges, person_id, node_id, "OWNS")

        properties = session.run("""
            MATCH (c:Citizen {cnic: $cnic})-[r:OWNS]->(p:Property)
            WHERE $fy IS NULL OR r.fiscal_year = $fy OR r.fiscal_year IS NULL
            RETURN DISTINCT
                p.registry_no AS registry_no,
                p.type AS type,
                p.address AS address,
                p.value AS value,
                p.area_marla AS area_marla,
                r.fiscal_year AS fiscal_year
        """, cnic=str(cnic), fy=fy)

        property_node_ids = []

        for row in properties:
            if not row["registry_no"]:
                continue

            node_id = f"property-{row['registry_no']}"
            property_node_ids.append(node_id)

            add_node(
                nodes,
                node_id,
                row["type"] or row["registry_no"],
                "Property",
                {
                    "registry_no": row["registry_no"],
                    "type": row["type"],
                    "address": row["address"],
                    "value": row["value"],
                    "area_marla": row["area_marla"],
                    "fiscal_year": row["fiscal_year"]
                }
            )

            add_edge(edges, person_id, node_id, "OWNS")

        utilities = session.run("""
            MATCH (c:Citizen {cnic: $cnic})-[r:USES]->(u:Utility)
            WHERE $fy IS NULL OR r.fiscal_year = $fy OR r.fiscal_year IS NULL
            RETURN DISTINCT
                u.meter_ref AS meter_ref,
                u.type AS type,
                u.avg_bill AS avg_bill,
                u.address AS address,
                r.fiscal_year AS fiscal_year
        """, cnic=str(cnic), fy=fy)

        for index, row in enumerate(utilities):
            if not row["meter_ref"]:
                continue

            node_id = f"utility-{row['meter_ref']}"

            add_node(
                nodes,
                node_id,
                row["meter_ref"],
                "Utility Meter",
                {
                    "meter_ref": row["meter_ref"],
                    "type": row["type"],
                    "avg_bill": row["avg_bill"],
                    "address": row["address"],
                    "fiscal_year": row["fiscal_year"]
                }
            )

            add_edge(edges, person_id, node_id, "USES")

            if property_node_ids:
                property_id = property_node_ids[index % len(property_node_ids)]
                add_edge(edges, property_id, node_id, "HAS_METER")

        tax_records = session.run("""
            MATCH (c:Citizen {cnic: $cnic})-[r:FILED]->(t:TaxRecord)
            WHERE $fy IS NULL OR r.fiscal_year = $fy OR r.fiscal_year IS NULL
            RETURN DISTINCT
                t.fbr_id AS fbr_id,
                t.declared_income AS declared_income,
                t.tax_paid AS tax_paid,
                t.filer_status AS filer_status,
                r.fiscal_year AS fiscal_year
        """, cnic=str(cnic), fy=fy)

        for row in tax_records:
            if not row["fbr_id"]:
                continue

            node_id = f"tax-{row['fbr_id']}"

            add_node(
                nodes,
                node_id,
                f"Tax Return {row['filer_status'] or ''}",
                "Tax Return",
                {
                    "fbr_id": row["fbr_id"],
                    "declared_income": row["declared_income"],
                    "tax_paid": row["tax_paid"],
                    "filer_status": row["filer_status"],
                    "fiscal_year": row["fiscal_year"]
                }
            )

            add_edge(edges, person_id, node_id, "FILED")

        travels = session.run("""
            MATCH (c:Citizen {cnic: $cnic})-[r:TRAVELLED]->(tr:Travel)
            WHERE $fy IS NULL OR r.fiscal_year = $fy OR r.fiscal_year IS NULL
            RETURN DISTINCT
                tr.travel_id AS travel_id,
                tr.destination AS destination,
                tr.ticket_class AS ticket_class,
                tr.trip_cost AS trip_cost,
                tr.travel_date AS travel_date,
                r.fiscal_year AS fiscal_year
        """, cnic=str(cnic), fy=fy)

        for row in travels:
            if not row["travel_id"]:
                continue

            node_id = f"travel-{row['travel_id']}"

            add_node(
                nodes,
                node_id,
                row["destination"] or "Luxury Travel",
                "Travel",
                {
                    "travel_id": row["travel_id"],
                    "destination": row["destination"],
                    "ticket_class": row["ticket_class"],
                    "trip_cost": row["trip_cost"],
                    "travel_date": row["travel_date"],
                    "fiscal_year": row["fiscal_year"]
                }
            )

            add_edge(edges, person_id, node_id, "TRAVELLED")

    return {
        "found": True,
        "fiscal_year": fy or "All",
        "citizen": {
            "cnic": citizen["cnic"],
            "name": citizen["name"],
            "address": citizen["address"]
        },
        "risk": risk_data,
        "nodes": list(nodes.values()),
        "edges": edges
    }