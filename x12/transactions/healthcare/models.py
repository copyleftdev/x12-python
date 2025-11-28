"""
Healthcare transaction models.

Models for 837 claims, 835 remittance, 270/271 eligibility, etc.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, computed_field, field_validator

if TYPE_CHECKING:
    from x12.core.delimiters import Delimiters
    from x12.models import TransactionSet


class Provider(BaseModel):
    """Healthcare provider model.

    Attributes:
        npi: National Provider Identifier (10 digits).
        name: Provider name.
        tax_id: Tax ID / EIN (9 digits).
        address: Provider address.
    """

    model_config = {"extra": "ignore"}

    npi: str = Field(..., min_length=10, max_length=10)
    name: str = Field(..., min_length=1)
    tax_id: str | None = Field(default=None, min_length=9, max_length=9)
    address: dict | str | None = None  # Can be dict with line1, city, state, postal_code
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None

    @field_validator("npi")
    @classmethod
    def validate_npi(cls, v: str) -> str:
        """Validate NPI is 10 digits."""
        if not v.isdigit():
            raise ValueError("NPI must be numeric")
        if len(v) != 10:
            raise ValueError("NPI must be 10 digits")
        return v


class Subscriber(BaseModel):
    """Insurance subscriber model.

    Attributes:
        member_id: Member/subscriber ID.
        last_name: Subscriber last name.
        first_name: Subscriber first name.
        dob: Date of birth.
        gender: Gender code (M/F/U).
    """

    model_config = {"extra": "ignore"}

    member_id: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    first_name: str = Field(..., min_length=1)
    dob: date | None = None
    gender: str | None = Field(default=None, pattern=r"^[MFU]$")
    group_number: str | None = None
    payer_id: str | None = None


class ServiceLine(BaseModel):
    """Service line for a claim.

    Attributes:
        line_number: Line sequence number.
        procedure_code: CPT/HCPCS procedure code.
        charge: Line item charge amount.
        units: Number of units.
        service_date: Date of service.
    """

    model_config = {"extra": "ignore", "populate_by_name": True}

    line_number: int = Field(..., ge=1)
    procedure_code: str = Field(..., min_length=1)
    charge: Decimal = Field(default=Decimal(0), ge=0, alias="charge_amount")
    units: Decimal = Field(default=Decimal("1"), ge=0)
    service_date: date | None = None
    modifier: str | None = None
    diagnosis_pointer: list[int] = Field(default_factory=list)

    @computed_field
    @property
    def line_total(self) -> Decimal:
        """Calculate line total (charge * units)."""
        return self.charge * self.units


class Claim(BaseModel):
    """Healthcare claim model.

    Attributes:
        claim_id: Claim/patient account number.
        total_charge: Total claim charge.
        service_date: Date of service.
        diagnosis_codes: List of diagnosis codes.
        service_lines: Service line items.
    """

    model_config = {"extra": "ignore"}

    claim_id: str = Field(..., min_length=1)
    total_charge: Decimal = Field(..., ge=0)
    service_date: date | None = None
    facility_code: str | None = None
    diagnosis_codes: list[str] = Field(default_factory=list)
    service_lines: list[ServiceLine] = Field(default_factory=list)

    @field_validator("total_charge")
    @classmethod
    def validate_charge(cls, v: Decimal) -> Decimal:
        """Validate charge is non-negative."""
        if v < 0:
            raise ValueError("Charge cannot be negative")
        return v


class Claim837P(BaseModel):
    """837P Professional Claim transaction model.

    Represents a complete 837P transaction with all required loops.

    Attributes:
        billing_provider: Billing provider (2000A/2010AA).
        subscriber: Subscriber (2000B/2010BA).
        claims: Claim information (2300).
    """

    model_config = {"extra": "ignore"}

    billing_provider: Provider
    subscriber: Subscriber
    patient: Subscriber | None = None  # If different from subscriber
    claims: list[Claim] = Field(default_factory=list)
    submitter_name: str | None = None
    receiver_name: str | None = None

    @classmethod
    def from_transaction(cls, transaction: TransactionSet) -> Claim837P:
        """Create Claim837P from parsed transaction.

        Args:
            transaction: Parsed 837 transaction.

        Returns:
            Claim837P model instance.
        """
        root = transaction.root_loop

        # Extract provider from 2000A/2010AA
        provider_data = {"npi": "0000000000", "name": "UNKNOWN"}
        loop_2000a = root.get_loop("2000A")
        if loop_2000a:
            loop_2010aa = loop_2000a.get_loop("2010AA")
            if loop_2010aa:
                nm1 = loop_2010aa.get_segment("NM1")
                if nm1:
                    provider_data["name"] = nm1[3].value if nm1[3] else "UNKNOWN"
                    provider_data["npi"] = nm1[9].value if nm1[9] else "0000000000"

        # Extract subscriber from 2000B/2010BA
        subscriber_data = {
            "member_id": "UNKNOWN",
            "last_name": "UNKNOWN",
            "first_name": "UNKNOWN",
        }
        loop_2000b = None
        if loop_2000a:
            loop_2000b = loop_2000a.get_loop("2000B")
        if loop_2000b:
            loop_2010ba = loop_2000b.get_loop("2010BA")
            if loop_2010ba:
                nm1 = loop_2010ba.get_segment("NM1")
                if nm1:
                    subscriber_data["last_name"] = nm1[3].value if nm1[3] else "UNKNOWN"
                    subscriber_data["first_name"] = nm1[4].value if nm1[4] else "UNKNOWN"
                    subscriber_data["member_id"] = nm1[9].value if nm1[9] else "UNKNOWN"

        # Extract claims from 2300 loops or directly from CLM segments
        claims = []

        def find_claims(loop):
            # Check this loop for CLM segments
            clm = loop.get_segment("CLM")
            if clm:
                claims.append(
                    Claim(
                        claim_id=clm[1].value if clm[1] else "UNKNOWN",
                        total_charge=clm[2].as_decimal() if clm[2] else Decimal(0),
                    )
                )
            # Also check children
            for child in loop.loops:
                if child.loop_id == "2300":
                    clm = child.get_segment("CLM")
                    if clm:
                        claims.append(
                            Claim(
                                claim_id=clm[1].value if clm[1] else "UNKNOWN",
                                total_charge=clm[2].as_decimal() if clm[2] else Decimal(0),
                            )
                        )
                find_claims(child)

        # Search all loops recursively
        find_claims(root)

        # Also search all segments in root for CLM
        for seg in root.segments:
            if seg.segment_id == "CLM":
                claims.append(
                    Claim(
                        claim_id=seg[1].value if seg[1] else "UNKNOWN",
                        total_charge=seg[2].as_decimal() if seg[2] else Decimal(0),
                    )
                )

        return cls(
            billing_provider=Provider(**provider_data),
            subscriber=Subscriber(**subscriber_data),
            claims=claims,
        )

    def to_edi(self, delimiters: Delimiters) -> str:
        """Generate EDI content for this claim.

        Args:
            delimiters: Delimiter configuration.

        Returns:
            EDI segment content.
        """
        d = delimiters
        parts = []

        # BHT - Beginning of Hierarchical Transaction
        parts.append(
            f"BHT*0019*00*{self.claims[0].claim_id if self.claims else 'REF'}*20231127*1200*CH{d.segment}"
        )

        # 2000A - Billing Provider
        parts.append(f"HL*1**20*1{d.segment}")
        parts.append(
            f"NM1*85*2*{self.billing_provider.name}*****XX*{self.billing_provider.npi}{d.segment}"
        )

        # 2000B - Subscriber
        parts.append(f"HL*2*1*22*0{d.segment}")
        parts.append(
            f"NM1*IL*1*{self.subscriber.last_name}*{self.subscriber.first_name}****MI*{self.subscriber.member_id}{d.segment}"
        )

        # 2300 - Claims
        for claim in self.claims:
            parts.append(f"CLM*{claim.claim_id}*{claim.total_charge}***11:B:1*Y*A*Y*Y{d.segment}")

        return "".join(parts)
