"""# auth_protocol.py"""
import json
import logging
from typing import Optional, Dict, Any
import secrets
import requests
from Crypto.Hash import SHA256, SHA1
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


def sha1(data: bytes) -> bytes:
    """Calculate SHA1 hash of the given data"""
    return SHA1.new(data).digest()


def sha256(data: bytes) -> bytes:
    """Calculate SHA256 hash of the given data"""
    return SHA256.new(data).digest()


def pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    """Apply PKCS#7 padding to the given data"""
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def pkcs7_unpad(data: bytes) -> bytes:
    """Remove PKCS#7 padding from the given data"""
    pad_len = data[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("Invalid PKCS#7 padding")
    return data[:-pad_len]


class AuthProtocolError(Exception):
    """Custom error for AuthProtocol failures"""

class AuthProtocol:
    """TP-Link Auth Protocol for communication with devices"""

    def __init__(self, address: str, username: str, password: str):
        """Initialize the AuthProtocol with device address, username, and password"""
        self.session    = requests.Session()  # single session, stores cookie
        self.address    = address
        self.username   = username
        self.password   = password
        self.key    : Optional[bytes] = None
        self.iv     : Optional[bytes] = None
        self.seq    : Optional[int]   = None
        self.sig    : Optional[bytes] = None


    def calc_auth_hash(self, username: str, password: str) -> bytes:
        """Calculate the authentication hash based on username and password"""
        return sha256(sha1(username.encode()) + sha1(password.encode()))


    def _request_raw(
            self,
            path: str,
            data: bytes,
            params: Optional[Dict[str, Any]] = None
        ) -> bytes:
        """Make a raw request to the device with the given path and data"""
        url = f"http://{self.address}/app/{path}"
        resp = self.session.post(url, data=data, timeout=2, params=params)
        resp.raise_for_status()
        return resp.content


    def request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a request to the device using the specified method and parameters"""
        if self.key is None:
            self.initialize()
        payload: Dict[str, Any] = {"method": method}
        if params:
            payload["params"] = params
        log.debug("Request: %s", payload)
        encrypted = self._encrypt(json.dumps(payload).encode("utf-8"))
        resp = self._request_raw("request", encrypted, params={"seq": self.seq})
        result = json.loads(self._decrypt(resp).decode("utf-8"))
        if result.get("error_code", 0) != 0:
            log.error("Error: %s", result)
            self.key = None
            raise AuthProtocolError(f"Error code: {result['error_code']}")
        log.debug("Response: %s", result.get("result"))
        return result.get("result")


    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt the given data using AES encryption"""
        if self.seq is None:
            raise ValueError("Sequence number (seq) is not initialized")
        if self.sig is None:
            raise ValueError("Signature (sig) is not initialized")
        if self.key is None:
            raise ValueError("Encryption key (key) is not initialized")
        if self.iv is None:
            raise ValueError("Initialization vector (iv) is not initialized")
        self.seq += 1
        seq_bytes = self.seq.to_bytes(4, "big", signed=True)
        data_padded = pkcs7_pad(data)
        cipher = AES.new(self.key, AES.MODE_CBC, iv=self.iv + seq_bytes)
        ciphertext = cipher.encrypt(data_padded)
        sig = sha256(self.sig + seq_bytes + ciphertext)
        return sig + ciphertext


    def _decrypt(self, data: bytes) -> bytes:
        """Decrypt the given data using AES decryption"""
        if self.seq is None:
            raise ValueError("Sequence number (seq) is not initialized")
        if self.sig is None:
            raise ValueError("Signature (sig) is not initialized")
        if self.key is None:
            raise ValueError("Encryption key (key) is not initialized")
        if self.iv is None:
            raise ValueError("Initialization vector (iv) is not initialized")
        seq_bytes = self.seq.to_bytes(4, "big", signed=True)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv + seq_bytes)
        # Only decrypt after signature (first 32 bytes)
        plaintext = cipher.decrypt(data[32:])
        return pkcs7_unpad(plaintext)


    def initialize(self):
        """Initialize the AuthProtocol by performing a handshake with the device"""
        local_seed = get_random_bytes(16)
        resp = self._request_raw("handshake1", local_seed)
        remote_seed, server_hash = resp[:16], resp[16:]
        auth_hash = None
        for creds in [
            (self.username, self.password),
            ("", ""),
            ("kasa@tp-link.net", "kasaSetup"),
        ]:
            ah = self.calc_auth_hash(*creds)
            candidate = sha256(local_seed + remote_seed + ah)
            # Constant-time compare
            if secrets.compare_digest(candidate, server_hash):
                auth_hash = ah
                log.debug("Authenticated with %s", creds[0])
                break
        if not auth_hash:
            raise AuthProtocolError("Failed to authenticate")
        self._request_raw("handshake2", sha256(remote_seed + local_seed + auth_hash))
        self.key = sha256(b"lsk" + local_seed + remote_seed + auth_hash)[:16]
        ivseq = sha256(b"iv" + local_seed + remote_seed + auth_hash)
        self.iv = ivseq[:12]
        self.seq = int.from_bytes(ivseq[-4:], "big", signed=True)
        self.sig = sha256(b"ldk" + local_seed + remote_seed + auth_hash)[:28]
        log.debug("Initialized")
