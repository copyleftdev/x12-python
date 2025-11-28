"""
TDD Tests: Segment Parser

These tests DEFINE the expected behavior of the SegmentParser class.
Implementation in x12/core/parser.py must satisfy these specifications.

Run: pytest tests/unit/test_segment_parser.py -v
"""
import pytest
from decimal import Decimal
from datetime import date


@pytest.mark.unit
class TestSegmentParserBasics:
    """Basic segment parsing functionality."""

    def test_creates_segment_with_id(self):
        """Parsed segment must have correct segment_id."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segments = list(parser.parse("NM1*85*2*PROVIDER~"))
        
        assert len(segments) == 1
        assert segments[0].segment_id == "NM1"

    def test_parses_multiple_segments(self):
        """Multiple segments must all be parsed."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        content = "NM1*85~REF*EI*123~N3*STREET~"
        
        segments = list(parser.parse(content))
        
        assert len(segments) == 3
        assert segments[0].segment_id == "NM1"
        assert segments[1].segment_id == "REF"
        assert segments[2].segment_id == "N3"

    def test_segment_has_elements(self):
        """Parsed segment must have elements list."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segments = list(parser.parse("NM1*85*2*PROVIDER~"))
        segment = segments[0]
        
        assert hasattr(segment, 'elements')
        assert len(segment.elements) == 3


@pytest.mark.unit
class TestElementAccess:
    """Tests for accessing elements within segments."""

    def test_element_access_by_index(self):
        """Elements must be accessible by 1-based index."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("NM1*85*2*PROVIDER*FIRST~"))[0]
        
        # X12 uses 1-based indexing
        assert segment[1].value == "85"
        assert segment[2].value == "2"
        assert segment[3].value == "PROVIDER"
        assert segment[4].value == "FIRST"

    def test_bracket_notation_access(self):
        """Elements must be accessible via bracket notation."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("REF*EI*123456789~"))[0]
        
        assert segment[1].value == "EI"
        assert segment[2].value == "123456789"

    def test_element_method_access(self):
        """Elements must be accessible via element() method."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("REF*EI*123~"))[0]
        
        elem = segment.element(1)
        assert elem is not None
        assert elem.value == "EI"

    def test_missing_element_returns_none(self):
        """Accessing element beyond count must return None."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("REF*EI*123~"))[0]
        
        assert segment[3] is None
        assert segment[99] is None
        assert segment.element(100) is None

    def test_empty_element_has_empty_value(self):
        """Empty elements must have empty string value."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("NM1*85**NAME~"))[0]
        
        assert segment[1].value == "85"
        assert segment[2].value == ""
        assert segment[3].value == "NAME"


@pytest.mark.unit
class TestElementTypeConversion:
    """Tests for element type conversion methods."""

    def test_as_str(self):
        """Element.as_str() must return string value."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("REF*EI*123ABC~"))[0]
        
        assert segment[2].as_str() == "123ABC"
        assert isinstance(segment[2].as_str(), str)

    def test_as_int(self):
        """Element.as_int() must convert numeric strings."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("SE*25*0001~"))[0]
        
        assert segment[1].as_int() == 25
        assert isinstance(segment[1].as_int(), int)

    def test_as_decimal(self):
        """Element.as_decimal() must return Decimal."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("CLM*CLAIM1*150.00~"))[0]
        
        assert segment[2].as_decimal() == Decimal("150.00")
        assert isinstance(segment[2].as_decimal(), Decimal)

    def test_as_date_ccyymmdd(self):
        """Element.as_date() must parse CCYYMMDD format."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("DTP*472*D8*20231115~"))[0]
        
        assert segment[3].as_date() == date(2023, 11, 15)

    def test_as_date_yymmdd(self):
        """Element.as_date() must parse YYMMDD format (6-digit)."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        # ISA dates are YYMMDD format
        segment = list(parser.parse("DMG*D8*800115~"))[0]
        
        # 800115 = Jan 15, 1980 (or 2080 depending on century logic)
        result = segment[2].as_date()
        assert result.month == 1
        assert result.day == 15

    def test_empty_element_conversions(self):
        """Empty element conversions must handle gracefully."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("REF*EI*~"))[0]
        
        # Empty element
        assert segment[2].as_str() == ""
        assert segment[2].as_int() == 0
        assert segment[2].as_decimal() == Decimal(0)
        assert segment[2].as_date() is None


