"""Encryption and decryption utilities for envchain profiles.

Uses AES-GCM via the cryptography library with a key derived from
a user-supplied passphrase using PBKDF2-HMAC-SHA256.
"""

import os
import base64
import json
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
ITERATIONS = 390_000


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a passphrase and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(passphrase.encode())


def encrypt_profile(data: dict, passphrase: str) -> str:
    """Encrypt a profile dict and return a base64-encoded ciphertext string.

    Format (all concatenated, then base64-encoded): salt | nonce | ciphertext
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    plaintext = json.dumps(data).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode()


def decrypt_profile(encoded: str, passphrase: str) -> dict:
    """Decrypt a base64-encoded profile string and return the original dict.

    Raises ValueError on authentication failure (wrong passphrase / tampered data).
    """
    try:
        payload = base64.b64decode(encoded.encode())
    except Exception as exc:
        raise ValueError("Invalid encoded profile data.") from exc

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE:]

    key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed: wrong passphrase or corrupted data.") from exc

    return json.loads(plaintext.decode())
