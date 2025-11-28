"""
X12 EDI Tokenizer.

Converts raw EDI content into a stream of tokens for parsing.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator

from x12.core.delimiters import Delimiters


class TokenType(Enum):
    """Types of tokens in X12 EDI."""
    
    SEGMENT_ID = auto()
    ELEMENT = auto()
    COMPONENT = auto()
    REPETITION = auto()
    SEGMENT_TERMINATOR = auto()


@dataclass(frozen=True, slots=True)
class Token:
    """A single token from X12 EDI content.
    
    Attributes:
        type: The type of token.
        value: The token's string value.
        position: Byte position in source content.
        line: Segment number (1-indexed).
        element_index: Element position within segment (1-indexed).
        component_index: Component position within element (0-indexed).
    """
    
    type: TokenType
    value: str
    position: int = 0
    line: int = 1
    element_index: int = 0
    component_index: int = 0
    
    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"


class Tokenizer:
    """Tokenizer for X12 EDI content.
    
    Converts raw EDI string into a stream of tokens. Supports automatic
    delimiter detection from ISA segment or explicit delimiter configuration.
    
    Attributes:
        delimiters: The delimiter configuration to use.
    
    Example:
        >>> tokenizer = Tokenizer()
        >>> for token in tokenizer.tokenize("ISA*00*..."):
        ...     print(token)
    """
    
    def __init__(self, delimiters: Delimiters | None = None) -> None:
        """Initialize tokenizer.
        
        Args:
            delimiters: Delimiter configuration. If None, will auto-detect
                       from ISA segment during tokenization.
        """
        self._delimiters = delimiters
    
    @property
    def delimiters(self) -> Delimiters | None:
        """Get current delimiter configuration."""
        return self._delimiters
    
    def tokenize(self, content: str) -> Iterator[Token]:
        """Tokenize EDI content into a stream of tokens.
        
        Args:
            content: Raw EDI content string.
        
        Yields:
            Token objects representing each piece of the EDI.
        
        Example:
            >>> tokenizer = Tokenizer()
            >>> tokens = list(tokenizer.tokenize("NM1*85*2*NAME~"))
            >>> tokens[0].type
            TokenType.SEGMENT_ID
        """
        if not content or not content.strip():
            return
        
        # Auto-detect delimiters if not set
        delimiters = self._delimiters
        if delimiters is None:
            if content.strip().startswith("ISA") and len(content) >= 106:
                delimiters = Delimiters.from_isa(content)
            else:
                delimiters = Delimiters()  # Use defaults
        
        # State tracking
        position = 0
        line = 1  # Segment number
        
        # Split into segments
        segments = self._split_segments(content, delimiters)
        
        for seg_content in segments:
            if not seg_content.strip():
                position += len(seg_content) + len(delimiters.segment)
                continue
            
            seg_content = seg_content.strip()
            
            # Split segment into elements
            elements = seg_content.split(delimiters.element)
            
            if not elements:
                position += len(seg_content) + len(delimiters.segment)
                continue
            
            # First element is segment ID
            segment_id = elements[0]
            yield Token(
                type=TokenType.SEGMENT_ID,
                value=segment_id,
                position=position,
                line=line,
                element_index=0,
            )
            
            # Process remaining elements
            elem_pos = position + len(segment_id)
            for elem_idx, elem_value in enumerate(elements[1:], start=1):
                elem_pos += len(delimiters.element)
                
                # Check for composite element
                if delimiters.component in elem_value:
                    # Composite element - yield components
                    components = elem_value.split(delimiters.component)
                    for comp_idx, comp_value in enumerate(components):
                        yield Token(
                            type=TokenType.COMPONENT,
                            value=comp_value,
                            position=elem_pos,
                            line=line,
                            element_index=elem_idx,
                            component_index=comp_idx,
                        )
                        elem_pos += len(comp_value) + (
                            len(delimiters.component) if comp_idx < len(components) - 1 else 0
                        )
                elif delimiters.repetition in elem_value:
                    # Repeated element
                    repetitions = elem_value.split(delimiters.repetition)
                    for rep_idx, rep_value in enumerate(repetitions):
                        yield Token(
                            type=TokenType.REPETITION if rep_idx > 0 else TokenType.ELEMENT,
                            value=rep_value,
                            position=elem_pos,
                            line=line,
                            element_index=elem_idx,
                        )
                        elem_pos += len(rep_value) + (
                            len(delimiters.repetition) if rep_idx < len(repetitions) - 1 else 0
                        )
                else:
                    # Simple element
                    yield Token(
                        type=TokenType.ELEMENT,
                        value=elem_value,
                        position=elem_pos,
                        line=line,
                        element_index=elem_idx,
                    )
                    elem_pos += len(elem_value)
            
            # Segment terminator
            yield Token(
                type=TokenType.SEGMENT_TERMINATOR,
                value=delimiters.segment,
                position=elem_pos,
                line=line,
            )
            
            position = elem_pos + len(delimiters.segment)
            line += 1
    
    def _split_segments(self, content: str, delimiters: Delimiters) -> list[str]:
        """Split content into segments using segment terminator."""
        # Handle Windows line endings in content
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        
        # Split by segment terminator
        if delimiters.segment == "\n":
            segments = content.split("\n")
        elif delimiters.segment == "\r\n":
            segments = content.replace("\n", "\r\n").split("\r\n")
        else:
            segments = content.split(delimiters.segment)
        
        return segments
