"""
Unit tests for X12 schema module.

Tests schema loading, segment definitions, and loop structures.
TDD: These tests define the expected interface before implementation.
"""
from __future__ import annotations

import pytest
from decimal import Decimal


@pytest.mark.unit
class TestSchemaLoader:
    """Tests for schema loading functionality."""

    def test_load_schema_by_version(self):
        """Must load schema by X12 version identifier."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X222A1")
        
        assert schema is not None
        assert schema.version == "005010X222A1"
        assert schema.transaction_set_id == "837"

    def test_load_schema_returns_none_for_unknown(self):
        """Must return None for unknown schema version."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("UNKNOWN_VERSION")
        
        assert schema is None

    def test_list_available_schemas(self):
        """Must list all available schema versions."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        versions = loader.list_versions()
        
        assert isinstance(versions, list)
        assert "005010X222A1" in versions  # 837P
        assert "005010X221A1" in versions  # 835

    def test_load_schema_by_transaction_type(self):
        """Must load schema by transaction type code."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load_by_transaction("837", "005010")
        
        assert schema is not None
        assert schema.transaction_set_id == "837"


@pytest.mark.unit
class TestSegmentDefinition:
    """Tests for segment definition structures."""

    def test_segment_definition_has_id(self):
        """Segment definition must have segment ID."""
        from x12.schema import SegmentDefinition
        
        seg_def = SegmentDefinition(
            segment_id="NM1",
            name="Individual or Organizational Name",
        )
        
        assert seg_def.segment_id == "NM1"
        assert seg_def.name == "Individual or Organizational Name"

    def test_segment_definition_has_elements(self):
        """Segment definition must define elements."""
        from x12.schema import SegmentDefinition, ElementDefinition
        
        seg_def = SegmentDefinition(
            segment_id="NM1",
            name="Individual or Organizational Name",
            elements=[
                ElementDefinition(position=1, name="Entity Identifier Code", required=True, data_type="ID", min_length=2, max_length=3),
                ElementDefinition(position=2, name="Entity Type Qualifier", required=True, data_type="ID", min_length=1, max_length=1),
                ElementDefinition(position=3, name="Name Last or Organization Name", required=False, data_type="AN", min_length=1, max_length=60),
            ],
        )
        
        assert len(seg_def.elements) == 3
        assert seg_def.elements[0].position == 1
        assert seg_def.elements[0].required is True
        assert seg_def.elements[2].required is False

    def test_element_definition_data_types(self):
        """Element definition must support X12 data types."""
        from x12.schema import ElementDefinition
        
        # ID - Identifier
        id_elem = ElementDefinition(position=1, name="Code", data_type="ID", min_length=2, max_length=3)
        assert id_elem.data_type == "ID"
        
        # AN - Alphanumeric
        an_elem = ElementDefinition(position=2, name="Name", data_type="AN", min_length=1, max_length=60)
        assert an_elem.data_type == "AN"
        
        # N0 - Numeric (integer)
        n0_elem = ElementDefinition(position=3, name="Count", data_type="N0", min_length=1, max_length=6)
        assert n0_elem.data_type == "N0"
        
        # N2 - Numeric (2 decimal places)
        n2_elem = ElementDefinition(position=4, name="Amount", data_type="N2", min_length=1, max_length=18)
        assert n2_elem.data_type == "N2"
        
        # DT - Date
        dt_elem = ElementDefinition(position=5, name="Date", data_type="DT", min_length=8, max_length=8)
        assert dt_elem.data_type == "DT"
        
        # TM - Time
        tm_elem = ElementDefinition(position=6, name="Time", data_type="TM", min_length=4, max_length=8)
        assert tm_elem.data_type == "TM"

    def test_element_definition_valid_values(self):
        """Element definition may specify valid values for ID types."""
        from x12.schema import ElementDefinition
        
        elem = ElementDefinition(
            position=1,
            name="Entity Identifier Code",
            data_type="ID",
            min_length=2,
            max_length=3,
            valid_values=["85", "87", "IL", "PR", "QC"],
        )
        
        assert "85" in elem.valid_values
        assert "XX" not in elem.valid_values


@pytest.mark.unit
class TestLoopDefinition:
    """Tests for loop definition structures."""

    def test_loop_definition_has_id(self):
        """Loop definition must have loop ID."""
        from x12.schema import LoopDefinition
        
        loop_def = LoopDefinition(
            loop_id="2000A",
            name="Billing Provider Hierarchical Level",
        )
        
        assert loop_def.loop_id == "2000A"
        assert loop_def.name == "Billing Provider Hierarchical Level"

    def test_loop_definition_has_segments(self):
        """Loop definition must list allowed segments."""
        from x12.schema import LoopDefinition
        
        loop_def = LoopDefinition(
            loop_id="2010AA",
            name="Billing Provider Name",
            segments=["NM1", "N3", "N4", "REF", "PER"],
        )
        
        assert "NM1" in loop_def.segments
        assert "N3" in loop_def.segments

    def test_loop_definition_repeat_bounds(self):
        """Loop definition must specify repeat bounds."""
        from x12.schema import LoopDefinition
        
        loop_def = LoopDefinition(
            loop_id="2300",
            name="Claim Information",
            min_occurs=1,
            max_occurs=100,
        )
        
        assert loop_def.min_occurs == 1
        assert loop_def.max_occurs == 100

    def test_loop_definition_nested_loops(self):
        """Loop definition may contain nested loops."""
        from x12.schema import LoopDefinition
        
        loop_def = LoopDefinition(
            loop_id="2000A",
            name="Billing Provider Hierarchical Level",
            child_loops=["2010AA", "2010AB"],
        )
        
        assert "2010AA" in loop_def.child_loops
        assert "2010AB" in loop_def.child_loops


