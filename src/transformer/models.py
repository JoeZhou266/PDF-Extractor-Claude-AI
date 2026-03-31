"""JSON output schema for extracted PDF documents.

To change the output structure, edit the dataclasses here first,
then update the system prompt in transformer.py accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Address:
    """Postal address."""

    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


@dataclass
class Party:
    """A person or organisation mentioned in the document."""

    name: Optional[str] = None
    role: Optional[str] = None  # e.g. "sender", "recipient", "vendor", "customer"
    address: Optional[Address] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None


@dataclass
class LineItem:
    """A single line item within a document (invoice line, order row, etc.)."""

    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None


@dataclass
class DocumentOutput:
    """Top-level schema for extracted document data.

    ``raw_text`` is always populated from the extraction step and is excluded
    from accuracy comparisons during the training/validation workflow.
    """

    # ── Identity ──────────────────────────────────────────────────────────
    document_type: Optional[str] = None       # e.g. "invoice", "receipt", "contract"
    document_number: Optional[str] = None
    document_date: Optional[str] = None       # ISO 8601 preferred: YYYY-MM-DD
    due_date: Optional[str] = None

    # ── Parties ───────────────────────────────────────────────────────────
    parties: list[Party] = field(default_factory=list)

    # ── Financial ─────────────────────────────────────────────────────────
    currency: Optional[str] = None            # ISO 4217, e.g. "USD"
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    tax_rate: Optional[float] = None          # as a decimal, e.g. 0.10 for 10 %
    discount: Optional[float] = None
    total_amount: Optional[float] = None

    # ── Line items ────────────────────────────────────────────────────────
    line_items: list[LineItem] = field(default_factory=list)

    # ── Additional metadata ───────────────────────────────────────────────
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    reference_numbers: list[str] = field(default_factory=list)

    # ── Raw extraction (excluded from validation comparisons) ─────────────
    raw_text: Optional[str] = None
