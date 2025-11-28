"""
TDD Tests: Pydantic Models

These tests DEFINE the expected behavior of the X12 data models.
Implementation in x12/models/ must satisfy these specifications.

Run: pytest tests/unit/test_models.py -v
"""
import pytest
from datetime import date
from decimal import Decimal


@pytest.mark.unit
class TestElementModel:
    """Tests for Element model."""

    def test_element_has_value(self):
        """Element must have value attribute."""
        from x12.models import Element
        
        elem = Element(value="TEST", index=1)
        
        assert elem.value == "TEST"

    def test_element_has_index(self):
        """Element must have index attribute."""
        from x12.models import Element
        
        elem = Element(value="TEST", index=3)
        
        assert elem.index == 3

    def test_element_is_immutable(self):
        """Element must be immutable."""
        from x12.models import Element
        
        elem = Element(value="TEST", index=1)
        
        with pytest.raises((AttributeError, TypeError, Exception)):
            elem.value = "CHANGED"

    def test_element_equality(self):
        """Elements with same values must be equal."""
        from x12.models import Element
        
        e1 = Element(value="TEST", index=1)
        e2 = Element(value="TEST", index=1)
        
        assert e1 == e2

    def test_element_string_representation(self):
        """Element must have useful string representation."""
        from x12.models import Element
        
        elem = Element(value="TEST", index=1)
        
        assert "TEST" in str(elem) or "TEST" in repr(elem)


@pytest.mark.unit
class TestCompositeElement:
    """Tests for composite element handling."""

    def test_composite_element_has_components(self):
        """Composite element must have components list."""
        from x12.models import CompositeElement, Component
        
        composite = CompositeElement(
            index=1,
            components=[
                Component(value="HC", index=0),
                Component(value="99213", index=1),
            ]
        )
        
        assert len(composite.components) == 2

    def test_composite_component_access(self):
        """Components must be accessible by index."""
        from x12.models import CompositeElement, Component
        
        composite = CompositeElement(
            index=1,
            components=[
                Component(value="HC", index=0),
                Component(value="99213", index=1),
            ]
        )
        
        assert composite.component(0).value == "HC"
        assert composite.component(1).value == "99213"

    def test_composite_is_composite_flag(self):
        """Composite element must have is_composite=True."""
        from x12.models import CompositeElement, Component
        
        composite = CompositeElement(
            index=1,
            components=[Component(value="HC", index=0)]
        )
        
        assert composite.is_composite == True


@pytest.mark.unit
class TestSegmentModel:
    """Tests for Segment model."""

    def test_segment_has_id(self):
        """Segment must have segment_id."""
        from x12.models import Segment, Element
        
        seg = Segment(
            segment_id="NM1",
            elements=[Element(value="85", index=1)]
        )
        
        assert seg.segment_id == "NM1"

    def test_segment_has_elements(self):
        """Segment must have elements list."""
        from x12.models import Segment, Element
        
        seg = Segment(
            segment_id="NM1",
            elements=[
                Element(value="85", index=1),
                Element(value="2", index=2),
            ]
        )
        
        assert len(seg.elements) == 2

    def test_segment_element_access_by_index(self):
        """Segment must support element access by index."""
        from x12.models import Segment, Element
        
        seg = Segment(
            segment_id="NM1",
            elements=[
                Element(value="85", index=1),
                Element(value="2", index=2),
            ]
        )
        
        assert seg[1].value == "85"
        assert seg[2].value == "2"

    def test_segment_missing_element_returns_none(self):
        """Accessing missing element must return None."""
        from x12.models import Segment, Element
        
        seg = Segment(
            segment_id="NM1",
            elements=[Element(value="85", index=1)]
        )
        
        assert seg[99] is None

    def test_segment_is_immutable(self):
        """Segment must be immutable."""
        from x12.models import Segment, Element
        
        seg = Segment(
            segment_id="NM1",
            elements=[Element(value="85", index=1)]
        )
        
        with pytest.raises((AttributeError, TypeError, Exception)):
            seg.segment_id = "REF"


@pytest.mark.unit
class TestLoopModel:
    """Tests for Loop model."""

    def test_loop_has_id(self):
        """Loop must have loop_id."""
        from x12.models import Loop
        
        loop = Loop(loop_id="2000A")
        
        assert loop.loop_id == "2000A"

    def test_loop_has_segments(self):
        """Loop must have segments list."""
        from x12.models import Loop, Segment, Element
        
        loop = Loop(
            loop_id="2000A",
            segments=[
                Segment(segment_id="HL", elements=[Element(value="1", index=1)])
            ]
        )
        
        assert len(loop.segments) == 1

    def test_loop_has_children(self):
        """Loop must have child loops list."""
        from x12.models import Loop
        
        parent = Loop(
            loop_id="2000A",
            loops=[Loop(loop_id="2010AA")]
        )
        
        assert len(parent.loops) == 1
        assert parent.loops[0].loop_id == "2010AA"

    def test_loop_get_segment(self):
        """Loop must support getting segment by ID."""
        from x12.models import Loop, Segment, Element
        
        loop = Loop(
            loop_id="2000A",
            segments=[
                Segment(segment_id="HL", elements=[]),
                Segment(segment_id="NM1", elements=[Element(value="85", index=1)]),
            ]
        )
        
        nm1 = loop.get_segment("NM1")
        assert nm1 is not None
        assert nm1.segment_id == "NM1"

    def test_loop_get_loop(self):
        """Loop must support getting child loop by ID."""
        from x12.models import Loop
        
        parent = Loop(
            loop_id="2000A",
            loops=[
                Loop(loop_id="2010AA"),
                Loop(loop_id="2010AB"),
            ]
        )
        
        child = parent.get_loop("2010AA")
        assert child is not None
        assert child.loop_id == "2010AA"


