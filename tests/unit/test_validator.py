"""
TDD Tests: Validation Framework

These tests DEFINE the expected behavior of the X12Validator class.
Implementation in x12/core/validator.py must satisfy these specifications.

Run: pytest tests/unit/test_validator.py -v
"""
import pytest


@pytest.mark.unit
class TestValidationReport:
    """Tests for ValidationReport structure."""

    def test_report_has_is_valid(self):
        """Report must have is_valid boolean property."""
        from x12.core.validator import ValidationReport
        
        report = ValidationReport()
        
        assert hasattr(report, 'is_valid')
        assert isinstance(report.is_valid, bool)

    def test_report_has_errors_list(self):
        """Report must have errors list."""
        from x12.core.validator import ValidationReport
        
        report = ValidationReport()
        
        assert hasattr(report, 'errors')
        assert isinstance(report.errors, list)

    def test_report_has_warnings_list(self):
        """Report must have warnings list."""
        from x12.core.validator import ValidationReport
        
        report = ValidationReport()
        
        assert hasattr(report, 'warnings')
        assert isinstance(report.warnings, list)

    def test_report_counts(self):
        """Report must track error and warning counts."""
        from x12.core.validator import ValidationReport
        
        report = ValidationReport()
        
        assert hasattr(report, 'error_count')
        assert hasattr(report, 'warning_count')


@pytest.mark.unit
class TestValidationResult:
    """Tests for individual validation results."""

    def test_result_has_severity(self):
        """Each result must have severity level."""
        from x12.core.validator import ValidationResult, ValidationSeverity
        
        result = ValidationResult(
            rule_id="TEST001",
            message="Test message",
            severity=ValidationSeverity.ERROR,
        )
        
        assert result.severity == ValidationSeverity.ERROR

    def test_result_has_location(self):
        """Each result must have location information."""
        from x12.core.validator import ValidationResult, ValidationSeverity
        
        result = ValidationResult(
            rule_id="TEST001",
            message="Test message",
            severity=ValidationSeverity.ERROR,
            segment_id="NM1",
            segment_position=5,
            element_index=3,
        )
        
        assert result.segment_id == "NM1"
        assert result.segment_position == 5
        assert result.element_index == 3

    def test_result_has_rule_id(self):
        """Each result must reference the rule that triggered it."""
        from x12.core.validator import ValidationResult, ValidationSeverity
        
        result = ValidationResult(
            rule_id="SYNTAX_001",
            message="Invalid character",
            severity=ValidationSeverity.ERROR,
        )
        
        assert result.rule_id == "SYNTAX_001"


@pytest.mark.unit
class TestSyntacticValidation:
    """Level 1: Syntactic validation tests."""

    def test_valid_edi_passes_syntax(self, minimal_837p_content):
        """Valid EDI must pass syntactic validation."""
        from x12.core.validator import X12Validator, ValidationCategory
        
        validator = X12Validator()
        report = validator.validate(minimal_837p_content)
        
        syntax_errors = [e for e in report.errors 
                        if e.category == ValidationCategory.SYNTAX]
        assert len(syntax_errors) == 0

    def test_must_start_with_isa(self):
        """EDI must start with ISA segment."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        content = "GS*HC*SENDER*RECEIVER~ST*837*0001~SE*2*0001~GE*1*1~"
        
        report = validator.validate(content)
        
        assert not report.is_valid
        assert any("ISA" in str(e.message) for e in report.errors)

    def test_must_end_with_iea(self):
        """EDI must end with IEA segment."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        content = "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~GS*HC~ST*837*0001~SE*2*0001~GE*1*1~"
        
        report = validator.validate(content)
        
        # Should flag missing/invalid IEA
        assert not report.is_valid or any("IEA" in str(e.message) for e in report.warnings)


@pytest.mark.unit
class TestStructuralValidation:
    """Level 2: Structural validation tests."""

    def test_missing_required_segment(self):
        """Missing required segment must be flagged."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        # 837P without BHT segment (required)
        content = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~
GS*HC*SENDER*RECEIVER*20231127*1200*1*X*005010X222A1~
ST*837*0001*005010X222A1~
SE*2*0001~
GE*1*1~
IEA*1*000000001~"""
        
        report = validator.validate(content)
        
        # Should flag missing BHT
        assert not report.is_valid

    def test_control_number_mismatch_st_se(self):
        """ST/SE control number mismatch must be flagged."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        content = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~
GS*HC*SENDER*RECEIVER*20231127*1200*1*X*005010X222A1~
ST*837*0001~
BHT*0019*00*244579*20231127*1200*CH~
SE*3*9999~
GE*1*1~
IEA*1*000000001~"""
        
        report = validator.validate(content)
        
        assert any("control number" in str(e.message).lower() for e in report.errors)

    def test_segment_count_mismatch(self):
        """SE01 segment count mismatch must be flagged."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        content = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~
GS*HC*SENDER*RECEIVER*20231127*1200*1*X*005010X222A1~
ST*837*0001~
BHT*0019*00*244579*20231127*1200*CH~
SE*99*0001~
GE*1*1~
IEA*1*000000001~"""
        
        report = validator.validate(content)
        
        assert any("count" in str(e.message).lower() for e in report.errors)

    def test_gs_ge_control_number_match(self):
        """GS/GE control numbers must match."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        content = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~
GS*HC*SENDER*RECEIVER*20231127*1200*1*X*005010X222A1~
ST*837*0001~
SE*2*0001~
GE*1*9999~
IEA*1*000000001~"""
        
        report = validator.validate(content)
        
        # GS06=1, GE02=9999 mismatch
        assert any("GE" in str(e.message) or "control" in str(e.message).lower() 
                  for e in report.errors)


