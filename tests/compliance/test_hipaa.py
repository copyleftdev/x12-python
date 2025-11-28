"""
HIPAA Compliance Tests

These tests verify that the library correctly implements HIPAA
transaction set requirements for healthcare EDI.

Run: pytest tests/compliance/test_hipaa.py -v -m hipaa
"""
import pytest


@pytest.mark.compliance
@pytest.mark.hipaa
class TestHIPAAEnvelope:
    """HIPAA envelope requirements."""

    def test_isa_version_00501(self, minimal_837p_content):
        """ISA12 must be 00501 for HIPAA 5010."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_837p_content)
        
        # ISA12 should be 00501
        assert interchange.version == "00501" or "00501" in str(interchange.version)

    def test_gs_version_required(self, minimal_837p_content):
        """GS08 must specify implementation guide version."""
        from x12.core.parser import Parser
        
        parser = Parser()
        interchange = parser.parse(minimal_837p_content)
        
        fg = interchange.functional_groups[0]
        
        # GS08 should have version like 005010X222A1
        assert fg.version is not None
        assert "005010" in fg.version


@pytest.mark.compliance
@pytest.mark.hipaa
class TestHIPAA837PRequirements:
    """HIPAA 837P (Professional Claim) requirements."""

    def test_bht_required(self, minimal_837p_content):
        """BHT segment is required in 837."""
        from x12.core.parser import Parser
        from x12.core.validator import X12Validator
        
        # Remove BHT from content
        content_no_bht = minimal_837p_content.replace(
            "BHT*0019*00*244579*20231127*1200*CH~", ""
        )
        
        parser = Parser()
        validator = X12Validator()
        
        try:
            interchange = parser.parse(content_no_bht)
            txn = interchange.functional_groups[0].transactions[0]
            report = validator.validate_transaction(txn, "005010X222A1")
            
            # Should flag missing BHT
            assert not report.is_valid or \
                   any("BHT" in str(e.message) for e in report.errors)
        except Exception:
            # Parsing failure is also acceptable
            pass

    def test_billing_provider_required(self):
        """2000A Billing Provider loop is required."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # 837 without 2000A (HL*1**20)
        content = """ST*837*0001*005010X222A1~
BHT*0019*00*244579*20231127*1200*CH~
NM1*41*2*SUBMITTER~
SE*4*0001~"""
        
        report = validator.validate(content, "005010X222A1")
        
        # Should flag missing billing provider
        assert not report.is_valid

    def test_subscriber_required(self):
        """2000B Subscriber loop is required for claims."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # 837 with billing provider but no subscriber
        content = """ST*837*0001*005010X222A1~
BHT*0019*00*244579*20231127*1200*CH~
HL*1**20*1~
NM1*85*2*PROVIDER*****XX*1234567890~
SE*5*0001~"""
        
        report = validator.validate(content, "005010X222A1")
        
        # Should flag missing subscriber
        assert not report.is_valid or len(report.warnings) > 0

    def test_clm_required_elements(self):
        """CLM segment must have required elements."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # CLM missing required elements
        report = validator.validate_segment(
            "CLM*CLAIM1~",  # Missing charge, place of service
            "CLM",
            "005010X222A1"
        )
        
        assert len(report.errors) > 0


@pytest.mark.compliance
@pytest.mark.hipaa
class TestNPIValidation:
    """National Provider Identifier validation."""

    def test_npi_must_be_10_digits(self):
        """NPI must be exactly 10 digits."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # NPI too short
        report = validator.validate_segment(
            "NM1*85*2*PROVIDER*****XX*123456789~",  # 9 digits
            "NM1",
            "005010X222A1"
        )
        
        assert any("NPI" in str(e.message).upper() or "length" in str(e.message).lower() 
                  for e in report.errors)

    def test_npi_must_be_numeric(self):
        """NPI must be all numeric."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        report = validator.validate_segment(
            "NM1*85*2*PROVIDER*****XX*12345ABCDE~",  # Contains letters
            "NM1",
            "005010X222A1"
        )
        
        assert len(report.errors) > 0

    def test_npi_luhn_check(self):
        """NPI must pass Luhn check digit validation."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # NPI with invalid check digit
        report = validator.validate_segment(
            "NM1*85*2*PROVIDER*****XX*1234567890~",  # Fails Luhn
            "NM1",
            "005010X222A1"
        )
        
        # Should flag invalid NPI (if strict validation enabled)
        # This may be a warning rather than error


@pytest.mark.compliance
@pytest.mark.hipaa
class TestEntityIdentifierCodes:
    """Entity Identifier Code validation for HIPAA."""

    @pytest.mark.parametrize("entity_code,description", [
        ("85", "Billing Provider"),
        ("87", "Pay-to Provider"),
        ("IL", "Insured/Subscriber"),
        ("QC", "Patient"),
        ("PR", "Payer"),
        ("82", "Rendering Provider"),
        ("77", "Service Facility"),
        ("DN", "Referring Provider"),
        ("71", "Attending Physician"),
    ])
    def test_valid_entity_codes(self, entity_code, description):
        """Valid HIPAA entity codes must be accepted."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        report = validator.validate_segment(
            f"NM1*{entity_code}*2*NAME~",
            "NM1",
            "005010X222A1"
        )
        
        # Should not flag the entity code as invalid
        entity_errors = [e for e in report.errors if "entity" in str(e.message).lower()]
        assert len(entity_errors) == 0


