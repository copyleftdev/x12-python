"""
Envelope models for X12 EDI (ISA/GS/ST).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from x12.core.delimiters import Delimiters
    from x12.models.loop import Loop


@dataclass
class TransactionSet:
    """A single X12 transaction set (ST/SE envelope).

    Attributes:
        transaction_set_id: Transaction type (e.g., "837", "850").
        control_number: ST02 control number.
        root_loop: Root loop containing all transaction content.
        version: Implementation version if specified.
    """

    transaction_set_id: str
    control_number: str
    root_loop: Loop
    version: str | None = None

    def __repr__(self) -> str:
        return f"TransactionSet({self.transaction_set_id}, ctrl={self.control_number})"


@dataclass
class FunctionalGroup:
    """A functional group (GS/GE envelope).

    Attributes:
        functional_id_code: GS01 functional identifier (e.g., "HC", "PO").
        sender_code: GS02 application sender code.
        receiver_code: GS03 application receiver code.
        control_number: GS06 group control number.
        version: GS08 version/implementation guide.
        transactions: Transaction sets in this group.
    """

    functional_id_code: str
    sender_code: str
    receiver_code: str
    control_number: str
    version: str | None = None
    transactions: list[TransactionSet] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"FunctionalGroup({self.functional_id_code}, {len(self.transactions)} txns)"


@dataclass
class Interchange:
    """An X12 interchange envelope (ISA/IEA).

    Attributes:
        sender_id: ISA06 interchange sender ID.
        sender_qualifier: ISA05 sender ID qualifier.
        receiver_id: ISA08 interchange receiver ID.
        receiver_qualifier: ISA07 receiver ID qualifier.
        control_number: ISA13 interchange control number.
        version: ISA12 interchange version.
        functional_groups: Functional groups in this interchange.
        delimiters: Delimiters detected/used for this interchange.
    """

    sender_id: str
    sender_qualifier: str
    receiver_id: str
    receiver_qualifier: str
    control_number: str
    version: str = "00501"
    functional_groups: list[FunctionalGroup] = field(default_factory=list)
    delimiters: Delimiters | None = None

    def __repr__(self) -> str:
        return f"Interchange({self.sender_id} -> {self.receiver_id}, {len(self.functional_groups)} groups)"
