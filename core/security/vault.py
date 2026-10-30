"""
OS Credential Vault for Miku Companion Runtime (`/core/security/vault.py`).
Stores and retrieves API keys and OAuth tokens securely using:
1. Windows Credential Manager / macOS Keychain / SecretService via `keyring` (when available).
2. Windows DPAPI (`CryptProtectData` / `CryptUnprotectData` via `ctypes.windll.crypt32`) on Windows if `keyring` is unavailable.
3. Machine-keyed authenticated encryption fallback (`.miku_vault.bin` with 0600 permissions) on headless Linux containers where no DBus keyring daemon is running.

Never writes raw secrets into plain-text `.env` files, and automatically migrates any
existing secrets found in `.env` into the encrypted vault while replacing them in `.env`
with `# [MOVED TO MIKU SECURE VAULT]`.
"""

import base64
import ctypes
import ctypes.wintypes
import hashlib
import hmac
import json
import os
import platform
import stat
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SERVICE_NAME = "MikuCompanionVault"

MANAGED_SECRET_KEYS: List[str] = [
    "GEMINI_API_KEY",
    "DEEPSEEK_API_KEY",
    "ZHIPU_API_KEY",
    "GROQ_API_KEY",
    "OPENROUTER_API_KEY",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
    "SPOTIPY_CLIENT_ID",
    "SPOTIPY_CLIENT_SECRET",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REFRESH_TOKEN",
    "MIKU_BRIDGE_TOKEN",
]


def mask_secret(value: Optional[str]) -> str:
    """
    Returns a safe masked preview of a secret (e.g. `sk-a...9f2b`).
    Never returns the full secret.
    """
    if not value:
        return ""
    val = value.strip()
    if len(val) <= 8:
        return "*" * len(val)
    return f"{val[:4]}••••{val[-4:]}"


class _WindowsDPAPI:
    """Native Windows DPAPI wrapper using ctypes (zero external dependencies)."""

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", ctypes.wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char)),
        ]

    @staticmethod
    def is_available() -> bool:
        return platform.system().lower() == "windows" and hasattr(ctypes, "windll")

    @classmethod
    def protect(cls, raw_bytes: bytes) -> bytes:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        buf = ctypes.create_string_buffer(raw_bytes, len(raw_bytes))
        blob_in = cls.DATA_BLOB(len(raw_bytes), buf)
        blob_out = cls.DATA_BLOB()
        CRYPTPROTECT_UI_FORBIDDEN = 0x01
        ok = crypt32.CryptProtectData(
            ctypes.byref(blob_in),
            "MikuCompanionVault",
            None,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(blob_out),
        )
        if not ok:
            raise OSError("Windows DPAPI CryptProtectData failed")
        try:
            return ctypes.string_at(blob_out.pbData, blob_out.cbData)
        finally:
            kernel32.LocalFree(blob_out.pbData)

    @classmethod
    def unprotect(cls, encrypted_bytes: bytes) -> bytes:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        buf = ctypes.create_string_buffer(encrypted_bytes, len(encrypted_bytes))
        blob_in = cls.DATA_BLOB(len(encrypted_bytes), buf)
        blob_out = cls.DATA_BLOB()
        CRYPTPROTECT_UI_FORBIDDEN = 0x01
        ok = crypt32.CryptUnprotectData(
            ctypes.byref(blob_in),
            None,
            None,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(blob_out),
        )
        if not ok:
            raise OSError("Windows DPAPI CryptUnprotectData failed")
        try:
            return ctypes.string_at(blob_out.pbData, blob_out.cbData)
        finally:
            kernel32.LocalFree(blob_out.pbData)


