"""
Unit tests for X12 trading partners module.

Tests partner configuration and management.
TDD: These tests define the expected interface before implementation.
"""
from __future__ import annotations

import pytest


@pytest.mark.unit
class TestTradingPartner:
    """Tests for trading partner configuration."""

    def test_partner_has_id(self):
        """Partner must have identifier."""
        from x12.trading_partners import TradingPartner
        
        partner = TradingPartner(
            partner_id="PARTNER001",
            name="Acme Healthcare",
        )
        
        assert partner.partner_id == "PARTNER001"
        assert partner.name == "Acme Healthcare"

    def test_partner_interchange_ids(self):
        """Partner must have ISA sender/receiver IDs."""
        from x12.trading_partners import TradingPartner
        
        partner = TradingPartner(
            partner_id="PARTNER001",
            name="Acme Healthcare",
            interchange_id="ACMEHLTH",
            interchange_qualifier="ZZ",
        )
        
        assert partner.interchange_id == "ACMEHLTH"
        assert partner.interchange_qualifier == "ZZ"

    def test_partner_application_ids(self):
        """Partner must have GS sender/receiver codes."""
        from x12.trading_partners import TradingPartner
        
        partner = TradingPartner(
            partner_id="PARTNER001",
            name="Acme Healthcare",
            application_sender_code="ACME",
            application_receiver_code="RECV",
        )
        
        assert partner.application_sender_code == "ACME"
        assert partner.application_receiver_code == "RECV"

    def test_partner_supported_transactions(self):
        """Partner may specify supported transaction types."""
        from x12.trading_partners import TradingPartner
        
        partner = TradingPartner(
            partner_id="PARTNER001",
            name="Acme Healthcare",
            supported_transactions=["837", "835", "270", "271"],
        )
        
        assert "837" in partner.supported_transactions
        assert "999" not in partner.supported_transactions

    def test_partner_custom_delimiters(self):
        """Partner may specify custom delimiters."""
        from x12.trading_partners import TradingPartner
        from x12.core.delimiters import Delimiters
        
        custom_delims = Delimiters(element="|", segment="\n")
        partner = TradingPartner(
            partner_id="PARTNER001",
            name="Acme Healthcare",
            delimiters=custom_delims,
        )
        
        assert partner.delimiters.element == "|"
        assert partner.delimiters.segment == "\n"

    def test_partner_acknowledgment_settings(self):
        """Partner may specify acknowledgment requirements."""
        from x12.trading_partners import TradingPartner
        
        partner = TradingPartner(
            partner_id="PARTNER001",
            name="Acme Healthcare",
            requires_997=True,
            requires_999=True,
        )
        
        assert partner.requires_997 is True
        assert partner.requires_999 is True


@pytest.mark.unit
class TestPartnerRegistry:
    """Tests for trading partner registry."""

    def test_registry_add_partner(self):
        """Must add partner to registry."""
        from x12.trading_partners import TradingPartner, PartnerRegistry
        
        registry = PartnerRegistry()
        partner = TradingPartner(partner_id="P001", name="Partner One")
        
        registry.add(partner)
        
        retrieved = registry.get("P001")
        assert retrieved is not None
        assert retrieved.partner_id == "P001"

    def test_registry_get_by_interchange_id(self):
        """Must find partner by interchange ID."""
        from x12.trading_partners import TradingPartner, PartnerRegistry
        
        registry = PartnerRegistry()
        partner = TradingPartner(
            partner_id="P001",
            name="Partner One",
            interchange_id="INTCHG001",
            interchange_qualifier="ZZ",
        )
        registry.add(partner)
        
        found = registry.get_by_interchange_id("INTCHG001", "ZZ")
        assert found is not None
        assert found.partner_id == "P001"

    def test_registry_list_partners(self):
        """Must list all partners."""
        from x12.trading_partners import TradingPartner, PartnerRegistry
        
        registry = PartnerRegistry()
        registry.add(TradingPartner(partner_id="P001", name="Partner One"))
        registry.add(TradingPartner(partner_id="P002", name="Partner Two"))
        
        partners = registry.list_all()
        
        assert len(partners) == 2
        assert any(p.partner_id == "P001" for p in partners)
        assert any(p.partner_id == "P002" for p in partners)

    def test_registry_remove_partner(self):
        """Must remove partner from registry."""
        from x12.trading_partners import TradingPartner, PartnerRegistry
        
        registry = PartnerRegistry()
        partner = TradingPartner(partner_id="P001", name="Partner One")
        registry.add(partner)
        
        registry.remove("P001")
        
        assert registry.get("P001") is None


