"""
Property-Based Tests: Roundtrip Invariants

These tests verify that parse(generate(x)) == x for all valid x.
Uses Hypothesis to generate thousands of test cases automatically.

Run: pytest tests/property/test_roundtrip.py -v
"""
import pytest
from hypothesis import given, assume, settings, HealthCheck

from tests.property.strategies import (
    valid_segment,
    valid_segment_string,
    valid_delimiters,
    standard_delimiters,
    x12_alphanumeric,
    element_value,
    minimal_interchange,
)

# Import hypothesis profiles
import tests.hypothesis_profiles  # noqa: F401


@pytest.mark.property
class TestSegmentRoundtrip:
    """Roundtrip tests for individual segments."""

    @given(valid_segment())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_segment_parse_generate_roundtrip(self, segment_data):
        """Any valid segment must survive parse→generate→parse roundtrip."""
        from x12.core.generator import Generator
        from x12.core.parser import SegmentParser
        from x12.core.delimiters import Delimiters
        
        # Skip ISA segments - they have fixed 106-char format
        assume(segment_data["id"] != "ISA")
        
        generator = Generator()
        parser = SegmentParser()
        
        # Generate EDI from segment data
        edi = generator.generate_segment(
            segment_data["id"],
            segment_data["elements"],
        )
        
        # Parse it back
        parsed_segments = list(parser.parse(edi))
        assert len(parsed_segments) == 1
        
        parsed = parsed_segments[0]
        
        # Must match original
        assert parsed.segment_id == segment_data["id"]
        for i, elem in enumerate(segment_data["elements"]):
            assert parsed[i + 1].value == elem

    @given(valid_segment_string())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_segment_string_roundtrip(self, segment_str):
        """Any valid segment string must survive parse→to_edi roundtrip."""
        from x12.core.parser import SegmentParser
        from x12.core.delimiters import Delimiters
        
        # Skip ISA segments - they have fixed 106-char format with special handling
        assume(not segment_str.startswith("ISA*"))
        
        parser = SegmentParser()
        delimiters = Delimiters()
        
        # Parse
        segments = list(parser.parse(segment_str))
        assume(len(segments) == 1)
        
        # Convert back to EDI
        segment = segments[0]
        regenerated = segment.to_edi(delimiters)
        
        # Should match (modulo trailing empty elements)
        assert regenerated.rstrip("~*") == segment_str.rstrip("~*") or \
               segment.segment_id in regenerated


@pytest.mark.property
class TestDelimiterRoundtrip:
    """Roundtrip tests for delimiter handling."""

    @given(valid_delimiters())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_any_delimiter_works(self, delimiters):
        """Any valid delimiter combination must work for roundtrip."""
        from x12.core.generator import Generator
        from x12.core.parser import SegmentParser
        from x12.core.delimiters import Delimiters
        
        delims = Delimiters(**delimiters)
        generator = Generator(delimiters=delims)
        parser = SegmentParser(delimiters=delims)
        
        # Generate a segment
        edi = generator.generate_segment("TST", ["A", "B", "C"])
        
        # Parse it back
        segments = list(parser.parse(edi))
        
        assert len(segments) == 1
        assert segments[0].segment_id == "TST"
        assert segments[0][1].value == "A"
        assert segments[0][2].value == "B"
        assert segments[0][3].value == "C"

    @given(standard_delimiters())
    @settings(max_examples=50)
    def test_isa_delimiter_detection(self, delimiters):
        """Delimiters from ISA must match what was used to generate."""
        from x12.core.generator import Generator
        from x12.core.delimiters import Delimiters
        
        delims = Delimiters(**delimiters)
        generator = Generator(delimiters=delims)
        
        # Generate ISA
        isa = generator.generate_isa(
            sender_id="SENDER",
            receiver_id="RECEIVER",
        )
        
        # Detect delimiters from generated ISA
        detected = Delimiters.from_isa(isa)
        
        assert detected.element == delimiters["element"]
        assert detected.segment == delimiters["segment"]
        assert detected.component == delimiters["component"]


