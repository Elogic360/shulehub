import pytest
from app.utils.phone import normalize_tanzanian_phone, calculate_sms_segments


def test_tanzanian_phone_normalization_valid():
    # Standard 07xx numbers
    assert normalize_tanzanian_phone("0712345678") == "+255712345678"
    assert normalize_tanzanian_phone("0754123456") == "+255754123456"
    assert normalize_tanzanian_phone("0684123456") == "+255684123456"

    # Already prefixed with 255
    assert normalize_tanzanian_phone("255712345678") == "+255712345678"
    assert normalize_tanzanian_phone("+255712345678") == "+255712345678"

    # Formatted with spaces or dashes
    assert normalize_tanzanian_phone("0712-345-678") == "+255712345678"
    assert normalize_tanzanian_phone("+255 754 123 456") == "+255754123456"


def test_tanzanian_phone_normalization_invalid():
    with pytest.raises(ValueError):
        normalize_tanzanian_phone("")

    with pytest.raises(ValueError):
        normalize_tanzanian_phone("12345")

    with pytest.raises(ValueError):
        normalize_tanzanian_phone("invalid_phone")


def test_sms_segmentation_gsm7():
    # 1 segment GSM 7-bit (<= 160 chars)
    msg_short = "Habari mzazi, tunapenda kuwajulisha kuwa shule itafungwa kesho kwa mapumziko ya pasaka. Asante."
    segments, is_unicode = calculate_sms_segments(msg_short)
    assert segments == 1
    assert is_unicode is False

    # 2 segments GSM 7-bit (> 160 chars)
    msg_long = "A" * 165
    segments, is_unicode = calculate_sms_segments(msg_long)
    assert segments == 2
    assert is_unicode is False


def test_sms_segmentation_unicode():
    # Message with emoji or non-GSM characters triggers Unicode (<= 70 chars per 1 segment)
    unicode_msg = "Habari ya asubuhi 🌟 Matokeo ya mtihani yapo tayari."
    segments, is_unicode = calculate_sms_segments(unicode_msg)
    assert is_unicode is True
    assert segments == 1

    # Longer unicode message (> 70 chars)
    unicode_long = "🌟" + ("Bora " * 20)  # > 70 chars
    segments, is_unicode = calculate_sms_segments(unicode_long)
    assert is_unicode is True
    assert segments >= 2