@pytest.mark.unit
class TestCompositeElements:
    """Tests for composite element handling."""

    def test_composite_is_composite_property(self):
        """Composite elements must have is_composite=True."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("SV1*HC:99213:25*100~"))[0]
        
        assert segment[1].is_composite == True
        assert segment[2].is_composite == False

    def test_component_access_by_index(self):
        """Components must be accessible by 0-based index."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("SV1*HC:99213:25~"))[0]
        
        composite = segment[1]
        assert composite.component(0).value == "HC"
        assert composite.component(1).value == "99213"
        assert composite.component(2).value == "25"

    def test_component_count(self):
        """Composite element must expose component count."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("SV1*HC:99213:25:M1~"))[0]
        
        composite = segment[1]
        assert len(composite.components) == 4

    def test_missing_component_returns_none(self):
        """Accessing component beyond count must return None."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("SV1*HC:99213~"))[0]
        
        composite = segment[1]
        assert composite.component(0) is not None
        assert composite.component(1) is not None
        assert composite.component(2) is None
        assert composite.component(99) is None


@pytest.mark.unit
class TestSegmentImmutability:
    """Tests for segment immutability."""

    def test_segment_is_immutable(self):
        """Segments must be immutable after creation."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("NM1*85~"))[0]
        
        with pytest.raises((AttributeError, TypeError)):
            segment.segment_id = "XXX"

    def test_element_is_immutable(self):
        """Elements must be immutable after creation."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segment = list(parser.parse("NM1*85~"))[0]
        
        with pytest.raises((AttributeError, TypeError)):
            segment[1].value = "99"


@pytest.mark.unit
class TestSegmentPosition:
    """Tests for segment position tracking."""

    def test_segment_has_position(self):
        """Segments must track their byte position."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segments = list(parser.parse("ISA*00~GS*HC~"))
        
        assert segments[0].position == 0
        # GS starts after ISA*00~
        assert segments[1].position > 0


@pytest.mark.unit
class TestSegmentSerialization:
    """Tests for segment serialization back to EDI."""

    def test_to_edi_basic(self):
        """Segment.to_edi() must produce valid EDI string."""
        from x12.core.parser import SegmentParser
        from x12.core.delimiters import Delimiters
        
        parser = SegmentParser()
        segment = list(parser.parse("NM1*85*2*NAME~"))[0]
        
        delimiters = Delimiters()
        edi = segment.to_edi(delimiters)
        
        assert edi == "NM1*85*2*NAME~"

    def test_to_edi_with_composite(self):
        """Segment.to_edi() must handle composites correctly."""
        from x12.core.parser import SegmentParser
        from x12.core.delimiters import Delimiters
        
        parser = SegmentParser()
        segment = list(parser.parse("SV1*HC:99213:25*100~"))[0]
        
        delimiters = Delimiters()
        edi = segment.to_edi(delimiters)
        
        assert "HC:99213:25" in edi


@pytest.mark.unit
class TestSegmentParserWithDelimiters:
    """Tests for custom delimiter handling."""

    def test_parse_with_pipe_delimiters(self):
        """Parser must work with pipe delimiters."""
        from x12.core.parser import SegmentParser
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters(element="|", segment="~", component=">", repetition="^")
        parser = SegmentParser(delimiters=delimiters)
        
        segment = list(parser.parse("NM1|85|2|NAME~"))[0]
        
        assert segment.segment_id == "NM1"
        assert segment[1].value == "85"

    def test_parse_with_newline_terminator(self):
        """Parser must work with newline segment terminator."""
        from x12.core.parser import SegmentParser
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters(element="*", segment="\n", component=":", repetition="^")
        parser = SegmentParser(delimiters=delimiters)
        
        segments = list(parser.parse("NM1*85\nREF*EI\n"))
        
        assert len(segments) == 2


@pytest.mark.unit
class TestSegmentParserEdgeCases:
    """Edge cases for segment parsing."""

    def test_segment_with_only_id(self):
        """Segment with only ID (no elements) must parse."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        segments = list(parser.parse("HL~"))
        
        assert len(segments) == 1
        assert segments[0].segment_id == "HL"
        assert len(segments[0].elements) == 0

    def test_very_long_element(self):
        """Very long element values must be preserved."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        long_value = "X" * 1000
        segment = list(parser.parse(f"NTE*ADD*{long_value}~"))[0]
        
        assert segment[2].value == long_value

    def test_special_characters_in_element(self):
        """Special characters in element values must be preserved."""
        from x12.core.parser import SegmentParser
        
        parser = SegmentParser()
        # Note: actual delimiters would conflict, so use allowed special chars
        segment = list(parser.parse("NTE*ADD*Value with spaces & symbols!~"))[0]
        
        assert "spaces" in segment[2].value
        assert "&" in segment[2].value
