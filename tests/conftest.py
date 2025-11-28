"""
Shared pytest fixtures for X12 EDI testing.

This module provides fixtures used across all test modules.
Fixtures are designed to support TDD - they define expected interfaces
before implementation exists.
"""
import pytest
from pathlib import Path
from typing import Dict, Any, List
from datetime import date
from decimal import Decimal


# =============================================================================
# Path Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def valid_edi_dir(fixtures_dir: Path) -> Path:
    """Directory containing valid EDI sample files."""
    path = fixtures_dir / "edi" / "valid"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def invalid_edi_dir(fixtures_dir: Path) -> Path:
    """Directory containing invalid EDI sample files."""
    path = fixtures_dir / "edi" / "invalid"
    path.mkdir(parents=True, exist_ok=True)
    return path


# =============================================================================
# Delimiter Fixtures
# =============================================================================

@pytest.fixture
def standard_delimiters() -> Dict[str, str]:
    """Standard X12 delimiters as dict (for pre-implementation tests)."""
    return {
        "element": "*",
        "segment": "~",
        "component": ":",
        "repetition": "^",
    }


@pytest.fixture
def pipe_delimiters() -> Dict[str, str]:
    """Alternative pipe-based delimiters."""
    return {
        "element": "|",
        "segment": "~",
        "component": ">",
        "repetition": "^",
    }


@pytest.fixture(params=[
    {"element": "*", "segment": "~", "component": ":", "repetition": "^"},
    {"element": "|", "segment": "~", "component": ">", "repetition": "^"},
    {"element": "*", "segment": "\n", "component": ":", "repetition": "^"},
    {"element": "\t", "segment": "~", "component": ":", "repetition": "!"},
])
def various_delimiters(request) -> Dict[str, str]:
    """Parametrized fixture for testing multiple delimiter combinations."""
    return request.param


# =============================================================================
# ISA Segment Fixtures
# =============================================================================

@pytest.fixture
def minimal_isa_segment() -> str:
    """Minimal valid ISA segment (106 characters, standard delimiters)."""
    return (
        "ISA*00*          *00*          *ZZ*SENDER         "
        "*ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~"
    )


@pytest.fixture
def isa_with_pipe_delimiters() -> str:
    """ISA segment using pipe delimiters."""
    return (
        "ISA|00|          |00|          |ZZ|SENDER         "
        "|ZZ|RECEIVER       |231127|1200|^|00501|000000001|0|P|>~"
    )


@pytest.fixture
def isa_with_newline_terminator() -> str:
    """ISA segment using newline as segment terminator."""
    return (
        "ISA*00*          *00*          *ZZ*SENDER         "
        "*ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:\n"
    )


# =============================================================================
# Sample EDI Content Fixtures
# =============================================================================

@pytest.fixture
def minimal_837p_content() -> str:
    """Minimal valid 837P professional claim transaction."""
    return """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~
GS*HC*SENDER*RECEIVER*20231127*1200*1*X*005010X222A1~
ST*837*0001*005010X222A1~
BHT*0019*00*244579*20231127*1200*CH~
NM1*41*2*SUBMITTER NAME*****46*123456789~
PER*IC*CONTACT NAME*TE*5551234567~
NM1*40*2*RECEIVER NAME*****46*987654321~
HL*1**20*1~
NM1*85*2*BILLING PROVIDER*****XX*1234567890~
N3*123 MAIN ST~
N4*ANYTOWN*NY*12345~
REF*EI*123456789~
HL*2*1*22*0~
SBR*P*18*******CI~
NM1*IL*1*DOE*JOHN****MI*ABC123456~
N3*456 OAK AVE~
N4*SOMEWHERE*CA*90210~
DMG*D8*19800115*M~
NM1*PR*2*INSURANCE CO*****PI*12345~
CLM*CLAIM001*150***11:B:1*Y*A*Y*Y~
HI*ABK:M545~
LX*1~
SV1*HC:99213*150*UN*1***1~
DTP*472*D8*20231115~
SE*24*0001~
GE*1*1~
IEA*1*000000001~"""


