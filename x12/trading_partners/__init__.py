"""
X12 Trading partner configuration.

Provides trading partner management and configuration.
"""

from __future__ import annotations

from x12.trading_partners.config import (
    ContactInfo,
    PartnerRegistry,
    TradingPartner,
)

__all__ = [
    "TradingPartner",
    "ContactInfo",
    "PartnerRegistry",
]
