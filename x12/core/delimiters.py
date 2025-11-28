"""
Delimiter detection and handling for X12 EDI.

ISA segment structure (always 106 characters):
- Position 3: Element separator
- Position 104: Component separator  
- Position 105: Segment terminator
"""
from __future__ import annotations

import re
import string
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class Delimiters:
    """X12 delimiter configuration.
    
    Immutable container for the four X12 delimiters extracted from
    the ISA segment or configured manually.
    
    Attributes:
        element: Element separator (default: *)
        segment: Segment terminator (default: ~)
        component: Component separator (default: :)
        repetition: Repetition separator (default: ^)
    
    Example:
        >>> d = Delimiters()
        >>> d.element
        '*'
        >>> d = Delimiters.from_isa(isa_content)
        >>> d.segment
        '~'
    """
    
    element: str = "*"
    segment: str = "~"
    component: str = ":"
    repetition: str = "^"
    
    # Characters that cannot be delimiters (alphanumeric)
    _INVALID_CHARS: ClassVar[set[str]] = set(string.ascii_letters + string.digits)
    
    def __post_init__(self) -> None:
        """Validate delimiter configuration."""
        self._validate_delimiters()
    
    def _validate_delimiters(self) -> None:
        """Ensure all delimiters are valid and distinct."""
        delims = [self.element, self.segment, self.component, self.repetition]
        names = ["element", "segment", "component", "repetition"]
        
        # Check each delimiter is a single character (except segment can be \r\n)
        for i, d in enumerate(delims):
            # Segment terminator can be \r\n for legacy systems
            if names[i] == "segment" and d == "\r\n":
                continue
            if len(d) != 1:
                raise ValueError(f"{names[i]} delimiter must be a single character, got {len(d)}")
            
            # Check not alphanumeric (only for single-char delimiters)
            if len(d) == 1 and d in self._INVALID_CHARS:
                raise ValueError(f"{names[i]} delimiter cannot be alphanumeric: {d!r}")
        
        # Check all distinct
        if len(set(delims)) != 4:
            raise ValueError("All delimiters must be distinct characters")
    
    @classmethod
    def from_isa(cls, content: str) -> "Delimiters":
        """Extract delimiters from ISA segment.
        
        The ISA segment is always exactly 106 characters with delimiters
        at fixed positions:
        - Position 3 (index 3): Element separator
        - Position 104 (index 104): Component separator
        - Position 105 (index 105): Segment terminator
        
        Args:
            content: EDI content starting with (or containing) ISA segment.
        
        Returns:
            Delimiters extracted from the ISA segment.
        
        Raises:
            ValueError: If ISA segment is invalid or too short.
        
        Example:
            >>> isa = "ISA*00*..."  # 106 chars
            >>> d = Delimiters.from_isa(isa)
            >>> d.element
            '*'
        """
        if not content:
            raise ValueError("Content is empty")
        
        # Find ISA position
        isa_pos = content.find("ISA")
        if isa_pos == -1:
            raise ValueError("ISA segment not found")
        
        # Extract ISA segment (106 characters from ISA position)
        isa_content = content[isa_pos:]
        
        if len(isa_content) < 106:
            raise ValueError(
                f"ISA segment too short: expected 106 characters, got {len(isa_content)}"
            )
        
        # Extract delimiters from fixed positions
        element = isa_content[3]  # Position 3 (after "ISA")
        segment = isa_content[105]  # Position 105
        component = isa_content[104]  # Position 104
        
        # Repetition separator is in ISA11 (element 11)
        # We need to parse ISA to find it, using the element separator we just found
        isa_elements = isa_content[:106].split(element)
        if len(isa_elements) >= 12:
            repetition = isa_elements[11]  # ISA11
        else:
            repetition = "^"  # Default if not found
        
        return cls(
            element=element,
            segment=segment,
            component=component,
            repetition=repetition if len(repetition) == 1 else "^",
        )
    
    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"Delimiters(element={self.element!r}, segment={self.segment!r}, "
            f"component={self.component!r}, repetition={self.repetition!r})"
        )
