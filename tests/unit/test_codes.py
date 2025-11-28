"""
Unit tests for X12 codes module.

Tests code set registry, lookups, and validation.
TDD: These tests define the expected interface before implementation.
"""
from __future__ import annotations

import pytest


@pytest.mark.unit
class TestCodeSetRegistry:
    """Tests for code set registry."""

    def test_registry_singleton(self):
        """Registry should be accessible as singleton."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        assert registry is not None

    def test_get_code_set_by_name(self):
        """Must retrieve code set by name."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        code_set = registry.get_code_set("entity_identifier")
        
        assert code_set is not None
        assert code_set.name == "entity_identifier"

    def test_list_available_code_sets(self):
        """Must list all available code sets."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        code_sets = registry.list_code_sets()
        
        assert isinstance(code_sets, list)
        assert "entity_identifier" in code_sets
        assert "place_of_service" in code_sets
        assert "claim_status" in code_sets

    def test_register_custom_code_set(self):
        """Must allow registering custom code sets."""
        from x12.codes import CodeRegistry, CodeSet
        
        registry = CodeRegistry()
        custom = CodeSet(
            name="custom_codes",
            description="Custom code set",
            codes={"A": "Code A", "B": "Code B"},
        )
        
        registry.register(custom)
        retrieved = registry.get_code_set("custom_codes")
        
        assert retrieved is not None
        assert retrieved.name == "custom_codes"


@pytest.mark.unit
class TestCodeSet:
    """Tests for code set structure."""

    def test_code_set_has_name(self):
        """Code set must have name."""
        from x12.codes import CodeSet
        
        code_set = CodeSet(
            name="test_codes",
            description="Test code set",
        )
        
        assert code_set.name == "test_codes"
        assert code_set.description == "Test code set"

    def test_code_set_contains_codes(self):
        """Code set must contain code-description pairs."""
        from x12.codes import CodeSet
        
        code_set = CodeSet(
            name="gender",
            description="Gender codes",
            codes={
                "M": "Male",
                "F": "Female",
                "U": "Unknown",
            },
        )
        
        assert "M" in code_set
        assert "X" not in code_set

    def test_code_set_get_description(self):
        """Must get description for code."""
        from x12.codes import CodeSet
        
        code_set = CodeSet(
            name="gender",
            description="Gender codes",
            codes={
                "M": "Male",
                "F": "Female",
            },
        )
        
        assert code_set.get_description("M") == "Male"
        assert code_set.get_description("X") is None

    def test_code_set_validate(self):
        """Must validate code exists in set."""
        from x12.codes import CodeSet
        
        code_set = CodeSet(
            name="gender",
            description="Gender codes",
            codes={"M": "Male", "F": "Female"},
        )
        
        assert code_set.is_valid("M") is True
        assert code_set.is_valid("X") is False


@pytest.mark.unit
class TestEntityIdentifierCodes:
    """Tests for Entity Identifier (NM101) codes."""

    def test_billing_provider_code(self):
        """85 = Billing Provider."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        code_set = registry.get_code_set("entity_identifier")
        
        assert code_set.is_valid("85")
        assert "Billing Provider" in code_set.get_description("85")

    def test_subscriber_code(self):
        """IL = Insured or Subscriber."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        code_set = registry.get_code_set("entity_identifier")
        
        assert code_set.is_valid("IL")
        assert "Subscriber" in code_set.get_description("IL") or "Insured" in code_set.get_description("IL")

    def test_payer_code(self):
        """PR = Payer."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        code_set = registry.get_code_set("entity_identifier")
        
        assert code_set.is_valid("PR")
        assert "Payer" in code_set.get_description("PR")


