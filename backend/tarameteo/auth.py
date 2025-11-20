"""API key management."""

import hashlib
import secrets
from typing import Protocol

import bcrypt


class KeyGenerator(Protocol):
    """Protocol for API key generation."""

    def generate(self, length: int) -> str:
        """Generate a new API key."""


class SecureKeyGenerator:
    """Generate secure API keys using secrets module."""

    def generate(self, length: int) -> str:
        """Generate a new API key using URL-safe base64 encoding."""
        return secrets.token_urlsafe(length)


class KeyHasher(Protocol):
    """Protocol for API key hashing."""

    def hash_index(self, key: str) -> str:
        """Create a fast hash for database lookups."""

    def hash_key(self, key: str) -> str:
        """Create a secure hash for storage."""

    def verify(self, key: str, hashed_key: str) -> bool:
        """Verify a key against its hash."""


class BcryptKeyHasher:
    """Hash API keys using bcrypt for storage and SHA-256 for lookups."""

    def hash_index(self, key: str) -> str:
        """Create a fast SHA-256 hash for database lookups."""
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def hash_key(self, key: str) -> str:
        """Create a secure bcrypt hash for storage."""
        return bcrypt.hashpw(
            key.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

    def verify(self, key: str, hashed_key: str) -> bool:
        """Verify an API key against its bcrypt storage hash."""
        return bcrypt.checkpw(
            key.encode("utf-8"),
            hashed_key.encode("utf-8"),
        )


# Default implementations
key_generator: KeyGenerator = SecureKeyGenerator()
key_hasher: KeyHasher = BcryptKeyHasher()
