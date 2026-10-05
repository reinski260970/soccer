"""Schneller Fußball-Quotenwächter über API-Football."""
from . import guard


def run(j=None, send=False, days=7, now=None):
    return guard.run(j, send=send, now=now, strict=True)
