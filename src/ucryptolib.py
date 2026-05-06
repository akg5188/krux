"""Minimal `ucryptolib` compatibility layer for desktop Python tests."""

from __future__ import annotations

from Crypto.Cipher import AES as _AES

MODE_ECB = _AES.MODE_ECB
MODE_CBC = _AES.MODE_CBC
MODE_CTR = _AES.MODE_CTR
MODE_GCM = _AES.MODE_GCM


def aes(key, mode, *args, **kwargs):
    return _AES.new(key, mode, *args, **kwargs)
