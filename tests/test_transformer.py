"""Tests for src/transformer."""

import dataclasses
import json
from unittest.mock import MagicMock, patch

import pytest

from src.transformer.models import DocumentOutput, Party, Address, LineItem
from src.transformer.transformer import Transformer, save_output


SAMPLE_CLAUDE_RESPONSE = json.dumps({
    "document_type": "invoice",
    "document_number": "INV-001",
    "document_date": "2024-01-15",
    "due_date": "2024-02-15",
    "parties": [
        {
            "name": "Acme Corp",
            "role": "vendor",
            "address": {
                "street": "123 Main St",
                "city": "Springfield",
                "state": "IL",
                "postal_code": "62701",
                "country": "US",
            },
            "email": "billing@acme.com",
            "phone": "555-0100",
            "tax_id": "12-3456789",
        }
    ],
    "currency": "USD",
    "subtotal": 1000.0,
    "tax_amount": 100.0,
    "tax_rate": 0.10,
    "discount": None,
    "total_amount": 1100.0,
    "line_items": [
        {
            "description": "Widget A",
            "quantity": 10,
            "unit": "pcs",
            "unit_price": 100.0,
            "total": 1000.0,
        }
    ],
    "notes": "Thank you for your business.",
    "payment_terms": "Net 30",
    "reference_numbers": ["PO-2024-001"],
})


@pytest.fixture()
def transformer():
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("src.transformer.transformer.anthropic.Anthropic"):
            t = Transformer()
    return t


class TestTransformer:
    def test_transform_parses_valid_response(self, transformer):
        mock_content = MagicMock()
        mock_content.text = SAMPLE_CLAUDE_RESPONSE
        transformer._client.messages.create.return_value = MagicMock(content=[mock_content])

        result = transformer.transform("some raw text")

        assert isinstance(result, DocumentOutput)
        assert result.document_type == "invoice"
        assert result.document_number == "INV-001"
        assert result.total_amount == 1100.0
        assert len(result.parties) == 1
        assert result.parties[0].name == "Acme Corp"
        assert result.parties[0].address.city == "Springfield"
        assert len(result.line_items) == 1
        assert result.line_items[0].description == "Widget A"
        assert result.raw_text == "some raw text"

    def test_transform_raises_on_invalid_json(self, transformer):
        mock_content = MagicMock()
        mock_content.text = "not json at all"
        transformer._client.messages.create.return_value = MagicMock(content=[mock_content])

        with pytest.raises(ValueError, match="non-JSON"):
            transformer.transform("raw text")

    def test_missing_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EnvironmentError):
                Transformer()


class TestSaveOutput:
    def test_writes_json_file(self, tmp_path):
        output = DocumentOutput(document_type="invoice", document_number="INV-001", raw_text="raw")
        path = tmp_path / "output" / "inv.json"
        save_output(output, path)

        assert path.exists()
        data = json.loads(path.read_text())
        assert data["document_type"] == "invoice"
        assert data["raw_text"] == "raw"

    def test_creates_parent_directories(self, tmp_path):
        output = DocumentOutput()
        path = tmp_path / "a" / "b" / "c" / "out.json"
        save_output(output, path)
        assert path.exists()
