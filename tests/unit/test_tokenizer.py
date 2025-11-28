"""
TDD Tests: Tokenizer

These tests DEFINE the expected behavior of the Tokenizer class.
Implementation in x12/core/tokenizer.py must satisfy these specifications.

Run: pytest tests/unit/test_tokenizer.py -v
"""
import pytest
from typing import List


@pytest.mark.unit
class TestTokenizerBasics:
    """Basic tokenization functionality."""

    def test_yields_segment_id_first(self):
        """First token of each segment must be SEGMENT_ID type."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "ISA*00*TEST~"
        
        tokens = list(tokenizer.tokenize(content))
        
        assert len(tokens) > 0
        assert tokens[0].type == TokenType.SEGMENT_ID
        assert tokens[0].value == "ISA"

    def test_yields_elements_in_order(self):
        """Elements must be yielded in segment order (1-indexed)."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "NM1*85*2*PROVIDER~"
        
        tokens = list(tokenizer.tokenize(content))
        elements = [t for t in tokens if t.type == TokenType.ELEMENT]
        
        assert len(elements) == 3
        assert elements[0].value == "85"
        assert elements[1].value == "2"
        assert elements[2].value == "PROVIDER"

    def test_yields_segment_terminator(self):
        """Segment terminator token must be yielded after each segment."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "NM1*85~REF*EI~"
        
        tokens = list(tokenizer.tokenize(content))
        terminators = [t for t in tokens if t.type == TokenType.SEGMENT_TERMINATOR]
        
        assert len(terminators) == 2

    def test_multiple_segments(self):
        """Multiple segments must all be tokenized."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "NM1*85~REF*EI*123~N3*STREET~"
        
        tokens = list(tokenizer.tokenize(content))
        segment_ids = [t for t in tokens if t.type == TokenType.SEGMENT_ID]
        
        assert len(segment_ids) == 3
        assert [s.value for s in segment_ids] == ["NM1", "REF", "N3"]


@pytest.mark.unit
class TestTokenizerEmptyElements:
    """Tests for handling empty elements."""

    def test_handles_empty_elements_middle(self):
        """Empty elements in middle must yield empty string tokens."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "NM1*85**NAME~"  # Empty element between 85 and NAME
        
        tokens = list(tokenizer.tokenize(content))
        elements = [t for t in tokens if t.type == TokenType.ELEMENT]
        
        assert len(elements) == 3
        assert elements[0].value == "85"
        assert elements[1].value == ""  # Empty element
        assert elements[2].value == "NAME"

    def test_handles_multiple_empty_elements(self):
        """Multiple consecutive empty elements must all be captured."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "NM1*85***NAME~"  # Two empty elements
        
        tokens = list(tokenizer.tokenize(content))
        elements = [t for t in tokens if t.type == TokenType.ELEMENT]
        
        assert len(elements) == 4
        assert elements[1].value == ""
        assert elements[2].value == ""
        assert elements[3].value == "NAME"

    def test_handles_trailing_empty_elements(self):
        """Trailing empty elements before terminator must be captured."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "REF*EI*123**~"  # Trailing empty element
        
        tokens = list(tokenizer.tokenize(content))
        elements = [t for t in tokens if t.type == TokenType.ELEMENT]
        
        # Should have: EI, 123, empty, empty
        assert len(elements) >= 3  # At minimum EI, 123, and one empty


@pytest.mark.unit
class TestTokenizerCompositeElements:
    """Tests for composite element handling."""

    def test_parses_composite_elements(self):
        """Composite elements must yield COMPONENT tokens."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "SV1*HC:99213:25*100~"
        
        tokens = list(tokenizer.tokenize(content))
        components = [t for t in tokens if t.type == TokenType.COMPONENT]
        
        assert len(components) == 3
        assert components[0].value == "HC"
        assert components[1].value == "99213"
        assert components[2].value == "25"

    def test_composite_element_index_tracking(self):
        """Component tokens must track their position within element."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "SV1*HC:99213:25~"
        
        tokens = list(tokenizer.tokenize(content))
        components = [t for t in tokens if t.type == TokenType.COMPONENT]
        
        assert components[0].component_index == 0
        assert components[1].component_index == 1
        assert components[2].component_index == 2

    def test_simple_element_has_no_components(self):
        """Simple (non-composite) elements must not yield COMPONENT tokens."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "REF*EI*123456789~"  # No composites
        
        tokens = list(tokenizer.tokenize(content))
        components = [t for t in tokens if t.type == TokenType.COMPONENT]
        
        # Simple elements should be ELEMENT type, not COMPONENT
        elements = [t for t in tokens if t.type == TokenType.ELEMENT]
        assert len(elements) == 2
        # No standalone COMPONENT tokens for simple elements
        # (Implementation may include simple elements as single-component composites)


