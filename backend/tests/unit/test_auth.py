"""Unit tests for the auth module."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tarameteo.auth import (
    key_generator,
    key_hasher,
)


@given(length=st.integers(min_value=1, max_value=100))
def test_key_generator_length(length):
    """Verify that generated keys have the expected length."""
    key = key_generator.generate(length)
    # URL-safe base64 encoding makes the actual length longer
    assert len(key) > length
    # URL-safe base64 uses 4/3 ratio
    assert len(key) <= (length * 4 // 3) + 2


def test_key_hasher_index_hash(unique):
    """Verify that index hash is deterministic."""
    key = unique("text")
    hash1 = key_hasher.hash_index(key)
    hash2 = key_hasher.hash_index(key)
    assert hash1 == hash2


def test_key_hasher_key_hash(unique):
    """Verify that key hash is non deterministic."""
    key = unique("text")
    hash1 = key_hasher.hash_key(key)
    hash2 = key_hasher.hash_key(key)
    assert hash1 != hash2


def test_key_hasher_verify(unique):
    """Verify that key verification works correctly."""
    key = unique("text")
    key_hash = key_hasher.hash_key(key)
    assert key_hasher.verify(key, key_hash)
    assert not key_hasher.verify(key + "x", key_hash)
    assert not key_hasher.verify("x" + key, key_hash)


def test_key_hasher_verify_invalid_hash():
    """Verify that verification fails with invalid hash format."""
    with pytest.raises(ValueError):
        key_hasher.verify("key", "invalid-hash")


def test_key_hasher_verify_empty_key():
    """Verify that empty keys are handled correctly."""
    key_hash = key_hasher.hash_key("")
    assert key_hasher.verify("", key_hash)
    assert not key_hasher.verify("x", key_hash)


def test_key_hasher_verify_unicode():
    """Verify that unicode keys are handled correctly."""
    key = "🔑" * 10
    key_hash = key_hasher.hash_key(key)
    assert key_hasher.verify(key, key_hash)
    assert not key_hasher.verify(key + "x", key_hash)


def test_key_hasher_index_hash_unicode():
    """Verify that unicode keys are handled correctly for index hash."""
    key = "🔑" * 10
    hash1 = key_hasher.hash_index(key)
    hash2 = key_hasher.hash_index(key)
    assert hash1 == hash2
