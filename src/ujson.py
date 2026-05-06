"""Minimal `ujson` compatibility layer for desktop Python tests."""

from __future__ import annotations

import json as _json

JSONDecodeError = _json.JSONDecodeError


def dumps(*args, **kwargs):
    return _json.dumps(*args, **kwargs)


def loads(*args, **kwargs):
    return _json.loads(*args, **kwargs)


def dump(*args, **kwargs):
    return _json.dump(*args, **kwargs)


def load(*args, **kwargs):
    return _json.load(*args, **kwargs)
