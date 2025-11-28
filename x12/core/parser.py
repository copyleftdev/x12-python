"""
X12 EDI Segment Parser.

Parses tokenized EDI content into Segment objects.
"""
from __future__ import annotations

from typing import Iterator, TYPE_CHECKING

from x12.core.delimiters import Delimiters
from x12.core.tokenizer import Tokenizer, TokenType
from x12.models.segment import Segment, Element, CompositeElement, Component

if TYPE_CHECKING:
    from x12.models import Loop, Interchange


class SegmentParser:
    """Parser that converts EDI content into Segment objects.
    
    Example:
        >>> parser = SegmentParser()
        >>> for segment in parser.parse("NM1*85*2*NAME~"):
        ...     print(segment.segment_id)
        NM1
    """
    
    def __init__(self, delimiters: Delimiters | None = None) -> None:
        """Initialize parser.
        
        Args:
            delimiters: Delimiter configuration. If None, auto-detects.
        """
        self._delimiters = delimiters
        self._tokenizer = Tokenizer(delimiters)
    
    def parse(self, content: str) -> Iterator[Segment]:
        """Parse EDI content into segments.
        
        Args:
            content: Raw EDI string.
        
        Yields:
            Segment objects.
        """
        if not content or not content.strip():
            return
        
        # Detect delimiters if needed
        delimiters = self._delimiters
        if delimiters is None:
            if content.strip().startswith("ISA") and len(content.strip()) >= 106:
                delimiters = Delimiters.from_isa(content)
            else:
                delimiters = Delimiters()
        
        # Parse using delimiters directly (more efficient than tokenizer for this)
        segments = self._split_segments(content, delimiters)
        position = 0
        
        for seg_str in segments:
            seg_str = seg_str.strip()
            if not seg_str:
                continue
            
            segment = self._parse_segment(seg_str, delimiters, position)
            if segment:
                yield segment
            
            position += len(seg_str) + len(delimiters.segment)
    
    def _split_segments(self, content: str, delimiters: Delimiters) -> list[str]:
        """Split content by segment terminator."""
        # Normalize line endings
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        
        if delimiters.segment == "\n":
            return content.split("\n")
        elif delimiters.segment == "\r\n":
            return content.split("\n")  # Already normalized
        else:
            return content.split(delimiters.segment)
    
    def _parse_segment(
        self, 
        seg_str: str, 
        delimiters: Delimiters,
        position: int = 0,
    ) -> Segment | None:
        """Parse a single segment string."""
        if not seg_str:
            return None
        
        parts = seg_str.split(delimiters.element)
        if not parts:
            return None
        
        segment_id = parts[0]
        elements: list[Element | CompositeElement] = []
        
        for idx, part in enumerate(parts[1:], start=1):
            if delimiters.component in part:
                # Composite element
                comp_parts = part.split(delimiters.component)
                components = tuple(
                    Component(value=v, index=i) 
                    for i, v in enumerate(comp_parts)
                )
                elements.append(CompositeElement(index=idx, components=components))
            else:
                # Simple element
                elements.append(Element(value=part, index=idx))
        
        return Segment(
            segment_id=segment_id,
            elements=tuple(elements),
            position=position,
        )