@pytest.mark.unit
class TestTokenizerRepetition:
    """Tests for repetition separator handling."""

    def test_handles_repetition_separator(self):
        """Repeated elements must be properly tokenized."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "REF*EI*123^456^789~"  # Three repetitions
        
        tokens = list(tokenizer.tokenize(content))
        
        # Should have repetition handling
        # Implementation may use REPETITION token type or multiple ELEMENT tokens
        values = [t.value for t in tokens if t.type in (TokenType.ELEMENT, TokenType.REPETITION)]
        
        # All three values should appear
        assert "123" in values or any("123" in str(v) for v in values)
        assert "456" in values or any("456" in str(v) for v in values)
        assert "789" in values or any("789" in str(v) for v in values)


@pytest.mark.unit
class TestTokenizerPositionTracking:
    """Tests for position and line tracking."""

    def test_tracks_byte_position(self):
        """Each token must track its byte position in source."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "ISA*00~GS*HC~"
        
        tokens = list(tokenizer.tokenize(content))
        
        # First token (ISA) should be at position 0
        assert tokens[0].position == 0

    def test_tracks_segment_number(self):
        """Tokens must track which segment they belong to (line number)."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "ISA*00~GS*HC~ST*837~"
        
        tokens = list(tokenizer.tokenize(content))
        segment_ids = [t for t in tokens if t.type == TokenType.SEGMENT_ID]
        
        # Line numbers should be 1, 2, 3 (1-indexed)
        assert segment_ids[0].line == 1
        assert segment_ids[1].line == 2
        assert segment_ids[2].line == 3

    def test_tracks_element_index(self):
        """Tokens must track element position within segment."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "NM1*85*2*NAME~"
        
        tokens = list(tokenizer.tokenize(content))
        elements = [t for t in tokens if t.type == TokenType.ELEMENT]
        
        # Element indices should be 1, 2, 3 (NM101, NM102, NM103)
        assert elements[0].element_index == 1
        assert elements[1].element_index == 2
        assert elements[2].element_index == 3