class SecretVault:
    """
    Unified OS Credential Vault with keyring -> Windows DPAPI -> encrypted local vault fallback.
    """

    def __init__(self, vault_file: Optional[Path] = None, service_name: str = SERVICE_NAME):
        self.service_name = service_name
        self._lock = threading.RLock()
        default_dir = Path(os.environ.get("MIKU_VAULT_DIR", Path.home() / ".miku_companion"))
        default_dir.mkdir(parents=True, exist_ok=True)
        self.vault_file = Path(vault_file) if vault_file else (default_dir / "vault.dpapi.bin")
        self._keyring = self._probe_keyring()
        self._backend_name = (
            "os_keyring"
            if self._keyring is not None
            else ("windows_dpapi" if _WindowsDPAPI.is_available() else "encrypted_file_vault")
        )

    @property
    def backend_name(self) -> str:
        return self._backend_name

    def _probe_keyring(self):
        if os.environ.get("MIKU_FORCE_FILE_VAULT") == "1":
            return None
        try:
            import keyring
            from keyring.backends import fail, null

            backend = keyring.get_keyring()
            if isinstance(backend, (fail.Keyring, null.Keyring)):
                return None
            # Quick write/read probe to verify the OS daemon responds
            probe_key = "__miku_vault_probe__"
            keyring.set_password(self.service_name, probe_key, "ok")
            val = keyring.get_password(self.service_name, probe_key)
            try:
                keyring.delete_password(self.service_name, probe_key)
            except Exception:
                pass
            if val == "ok":
                return keyring
        except Exception:
            return None
        return None

    def _derive_machine_key(self) -> bytes:
        seed_parts = [
            platform.node(),
            platform.system(),
            platform.machine(),
            str(os.getuid() if hasattr(os, "getuid") else os.environ.get("USERNAME", "miku")),
            os.environ.get("MIKU_VAULT_SALT", "miku-companion-v2.5-google-standard"),
        ]
        # Try Linux machine-id if available
        for mid_path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                if os.path.exists(mid_path):
                    with open(mid_path, "r", encoding="utf-8") as f:
                        seed_parts.append(f.read().strip())
                    break
            except Exception:
                pass
        raw = "|".join(seed_parts).encode("utf-8")
        return hashlib.pbkdf2_hmac("sha256", raw, b"MikuVaultSalt_2026", 100_000, dklen=32)

    def _encrypt_payload(self, data: Dict[str, str]) -> bytes:
        raw_json = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        if _WindowsDPAPI.is_available():
            return b"DPAPI1:" + _WindowsDPAPI.protect(raw_json)

        key = self._derive_machine_key()
        nonce = os.urandom(16)
        # Stream-cipher XOR with HMAC-SHA256 keystream blocks + authenticated tag
        ciphertext = bytearray(len(raw_json))
        block_count = (len(raw_json) + 31) // 32
        for blk in range(block_count):
            counter_bytes = blk.to_bytes(8, "big")
            keystream = hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest()
            start = blk * 32
            end = min(start + 32, len(raw_json))
            for i in range(start, end):
                ciphertext[i] = raw_json[i] ^ keystream[i - start]

        mac = hmac.new(key, b"ENC1" + nonce + bytes(ciphertext), hashlib.sha256).digest()
        envelope = {
            "v": "ENC1",
            "n": base64.b64encode(nonce).decode("ascii"),
            "c": base64.b64encode(bytes(ciphertext)).decode("ascii"),
            "m": base64.b64encode(mac).decode("ascii"),
        }
        return json.dumps(envelope, sort_keys=True).encode("utf-8")

    def _decrypt_payload(self, blob: bytes) -> Dict[str, str]:
        if not blob:
            return {}
        if blob.startswith(b"DPAPI1:"):
            raw_json = _WindowsDPAPI.unprotect(blob[len(b"DPAPI1:") :])
            return json.loads(raw_json.decode("utf-8"))

        envelope = json.loads(blob.decode("utf-8"))
        if envelope.get("v") != "ENC1":
            raise ValueError("Unsupported vault envelope version")
        nonce = base64.b64decode(envelope["n"])
        ciphertext = base64.b64decode(envelope["c"])
        mac = base64.b64decode(envelope["m"])

        key = self._derive_machine_key()
        expected_mac = hmac.new(key, b"ENC1" + nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("Vault integrity check failed (HMAC mismatch)")

        plaintext = bytearray(len(ciphertext))
        block_count = (len(ciphertext) + 31) // 32
        for blk in range(block_count):
            counter_bytes = blk.to_bytes(8, "big")
            keystream = hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest()
            start = blk * 32
            end = min(start + 32, len(ciphertext))
            for i in range(start, end):
                plaintext[i] = ciphertext[i] ^ keystream[i - start]

        return json.loads(bytes(plaintext).decode("utf-8"))

    def _read_store(self) -> Dict[str, str]:
        if not self.vault_file.exists():
            return {}
        try:
            blob = self.vault_file.read_bytes()
            return self._decrypt_payload(blob)
        except Exception:
            return {}

    def _write_store(self, store: Dict[str, str]) -> None:
        self.vault_file.parent.mkdir(parents=True, exist_ok=True)
        blob = self._encrypt_payload(store)
        tmp_file = self.vault_file.with_suffix(".tmp")
        tmp_file.write_bytes(blob)
        try:
            os.chmod(tmp_file, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass
        tmp_file.replace(self.vault_file)

    def set_secret(self, key: str, value: str) -> bool:
        """
        Saves `key` safely in the OS Credential Vault and injects it into `os.environ`
        for the current runtime process without writing plain text to `.env`.
        """
        clean_key = (key or "").strip()
        if not clean_key:
            raise ValueError("Secret key cannot be empty")
        clean_val = (value or "").strip()

        with self._lock:
            if not clean_val:
                return self.delete_secret(clean_key)

            os.environ[clean_key] = clean_val
            if self._keyring is not None:
                try:
                    self._keyring.set_password(self.service_name, clean_key, clean_val)
                except Exception:
                    pass

            store = self._read_store()
            store[clean_key] = clean_val
            self._write_store(store)
            return True

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieves `key` from OS Credential Vault (or environment variable fallback).
        """
        clean_key = (key or "").strip()
        if not clean_key:
            return default

        with self._lock:
            if self._keyring is not None:
                try:
                    val = self._keyring.get_password(self.service_name, clean_key)
                    if val:
                        os.environ[clean_key] = val
                        return val
                except Exception:
                    pass

            store = self._read_store()
            if clean_key in store and store[clean_key]:
                os.environ[clean_key] = store[clean_key]
                return store[clean_key]

            env_val = os.environ.get(clean_key)
            if env_val:
                return env_val
            return default

    def delete_secret(self, key: str) -> bool:
        """
        Deletes `key` from the OS Credential Vault and removes it from `os.environ`.
        """
        clean_key = (key or "").strip()
        if not clean_key:
            return False

        with self._lock:
            os.environ.pop(clean_key, None)
            if self._keyring is not None:
                try:
                    self._keyring.delete_password(self.service_name, clean_key)
                except Exception:
                    pass

            store = self._read_store()
            removed = clean_key in store
            if removed:
                store.pop(clean_key, None)
                self._write_store(store)
            return removed

    def list_masked_secrets(self, keys: Optional[Iterable[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Returns metadata and masked values for managed keys without exposing plaintext secrets.
        """
        target_keys = list(keys) if keys is not None else list(MANAGED_SECRET_KEYS)
        store = self._read_store()
        all_keys = sorted(set(target_keys) | set(store.keys()))
        result: Dict[str, Dict[str, Any]] = {}
        for k in all_keys:
            val = self.get_secret(k)
            result[k] = {
                "configured": bool(val),
                "masked": mask_secret(val) if val else "",
                "backend": self._backend_name,
            }
        return result

    def hydrate_environ(self, keys: Optional[Iterable[str]] = None) -> int:
        """
        Loads stored vault secrets into `os.environ` at startup.
        """
        count = 0
        store = self._read_store()
        target_keys = set(keys or MANAGED_SECRET_KEYS) | set(store.keys())
        for k in target_keys:
            val = self.get_secret(k)
            if val:
                os.environ[k] = val
                count += 1
        return count

    def migrate_plaintext_env(self, env_path: Path) -> Dict[str, Any]:
        """
        Scans an existing `.env` file, migrates any sensitive API keys in `MANAGED_SECRET_KEYS`
        into the encrypted OS Vault, and scrubs the plaintext values from `.env`.
        Non-secret configuration lines (like ports or flags) are preserved intact.
        """
        env_path = Path(env_path)
        if not env_path.exists():
            return {"migrated_keys": [], "env_exists": False}

        lines = env_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        new_lines: List[str] = []
        migrated: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                new_lines.append(line)
                continue

            k, v = stripped.split("=", 1)
            key_name = k.strip()
            raw_val = v.strip().strip('"').strip("'")

            is_secret_key = (
                key_name in MANAGED_SECRET_KEYS
                or key_name.endswith("_API_KEY")
                or key_name.endswith("_SECRET")
                or key_name.endswith("_TOKEN")
            )
            if is_secret_key and raw_val and not raw_val.startswith("your_") and raw_val != "tu_clave_aqui":
                self.set_secret(key_name, raw_val)
                migrated.append(key_name)
                new_lines.append(f"# {key_name}= [MOVED TO MIKU OS CREDENTIAL VAULT]")
            else:
                new_lines.append(line)

        if migrated:
            env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        return {"migrated_keys": migrated, "env_exists": True, "backend": self._backend_name}


_DEFAULT_VAULT: Optional[SecretVault] = None
_VAULT_INIT_LOCK = threading.Lock()


def get_vault() -> SecretVault:
    global _DEFAULT_VAULT
    if _DEFAULT_VAULT is None:
        with _VAULT_INIT_LOCK:
            if _DEFAULT_VAULT is None:
                _DEFAULT_VAULT = SecretVault()
    return _DEFAULT_VAULT


def set_secret(key: str, value: str) -> bool:
    return get_vault().set_secret(key, value)


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    return get_vault().get_secret(key, default=default)


def delete_secret(key: str) -> bool:
    return get_vault().delete_secret(key)


def list_masked_secrets(keys: Optional[Iterable[str]] = None) -> Dict[str, Dict[str, Any]]:
    return get_vault().list_masked_secrets(keys=keys)


def migrate_plaintext_env(env_path: Path) -> Dict[str, Any]:
    return get_vault().migrate_plaintext_env(env_path)
