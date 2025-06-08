from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import zlib
import os

class CryptoUtils:
    def __init__(self, password="securichat_key"):
        self.key = self._derive_key(password)
        self.cipher = Fernet(self.key)

    def _derive_key(self, password):
        salt = b'securichat_salt'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)

    def decrypt(self, encrypted_data):
        try:
            return self.cipher.decrypt(encrypted_data).decode()
        except:
            return None

    def calculate_checksum(self, data):
        if isinstance(data, str):
            data = data.encode()
        return zlib.crc32(data)

    def verify_checksum(self, data, checksum):
        return self.calculate_checksum(data) == checksum