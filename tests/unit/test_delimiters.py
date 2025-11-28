"""
TDD Tests: Delimiter Detection

These tests DEFINE the expected behavior of the Delimiters class.
Implementation in x12/core/delimiters.py must satisfy these specifications.

Run: pytest tests/unit/test_delimiters.py -v
"""
import pytest


@pytest.mark.unit
class TestDelimiterConstruction:
    """Tests for Delimiters class construction."""

    def test_default_delimiters(self):
        """Default delimiters must be standard X12 values."""
        from x12.core.delimiters import Delimiters
        
        d = Delimiters()
        
        assert d.element == "*"
        assert d.segment == "~"
        assert d.component == ":"
        assert d.repetition == "^"

    def test_custom_delimiters(self):
        """Custom delimiters must be accepted."""
        from x12.core.delimiters import Delimiters
        
        d = Delimiters(
            element="|",
            segment="\n",
            component=">",
            repetition="!",
        )
        
        assert d.element == "|"
        assert d.segment == "\n"
        assert d.component == ">"
        assert d.repetition == "!"

    def test_delimiters_immutable(self):
        """Delimiters should be immutable after creation."""
        from x12.core.delimiters import Delimiters
        
        d = Delimiters()
        
        with pytest.raises((AttributeError, TypeError)):
            d.element = "|"


@pytest.mark.unit
class TestDelimiterDetectionFromISA:
    """Tests for extracting delimiters from ISA segment."""

    def test_standard_delimiters_detected(self, minimal_isa_segment):
        """Standard delimiters (* ~ : ^) must be detected from ISA."""
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters.from_isa(minimal_isa_segment)
        
        assert delimiters.element == "*"
        assert delimiters.segment == "~"
        assert delimiters.component == ":"
        assert delimiters.repetition == "^"

    def test_pipe_delimiters_detected(self, isa_with_pipe_delimiters):
        """Pipe-based delimiters must be detected from ISA."""
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters.from_isa(isa_with_pipe_delimiters)
        
        assert delimiters.element == "|"
        assert delimiters.component == ">"
        # Segment terminator is still ~
        assert delimiters.segment == "~"

    def test_newline_segment_terminator_detected(self, isa_with_newline_terminator):
        """Newline as segment terminator must be detected."""
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters.from_isa(isa_with_newline_terminator)
        
        assert delimiters.segment == "\n"

    def test_element_separator_at_position_3(self):
        """Element separator must be extracted from ISA position 3."""
        from x12.core.delimiters import Delimiters
        
        # ISA with | as element separator
        isa = "ISA|00|" + " " * 94 + "|:"  # Minimal to show position
        # Actually need proper ISA structure
        isa = (
            "ISA|00|          |00|          |ZZ|SENDER         "
            "|ZZ|RECEIVER       |231127|1200|^|00501|000000001|0|P|>~"
        )
        
        delimiters = Delimiters.from_isa(isa)
        
        assert delimiters.element == "|"

    def test_component_separator_at_position_104(self):
        """Component separator must be at ISA position 104."""
        from x12.core.delimiters import Delimiters
        
        # Standard ISA with > as component separator
        isa = (
            "ISA*00*          *00*          *ZZ*SENDER         "
            "*ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*>~"
        )
        
        delimiters = Delimiters.from_isa(isa)
        
        assert delimiters.component == ">"

    def test_segment_terminator_at_position_105(self):
        """Segment terminator must be at ISA position 105."""
        from x12.core.delimiters import Delimiters
        
        # ISA with | as segment terminator
        isa = (
            "ISA*00*          *00*          *ZZ*SENDER         "
            "*ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:|"
        )
        
        delimiters = Delimiters.from_isa(isa)
        
        assert delimiters.segment == "|"


