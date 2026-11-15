import base64
import hashlib
from django.conf import settings
from cryptography.fernet import Fernet
from decouple import config

def get_fernet():
    key_str = config('FIELD_ENCRYPTION_KEY', default='').strip()
    if key_str:
        key = key_str.encode('utf-8')
    else:
        # Fallback to key derived deterministically from SECRET_KEY
        secret = getattr(settings, 'SECRET_KEY', 'default-belings-secret-key')
        digest = hashlib.sha256(secret.encode('utf-8')).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)

def encrypt_value(raw_text: str) -> str:
    if not raw_text:
        return ""
    f = get_fernet()
    return f.encrypt(raw_text.encode('utf-8')).decode('utf-8')

def decrypt_value(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    try:
        f = get_fernet()
        return f.decrypt(cipher_text.encode('utf-8')).decode('utf-8')
    except Exception:
        return ""

