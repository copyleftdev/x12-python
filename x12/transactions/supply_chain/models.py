"""
Supply chain transaction models.

Models for 850 Purchase Order, 856 Ship Notice, 810 Invoice, etc.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, computed_field

if TYPE_CHECKING:
    from x12.models import TransactionSet
    from x12.core.delimiters import Delimiters


class LineItem(BaseModel):
    """Purchase order line item.
    
    Attributes:
        line_number: Line sequence number.
        quantity: Order quantity.
        unit: Unit of measure.
        price: Unit price.
        upc: UPC/product code.
        description: Item description.
    """
    
    model_config = {"extra": "ignore"}
    
    line_number: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., ge=0)
    unit: str = Field(..., min_length=1, max_length=2)
    price: Decimal = Field(..., ge=0)
    upc: str | None = None
    sku: str | None = None
    description: str | None = None
    
    @computed_field
    @property
    def line_total(self) -> Decimal:
        """Calculate line total (quantity * price)."""
        return self.quantity * self.price


class PurchaseOrder(BaseModel):
    """Purchase order model.
    
    Attributes:
        po_number: Purchase order number.
        order_date: Date order was placed.
        line_items: Line items on the order.
    """
    
    model_config = {"extra": "ignore"}
    
    po_number: str = Field(..., min_length=1)
    order_date: date | None = None
    ship_to_name: str | None = None
    ship_to_address: str | None = None
    bill_to_name: str | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    
    @computed_field
    @property
    def calculated_total(self) -> Decimal:
        """Calculate order total from line items."""
        return sum((item.line_total for item in self.line_items), Decimal(0))
    
    @computed_field
    @property
    def line_count(self) -> int:
        """Number of line items."""
        return len(self.line_items)


class PurchaseOrder850(PurchaseOrder):
    """850 Purchase Order transaction model.
    
    Extends PurchaseOrder with 850-specific functionality.
    """
    
    purpose_code: str = Field(default="00")  # 00=Original
    po_type: str = Field(default="SA")  # SA=Stand-alone
    
    @classmethod
    def from_transaction(cls, transaction: "TransactionSet") -> "PurchaseOrder850":
        """Create PurchaseOrder850 from parsed transaction.
        
        Args:
            transaction: Parsed 850 transaction.
        
        Returns:
            PurchaseOrder850 model instance.
        """
        root = transaction.root_loop
        
        # Extract BEG segment
        beg = root.get_segment("BEG")
        po_number = beg[3].value if beg and beg[3] else "UNKNOWN"
        purpose_code = beg[1].value if beg and beg[1] else "00"
        po_type = beg[2].value if beg and beg[2] else "SA"
        
        # Extract line items from PO1 segments
        line_items = []
        
        def find_po1(loop):
            for seg in loop.segments:
                if seg.segment_id == "PO1":
                    line_items.append(LineItem(
                        line_number=seg[1].value if seg[1] else str(len(line_items) + 1),
                        quantity=seg[2].as_decimal() if seg[2] else Decimal(0),
                        unit=seg[3].value if seg[3] else "EA",
                        price=seg[4].as_decimal() if seg[4] else Decimal(0),
                        upc=seg[7].value if seg[7] else None,
                        description=seg[8].value if len(seg.elements) > 7 and seg[8] else None,
                    ))
            for child in loop.loops:
                find_po1(child)
        
        find_po1(root)
        
        return cls(
            po_number=po_number,
            purpose_code=purpose_code,
            po_type=po_type,
            line_items=line_items,
        )
    
    def to_edi(self, delimiters: "Delimiters") -> str:
        """Generate EDI content for this PO.
        
        Args:
            delimiters: Delimiter configuration.
        
        Returns:
            EDI segment content.
        """
        d = delimiters
        parts = []
        
        # BEG - Beginning Segment for PO
        date_str = self.order_date.strftime("%Y%m%d") if self.order_date else "20231127"
        parts.append(f"BEG*{self.purpose_code}*{self.po_type}*{self.po_number}**{date_str}{d.segment}")
        
        # PO1 - Line Items
        for item in self.line_items:
            parts.append(f"PO1*{item.line_number}*{item.quantity}*{item.unit}*{item.price}**UP*{item.upc or ''}{d.segment}")
        
        # CTT - Transaction Totals
        parts.append(f"CTT*{len(self.line_items)}{d.segment}")
        
        return "".join(parts)
