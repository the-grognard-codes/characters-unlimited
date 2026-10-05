"""Bounded canonical JSON encoding shared by saves and rule content pins."""

import json

MAX_BYTES = 10_000_000


def canonical(value):
    try:
        encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, RecursionError) as error:
        raise ValueError('The bundle must contain finite JSON data') from error
    if len(encoded) > MAX_BYTES:
        raise ValueError('The portable character exceeds the 10 MB limit')
    return encoded
