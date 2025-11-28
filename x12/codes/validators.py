"""
X12 Code validators.

Provides validation functions for NPI, Tax ID, and medical codes.
"""

from __future__ import annotations


def validate_npi(npi: str) -> bool:
    """Validate NPI (National Provider Identifier).

    NPI must be 10 digits and pass Luhn check with 80840 prefix.

    Args:
        npi: NPI string to validate.

    Returns:
        True if valid, False otherwise.
    """
    # Must be 10 digits
    if not npi or len(npi) != 10 or not npi.isdigit():
        return False

    # Luhn check with 80840 prefix
    # Prepend 80840 to make 15 digits, then apply Luhn
    full_number = "80840" + npi

    total = 0
    for i, digit in enumerate(reversed(full_number)):
        d = int(digit)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d

    return total % 10 == 0


def validate_tax_id(tax_id: str) -> bool:
    """Validate Tax ID (EIN - Employer Identification Number).

    EIN must be 9 digits.

    Args:
        tax_id: Tax ID string to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not tax_id or len(tax_id) != 9:
        return False

    return tax_id.isdigit()


def validate_diagnosis_code(code: str) -> bool:
    """Validate ICD-10 diagnosis code format.

    ICD-10 codes start with a letter, followed by 2-6 alphanumeric characters.
    Format: A00-Z99 with optional additional characters.

    Args:
        code: Diagnosis code to validate.

    Returns:
        True if valid format, False otherwise.
    """
    if not code or len(code) < 3:
        return False

    # Must start with a letter
    if not code[0].isalpha():
        return False

    # Second and third characters must be digits
    if len(code) < 3 or not code[1:3].isdigit():
        return False

    # Remaining characters (if any) must be alphanumeric
    if len(code) > 3 and not code[3:].isalnum():
        return False

    # Max length is typically 7 characters
    return not len(code) > 7


def validate_procedure_code(code: str) -> bool:
    """Validate CPT/HCPCS procedure code format.

    CPT codes are 5 digits.
    HCPCS codes are 1 letter followed by 4 digits.

    Args:
        code: Procedure code to validate.

    Returns:
        True if valid format, False otherwise.
    """
    if not code or len(code) != 5:
        return False

    # CPT: 5 digits
    if code.isdigit():
        return True

    # HCPCS: Letter + 4 digits
    return bool(code[0].isalpha() and code[1:].isdigit())
