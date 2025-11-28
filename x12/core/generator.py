"""
X12 EDI Generator.

Generates EDI content from models and data structures.
"""
from __future__ import annotations

from datetime import date, time, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from x12.core.delimiters import Delimiters

if TYPE_CHECKING:
    from x12.models import Segment, TransactionSet


class Generator:
    """X12 EDI Generator.
    
    Generates EDI content from segments and models.
    
    Example:
        >>> gen = Generator()
        >>> edi = gen.generate_segment("NM1", ["85", "2", "NAME"])
        >>> print(edi)
        NM1*85*2*NAME~
    """
    
    def __init__(self, delimiters: Delimiters | None = None) -> None:
        """Initialize generator.
        
        Args:
            delimiters: Delimiter configuration. Defaults to standard delimiters.
        """
        self._delimiters = delimiters or Delimiters()
        self._isa_control_number = 0
        self._gs_control_number = 0
        self._st_control_number = 0
    
    @property
    def delimiters(self) -> Delimiters:
        """Get current delimiter configuration."""
        return self._delimiters
    
    def generate_segment(
        self, 
        segment_id: str, 
        elements: list[str | list[str]],
    ) -> str:
        """Generate a single segment.
        
        Args:
            segment_id: Segment identifier (e.g., "NM1").
            elements: List of element values. Nested lists are composite elements.
        
        Returns:
            EDI segment string.
        
        Example:
            >>> gen.generate_segment("NM1", ["85", "2", "NAME"])
            'NM1*85*2*NAME~'
        """
        d = self._delimiters
        parts = [segment_id]
        
        for elem in elements:
            if isinstance(elem, list):
                # Composite element
                parts.append(d.component.join(str(c) for c in elem))
            else:
                parts.append(str(elem) if elem is not None else "")
        
        return d.element.join(parts) + d.segment
    
    def generate_isa(
        self,
        sender_id: str,
        receiver_id: str,
        sender_qualifier: str = "ZZ",
        receiver_qualifier: str = "ZZ",
        control_number: int | None = None,
        date_value: date | None = None,
        time_value: time | None = None,
        version: str = "00501",
        usage: str = "P",
        ack_requested: str = "0",
    ) -> str:
        """Generate ISA segment (exactly 106 characters).
        
        Args:
            sender_id: Interchange sender ID (ISA06).
            receiver_id: Interchange receiver ID (ISA08).
            sender_qualifier: Sender ID qualifier (ISA05).
            receiver_qualifier: Receiver ID qualifier (ISA07).
            control_number: Interchange control number (ISA13).
            date_value: Interchange date (ISA09).
            time_value: Interchange time (ISA10).
            version: Interchange version (ISA12).
            usage: Usage indicator (ISA15) - P=Production, T=Test.
            ack_requested: Acknowledgment requested (ISA14).
        
        Returns:
            ISA segment string (106 characters).
        """
        d = self._delimiters
        
        # Auto-increment control number if not provided
        if control_number is None:
            self._isa_control_number += 1
            control_number = self._isa_control_number
        
        # Use current date/time if not provided
        now = datetime.now()
        if date_value is None:
            date_value = now.date()
        if time_value is None:
            time_value = now.time()
        
        # Build ISA with fixed-width fields
        isa = (
            f"ISA{d.element}"
            f"00{d.element}"  # ISA01 - Auth qualifier (2)
            f"          {d.element}"  # ISA02 - Auth info (10)
            f"00{d.element}"  # ISA03 - Security qualifier (2)
            f"          {d.element}"  # ISA04 - Security info (10)
            f"{sender_qualifier:2}{d.element}"  # ISA05 (2)
            f"{sender_id:15}{d.element}"  # ISA06 (15)
            f"{receiver_qualifier:2}{d.element}"  # ISA07 (2)
            f"{receiver_id:15}{d.element}"  # ISA08 (15)
            f"{date_value.strftime('%y%m%d')}{d.element}"  # ISA09 (6)
            f"{time_value.strftime('%H%M')}{d.element}"  # ISA10 (4)
            f"{d.repetition}{d.element}"  # ISA11 (1)
            f"{version:5}{d.element}"  # ISA12 (5)
            f"{control_number:09d}{d.element}"  # ISA13 (9)
            f"{ack_requested}{d.element}"  # ISA14 (1)
            f"{usage}{d.element}"  # ISA15 (1)
            f"{d.component}{d.segment}"  # ISA16 (1) + terminator
        )
        
        return isa
    
    def generate_gs(
        self,
        functional_id: str,
        sender_code: str,
        receiver_code: str,
        control_number: int | None = None,
        version: str = "005010X222A1",
        date_value: date | None = None,
        time_value: time | None = None,
    ) -> str:
        """Generate GS segment.
        
        Args:
            functional_id: Functional identifier (GS01) - HC, PO, etc.
            sender_code: Application sender code (GS02).
            receiver_code: Application receiver code (GS03).
            control_number: Group control number (GS06).
            version: Version/implementation guide (GS08).
            date_value: Functional group date (GS04).
            time_value: Functional group time (GS05).
        
        Returns:
            GS segment string.
        """
        if control_number is None:
            self._gs_control_number += 1
            control_number = self._gs_control_number
        
        now = datetime.now()
        if date_value is None:
            date_value = now.date()
        if time_value is None:
            time_value = now.time()
        
        return self.generate_segment("GS", [
            functional_id,
            sender_code,
            receiver_code,
            date_value.strftime("%Y%m%d"),
            time_value.strftime("%H%M"),
            str(control_number),
            "X",  # Responsible agency code
            version,
        ])
    
    def generate_st(
        self,
        transaction_set_id: str,
        control_number: str,
        version: str | None = None,
    ) -> str:
        """Generate ST segment.
        
        Args:
            transaction_set_id: Transaction set ID (ST01) - 837, 850, etc.
            control_number: Transaction control number (ST02).
            version: Implementation convention reference (ST03).
        
        Returns:
            ST segment string.
        """
        elements = [transaction_set_id, control_number]
        if version:
            elements.append(version)
        
        return self.generate_segment("ST", elements)
    
    def generate_se(
        self,
        segment_count: int,
        control_number: str,
    ) -> str:
        """Generate SE segment.
        
        Args:
            segment_count: Number of segments including ST and SE (SE01).
            control_number: Transaction control number (SE02).
        
        Returns:
            SE segment string.
        """
        return self.generate_segment("SE", [str(segment_count), control_number])
    
    def generate_ge(
        self,
        transaction_count: int,
        control_number: int,
    ) -> str:
        """Generate GE segment.
        
        Args:
            transaction_count: Number of transaction sets (GE01).
            control_number: Group control number (GE02).
        
        Returns:
            GE segment string.
        """
        return self.generate_segment("GE", [str(transaction_count), str(control_number)])
    
    def generate_iea(
        self,
        group_count: int,
        control_number: int,
    ) -> str:
        """Generate IEA segment.
        
        Args:
            group_count: Number of functional groups (IEA01).
            control_number: Interchange control number (IEA02).
        
        Returns:
            IEA segment string.
        """
        return self.generate_segment("IEA", [str(group_count), f"{control_number:09d}"])
    
    def generate_with_envelope(
        self,
        content: str | Any,
        transaction_set_id: str | None = None,
        sender_id: str = "SENDER",
        receiver_id: str = "RECEIVER",
        functional_id: str | None = None,
        version: str | None = None,
    ) -> str:
        """Generate complete EDI with ISA/GS/ST/SE/GE/IEA envelope.
        
        Args:
            content: Transaction content (segments between ST and SE), or a model.
            transaction_set_id: Transaction type (837, 850, etc.). Auto-detected if None.
            sender_id: Interchange sender ID.
            receiver_id: Interchange receiver ID.
            functional_id: Functional group ID (HC, PO, etc.). Auto-detected if None.
            version: Implementation guide version. Auto-detected if None.
        
        Returns:
            Complete EDI interchange string.
        """
        # If content is a model, detect type and generate from it
        if hasattr(content, 'to_edi'):
            model_name = type(content).__name__.lower()
            if transaction_set_id is None:
                if "837" in model_name or "claim" in model_name:
                    transaction_set_id = "837"
                elif "850" in model_name or "purchaseorder" in model_name:
                    transaction_set_id = "850"
                elif "835" in model_name or "remittance" in model_name:
                    transaction_set_id = "835"
                else:
                    transaction_set_id = "837"
            content = content.to_edi(self._delimiters)
        elif not isinstance(content, str):
            content = str(content)
        
        # Set defaults based on transaction type
        if transaction_set_id is None:
            transaction_set_id = "837"
        if functional_id is None:
            if transaction_set_id == "850":
                functional_id = "PO"
            elif transaction_set_id == "835":
                functional_id = "HP"
            else:
                functional_id = "HC"
        if version is None:
            if transaction_set_id == "850":
                version = "004010"
            elif transaction_set_id == "835":
                version = "005010X221A1"
            else:
                version = "005010X222A1"
        
        # Count segments in content
        content_segments = content.count(self._delimiters.segment)
        total_segments = content_segments + 2  # +2 for ST and SE
        
        # Generate control numbers
        isa_ctrl = self._isa_control_number + 1
        gs_ctrl = self._gs_control_number + 1
        
        parts = [
            self.generate_isa(sender_id, receiver_id, control_number=isa_ctrl),
            self.generate_gs(functional_id, sender_id, receiver_id, 
                           control_number=gs_ctrl, version=version),
            self.generate_st(transaction_set_id, "0001", version),
            content,
            self.generate_se(total_segments, "0001"),
            self.generate_ge(1, gs_ctrl),
            self.generate_iea(1, isa_ctrl),
        ]
        
        return "".join(parts)
    
    def generate_from_segment(self, segment: "Segment") -> str:
        """Generate EDI string from a Segment model.
        
        Args:
            segment: Segment model.
        
        Returns:
            EDI segment string.
        """
        return segment.to_edi(self._delimiters)
    
    def generate_from_transaction(self, transaction: "TransactionSet") -> str:
        """Generate EDI from a TransactionSet model.
        
        Args:
            transaction: TransactionSet model.
        
        Returns:
            Complete EDI interchange with envelope.
        """
        # Collect all segments from the transaction
        parts = []
        
        def collect_segments(loop):
            for seg in loop.segments:
                parts.append(self.generate_from_segment(seg))
            for child in loop.loops:
                collect_segments(child)
        
        if transaction.root_loop:
            collect_segments(transaction.root_loop)
        
        content = "".join(parts)
        
        # Determine transaction type
        txn_type = transaction.transaction_set_id or "837"
        func_id = "HC"
        version = "005010X222A1"
        
        if txn_type == "850":
            func_id = "PO"
            version = "004010"
        elif txn_type == "835":
            func_id = "HP"
            version = "005010X221A1"
        
        # Wrap in envelope
        return self.generate_with_envelope(
            content=content,
            transaction_set_id=txn_type,
            sender_id="SENDER",
            receiver_id="RECEIVER",
            functional_id=func_id,
            version=version,
        )
    
    def generate(self, model: Any) -> str:
        """Generate EDI from any supported model.
        
        Args:
            model: Any model with to_edi method or TransactionSet.
        
        Returns:
            Generated EDI string with complete envelope.
        """
        # Determine transaction type
        txn_type = "837"
        func_id = "HC"
        version = "005010X222A1"
        
        model_name = type(model).__name__.lower()
        if "837" in model_name or "claim" in model_name:
            txn_type = "837"
            func_id = "HC"
            version = "005010X222A1"
        elif "850" in model_name or "purchaseorder" in model_name:
            txn_type = "850"
            func_id = "PO"
            version = "004010"
        elif "835" in model_name or "remittance" in model_name:
            txn_type = "835"
            func_id = "HP"
            version = "005010X221A1"
        
        # Get content from model
        if hasattr(model, 'to_edi'):
            content = model.to_edi(self._delimiters)
        elif hasattr(model, 'root_loop'):
            content = self.generate_from_transaction(model)
        else:
            raise TypeError(f"Cannot generate EDI from {type(model)}")
        
        # Wrap in envelope
        return self.generate_with_envelope(
            content=content,
            transaction_set_id=txn_type,
            sender_id="SENDER",
            receiver_id="RECEIVER",
            functional_id=func_id,
            version=version,
        )
    
    def reset_control_numbers(self) -> None:
        """Reset all control numbers to 0."""
        self._isa_control_number = 0
        self._gs_control_number = 0
        self._st_control_number = 0
    
    def format_date(self, d: date, format: str = "CCYYMMDD") -> str:
        """Format date for EDI.
        
        Args:
            d: Date to format.
            format: Format string - CCYYMMDD or YYMMDD.
        
        Returns:
            Formatted date string.
        """
        if format == "YYMMDD":
            return d.strftime("%y%m%d")
        return d.strftime("%Y%m%d")
    
    def format_time(self, t: time, include_seconds: bool = False) -> str:
        """Format time for EDI.
        
        Args:
            t: Time to format.
            include_seconds: Include seconds in output.
        
        Returns:
            Formatted time string (HHMM or HHMMSS).
        """
        if include_seconds:
            return t.strftime("%H%M%S")
        return t.strftime("%H%M")