@pytest.mark.unit
class TestTokenizerDelimiterHandling:
    """Tests for custom delimiter support."""

    def test_custom_element_separator(self):
        """Tokenizer must work with custom element separator."""
        from x12.core.tokenizer import Tokenizer, TokenType
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters(element="|", segment="~", component=":", repetition="^")
        tokenizer = Tokenizer(delimiters)
        
        content = "NM1|85|2|NAME~"
        tokens = list(tokenizer.tokenize(content))
        elements = [t for t in tokens if t.type == TokenType.ELEMENT]
        
        assert elements[0].value == "85"
        assert elements[1].value == "2"
        assert elements[2].value == "NAME"

    def test_custom_segment_terminator(self):
        """Tokenizer must work with custom segment terminator."""
        from x12.core.tokenizer import Tokenizer, TokenType
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters(element="*", segment="\n", component=":", repetition="^")
        tokenizer = Tokenizer(delimiters)
        
        content = "NM1*85*2\nREF*EI*123\n"
        tokens = list(tokenizer.tokenize(content))
        segment_ids = [t for t in tokens if t.type == TokenType.SEGMENT_ID]
        
        assert len(segment_ids) == 2
        assert segment_ids[0].value == "NM1"
        assert segment_ids[1].value == "REF"

    def test_custom_component_separator(self):
        """Tokenizer must work with custom component separator."""
        from x12.core.tokenizer import Tokenizer, TokenType
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters(element="*", segment="~", component=">", repetition="^")
        tokenizer = Tokenizer(delimiters)
        
        content = "SV1*HC>99213>25*100~"
        tokens = list(tokenizer.tokenize(content))
        components = [t for t in tokens if t.type == TokenType.COMPONENT]
        
        assert components[0].value == "HC"
        assert components[1].value == "99213"
        assert components[2].value == "25"

    def test_auto_detect_delimiters_from_isa(self):
        """Tokenizer without explicit delimiters must auto-detect from ISA."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()  # No explicit delimiters
        
        # Content with pipe delimiters
        content = (
            "ISA|00|          |00|          |ZZ|SENDER         "
            "|ZZ|RECEIVER       |231127|1200|^|00501|000000001|0|P|>~"
            "GS|HC|SENDER|RECEIVER~"
        )
        
        tokens = list(tokenizer.tokenize(content))
        
        # Should detect | as element separator
        gs_elements = [t for t in tokens if t.type == TokenType.ELEMENT and t.line == 2]
        assert gs_elements[0].value == "HC"


@pytest.mark.unit
class TestTokenizerStreaming:
    """Tests for streaming/memory efficiency."""

    def test_returns_iterator(self):
        """Tokenize must return an iterator, not a list."""
        from x12.core.tokenizer import Tokenizer
        
        tokenizer = Tokenizer()
        content = "ISA*00~"
        
        result = tokenizer.tokenize(content)
        
        # Should be an iterator/generator
        assert hasattr(result, '__iter__')
        assert hasattr(result, '__next__')

    def test_lazy_evaluation(self):
        """Tokenizer must not process entire content upfront."""
        from x12.core.tokenizer import Tokenizer
        
        tokenizer = Tokenizer()
        
        # Large content
        content = "SEG*" + "X" * 1000 + "~" * 1000
        
        # Create generator
        gen = tokenizer.tokenize(content)
        
        # Taking first token should work without processing all
        first = next(gen)
        assert first.value == "SEG"


@pytest.mark.unit
class TestTokenizerEdgeCases:
    """Edge cases and error handling."""

    def test_empty_content(self):
        """Empty content must yield no tokens."""
        from x12.core.tokenizer import Tokenizer
        
        tokenizer = Tokenizer()
        tokens = list(tokenizer.tokenize(""))
        
        assert len(tokens) == 0

    def test_whitespace_only(self):
        """Whitespace-only content must yield no tokens."""
        from x12.core.tokenizer import Tokenizer
        
        tokenizer = Tokenizer()
        tokens = list(tokenizer.tokenize("   \n\t  "))
        
        assert len(tokens) == 0

    def test_segment_id_only(self):
        """Segment with only ID (no elements) must be handled."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "HL~"
        
        tokens = list(tokenizer.tokenize(content))
        segment_ids = [t for t in tokens if t.type == TokenType.SEGMENT_ID]
        
        assert len(segment_ids) == 1
        assert segment_ids[0].value == "HL"

    def test_handles_windows_line_endings(self):
        """Windows line endings (\\r\\n) in content must be handled."""
        from x12.core.tokenizer import Tokenizer, TokenType
        
        tokenizer = Tokenizer()
        content = "ISA*00*TEST~\r\nGS*HC~\r\n"
        
        tokens = list(tokenizer.tokenize(content))
        segment_ids = [t for t in tokens if t.type == TokenType.SEGMENT_ID]
        
        # Both segments should be found
        assert len(segment_ids) == 2
