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
    q = str(q or "").strip()

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Citizen)

            OPTIONAL MATCH (c)-[:OWNS]->(v:Vehicle)
            OPTIONAL MATCH (c)-[:OWNS]->(p:Property)
            OPTIONAL MATCH (c)-[:USES]->(u:Utility)
            OPTIONAL MATCH (c)-[:FILED]->(t:TaxRecord)
            OPTIONAL MATCH (c)-[:TRAVELLED]->(tr:Travel)

            WITH c,
                collect(DISTINCT c.name) +
                collect(DISTINCT c.latest_name) +
                collect(DISTINCT v.owner_name) +
                collect(DISTINCT p.buyer_name) +
                collect(DISTINCT u.consumer_name) +
                collect(DISTINCT t.full_name) +
                collect(DISTINCT tr.traveler_name) AS names,

                collect(DISTINCT c.address) +
                collect(DISTINCT c.latest_address) +
                collect(DISTINCT p.address) +
                collect(DISTINCT u.address) AS addresses

            WITH c,
                [name IN names WHERE name IS NOT NULL AND trim(toString(name)) <> ""] AS clean_names,
                [addr IN addresses WHERE addr IS NOT NULL AND trim(toString(addr)) <> ""] AS clean_addresses

            WHERE
                $q = ""
                OR toString(c.cnic) CONTAINS $q
                OR any(name IN clean_names WHERE toLower(toString(name)) CONTAINS toLower($q))

            RETURN
                c.cnic AS cnic,
                clean_names AS all_names,
                clean_addresses AS all_addresses

            ORDER BY cnic
            LIMIT 100
        """, q=q)

        people = []

        for row in result:
            all_names = []
            for name in row["all_names"]:
                name = str(name).strip()
                if name and name not in all_names:
                    all_names.append(name)

            all_addresses = []
            for address in row["all_addresses"]:
                address = str(address).strip()
                if address and address not in all_addresses:
                    all_addresses.append(address)

            people.append({
                "cnic": row["cnic"],
                "name": all_names[0] if all_names else "Unknown Citizen",
                "address": all_addresses[0] if all_addresses else "",
                "all_names": all_names,
                "all_addresses": all_addresses
            })

        return people


async def build_person_knowledge_graph(cnic, fiscal_year=None):
    driver = get_driver()
    fy = None if fiscal_year in [None, "", "All", "all"] else str(fiscal_year)

    risk_data = await calculate_risk_score(cnic, fy or "All")

    nodes = {}
    edges = []

    with driver.session() as session:
        citizen = session.run("""
            MATCH (c:Citizen {cnic: $cnic})
            RETURN
                c.cnic AS cnic,
                coalesce(c.name, c.latest_name, "Unknown Citizen") AS name,
                coalesce(c.address, c.latest_address, "") AS address
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
                "address": citizen["address"],
                "owner_name": citizen["name"]
            }
        )

        property_node_ids = []

        vehicles = session.run("""
            MATCH (c:Citizen {cnic: $cnic})-[r:OWNS]->(v:Vehicle)
            WHERE $fy IS NULL OR toString(r.fiscal_year) = $fy OR r.fiscal_year IS NULL
            RETURN DISTINCT
                v.reg_no AS reg_no,
                v.owner_name AS owner_name,
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
                    "owner_name": row["owner_name"] or citizen["name"],
                    "model": row["model"],
                    "engine_cc": row["engine_cc"],
                    "value": row["value"],
                    "fiscal_year": row["fiscal_year"]
                }
            )

            add_edge(edges, person_id, node_id, "OWNS")

        properties = session.run("""
            MATCH (c:Citizen {cnic: $cnic})-[r:OWNS]->(p:Property)
            WHERE $fy IS NULL OR toString(r.fiscal_year) = $fy OR r.fiscal_year IS NULL
            RETURN DISTINCT
                p.registry_no AS registry_no,
                p.buyer_name AS buyer_name,
                p.type AS type,
                p.address AS address,
                p.value AS value,
                p.area_marla AS area_marla,
                r.fiscal_year AS fiscal_year
        """, cnic=str(cnic), fy=fy)

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
                    "buyer_name": row["buyer_name"] or citizen["name"],
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
            WHERE $fy IS NULL OR toString(r.fiscal_year) = $fy OR r.fiscal_year IS NULL
            RETURN DISTINCT
                u.meter_ref AS meter_ref,
                u.consumer_name AS consumer_name,
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
                    "consumer_name": row["consumer_name"] or citizen["name"],
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
            WHERE $fy IS NULL OR toString(r.fiscal_year) = $fy OR r.fiscal_year IS NULL
            RETURN DISTINCT
                t.fbr_id AS fbr_id,
                t.full_name AS full_name,
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
                    "full_name": row["full_name"] or citizen["name"],
                    "declared_income": row["declared_income"],
                    "tax_paid": row["tax_paid"],
                    "filer_status": row["filer_status"],
                    "fiscal_year": row["fiscal_year"]
                }
            )

            add_edge(edges, person_id, node_id, "FILED")

        travels = session.run("""
            MATCH (c:Citizen {cnic: $cnic})-[r:TRAVELLED]->(tr:Travel)
            WHERE $fy IS NULL OR toString(r.fiscal_year) = $fy OR r.fiscal_year IS NULL
            RETURN DISTINCT
                tr.travel_id AS travel_id,
                tr.traveler_name AS traveler_name,
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
                    "traveler_name": row["traveler_name"] or citizen["name"],
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