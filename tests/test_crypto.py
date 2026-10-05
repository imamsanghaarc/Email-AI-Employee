import base64

import pytest

from ai_employee_mcp.crypto import (
    KEY_BYTES,
    CredentialCipher,
    DecryptionError,
    constant_time_equals,
)


def test_generated_master_key_decodes_to_32_bytes():
    encoded = CredentialCipher.generate_master_key()
    assert len(base64.b64decode(encoded)) == KEY_BYTES


def test_rejects_master_key_of_wrong_length():
    with pytest.raises(ValueError, match="32 bytes"):
        CredentialCipher(b"too-short")


def test_seal_and_open_roundtrip(cipher):
    aad = CredentialCipher.build_aad("usr_1", "odoo", "api_key")
    blob = cipher.seal("s3cr3t-value", aad)
    assert "s3cr3t-value" not in blob
    assert cipher.open(blob, aad) == "s3cr3t-value"


def test_ciphertext_is_not_deterministic(cipher):
    aad = CredentialCipher.build_aad("usr_1", "odoo", "api_key")
    assert cipher.seal("same", aad) != cipher.seal("same", aad)


def test_aad_binds_to_user(cipher):
    alice = CredentialCipher.build_aad("usr_alice", "odoo", "api_key")
    bob = CredentialCipher.build_aad("usr_bob", "odoo", "api_key")
    blob = cipher.seal("alice-key", alice)
    with pytest.raises(DecryptionError, match="AAD"):
        cipher.open(blob, bob)


def test_aad_binds_to_field_and_provider(cipher):
    user = "usr_1"
    blob = cipher.seal("value", CredentialCipher.build_aad(user, "odoo", "api_key"))
    with pytest.raises(DecryptionError):
        cipher.open(blob, CredentialCipher.build_aad(user, "odoo", "password"))
    with pytest.raises(DecryptionError):
        cipher.open(blob, CredentialCipher.build_aad(user, "gmail", "api_key"))


def test_wrong_master_key_cannot_decrypt(cipher, master_key):
    aad = CredentialCipher.build_aad("usr_1", "odoo", "api_key")
    blob = cipher.seal("value", aad)
    other = CredentialCipher(base64.b64decode(CredentialCipher.generate_master_key()))
    with pytest.raises(DecryptionError):
        other.open(blob, aad)


def test_tampered_ciphertext_is_rejected(cipher):
    aad = CredentialCipher.build_aad("usr_1", "gmail", "refresh_token")
    sealed = cipher.seal("token-value", aad)
    import json

    parsed = json.loads(sealed)
    raw = bytearray(base64.b64decode(parsed["ct"]))
    raw[0] ^= 0xFF
    parsed["ct"] = base64.b64encode(bytes(raw)).decode("ascii")
    with pytest.raises(DecryptionError):
        cipher.open(json.dumps(parsed), aad)


def test_seal_mapping_skips_empty_values(cipher):
    sealed = cipher.seal_mapping(
        {"db": "prod", "username": "admin", "api_key": ""}, "usr_1", "odoo"
    )
    assert set(sealed) == {"db", "username"}
    opened = cipher.open_mapping(sealed, "usr_1", "odoo")
    assert opened == {"db": "prod", "username": "admin"}


def test_unsupported_version_is_rejected(cipher):
    aad = CredentialCipher.build_aad("usr_1", "odoo", "api_key")
    blob = cipher.seal("value", aad)
    import json

    parsed = json.loads(blob)
    parsed["v"] = "v99"
    with pytest.raises(DecryptionError, match="unsupported"):
        cipher.open(json.dumps(parsed), aad)


def test_constant_time_equals():
    assert constant_time_equals("abc", "abc")
    assert not constant_time_equals("abc", "abd")
    assert not constant_time_equals("abc", "abcd")