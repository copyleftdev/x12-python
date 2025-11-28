"""
Streaming readers for X12 EDI.

Provides memory-efficient processing of large EDI files.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from x12.core.delimiters import Delimiters


@dataclass
class StreamingSegment:
    """A segment read from a stream."""

    segment_id: str
    raw: str
    position: int


class StreamingSegmentReader:
    """Memory-efficient segment reader for large EDI files.

    Reads segments one at a time without loading entire file.

    Example:
        >>> with open("large.edi") as f:
        ...     reader = StreamingSegmentReader(f)
        ...     for segment in reader:
        ...         print(segment.segment_id)
    """

    def __init__(
        self,
        source: TextIO | str | Path,
        delimiters: Delimiters | None = None,
        buffer_size: int = 4096,
    ) -> None:
        """Initialize streaming reader.

        Args:
            source: File handle, string content, or Path.
            delimiters: Delimiter configuration. Auto-detected if None.
            buffer_size: Read buffer size in bytes.
        """
        self._buffer_size = buffer_size
        self._position = 0
        self._buffer = ""
        self._delimiters = delimiters
        self._isa_detected = False
        self._path: Path | None = None
        self._content: str | None = None
        self._source: TextIO | None = None

        # Handle different source types
        if isinstance(source, str):
            self._content = source
        elif isinstance(source, Path):
            self._path = source
        elif hasattr(source, "read"):
            self._source = source
        else:
            self._content = str(source)

    @property
    def delimiters(self) -> Delimiters:
        """Get delimiters (auto-detected from ISA if needed)."""
        if self._delimiters is None:
            from x12.core.delimiters import Delimiters

            self._delimiters = Delimiters()
        return self._delimiters

    def __iter__(self) -> Iterator[StreamingSegment]:
        """Iterate over segments."""
        return self._read_segments()

    def segments(self) -> Iterator[StreamingSegment]:
        """Iterate over segments (alias for __iter__)."""
        return self._read_segments()

    def _read_segments(self) -> Iterator[StreamingSegment]:
        """Read and yield segments one at a time with bounded memory."""

        # If we have string content, process it directly
        if self._content is not None:
            yield from self._read_from_string(self._content)
            return

        # For files, use chunked reading
        if self._path is not None:
            with open(self._path) as f:
                yield from self._read_from_file(f)
            return

        if self._source is not None:
            yield from self._read_from_file(self._source)
            return

    def _read_from_file(self, f: TextIO) -> Iterator[StreamingSegment]:
        """Stream segments from a file handle with bounded memory."""
        from x12.core.delimiters import Delimiters

        # Read first 106 chars to detect delimiters from ISA
        header = f.read(106)
        if not header:
            return

        if self._delimiters is None and header.startswith("ISA"):
            self._delimiters = Delimiters.from_isa(header)
        elif self._delimiters is None:
            self._delimiters = Delimiters()

        segment_term = self._delimiters.segment
        elem_sep = self._delimiters.element

        # Process in chunks
        buffer = header
        position = 0

        while True:
            # Find next segment terminator
            term_pos = buffer.find(segment_term)

            if term_pos == -1:
                # Read more data
                chunk = f.read(self._buffer_size)
                if not chunk:
                    # End of file - process remaining buffer
                    if buffer.strip():
                        seg_str = buffer.strip()
                        seg_id = (
                            seg_str[: seg_str.index(elem_sep)] if elem_sep in seg_str else seg_str
                        )
                        yield StreamingSegment(segment_id=seg_id, raw=seg_str, position=position)
                    break
                buffer += chunk
                continue

            # Extract segment
            seg_str = buffer[:term_pos].strip()
            buffer = buffer[term_pos + len(segment_term) :]

            if seg_str:
                seg_id = seg_str[: seg_str.index(elem_sep)] if elem_sep in seg_str else seg_str
                yield StreamingSegment(segment_id=seg_id, raw=seg_str, position=position)

            position += len(seg_str) + len(segment_term)

    def _read_from_string(self, content: str) -> Iterator[StreamingSegment]:
        """Process string content."""
        from x12.core.delimiters import Delimiters

        # Auto-detect delimiters from ISA
        if self._delimiters is None and content.startswith("ISA"):
            self._delimiters = Delimiters.from_isa(content)
        elif self._delimiters is None:
            self._delimiters = Delimiters()

        segment_term = self._delimiters.segment
        elem_sep = self._delimiters.element

        # Handle multi-char terminators like \r\n
        if segment_term in ("\r\n", "\n"):
            segments = content.replace("\r\n", "\n").split("\n")
        else:
            segments = content.split(segment_term)

        position = 0
        for seg_str in segments:
            seg_str = seg_str.strip()
            if not seg_str:
                continue

            seg_id = seg_str[: seg_str.index(elem_sep)] if elem_sep in seg_str else seg_str

            yield StreamingSegment(
                segment_id=seg_id,
                raw=seg_str,
                position=position,
            )

            position += len(seg_str) + len(segment_term)


class StreamingTransactionParser:
    """Memory-efficient transaction parser for large EDI files.

    Parses transactions one at a time without loading entire file.

    Example:
        >>> with open("large.edi") as f:
        ...     parser = StreamingTransactionParser(f)
        ...     for txn in parser:
        ...         process(txn)
    """

    def __init__(
        self,
        source: TextIO | str | Path | StreamingSegmentReader,
        delimiters: Delimiters | None = None,
    ) -> None:
        """Initialize streaming parser.

        Args:
            source: File handle, string content, Path, or StreamingSegmentReader.
            delimiters: Delimiter configuration. Auto-detected if None.
        """
        if isinstance(source, StreamingSegmentReader):
            self._reader = source
        else:
            self._reader = StreamingSegmentReader(source, delimiters)
        self._current_transaction: list = []
        self._in_transaction = False

    def __iter__(self) -> Iterator[list[StreamingSegment]]:
        """Iterate over transactions (as lists of segments)."""
        return self._read_transactions()

    def transactions(self) -> Iterator[list[StreamingSegment]]:
        """Iterate over transactions (alias for __iter__)."""
        return self._read_transactions()

    def _read_transactions(self) -> Iterator[list[StreamingSegment]]:
        """Read and yield transactions one at a time."""
        current_txn: list[StreamingSegment] = []

        for segment in self._reader:
            if segment.segment_id == "ST":
                # Start new transaction
                if current_txn:
                    yield current_txn
                current_txn = [segment]
            elif segment.segment_id == "SE":
                # End transaction
                current_txn.append(segment)
                yield current_txn
                current_txn = []
            elif current_txn or segment.segment_id in ("ISA", "GS", "GE", "IEA"):
                # Add to current transaction or envelope
                current_txn.append(segment)

        # Yield any remaining segments
        if current_txn:
            yield current_txn
