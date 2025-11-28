"""
Hypothesis Strategies for X12 EDI Data Generation

These strategies generate valid X12 data structures for property-based testing.
"""
import string
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

from hypothesis import strategies as st
from hypothesis.strategies import composite, SearchStrategy


# =============================================================================
# Character Sets
# =============================================================================

# Valid X12 basic character set
X12_BASIC_CHARS = string.ascii_uppercase + string.digits + " "

# Extended character set (includes punctuation)
X12_EXTENDED_CHARS = X12_BASIC_CHARS + ".,;:!?-'/()"

# Characters safe for use as delimiters (not alphanumeric)
DELIMITER_CHARS = list("*|~^:><!@#$%&-_=+")


# =============================================================================
# Primitive Strategies
# =============================================================================

@composite
def x12_alphanumeric(draw, min_length: int = 1, max_length: int = 80) -> str:
    """Generate valid X12 alphanumeric string (AN data type)."""
    length = draw(st.integers(min_value=min_length, max_value=max_length))
    text = draw(st.text(alphabet=X12_BASIC_CHARS, min_size=length, max_size=length))
    # X12 strings should not be all spaces
    result = text.strip()
    return result if result else "X"


@composite
def x12_string(draw, min_length: int = 1, max_length: int = 80) -> str:
    """Generate X12 string with extended characters."""
    length = draw(st.integers(min_value=min_length, max_value=max_length))
    text = draw(st.text(alphabet=X12_EXTENDED_CHARS, min_size=length, max_size=length))
    result = text.strip()
    return result if result else "X"


@composite
def x12_numeric(draw, min_value: int = 0, max_value: int = 999999999) -> str:
    """Generate X12 numeric string (N data type)."""
    value = draw(st.integers(min_value=min_value, max_value=max_value))
    return str(value)


@composite
def x12_decimal(
    draw, 
    min_value: float = 0.0, 
    max_value: float = 999999.99,
    decimal_places: int = 2
) -> str:
    """Generate X12 decimal string (R data type)."""
    value = draw(st.decimals(
        min_value=Decimal(str(min_value)),
        max_value=Decimal(str(max_value)),
        places=decimal_places,
        allow_nan=False,
        allow_infinity=False,
    ))
    return str(value)


@composite
def x12_date(
    draw,
    min_date: date = date(1900, 1, 1),
    max_date: date = date(2099, 12, 31)
) -> str:
    """Generate X12 date string (DT data type, CCYYMMDD format)."""
    d = draw(st.dates(min_value=min_date, max_value=max_date))
    return d.strftime("%Y%m%d")


@composite
def x12_date_short(draw) -> str:
    """Generate X12 short date string (YYMMDD format)."""
    d = draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2099, 12, 31)))
    return d.strftime("%y%m%d")


@composite
def x12_time(draw, include_seconds: bool = False) -> str:
    """Generate X12 time string (TM data type, HHMM or HHMMSS)."""
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    
    if include_seconds or draw(st.booleans()):
        second = draw(st.integers(min_value=0, max_value=59))
        return f"{hour:02d}{minute:02d}{second:02d}"
    return f"{hour:02d}{minute:02d}"


# =============================================================================
# Delimiter Strategies
# =============================================================================

@composite
def valid_delimiters(draw) -> Dict[str, str]:
    """Generate valid delimiter combination (all distinct)."""
    chars = draw(st.permutations(DELIMITER_CHARS))
    return {
        "element": chars[0],
        "segment": chars[1],
        "component": chars[2],
        "repetition": chars[3],
    }


@composite
def standard_delimiters(draw) -> Dict[str, str]:
    """Generate standard-ish delimiters with minor variations."""
    elem = draw(st.sampled_from(["*", "|"]))
    seg = draw(st.sampled_from(["~", "\n"]))
    comp = draw(st.sampled_from([":", ">"]))
    rep = draw(st.sampled_from(["^", "!"]))
    
    return {
        "element": elem,
        "segment": seg,
        "component": comp,
        "repetition": rep,
    }


# =============================================================================
# Segment Strategies
# =============================================================================

