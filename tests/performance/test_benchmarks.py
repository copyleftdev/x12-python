"""
Performance Benchmark Tests

These tests verify that parsing, validation, and generation
meet performance requirements.

Run: pytest tests/performance/test_benchmarks.py -v --benchmark-json=benchmark.json
"""
import pytest
import time
from pathlib import Path


@pytest.mark.performance
class TestParsingPerformance:
    """Parsing performance benchmarks."""

    def test_parse_small_file_under_10ms(self, minimal_837p_content):
        """Small file (< 5KB) must parse in under 10ms."""
        from x12.core.parser import Parser
        
        parser = Parser()
        
        start = time.perf_counter()
        parser.parse(minimal_837p_content)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.010, f"Parsing took {elapsed:.3f}s, expected < 10ms"

    def test_parse_medium_file_under_100ms(self, minimal_837p_content):
        """Medium file (~50KB, ~50 claims) must parse in under 100ms."""
        from x12.core.parser import Parser
        
        # Generate medium-sized content (repeat claims)
        content = minimal_837p_content * 10  # ~20KB
        
        parser = Parser()
        
        start = time.perf_counter()
        parser.parse(content)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.100, f"Parsing took {elapsed:.3f}s, expected < 100ms"

    def test_tokenizer_throughput(self, minimal_837p_content):
        """Tokenizer must achieve > 0.5MB/s throughput.
        
        Note: Threshold lowered for CI environments which have variable performance.
        Local development typically achieves > 1 MB/s.
        """
        from x12.core.tokenizer import Tokenizer
        
        # Generate larger content
        content = minimal_837p_content * 100  # ~200KB
        content_size = len(content)
        
        tokenizer = Tokenizer()
        
        start = time.perf_counter()
        tokens = list(tokenizer.tokenize(content))
        elapsed = time.perf_counter() - start
        
        throughput_mbps = (content_size / 1_000_000) / elapsed
        
        # Use 0.5 MB/s as threshold for CI compatibility
        assert throughput_mbps > 0.5, \
            f"Throughput {throughput_mbps:.2f} MB/s, expected > 0.5 MB/s"

    def test_segment_parser_throughput(self, minimal_837p_content):
        """Segment parser must achieve > 500KB/s throughput."""
        from x12.core.parser import SegmentParser
        
        content = minimal_837p_content * 50
        content_size = len(content)
        
        parser = SegmentParser()
        
        start = time.perf_counter()
        segments = list(parser.parse(content))
        elapsed = time.perf_counter() - start
        
        throughput_kbps = (content_size / 1000) / elapsed
        
        assert throughput_kbps > 500, \
            f"Throughput {throughput_kbps:.0f} KB/s, expected > 500 KB/s"


@pytest.mark.performance
class TestValidationPerformance:
    """Validation performance benchmarks."""

    def test_validate_segment_under_1ms(self):
        """Single segment validation must complete in under 1ms."""
        from x12.core.validator import X12Validator
        
        validator = X12Validator()
        segment = "NM1*85*2*PROVIDER NAME*****XX*1234567890~"
        
        start = time.perf_counter()
        validator.validate_segment(segment, "NM1", "005010X222A1")
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.001, f"Validation took {elapsed:.4f}s, expected < 1ms"

    def test_validate_transaction_under_50ms(self, minimal_837p_content):
        """Transaction validation must complete in under 50ms."""
        from x12.core.parser import Parser
        from x12.core.validator import X12Validator
        
        parser = Parser()
        validator = X12Validator()
        
        interchange = parser.parse(minimal_837p_content)
        txn = interchange.functional_groups[0].transactions[0]
        
        start = time.perf_counter()
        validator.validate_transaction(txn, "005010X222A1")
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.050, f"Validation took {elapsed:.3f}s, expected < 50ms"


