"""
Miku Security Subsystem: OS Credential Vault & Secret Sanitization.
"""

from .vault import (
    MANAGED_SECRET_KEYS,
    SecretVault,
    delete_secret,
    get_secret,
    get_vault,
    list_masked_secrets,
    mask_secret,
    migrate_plaintext_env,
    set_secret,
)

__all__ = [
    "MANAGED_SECRET_KEYS",
    "SecretVault",
    "get_vault",
    "get_secret",
    "set_secret",
    "delete_secret",
    "list_masked_secrets",
    "mask_secret",
    "migrate_plaintext_env",
]
