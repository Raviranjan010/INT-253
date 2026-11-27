from hashlib import sha256

from django.core.cache import cache


def rate_limited(request, scope: str, limit: int, seconds: int) -> bool:
    """Use the server-provided address, never an untrusted forwarding header."""
    address = request.META.get('REMOTE_ADDR') or 'unknown'
    key = f'{scope}:{sha256(address.encode()).hexdigest()}'
    if cache.add(key, 1, timeout=seconds):
        return False
    try:
        return cache.incr(key) > limit
    except ValueError:
        cache.add(key, 1, timeout=seconds)
        return False
