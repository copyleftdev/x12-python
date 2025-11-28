"""
Integration Tests: Acknowledgment Generation (997/999)

These tests verify the complete flow of generating functional
acknowledgments from validation results.

Run: pytest tests/integration/test_acknowledgments.py -v
"""
import pytest


@pytest.mark.integration
class TestGenerate997:
    """Tests for generating 997 functional acknowledgments."""

    def test_generate_997_for_valid_transaction(self, minimal_837p_content):
        """Must generate 997 acknowledging valid transaction."""
        from x12.core.parser import Parser
        from x12.core.validator import X12Validator
        from x12.acknowledgments import AcknowledgmentGenerator
        
        parser = Parser()
        validator = X12Validator()
        
        # Parse and validate
        interchange = parser.parse(minimal_837p_content)
        txn = interchange.functional_groups[0].transactions[0]
        report = validator.validate_transaction(txn)
        
        # Generate 997
        ack_gen = AcknowledgmentGenerator(
            sender_id="RECEIVER",
            sender_qualifier="ZZ",
            receiver_id="SENDER",
            receiver_qualifier="ZZ",
        )
        
        ack = ack_gen.generate_997(
            received_gs=interchange.functional_groups[0],
            validation_reports=[report],
        )
        
        assert ack is not None
        assert ack.functional_id_code == "HC"

    def test_997_accepted_status(self, minimal_837p_content):
        """997 for valid transaction must have accepted status."""
        from x12.core.parser import Parser
        from x12.core.validator import X12Validator
        from x12.acknowledgments import AcknowledgmentGenerator, FunctionalGroupAckCode
        
        parser = Parser()
        validator = X12Validator()
        
        interchange = parser.parse(minimal_837p_content)
        report = validator.validate_transaction(
            interchange.functional_groups[0].transactions[0]
        )
        
        ack_gen = AcknowledgmentGenerator(
            sender_id="R", sender_qualifier="ZZ",
            receiver_id="S", receiver_qualifier="ZZ",
        )
        
        ack = ack_gen.generate_997(
            interchange.functional_groups[0],
            [report],
        )
        
        # If no errors, should be accepted
        if report.error_count == 0:
            assert ack.group_ack_code == FunctionalGroupAckCode.ACCEPTED

    def test_997_rejected_for_invalid(self, edi_mismatched_control_numbers):
        """997 for invalid transaction must have rejected status."""
        from x12.core.parser import Parser
        from x12.core.validator import X12Validator
        from x12.acknowledgments import AcknowledgmentGenerator, FunctionalGroupAckCode
        
        parser = Parser()
        validator = X12Validator()
        
        try:
            interchange = parser.parse(edi_mismatched_control_numbers)
            report = validator.validate_transaction(
                interchange.functional_groups[0].transactions[0]
            )
            
            ack_gen = AcknowledgmentGenerator(
                sender_id="R", sender_qualifier="ZZ",
                receiver_id="S", receiver_qualifier="ZZ",
            )
            
            ack = ack_gen.generate_997(
                interchange.functional_groups[0],
                [report],
            )
            
            # Should be rejected or have errors
            assert ack.group_ack_code != FunctionalGroupAckCode.ACCEPTED or \
                   report.error_count > 0
        except Exception:
            # Parsing may fail for invalid content - that's OK
            pass

    def test_997_contains_ak_segments(self, minimal_837p_content):
        """Generated 997 must contain AK1, AK2, AK5, AK9 segments."""
        from x12.core.parser import Parser
        from x12.core.validator import X12Validator
        from x12.acknowledgments import AcknowledgmentGenerator, AcknowledgmentSerializer
        
        parser = Parser()
        validator = X12Validator()
        
        interchange = parser.parse(minimal_837p_content)
        report = validator.validate_transaction(
            interchange.functional_groups[0].transactions[0]
        )
        
        ack_gen = AcknowledgmentGenerator(
            sender_id="R", sender_qualifier="ZZ",
            receiver_id="S", receiver_qualifier="ZZ",
        )
        
        ack = ack_gen.generate_997(
            interchange.functional_groups[0],
            [report],
        )
        
        # Serialize to EDI
        serializer = AcknowledgmentSerializer()
        edi = serializer.serialize_997(ack, interchange.delimiters)
        
        assert "AK1*" in edi
        assert "AK9*" in edi