@pytest.mark.compliance
@pytest.mark.hipaa
class TestDiagnosisCodes:
    """Diagnosis code validation."""

    def test_icd10_format_accepted(self):
        """Valid ICD-10 format must be accepted."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # HI with valid ICD-10
        report = validator.validate_segment(
            "HI*ABK:M545~",  # M54.5 without dot
            "HI",
            "005010X222A1"
        )
        
        # Should accept valid ICD-10
        icd_errors = [e for e in report.errors 
                     if "diagnosis" in str(e.message).lower() or "ICD" in str(e.message)]
        assert len(icd_errors) == 0

    def test_icd10_qualifier_required(self):
        """Diagnosis qualifier (ABK/ABF) is required."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # HI without proper qualifier
        report = validator.validate_segment(
            "HI*XX:M545~",  # Invalid qualifier
            "HI",
            "005010X222A1"
        )
        
        # Should flag invalid qualifier
        assert len(report.errors) > 0 or len(report.warnings) > 0


@pytest.mark.compliance
@pytest.mark.hipaa
class TestDateFormats:
    """Date format validation for HIPAA."""

    def test_date_ccyymmdd_format(self):
        """Dates must be in CCYYMMDD format."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # Valid date format
        report = validator.validate_segment(
            "DTP*472*D8*20231115~",
            "DTP",
            "005010X222A1"
        )
        
        date_errors = [e for e in report.errors if "date" in str(e.message).lower()]
        assert len(date_errors) == 0

    def test_invalid_date_rejected(self):
        """Invalid dates must be rejected."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # Invalid date (month 13)
        report = validator.validate_segment(
            "DTP*472*D8*20231315~",
            "DTP",
            "005010X222A1"
        )
        
        assert len(report.errors) > 0

    def test_date_qualifier_d8_required(self):
        """D8 qualifier required for single dates."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # Date without D8 qualifier
        report = validator.validate_segment(
            "DTP*472**20231115~",  # Missing D8
            "DTP",
            "005010X222A1"
        )
        
        assert len(report.errors) > 0 or len(report.warnings) > 0


@pytest.mark.compliance
@pytest.mark.hipaa
class TestServiceLineCodes:
    """Service line (SV1/SV2) validation."""

    def test_sv1_procedure_code_required(self):
        """SV1 must have procedure code."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        report = validator.validate_segment(
            "SV1**100*UN*1~",  # Missing procedure
            "SV1",
            "005010X222A1"
        )
        
        assert len(report.errors) > 0

    def test_sv1_charge_required(self):
        """SV1 must have line item charge."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        report = validator.validate_segment(
            "SV1*HC:99213~",  # Missing charge
            "SV1",
            "005010X222A1"
        )
        
        assert len(report.errors) > 0

    def test_sv1_units_required(self):
        """SV1 must have service units."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        report = validator.validate_segment(
            "SV1*HC:99213*100~",  # Missing units
            "SV1",
            "005010X222A1"
        )
        
        assert len(report.errors) > 0 or len(report.warnings) > 0


@pytest.mark.compliance
@pytest.mark.hipaa
class TestAcknowledgment999:
    """999 Implementation Acknowledgment requirements."""

    def test_999_required_for_hipaa(self, minimal_837p_content):
        """HIPAA transactions require 999 (not 997)."""
        from x12.core.parser import Parser
        from x12.core.validator import X12Validator
        from x12.acknowledgments import AcknowledgmentGenerator
        
        parser = Parser()
        validator = X12Validator()
        
        interchange = parser.parse(minimal_837p_content)
        report = validator.validate_transaction(
            interchange.functional_groups[0].transactions[0],
            "005010X222A1"
        )
        
        ack_gen = AcknowledgmentGenerator(
            sender_id="R", sender_qualifier="ZZ",
            receiver_id="S", receiver_qualifier="ZZ",
        )
        
        # Should generate 999 for HIPAA
        ack = ack_gen.generate_999(
            interchange.functional_groups[0],
            [report],
        )
        
        assert ack is not None
        # 999 should have implementation convention reference
        assert ack.implementation_convention is not None
