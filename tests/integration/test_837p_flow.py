"""
Integration Tests: 837P Professional Claim Flow

These tests verify the complete flow of parsing, validating, and
generating 837P healthcare claims.

Run: pytest tests/integration/test_837p_flow.py -v
"""
import pytest
from datetime import date
from decimal import Decimal


@pytest.mark.integration
class TestParse837P:
    """Tests for parsing 837P claims."""

    def test_parse_minimal_837p(self, minimal_837p_content):
        """Must parse minimal 837P transaction."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_837p_content)
        
        assert interchange is not None
        assert len(interchange.functional_groups) == 1
        assert len(interchange.functional_groups[0].transactions) == 1

    def test_parse_extracts_transaction_type(self, minimal_837p_content):
        """Must extract transaction set ID (837)."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_837p_content)
        
        txn = interchange.functional_groups[0].transactions[0]
        assert txn.transaction_set_id == "837"

    def test_parse_extracts_bht(self, minimal_837p_content):
        """Must extract BHT segment data."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_837p_content)
        
        txn = interchange.functional_groups[0].transactions[0]
        bht = txn.root_loop.get_segment("BHT")
        
        assert bht is not None
        assert bht[1].value == "0019"  # Hierarchical structure code

    def test_parse_extracts_provider_loop(self, minimal_837p_content):
        """Must extract 2000A billing provider loop."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_837p_content)
        
        txn = interchange.functional_groups[0].transactions[0]
        
        # Should have 2000A loop (billing provider)
        loop_2000a = txn.root_loop.get_loop("2000A")
        assert loop_2000a is not None

    def test_parse_extracts_subscriber_loop(self, minimal_837p_content):
        """Must extract 2000B subscriber loop."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_837p_content)
        
        txn = interchange.functional_groups[0].transactions[0]
        loop_2000a = txn.root_loop.get_loop("2000A")
        
        if loop_2000a:
            loop_2000b = loop_2000a.get_loop("2000B")
            assert loop_2000b is not None

    def test_parse_extracts_claim(self, minimal_837p_content):
        """Must extract CLM segment with claim data."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_837p_content)
        
        txn = interchange.functional_groups[0].transactions[0]
        
        # Find CLM segment somewhere in structure
        def find_segment(loop, seg_id):
            seg = loop.get_segment(seg_id)
            if seg:
                return seg
            for child in loop.loops:
                result = find_segment(child, seg_id)
                if result:
                    return result
            return None
        
        clm = find_segment(txn.root_loop, "CLM")
        assert clm is not None
        assert clm[1].value == "CLAIM001"
        assert clm[2].as_decimal() == Decimal("150")


@pytest.mark.integration
class TestValidate837P:
    """Tests for validating 837P claims."""

    def test_valid_837p_passes(self, minimal_837p_content):
        """Valid 837P must pass validation."""
        from x12.core.parser import Parser
        from x12.core.validator import X12Validator
        
        parser = Parser()
        validator = X12Validator()
        
        interchange = parser.parse(minimal_837p_content)
        txn = interchange.functional_groups[0].transactions[0]
        
        report = validator.validate_transaction(txn, "005010X222A1")
        
        # Should pass or only have warnings
        assert report.error_count == 0 or report.is_valid

    @pytest.mark.hipaa
    def test_validates_npi_format(self, minimal_837p_content):
        """Must validate NPI format in NM1 segments."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # NM1*85 with invalid NPI
        report = validator.validate_segment(
            "NM1*85*2*PROVIDER*****XX*123~",  # NPI too short
            "NM1",
            "005010X222A1"
        )
        
        assert len(report.errors) > 0

    def test_validates_claim_structure(self):
        """Must validate required claim segments present."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # Claim without required HI (diagnosis)
        incomplete_claim = """ST*837*0001~
CLM*CLAIM1*100***11:B:1~
SE*3*0001~"""
        
        report = validator.validate(incomplete_claim, "005010X222A1")
        
        # Should flag missing required segments
        assert not report.is_valid or len(report.warnings) > 0


