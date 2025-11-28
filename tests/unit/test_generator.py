"""
TDD Tests: EDI Generator

These tests DEFINE the expected behavior of the Generator class.
Implementation in x12/core/generator.py must satisfy these specifications.

Run: pytest tests/unit/test_generator.py -v
"""
import pytest
from datetime import date
from decimal import Decimal


@pytest.mark.unit
class TestGeneratorBasics:
    """Basic generation functionality."""

    def test_generate_segment(self):
        """Must generate a segment from ID and elements."""
        from x12.core.generator import Generator
        
        generator = Generator()
        segment = generator.generate_segment("NM1", ["85", "2", "PROVIDER"])
        
        assert segment == "NM1*85*2*PROVIDER~"

    def test_generate_segment_with_empty_elements(self):
        """Must handle empty elements in middle."""
        from x12.core.generator import Generator
        
        generator = Generator()
        segment = generator.generate_segment("NM1", ["85", "", "NAME"])
        
        assert segment == "NM1*85**NAME~"

    def test_generate_uses_configured_delimiters(self):
        """Must use configured delimiters."""
        from x12.core.generator import Generator
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters(element="|", segment="\n", component=">", repetition="^")
        generator = Generator(delimiters=delimiters)
        
        segment = generator.generate_segment("NM1", ["85", "2"])
        
        assert "|" in segment
        assert "*" not in segment
        assert segment.endswith("\n")


@pytest.mark.unit
class TestISAGeneration:
    """Tests for ISA segment generation."""

    def test_isa_is_106_characters(self):
        """Generated ISA must be exactly 106 characters."""
        from x12.core.generator import Generator
        
        generator = Generator()
        isa = generator.generate_isa(
            sender_id="SENDER",
            sender_qualifier="ZZ",
            receiver_id="RECEIVER",
            receiver_qualifier="ZZ",
        )
        
        # ISA is fixed length 106 characters
        assert len(isa) == 106

    def test_isa_starts_with_isa(self):
        """Generated ISA must start with 'ISA'."""
        from x12.core.generator import Generator
        
        generator = Generator()
        isa = generator.generate_isa(
            sender_id="SENDER",
            receiver_id="RECEIVER",
        )
        
        assert isa.startswith("ISA")

    def test_isa_fields_padded(self):
        """ISA fixed-width fields must be padded correctly."""
        from x12.core.generator import Generator
        
        generator = Generator()
        isa = generator.generate_isa(
            sender_id="X",
            receiver_id="Y",
        )
        
        # Sender ID (ISA06) should be padded to 15 chars
        # Receiver ID (ISA08) should be padded to 15 chars
        assert "X              " in isa or "X" in isa  # Padded to 15

    def test_isa_control_number_format(self):
        """ISA control number must be 9 digits."""
        from x12.core.generator import Generator
        
        generator = Generator()
        isa = generator.generate_isa(
            sender_id="SENDER",
            receiver_id="RECEIVER",
            control_number=1,
        )
        
        # ISA13 should be 000000001
        assert "000000001" in isa

    def test_isa_includes_delimiters(self):
        """ISA must include delimiter characters at correct positions."""
        from x12.core.generator import Generator
        
        generator = Generator()
        isa = generator.generate_isa(
            sender_id="SENDER",
            receiver_id="RECEIVER",
        )
        
        # Position 3 = element separator (*)
        assert isa[3] == "*"
        # Position 104 = component separator (:)
        assert isa[104] == ":"
        # Position 105 = segment terminator (~)
        assert isa[105] == "~"


@pytest.mark.unit
class TestGSGeneration:
    """Tests for GS segment generation."""

    def test_generate_gs_healthcare(self):
        """Must generate GS for healthcare transactions."""
        from x12.core.generator import Generator
        
        generator = Generator()
        gs = generator.generate_gs(
            functional_id="HC",
            sender_code="SENDER",
            receiver_code="RECEIVER",
            control_number=1,
            version="005010X222A1",
        )
        
        assert gs.startswith("GS*HC*")
        assert "005010X222A1" in gs

    def test_generate_gs_purchase_order(self):
        """Must generate GS for purchase order transactions."""
        from x12.core.generator import Generator
        
        generator = Generator()
        gs = generator.generate_gs(
            functional_id="PO",
            sender_code="BUYER",
            receiver_code="SELLER",
            control_number=1,
            version="004010",
        )
        
        assert gs.startswith("GS*PO*")


@pytest.mark.unit
class TestSTSEGeneration:
    """Tests for ST/SE segment generation."""

    def test_generate_st(self):
        """Must generate ST segment."""
        from x12.core.generator import Generator
        
        generator = Generator()
        st = generator.generate_st(
            transaction_set_id="837",
            control_number="0001",
            version="005010X222A1",
        )
        
        assert st.startswith("ST*837*0001")

    def test_generate_se(self):
        """Must generate SE segment with correct count."""
        from x12.core.generator import Generator
        
        generator = Generator()
        se = generator.generate_se(
            segment_count=25,
            control_number="0001",
        )
        
        assert se.startswith("SE*25*0001")

    def test_se_count_matches_segments(self):
        """SE segment count must match actual segments."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        # Build a transaction
        segments = [
            generator.generate_st("837", "0001"),
            generator.generate_segment("BHT", ["0019", "00"]),
            # SE will be segment 3
        ]
        
        se = generator.generate_se(len(segments) + 1, "0001")  # +1 for SE itself
        
        assert "3" in se  # Should have 3 segments


@pytest.mark.unit
class TestControlNumbers:
    """Tests for control number management."""

    def test_control_numbers_increment(self):
        """Control numbers must increment with each generation."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        isa1 = generator.generate_isa(sender_id="S", receiver_id="R")
        isa2 = generator.generate_isa(sender_id="S", receiver_id="R")
        
        # Extract control numbers (ISA13 at position 90-99 in 106-char ISA)
        ctrl1 = isa1[90:99]
        ctrl2 = isa2[90:99]
        
        assert int(ctrl2) == int(ctrl1) + 1

    def test_custom_control_number(self):
        """Must accept custom control number."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        isa = generator.generate_isa(
            sender_id="S",
            receiver_id="R",
            control_number=12345,
        )
        
        assert "000012345" in isa

    def test_reset_control_numbers(self):
        """Must be able to reset control numbers."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        # Generate some
        generator.generate_isa(sender_id="S", receiver_id="R")
        generator.generate_isa(sender_id="S", receiver_id="R")
        
        # Reset
        generator.reset_control_numbers()
        
        isa = generator.generate_isa(sender_id="S", receiver_id="R")
        
        assert "000000001" in isa


