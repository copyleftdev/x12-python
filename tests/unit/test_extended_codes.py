"""
Unit tests for extended X12 code sets.

Tests additional code sets for healthcare and supply chain transactions.
TDD: These tests define the expected interface before implementation.
"""
from __future__ import annotations

import pytest


@pytest.mark.unit
class TestClaimAdjustmentReasonCodes:
    """Tests for Claim Adjustment Reason Codes (CARC)."""

    def test_carc_code_set_exists(self):
        """CARC code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        carc = registry.get_code_set("claim_adjustment_reason")
        
        assert carc is not None
        assert carc.name == "claim_adjustment_reason"

    def test_carc_common_codes(self):
        """Must have common CARC codes."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        carc = registry.get_code_set("claim_adjustment_reason")
        
        # Contractual Obligation
        assert carc.is_valid("45")
        assert "Charge" in carc.get_description("45") or "exceed" in carc.get_description("45").lower()
        
        # Deductible
        assert carc.is_valid("1")
        assert "Deductible" in carc.get_description("1")
        
        # Coinsurance
        assert carc.is_valid("2")
        assert "Coinsurance" in carc.get_description("2")
        
        # Copay
        assert carc.is_valid("3")
        assert "Co-pay" in carc.get_description("3") or "Copay" in carc.get_description("3")

    def test_carc_denial_codes(self):
        """Must have denial reason codes."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        carc = registry.get_code_set("claim_adjustment_reason")
        
        # Not covered
        assert carc.is_valid("96")
        
        # Non-covered charges
        assert carc.is_valid("97")


@pytest.mark.unit
class TestRemittanceAdviceRemarkCodes:
    """Tests for Remittance Advice Remark Codes (RARC)."""

    def test_rarc_code_set_exists(self):
        """RARC code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        rarc = registry.get_code_set("remittance_advice_remark")
        
        assert rarc is not None
        assert rarc.name == "remittance_advice_remark"

    def test_rarc_common_codes(self):
        """Must have common RARC codes."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        rarc = registry.get_code_set("remittance_advice_remark")
        
        # Common remark codes
        assert rarc.is_valid("M1")  # X-ray not taken
        assert rarc.is_valid("N1")  # Alert
        assert rarc.is_valid("MA01")  # Medicare secondary payer


@pytest.mark.unit
class TestServiceTypeCodes:
    """Tests for Service Type Codes (EB01 in 271)."""

    def test_service_type_code_set_exists(self):
        """Service type code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        stc = registry.get_code_set("service_type")
        
        assert stc is not None

    def test_common_service_types(self):
        """Must have common service type codes."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        stc = registry.get_code_set("service_type")
        
        # Medical Care
        assert stc.is_valid("1")
        
        # Surgical
        assert stc.is_valid("2")
        
        # Hospital - Inpatient
        assert stc.is_valid("48")
        
        # Hospital - Outpatient
        assert stc.is_valid("50")
        
        # Professional (Physician) Visit - Office
        assert stc.is_valid("98")
        
        # Health Benefit Plan Coverage
        assert stc.is_valid("30")


@pytest.mark.unit
class TestDiagnosisTypeQualifiers:
    """Tests for Diagnosis Type Qualifier codes."""

    def test_diagnosis_qualifier_code_set_exists(self):
        """Diagnosis qualifier code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        dq = registry.get_code_set("diagnosis_type_qualifier")
        
        assert dq is not None

    def test_diagnosis_qualifiers(self):
        """Must have HI segment qualifiers."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        dq = registry.get_code_set("diagnosis_type_qualifier")
        
        # Principal Diagnosis
        assert dq.is_valid("ABK")
        assert "Principal" in dq.get_description("ABK")
        
        # Admitting Diagnosis  
        assert dq.is_valid("ABJ")
        
        # Other Diagnosis
        assert dq.is_valid("ABF")
        
        # Principal Procedure
        assert dq.is_valid("BBR")


@pytest.mark.unit
class TestProcedureCodeQualifiers:
    """Tests for Procedure Code Qualifier codes."""

    def test_procedure_qualifier_code_set_exists(self):
        """Procedure qualifier code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        pq = registry.get_code_set("procedure_code_qualifier")
        
        assert pq is not None

    def test_procedure_qualifiers(self):
        """Must have SV1/SV2 procedure qualifiers."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        pq = registry.get_code_set("procedure_code_qualifier")
        
        # HCPCS
        assert pq.is_valid("HC")
        
        # ICD Procedure
        assert pq.is_valid("AD")
        
        # Revenue Code
        assert pq.is_valid("ER")
        
        # NDC (National Drug Code)
        assert pq.is_valid("N4")


@pytest.mark.unit
class TestClaimFrequencyCodes:
    """Tests for Claim Frequency Type codes."""

    def test_claim_frequency_code_set_exists(self):
        """Claim frequency code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        cf = registry.get_code_set("claim_frequency")
        
        assert cf is not None

    def test_claim_frequency_codes(self):
        """Must have CLM05-3 frequency codes."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        cf = registry.get_code_set("claim_frequency")
        
        # Original
        assert cf.is_valid("1")
        assert "Original" in cf.get_description("1")
        
        # Replacement
        assert cf.is_valid("7")
        assert "Replacement" in cf.get_description("7")
        
        # Void
        assert cf.is_valid("8")
        assert "Void" in cf.get_description("8")


@pytest.mark.unit
class TestProviderTaxonomyCodes:
    """Tests for Provider Taxonomy codes."""

    def test_taxonomy_code_set_exists(self):
        """Provider taxonomy code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        tax = registry.get_code_set("provider_taxonomy")
        
        assert tax is not None

    def test_common_taxonomy_codes(self):
        """Must have common provider taxonomy codes."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        tax = registry.get_code_set("provider_taxonomy")
        
        # Internal Medicine
        assert tax.is_valid("207R00000X")
        
        # Family Medicine
        assert tax.is_valid("207Q00000X")
        
        # General Acute Care Hospital
        assert tax.is_valid("282N00000X")
        
        # Pharmacy
        assert tax.is_valid("333600000X")


@pytest.mark.unit
class TestRevenueCodeSet:
    """Tests for Revenue Codes (UB-04)."""

    def test_revenue_code_set_exists(self):
        """Revenue code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        rev = registry.get_code_set("revenue_code")
        
        assert rev is not None

    def test_common_revenue_codes(self):
        """Must have common revenue codes."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        rev = registry.get_code_set("revenue_code")
        
        # Room & Board - Private
        assert rev.is_valid("0110")
        
        # Emergency Room
        assert rev.is_valid("0450")
        
        # Laboratory
        assert rev.is_valid("0300")
        
        # Pharmacy
        assert rev.is_valid("0250")


@pytest.mark.unit
class TestModifierCodes:
    """Tests for CPT/HCPCS Modifier codes."""

    def test_modifier_code_set_exists(self):
        """Modifier code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        mod = registry.get_code_set("modifier")
        
        assert mod is not None

    def test_common_modifiers(self):
        """Must have common modifier codes."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        mod = registry.get_code_set("modifier")
        
        # Professional component
        assert mod.is_valid("26")
        
        # Technical component
        assert mod.is_valid("TC")
        
        # Left side
        assert mod.is_valid("LT")
        
        # Right side
        assert mod.is_valid("RT")
        
        # Modifier 59 - Distinct Service
        assert mod.is_valid("59")


@pytest.mark.unit
class TestUnitsOfMeasure:
    """Tests for Units of Measure codes."""

    def test_uom_code_set_exists(self):
        """UOM code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        uom = registry.get_code_set("unit_of_measure")
        
        assert uom is not None

    def test_common_uom_codes(self):
        """Must have common unit codes."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        uom = registry.get_code_set("unit_of_measure")
        
        # Unit
        assert uom.is_valid("UN")
        
        # Minutes
        assert uom.is_valid("MJ")
        
        # Days
        assert uom.is_valid("DA")
        
        # Each
        assert uom.is_valid("EA")
        
        # Milliliter
        assert uom.is_valid("ML")


@pytest.mark.unit
class TestAdjustmentGroupCodes:
    """Tests for Claim Adjustment Group codes."""

    def test_adjustment_group_code_set_exists(self):
        """Adjustment group code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        grp = registry.get_code_set("adjustment_group")
        
        assert grp is not None

    def test_adjustment_group_codes(self):
        """Must have CAS segment group codes."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        grp = registry.get_code_set("adjustment_group")
        
        # Contractual Obligation
        assert grp.is_valid("CO")
        assert "Contractual" in grp.get_description("CO")
        
        # Patient Responsibility
        assert grp.is_valid("PR")
        assert "Patient" in grp.get_description("PR")
        
        # Other Adjustment
        assert grp.is_valid("OA")
        
        # Payer Initiated Reduction
        assert grp.is_valid("PI")
        
        # Correction/Reversal
        assert grp.is_valid("CR")


@pytest.mark.unit
class TestEligibilityResponseCodes:
    """Tests for Eligibility/Benefit Response codes."""

    def test_eligibility_info_code_set_exists(self):
        """EB01 code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        eb = registry.get_code_set("eligibility_benefit_info")
        
        assert eb is not None

    def test_eligibility_info_codes(self):
        """Must have EB01 eligibility codes."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        eb = registry.get_code_set("eligibility_benefit_info")
        
        # Active Coverage
        assert eb.is_valid("1")
        assert "Active" in eb.get_description("1")
        
        # Active - Full Risk Capitation
        assert eb.is_valid("2")
        
        # Inactive
        assert eb.is_valid("6")
        assert "Inactive" in eb.get_description("6")
        
        # Co-Insurance
        assert eb.is_valid("A")
        
        # Co-Payment
        assert eb.is_valid("B")
        
        # Deductible
        assert eb.is_valid("C")
        
        # Limitations
        assert eb.is_valid("F")


@pytest.mark.unit
class TestTimeQualifierCodes:
    """Tests for Time Period Qualifier codes (EB06)."""

    def test_time_qualifier_code_set_exists(self):
        """Time qualifier code set must exist."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        tq = registry.get_code_set("time_period_qualifier")
        
        assert tq is not None

    def test_time_qualifier_codes(self):
        """Must have EB06 time qualifiers."""
        from x12.codes import CodeRegistry
        
        registry = CodeRegistry()
        tq = registry.get_code_set("time_period_qualifier")
        
        # Calendar Year
        assert tq.is_valid("23")
        
        # Year to Date
        assert tq.is_valid("24")
        
        # Visit
        assert tq.is_valid("27")
        
        # Lifetime
        assert tq.is_valid("29")
        
        # Service Year
        assert tq.is_valid("26")