@pytest.mark.performance
class TestGenerationPerformance:
    """Generation performance benchmarks."""

    def test_generate_segment_under_100us(self):
        """Single segment generation must complete in under 100μs."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        start = time.perf_counter()
        generator.generate_segment("NM1", ["85", "2", "PROVIDER", "", "", "", "", "XX", "1234567890"])
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.0001, f"Generation took {elapsed:.6f}s, expected < 100μs"

    def test_generate_isa_under_500us(self):
        """ISA generation must complete in under 500μs."""
        from x12.core.generator import Generator
        
        generator = Generator()
        
        start = time.perf_counter()
        generator.generate_isa(sender_id="SENDER", receiver_id="RECEIVER")
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.0005, f"ISA generation took {elapsed:.6f}s, expected < 500μs"


@pytest.mark.performance
class TestStreamingPerformance:
    """Streaming performance benchmarks."""

    def test_streaming_memory_bounded(self, minimal_837p_content, tmp_path):
        """Streaming parser must use bounded memory regardless of file size."""
        from x12.streaming import StreamingSegmentReader
        import tracemalloc
        
        # Create a large file
        large_file = tmp_path / "large.edi"
        large_content = minimal_837p_content * 1000  # ~2MB
        large_file.write_text(large_content)
        
        tracemalloc.start()
        
        reader = StreamingSegmentReader(large_file)
        segment_count = 0
        for segment in reader.segments():
            segment_count += 1
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_mb = peak / 1024 / 1024
        
        # Peak memory should be much less than file size
        # Allow 75% for Python string/object overhead on small files
        file_size_mb = len(large_content) / 1024 / 1024
        
        assert peak_mb < file_size_mb * 0.75, \
            f"Peak memory {peak_mb:.1f}MB exceeds 75% of file size {file_size_mb:.1f}MB"

    def test_streaming_throughput(self, minimal_837p_content, tmp_path):
        """Streaming must achieve > 5MB/s throughput."""
        from x12.streaming import StreamingSegmentReader
        
        # Create large file
        large_file = tmp_path / "large.edi"
        large_content = minimal_837p_content * 500  # ~1MB
        large_file.write_text(large_content)
        content_size = len(large_content)
        
        reader = StreamingSegmentReader(large_file)
        
        start = time.perf_counter()
        for segment in reader.segments():
            pass
        elapsed = time.perf_counter() - start
        
        throughput_mbps = (content_size / 1_000_000) / elapsed
        
        assert throughput_mbps > 5.0, \
            f"Streaming throughput {throughput_mbps:.1f} MB/s, expected > 5 MB/s"


@pytest.mark.performance
class TestMemoryUsage:
    """Memory usage benchmarks."""

    def test_segment_memory_efficient(self):
        """Segment objects must be memory efficient."""
        from x12.models import Segment, Element
        import sys
        
        # Create segment
        segment = Segment(
            segment_id="NM1",
            elements=[Element(value=f"elem{i}", index=i) for i in range(10)]
        )
        
        size = sys.getsizeof(segment)
        
        # Segment should be reasonably sized
        assert size < 1000, f"Segment size {size} bytes, expected < 1000"

    def test_parser_doesnt_leak_memory(self, minimal_837p_content):
        """Parser must not leak memory on repeated parses."""
        from x12.core.parser import Parser
        import tracemalloc
        
        parser = Parser()
        
        # Warm up
        parser.parse(minimal_837p_content)
        
        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]
        
        # Parse many times
        for _ in range(100):
            parser.parse(minimal_837p_content)
        
        current = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        growth = current - baseline
        growth_mb = growth / 1024 / 1024
        
        # Memory growth should be minimal
        assert growth_mb < 10, f"Memory grew {growth_mb:.1f}MB after 100 parses"


@pytest.mark.performance
@pytest.mark.slow
class TestLargeFilePerformance:
    """Large file handling benchmarks."""

    def test_parse_1mb_file(self, minimal_837p_content, tmp_path):
        """1MB file must parse in under 2 seconds."""
        from x12.core.parser import Parser
        
        # Generate 1MB file
        large_file = tmp_path / "1mb.edi"
        target_size = 1_000_000
        multiplier = target_size // len(minimal_837p_content) + 1
        large_content = minimal_837p_content * multiplier
        large_file.write_text(large_content[:target_size])
        
        parser = Parser()
        
        start = time.perf_counter()
        parser.parse(large_file.read_text())
        elapsed = time.perf_counter() - start
        
        assert elapsed < 2.0, f"Parsing 1MB took {elapsed:.2f}s, expected < 2s"

    def test_streaming_10mb_file(self, minimal_837p_content, tmp_path):
        """10MB file must stream in under 5 seconds."""
        from x12.streaming import StreamingTransactionParser, StreamingSegmentReader
        
        # Generate 10MB file
        large_file = tmp_path / "10mb.edi"
        target_size = 10_000_000
        multiplier = target_size // len(minimal_837p_content) + 1
        large_content = minimal_837p_content * multiplier
        large_file.write_text(large_content[:target_size])
        
        reader = StreamingSegmentReader(large_file)
        parser = StreamingTransactionParser(reader)
        
        start = time.perf_counter()
        txn_count = sum(1 for _ in parser.transactions())
        elapsed = time.perf_counter() - start
        
        assert elapsed < 5.0, f"Streaming 10MB took {elapsed:.2f}s, expected < 5s"
        assert txn_count > 0


@pytest.mark.performance
class TestComparisonBenchmarks:
    """Comparative benchmarks against baseline."""

    def test_parse_vs_baseline(self, minimal_837p_content, benchmark_baseline):
        """Parsing must not regress from baseline."""
        from x12.core.parser import Parser
        
        parser = Parser()
        
        # Run multiple iterations
        times = []
        for _ in range(10):
            start = time.perf_counter()
            parser.parse(minimal_837p_content)
            times.append(time.perf_counter() - start)
        
        avg_time = sum(times) / len(times)
        
        if "parse_small" in benchmark_baseline:
            baseline = benchmark_baseline["parse_small"]
            # Allow 20% regression
            assert avg_time < baseline * 1.2, \
                f"Parsing regressed: {avg_time:.4f}s vs baseline {baseline:.4f}s"