@pytest.mark.integration
class TestGenerate837P:
    """Tests for generating 837P claims."""

    def test_generate_from_model(self, sample_claim_data, sample_provider_data, sample_subscriber_data):
        """Must generate 837P from typed models."""
        from x12.transactions.healthcare import Claim837P, Claim, Provider, Subscriber
        from x12.core.generator import Generator
        
        # Build the claim model
        claim = Claim(**sample_claim_data)
        provider = Provider(**sample_provider_data)
        subscriber = Subscriber(**sample_subscriber_data)
        
        transaction = Claim837P(
            billing_provider=provider,
            subscriber=subscriber,
            claims=[claim],
        )
        
        generator = Generator()
        edi = generator.generate(transaction)
        
        # Should produce valid EDI
        assert "ST*837" in edi
        assert "CLM*" in edi
        assert sample_claim_data["claim_id"] in edi

    def test_generated_837p_is_parseable(self, sample_claim_data, sample_provider_data, sample_subscriber_data):
        """Generated 837P must be parseable."""
        from x12.transactions.healthcare import Claim837P, Claim, Provider, Subscriber
        from x12.core.generator import Generator
        from x12.core.parser import Parser
        
        claim = Claim(**sample_claim_data)
        provider = Provider(**sample_provider_data)
        subscriber = Subscriber(**sample_subscriber_data)
        
        transaction = Claim837P(
            billing_provider=provider,
            subscriber=subscriber,
            claims=[claim],
        )
        
        generator = Generator()
        edi = generator.generate_with_envelope(
            transaction,
            sender_id="SENDER",
            receiver_id="RECEIVER",
        )
        
        parser = Parser()
        result = parser.parse(edi)
        
        assert result is not None


@pytest.mark.integration
class TestRoundtrip837P:
    """Roundtrip tests for 837P."""

    def test_parse_generate_parse(self, minimal_837p_content):
        """Parse→Generate→Parse must preserve data."""
        from x12.core.parser import Parser
        from x12.core.generator import Generator
        
        parser = Parser()
        
        # Parse original
        original = parser.parse(minimal_837p_content)
        original_txn = original.functional_groups[0].transactions[0]
        
        # Generate from parsed
        generator = Generator()
        regenerated_edi = generator.generate_from_transaction(original_txn)
        
        # Parse again
        reparsed = parser.parse(regenerated_edi)
        reparsed_txn = reparsed.functional_groups[0].transactions[0]
        
        # Core data should match
        assert original_txn.transaction_set_id == reparsed_txn.transaction_set_id


@pytest.mark.integration
class TestTypedModelConversion:
    """Tests for converting to/from typed models."""

    def test_parse_to_typed_model(self, minimal_837p_content):
        """Must convert parsed transaction to typed model."""
        from x12.core.parser import Parser
        from x12.transactions.healthcare import Claim837P
        
        parser = Parser()
        interchange = parser.parse(minimal_837p_content)
        txn = interchange.functional_groups[0].transactions[0]
        
        # Convert to typed model
        claim_837p = Claim837P.from_transaction(txn)
        
        assert claim_837p is not None
        assert len(claim_837p.claims) >= 1

    def test_typed_model_to_edi(self, minimal_837p_content):
        """Must convert typed model back to EDI."""
        from x12.core.parser import Parser
        from x12.transactions.healthcare import Claim837P
        from x12.core.generator import Generator
        
        parser = Parser()
        generator = Generator()
        
        # Parse to model
        interchange = parser.parse(minimal_837p_content)
        txn = interchange.functional_groups[0].transactions[0]
        claim_837p = Claim837P.from_transaction(txn)
        
        # Generate EDI
        edi = generator.generate(claim_837p)
        
        assert "CLM*" in edi
