"""
Integration Tests: 850 Purchase Order Flow

These tests verify the complete flow of parsing, validating, and
generating 850 purchase order transactions.

Run: pytest tests/integration/test_850_flow.py -v
"""
import pytest
from decimal import Decimal


@pytest.mark.integration
class TestParse850:
    """Tests for parsing 850 purchase orders."""

    def test_parse_minimal_850(self, minimal_850_content):
        """Must parse minimal 850 transaction."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_850_content)
        
        assert interchange is not None
        assert len(interchange.functional_groups) == 1
        
        fg = interchange.functional_groups[0]
        assert fg.functional_id_code == "PO"
        assert len(fg.transactions) == 1

    def test_parse_extracts_beg(self, minimal_850_content):
        """Must extract BEG segment (beginning segment for PO)."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_850_content)
        
        txn = interchange.functional_groups[0].transactions[0]
        beg = txn.root_loop.get_segment("BEG")
        
        assert beg is not None
        assert beg[1].value == "00"  # Purpose code - Original
        assert beg[2].value == "SA"  # PO type - Stand-alone
        assert beg[3].value == "PO123456"  # PO number

    def test_parse_extracts_n1_ship_to(self, minimal_850_content):
        """Must extract N1 ship-to party."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_850_content)
        
        txn = interchange.functional_groups[0].transactions[0]
        
        # Find N1*ST (ship to)
        def find_n1(loop, entity_code):
            for seg in loop.segments:
                if seg.segment_id == "N1" and seg[1].value == entity_code:
                    return seg
            for child in loop.loops:
                result = find_n1(child, entity_code)
                if result:
                    return result
            return None
        
        n1_st = find_n1(txn.root_loop, "ST")
        assert n1_st is not None
        assert "SHIP TO" in n1_st[2].value.upper()

    def test_parse_extracts_line_items(self, minimal_850_content):
        """Must extract PO1 line items."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_850_content)
        
        txn = interchange.functional_groups[0].transactions[0]
        
        # Find all PO1 segments
        def find_all_segments(loop, seg_id):
            results = []
            for seg in loop.segments:
                if seg.segment_id == seg_id:
                    results.append(seg)
            for child in loop.loops:
                results.extend(find_all_segments(child, seg_id))
            return results
        
        po1_segments = find_all_segments(txn.root_loop, "PO1")
        
        assert len(po1_segments) == 2  # Two line items
        
        # First line item
        assert po1_segments[0][1].value == "1"  # Line number
        assert po1_segments[0][2].as_int() == 10  # Quantity
        assert po1_segments[0][3].value == "EA"  # Unit
        assert po1_segments[0][4].as_decimal() == Decimal("25.00")  # Price

    def test_parse_extracts_ctt(self, minimal_850_content):
        """Must extract CTT summary segment."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_850_content)
        
        txn = interchange.functional_groups[0].transactions[0]
        ctt = txn.root_loop.get_segment("CTT")
        
        assert ctt is not None
        assert ctt[1].as_int() == 2  # Number of line items


@pytest.mark.integration
class TestValidate850:
    """Tests for validating 850 purchase orders."""

    def test_valid_850_passes(self, minimal_850_content):
        """Valid 850 must pass validation."""
        from x12.core.parser import Parser
        from x12.core.validator import X12Validator
        
        parser = Parser()
        validator = X12Validator()
        
        interchange = parser.parse(minimal_850_content)
        txn = interchange.functional_groups[0].transactions[0]
        
        report = validator.validate_transaction(txn, "004010")
        
        assert report.error_count == 0 or report.is_valid

    def test_validates_po_number_present(self):
        """Must validate PO number is present in BEG03."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # BEG without PO number
        report = validator.validate_segment(
            "BEG*00*SA~",  # Missing PO number
            "BEG",
            "004010"
        )
        
        assert len(report.errors) > 0

    def test_validates_line_item_required_fields(self):
        """Must validate required PO1 fields."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # PO1 without quantity
        report = validator.validate_segment(
            "PO1*1~",  # Missing quantity, unit, price
            "PO1",
            "004010"
        )
        
        assert len(report.errors) > 0 or len(report.warnings) > 0


@pytest.mark.integration
class TestGenerate850:
    """Tests for generating 850 purchase orders."""

    def test_generate_from_model(self, sample_purchase_order_data):
        """Must generate 850 from typed model."""
        from x12.transactions.supply_chain import PurchaseOrder850
        from x12.core.generator import Generator
        
        po = PurchaseOrder850(**sample_purchase_order_data)
        
        generator = Generator()
        edi = generator.generate(po)
        
        assert "ST*850" in edi
        assert "BEG*" in edi
        assert sample_purchase_order_data["po_number"] in edi

    def test_generated_850_has_line_items(self, sample_purchase_order_data):
        """Generated 850 must include PO1 line items."""
        from x12.transactions.supply_chain import PurchaseOrder850
        from x12.core.generator import Generator
        
        po = PurchaseOrder850(**sample_purchase_order_data)
        
        generator = Generator()
        edi = generator.generate(po)
        
        # Should have 2 PO1 segments
        assert edi.count("PO1*") == 2

    def test_generated_850_has_ctt(self, sample_purchase_order_data):
        """Generated 850 must include CTT with correct count."""
        from x12.transactions.supply_chain import PurchaseOrder850
        from x12.core.generator import Generator
        
        po = PurchaseOrder850(**sample_purchase_order_data)
        
        generator = Generator()
        edi = generator.generate(po)
        
        # CTT should show 2 line items
        assert "CTT*2" in edi


@pytest.mark.integration
class TestRoundtrip850:
    """Roundtrip tests for 850."""

    def test_parse_to_model_to_edi(self, minimal_850_content):
        """Parse→Model→EDI must preserve data."""
        from x12.core.parser import Parser
        from x12.transactions.supply_chain import PurchaseOrder850
        from x12.core.generator import Generator
        
        parser = Parser()
        generator = Generator()
        
        # Parse to generic transaction
        interchange = parser.parse(minimal_850_content)
        txn = interchange.functional_groups[0].transactions[0]
        
        # Convert to typed model
        po = PurchaseOrder850.from_transaction(txn)
        
        assert po.po_number == "PO123456"
        assert len(po.line_items) == 2
        
        # Generate back to EDI
        edi = generator.generate(po)
        
        assert "PO123456" in edi
        assert edi.count("PO1*") == 2


@pytest.mark.integration  
class TestPurchaseOrderModel:
    """Tests for PurchaseOrder model functionality."""

    def test_model_calculates_total(self, sample_purchase_order_data):
        """PurchaseOrder model must calculate order total."""
        from x12.transactions.supply_chain import PurchaseOrder850
        
        po = PurchaseOrder850(**sample_purchase_order_data)
        
        # 10 * $25.00 + 5 * $50.00 = $500.00
        assert po.calculated_total == Decimal("500.00")

    def test_model_line_item_totals(self, sample_purchase_order_data):
        """Line items must calculate their totals."""
        from x12.transactions.supply_chain import PurchaseOrder850
        
        po = PurchaseOrder850(**sample_purchase_order_data)
        
        assert po.line_items[0].line_total == Decimal("250.00")
        assert po.line_items[1].line_total == Decimal("250.00")
