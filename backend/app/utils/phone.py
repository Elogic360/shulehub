import re
import math
import phonenumbers
from typing import Tuple

# GSM 7-bit basic character set
GSM_BASIC_CHARS = set(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`abcdefghijklmnopqrstuvwxyzäöñüà"
)
# GSM extended characters (count as 2 septets / 2 characters)
GSM_EXTENDED_CHARS = set("^{}\\[~]|€")


def normalize_tanzanian_phone(phone_str: str) -> str:
    """
    Normalizes a Tanzanian mobile number to E.164 format (+255XXXXXXXXX).
    Handles variations:
    - 0712345678 -> +255712345678
    - 255712345678 -> +255712345678
    - +255 712 345 678 -> +255712345678
    Raises ValueError if invalid.
    """
    if not phone_str:
        raise ValueError("Phone number cannot be empty")

    cleaned = re.sub(r"[\s\-\(\)]", "", phone_str.strip())

    try:
        parsed = phonenumbers.parse(cleaned, "TZ")
        if not phonenumbers.is_valid_number(parsed):
            # Fallback simple normalization if valid TZ format
            digits = re.sub(r"\D", "", cleaned)
            if digits.startswith("0") and len(digits) == 10:
                digits = "255" + digits[1:]
            elif digits.startswith("255") and len(digits) == 12:
                pass
            else:
                raise ValueError(f"Invalid Tanzanian phone number: {phone_str}")
            return f"+{digits}"
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception as e:
        digits = re.sub(r"\D", "", cleaned)
        if digits.startswith("0") and len(digits) == 10:
            return f"+255{digits[1:]}"
        if digits.startswith("255") and len(digits) == 12:
            return f"+{digits}"
        raise ValueError(f"Invalid Tanzanian phone number: {phone_str}") from e


def calculate_sms_segments(text: str) -> Tuple[int, bool]:
    """
    Calculates number of SMS segments and whether Unicode encoding is required.
    Returns: (segments, is_unicode)
    """
    if not text:
        return 0, False

    is_unicode = False
    gsm_char_count = 0

    for char in text:
        if char in GSM_EXTENDED_CHARS:
            gsm_char_count += 2
        elif char in GSM_BASIC_CHARS:
            gsm_char_count += 1
        else:
            is_unicode = True
            break

    length = len(text)
    if is_unicode:
        if length <= 70:
            return 1, True
        return math.ceil(length / 67), True
    else:
        if gsm_char_count <= 160:
            return 1, False
        return math.ceil(gsm_char_count / 153), False