@pytest.mark.unit
class TestTransactionSetModel:
    """Tests for TransactionSet model."""

    def test_transaction_has_id(self):
        """TransactionSet must have transaction_set_id."""
        from x12.models import TransactionSet, Loop
        
        txn = TransactionSet(
            transaction_set_id="837",
            control_number="0001",
            root_loop=Loop(loop_id="ROOT"),
        )
        
        assert txn.transaction_set_id == "837"

    def test_transaction_has_control_number(self):
        """TransactionSet must have control_number."""
        from x12.models import TransactionSet, Loop
        
        txn = TransactionSet(
            transaction_set_id="837",
            control_number="0001",
            root_loop=Loop(loop_id="ROOT"),
        )
        
        assert txn.control_number == "0001"

    def test_transaction_has_root_loop(self):
        """TransactionSet must have root_loop."""
        from x12.models import TransactionSet, Loop
        
        root = Loop(loop_id="ROOT")
        txn = TransactionSet(
            transaction_set_id="837",
            control_number="0001",
            root_loop=root,
        )
        
        assert txn.root_loop is not None


@pytest.mark.unit
class TestFunctionalGroupModel:
    """Tests for FunctionalGroup model."""

    def test_functional_group_has_id(self):
        """FunctionalGroup must have functional_id_code."""
        from x12.models import FunctionalGroup
        
        fg = FunctionalGroup(
            functional_id_code="HC",
            sender_code="SENDER",
            receiver_code="RECEIVER",
            control_number="1",
        )
        
        assert fg.functional_id_code == "HC"

    def test_functional_group_has_transactions(self):
        """FunctionalGroup must have transactions list."""
        from x12.models import FunctionalGroup, TransactionSet, Loop
        
        fg = FunctionalGroup(
            functional_id_code="HC",
            sender_code="SENDER",
            receiver_code="RECEIVER",
            control_number="1",
            transactions=[
                TransactionSet(
                    transaction_set_id="837",
                    control_number="0001",
                    root_loop=Loop(loop_id="ROOT"),
                )
            ]
        )
        
        assert len(fg.transactions) == 1


@pytest.mark.unit
class TestInterchangeModel:
    """Tests for Interchange model."""

    def test_interchange_has_sender(self):
        """Interchange must have sender info."""
        from x12.models import Interchange
        
        interchange = Interchange(
            sender_id="SENDER",
            sender_qualifier="ZZ",
            receiver_id="RECEIVER",
            receiver_qualifier="ZZ",
            control_number="000000001",
        )
        
        assert interchange.sender_id == "SENDER"

    def test_interchange_has_functional_groups(self):
        """Interchange must have functional_groups list."""
        from x12.models import Interchange, FunctionalGroup
        
        interchange = Interchange(
            sender_id="SENDER",
            sender_qualifier="ZZ",
            receiver_id="RECEIVER",
            receiver_qualifier="ZZ",
            control_number="000000001",
            functional_groups=[
                FunctionalGroup(
                    functional_id_code="HC",
                    sender_code="S",
                    receiver_code="R",
                    control_number="1",
                )
            ]
        )
        
        assert len(interchange.functional_groups) == 1


@pytest.mark.unit
class TestHealthcareModels:
    """Tests for healthcare-specific models."""

    def test_claim_model_structure(self, sample_claim_data):
        """Claim model must accept standard claim data."""
        from x12.transactions.healthcare import Claim
        
        claim = Claim(**sample_claim_data)
        
        assert claim.claim_id == "TEST001"
        assert claim.total_charge == Decimal("150.00")

    def test_provider_model_structure(self, sample_provider_data):
        """Provider model must accept standard provider data."""
        from x12.transactions.healthcare import Provider
        
        provider = Provider(**sample_provider_data)
        
        assert provider.npi == "1234567890"
        assert provider.name == "ACME MEDICAL GROUP"

    def test_subscriber_model_structure(self, sample_subscriber_data):
        """Subscriber model must accept standard subscriber data."""
        from x12.transactions.healthcare import Subscriber
        
        subscriber = Subscriber(**sample_subscriber_data)
        
        assert subscriber.member_id == "ABC123456789"
        assert subscriber.last_name == "DOE"


@pytest.mark.unit
class TestSupplyChainModels:
    """Tests for supply chain models."""

    def test_purchase_order_model_structure(self, sample_purchase_order_data):
        """PurchaseOrder model must accept standard PO data."""
        from x12.transactions.supply_chain import PurchaseOrder
        
        po = PurchaseOrder(**sample_purchase_order_data)
        
        assert po.po_number == "PO123456"
        assert len(po.line_items) == 2

    def test_line_item_model(self):
        """LineItem model must have required fields."""
        from x12.transactions.supply_chain import LineItem
        
        item = LineItem(
            line_number="1",
            quantity=Decimal("10"),
            unit="EA",
            price=Decimal("25.00"),
            upc="012345678901",
            description="WIDGET",
        )
        
        assert item.line_number == "1"
        assert item.quantity == Decimal("10")


@pytest.mark.unit
class TestModelValidation:
    """Tests for model validation."""

    def test_invalid_npi_rejected(self):
        """Invalid NPI must be rejected."""
        from x12.transactions.healthcare import Provider
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            Provider(
                npi="123",  # Too short
                name="TEST",
            )

    def test_negative_charge_rejected(self):
        """Negative charge amount must be rejected."""
        from x12.transactions.healthcare import Claim
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            Claim(
                claim_id="TEST",
                total_charge=Decimal("-100.00"),  # Negative
            )
