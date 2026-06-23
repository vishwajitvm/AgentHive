import base64
from cryptography.fernet import Fernet
from app.core.config import settings
from app.logging.logger import get_logger

logger = get_logger(__name__)

# Initialize Fernet encryptor using the 32-byte base64-encoded key
try:
    key_bytes = settings.encryption_key.encode("utf-8")
    # Validate the key
    base64.urlsafe_b64decode(key_bytes)
    encryptor = Fernet(key_bytes)
except Exception as e:
    logger.error("Invalid ENCRYPTION_KEY configured. Fernet encryption will fail.", error=str(e))
    # Fallback placeholder to prevent startup crashes in bad envs
    encryptor = None

def encrypt_secret(plain_text: str) -> str:
    """Encrypts a plaintext string into a secure ciphertext string."""
    if not plain_text:
        return ""
    if not encryptor:
        raise ValueError("Encryption engine is not initialized due to invalid ENCRYPTION_KEY.")
    try:
        cipher_text = encryptor.encrypt(plain_text.encode("utf-8"))
        return cipher_text.decode("utf-8")
    except Exception as e:
        logger.exception("Secret encryption failed", error=str(e))
        raise ValueError("Encryption failed") from e

def decrypt_secret(cipher_text: str) -> str:
    """Decrypts a secure ciphertext string back to plaintext."""
    if not cipher_text:
        return ""
    if not encryptor:
        raise ValueError("Encryption engine is not initialized due to invalid ENCRYPTION_KEY.")
    try:
        plain_bytes = encryptor.decrypt(cipher_text.encode("utf-8"))
        return plain_bytes.decode("utf-8")
    except Exception as e:
        logger.exception("Secret decryption failed", error=str(e))
        raise ValueError("Decryption failed") from e