@pytest.mark.unit
class TestTransactionSchema:
    """Tests for complete transaction schema."""

    def test_schema_has_metadata(self):
        """Transaction schema must have metadata."""
        from x12.schema import TransactionSchema
        
        schema = TransactionSchema(
            version="005010X222A1",
            transaction_set_id="837",
            name="Health Care Claim: Professional",
            functional_group_id="HC",
        )
        
        assert schema.version == "005010X222A1"
        assert schema.transaction_set_id == "837"
        assert schema.name == "Health Care Claim: Professional"
        assert schema.functional_group_id == "HC"

    def test_schema_has_segment_definitions(self):
        """Transaction schema must contain segment definitions."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X222A1")
        
        assert schema is not None
        nm1_def = schema.get_segment_definition("NM1")
        assert nm1_def is not None
        assert nm1_def.segment_id == "NM1"

    def test_schema_has_loop_definitions(self):
        """Transaction schema must contain loop definitions."""
        from x12.schema import SchemaLoader
        
        loader = SchemaLoader()
        schema = loader.load("005010X222A1")
        
        assert schema is not None
        loop_def = schema.get_loop_definition("2000A")
        assert loop_def is not None
        assert loop_def.loop_id == "2000A"

    def test_schema_validate_segment(self):
        """Schema must validate segment against definition."""
        from x12.schema import SchemaLoader
        from x12.models import Segment, Element
        
        loader = SchemaLoader()
        schema = loader.load("005010X222A1")
        
        # Valid NM1 segment
        segment = Segment(
            segment_id="NM1",
            elements=[
                Element(value="85", index=1),  # Billing Provider
                Element(value="2", index=2),   # Non-Person Entity
                Element(value="ACME HOSPITAL", index=3),
            ],
        )
        
        result = schema.validate_segment(segment)
        assert result.is_valid

    def test_schema_validate_segment_missing_required(self):
        """Schema must reject segment missing required elements."""
        from x12.schema import SchemaLoader
        from x12.models import Segment, Element
        
        loader = SchemaLoader()
        schema = loader.load("005010X222A1")
        
        # NM1 missing required NM101 (Entity Identifier Code)
        segment = Segment(
            segment_id="NM1",
            elements=[
                Element(value="", index=1),  # Empty - required!
                Element(value="2", index=2),
            ],
        )
        
        result = schema.validate_segment(segment)
        assert not result.is_valid
        assert len(result.errors) > 0


@pytest.mark.unit
class TestSchemaValidation:
    """Tests for schema-based validation."""

    def test_validate_element_length(self):
        """Must validate element length against schema."""
        from x12.schema import ElementDefinition
        
        elem_def = ElementDefinition(
            position=1,
            name="State Code",
            data_type="ID",
            min_length=2,
            max_length=2,
        )
        
        assert elem_def.validate_value("CA") is True
        assert elem_def.validate_value("C") is False  # Too short
        assert elem_def.validate_value("CAL") is False  # Too long

    def test_validate_element_data_type(self):
        """Must validate element data type."""
        from x12.schema import ElementDefinition
        
        # Numeric field
        num_def = ElementDefinition(
            position=1,
            name="Amount",
            data_type="N2",
            min_length=1,
            max_length=10,
        )
        
        assert num_def.validate_value("12345") is True
        assert num_def.validate_value("ABC") is False  # Not numeric

    def test_validate_element_valid_values(self):
        """Must validate element against valid values list."""
        from x12.schema import ElementDefinition
        
        elem_def = ElementDefinition(
            position=1,
            name="Gender Code",
            data_type="ID",
            min_length=1,
            max_length=1,
            valid_values=["M", "F", "U"],
        )
        
        assert elem_def.validate_value("M") is True
        assert elem_def.validate_value("X") is False  # Not in valid values

    def test_validate_date_format(self):
        """Must validate date format CCYYMMDD."""
        from x12.schema import ElementDefinition
        
        date_def = ElementDefinition(
            position=1,
            name="Service Date",
            data_type="DT",
            min_length=8,
            max_length=8,
        )
        
        assert date_def.validate_value("20231127") is True
        assert date_def.validate_value("2023-11-27") is False  # Wrong format
        assert date_def.validate_value("20231327") is False  # Invalid month