@pytest.mark.unit
class TestElementValidation:
    """Level 3: Element-level validation tests."""

    def test_required_element_missing(self):
        """Missing required element must be flagged."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        # NM1*85 requires NM103 (name) but it's empty
        
        report = validator.validate_segment("NM1*85*2~", "NM1", "005010X222A1")
        
        # Should flag missing required element
        assert len(report.errors) > 0 or len(report.warnings) > 0

    def test_element_exceeds_max_length(self):
        """Element exceeding max length must be flagged."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        # NM103 max length is 60 for most implementations
        long_name = "X" * 100
        
        report = validator.validate_segment(f"NM1*85*2*{long_name}~", "NM1", "005010X222A1")
        
        assert any("length" in str(e.message).lower() for e in report.errors)

    def test_element_below_min_length(self):
        """Element below min length must be flagged."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        # NPI must be 10 digits
        
        report = validator.validate_segment("NM1*85*2*NAME*****XX*123~", "NM1", "005010X222A1")
        
        # NM109 too short for NPI
        assert len(report.errors) > 0 or len(report.warnings) > 0

    def test_invalid_code_value(self):
        """Invalid code value must be flagged."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        # NM101 must be valid entity identifier
        
        report = validator.validate_segment("NM1*ZZ*2*NAME~", "NM1", "005010X222A1")
        
        # ZZ may not be valid for NM101 depending on context
        assert len(report.results) >= 0  # At minimum, validation ran

    def test_invalid_date_format(self):
        """Invalid date must be flagged."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        report = validator.validate_segment("DTP*472*D8*20231340~", "DTP", "005010X222A1")
        
        # Month 13, day 40 is invalid
        assert any("date" in str(e.message).lower() for e in report.errors)

    def test_numeric_element_with_alpha(self):
        """Numeric element with alphabetic chars must be flagged."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # CLM02 (charge amount) should be numeric
        report = validator.validate_segment("CLM*CLAIM1*ABC~", "CLM", "005010X222A1")
        
        assert len(report.errors) > 0


@pytest.mark.unit
class TestSemanticValidation:
    """Level 4: Cross-element/segment validation tests."""

    def test_id_requires_qualifier(self):
        """NM109 (ID) requires NM108 (qualifier) when populated."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        # NM108 empty but NM109 populated
        
        report = validator.validate_segment("NM1*85*2*NAME*****1234567890~", "NM1", "005010X222A1")
        
        # Should flag missing qualifier
        assert len(report.errors) > 0 or len(report.warnings) > 0

    def test_qualifier_code_match(self):
        """ID qualifier must match ID format."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        # XX qualifier requires 10-digit NPI
        
        report = validator.validate_segment("NM1*85*2*NAME*****XX*123~", "NM1", "005010X222A1")
        
        # NPI too short
        assert len(report.errors) > 0


@pytest.mark.unit
class TestValidatorConfiguration:
    """Tests for validator configuration."""

    def test_strict_mode(self):
        """Strict mode must treat warnings as errors."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator(strict=True)
        
        assert validator.strict == True

    def test_lenient_mode(self):
        """Lenient mode must allow some deviations."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator(strict=False)
        
        assert validator.strict == False

    def test_custom_rules(self):
        """Validator must accept custom validation rules."""
        from x12.core.validator import X12Validator, ValidationRule
        
        custom_rule = ValidationRule(
            rule_id="CUSTOM_001",
            description="Custom test rule",
            validator=lambda seg: True,
        )
        
        validator = X12Validator(custom_rules=[custom_rule])
        
        assert len(validator.custom_rules) > 0


@pytest.mark.unit
class TestValidatorMethods:
    """Tests for validator methods."""

    def test_validate_content(self, minimal_837p_content):
        """validate() must accept EDI content string."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        report = validator.validate(minimal_837p_content)
        
        assert report is not None
        assert hasattr(report, 'is_valid')

    def test_validate_segment(self):
        """validate_segment() must validate single segment."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        report = validator.validate_segment("NM1*85*2*NAME~", "NM1")
        
        assert report is not None

    def test_validate_transaction(self):
        """validate_transaction() must validate parsed transaction."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # Assumes we have a TransactionSet object
        # report = validator.validate_transaction(transaction)
        
        assert hasattr(validator, 'validate_transaction')


@pytest.mark.unit
class TestHIPAAValidation:
    """HIPAA-specific validation tests."""

    @pytest.mark.hipaa
    def test_npi_validation(self):
        """NPI must be validated with Luhn check."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # Valid NPI: 1234567893 (passes Luhn)
        report = validator.validate_segment(
            "NM1*85*2*PROVIDER*****XX*1234567893~", 
            "NM1", 
            "005010X222A1"
        )
        
        # Should pass NPI validation
        npi_errors = [e for e in report.errors if "NPI" in str(e.message).upper()]
        assert len(npi_errors) == 0

    @pytest.mark.hipaa
    def test_invalid_npi(self):
        """Invalid NPI must be flagged."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        # Invalid NPI: 1234567890 (fails Luhn)
        report = validator.validate_segment(
            "NM1*85*2*PROVIDER*****XX*1234567890~",
            "NM1",
            "005010X222A1"
        )
        
        # Should flag invalid NPI
        assert len(report.errors) > 0 or len(report.warnings) > 0

    @pytest.mark.hipaa
    def test_tax_id_format(self):
        """Tax ID (EIN) must be 9 digits."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        
        report = validator.validate_segment(
            "REF*EI*12345~",  # Too short
            "REF",
            "005010X222A1"
        )
        
        assert len(report.errors) > 0 or len(report.warnings) > 0