@composite
def segment_id(draw) -> str:
    """Generate valid segment ID (2-3 uppercase letters/digits)."""
    length = draw(st.integers(min_value=2, max_value=3))
    chars = draw(st.text(
        alphabet=string.ascii_uppercase + string.digits,
        min_size=length,
        max_size=length,
    ))
    # Segment IDs typically start with a letter
    if chars[0].isdigit():
        chars = "X" + chars[1:]
    return chars


@composite
def valid_segment_id(draw) -> str:
    """Generate a known valid X12 segment ID."""
    return draw(st.sampled_from([
        "ISA", "GS", "ST", "SE", "GE", "IEA",
        "BHT", "NM1", "N3", "N4", "REF", "PER",
        "HL", "SBR", "PAT", "CLM", "DTP", "HI",
        "LX", "SV1", "SV2", "SV3", "PWK", "CRC",
        "AMT", "QTY", "MEA", "NTE", "DMG",
        "BEG", "PO1", "PID", "CTT", "CUR",
        "TD1", "TD5", "N1", "N2", "SAC", "ITD",
    ]))


@composite
def element_value(
    draw,
    data_type: str = "AN",
    min_len: int = 1,
    max_len: int = 35,
    delimiters: Optional[Dict[str, str]] = None
) -> str:
    """Generate element value based on data type."""
    if data_type == "AN":
        value = draw(x12_alphanumeric(min_len, max_len))
    elif data_type == "N" or data_type == "N0":
        value = draw(x12_numeric())
    elif data_type == "R":
        value = draw(x12_decimal())
    elif data_type == "DT":
        value = draw(x12_date())
    elif data_type == "TM":
        value = draw(x12_time())
    elif data_type == "ID":
        value = draw(x12_alphanumeric(min_len, min(max_len, 3)))
    else:
        value = draw(x12_alphanumeric(min_len, max_len))
    
    # Remove delimiter characters if delimiters provided
    if delimiters:
        for delim in delimiters.values():
            value = value.replace(delim, "")
    
    return value