class Parser:
    """Full X12 parser that builds hierarchical structure.
    
    Parses complete EDI content into Interchange/FunctionalGroup/TransactionSet
    structure with proper loop hierarchy.
    
    Example:
        >>> parser = Parser()
        >>> interchange = parser.parse(edi_content)
        >>> print(interchange.functional_groups[0].transactions[0])
    """
    
    def __init__(self) -> None:
        """Initialize parser."""
        self._segment_parser = SegmentParser()
    
    def parse(self, content: str) -> "Interchange":
        """Parse EDI content into full structure.
        
        Args:
            content: Raw EDI string.
        
        Returns:
            Interchange object with full hierarchy.
        """
        from x12.models import Interchange, FunctionalGroup, TransactionSet, Loop
        
        if not content or not content.strip():
            raise ValueError("Content is empty")
        
        # Detect delimiters
        delimiters = Delimiters.from_isa(content)
        
        # Parse all segments
        segments = list(self._segment_parser.parse(content))
        
        # Build structure
        interchange = self._build_interchange(segments, delimiters)
        
        return interchange
    
    def _build_interchange(
        self, 
        segments: list[Segment],
        delimiters: Delimiters,
    ) -> "Interchange":
        """Build Interchange from segments."""
        from x12.models import Interchange, FunctionalGroup, TransactionSet, Loop
        
        # Find ISA segment
        isa_seg = next((s for s in segments if s.segment_id == "ISA"), None)
        if not isa_seg:
            raise ValueError("ISA segment not found")
        
        interchange = Interchange(
            sender_id=isa_seg[6].value.strip() if isa_seg[6] else "",
            sender_qualifier=isa_seg[5].value if isa_seg[5] else "ZZ",
            receiver_id=isa_seg[8].value.strip() if isa_seg[8] else "",
            receiver_qualifier=isa_seg[7].value if isa_seg[7] else "ZZ",
            control_number=isa_seg[13].value if isa_seg[13] else "",
            version=isa_seg[12].value if isa_seg[12] else "00501",
            delimiters=delimiters,
        )
        
        # Group segments into functional groups and transactions
        current_fg: FunctionalGroup | None = None
        current_txn: TransactionSet | None = None
        current_segments: list[Segment] = []
        
        for seg in segments:
            if seg.segment_id == "ISA":
                continue  # Already processed
            elif seg.segment_id == "GS":
                # Start new functional group
                current_fg = FunctionalGroup(
                    functional_id_code=seg[1].value if seg[1] else "",
                    sender_code=seg[2].value if seg[2] else "",
                    receiver_code=seg[3].value if seg[3] else "",
                    control_number=seg[6].value if seg[6] else "",
                    version=seg[8].value if seg[8] else None,
                )
                interchange.functional_groups.append(current_fg)
            elif seg.segment_id == "ST":
                # Start new transaction
                root_loop = Loop(loop_id="ROOT")
                current_txn = TransactionSet(
                    transaction_set_id=seg[1].value if seg[1] else "",
                    control_number=seg[2].value if seg[2] else "",
                    root_loop=root_loop,
                    version=seg[3].value if seg[3] else None,
                )
                if current_fg:
                    current_fg.transactions.append(current_txn)
                current_segments = []
            elif seg.segment_id == "SE":
                # End transaction - build loops
                if current_txn:
                    self._build_loops(current_txn.root_loop, current_segments)
            elif seg.segment_id == "GE":
                current_fg = None
            elif seg.segment_id == "IEA":
                pass  # End of interchange
            else:
                # Regular segment
                current_segments.append(seg)
        
        return interchange
    
    def _build_loops(self, root_loop: "Loop", segments: list[Segment]) -> None:
        """Build loop hierarchy from segments."""
        from x12.models import Loop
        
        # Simple implementation - just add all segments to root
        # Full implementation would use schema to determine loop structure
        current_loop = root_loop
        hl_loops: dict[str, Loop] = {}
        
        for seg in segments:
            if seg.segment_id == "HL":
                # Hierarchical level segment
                hl_id = seg[1].value if seg[1] else ""
                parent_id = seg[2].value if seg[2] else ""
                level_code = seg[3].value if seg[3] else ""
                
                # Determine loop ID based on level code
                loop_id = self._get_loop_id_for_hl(level_code)
                
                new_loop = Loop(loop_id=loop_id)
                new_loop.segments.append(seg)
                hl_loops[hl_id] = new_loop
                
                if parent_id and parent_id in hl_loops:
                    hl_loops[parent_id].loops.append(new_loop)
                else:
                    root_loop.loops.append(new_loop)
                
                current_loop = new_loop
            else:
                current_loop.segments.append(seg)
    
    def _get_loop_id_for_hl(self, level_code: str) -> str:
        """Map HL level code to loop ID."""
        mapping = {
            "20": "2000A",  # Billing Provider
            "22": "2000B",  # Subscriber
            "23": "2000C",  # Patient
            "S": "SHIPMENT",
            "O": "ORDER",
            "I": "ITEM",
        }
        return mapping.get(level_code, f"HL_{level_code}")
