"""
X12 Schema definition classes.

Defines the structure of X12 segments, elements, and loops.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from x12.models import Segment


@dataclass
class ValidationResult:
    """Result of schema validation."""

    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ElementDefinition:
    """Definition of an X12 element within a segment.

    Attributes:
        position: 1-indexed position in segment.
        name: Human-readable element name.
        data_type: X12 data type (ID, AN, N0, N2, DT, TM, etc.).
        min_length: Minimum length.
        max_length: Maximum length.
        required: Whether element is required.
        valid_values: Optional list of valid values for ID types.
    """

    position: int
    name: str
    data_type: str = "AN"
    min_length: int = 1
    max_length: int = 80
    required: bool = False
    valid_values: list[str] = field(default_factory=list)

    def validate_value(self, value: str) -> bool:
        """Validate a value against this element definition.

        Args:
            value: The value to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not value:
            return not self.required

        # Check length
        if len(value) < self.min_length or len(value) > self.max_length:
            return False

        # Check valid values if specified
        if self.valid_values and value not in self.valid_values:
            return False

        # Check data type
        if self.data_type.startswith("N"):
            # Numeric types
            try:
                float(value.replace("-", "").replace(".", ""))
                if not value.replace("-", "").replace(".", "").isdigit():
                    return False
            except ValueError:
                return False

        elif self.data_type == "DT":
            # Date type - CCYYMMDD
            if len(value) != 8:
                return False
            try:
                datetime.strptime(value, "%Y%m%d")
            except ValueError:
                return False

        elif self.data_type == "TM":
            # Time type - HHMM or HHMMSS
            if len(value) not in (4, 6, 8):
                return False
            if not value.isdigit():
                return False

        return True


@dataclass
class SegmentDefinition:
    """Definition of an X12 segment.

    Attributes:
        segment_id: 2-3 character segment identifier.
        name: Human-readable segment name.
        elements: List of element definitions.
        required: Whether segment is required in its context.
    """

    segment_id: str
    name: str
    elements: list[ElementDefinition] = field(default_factory=list)
    required: bool = False

    def get_element(self, position: int) -> ElementDefinition | None:
        """Get element definition by position."""
        for elem in self.elements:
            if elem.position == position:
                return elem
        return None


@dataclass
class LoopDefinition:
    """Definition of an X12 loop structure.

    Attributes:
        loop_id: Loop identifier (e.g., "2000A", "2010AA").
        name: Human-readable loop name.
        segments: List of segment IDs allowed in this loop.
        child_loops: List of child loop IDs.
        min_occurs: Minimum occurrences.
        max_occurs: Maximum occurrences (None = unbounded).
    """

    loop_id: str
    name: str
    segments: list[str] = field(default_factory=list)
    child_loops: list[str] = field(default_factory=list)
    min_occurs: int = 0
    max_occurs: int | None = None


@dataclass
class TransactionSchema:
    """Complete schema for an X12 transaction set.

    Attributes:
        version: Implementation guide version (e.g., "005010X222A1").
        transaction_set_id: Transaction type (e.g., "837", "835").
        name: Human-readable transaction name.
        functional_group_id: Functional group identifier (e.g., "HC", "HP").
        segment_definitions: Dictionary of segment definitions.
        loop_definitions: Dictionary of loop definitions.
    """

    version: str
    transaction_set_id: str
    name: str
    functional_group_id: str
    segment_definitions: dict[str, SegmentDefinition] = field(default_factory=dict)
    loop_definitions: dict[str, LoopDefinition] = field(default_factory=dict)

    def get_segment_definition(self, segment_id: str) -> SegmentDefinition | None:
        """Get segment definition by ID."""
        return self.segment_definitions.get(segment_id)

    def get_loop_definition(self, loop_id: str) -> LoopDefinition | None:
        """Get loop definition by ID."""
        return self.loop_definitions.get(loop_id)

    def validate_segment(self, segment: Segment) -> ValidationResult:
        """Validate a segment against this schema.

        Args:
            segment: The segment to validate.

        Returns:
            ValidationResult with is_valid and any errors.
        """
        result = ValidationResult()

        seg_def = self.get_segment_definition(segment.segment_id)
        if seg_def is None:
            # Unknown segment - might be valid, just not in schema
            return result

        # Validate each required element
        for elem_def in seg_def.elements:
            if elem_def.required:
                # Get element value
                elem = (
                    segment[elem_def.position]
                    if elem_def.position <= len(segment.elements)
                    else None
                )
                value = elem.value if elem else ""

                if not value:
                    result.is_valid = False
                    result.errors.append(
                        f"{segment.segment_id}{elem_def.position:02d} ({elem_def.name}) is required"
                    )
                elif not elem_def.validate_value(value):
                    result.is_valid = False
                    result.errors.append(
                        f"{segment.segment_id}{elem_def.position:02d} ({elem_def.name}) has invalid value: {value}"
                    )

        return result