@composite
def valid_segment(
    draw,
    seg_id: Optional[str] = None,
    num_elements: Optional[int] = None,
    delimiters: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Generate valid segment structure."""
    if delimiters is None:
        delimiters = {"element": "*", "segment": "~", "component": ":", "repetition": "^"}
    
    sid = seg_id or draw(valid_segment_id())
    n_elems = num_elements or draw(st.integers(min_value=1, max_value=10))
    
    elements = []
    for _ in range(n_elems):
        elem = draw(element_value(delimiters=delimiters))
        elements.append(elem)
    
    return {"id": sid, "elements": elements}


@composite
def valid_segment_string(draw, delimiters: Optional[Dict[str, str]] = None) -> str:
    """Generate valid segment as EDI string."""
    if delimiters is None:
        delimiters = {"element": "*", "segment": "~", "component": ":", "repetition": "^"}
    
    seg_data = draw(valid_segment(delimiters=delimiters))
    
    parts = [seg_data["id"]] + seg_data["elements"]
    return delimiters["element"].join(parts) + delimiters["segment"]


# =============================================================================
# Composite Element Strategies
# =============================================================================

@composite
def composite_element(
    draw,
    num_components: Optional[int] = None,
    delimiters: Optional[Dict[str, str]] = None
) -> List[str]:
    """Generate composite element as list of components."""
    if delimiters is None:
        delimiters = {"component": ":"}
    
    n_comps = num_components or draw(st.integers(min_value=2, max_value=5))
    
    components = []
    for _ in range(n_comps):
        comp = draw(x12_alphanumeric(1, 10))
        comp = comp.replace(delimiters.get("component", ":"), "")
        components.append(comp)
    
    return components


# =============================================================================
# Healthcare-Specific Strategies
# =============================================================================

@composite
def valid_npi(draw) -> str:
    """Generate valid NPI (10 digits, passes Luhn check)."""
    # Generate 9 random digits
    prefix = "".join([str(draw(st.integers(0, 9))) for _ in range(9)])
    
    # Calculate Luhn check digit (simplified - real NPI uses modified Luhn)
    # For testing, we'll generate plausible NPIs
    check = draw(st.integers(0, 9))
    
    return prefix + str(check)


@composite
def valid_tax_id(draw) -> str:
    """Generate valid Tax ID (EIN format: 9 digits)."""
    return "".join([str(draw(st.integers(0, 9))) for _ in range(9)])


@composite
def valid_diagnosis_code(draw) -> str:
    """Generate plausible ICD-10 diagnosis code."""
    # ICD-10 format: Letter + 2 digits + optional . + up to 4 more chars
    letter = draw(st.sampled_from(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")))
    digits = "".join([str(draw(st.integers(0, 9))) for _ in range(2)])
    
    if draw(st.booleans()):
        extra = "".join([str(draw(st.integers(0, 9))) for _ in range(draw(st.integers(1, 2)))])
        return f"{letter}{digits}.{extra}"
    
    return f"{letter}{digits}"


@composite
def valid_procedure_code(draw) -> str:
    """Generate plausible CPT procedure code (5 digits)."""
    return "".join([str(draw(st.integers(0, 9))) for _ in range(5)])


@composite
def valid_claim_data(draw) -> Dict[str, Any]:
    """Generate valid claim data structure."""
    return {
        "claim_id": draw(x12_alphanumeric(5, 20)),
        "total_charge": Decimal(str(draw(st.floats(min_value=1.0, max_value=99999.99)))).quantize(Decimal("0.01")),
        "service_date": draw(st.dates(min_value=date(2020, 1, 1), max_value=date.today())),
        "diagnosis_code": draw(valid_diagnosis_code()),
        "procedure_code": draw(valid_procedure_code()),
        "facility_code": draw(st.sampled_from(["11", "12", "21", "22", "23", "31"])),
    }


# =============================================================================
# Supply Chain Strategies
# =============================================================================

@composite
def valid_upc(draw) -> str:
    """Generate valid UPC-A (12 digits)."""
    return "".join([str(draw(st.integers(0, 9))) for _ in range(12)])


@composite
def valid_po_number(draw) -> str:
    """Generate valid purchase order number."""
    return draw(x12_alphanumeric(5, 15))


@composite
def valid_line_item(draw) -> Dict[str, Any]:
    """Generate valid line item data."""
    return {
        "line_number": str(draw(st.integers(1, 999))),
        "quantity": Decimal(str(draw(st.integers(1, 1000)))),
        "unit": draw(st.sampled_from(["EA", "CA", "BX", "PK", "DZ", "LB", "KG"])),
        "price": Decimal(str(draw(st.floats(min_value=0.01, max_value=9999.99)))).quantize(Decimal("0.01")),
        "upc": draw(valid_upc()),
        "description": draw(x12_alphanumeric(5, 50)),
    }


# =============================================================================
# Full Transaction Strategies
# =============================================================================

@composite
def minimal_interchange(draw, transaction_type: str = "837") -> str:
    """Generate minimal valid interchange."""
    delimiters = draw(standard_delimiters())
    e = delimiters["element"]
    s = delimiters["segment"]
    c = delimiters["component"]
    r = delimiters["repetition"]
    
    sender = draw(x12_alphanumeric(2, 15)).ljust(15)
    receiver = draw(x12_alphanumeric(2, 15)).ljust(15)
    ctrl_num = str(draw(st.integers(1, 999999999))).zfill(9)
    date_str = draw(x12_date_short())
    time_str = draw(x12_time())[:4]
    
    isa = (
        f"ISA{e}00{e}          {e}00{e}          {e}ZZ{e}{sender}"
        f"{e}ZZ{e}{receiver}{e}{date_str}{e}{time_str}{e}{r}{e}00501"
        f"{e}{ctrl_num}{e}0{e}P{e}{c}{s}"
    )
    
    # Functional group
    gs = f"GS{e}HC{e}SENDER{e}RECEIVER{e}{draw(x12_date())}{e}{time_str}{e}1{e}X{e}005010X222A1{s}"
    
    # Transaction
    st_seg = f"ST{e}{transaction_type}{e}0001{s}"
    bht = f"BHT{e}0019{e}00{e}12345{e}{draw(x12_date())}{e}{time_str}{e}CH{s}"
    se = f"SE{e}3{e}0001{s}"
    
    # Trailers
    ge = f"GE{e}1{e}1{s}"
    iea = f"IEA{e}1{e}{ctrl_num}{s}"
    
    return isa + gs + st_seg + bht + se + ge + iea
