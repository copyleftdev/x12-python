"""
X12 Schema definitions and loading.

Provides schema structures for X12 transaction validation.
"""
from __future__ import annotations

from x12.schema.definitions import (
    ElementDefinition,
    SegmentDefinition,
    LoopDefinition,
    TransactionSchema,
)
from x12.schema.loader import SchemaLoader

__all__ = [
    "ElementDefinition",
    "SegmentDefinition",
    "LoopDefinition",
    "TransactionSchema",
    "SchemaLoader",
]