@pytest.mark.unit
class TestDelimiterDetectionErrors:
    """Tests for error handling in delimiter detection."""

    def test_isa_too_short_raises_value_error(self):
        """ISA shorter than 106 characters must raise ValueError."""
        from x12.core.delimiters import Delimiters
        
        short_isa = "ISA*00*          *00*"
        
        with pytest.raises(ValueError, match="too short|Invalid ISA"):
            Delimiters.from_isa(short_isa)

    def test_empty_string_raises_value_error(self):
        """Empty string must raise ValueError."""
        from x12.core.delimiters import Delimiters
        
        with pytest.raises(ValueError):
            Delimiters.from_isa("")

    def test_no_isa_prefix_raises_value_error(self):
        """String not starting with ISA must raise ValueError."""
        from x12.core.delimiters import Delimiters
        
        with pytest.raises(ValueError, match="ISA"):
            Delimiters.from_isa("GS*HC*SENDER*RECEIVER~")

    def test_handles_isa_in_middle_of_content(self):
        """ISA not at start should still be found."""
        from x12.core.delimiters import Delimiters
        
        content = "GARBAGE" + (
            "ISA*00*          *00*          *ZZ*SENDER         "
            "*ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~"
        )
        
        # Should either raise or find the ISA
        # Implementation decision: we require ISA at start or find it
        try:
            delimiters = Delimiters.from_isa(content)
            # If it finds ISA in middle, delimiters should be correct
            assert delimiters.element == "*"
        except ValueError:
            # Also acceptable to require ISA at start
            pass


@pytest.mark.unit
class TestDelimiterValidation:
    """Tests for delimiter validation rules."""

    def test_all_delimiters_must_be_distinct(self):
        """All four delimiters must be different characters."""
        from x12.core.delimiters import Delimiters
        
        # Same character for element and component should fail
        with pytest.raises((ValueError, AssertionError)):
            Delimiters(
                element="*",
                segment="~",
                component="*",  # Same as element!
                repetition="^",
            )

    def test_delimiter_must_be_single_character(self):
        """Each delimiter must be exactly one character."""
        from x12.core.delimiters import Delimiters
        
        with pytest.raises((ValueError, TypeError)):
            Delimiters(
                element="**",  # Two characters
                segment="~",
                component=":",
                repetition="^",
            )

    def test_delimiter_cannot_be_alphanumeric(self):
        """Delimiters should not be alphanumeric characters."""
        from x12.core.delimiters import Delimiters
        
        # Using 'A' as delimiter should fail (would conflict with data)
        with pytest.raises(ValueError):
            Delimiters(
                element="A",  # Alphanumeric!
                segment="~",
                component=":",
                repetition="^",
            )


@pytest.mark.unit
class TestDelimiterEquality:
    """Tests for delimiter comparison."""

    def test_equal_delimiters(self):
        """Delimiters with same values should be equal."""
        from x12.core.delimiters import Delimiters
        
        d1 = Delimiters(element="*", segment="~", component=":", repetition="^")
        d2 = Delimiters(element="*", segment="~", component=":", repetition="^")
        
        assert d1 == d2

    def test_unequal_delimiters(self):
        """Delimiters with different values should not be equal."""
        from x12.core.delimiters import Delimiters
        
        d1 = Delimiters(element="*", segment="~", component=":", repetition="^")
        d2 = Delimiters(element="|", segment="~", component=":", repetition="^")
        
        assert d1 != d2

    def test_hashable_for_dict_keys(self):
        """Delimiters should be hashable for use as dict keys."""
        from x12.core.delimiters import Delimiters
        
        d = Delimiters()
        
        # Should not raise
        hash(d)
        
        # Should work as dict key
        cache = {d: "cached_value"}
        assert cache[d] == "cached_value"


@pytest.mark.unit
class TestDelimiterSpecialCases:
    """Tests for special delimiter characters."""

    @pytest.mark.parametrize("segment_term", ["~", "\n", "\r\n", "|"])
    def test_various_segment_terminators(self, segment_term):
        """Various segment terminators must be supported."""
        from x12.core.delimiters import Delimiters
        
        d = Delimiters(
            element="*",
            segment=segment_term,
            component=":",
            repetition="^",
        )
        
        assert d.segment == segment_term

    @pytest.mark.parametrize("elem_sep", ["*", "|", "!", "+", "~"])
    def test_various_element_separators(self, elem_sep):
        """Various element separators must be supported."""
        from x12.core.delimiters import Delimiters
        
        # Ensure segment is different from element
        seg = "\n" if elem_sep == "~" else "~"
        
        d = Delimiters(
            element=elem_sep,
            segment=seg,
            component=":",
            repetition="^",
        )
        
        assert d.element == elem_sep

    def test_tab_as_delimiter(self):
        """Tab character must be supported as delimiter."""
        from x12.core.delimiters import Delimiters
        
        d = Delimiters(
            element="\t",
            segment="~",
            component=":",
            repetition="^",
        )
        
        assert d.element == "\t"