@pytest.mark.unit
class TestPlaceOfServiceCodes:
    """Tests for Place of Service codes."""

    def test_office_code(self):
        """11 = Office."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        code_set = registry.get_code_set("place_of_service")
        
        assert code_set.is_valid("11")
        assert "Office" in code_set.get_description("11")

    def test_hospital_codes(self):
        """21 = Inpatient Hospital, 22 = Outpatient Hospital."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        code_set = registry.get_code_set("place_of_service")
        
        assert code_set.is_valid("21")
        assert code_set.is_valid("22")
        assert "Inpatient" in code_set.get_description("21")

    def test_emergency_room_code(self):
        """23 = Emergency Room."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        code_set = registry.get_code_set("place_of_service")
        
        assert code_set.is_valid("23")


@pytest.mark.unit
class TestClaimStatusCodes:
    """Tests for Claim Status codes (CLP02)."""

    def test_processed_primary(self):
        """1 = Processed as Primary."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        code_set = registry.get_code_set("claim_status")
        
        assert code_set.is_valid("1")
        assert "Primary" in code_set.get_description("1")

    def test_denied(self):
        """4 = Denied."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        code_set = registry.get_code_set("claim_status")
        
        assert code_set.is_valid("4")
        assert "Denied" in code_set.get_description("4")


@pytest.mark.unit
class TestNPIValidation:
    """Tests for NPI validation."""

    def test_validate_valid_npi(self):
        """Must validate correct NPI."""
        from x12.codes import validate_npi
        
        # Valid NPI (passes Luhn check with prefix 80840)
        assert validate_npi("1234567893") is True

    def test_reject_invalid_npi_checksum(self):
        """Must reject NPI with invalid checksum."""
        from x12.codes import validate_npi
        
        assert validate_npi("1234567890") is False

    def test_reject_wrong_length_npi(self):
        """Must reject NPI with wrong length."""
        from x12.codes import validate_npi
        
        assert validate_npi("12345") is False
        assert validate_npi("12345678901234") is False

    def test_reject_non_numeric_npi(self):
        """Must reject non-numeric NPI."""
        from x12.codes import validate_npi
        
        assert validate_npi("123456789A") is False


@pytest.mark.unit
class TestTaxIdValidation:
    """Tests for Tax ID (EIN) validation."""

    def test_validate_valid_ein(self):
        """Must validate correct EIN format."""
        from x12.codes import validate_tax_id
        
        assert validate_tax_id("123456789") is True

    def test_reject_wrong_length(self):
        """Must reject wrong length."""
        from x12.codes import validate_tax_id
        
        assert validate_tax_id("12345") is False
        assert validate_tax_id("1234567890") is False

    def test_reject_non_numeric(self):
        """Must reject non-numeric."""
        from x12.codes import validate_tax_id
        
        assert validate_tax_id("12345678A") is False


@pytest.mark.unit
class TestDiagnosisCodeValidation:
    """Tests for ICD-10 diagnosis code validation."""

    def test_validate_icd10_format(self):
        """Must validate ICD-10 format."""
        from x12.codes import validate_diagnosis_code
        
        assert validate_diagnosis_code("A00") is True
        assert validate_diagnosis_code("A000") is True
        assert validate_diagnosis_code("Z9989") is True

    def test_reject_invalid_format(self):
        """Must reject invalid ICD-10 format."""
        from x12.codes import validate_diagnosis_code
        
        assert validate_diagnosis_code("123") is False  # Must start with letter
        assert validate_diagnosis_code("A") is False    # Too short


@pytest.mark.unit  
class TestProcedureCodeValidation:
    """Tests for CPT/HCPCS procedure code validation."""

    def test_validate_cpt_format(self):
        """Must validate CPT format (5 digits)."""
        from x12.codes import validate_procedure_code
        
        assert validate_procedure_code("99213") is True
        assert validate_procedure_code("00100") is True

    def test_validate_hcpcs_format(self):
        """Must validate HCPCS format (letter + 4 digits)."""
        from x12.codes import validate_procedure_code
        
        assert validate_procedure_code("J0120") is True
        assert validate_procedure_code("G0101") is True

    def test_reject_invalid_format(self):
        """Must reject invalid procedure code format."""
        from x12.codes import validate_procedure_code
        
        assert validate_procedure_code("123") is False   # Too short
        assert validate_procedure_code("ABCDE") is False # Wrong format