@pytest.fixture
def minimal_850_content() -> str:
    """Minimal valid 850 purchase order transaction."""
    return """ISA*00*          *00*          *ZZ*BUYER          *ZZ*SELLER         *231127*1200*^*00401*000000001*0*P*:~
GS*PO*BUYER*SELLER*20231127*1200*1*X*004010~
ST*850*0001~
BEG*00*SA*PO123456**20231127~
N1*ST*SHIP TO LOCATION*92*SHIPTO001~
N3*789 WAREHOUSE DR~
N4*DISTRIBUTION*TX*75001~
PO1*1*10*EA*25.00**UP*012345678901~
PID*F****WIDGET BLUE~
PO1*2*5*EA*50.00**UP*012345678902~
PID*F****GADGET RED~
CTT*2~
SE*12*0001~
GE*1*1~
IEA*1*000000001~"""


@pytest.fixture
def minimal_835_content() -> str:
    """Minimal valid 835 remittance advice transaction."""
    return """ISA*00*          *00*          *ZZ*PAYER          *ZZ*PAYEE          *231127*1200*^*00501*000000001*0*P*:~
GS*HP*PAYER*PAYEE*20231127*1200*1*X*005010X221A1~
ST*835*0001~
BPR*I*150.00*C*ACH*CTX*01*123456789*DA*123456789*9876543210**01*111111111*DA*222222222*20231201~
TRN*1*12345*1512345678~
N1*PR*INSURANCE COMPANY~
N1*PE*PROVIDER NAME*XX*1234567890~
LX*1~
CLP*CLAIM001*1*150*150*0*12*CLAIMREF*11*1~
NM1*QC*1*DOE*JOHN~
SVC*HC:99213*150*150*UN*1~
DTM*472*20231115~
SE*13*0001~
GE*1*1~
IEA*1*000000001~"""


@pytest.fixture
def minimal_270_content() -> str:
    """Minimal valid 270 eligibility inquiry transaction."""
    return """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~
GS*HS*SENDER*RECEIVER*20231127*1200*1*X*005010X279A1~
ST*270*0001*005010X279A1~
BHT*0022*13*10001234*20231127*1200~
HL*1**20*1~
NM1*PR*2*PAYER NAME*****PI*12345~
HL*2*1*21*1~
NM1*1P*2*PROVIDER NAME*****XX*1234567890~
HL*3*2*22*0~
NM1*IL*1*DOE*JOHN****MI*ABC123456~
DMG*D8*19800115~
EQ*30~
SE*12*0001~
GE*1*1~
IEA*1*000000001~"""


@pytest.fixture
def minimal_856_content() -> str:
    """Minimal valid 856 advance ship notice transaction."""
    return """ISA*00*          *00*          *ZZ*SELLER         *ZZ*BUYER          *231127*1200*^*00401*000000001*0*P*:~
GS*SH*SELLER*BUYER*20231127*1200*1*X*004010~
ST*856*0001~
BSN*00*SHIPMENT001*20231127*1200*0001~
HL*1**S~
TD1*CTN*10****G*150*LB~
TD5**2*UPSN*M~
REF*BM*BOL123456~
DTM*011*20231127~
N1*SF*SHIP FROM NAME*92*SHIPFROM001~
N3*123 ORIGIN ST~
N4*ORIGINCITY*CA*90001~
N1*ST*SHIP TO NAME*92*SHIPTO001~
N3*456 DEST AVE~
N4*DESTCITY*TX*75001~
HL*2*1*O~
PRF*PO123456~
HL*3*2*I~
LIN**UP*012345678901~
SN1**10*EA~
SE*20*0001~
GE*1*1~
IEA*1*000000001~"""


# =============================================================================
# Segment Test Data Fixtures
# =============================================================================

