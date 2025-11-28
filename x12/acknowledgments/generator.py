"""
Acknowledgment Generation for X12 EDI.

Generates 997 (Functional Acknowledgment) and 999 (Implementation Acknowledgment)
transactions based on validation results.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from x12.core.validator import ValidationReport, ValidationResult
    from x12.core.delimiters import Delimiters


class FunctionalGroupAckCode(str, Enum):
    """Functional group acknowledgment codes (AK901)."""
    ACCEPTED = "A"  # Accepted
    ACCEPTED_WITH_ERRORS = "E"  # Accepted but errors noted
    PARTIALLY_ACCEPTED = "P"  # Partially accepted
    REJECTED = "R"  # Rejected


class TransactionSetAckCode(str, Enum):
    """Transaction set acknowledgment codes (AK501)."""
    ACCEPTED = "A"  # Accepted
    ACCEPTED_WITH_ERRORS = "E"  # Accepted with errors
    REJECTED = "R"  # Rejected


@dataclass
class AK3Segment:
    """AK3 - Data Segment Note (error in a segment)."""
    segment_id: str
    segment_position: int
    loop_id: str = ""
    error_code: str = ""


@dataclass
class AK4Segment:
    """AK4 - Data Element Note (error in an element)."""
    element_position: int
    component_position: int = 0
    element_reference: str = ""
    error_code: str = ""
    bad_value: str = ""
    
    @property
    def position(self) -> int:
        """Alias for element_position."""
        return self.element_position


@dataclass
class IK3Segment:
    """IK3 - Implementation Data Segment Note (999)."""
    segment_id: str
    segment_position: int
    loop_id: str = ""
    error_code: str = ""


@dataclass  
class IK4Segment:
    """IK4 - Implementation Data Element Note (999)."""
    element_position: int
    component_position: int = 0
    element_reference: str = ""
    error_code: str = ""
    bad_value: str = ""


@dataclass
class Acknowledgment:
    """Acknowledgment result for a transaction."""
    transaction_set_id: str
    control_number: str
    status: TransactionSetAckCode
    ak3_segments: list[AK3Segment] = field(default_factory=list)
    ak4_segments: list[AK4Segment] = field(default_factory=list)
    ik3_segments: list[IK3Segment] = field(default_factory=list)
    ik4_segments: list[IK4Segment] = field(default_factory=list)
    error_count: int = 0
    
    @property
    def segment_errors(self) -> list:
        """Return IK3 or AK3 segment errors."""
        return self.ik3_segments if self.ik3_segments else self.ak3_segments
    
    @property
    def element_errors(self) -> list:
        """Return IK4 or AK4 element errors."""
        return self.ik4_segments if self.ik4_segments else self.ak4_segments


@dataclass
class FunctionalGroupAck:
    """Functional Group acknowledgment result."""
    functional_id_code: str
    group_control_number: str
    group_ack_code: FunctionalGroupAckCode
    transaction_acks: list[Acknowledgment] = field(default_factory=list)
    error_count: int = 0
    implementation_convention: str = ""
    
    @property
    def transaction_responses(self) -> list[Acknowledgment]:
        """Alias for transaction_acks for compatibility."""
        return self.transaction_acks


class AcknowledgmentGenerator:
    """Generates 997/999 acknowledgments from validation results.
    
    Example:
        >>> gen = AcknowledgmentGenerator(sender_id="R", receiver_id="S")
        >>> ack = gen.generate_997(functional_group, [report])
        >>> print(ack.group_ack_code)
    """
    
    def __init__(
        self,
        sender_id: str = "RECEIVER",
        sender_qualifier: str = "ZZ",
        receiver_id: str = "SENDER",
        receiver_qualifier: str = "ZZ",
    ) -> None:
        """Initialize generator."""
        self.sender_id = sender_id
        self.sender_qualifier = sender_qualifier
        self.receiver_id = receiver_id
        self.receiver_qualifier = receiver_qualifier
    
    def generate_997(
        self,
        received_gs: "object",  # FunctionalGroup
        validation_reports: list["ValidationReport"],
    ) -> FunctionalGroupAck:
        """Generate 997 Functional Acknowledgment.
        
        Args:
            received_gs: The functional group being acknowledged.
            validation_reports: Validation reports for each transaction.
        
        Returns:
            FunctionalGroupAck with status and transaction acknowledgments.
        """
        # Get functional group info
        func_id = getattr(received_gs, 'functional_id_code', 'HC')
        ctrl_num = getattr(received_gs, 'control_number', '1')
        transactions = getattr(received_gs, 'transactions', [])
        
        # Process each transaction
        transaction_acks = []
        total_errors = 0
        all_accepted = True
        
        for i, report in enumerate(validation_reports):
            # Get transaction info
            txn = transactions[i] if i < len(transactions) else None
            txn_id = getattr(txn, 'transaction_set_id', '837') if txn else '837'
            txn_ctrl = getattr(txn, 'control_number', str(i + 1)) if txn else str(i + 1)
            
            # Determine status
            if report.is_valid:
                status = TransactionSetAckCode.ACCEPTED
            elif report.error_count > 0:
                status = TransactionSetAckCode.REJECTED
                all_accepted = False
            else:
                status = TransactionSetAckCode.ACCEPTED_WITH_ERRORS
                all_accepted = False
            
            # Build AK3/AK4 segments from errors
            ak3_segments = []
            ak4_segments = []
            
            for error in report.errors:
                if error.segment_id:
                    ak3 = AK3Segment(
                        segment_id=error.segment_id,
                        segment_position=error.segment_position or 0,
                        error_code=self._map_error_to_ak3_code(error),
                    )
                    ak3_segments.append(ak3)
                    
                    if error.element_index:
                        ak4 = AK4Segment(
                            element_position=error.element_index,
                            error_code=self._map_error_to_ak4_code(error),
                            bad_value=error.actual or "",
                        )
                        ak4_segments.append(ak4)
            
            total_errors += report.error_count
            
            transaction_acks.append(Acknowledgment(
                transaction_set_id=txn_id,
                control_number=txn_ctrl,
                status=status,
                ak3_segments=ak3_segments,
                ak4_segments=ak4_segments,
                error_count=report.error_count,
            ))
        
        # Determine group-level status
        if all_accepted:
            group_status = FunctionalGroupAckCode.ACCEPTED
        elif total_errors > 0:
            group_status = FunctionalGroupAckCode.REJECTED
        else:
            group_status = FunctionalGroupAckCode.ACCEPTED_WITH_ERRORS
        
        return FunctionalGroupAck(
            functional_id_code=func_id,
            group_control_number=ctrl_num,
            group_ack_code=group_status,
            transaction_acks=transaction_acks,
            error_count=total_errors,
        )
    
    def generate_999(
        self,
        received_gs: "object",  # FunctionalGroup
        validation_reports: list["ValidationReport"],
        version: str = "005010X222A1",
    ) -> FunctionalGroupAck:
        """Generate 999 Implementation Acknowledgment (HIPAA).
        
        Args:
            received_gs: The functional group being acknowledged.
            validation_reports: Validation reports for each transaction.
            version: Implementation convention reference.
        
        Returns:
            FunctionalGroupAck with status and IK3/IK4 segments.
        """
        # Get functional group info
        func_id = getattr(received_gs, 'functional_id_code', 'HC')
        ctrl_num = getattr(received_gs, 'control_number', '1')
        transactions = getattr(received_gs, 'transactions', [])
        
        # Process each transaction
        transaction_acks = []
        total_errors = 0
        all_accepted = True
        
        for i, report in enumerate(validation_reports):
            txn = transactions[i] if i < len(transactions) else None
            txn_id = getattr(txn, 'transaction_set_id', '837') if txn else '837'
            txn_ctrl = getattr(txn, 'control_number', str(i + 1)) if txn else str(i + 1)
            
            if report.is_valid:
                status = TransactionSetAckCode.ACCEPTED
            elif report.error_count > 0:
                status = TransactionSetAckCode.REJECTED
                all_accepted = False
            else:
                status = TransactionSetAckCode.ACCEPTED_WITH_ERRORS
                all_accepted = False
            
            # Build IK3/IK4 segments from errors
            ik3_segments = []
            ik4_segments = []
            
            for error in report.errors:
                if error.segment_id:
                    ik3 = IK3Segment(
                        segment_id=error.segment_id,
                        segment_position=error.segment_position or 0,
                        error_code=self._map_error_to_ik3_code(error),
                    )
                    ik3_segments.append(ik3)
                    
                    if error.element_index:
                        ik4 = IK4Segment(
                            element_position=error.element_index,
                            error_code=self._map_error_to_ik4_code(error),
                            bad_value=error.actual or "",
                        )
                        ik4_segments.append(ik4)
            
            total_errors += report.error_count
            
            transaction_acks.append(Acknowledgment(
                transaction_set_id=txn_id,
                control_number=txn_ctrl,
                status=status,
                ik3_segments=ik3_segments,
                ik4_segments=ik4_segments,
                error_count=report.error_count,
            ))
        
        # Determine group-level status
        if all_accepted:
            group_status = FunctionalGroupAckCode.ACCEPTED
        elif total_errors > 0:
            group_status = FunctionalGroupAckCode.REJECTED
        else:
            group_status = FunctionalGroupAckCode.ACCEPTED_WITH_ERRORS
        
        return FunctionalGroupAck(
            functional_id_code=func_id,
            group_control_number=ctrl_num,
            group_ack_code=group_status,
            transaction_acks=transaction_acks,
            error_count=total_errors,
            implementation_convention=version,
        )
    
    def _map_error_to_ak3_code(self, error: "ValidationResult") -> str:
        """Map validation error to AK3 error code."""
        rule_id = error.rule_id.upper() if error.rule_id else ""
        
        if "MISSING" in rule_id:
            return "3"  # Mandatory segment missing
        elif "SYNTAX" in rule_id:
            return "8"  # Segment has data element errors
        else:
            return "8"  # Default: data element errors
    
    def _map_error_to_ak4_code(self, error: "ValidationResult") -> str:
        """Map validation error to AK4 error code."""
        rule_id = error.rule_id.upper() if error.rule_id else ""
        
        if "REQUIRED" in rule_id or "MISSING" in rule_id:
            return "1"  # Mandatory data element missing
        elif "LENGTH" in rule_id:
            return "4"  # Data element too long
        elif "INVALID" in rule_id:
            return "7"  # Invalid code value
        else:
            return "8"  # Invalid date/time
    
    def _map_error_to_ik3_code(self, error: "ValidationResult") -> str:
        """Map validation error to IK3 error code."""
        return self._map_error_to_ak3_code(error)
    
    def _map_error_to_ik4_code(self, error: "ValidationResult") -> str:
        """Map validation error to IK4 error code."""
        return self._map_error_to_ak4_code(error)
    
    def _map_to_segment_error(self, error: "ValidationResult") -> AK3Segment:
        """Map validation error to AK3 segment error."""
        return AK3Segment(
            segment_id=error.segment_id or "UNK",
            segment_position=error.segment_position or 0,
            error_code=self._map_error_to_ak3_code(error),
        )
    
    def _map_to_element_error(self, error: "ValidationResult") -> AK4Segment:
        """Map validation error to AK4 element error."""
        return AK4Segment(
            element_position=error.element_index or 0,
            error_code=self._map_error_to_ak4_code(error),
            bad_value=error.actual or "",
        )


class AcknowledgmentSerializer:
    """Serializes Acknowledgment objects to EDI format.
    
    Example:
        >>> serializer = AcknowledgmentSerializer()
        >>> edi = serializer.serialize_997(acknowledgment)
    """
    
    def __init__(self, delimiters: "Delimiters | None" = None) -> None:
        """Initialize serializer."""
        from x12.core.delimiters import Delimiters
        self._delimiters = delimiters or Delimiters()
    
    def serialize_997(
        self,
        ack: FunctionalGroupAck,
        delimiters: "Delimiters | None" = None,
        sender_id: str = "RECEIVER",
        receiver_id: str = "SENDER",
    ) -> str:
        """Serialize 997 acknowledgment to EDI.
        
        Args:
            ack: FunctionalGroupAck to serialize.
            delimiters: Optional delimiter configuration.
            sender_id: Sender ID for envelope.
            receiver_id: Receiver ID for envelope.
        
        Returns:
            Complete EDI interchange string.
        """
        from x12.core.generator import Generator
        from x12.core.delimiters import Delimiters
        
        d = delimiters or self._delimiters or Delimiters()
        gen = Generator(delimiters=d)
        parts = []
        
        # AK1 - Functional Group Response Header
        parts.append(f"AK1{d.element}{ack.functional_id_code}{d.element}{ack.group_control_number}{d.segment}")
        
        # Process each transaction acknowledgment
        for txn_ack in ack.transaction_acks:
            # AK2 - Transaction Set Response Header
            parts.append(f"AK2{d.element}{txn_ack.transaction_set_id}{d.element}{txn_ack.control_number}{d.segment}")
            
            # AK3/AK4 for errors
            for ak3 in txn_ack.ak3_segments:
                parts.append(f"AK3{d.element}{ak3.segment_id}{d.element}{ak3.segment_position}{d.element}{ak3.loop_id}{d.element}{ak3.error_code}{d.segment}")
            
            for ak4 in txn_ack.ak4_segments:
                parts.append(f"AK4{d.element}{ak4.element_position}{d.element}{ak4.component_position}{d.element}{ak4.element_reference}{d.element}{ak4.error_code}{d.segment}")
            
            # AK5 - Transaction Set Response Trailer
            parts.append(f"AK5{d.element}{txn_ack.status.value}{d.segment}")
        
        # AK9 - Functional Group Response Trailer
        accepted = sum(1 for t in ack.transaction_acks if t.status == TransactionSetAckCode.ACCEPTED)
        parts.append(f"AK9{d.element}{ack.group_ack_code.value}{d.element}{len(ack.transaction_acks)}{d.element}{len(ack.transaction_acks)}{d.element}{accepted}{d.segment}")
        
        content = "".join(parts)
        
        return gen.generate_with_envelope(
            content=content,
            transaction_set_id="997",
            sender_id=sender_id,
            receiver_id=receiver_id,
            functional_id="FA",
            version="005010",
        )
    
    def to_edi(
        self,
        ack: Acknowledgment,
        is_999: bool = False,
        sender_id: str = "RECEIVER",
        receiver_id: str = "SENDER",
    ) -> str:
        """Convert acknowledgment to EDI string.
        
        Args:
            ack: Acknowledgment object.
            is_999: True for 999, False for 997.
            sender_id: Sender ID for envelope.
            receiver_id: Receiver ID for envelope.
        
        Returns:
            Complete EDI interchange string.
        """
        from x12.core.generator import Generator
        
        d = self._delimiters
        gen = Generator(delimiters=d)
        
        # Build transaction content
        txn_type = "999" if is_999 else "997"
        
        parts = []
        
        # AK1 - Functional Group Response Header
        parts.append(f"AK1{d.element}HC{d.element}{ack.control_number}{d.segment}")
        
        # AK2 - Transaction Set Response Header
        parts.append(f"AK2{d.element}{ack.transaction_set_id}{d.element}{ack.control_number}{d.segment}")
        
        if is_999:
            # IK3/IK4 for 999
            for ik3 in ack.ik3_segments:
                parts.append(f"IK3{d.element}{ik3.segment_id}{d.element}{ik3.segment_position}{d.element}{ik3.loop_id}{d.element}{ik3.error_code}{d.segment}")
            
            for ik4 in ack.ik4_segments:
                parts.append(f"IK4{d.element}{ik4.element_position}{d.element}{ik4.component_position}{d.element}{ik4.element_reference}{d.element}{ik4.error_code}{d.segment}")
            
            # IK5 - Implementation Transaction Set Response Trailer
            parts.append(f"IK5{d.element}{ack.status.value}{d.segment}")
        else:
            # AK3/AK4 for 997
            for ak3 in ack.ak3_segments:
                parts.append(f"AK3{d.element}{ak3.segment_id}{d.element}{ak3.segment_position}{d.element}{ak3.loop_id}{d.element}{ak3.error_code}{d.segment}")
            
            for ak4 in ack.ak4_segments:
                parts.append(f"AK4{d.element}{ak4.element_position}{d.element}{ak4.component_position}{d.element}{ak4.element_reference}{d.element}{ak4.error_code}{d.segment}")
            
            # AK5 - Transaction Set Response Trailer
            parts.append(f"AK5{d.element}{ack.status.value}{d.segment}")
        
        # AK9 - Functional Group Response Trailer
        group_status = FunctionalGroupAckCode.ACCEPTED if ack.status == TransactionSetAckCode.ACCEPTED else FunctionalGroupAckCode.REJECTED
        parts.append(f"AK9{d.element}{group_status.value}{d.element}1{d.element}1{d.element}{'1' if ack.status == TransactionSetAckCode.ACCEPTED else '0'}{d.segment}")
        
        content = "".join(parts)
        
        # Wrap in envelope
        return gen.generate_with_envelope(
            content=content,
            transaction_set_id=txn_type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            functional_id="FA",  # Functional Acknowledgment
            version="005010X231A1" if is_999 else "005010",
        )
