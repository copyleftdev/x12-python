"""
Loop model for X12 EDI hierarchical structure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from x12.models.segment import Segment


@dataclass
class Loop:
    """A hierarchical loop containing segments and child loops.
    
    Attributes:
        loop_id: Identifier for this loop (e.g., "2000A", "2010AA").
        segments: Segments directly in this loop.
        loops: Child loops.
    """
    loop_id: str
    segments: list["Segment"] = field(default_factory=list)
    loops: list["Loop"] = field(default_factory=list)
    
    def get_segment(self, segment_id: str) -> "Segment | None":
        """Get first segment with given ID."""
        for seg in self.segments:
            if seg.segment_id == segment_id:
                return seg
        return None
    
    def get_segments(self, segment_id: str) -> list["Segment"]:
        """Get all segments with given ID."""
        return [seg for seg in self.segments if seg.segment_id == segment_id]
    
    def get_loop(self, loop_id: str) -> "Loop | None":
        """Get first child loop with given ID."""
        for loop in self.loops:
            if loop.loop_id == loop_id:
                return loop
        return None
    
    def get_loops(self, loop_id: str) -> list["Loop"]:
        """Get all child loops with given ID."""
        return [loop for loop in self.loops if loop.loop_id == loop_id]
    
    def get_loop_by_path(self, path: str) -> "Loop | None":
        """Get loop by path (e.g., '2000A/2010AA').
        
        Args:
            path: Slash-separated loop path.
        
        Returns:
            Loop if found, None otherwise.
        """
        parts = path.split("/")
        current: Loop | None = self
        
        for part in parts:
            if current is None:
                return None
            current = current.get_loop(part)
        
        return current
    
    def has_segment(self, segment_id: str) -> bool:
        """Check if loop contains segment with given ID."""
        return any(seg.segment_id == segment_id for seg in self.segments)
    
    @property
    def children(self) -> list["Loop"]:
        """Alias for loops property."""
        return self.loops
    
    def __repr__(self) -> str:
        return f"Loop({self.loop_id}, {len(self.segments)} segs, {len(self.loops)} loops)"