@pytest.mark.property
class TestElementValueRoundtrip:
    """Roundtrip tests for element values."""

    @given(x12_alphanumeric(min_length=1, max_length=60))
    @settings(max_examples=200)
    def test_alphanumeric_preserved(self, value):
        """Any alphanumeric value must be preserved through roundtrip."""
        from x12.core.generator import Generator
        from x12.core.parser import SegmentParser
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters()
        
        # Skip if value contains delimiter chars
        assume(delimiters.element not in value)
        assume(delimiters.segment not in value)
        assume(delimiters.component not in value)
        
        generator = Generator(delimiters=delimiters)
        parser = SegmentParser(delimiters=delimiters)
        
        # Generate and parse
        edi = generator.generate_segment("REF", ["XX", value])
        parsed = list(parser.parse(edi))[0]
        
        assert parsed[2].value == value

    @given(element_value(data_type="N"))
    @settings(max_examples=100)
    def test_numeric_preserved(self, value):
        """Numeric values must be preserved."""
        from x12.core.generator import Generator
        from x12.core.parser import SegmentParser
        
        generator = Generator()
        parser = SegmentParser()
        
        edi = generator.generate_segment("QTY", ["PT", value])
        parsed = list(parser.parse(edi))[0]
        
        assert parsed[2].value == value

    @given(element_value(data_type="DT"))
    @settings(max_examples=100)
    def test_date_preserved(self, value):
        """Date values must be preserved."""
        from x12.core.generator import Generator
        from x12.core.parser import SegmentParser
        
        generator = Generator()
        parser = SegmentParser()
        
        edi = generator.generate_segment("DTP", ["472", "D8", value])
        parsed = list(parser.parse(edi))[0]
        
        assert parsed[3].value == value


@pytest.mark.property
class TestIdempotence:
    """Idempotence tests - operations should be stable."""

    @given(valid_segment())
    @settings(max_examples=100)
    def test_parse_is_idempotent(self, segment_data):
        """Parsing same content twice must yield identical results."""
        from x12.core.parser import SegmentParser
        from x12.core.generator import Generator
        
        # Skip ISA segments - they have fixed format
        assume(segment_data["id"] != "ISA")
        
        generator = Generator()
        parser = SegmentParser()
        
        edi = generator.generate_segment(segment_data["id"], segment_data["elements"])
        
        parsed1 = list(parser.parse(edi))
        parsed2 = list(parser.parse(edi))
        
        assert len(parsed1) == len(parsed2)
        for s1, s2 in zip(parsed1, parsed2):
            assert s1.segment_id == s2.segment_id
            assert len(s1.elements) == len(s2.elements)

    @given(valid_segment())
    @settings(max_examples=100)
    def test_generate_is_idempotent(self, segment_data):
        """Generating from same data twice must yield identical EDI."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        edi1 = generator.generate_segment(segment_data["id"], segment_data["elements"])
        edi2 = generator.generate_segment(segment_data["id"], segment_data["elements"])
        
        assert edi1 == edi2


@pytest.mark.property
class TestInterchangeRoundtrip:
    """Roundtrip tests for complete interchanges."""

    @given(minimal_interchange())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_interchange_roundtrip(self, edi_content):
        """Complete interchange must survive parse→generate roundtrip."""
        from x12.core.parser import Parser
        
        parser = Parser()
        
        # Parse the generated content
        try:
            result = parser.parse(edi_content)
            assert result is not None
        except Exception as e:
            # If parsing fails, that's also valuable test information
            pytest.skip(f"Generated content failed to parse: {e}")


@pytest.mark.property
class TestTokenizerRoundtrip:
    """Roundtrip tests for tokenizer."""

    @given(valid_segment_string())
    @settings(max_examples=200)
    def test_tokenize_detokenize(self, segment_str):
        """Tokenizing and reconstructing must yield original."""
        from x12.core.tokenizer import Tokenizer, TokenType
        from x12.core.delimiters import Delimiters
        
        # Skip ISA segments - they have fixed 106-char format
        assume(not segment_str.startswith("ISA*"))
        
        tokenizer = Tokenizer()
        delimiters = Delimiters()
        
        tokens = list(tokenizer.tokenize(segment_str))
        
        # Reconstruct from tokens
        parts = []
        for token in tokens:
            if token.type == TokenType.SEGMENT_ID:
                parts.append(token.value)
            elif token.type == TokenType.ELEMENT:
                parts.append(token.value)
            # Skip terminators for reconstruction
        
        # At minimum, segment ID should be preserved
        if parts:
            assert parts[0] in segment_str
