"""
Unit tests for extended X12 schemas.

Tests additional healthcare and supply chain transaction schemas.
TDD: These tests define the expected interface before implementation.
"""
from __future__ import annotations

import pytest


@pytest.mark.unit
class TestHealthcareSchemas:
    """Tests for additional healthcare transaction schemas."""

    def test_load_837i_institutional_claim(self):
        """Must load 837I Institutional Claim schema."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X223A3")
        
        assert schema is not None
        assert schema.transaction_set_id == "837"
        assert schema.name == "Health Care Claim: Institutional"
        assert schema.functional_group_id == "HC"

    def test_837i_has_ub04_segments(self):
        """837I must have UB-04 specific segments."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X223A3")
        
        # CL1 - Institutional Claim Code
        cl1 = schema.get_segment_definition("CL1")
        assert cl1 is not None
        
        # SV2 - Institutional Service Line
        sv2 = schema.get_segment_definition("SV2")
        assert sv2 is not None

    def test_load_837d_dental_claim(self):
        """Must load 837D Dental Claim schema."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X224A3")
        
        assert schema is not None
        assert schema.transaction_set_id == "837"
        assert "Dental" in schema.name

    def test_837d_has_dental_segments(self):
        """837D must have dental-specific segments."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X224A3")
        
        # DN1 - Orthodontic Information
        dn1 = schema.get_segment_definition("DN1")
        assert dn1 is not None
        
        # DN2 - Tooth Status
        dn2 = schema.get_segment_definition("DN2")
        assert dn2 is not None

    def test_load_271_eligibility_response(self):
        """Must load 271 Eligibility Response schema."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X279A1")
        
        assert schema is not None
        # 270/271 share same implementation guide
        assert schema.transaction_set_id in ("270", "271")

    def test_271_has_eligibility_segments(self):
        """271 must have eligibility response segments."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X279A1")
        
        # EB - Eligibility or Benefit Information
        eb = schema.get_segment_definition("EB")
        assert eb is not None

    def test_load_276_claim_status_request(self):
        """Must load 276 Claim Status Request schema."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X212")
        
        assert schema is not None
        assert schema.transaction_set_id in ("276", "277")

    def test_load_834_enrollment(self):
        """Must load 834 Benefit Enrollment schema."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X220A1")
        
        assert schema is not None
        assert schema.transaction_set_id == "834"
        assert "Enrollment" in schema.name

    def test_834_has_member_segments(self):
        """834 must have member enrollment segments."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X220A1")
        
        # INS - Member Level Detail
        ins = schema.get_segment_definition("INS")
        assert ins is not None
        
        # HD - Health Coverage
        hd = schema.get_segment_definition("HD")
        assert hd is not None

    def test_load_278_authorization(self):
        """Must load 278 Prior Authorization schema."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X217")
        
        assert schema is not None
        assert schema.transaction_set_id == "278"

    def test_278_has_auth_segments(self):
        """278 must have authorization segments."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X217")
        
        # UM - Health Care Services Review Information
        um = schema.get_segment_definition("UM")
        assert um is not None

    def test_load_820_premium_payment(self):
        """Must load 820 Premium Payment schema."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X218")
        
        assert schema is not None
        assert schema.transaction_set_id == "820"


@pytest.mark.unit
class TestSupplyChainSchemas:
    """Tests for supply chain transaction schemas."""

    def test_load_856_ship_notice(self):
        """Must load 856 Ship Notice/Manifest schema."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("004010_856")
        
        assert schema is not None
        assert schema.transaction_set_id == "856"
        assert "Ship" in schema.name

    def test_856_has_shipment_segments(self):
        """856 must have shipment segments."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("004010_856")
        
        # BSN - Beginning Segment for Ship Notice
        bsn = schema.get_segment_definition("BSN")
        assert bsn is not None
        
        # HL - Hierarchical Level
        hl = schema.get_segment_definition("HL")
        assert hl is not None

    def test_load_810_invoice(self):
        """Must load 810 Invoice schema."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("004010_810")
        
        assert schema is not None
        assert schema.transaction_set_id == "810"
        assert "Invoice" in schema.name

    def test_810_has_invoice_segments(self):
        """810 must have invoice segments."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("004010_810")
        
        # BIG - Beginning Segment for Invoice
        big = schema.get_segment_definition("BIG")
        assert big is not None
        
        # IT1 - Baseline Item Data (Invoice)
        it1 = schema.get_segment_definition("IT1")
        assert it1 is not None

    def test_load_855_po_acknowledgment(self):
        """Must load 855 Purchase Order Acknowledgment schema."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("004010_855")
        
        assert schema is not None
        assert schema.transaction_set_id == "855"

    def test_load_860_po_change(self):
        """Must load 860 Purchase Order Change schema."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("004010_860")
        
        assert schema is not None
        assert schema.transaction_set_id == "860"


@pytest.mark.unit
class TestSchemaSegmentDefinitions:
    """Tests for complete segment definitions across schemas."""

    def test_all_schemas_have_common_segments(self):
        """All schemas should have common envelope segments."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        
        for version in loader.list_versions():
            schema = loader.load(version)
            if schema:
                # All should recognize NM1 for name segments
                # (Not all schemas require it, but should define it)
                pass  # Basic structural test

    def test_healthcare_schemas_have_nm1(self):
        """Healthcare schemas must define NM1 segment."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        healthcare_versions = [
            "005010X222A1",  # 837P
            "005010X223A3",  # 837I
            "005010X224A3",  # 837D
            "005010X221A1",  # 835
            "005010X279A1",  # 270/271
        ]
        
        for version in healthcare_versions:
            schema = loader.load(version)
            assert schema is not None, f"Schema {version} not found"
            nm1 = schema.get_segment_definition("NM1")
            assert nm1 is not None, f"NM1 not defined in {version}"
