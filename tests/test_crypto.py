"""Tests for envchain.crypto encryption/decryption utilities."""

import pytest
from envchain.crypto import encrypt_profile, decrypt_profile


SAMPLE_DATA = {
    "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
    "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "AWS_DEFAULT_REGION": "us-east-1",
}
PASSPHRASE = "super-secret-passphrase"


def test_encrypt_returns_string():
    result = encrypt_profile(SAMPLE_DATA, PASSPHRASE)
    assert isinstance(result, str)
    assert len(result) > 0


def test_roundtrip():
    encoded = encrypt_profile(SAMPLE_DATA, PASSPHRASE)
    decoded = decrypt_profile(encoded, PASSPHRASE)
    assert decoded == SAMPLE_DATA


def test_each_encryption_produces_unique_ciphertext():
    enc1 = encrypt_profile(SAMPLE_DATA, PASSPHRASE)
    enc2 = encrypt_profile(SAMPLE_DATA, PASSPHRASE)
    # Different random salt/nonce should yield different ciphertexts
    assert enc1 != enc2


def test_wrong_passphrase_raises():
    encoded = encrypt_profile(SAMPLE_DATA, PASSPHRASE)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_profile(encoded, "wrong-passphrase")


def test_tampered_data_raises():
    encoded = encrypt_profile(SAMPLE_DATA, PASSPHRASE)
    # Flip a character near the end of the base64 string to corrupt ciphertext
    tampered = encoded[:-4] + "AAAA"
    with pytest.raises(ValueError):
        decrypt_profile(tampered, PASSPHRASE)


def test_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid encoded profile data"):
        decrypt_profile("!!!not-base64!!!", PASSPHRASE)


def test_empty_profile_roundtrip():
    empty = {}
    encoded = encrypt_profile(empty, PASSPHRASE)
    assert decrypt_profile(encoded, PASSPHRASE) == empty


def test_unicode_values_roundtrip():
    data = {"NOTE": "caf\u00e9 \u4e2d\u6587 \U0001f511"}
    encoded = encrypt_profile(data, PASSPHRASE)
    assert decrypt_profile(encoded, PASSPHRASE) == data