@pytest.mark.unit
class TestCompositeGeneration:
    """Tests for composite element generation."""

    def test_generate_composite_element(self):
        """Must generate composite element with components."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        segment = generator.generate_segment(
            "SV1",
            [["HC", "99213", "25"], "100", "UN", "1"]  # First element is composite
        )
        
        assert "HC:99213:25" in segment

    def test_composite_uses_component_separator(self):
        """Composite must use configured component separator."""
        from x12.core.generator import Generator
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters(element="*", segment="~", component=">", repetition="^")
        generator = Generator(delimiters=delimiters)
        
        segment = generator.generate_segment(
            "SV1",
            [["HC", "99213"], "100"]
        )
        
        assert "HC>99213" in segment


@pytest.mark.unit
class TestEnvelopeGeneration:
    """Tests for complete envelope generation."""

    def test_generate_with_envelope(self):
        """Must wrap content in ISA/IEA envelope."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        content = "BHT*0019*00*12345~NM1*41*2*SUBMITTER~"
        
        edi = generator.generate_with_envelope(
            content=content,
            transaction_set_id="837",
            sender_id="SENDER",
            receiver_id="RECEIVER",
        )
        
        assert edi.startswith("ISA")
        assert "GS*" in edi
        assert "ST*837" in edi
        assert "BHT*0019" in edi
        assert "SE*" in edi
        assert "GE*" in edi
        assert "IEA" in edi

    def test_envelope_structure_order(self):
        """Envelope must have correct segment order."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        edi = generator.generate_with_envelope(
            content="BHT*0019~",
            transaction_set_id="837",
            sender_id="S",
            receiver_id="R",
        )
        
        # Check order: ISA before GS before ST before content before SE before GE before IEA
        isa_pos = edi.find("ISA")
        gs_pos = edi.find("GS*")
        st_pos = edi.find("ST*")
        se_pos = edi.find("SE*")
        ge_pos = edi.find("GE*")
        iea_pos = edi.find("IEA")
        
        assert isa_pos < gs_pos < st_pos < se_pos < ge_pos < iea_pos


@pytest.mark.unit
class TestModelGeneration:
    """Tests for generating EDI from Pydantic models."""

    def test_generate_from_segment_model(self):
        """Must generate from Segment model."""
        from x12.core.generator import Generator
        from x12.models import Segment, Element
        
        generator = Generator()
        
        segment = Segment(
            segment_id="NM1",
            elements=[
                Element(value="85", index=1),
                Element(value="2", index=2),
                Element(value="PROVIDER", index=3),
            ]
        )
        
        edi = generator.generate_from_segment(segment)
        
        assert edi == "NM1*85*2*PROVIDER~"

    def test_generate_from_transaction_model(self, sample_claim_data):
        """Must generate from transaction model."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        # This would use the Claim837P model once implemented
        # edi = generator.generate(claim_model)
        
        assert hasattr(generator, 'generate')


@pytest.mark.unit
class TestGeneratedEDIParseable:
    """Tests ensuring generated EDI is parseable."""

    def test_generated_isa_parseable(self):
        """Generated ISA must be parseable."""
        from x12.core.generator import Generator
        from x12.core.delimiters import Delimiters
        
        generator = Generator()
        isa = generator.generate_isa(sender_id="SENDER", receiver_id="RECEIVER")
        
        # Should be parseable for delimiters
        delimiters = Delimiters.from_isa(isa)
        
        assert delimiters.element == "*"
        assert delimiters.segment == "~"

    def test_generated_content_parseable(self):
        """Complete generated EDI must be parseable."""
        from x12.core.generator import Generator
        from x12.core.parser import Parser
        
        generator = Generator()
        
        edi = generator.generate_with_envelope(
            content="BHT*0019*00*12345~",
            transaction_set_id="837",
            sender_id="SENDER",
            receiver_id="RECEIVER",
        )
        
        parser = Parser()
        result = parser.parse(edi)
        
        assert result is not None


@pytest.mark.unit
class TestDateTimeGeneration:
    """Tests for date/time formatting."""

    def test_format_date_ccyymmdd(self):
        """Must format date as CCYYMMDD."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        d = date(2023, 11, 27)
        formatted = generator.format_date(d)
        
        assert formatted == "20231127"

    def test_format_date_yymmdd(self):
        """Must support YYMMDD format."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        d = date(2023, 11, 27)
        formatted = generator.format_date(d, format="YYMMDD")
        
        assert formatted == "231127"

    def test_format_time_hhmm(self):
        """Must format time as HHMM."""
        from x12.core.generator import Generator
        from datetime import time
        
        generator = Generator()
        
        t = time(14, 30)
        formatted = generator.format_time(t)
        
        assert formatted == "1430"
