"""
Loop hierarchy builder for X12 EDI.

Constructs nested loop structure from flat segment lists.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from x12.models.loop import Loop

if TYPE_CHECKING:
    from x12.models.segment import Segment


class LoopBuilder:
    """Builds hierarchical loop structure from segments.

    Uses HL segments and schema definitions to determine loop nesting.

    Example:
        >>> builder = LoopBuilder(transaction_type="837")
        >>> root = builder.build(segments)
        >>> print(root.get_loop("2000A"))
    """

    # HL level code to loop ID mapping
    HL_LOOP_MAPPING = {
        # Healthcare 837
        "20": "2000A",  # Billing Provider
        "22": "2000B",  # Subscriber
        "23": "2000C",  # Patient/Dependent
        # Supply Chain 856
        "S": "SHIPMENT",
        "O": "ORDER",
        "P": "PACK",
        "I": "ITEM",
    }

    # NM1 entity codes that start sub-loops (837P)
    NM1_LOOP_MAPPING = {
        "85": "2010AA",  # Billing Provider Name
        "87": "2010AB",  # Pay-to Address
        "IL": "2010BA",  # Subscriber Name
        "PR": "2010BB",  # Payer Name
        "QC": "2010CA",  # Patient Name
        "82": "2310A",  # Rendering Provider
        "77": "2310C",  # Service Facility
    }

    def __init__(
        self,
        transaction_type: str | None = None,
        version: str | None = None,
        schema: object | None = None,
    ) -> None:
        """Initialize loop builder.

        Args:
            transaction_type: Transaction set ID (e.g., "837", "850").
            version: Implementation version (e.g., "005010X222A1").
            schema: Optional schema for loop determination.
        """
        self.transaction_type = transaction_type
        self.version = version
        self.schema = schema

    def build(self, segments: list[Segment]) -> Loop:
        """Build loop hierarchy from segments.

        Args:
            segments: Flat list of segments.

        Returns:
            Root loop containing hierarchical structure.
        """
        root = Loop(loop_id="ROOT")

        if not segments:
            return root

        # Track HL hierarchy
        hl_loops: dict[str, Loop] = {}
        current_loop = root
        current_2000_loop: Loop | None = None

        for seg in segments:
            if seg.segment_id == "HL":
                # HL creates new loop level
                hl_id = seg[1].value if seg[1] else ""
                parent_id = seg[2].value if seg[2] else ""
                level_code = seg[3].value if seg[3] else ""

                loop_id = self.HL_LOOP_MAPPING.get(level_code, f"HL_{level_code}")
                new_loop = Loop(loop_id=loop_id)
                new_loop.segments.append(seg)

                hl_loops[hl_id] = new_loop

                # Attach to parent or root
                if parent_id and parent_id in hl_loops:
                    hl_loops[parent_id].loops.append(new_loop)
                else:
                    root.loops.append(new_loop)

                current_loop = new_loop
                current_2000_loop = new_loop

            elif seg.segment_id == "NM1" and current_2000_loop:
                # NM1 may create a 2010 level sub-loop
                entity_code = seg[1].value if seg[1] else ""
                sub_loop_id = self.NM1_LOOP_MAPPING.get(entity_code)

                if sub_loop_id:
                    sub_loop = Loop(loop_id=sub_loop_id)
                    sub_loop.segments.append(seg)
                    current_2000_loop.loops.append(sub_loop)
                    current_loop = sub_loop
                else:
                    current_loop.segments.append(seg)

            elif seg.segment_id == "CLM" and current_2000_loop:
                # CLM creates 2300 claim loop
                claim_loop = Loop(loop_id="2300")
                claim_loop.segments.append(seg)
                current_2000_loop.loops.append(claim_loop)
                current_loop = claim_loop

            elif seg.segment_id == "LX" and current_2000_loop:
                # LX creates 2400 service line loop
                line_loop = Loop(loop_id="2400")
                line_loop.segments.append(seg)
                # Find parent 2300 loop or use current_2000_loop
                parent = self._find_loop(current_2000_loop, "2300")
                if parent:
                    parent.loops.append(line_loop)
                else:
                    current_2000_loop.loops.append(line_loop)
                current_loop = line_loop

            else:
                # Regular segment goes in current loop
                current_loop.segments.append(seg)

        return root

    def _find_loop(self, start: Loop, loop_id: str) -> Loop | None:
        """Find a loop by ID starting from given loop."""
        if start.loop_id == loop_id:
            return start
        for child in start.loops:
            found = self._find_loop(child, loop_id)
            if found:
                return found
        return None
