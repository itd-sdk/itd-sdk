"""JIT for the drawing kernels: numba if installed, otherwise the same code runs as plain Python (identical result, much slower)."""

from os import environ

try:
    if environ.get('ITD_BANNER_NO_JIT'):
        raise ImportError
    from numba import njit
except ImportError:
    njit = None

JIT = njit is not None


def jit(fn):
    # error_model='numpy': float division by zero gives inf/nan instead of raising
    return njit(cache=True, nogil=True, error_model='numpy')(fn) if njit is not None else fn
