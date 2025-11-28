"""
X12 EDI Validation Framework.

Multi-level validation: syntax, structure, element, semantic.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from x12.models import Segment, TransactionSet


class ValidationSeverity(Enum):
    """Severity level for validation results."""
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


class ValidationCategory(Enum):
    """Category of validation rule."""
    SYNTAX = auto()
    STRUCTURE = auto()
    ELEMENT = auto()
    SEMANTIC = auto()
    HIPAA = auto()


@dataclass
class ValidationResult:
    """A single validation result.
    
    Attributes:
        rule_id: Identifier for the rule that produced this result.
        message: Human-readable description.
        severity: Error, warning, or info.
        category: Type of validation.
        segment_id: Segment that triggered result.
        segment_position: Position in transaction.
        element_index: Element position (1-indexed).
        actual: The actual value found.
    """
    rule_id: str
    message: str
    severity: ValidationSeverity
    category: ValidationCategory = ValidationCategory.SYNTAX
    segment_id: str | None = None
    segment_position: int | None = None
    element_index: int | None = None
    actual: str | None = None
    
    def __repr__(self) -> str:
        loc = ""
        if self.segment_id:
            loc = f" at {self.segment_id}"
            if self.element_index:
                loc += f"[{self.element_index}]"
        return f"ValidationResult({self.severity.name}: {self.message}{loc})"


@dataclass
class ValidationRule:
    """A validation rule definition."""
    rule_id: str
    description: str
    validator: Callable[..., bool]
    severity: ValidationSeverity = ValidationSeverity.ERROR
    category: ValidationCategory = ValidationCategory.SYNTAX


@dataclass
class ValidationReport:
    """Complete validation report.
    
    Attributes:
        is_valid: True if no errors.
        errors: List of error results.
        warnings: List of warning results.
        results: All results.
    """
    results: list[ValidationResult] = field(default_factory=list)
    _errors: list[ValidationResult] = field(default_factory=list)
    _warnings: list[ValidationResult] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """True if no errors."""
        return self.error_count == 0
    
    @property
    def errors(self) -> list[ValidationResult]:
        """Get all error results."""
        # Always return the backing list - allows direct modification
        # On first access, populate from results if empty
        if not self._errors and self.results:
            self._errors = [r for r in self.results if r.severity == ValidationSeverity.ERROR]
        return self._errors
    
    @errors.setter
    def errors(self, value: list[ValidationResult]) -> None:
        """Set errors list directly."""
        self._errors = value
    
    @property
    def warnings(self) -> list[ValidationResult]:
        """Get all warning results."""
        if not self._warnings and self.results:
            self._warnings = [r for r in self.results if r.severity == ValidationSeverity.WARNING]
        return self._warnings
    
    @warnings.setter
    def warnings(self, value: list[ValidationResult]) -> None:
        """Set warnings list directly."""
        self._warnings = value
    
    @property
    def error_count(self) -> int:
        """Number of errors."""
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        """Number of warnings."""
        return len(self.warnings)
    
    def add_error(
        self, 
        rule_id: str, 
        message: str,
        category: ValidationCategory = ValidationCategory.SYNTAX,
        **kwargs,
    ) -> None:
        """Add an error result."""
        self.results.append(ValidationResult(
            rule_id=rule_id,
            message=message,
            severity=ValidationSeverity.ERROR,
            category=category,
            **kwargs,
        ))
    
    def add_warning(
        self,
        rule_id: str,
        message: str,
        category: ValidationCategory = ValidationCategory.SYNTAX,
        **kwargs,
    ) -> None:
        """Add a warning result."""
        self.results.append(ValidationResult(
            rule_id=rule_id,
            message=message,
            severity=ValidationSeverity.WARNING,
            category=category,
            **kwargs,
        ))


class X12Validator:
    """X12 EDI Validator.
    
    Performs multi-level validation of X12 content.
    
    Example:
        >>> validator = X12Validator()
        >>> report = validator.validate(edi_content)
        >>> if not report.is_valid:
        ...     for error in report.errors:
        ...         print(error)
    """
    
    def __init__(
        self, 
        strict: bool = False,
        custom_rules: list[ValidationRule] | None = None,
    ) -> None:
        """Initialize validator.
        
        Args:
            strict: If True, treat warnings as errors.
            custom_rules: Additional validation rules.
        """
        self.strict = strict
        self.custom_rules = custom_rules or []
    
    def validate(
        self, 
        content: str, 
        version: str | None = None,
    ) -> ValidationReport:
        """Validate EDI content.
        
        Args:
            content: Raw EDI string.
            version: Implementation version for validation.
        
        Returns:
            ValidationReport with all results.
        """
        report = ValidationReport()
        
        if not content or not content.strip():
            report.add_error("EMPTY_CONTENT", "Content is empty")
            return report
        
        content = content.strip()
        
        # Check for ISA
        if not content.startswith("ISA"):
            report.add_error(
                "MISSING_ISA",
                "EDI content must start with ISA segment",
                category=ValidationCategory.STRUCTURE,
            )
            return report
        
        # Parse and validate structure
        from x12.core.parser import SegmentParser
        from x12.core.delimiters import Delimiters
        
        try:
            delimiters = Delimiters.from_isa(content)
        except ValueError as e:
            report.add_error("INVALID_ISA", str(e))
            return report
        
        parser = SegmentParser(delimiters=delimiters)
        segments = list(parser.parse(content))
        
        # Validate envelope structure
        self._validate_envelope(segments, report)
        
        # Validate control number matching
        self._validate_control_numbers(segments, report)
        
        # Validate segment counts
        self._validate_segment_counts(segments, report)
        
        # Validate transaction-specific requirements
        self._validate_transaction_requirements(segments, report, version)
        
        return report
    
    def validate_segment(
        self,
        segment_str: str,
        segment_id: str,
        version: str | None = None,
    ) -> ValidationReport:
        """Validate a single segment.
        
        Args:
            segment_str: Raw segment string.
            segment_id: Expected segment ID.
            version: Implementation version.
        
        Returns:
            ValidationReport for this segment.
        """
        report = ValidationReport()
        
        from x12.core.parser import SegmentParser
        from x12.core.delimiters import Delimiters
        
        delimiters = Delimiters()
        parser = SegmentParser(delimiters=delimiters)
        
        segments = list(parser.parse(segment_str))
        if not segments:
            report.add_error("EMPTY_SEGMENT", "No segment found")
            return report
        
        segment = segments[0]
        
        # Validate based on segment type
        if segment.segment_id == "NM1":
            self._validate_nm1(segment, report, version)
        elif segment.segment_id == "DTP":
            self._validate_dtp(segment, report, version)
        elif segment.segment_id == "CLM":
            self._validate_clm(segment, report, version)
        elif segment.segment_id == "HI":
            self._validate_hi(segment, report, version)
        elif segment.segment_id == "SV1":
            self._validate_sv1(segment, report, version)
        elif segment.segment_id == "BEG":
            self._validate_beg(segment, report, version)
        elif segment.segment_id == "PO1":
            self._validate_po1(segment, report, version)
        elif segment.segment_id == "REF":
            self._validate_ref(segment, report, version)
        
        return report
    
    def validate_transaction(
        self,
        transaction: "TransactionSet",
        version: str | None = None,
    ) -> ValidationReport:
        """Validate a transaction set.
        
        Args:
            transaction: Parsed transaction.
            version: Implementation version.
        
        Returns:
            ValidationReport for this transaction.
        """
        report = ValidationReport()
        
        # Check for required segments based on transaction type
        if transaction.transaction_set_id == "837":
            self._validate_837_structure(transaction, report, version)
        elif transaction.transaction_set_id == "850":
            self._validate_850_structure(transaction, report, version)
        
        return report
    
    def _validate_envelope(
        self, 
        segments: list, 
        report: ValidationReport,
    ) -> None:
        """Validate ISA/IEA, GS/GE, ST/SE structure."""
        seg_ids = [s.segment_id for s in segments]
        
        # Check ISA/IEA
        if "ISA" not in seg_ids:
            report.add_error("MISSING_ISA", "ISA segment required")
        if "IEA" not in seg_ids:
            report.add_error("MISSING_IEA", "IEA segment required")
        
        # Check GS/GE
        gs_count = seg_ids.count("GS")
        ge_count = seg_ids.count("GE")
        if gs_count != ge_count:
            report.add_error(
                "GS_GE_MISMATCH",
                f"GS count ({gs_count}) != GE count ({ge_count})",
                category=ValidationCategory.STRUCTURE,
            )
        
        # Check ST/SE
        st_count = seg_ids.count("ST")
        se_count = seg_ids.count("SE")
        if st_count != se_count:
            report.add_error(
                "ST_SE_MISMATCH",
                f"ST count ({st_count}) != SE count ({se_count})",
                category=ValidationCategory.STRUCTURE,
            )
    
    def _validate_control_numbers(
        self,
        segments: list,
        report: ValidationReport,
    ) -> None:
        """Validate control number matching."""
        st_segments = [s for s in segments if s.segment_id == "ST"]
        se_segments = [s for s in segments if s.segment_id == "SE"]
        
        for st, se in zip(st_segments, se_segments):
            st_ctrl = st[2].value if st[2] else ""
            se_ctrl = se[2].value if se[2] else ""
            
            if st_ctrl != se_ctrl:
                report.add_error(
                    "CTRL_NUM_MISMATCH",
                    f"ST/SE control number mismatch: ST={st_ctrl}, SE={se_ctrl}",
                    category=ValidationCategory.STRUCTURE,
                )
        
        # GS/GE control numbers
        gs_segments = [s for s in segments if s.segment_id == "GS"]
        ge_segments = [s for s in segments if s.segment_id == "GE"]
        
        for gs, ge in zip(gs_segments, ge_segments):
            gs_ctrl = gs[6].value if gs[6] else ""
            ge_ctrl = ge[2].value if ge[2] else ""
            
            if gs_ctrl != ge_ctrl:
                report.add_error(
                    "GS_GE_CTRL_MISMATCH",
                    f"GS/GE control number mismatch: GS={gs_ctrl}, GE={ge_ctrl}",
                    category=ValidationCategory.STRUCTURE,
                )
    
    def _validate_segment_counts(
        self,
        segments: list,
        report: ValidationReport,
    ) -> None:
        """Validate SE01 segment counts."""
        # Find ST/SE pairs and count segments between them
        st_positions = [i for i, s in enumerate(segments) if s.segment_id == "ST"]
        se_positions = [i for i, s in enumerate(segments) if s.segment_id == "SE"]
        
        for st_pos, se_pos in zip(st_positions, se_positions):
            # Count includes ST and SE
            actual_count = se_pos - st_pos + 1
            se_seg = segments[se_pos]
            declared_count = se_seg[1].as_int() if se_seg[1] else 0
            
            if actual_count != declared_count:
                report.add_error(
                    "SEGMENT_COUNT_MISMATCH",
                    f"Segment count mismatch: SE01 declares {declared_count}, found {actual_count}",
                    category=ValidationCategory.STRUCTURE,
                )
    
    def _validate_nm1(
        self,
        segment,
        report: ValidationReport,
        version: str | None,
    ) -> None:
        """Validate NM1 segment."""
        # NM103 (name) required for most entity types
        entity_code = segment[1].value if segment[1] else ""
        name = segment[3].value if segment[3] else ""
        
        if entity_code in ("85", "IL", "QC", "PR") and not name:
            report.add_error(
                "NM1_NAME_REQUIRED",
                f"NM103 (name) required for entity {entity_code}",
                segment_id="NM1",
                element_index=3,
                category=ValidationCategory.ELEMENT,
            )
        
        # Check name length
        if name and len(name) > 60:
            report.add_error(
                "NM1_NAME_TOO_LONG",
                f"NM103 exceeds max length 60: {len(name)}",
                segment_id="NM1",
                element_index=3,
                category=ValidationCategory.ELEMENT,
            )
        
        # NM108/09 validation
        id_qualifier = segment[8].value if segment[8] else ""
        id_value = segment[9].value if segment[9] else ""
        
        if id_value and not id_qualifier:
            report.add_error(
                "NM1_ID_REQUIRES_QUALIFIER",
                "NM109 (ID) present but NM108 (qualifier) missing",
                segment_id="NM1",
                element_index=8,
                category=ValidationCategory.SEMANTIC,
            )
        
        # Check if qualifier position contains an ID-like value (misplaced ID)
        if id_qualifier and len(id_qualifier) > 3 and id_qualifier.isdigit():
            report.add_warning(
                "NM1_POSSIBLE_MISPLACED_ID",
                f"NM108 contains numeric value that looks like ID: {id_qualifier}",
                segment_id="NM1",
                element_index=8,
                category=ValidationCategory.SEMANTIC,
            )
        
        # NPI validation
        if id_qualifier == "XX" and id_value:
            if not self._validate_npi(id_value):
                report.add_error(
                    "NM1_INVALID_NPI",
                    f"Invalid NPI: {id_value}",
                    segment_id="NM1",
                    element_index=9,
                    category=ValidationCategory.HIPAA,
                )
    
    def _validate_npi(self, npi: str) -> bool:
        """Validate NPI using Luhn algorithm.
        
        NPI is a 10-digit number. For validation, prefix with 80840
        and apply Luhn check (ISO/IEC 7812).
        """
        if not npi or len(npi) != 10:
            return False
        if not npi.isdigit():
            return False
        
        # NPI Luhn check: prefix with 80840, then standard Luhn
        # The check digit is already included in the NPI
        prefixed = "80840" + npi[:9]  # Without check digit
        
        total = 0
        for i, digit in enumerate(reversed(prefixed)):
            d = int(digit)
            if i % 2 == 0:  # Even positions from right (0-indexed)
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        
        # Check digit should make (total + check) % 10 == 0
        check_digit = int(npi[9])
        return (total + check_digit) % 10 == 0
    
    def _validate_dtp(
        self,
        segment,
        report: ValidationReport,
        version: str | None,
    ) -> None:
        """Validate DTP segment."""
        qualifier = segment[1].value if segment[1] else ""  # DTP01 - Qualifier
        format_qualifier = segment[2].value if segment[2] else ""  # DTP02 - Format
        date_value = segment[3].value if segment[3] else ""  # DTP03 - Value
        
        # Validate date format qualifier D8 for 8-char dates
        if format_qualifier == "D8":
            if date_value and not self._is_valid_date(date_value):
                report.add_error(
                    "DTP_INVALID_DATE",
                    f"Invalid date format: {date_value}",
                    segment_id="DTP",
                    element_index=3,
                    category=ValidationCategory.ELEMENT,
                )
        elif date_value and len(date_value) == 8:
            # 8-char date should use D8 qualifier
            if not format_qualifier:
                report.add_error(
                    "DTP_QUALIFIER_MISSING",
                    "DTP02 date format qualifier required (D8 for 8-char date)",
                    segment_id="DTP",
                    element_index=2,
                    category=ValidationCategory.ELEMENT,
                )
            else:
                report.add_warning(
                    "DTP_QUALIFIER_MISMATCH",
                    f"8-character date should use D8 qualifier, found: {format_qualifier}",
                    segment_id="DTP",
                    element_index=2,
                    category=ValidationCategory.ELEMENT,
                )
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is valid CCYYMMDD."""
        if len(date_str) != 8:
            return False
        try:
            datetime.strptime(date_str, "%Y%m%d")
            return True
        except ValueError:
            return False
    
    def _validate_clm(
        self,
        segment,
        report: ValidationReport,
        version: str | None,
    ) -> None:
        """Validate CLM segment."""
        # CLM01 - Claim ID required
        claim_id = segment[1].value if segment[1] else ""
        if not claim_id:
            report.add_error(
                "CLM_ID_REQUIRED",
                "CLM01 claim ID required",
                segment_id="CLM",
                element_index=1,
                category=ValidationCategory.ELEMENT,
            )
        
        # CLM02 - Total charge required
        charge = segment[2].value if segment[2] else ""
        if not charge:
            report.add_error(
                "CLM_CHARGE_REQUIRED",
                "CLM02 total charge required",
                segment_id="CLM",
                element_index=2,
                category=ValidationCategory.ELEMENT,
            )
        elif charge:
            try:
                float(charge)
            except ValueError:
                report.add_error(
                    "CLM_INVALID_CHARGE",
                    f"CLM02 must be numeric: {charge}",
                    segment_id="CLM",
                    element_index=2,
                    category=ValidationCategory.ELEMENT,
                )
        
        # CLM05 - Facility code composite required for HIPAA
        facility = segment[5].value if segment[5] else ""
        if not facility:
            report.add_error(
                "CLM_FACILITY_REQUIRED",
                "CLM05 facility code required for HIPAA",
                segment_id="CLM",
                element_index=5,
                category=ValidationCategory.HIPAA,
            )
    
    def _validate_hi(
        self,
        segment,
        report: ValidationReport,
        version: str | None,
    ) -> None:
        """Validate HI (diagnosis) segment."""
        if segment[1]:
            elem = segment[1]
            if hasattr(elem, 'components') and elem.components:
                qualifier = elem.components[0].value if elem.components else ""
                if qualifier not in ("ABK", "ABF", "ABJ", "ABN", "APR", "BK", "BF"):
                    report.add_warning(
                        "HI_INVALID_QUALIFIER",
                        f"HI qualifier may be invalid: {qualifier}",
                        segment_id="HI",
                        element_index=1,
                        category=ValidationCategory.ELEMENT,
                    )
    
    def _validate_sv1(
        self,
        segment,
        report: ValidationReport,
        version: str | None,
    ) -> None:
        """Validate SV1 segment."""
        # SV101 - procedure code required
        proc = segment[1]
        if not proc or (hasattr(proc, 'value') and not proc.value):
            report.add_error(
                "SV1_PROC_REQUIRED",
                "SV101 procedure code required",
                segment_id="SV1",
                element_index=1,
                category=ValidationCategory.ELEMENT,
            )
        
        # SV102 - charge required
        charge = segment[2].value if segment[2] else ""
        if not charge:
            report.add_error(
                "SV1_CHARGE_REQUIRED",
                "SV102 charge amount required",
                segment_id="SV1",
                element_index=2,
                category=ValidationCategory.ELEMENT,
            )
        
        # SV104 - units required for HIPAA
        units = segment[4].value if segment[4] else ""
        if not units:
            report.add_warning(
                "SV1_UNITS_RECOMMENDED",
                "SV104 units recommended for HIPAA compliance",
                segment_id="SV1",
                element_index=4,
                category=ValidationCategory.HIPAA,
            )
    
    def _validate_beg(
        self,
        segment,
        report: ValidationReport,
        version: str | None,
    ) -> None:
        """Validate BEG segment."""
        po_number = segment[3].value if segment[3] else ""
        if not po_number:
            report.add_error(
                "BEG_PO_REQUIRED",
                "BEG03 PO number required",
                segment_id="BEG",
                element_index=3,
                category=ValidationCategory.ELEMENT,
            )
    
    def _validate_po1(
        self,
        segment,
        report: ValidationReport,
        version: str | None,
    ) -> None:
        """Validate PO1 segment."""
        quantity = segment[2].value if segment[2] else ""
        if not quantity:
            report.add_warning(
                "PO1_QTY_RECOMMENDED",
                "PO102 quantity recommended",
                segment_id="PO1",
                element_index=2,
                category=ValidationCategory.ELEMENT,
            )
    
    def _validate_ref(
        self,
        segment,
        report: ValidationReport,
        version: str | None,
    ) -> None:
        """Validate REF segment."""
        qualifier = segment[1].value if segment[1] else ""
        value = segment[2].value if segment[2] else ""
        
        # EIN validation
        if qualifier == "EI" and value:
            if len(value) != 9 or not value.isdigit():
                report.add_error(
                    "REF_INVALID_EIN",
                    f"Invalid EIN (must be 9 digits): {value}",
                    segment_id="REF",
                    element_index=2,
                    category=ValidationCategory.HIPAA,
                )
    
    def _validate_transaction_requirements(
        self,
        segments: list,
        report: ValidationReport,
        version: str | None,
    ) -> None:
        """Validate transaction-specific requirements."""
        # Find transaction type from ST segment
        st_seg = next((s for s in segments if s.segment_id == "ST"), None)
        if not st_seg:
            return
        
        txn_type = st_seg[1].value if st_seg[1] else ""
        seg_ids = [s.segment_id for s in segments]
        
        if txn_type == "837":
            # 837 requires BHT
            if "BHT" not in seg_ids:
                report.add_error(
                    "837_MISSING_BHT",
                    "BHT segment required in 837 transaction",
                    category=ValidationCategory.STRUCTURE,
                )
        elif txn_type == "850":
            # 850 requires BEG
            if "BEG" not in seg_ids:
                report.add_error(
                    "850_MISSING_BEG",
                    "BEG segment required in 850 transaction",
                    category=ValidationCategory.STRUCTURE,
                )
    
    def _validate_837_structure(
        self,
        transaction: "TransactionSet",
        report: ValidationReport,
        version: str | None,
    ) -> None:
        """Validate 837 transaction structure."""
        root = transaction.root_loop
        
        # Check for BHT
        if not root.has_segment("BHT"):
            has_bht = False
            for loop in root.loops:
                if loop.has_segment("BHT"):
                    has_bht = True
                    break
            if not has_bht:
                report.add_error(
                    "837_MISSING_BHT",
                    "BHT segment required in 837",
                    category=ValidationCategory.STRUCTURE,
                )
    
    def _validate_850_structure(
        self,
        transaction: "TransactionSet",
        report: ValidationReport,
        version: str | None,
    ) -> None:
        """Validate 850 transaction structure."""
        root = transaction.root_loop
        
        # Check for BEG
        if not root.has_segment("BEG"):
            report.add_error(
                "850_MISSING_BEG",
                "BEG segment required in 850",
                category=ValidationCategory.STRUCTURE,
            )
