"""JWT token handling implementation."""
import json
import base64
import hashlib
import hmac
from typing import Any

from domain.interfaces import IJWTHandler


class JWTHandler(IJWTHandler):
    """Implementation of JWT encoding/decoding using HS256."""

    def __init__(self, secret: str, algorithm: str = "HS256"):
        """Initialize JWT handler with secret key.

        Args:
            secret: Secret key for signing tokens
            algorithm: Algorithm to use (default: HS256)
        """
        self.secret = secret
        self.algorithm = algorithm

    def encode(self, payload: dict) -> str:
        """Encode payload into JWT token.

        Args:
            payload: Dictionary to encode (should include exp, iat, sub, etc.)

        Returns:
            JWT token string
        """
        # Create header
        header = {
            "alg": self.algorithm,
            "typ": "JWT"
        }

        # Encode header and payload
        header_b64 = self._base64url_encode(
            json.dumps(header, separators=(',', ':'), sort_keys=True).encode()
        )
        payload_b64 = self._base64url_encode(
            json.dumps(payload, separators=(',', ':'), sort_keys=True).encode()
        )

        # Create signature
        signing_input = f"{header_b64}.{payload_b64}".encode()
        signature = hmac.new(
            self.secret.encode(),
            signing_input,
            hashlib.sha256
        ).digest()
        signature_b64 = self._base64url_encode(signature)

        # Combine parts
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def decode(self, token: str) -> dict:
        """Decode and verify JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload dictionary

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            # Split token
            header_b64, payload_b64, signature_b64 = token.split('.')
        except ValueError:
            raise ValueError("Invalid token format")

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected_signature = hmac.new(
            self.secret.encode(),
            signing_input,
            hashlib.sha256
        ).digest()

        try:
            provided_signature = self._base64url_decode(signature_b64)
        except Exception:
            raise ValueError("Invalid signature encoding")

        if not hmac.compare_digest(expected_signature, provided_signature):
            raise ValueError("Invalid signature")

        # Decode payload
        try:
            payload = json.loads(self._base64url_decode(payload_b64))
        except Exception:
            raise ValueError("Invalid payload encoding")

        # Verify expiration
        if 'exp' in payload:
            import time
            if int(payload['exp']) < int(time.time()):
                raise ValueError("Token expired")

        return payload

    @staticmethod
    def _base64url_encode(data: bytes) -> str:
        """Base64url encode (without padding)."""
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    @staticmethod
    def _base64url_decode(data: str) -> bytes:
        """Base64url decode (with padding added if needed)."""
        # Add padding if needed
        padding = '=' * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding)
