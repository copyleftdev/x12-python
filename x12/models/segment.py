"""
Segment and Element models for X12 EDI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from x12.core.delimiters import Delimiters


@dataclass(frozen=True, slots=True)
class Component:
    """A component within a composite element.
    
    Attributes:
        value: The component's string value.
        index: Position within composite (0-indexed).
    """
    value: str
    index: int
    
    def __repr__(self) -> str:
        return f"Component({self.index}={self.value!r})"


@dataclass(frozen=True, slots=True)
class Element:
    """A simple (non-composite) X12 element.
    
    Attributes:
        value: The element's string value.
        index: Position within segment (1-indexed).
    """
    value: str
    index: int
    is_composite: bool = False
    
    def as_str(self) -> str:
        """Return value as string."""
        return self.value
    
    def as_int(self) -> int:
        """Return value as integer, 0 if empty or invalid."""
        if not self.value:
            return 0
        try:
            return int(self.value)
        except ValueError:
            return 0
    
    def as_decimal(self) -> Decimal:
        """Return value as Decimal, 0 if empty or invalid."""
        if not self.value:
            return Decimal(0)
        try:
            return Decimal(self.value)
        except InvalidOperation:
            return Decimal(0)
    
    def as_date(self) -> date | None:
        """Parse value as date (CCYYMMDD or YYMMDD format)."""
        if not self.value:
            return None
        
        try:
            if len(self.value) == 8:
                # CCYYMMDD format
                return datetime.strptime(self.value, "%Y%m%d").date()
            elif len(self.value) == 6:
                # YYMMDD format - assume 2000s for years < 50, 1900s otherwise
                year = int(self.value[:2])
                if year < 50:
                    year += 2000
                else:
                    year += 1900
                month = int(self.value[2:4])
                day = int(self.value[4:6])
                return date(year, month, day)
        except (ValueError, TypeError):
            return None
        
        return None
    
    def component(self, index: int) -> Component | None:
        """Get component by index (for non-composite, returns None)."""
        return None
    
    @property
    def components(self) -> list[Component]:
        """Get all components (empty for non-composite)."""
        return []
    
    def __repr__(self) -> str:
        return f"Element({self.index}={self.value!r})"


@dataclass(frozen=True, slots=True)
class CompositeElement:
    """A composite X12 element containing multiple components.
    
    Attributes:
        index: Position within segment (1-indexed).
        components: List of components.
    """
    index: int
    components: tuple[Component, ...] = field(default_factory=tuple)
    is_composite: bool = True
    
    @property
    def value(self) -> str:
        """Get combined value of all components."""
        return ":".join(c.value for c in self.components)
    
    def component(self, index: int) -> Component | None:
        """Get component by index (0-indexed)."""
        if 0 <= index < len(self.components):
            return self.components[index]
        return None
    
    def as_str(self) -> str:
        """Return combined value as string."""
        return self.value
    
    def as_int(self) -> int:
        """Return first component as integer."""
        if self.components:
            try:
                return int(self.components[0].value)
            except ValueError:
                pass
        return 0
    
    def as_decimal(self) -> Decimal:
        """Return first component as Decimal."""
        if self.components:
            try:
                return Decimal(self.components[0].value)
            except InvalidOperation:
                pass
        return Decimal(0)
    
    def as_date(self) -> date | None:
        """Parse first component as date."""
        if self.components:
            elem = Element(value=self.components[0].value, index=0)
            return elem.as_date()
        return None
    
    def __repr__(self) -> str:
        return f"CompositeElement({self.index}={self.value!r})"


@dataclass(frozen=True, slots=True) 
class Segment:
    """An X12 segment containing elements.
    
    Attributes:
        segment_id: The segment identifier (e.g., "NM1", "CLM").
        elements: List of elements in the segment.
        position: Byte position in source (optional).
    """
    segment_id: str
    elements: tuple[Element | CompositeElement, ...] = field(default_factory=tuple)
    position: int = 0
    
    def __getitem__(self, index: int) -> Element | CompositeElement | None:
        """Get element by 1-based index."""
        if index < 1:
            return None
        # Elements are stored 0-indexed but accessed 1-indexed
        actual_index = index - 1
        if 0 <= actual_index < len(self.elements):
            return self.elements[actual_index]
        return None
    
    def element(self, index: int) -> Element | CompositeElement | None:
        """Get element by 1-based index."""
        return self[index]
    
    def get_segment(self, segment_id: str) -> "Segment | None":
        """For API compatibility - segments don't contain other segments."""
        return None
    
    def to_edi(self, delimiters: "Delimiters") -> str:
        """Serialize segment to EDI string.
        
        Args:
            delimiters: Delimiter configuration to use.
        
        Returns:
            EDI string representation of the segment.
        """
        parts = [self.segment_id]
        
        for elem in self.elements:
            if isinstance(elem, CompositeElement):
                comp_values = [c.value for c in elem.components]
                parts.append(delimiters.component.join(comp_values))
            else:
                parts.append(elem.value)
        
        return delimiters.element.join(parts) + delimiters.segment
    
    def __repr__(self) -> str:
        elem_count = len(self.elements)
        return f"Segment({self.segment_id}, {elem_count} elements)"
