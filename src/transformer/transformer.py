"""Transform extracted PDF text into structured JSON using the Claude AI API."""

from __future__ import annotations

import dataclasses
import json
import logging
import os
from pathlib import Path
from typing import Any

import anthropic

_logger = logging.getLogger(__name__)

from .models import Address, DocumentOutput, LineItem, Party


_SYSTEM_PROMPT = """You are a document data extraction assistant.
Given raw text extracted from a PDF document, extract structured information and return it as a valid JSON object.

The JSON must match this exact schema (omit fields you cannot find, do not invent values):
{
  "document_type": string or null,
  "document_number": string or null,
  "document_date": string (ISO 8601 YYYY-MM-DD) or null,
  "due_date": string (ISO 8601 YYYY-MM-DD) or null,
  "parties": [
    {
      "name": string or null,
      "role": string or null,
      "address": {
        "street": string or null,
        "city": string or null,
        "state": string or null,
        "postal_code": string or null,
        "country": string or null
      } or null,
      "email": string or null,
      "phone": string or null,
      "tax_id": string or null
    }
  ],
  "currency": string (ISO 4217) or null,
  "subtotal": number or null,
  "tax_amount": number or null,
  "tax_rate": number (decimal, e.g. 0.10 for 10%) or null,
  "discount": number or null,
  "total_amount": number or null,
  "line_items": [
    {
      "description": string or null,
      "quantity": number or null,
      "unit": string or null,
      "unit_price": number or null,
      "total": number or null
    }
  ],
  "notes": string or null,
  "payment_terms": string or null,
  "reference_numbers": [string]
}

Rules:
- Preserve original casing for names, addresses, descriptions, and free-text fields.
- document_type must be lowercase (e.g. "invoice", "receipt", "contract").
- For party role use exactly one of: "vendor", "customer", "shipper", "consignee", "issuer", "recipient".
  - The party that issues/sends/bills is "vendor"; the party that receives/pays is "customer".
- Return ONLY the JSON object with no markdown fences, no explanation, no extra text."""


class Transformer:
    """Calls the Claude AI API to convert raw document text to :class:`DocumentOutput`."""

    def __init__(self, model: str = "claude-sonnet-4-6", max_tokens: int = 4096) -> None:
        """Initialise the transformer.

        Args:
            model: Claude model ID to use.
            max_tokens: Maximum tokens in the Claude response.

        Raises:
            EnvironmentError: If ``ANTHROPIC_API_KEY`` is not set.
        """
        _logger.debug("Transformer.__init__: start model=%s max_tokens=%d", model, max_tokens)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set.")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens
        _logger.debug("Transformer.__init__: complete model=%s", model)

    def transform(self, raw_text: str) -> DocumentOutput:
        """Send *raw_text* to Claude and parse the JSON response into a :class:`DocumentOutput`.

        Args:
            raw_text: Text extracted from a PDF page.

        Returns:
            Populated :class:`DocumentOutput` instance (``raw_text`` field is set here).

        Raises:
            ValueError: If Claude returns invalid JSON or an unexpected structure.
        """
        _logger.debug("Transformer.transform: start raw_text_len=%d", len(raw_text))
        message = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": raw_text}],
        )

        response_text = message.content[0].text.strip()

        try:
            data: dict[str, Any] = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Claude returned non-JSON response: {response_text[:200]}") from exc

        output = self._dict_to_output(data)
        output.raw_text = raw_text
        _logger.debug("Transformer.transform: complete document_type=%s document_number=%s", output.document_type, output.document_number)
        return output

    # ── Private helpers ───────────────────────────────────────────────────

    # Synonyms Claude may return → canonical role value
    _ROLE_ALIASES: dict[str, str] = {
        "supplier": "vendor",
        "seller": "vendor",
        "issuer": "vendor",
        "client": "customer",
        "buyer": "customer",
        "payer": "customer",
    }

    @classmethod
    def _normalise_role(cls, role: str | None) -> str | None:
        _logger.debug("Transformer._normalise_role: start role=%s", role)
        if role is None:
            _logger.debug("Transformer._normalise_role: complete result=None")
            return None
        lower = role.lower()
        result = cls._ROLE_ALIASES.get(lower, lower)
        _logger.debug("Transformer._normalise_role: complete role=%s result=%s", role, result)
        return result

    @classmethod
    def _dict_to_output(cls, data: dict[str, Any]) -> DocumentOutput:
        """Map a raw dict (from Claude JSON) to a :class:`DocumentOutput`."""
        _logger.debug("Transformer._dict_to_output: start keys=%s", list(data.keys()))
        parties = [
            Party(
                name=p.get("name"),
                role=cls._normalise_role(p.get("role")),
                address=Address(**p["address"]) if p.get("address") else None,
                email=p.get("email"),
                phone=p.get("phone"),
                tax_id=p.get("tax_id"),
            )
            for p in data.get("parties", [])
        ]
        line_items = [
            LineItem(
                description=li.get("description"),
                quantity=li.get("quantity"),
                unit=li.get("unit"),
                unit_price=li.get("unit_price"),
                total=li.get("total"),
            )
            for li in data.get("line_items", [])
        ]
        doc_type = data.get("document_type")
        _logger.debug("Transformer._dict_to_output: complete document_type=%s parties=%d line_items=%d", doc_type, len(parties), len(line_items))
        return DocumentOutput(
            document_type=doc_type.lower() if doc_type else None,
            document_number=data.get("document_number"),
            document_date=data.get("document_date"),
            due_date=data.get("due_date"),
            parties=parties,
            currency=data.get("currency"),
            subtotal=data.get("subtotal"),
            tax_amount=data.get("tax_amount"),
            tax_rate=data.get("tax_rate"),
            discount=data.get("discount"),
            total_amount=data.get("total_amount"),
            line_items=line_items,
            notes=data.get("notes"),
            payment_terms=data.get("payment_terms"),
            reference_numbers=data.get("reference_numbers", []),
        )


def save_output(output: DocumentOutput, output_path: str | Path) -> None:
    """Serialise *output* to JSON and write to *output_path*.

    Args:
        output: The document output dataclass instance.
        output_path: Destination file path (will be created or overwritten).
    """
    _logger.debug("save_output: start output_path=%s", output_path)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(dataclasses.asdict(output), fh, indent=2, ensure_ascii=False)
    _logger.debug("save_output: complete output_path=%s", output_path)
