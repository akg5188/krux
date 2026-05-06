"""Minimal `urandom` compatibility layer for desktop Python tests.

Krux expects MicroPython's `urandom` module to provide a small RNG API.
This wrapper mirrors the handful of functions used by the codebase so
the same imports work in the local pytest environment.
"""

from __future__ import annotations

import os
import random as _random

_rng = _random.Random()


def seed(value=None):
    _rng.seed(value)


def choice(seq):
    return _rng.choice(seq)


def randint(a, b):
    return _rng.randint(a, b)


def randrange(*args, **kwargs):
    return _rng.randrange(*args, **kwargs)


def random():
    return _rng.random()


def shuffle(seq):
    _rng.shuffle(seq)


def getrandbits(k):
    return _rng.getrandbits(k)


def urandom(n):
    return os.urandom(n)