@pytest.fixture
def nm1_billing_provider_segment() -> str:
    """NM1 segment for billing provider (entity code 85)."""
    return "NM1*85*2*ACME MEDICAL GROUP*****XX*1234567890~"


@pytest.fixture
def nm1_subscriber_segment() -> str:
    """NM1 segment for subscriber (entity code IL)."""
    return "NM1*IL*1*DOE*JOHN*M***MI*ABC123456789~"


@pytest.fixture
def nm1_patient_segment() -> str:
    """NM1 segment for patient (entity code QC)."""
    return "NM1*QC*1*DOE*JANE*A~"


@pytest.fixture
def clm_segment() -> str:
    """CLM (claim) segment."""
    return "CLM*CLAIM12345*1500***11:B:1*Y*A*Y*Y~"


@pytest.fixture
def sv1_segment() -> str:
    """SV1 (professional service) segment with composite."""
    return "SV1*HC:99214:25*150*UN*1***1:2:3:4~"


@pytest.fixture
def hi_segment() -> str:
    """HI (health care information/diagnosis) segment."""
    return "HI*ABK:M5450*ABF:Z7389*ABF:E1165~"


@pytest.fixture
def dtp_segment() -> str:
    """DTP (date/time) segment."""
    return "DTP*472*D8*20231115~"


# =============================================================================
# Model Data Fixtures (for testing model construction)
# =============================================================================

@pytest.fixture
def sample_claim_data() -> Dict[str, Any]:
    """Sample data for constructing a claim model."""
    return {
        "claim_id": "TEST001",
        "total_charge": Decimal("150.00"),
        "facility_code": "11",
        "facility_qualifier": "B",
        "frequency_code": "1",
        "statement_from_date": date(2023, 11, 15),
        "statement_to_date": date(2023, 11, 15),
        "principal_diagnosis": {"code": "M54.5", "qualifier": "ABK"},
        "service_lines": [
            {
                "line_number": 1,
                "procedure_code": "99213",
                "charge_amount": Decimal("150.00"),
                "units": Decimal("1"),
                "service_date": date(2023, 11, 15),
                "diagnosis_pointers": [1],
            }
        ],
    }


@pytest.fixture
def sample_provider_data() -> Dict[str, Any]:
    """Sample data for constructing a provider model."""
    return {
        "npi": "1234567890",
        "tax_id": "123456789",
        "name": "ACME MEDICAL GROUP",
        "address": {
            "line1": "123 MAIN STREET",
            "city": "ANYTOWN",
            "state": "NY",
            "postal_code": "12345",
        },
        "taxonomy_code": "207Q00000X",
    }


@pytest.fixture
def sample_subscriber_data() -> Dict[str, Any]:
    """Sample data for constructing a subscriber model."""
    return {
        "member_id": "ABC123456789",
        "last_name": "DOE",
        "first_name": "JOHN",
        "middle_name": "M",
        "date_of_birth": date(1980, 1, 15),
        "gender": "M",
        "address": {
            "line1": "456 OAK AVENUE",
            "city": "SOMEWHERE",
            "state": "CA",
            "postal_code": "90210",
        },
    }


@pytest.fixture
def sample_purchase_order_data() -> Dict[str, Any]:
    """Sample data for constructing a purchase order model."""
    return {
        "po_number": "PO123456",
        "po_date": date(2023, 11, 27),
        "buyer": {
            "name": "ACME CORP",
            "id": "BUYER001",
        },
        "seller": {
            "name": "WIDGET SUPPLY CO",
            "id": "SELLER001",
        },
        "ship_to": {
            "name": "ACME WAREHOUSE",
            "address": {
                "line1": "789 WAREHOUSE DR",
                "city": "DISTRIBUTION",
                "state": "TX",
                "postal_code": "75001",
            },
        },
        "line_items": [
            {
                "line_number": "1",
                "quantity": Decimal("10"),
                "unit": "EA",
                "price": Decimal("25.00"),
                "upc": "012345678901",
                "description": "WIDGET BLUE",
            },
            {
                "line_number": "2",
                "quantity": Decimal("5"),
                "unit": "EA",
                "price": Decimal("50.00"),
                "upc": "012345678902",
                "description": "GADGET RED",
            },
        ],
    }