@pytest.mark.unit
class TestPartnerConfiguration:
    """Tests for partner-specific configuration."""

    def test_partner_contact_info(self):
        """Partner may have contact information."""
        from x12.trading_partners import TradingPartner, ContactInfo
        
        contact = ContactInfo(
            name="John Smith",
            phone="555-123-4567",
            email="john@acme.com",
        )
        
        partner = TradingPartner(
            partner_id="P001",
            name="Partner One",
            contact=contact,
        )
        
        assert partner.contact is not None
        assert partner.contact.name == "John Smith"
        assert partner.contact.email == "john@acme.com"

    def test_partner_production_vs_test(self):
        """Partner config may specify production vs test mode."""
        from x12.trading_partners import TradingPartner
        
        partner = TradingPartner(
            partner_id="P001",
            name="Partner One",
            is_production=False,
        )
        
        assert partner.is_production is False

    def test_partner_version_preference(self):
        """Partner may specify preferred X12 version."""
        from x12.trading_partners import TradingPartner
        
        partner = TradingPartner(
            partner_id="P001",
            name="Partner One",
            preferred_version="005010X222A1",
        )
        
        assert partner.preferred_version == "005010X222A1"


@pytest.mark.unit
class TestPartnerSerialization:
    """Tests for partner serialization/deserialization."""

    def test_partner_to_dict(self):
        """Partner must serialize to dictionary."""
        from x12.trading_partners import TradingPartner
        
        partner = TradingPartner(
            partner_id="P001",
            name="Partner One",
            interchange_id="INTCHG",
            interchange_qualifier="ZZ",
        )
        
        data = partner.to_dict()
        
        assert data["partner_id"] == "P001"
        assert data["name"] == "Partner One"
        assert data["interchange_id"] == "INTCHG"

    def test_partner_from_dict(self):
        """Partner must deserialize from dictionary."""
        from x12.trading_partners import TradingPartner
        
        data = {
            "partner_id": "P001",
            "name": "Partner One",
            "interchange_id": "INTCHG",
            "interchange_qualifier": "ZZ",
        }
        
        partner = TradingPartner.from_dict(data)
        
        assert partner.partner_id == "P001"
        assert partner.interchange_id == "INTCHG"


@pytest.mark.unit
class TestPartnerValidation:
    """Tests for partner validation."""

    def test_validate_partner_required_fields(self):
        """Must validate required fields."""
        from x12.trading_partners import TradingPartner
        
        partner = TradingPartner(partner_id="P001", name="Partner")
        errors = partner.validate()
        
        # Basic partner is valid (only ID and name required)
        assert len(errors) == 0

    def test_validate_interchange_id_length(self):
        """Interchange ID must be <= 15 characters."""
        from x12.trading_partners import TradingPartner
        
        partner = TradingPartner(
            partner_id="P001",
            name="Partner",
            interchange_id="TOOLONGINTERCHGID123",  # > 15 chars
            interchange_qualifier="ZZ",
        )
        
        errors = partner.validate()
        assert len(errors) > 0
        assert any("interchange" in e.lower() for e in errors)

    def test_validate_interchange_qualifier(self):
        """Interchange qualifier must be 2 characters."""
        from x12.trading_partners import TradingPartner
        
        partner = TradingPartner(
            partner_id="P001",
            name="Partner",
            interchange_id="INTCHG",
            interchange_qualifier="INVALID",  # Should be 2 chars
        )
        
        errors = partner.validate()
        assert len(errors) > 0
