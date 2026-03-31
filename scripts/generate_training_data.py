"""Generate demo invoice PDF and its ground-truth JSON for training/validation.

Run:
    python scripts/generate_training_data.py
"""

import dataclasses
import json
import sys
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transformer.models import Address, DocumentOutput, LineItem, Party

TRAINING_DIR = Path("pdfs/training")


# ── Ground-truth data ─────────────────────────────────────────────────────────

GROUND_TRUTH = DocumentOutput(
    document_type="invoice",
    document_number="INV-2024-0042",
    document_date="2024-03-15",
    due_date="2024-04-14",
    parties=[
        Party(
            name="Acme Supplies Co.",
            role="vendor",
            address=Address(
                street="500 Commerce Blvd",
                city="Chicago",
                state="IL",
                postal_code="60601",
                country="US",
            ),
            email="accounts@acmesupplies.com",
            phone="+1-312-555-0199",
            tax_id="36-1234567",
        ),
        Party(
            name="Bright Future Ltd.",
            role="customer",
            address=Address(
                street="88 Innovation Way",
                city="Austin",
                state="TX",
                postal_code="78701",
                country="US",
            ),
            email="ap@brightfuture.io",
            phone="+1-512-555-0177",
            tax_id="74-7654321",
        ),
    ],
    currency="USD",
    subtotal=2850.00,
    tax_amount=228.00,
    tax_rate=0.08,
    discount=0.00,
    total_amount=3078.00,
    line_items=[
        LineItem(description="Industrial Widget Model X", quantity=10, unit="pcs", unit_price=150.00, total=1500.00),
        LineItem(description="Heavy-Duty Connector Kit",  quantity=15, unit="pcs", unit_price=45.00,  total=675.00),
        LineItem(description="Premium Maintenance Bundle", quantity=3, unit="ea",  unit_price=225.00, total=675.00),
    ],
    notes="All prices in USD. Late payments subject to 1.5% monthly interest.",
    payment_terms="Net 30",
    reference_numbers=["PO-2024-00887", "CONTRACT-TX-009"],
    raw_text=None,
)


def generate_pdf(output_path: Path) -> None:
    """Render the ground-truth invoice as a text-based PDF."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    story = []

    # ── Header ────────────────────────────────────────────────────────────
    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=20, spaceAfter=4)
    story.append(Paragraph("INVOICE", title_style))
    story.append(Paragraph(f"Invoice #: {GROUND_TRUTH.document_number}", styles["Normal"]))
    story.append(Paragraph(f"Invoice Date: {GROUND_TRUTH.document_date}", styles["Normal"]))
    story.append(Paragraph(f"Due Date: {GROUND_TRUTH.due_date}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    # ── Parties ───────────────────────────────────────────────────────────
    vendor, customer = GROUND_TRUTH.parties
    party_data = [
        ["FROM", "BILL TO"],
        [
            f"{vendor.name}\n{vendor.address.street}\n{vendor.address.city}, {vendor.address.state} {vendor.address.postal_code}\n{vendor.address.country}\nEmail: {vendor.email}\nPhone: {vendor.phone}\nTax ID: {vendor.tax_id}",
            f"{customer.name}\n{customer.address.street}\n{customer.address.city}, {customer.address.state} {customer.address.postal_code}\n{customer.address.country}\nEmail: {customer.email}\nPhone: {customer.phone}\nTax ID: {customer.tax_id}",
        ],
    ]
    party_table = Table(party_data, colWidths=[3.25 * inch, 3.25 * inch])
    party_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A90D9")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("LEADING",    (0, 1), (-1, -1), 13),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
    ]))
    story.append(party_table)
    story.append(Spacer(1, 0.2 * inch))

    # ── Line Items ────────────────────────────────────────────────────────
    story.append(Paragraph("Line Items", styles["Heading3"]))
    item_data = [["Description", "Qty", "Unit", "Unit Price", "Total"]]
    for li in GROUND_TRUTH.line_items:
        item_data.append([
            li.description,
            str(li.quantity),
            li.unit,
            f"${li.unit_price:,.2f}",
            f"${li.total:,.2f}",
        ])
    item_table = Table(item_data, colWidths=[2.8 * inch, 0.5 * inch, 0.6 * inch, 1.0 * inch, 1.0 * inch])
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A90D9")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN",      (1, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 0.15 * inch))

    # ── Totals ────────────────────────────────────────────────────────────
    totals_data = [
        ["Subtotal:", f"${GROUND_TRUTH.subtotal:,.2f}"],
        [f"Tax ({GROUND_TRUTH.tax_rate * 100:.0f}%):", f"${GROUND_TRUTH.tax_amount:,.2f}"],
        ["Discount:", f"${GROUND_TRUTH.discount:,.2f}"],
        ["Total (USD):", f"${GROUND_TRUTH.total_amount:,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[5.5 * inch, 1.1 * inch])
    totals_table.setStyle(TableStyle([
        ("ALIGN",    (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 0.15 * inch))

    # ── References & Notes ────────────────────────────────────────────────
    story.append(Paragraph(f"Reference Numbers: {', '.join(GROUND_TRUTH.reference_numbers)}", styles["Normal"]))
    story.append(Paragraph(f"Payment Terms: {GROUND_TRUTH.payment_terms}", styles["Normal"]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(f"Notes: {GROUND_TRUTH.notes}", styles["Italic"]))

    doc.build(story)
    print(f"  PDF generated: {output_path}")


def generate_ground_truth_json(output_path: Path) -> None:
    """Write ground-truth JSON (raw_text excluded / null)."""
    data = dataclasses.asdict(GROUND_TRUTH)
    data["raw_text"] = None  # excluded from comparisons
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  Ground-truth JSON: {output_path}")


if __name__ == "__main__":
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating training data...")
    generate_pdf(TRAINING_DIR / "invoice_sample.pdf")
    generate_ground_truth_json(TRAINING_DIR / "invoice_sample.json")
    print("Done.")