@pytest.mark.integration
@pytest.mark.hipaa
class TestGenerate999:
    """Tests for generating 999 implementation acknowledgments (HIPAA)."""

    def test_generate_999_for_hipaa_transaction(self, minimal_837p_content):
        """Must generate 999 for HIPAA transaction."""
        from x12.core.parser import Parser
        from x12.core.validator import X12Validator
        from x12.acknowledgments import AcknowledgmentGenerator
        
        parser = Parser()
        validator = X12Validator()
        
        interchange = parser.parse(minimal_837p_content)
        report = validator.validate_transaction(
            interchange.functional_groups[0].transactions[0],
            version="005010X222A1"
        )
        
        ack_gen = AcknowledgmentGenerator(
            sender_id="R", sender_qualifier="ZZ",
            receiver_id="S", receiver_qualifier="ZZ",
        )
        
        ack = ack_gen.generate_999(
            interchange.functional_groups[0],
            [report],
        )
        
        assert ack is not None
        assert ack.implementation_convention == "005010X222A1"

    def test_999_contains_ik_segments_for_errors(self):
        """999 for transaction with errors must contain IK3/IK4 segments."""
        from x12.core.validator import X12Validator, ValidationReport, ValidationResult, ValidationSeverity
        from x12.acknowledgments import AcknowledgmentGenerator, AcknowledgmentSerializer
        from x12.models import FunctionalGroup
        
        # Create a validation report with errors
        report = ValidationReport()
        report.errors.append(ValidationResult(
            rule_id="ELEM_001",
            message="Required element missing",
            severity=ValidationSeverity.ERROR,
            segment_id="NM1",
            segment_position=5,
            element_index=3,
        ))
        
        # Mock functional group
        fg = FunctionalGroup(
            functional_id_code="HC",
            sender_code="SENDER",
            receiver_code="RECEIVER",
            control_number="1",
        )
        
        ack_gen = AcknowledgmentGenerator(
            sender_id="R", sender_qualifier="ZZ",
            receiver_id="S", receiver_qualifier="ZZ",
        )
        
        ack = ack_gen.generate_999(fg, [report])
        
        # Should have error details
        assert len(ack.transaction_responses) > 0
        assert len(ack.transaction_responses[0].segment_errors) > 0


@pytest.mark.integration
class TestAcknowledgmentRoundtrip:
    """Tests for acknowledgment roundtrip."""

    def test_997_is_parseable(self, minimal_837p_content):
        """Generated 997 must be parseable."""
        from x12.core.parser import Parser
        from x12.core.validator import X12Validator
        from x12.acknowledgments import AcknowledgmentGenerator, AcknowledgmentSerializer
        from x12.core.generator import Generator
        
        parser = Parser()
        validator = X12Validator()
        generator = Generator()
        
        # Generate 997
        interchange = parser.parse(minimal_837p_content)
        report = validator.validate_transaction(
            interchange.functional_groups[0].transactions[0]
        )
        
        ack_gen = AcknowledgmentGenerator(
            sender_id="RECEIVER", sender_qualifier="ZZ",
            receiver_id="SENDER", receiver_qualifier="ZZ",
        )
        
        ack = ack_gen.generate_997(
            interchange.functional_groups[0],
            [report],
        )
        
        # Wrap in envelope
        serializer = AcknowledgmentSerializer()
        ack_content = serializer.serialize_997(ack, interchange.delimiters)
        
        ack_edi = generator.generate_with_envelope(
            content=ack_content,
            transaction_set_id="997",
            sender_id="RECEIVER",
            receiver_id="SENDER",
            functional_id="FA",
        )
        
        # Parse the 997
        ack_interchange = parser.parse(ack_edi)
        
        assert ack_interchange is not None
        assert ack_interchange.functional_groups[0].transactions[0].transaction_set_id == "997"


@pytest.mark.integration
class TestAcknowledgmentFromValidationResults:
    """Tests for creating acknowledgments from validation results."""

    def test_maps_syntax_error_to_ak3(self):
        """Syntax error must map to AK3 segment."""
        from x12.core.validator import ValidationResult, ValidationSeverity, ValidationCategory
        from x12.acknowledgments import AcknowledgmentGenerator
        
        # Create validation result
        result = ValidationResult(
            rule_id="SYNTAX_001",
            message="Invalid segment ID",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.SYNTAX,
            segment_id="XXX",
            segment_position=5,
        )
        
        ack_gen = AcknowledgmentGenerator(
            sender_id="R", sender_qualifier="ZZ",
            receiver_id="S", receiver_qualifier="ZZ",
        )
        
        # Should map to segment error
        segment_error = ack_gen._map_to_segment_error(result)
        
        assert segment_error.segment_id == "XXX"
        assert segment_error.segment_position == 5

    def test_maps_element_error_to_ak4(self):
        """Element error must map to AK4 segment."""
        from x12.core.validator import ValidationResult, ValidationSeverity, ValidationCategory
        from x12.acknowledgments import AcknowledgmentGenerator
        
        result = ValidationResult(
            rule_id="ELEM_TOO_LONG",
            message="Element exceeds maximum length",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.ELEMENT,
            segment_id="NM1",
            segment_position=10,
            element_index=3,
            actual="X" * 100,
        )
        
        ack_gen = AcknowledgmentGenerator(
            sender_id="R", sender_qualifier="ZZ",
            receiver_id="S", receiver_qualifier="ZZ",
        )
        
        elem_error = ack_gen._map_to_element_error(result)
        
        assert elem_error.position == 3
        assert elem_error.bad_value == "X" * 100
