"""
X12 Trading partner configuration classes.

Defines trading partner data structures and registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from x12.core.delimiters import Delimiters


@dataclass
class ContactInfo:
    """Trading partner contact information.

    Attributes:
        name: Contact name.
        phone: Phone number.
        email: Email address.
        fax: Fax number.
    """

    name: str = ""
    phone: str = ""
    email: str = ""
    fax: str = ""


@dataclass
class TradingPartner:
    """Trading partner configuration.

    Stores all configuration needed to exchange EDI with a trading partner.

    Attributes:
        partner_id: Unique internal identifier.
        name: Human-readable partner name.
        interchange_id: ISA sender/receiver ID (ISA06/ISA08).
        interchange_qualifier: ISA ID qualifier (ISA05/ISA07).
        application_sender_code: GS sender code (GS02).
        application_receiver_code: GS receiver code (GS03).
        supported_transactions: List of supported transaction types.
        delimiters: Custom delimiter configuration.
        requires_997: Whether partner requires 997 acknowledgment.
        requires_999: Whether partner requires 999 acknowledgment.
        contact: Contact information.
        is_production: Whether this is a production partner.
        preferred_version: Preferred X12 version.
    """

    partner_id: str
    name: str
    interchange_id: str = ""
    interchange_qualifier: str = "ZZ"
    application_sender_code: str = ""
    application_receiver_code: str = ""
    supported_transactions: list[str] = field(default_factory=list)
    delimiters: Delimiters | None = None
    requires_997: bool = False
    requires_999: bool = False
    contact: ContactInfo | None = None
    is_production: bool = True
    preferred_version: str = "005010"

    def to_dict(self) -> dict[str, Any]:
        """Serialize partner to dictionary.

        Returns:
            Dictionary representation.
        """
        result: dict[str, Any] = {
            "partner_id": self.partner_id,
            "name": self.name,
            "interchange_id": self.interchange_id,
            "interchange_qualifier": self.interchange_qualifier,
            "application_sender_code": self.application_sender_code,
            "application_receiver_code": self.application_receiver_code,
            "supported_transactions": self.supported_transactions,
            "requires_997": self.requires_997,
            "requires_999": self.requires_999,
            "is_production": self.is_production,
            "preferred_version": self.preferred_version,
        }

        if self.contact:
            result["contact"] = {
                "name": self.contact.name,
                "phone": self.contact.phone,
                "email": self.contact.email,
                "fax": self.contact.fax,
            }

        if self.delimiters:
            result["delimiters"] = {
                "element": self.delimiters.element,
                "segment": self.delimiters.segment,
                "component": self.delimiters.component,
                "repetition": self.delimiters.repetition,
            }

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TradingPartner:
        """Deserialize partner from dictionary.

        Args:
            data: Dictionary representation.

        Returns:
            TradingPartner instance.
        """
        contact = None
        if "contact" in data and data["contact"]:
            contact = ContactInfo(**data["contact"])

        delimiters = None
        if "delimiters" in data and data["delimiters"]:
            from x12.core.delimiters import Delimiters

            delimiters = Delimiters(**data["delimiters"])

        return cls(
            partner_id=data.get("partner_id", ""),
            name=data.get("name", ""),
            interchange_id=data.get("interchange_id", ""),
            interchange_qualifier=data.get("interchange_qualifier", "ZZ"),
            application_sender_code=data.get("application_sender_code", ""),
            application_receiver_code=data.get("application_receiver_code", ""),
            supported_transactions=data.get("supported_transactions", []),
            requires_997=data.get("requires_997", False),
            requires_999=data.get("requires_999", False),
            is_production=data.get("is_production", True),
            preferred_version=data.get("preferred_version", "005010"),
            contact=contact,
            delimiters=delimiters,
        )

    def validate(self) -> list[str]:
        """Validate partner configuration.

        Returns:
            List of validation error messages.
        """
        errors = []

        if not self.partner_id:
            errors.append("Partner ID is required")

        if not self.name:
            errors.append("Partner name is required")

        if self.interchange_id and len(self.interchange_id) > 15:
            errors.append("Interchange ID must be <= 15 characters")

        if self.interchange_qualifier and len(self.interchange_qualifier) != 2:
            errors.append("Interchange qualifier must be 2 characters")

        return errors


class PartnerRegistry:
    """Registry for managing trading partners.

    Provides CRUD operations for trading partner configurations.

    Example:
        >>> registry = PartnerRegistry()
        >>> registry.add(TradingPartner("P001", "Acme"))
        >>> partner = registry.get("P001")
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._partners: dict[str, TradingPartner] = {}
        self._by_interchange: dict[str, TradingPartner] = {}

    def add(self, partner: TradingPartner) -> None:
        """Add partner to registry.

        Args:
            partner: Trading partner to add.
        """
        self._partners[partner.partner_id] = partner

        if partner.interchange_id and partner.interchange_qualifier:
            key = f"{partner.interchange_id}:{partner.interchange_qualifier}"
            self._by_interchange[key] = partner

    def get(self, partner_id: str) -> TradingPartner | None:
        """Get partner by ID.

        Args:
            partner_id: Partner identifier.

        Returns:
            TradingPartner or None if not found.
        """
        return self._partners.get(partner_id)

    def get_by_interchange_id(
        self,
        interchange_id: str,
        qualifier: str,
    ) -> TradingPartner | None:
        """Find partner by interchange ID and qualifier.

        Args:
            interchange_id: ISA sender/receiver ID.
            qualifier: ID qualifier.

        Returns:
            TradingPartner or None if not found.
        """
        key = f"{interchange_id}:{qualifier}"
        return self._by_interchange.get(key)

    def list_all(self) -> list[TradingPartner]:
        """List all registered partners.

        Returns:
            List of all trading partners.
        """
        return list(self._partners.values())

    def remove(self, partner_id: str) -> None:
        """Remove partner from registry.

        Args:
            partner_id: Partner identifier to remove.
        """
        partner = self._partners.pop(partner_id, None)

        if partner and partner.interchange_id and partner.interchange_qualifier:
            key = f"{partner.interchange_id}:{partner.interchange_qualifier}"
            self._by_interchange.pop(key, None)
