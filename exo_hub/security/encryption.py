"""
End-to-End Encryption for P2P Communication
"""
import os
import asyncio
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from base64 import b64encode, b64decode
from typing import Dict, Any, Optional

class E2EEncryption:
    def __init__(self):
        self.key_registry = {}
        self.session_keys = {}

    async def establish_secure_channel(
        self,
        peer_id: str,
        peer_public_key: bytes
    ) -> Dict[str, Any]:
        """Establish secure communication channel with peer"""
        try:
            # Generate session key
            session_key = Fernet.generate_key()
            
            # Exchange keys using asymmetric encryption
            encrypted_session_key = self._encrypt_with_public_key(
                session_key,
                peer_public_key
            )
            
            # Store session key
            self.session_keys[peer_id] = session_key
            
            return {
                'encrypted_session_key': encrypted_session_key,
                'channel_id': os.urandom(16).hex()
            }

        except Exception as e:
            logger.error(f"Failed to establish secure channel: {e}")
            raise

    async def encrypt_message(
        self,
        peer_id: str,
        message: Dict[str, Any]
    ) -> bytes:
        """Encrypt message for peer"""
        try:
            session_key = self.session_keys.get(peer_id)
            if not session_key:
                raise ValueError(f"No session key for peer {peer_id}")

            f = Fernet(session_key)
            return f.encrypt(json.dumps(message).encode())

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    async def decrypt_message(
        self,
        peer_id: str,
        encrypted_message: bytes
    ) -> Dict[str, Any]:
        """Decrypt message from peer"""
        try:
            session_key = self.session_keys.get(peer_id)
            if not session_key:
                raise ValueError(f"No session key for peer {peer_id}")

            f = Fernet(session_key)
            decrypted = f.decrypt(encrypted_message)
            return json.loads(decrypted.decode())

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