# =============================================================================
# Validation Fixtures
# =============================================================================

@pytest.fixture
def valid_npi_numbers() -> List[str]:
    """List of valid NPI numbers for testing."""
    return [
        "1234567890",
        "1111111112",
        "9876543210",
    ]


@pytest.fixture
def invalid_npi_numbers() -> List[str]:
    """List of invalid NPI numbers for testing."""
    return [
        "123456789",   # Too short
        "12345678901", # Too long
        "ABCDEFGHIJ",  # Non-numeric
        "0000000000",  # Invalid check digit
    ]


@pytest.fixture
def valid_diagnosis_codes() -> List[str]:
    """List of valid ICD-10 diagnosis codes."""
    return [
        "M54.5",   # Low back pain
        "J06.9",   # Acute upper respiratory infection
        "E11.65",  # Type 2 diabetes with hyperglycemia
        "Z00.00",  # General examination
    ]


@pytest.fixture
def valid_procedure_codes() -> List[str]:
    """List of valid CPT procedure codes."""
    return [
        "99213",  # Office visit, established patient, level 3
        "99214",  # Office visit, established patient, level 4
        "99203",  # Office visit, new patient, level 3
        "90834",  # Psychotherapy, 45 minutes
    ]


# =============================================================================
# Error Case Fixtures
# =============================================================================

@pytest.fixture
def edi_missing_isa() -> str:
    """EDI content missing ISA segment."""
    return "GS*HC*SENDER*RECEIVER*20231127*1200*1*X*005010X222A1~ST*837*0001~SE*2*0001~GE*1*1~"


@pytest.fixture
def edi_missing_gs() -> str:
    """EDI content missing GS segment."""
    return "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~ST*837*0001~SE*2*0001~IEA*1*000000001~"


@pytest.fixture
def edi_mismatched_control_numbers() -> str:
    """EDI with mismatched ST/SE control numbers."""
    return """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~
GS*HC*SENDER*RECEIVER*20231127*1200*1*X*005010X222A1~
ST*837*0001~
BHT*0019*00*244579*20231127*1200*CH~
SE*2*9999~
GE*1*1~
IEA*1*000000001~"""


@pytest.fixture
def edi_invalid_segment_count() -> str:
    """EDI with incorrect segment count in SE01."""
    return """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231127*1200*^*00501*000000001*0*P*:~
GS*HC*SENDER*RECEIVER*20231127*1200*1*X*005010X222A1~
ST*837*0001~
BHT*0019*00*244579*20231127*1200*CH~
SE*99*0001~
GE*1*1~
IEA*1*000000001~"""


# =============================================================================
# Performance Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def benchmark_baseline() -> Dict[str, float]:
    """Baseline timing data for performance comparisons.
    
    These values represent acceptable performance targets.
    Actual baselines should be measured on consistent hardware.
    """
    return {
        "parse_small": 0.01,  # 10ms for small file
        "parse_large": 0.5,   # 500ms for large file
        "validate_small": 0.005,  # 5ms for validation
        "generate_small": 0.002,  # 2ms for generation
    }


# =============================================================================
# Pytest Hooks
# =============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: Fast isolated unit tests")
    config.addinivalue_line("markers", "integration: Multi-component tests")
    config.addinivalue_line("markers", "property: Hypothesis property-based tests")
    config.addinivalue_line("markers", "compliance: Standards compliance tests")
    config.addinivalue_line("markers", "hipaa: HIPAA-specific compliance tests")
    config.addinivalue_line("markers", "regression: Bug regression tests")
    config.addinivalue_line("markers", "performance: Performance benchmark tests")
    config.addinivalue_line("markers", "slow: Slow tests (> 1 second)")
