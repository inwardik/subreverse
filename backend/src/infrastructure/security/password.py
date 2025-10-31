"""Password hashing implementation."""
import secrets
import hashlib
import hmac

from domain.interfaces import IPasswordHandler


class PasswordHandler(IPasswordHandler):
    """Implementation of password hashing using SHA256 with salt."""

    def hash_password(self, password: str, salt: str | None = None) -> tuple[str, str]:
        """Hash a password with salt using SHA256.

        Args:
            password: Plain text password
            salt: Optional salt (generated if not provided)

        Returns:
            Tuple of (password_hash, salt)
        """
        if not salt:
            salt = secrets.token_hex(16)

        # Combine salt and password
        combined = f"{salt}:{password}"

        # Hash with SHA256
        password_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()

        return password_hash, salt

    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against stored hash and salt.

        Args:
            password: Plain text password to verify
            password_hash: Stored password hash
            salt: Salt used for hashing

        Returns:
            True if password matches, False otherwise
        """
        calculated_hash, _ = self.hash_password(password, salt)

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(calculated_hash, password_hash)
