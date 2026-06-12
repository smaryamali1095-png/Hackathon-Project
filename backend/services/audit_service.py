from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_investigation_report(cnic, risk_data):
    vehicles = risk_data.get("vehicles", [])
    properties = risk_data.get("properties", [])
    utilities = risk_data.get("utilities", [])
    travels = risk_data.get("travels", [])

    vehicle_lines = "\n".join([
        f"- {v.get('model')} | Reg No: {v.get('reg_no')} | CC: {v.get('engine_cc')} | Value: PKR {v.get('value')}"
        for v in vehicles
    ]) or "No vehicles found."

    property_lines = "\n".join([
        f"- {p.get('type')} | Registry: {p.get('registry_no')} | Value: PKR {p.get('value')}"
        for p in properties
    ]) or "No properties found."

    utility_lines = "\n".join([
        f"- Meter: {u.get('meter_ref')} | Monthly Bill: PKR {u.get('avg_bill')}"
        for u in utilities
    ]) or "No utility records found."

    travel_lines = "\n".join([
        f"- Destination: {t.get('destination')} | Class: {t.get('ticket_class')} | Cost: PKR {t.get('trip_cost')}"
        for t in travels
    ]) or "No luxury travel records found."

    return f"""
INVESTIGATION SUMMARY
---------------------

CNIC:
{cnic}

Risk Level:
{risk_data.get('risk_level')}

Tax Compliance Deviation Score:
{risk_data.get('risk_score')}

Declared Income:
PKR {risk_data.get('declared_income', 0):,}

Tax Paid:
PKR {risk_data.get('tax_paid', 0):,}

Filer Status:
{risk_data.get('filer_status')}

Observed Lifestyle Value:
PKR {risk_data.get('observed_lifestyle_value', 0):,}

Deviation Amount:
PKR {risk_data.get('deviation_amount', 0):,}

Deviation Percentage:
{risk_data.get('deviation_percentage')}%

Vehicles:
{vehicle_lines}

Properties:
{property_lines}

Utilities:
{utility_lines}

Luxury Travel:
{travel_lines}

Explanation:
{risk_data.get('explanation')}

Recommendation:
This individual should be reviewed because declared income appears inconsistent with observed assets, property ownership, vehicle ownership, electricity consumption, and luxury travel spending.
"""


def create_pdf_report(cnic, risk_data):
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    file_path = reports_dir / f"investigation_report_{cnic}.pdf"
    report_text = generate_investigation_report(cnic, risk_data)

    c = canvas.Canvas(str(file_path), pagesize=letter)
    width, height = letter

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Tax Intel AI - Investigation Report")

    y -= 35
    c.setFont("Helvetica", 10)

    for line in report_text.split("\n"):
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 50

        c.drawString(50, y, str(line)[:110])
        y -= 15

    c.save()
    return str(file_path)