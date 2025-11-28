# Contributing to X12 EDI Tools

Thank you for your interest in contributing to X12 EDI Tools! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build great software.

## Getting Started

### Prerequisites

- Python 3.10+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/donjohnson/x12-edi-tools.git
cd x12-edi-tools

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

## Development Workflow

### Test-Driven Development (TDD)

This project follows strict TDD. **All code changes must follow the RED-GREEN-REFACTOR cycle:**

1. **RED**: Write a failing test first
2. **GREEN**: Write minimal code to make it pass
3. **REFACTOR**: Clean up while keeping tests green

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=x12 --cov-report=term-missing

# Run specific test types
pytest tests/unit -v
pytest tests/integration -v
pytest tests/property -v
pytest tests/compliance -v
pytest tests/performance -v
```

### Code Quality

Before submitting, ensure your code passes all quality checks:

```bash
# Linting
ruff check x12/
ruff format x12/

# Type checking
mypy x12/ --strict
```

## Making Changes

### Branch Naming

- `feat/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `test/description` - Test additions/changes

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add 837D dental claim support
fix: handle empty trailing elements in segment parser
test: add property tests for roundtrip invariants
docs: update README with streaming examples
refactor: extract loop builder from parser
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Write tests for your changes (TDD!)
4. Implement your changes
5. Ensure all tests pass
6. Update documentation if needed
7. Submit a pull request

### PR Checklist

- [ ] Tests written and passing
- [ ] Coverage maintained (≥80%)
- [ ] Code passes `ruff check`
- [ ] Type hints added for public APIs
- [ ] Docstrings for public functions/classes
- [ ] CHANGELOG.md updated (if applicable)

## Testing Guidelines

### Test Organization

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Multi-component tests
├── property/       # Hypothesis property tests
├── compliance/     # Standards compliance
└── performance/    # Benchmarks
```

### Writing Tests

```python
@pytest.mark.unit
class TestMyFeature:
    """Tests for my feature."""

    def test_basic_functionality(self):
        """Must do the basic thing."""
        result = my_function()
        assert result == expected

    def test_edge_case(self):
        """Must handle edge case."""
        with pytest.raises(ValueError):
            my_function(invalid_input)
```

### Test Requirements

- Minimum 80% overall coverage
- 100% coverage for public APIs
- No real patient data (PHI) in tests
- Use synthetic/fake data only

## Code Style

### Python Standards

- Follow PEP 8
- Line length: 100 characters
- Use type hints for all public APIs
- Use Google-style docstrings

### Example

```python
def parse_segment(
    content: str,
    delimiters: Delimiters,
    strict: bool = False,
) -> Segment:
    """Parse an EDI segment from string content.

    Args:
        content: Raw EDI segment string.
        delimiters: Delimiter configuration.
        strict: If True, raise on validation errors.

    Returns:
        Parsed Segment object.

    Raises:
        ParseError: If content cannot be parsed.
    """
```

## Adding New Features

### New Transaction Type

1. Add schema in `x12/schema/loader.py`
2. Add models in `x12/transactions/`
3. Add tests in `tests/unit/`
4. Update README if significant

### New Code Set

1. Add to `x12/codes/registry.py`
2. Add tests in `tests/unit/test_codes.py`

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
