"""
X12 Code set registry.

Manages code sets for X12 element validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CodeSet:
    """A set of valid codes with descriptions.

    Attributes:
        name: Unique identifier for the code set.
        description: Human-readable description.
        codes: Dictionary mapping codes to descriptions.
    """

    name: str
    description: str
    codes: dict[str, str] = field(default_factory=dict)

    def __contains__(self, code: str) -> bool:
        """Check if code exists in set."""
        return code in self.codes

    def is_valid(self, code: str) -> bool:
        """Check if code is valid."""
        return code in self.codes

    def get_description(self, code: str) -> str | None:
        """Get description for code."""
        return self.codes.get(code)


class CodeRegistry:
    """Registry of X12 code sets.

    Provides access to standard X12 code sets for validation.

    Example:
        >>> registry = CodeRegistry()
        >>> entity_codes = registry.get_code_set("entity_identifier")
        >>> entity_codes.is_valid("85")
        True
    """

    def __init__(self) -> None:
        """Initialize registry with built-in code sets."""
        self._code_sets: dict[str, CodeSet] = {}
        self._load_builtin_code_sets()

    def _load_builtin_code_sets(self) -> None:
        """Load built-in X12 code sets."""
        # Entity Identifier Codes (NM101)
        self._code_sets["entity_identifier"] = CodeSet(
            name="entity_identifier",
            description="Entity Identifier Codes (NM101)",
            codes={
                "03": "Dependent",
                "1P": "Provider",
                "36": "Employer",
                "40": "Receiver",
                "41": "Submitter",
                "45": "Drop-off Location",
                "71": "Attending Physician",
                "72": "Operating Physician",
                "73": "Other Physician",
                "74": "Corrected Insured",
                "77": "Service Location",
                "82": "Rendering Provider",
                "85": "Billing Provider",
                "87": "Pay-to Provider",
                "DD": "Assistant Surgeon",
                "DK": "Ordering Physician",
                "DN": "Referring Provider",
                "DQ": "Supervising Physician",
                "FA": "Facility",
                "GB": "Other Insured",
                "IL": "Insured or Subscriber",
                "LI": "Independent Lab",
                "P3": "Primary Care Provider",
                "PE": "Payee",
                "PR": "Payer",
                "PW": "Pickup Address",
                "QC": "Patient",
                "QD": "Responsible Party",
                "SEP": "Secondary Payer",
                "TT": "Transfer To",
                "VN": "Vendor",
            },
        )

        # Place of Service Codes
        self._code_sets["place_of_service"] = CodeSet(
            name="place_of_service",
            description="Place of Service Codes (CLM05-1)",
            codes={
                "01": "Pharmacy",
                "02": "Telehealth",
                "03": "School",
                "04": "Homeless Shelter",
                "05": "Indian Health Service Free-standing",
                "06": "Indian Health Service Provider-based",
                "07": "Tribal 638 Free-standing",
                "08": "Tribal 638 Provider-based",
                "09": "Prison/Correctional Facility",
                "10": "Telehealth in Patient's Home",
                "11": "Office",
                "12": "Home",
                "13": "Assisted Living Facility",
                "14": "Group Home",
                "15": "Mobile Unit",
                "16": "Temporary Lodging",
                "17": "Walk-in Retail Health Clinic",
                "18": "Place of Employment",
                "19": "Off Campus-Outpatient Hospital",
                "20": "Urgent Care Facility",
                "21": "Inpatient Hospital",
                "22": "On Campus-Outpatient Hospital",
                "23": "Emergency Room - Hospital",
                "24": "Ambulatory Surgical Center",
                "25": "Birthing Center",
                "26": "Military Treatment Facility",
                "31": "Skilled Nursing Facility",
                "32": "Nursing Facility",
                "33": "Custodial Care Facility",
                "34": "Hospice",
                "41": "Ambulance - Land",
                "42": "Ambulance - Air or Water",
                "49": "Independent Clinic",
                "50": "Federally Qualified Health Center",
                "51": "Inpatient Psychiatric Facility",
                "52": "Psychiatric Facility Partial Hospitalization",
                "53": "Community Mental Health Center",
                "54": "Intermediate Care Facility",
                "55": "Residential Substance Abuse Facility",
                "56": "Psychiatric Residential Treatment Center",
                "57": "Non-residential Substance Abuse Facility",
                "58": "Non-residential Opioid Treatment Facility",
                "60": "Mass Immunization Center",
                "61": "Comprehensive Inpatient Rehabilitation Facility",
                "62": "Comprehensive Outpatient Rehabilitation Facility",
                "65": "End Stage Renal Disease Treatment Facility",
                "71": "Public Health Clinic",
                "72": "Rural Health Clinic",
                "81": "Independent Laboratory",
                "99": "Other Place of Service",
            },
        )

        # Claim Status Codes (CLP02)
        self._code_sets["claim_status"] = CodeSet(
            name="claim_status",
            description="Claim Status Codes (CLP02)",
            codes={
                "1": "Processed as Primary",
                "2": "Processed as Secondary",
                "3": "Processed as Tertiary",
                "4": "Denied",
                "19": "Processed as Primary, Forwarded to Additional Payer",
                "20": "Processed as Secondary, Forwarded to Additional Payer",
                "21": "Processed as Tertiary, Forwarded to Additional Payer",
                "22": "Reversal of Previous Payment",
                "23": "Not Our Claim, Forwarded to Additional Payer",
                "25": "Predetermination Pricing Only - No Payment",
            },
        )

        # Claim Filing Indicator Codes
        self._code_sets["claim_filing_indicator"] = CodeSet(
            name="claim_filing_indicator",
            description="Claim Filing Indicator Codes (SBR09)",
            codes={
                "09": "Self Pay",
                "11": "Other Non-Federal Programs",
                "12": "Preferred Provider Organization (PPO)",
                "13": "Point of Service (POS)",
                "14": "Exclusive Provider Organization (EPO)",
                "15": "Indemnity Insurance",
                "16": "Health Maintenance Organization (HMO) Medicare Risk",
                "17": "Dental Maintenance Organization",
                "AM": "Automobile Medical",
                "BL": "Blue Cross/Blue Shield",
                "CH": "CHAMPUS",
                "CI": "Commercial Insurance Co.",
                "DS": "Disability",
                "FI": "Federal Employees Program",
                "HM": "Health Maintenance Organization",
                "LM": "Liability Medical",
                "MA": "Medicare Part A",
                "MB": "Medicare Part B",
                "MC": "Medicaid",
                "OF": "Other Federal Program",
                "TV": "Title V",
                "VA": "Veterans Affairs Plan",
                "WC": "Workers' Compensation Health Claim",
                "ZZ": "Mutually Defined",
            },
        )

        # Gender Codes
        self._code_sets["gender"] = CodeSet(
            name="gender",
            description="Gender Codes (DMG03)",
            codes={
                "F": "Female",
                "M": "Male",
                "U": "Unknown",
            },
        )

        # Relationship Codes
        self._code_sets["relationship"] = CodeSet(
            name="relationship",
            description="Individual Relationship Codes (SBR02)",
            codes={
                "01": "Spouse",
                "18": "Self",
                "19": "Child",
                "20": "Employee",
                "21": "Unknown",
                "39": "Organ Donor",
                "40": "Cadaver Donor",
                "53": "Life Partner",
                "G8": "Other Relationship",
            },
        )

        # Load extended code sets
        self._load_extended_code_sets()

    def _load_extended_code_sets(self) -> None:
        """Load extended code sets for healthcare transactions."""
        # Claim Adjustment Reason Codes (CARC) - most common
        self._code_sets["claim_adjustment_reason"] = CodeSet(
            name="claim_adjustment_reason",
            description="Claim Adjustment Reason Codes (CARC)",
            codes={
                "1": "Deductible Amount",
                "2": "Coinsurance Amount",
                "3": "Co-payment Amount",
                "4": "Procedure code inconsistent with modifier",
                "16": "Claim lacks information or has errors",
                "18": "Exact duplicate claim/service",
                "23": "Impact of prior payer adjudication",
                "29": "Time limit for filing has expired",
                "45": "Charge exceeds fee schedule/maximum allowable",
                "50": "Non-covered service - not medically necessary",
                "96": "Non-covered charge(s)",
                "97": "Benefit included in another service",
                "119": "Benefit maximum reached for this period",
                "197": "Precertification/authorization absent",
            },
        )

        # Remittance Advice Remark Codes (RARC) - most common
        self._code_sets["remittance_advice_remark"] = CodeSet(
            name="remittance_advice_remark",
            description="Remittance Advice Remark Codes (RARC)",
            codes={
                "M1": "X-ray not taken within required timeframe",
                "M15": "Assistant at surgery services not covered separately",
                "M76": "Missing/incomplete/invalid diagnosis",
                "MA01": "Alert: If you disagree with approved amounts",
                "MA04": "Secondary payment requires identity of prior payer",
                "MA07": "Claim forwarded to supplemental insurer",
                "MA18": "Claim forwarded to Medigap insurer",
                "N1": "Alert: You may appeal this decision",
                "N4": "Missing/incomplete/invalid prior authorization number",
                "N20": "Service not separately payable",
                "N362": "Missing/incomplete/invalid tooth number",
            },
        )

        # Service Type Codes (270/271)
        self._code_sets["service_type"] = CodeSet(
            name="service_type",
            description="Service Type Codes (270/271)",
            codes={
                "1": "Medical Care",
                "2": "Surgical",
                "3": "Consultation",
                "4": "Diagnostic X-Ray",
                "5": "Diagnostic Lab",
                "30": "Health Benefit Plan Coverage",
                "35": "Dental Care",
                "47": "Hospital",
                "48": "Hospital - Inpatient",
                "50": "Hospital - Outpatient",
                "86": "Emergency Services",
                "88": "Pharmacy",
                "98": "Professional (Physician) Visit - Office",
                "UC": "Urgent Care",
                "MH": "Mental Health",
            },
        )

        # Diagnosis Type Qualifiers
        self._code_sets["diagnosis_type_qualifier"] = CodeSet(
            name="diagnosis_type_qualifier",
            description="Diagnosis Type Qualifier Codes (HI)",
            codes={
                "ABK": "Principal Diagnosis - ICD-10-CM",
                "ABJ": "Admitting Diagnosis - ICD-10-CM",
                "ABF": "Other Diagnosis - ICD-10-CM",
                "ABN": "External Cause of Injury",
                "BBR": "Principal Procedure - ICD-10-PCS",
                "BBQ": "Other Procedure - ICD-10-PCS",
                "BK": "Principal Diagnosis - ICD-9-CM",
                "BF": "Other Diagnosis - ICD-9-CM",
            },
        )

        # Procedure Code Qualifiers
        self._code_sets["procedure_code_qualifier"] = CodeSet(
            name="procedure_code_qualifier",
            description="Procedure Code Qualifier Codes",
            codes={
                "HC": "HCPCS",
                "AD": "American Dental Association Codes",
                "ER": "Revenue Code",
                "N4": "National Drug Code (NDC)",
                "ZZ": "Mutually Defined",
            },
        )

        # Claim Frequency Codes
        self._code_sets["claim_frequency"] = CodeSet(
            name="claim_frequency",
            description="Claim Frequency Type Codes (CLM05-3)",
            codes={
                "1": "Original Claim",
                "5": "Late Charges Only",
                "6": "Corrected Claim",
                "7": "Replacement of Prior Claim",
                "8": "Void/Cancel of Prior Claim",
            },
        )

        # Provider Taxonomy Codes (common)
        self._code_sets["provider_taxonomy"] = CodeSet(
            name="provider_taxonomy",
            description="Provider Taxonomy Codes",
            codes={
                "207Q00000X": "Family Medicine",
                "207R00000X": "Internal Medicine",
                "208000000X": "Pediatrics",
                "208D00000X": "General Practice",
                "282N00000X": "General Acute Care Hospital",
                "333600000X": "Pharmacy",
                "363L00000X": "Nurse Practitioner",
                "363LA2200X": "Adult Health Nurse Practitioner",
                "367A00000X": "Advanced Practice Midwife",
            },
        )

        # Revenue Codes (UB-04)
        self._code_sets["revenue_code"] = CodeSet(
            name="revenue_code",
            description="Revenue Codes (UB-04)",
            codes={
                "0100": "All-Inclusive Room & Board",
                "0110": "Room & Board - Private",
                "0120": "Room & Board - Semi-Private",
                "0250": "Pharmacy",
                "0260": "IV Therapy",
                "0270": "Medical/Surgical Supplies",
                "0300": "Laboratory",
                "0320": "Radiology - Diagnostic",
                "0350": "CT Scan",
                "0360": "OR Services",
                "0370": "Anesthesia",
                "0450": "Emergency Room",
                "0460": "Pulmonary Function",
                "0636": "Drugs Requiring Detailed Coding",
            },
        )

        # Modifier Codes
        self._code_sets["modifier"] = CodeSet(
            name="modifier",
            description="CPT/HCPCS Modifier Codes",
            codes={
                "22": "Increased Procedural Services",
                "25": "Significant, Separately Identifiable E/M Service",
                "26": "Professional Component",
                "50": "Bilateral Procedure",
                "51": "Multiple Procedures",
                "59": "Distinct Procedural Service",
                "76": "Repeat Procedure Same Physician",
                "77": "Repeat Procedure Different Physician",
                "LT": "Left Side",
                "RT": "Right Side",
                "TC": "Technical Component",
                "XE": "Separate Encounter",
                "XP": "Separate Practitioner",
                "XS": "Separate Structure",
                "XU": "Unusual Non-Overlapping Service",
            },
        )

        # Unit of Measure Codes
        self._code_sets["unit_of_measure"] = CodeSet(
            name="unit_of_measure",
            description="Unit of Measure Codes",
            codes={
                "DA": "Days",
                "EA": "Each",
                "GR": "Gram",
                "ME": "Milligram",
                "MJ": "Minutes",
                "ML": "Milliliter",
                "UN": "Unit",
                "F2": "International Unit",
            },
        )

        # Adjustment Group Codes (CAS)
        self._code_sets["adjustment_group"] = CodeSet(
            name="adjustment_group",
            description="Claim Adjustment Group Codes (CAS)",
            codes={
                "CO": "Contractual Obligations",
                "CR": "Correction and Reversal",
                "OA": "Other Adjustments",
                "PI": "Payer Initiated Reductions",
                "PR": "Patient Responsibility",
            },
        )

        # Eligibility/Benefit Information Codes (EB01)
        self._code_sets["eligibility_benefit_info"] = CodeSet(
            name="eligibility_benefit_info",
            description="Eligibility/Benefit Information Codes (EB01)",
            codes={
                "1": "Active Coverage",
                "2": "Active - Full Risk Capitation",
                "3": "Active - Services Capitated",
                "4": "Active - Services Capitated to Primary Care Physician",
                "5": "Active - Pending Investigation",
                "6": "Inactive",
                "7": "Inactive - Pending Eligibility Update",
                "8": "Inactive - Pending Investigation",
                "A": "Co-Insurance",
                "B": "Co-Payment",
                "C": "Deductible",
                "D": "Benefit Description",
                "E": "Exclusions",
                "F": "Limitations",
                "G": "Out of Pocket (Stop Loss)",
                "H": "Unlimited",
                "I": "Non-Covered",
                "J": "Cost Containment",
                "K": "Reserve",
                "L": "Primary Care Provider",
                "M": "Pre-existing Condition",
                "MC": "Managed Care Coordinator",
                "N": "Services Restricted to Following Provider",
                "O": "Not Deemed a Medical Necessity",
                "P": "Benefit Disclaimer",
                "Q": "Second Surgical Opinion Required",
                "R": "Other or Additional Payor",
                "S": "Prior Year(s) History",
                "T": "Card(s) Reported Lost/Stolen",
                "U": "Contact Following Entity for Information",
                "V": "Cannot Process",
                "W": "Other Source of Data",
                "X": "Health Care Facility",
                "Y": "Spend Down",
            },
        )

        # Time Period Qualifier Codes (EB06)
        self._code_sets["time_period_qualifier"] = CodeSet(
            name="time_period_qualifier",
            description="Time Period Qualifier Codes (EB06)",
            codes={
                "6": "Hour",
                "7": "Day",
                "21": "Years",
                "22": "Service Year",
                "23": "Calendar Year",
                "24": "Year to Date",
                "25": "Contract",
                "26": "Episode",
                "27": "Visit",
                "28": "Outlier",
                "29": "Remaining",
                "30": "Exceeded",
                "31": "Not Exceeded",
                "32": "Lifetime",
                "33": "Lifetime Remaining",
                "34": "Month",
                "35": "Week",
                "36": "Admission",
            },
        )

    def get_code_set(self, name: str) -> CodeSet | None:
        """Get code set by name.

        Args:
            name: Code set name.

        Returns:
            CodeSet or None if not found.
        """
        return self._code_sets.get(name)

    def list_code_sets(self) -> list[str]:
        """List all available code set names.

        Returns:
            List of code set names.
        """
        return list(self._code_sets.keys())

    def register(self, code_set: CodeSet) -> None:
        """Register a custom code set.

        Args:
            code_set: CodeSet to register.
        """
        self._code_sets[code_set.name] = code_set
