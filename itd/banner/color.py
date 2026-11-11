"""Color: sRGB <-> OKLab, hex. Colors inside the kernels are ints 0xRRGGBB."""

import numpy as np

from itd.banner.jit import jit


def _lin_table() -> np.ndarray:
    out = np.zeros(256)
    for i in range(256):
        v = i / 255
        out[i] = v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return out


LIN = _lin_table()


@jit
def oklab_lin(lr, lg, lb):
    l = np.cbrt(0.4122214708 * lr + 0.5363325363 * lg + 0.0514459929 * lb)
    m = np.cbrt(0.2119034982 * lr + 0.6806995451 * lg + 0.1073969566 * lb)
    s = np.cbrt(0.0883024619 * lr + 0.2817188376 * lg + 0.6299787005 * lb)
    return (
        0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
        1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
        0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    )


@jit
def oklab(r, g, b):
    """OKLab of 8-bit channels."""
    return oklab_lin(LIN[r], LIN[g], LIN[b])


@jit
def oklab_code(c):
    return oklab_lin(LIN[(c >> 16) & 255], LIN[(c >> 8) & 255], LIN[c & 255])


@jit
def _lin_f(v):
    v = min(255.0, max(0.0, v)) / 255
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


@jit
def oklab_f(r, g, b):
    """OKLab of fractional channels 0..255 (mean colors)."""
    return oklab_lin(_lin_f(r), _lin_f(g), _lin_f(b))


@jit
def _lab_codes(codes, out):
    for k in range(codes.shape[0]):
        L, A, B = oklab_code(codes[k])
        out[k, 0] = L
        out[k, 1] = A
        out[k, 2] = B


def lab_of(data: np.ndarray, n: int) -> np.ndarray:
    """Flat OKLab (3 numbers per pixel, Float32 precision) of RGBA bytes."""
    px = np.asarray(data, dtype=np.int64).reshape(-1, 4)[:n]
    keys = (px[:, 0] << 16) | (px[:, 1] << 8) | px[:, 2]
    uniq, inv = np.unique(keys, return_inverse=True)
    lab = np.zeros((uniq.shape[0], 3))
    _lab_codes(uniq, lab)
    return lab[inv.reshape(-1)].reshape(-1)


@jit
def _enc(v):
    return 255 * (12.92 * v if v <= 0.0031308 else 1.055 * max(0.0, v) ** (1 / 2.4) - 0.055)


@jit
def lab_to_rgb(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (
        _enc(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
        _enc(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
        _enc(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    )


@jit
def _in_gamut(r, g, b):
    return r >= -0.5 and r <= 255.5 and g >= -0.5 and g <= 255.5 and b >= -0.5 and b <= 255.5


@jit
def from_oklab(L, a, b):
    """OKLab -> sRGB 0..255; out of gamut the chroma is reduced to the boundary (lightness and hue are kept)."""
    r, g, bl = lab_to_rgb(L, a, b)
    if not _in_gamut(r, g, bl):
        lo = 0.0
        hi = 1.0
        for _ in range(16):
            k = (lo + hi) / 2
            r, g, bl = lab_to_rgb(L, a * k, b * k)
            if _in_gamut(r, g, bl):
                lo = k
            else:
                hi = k
        r, g, bl = lab_to_rgb(L, a * lo, b * lo)
    return min(255.0, max(0.0, r)), min(255.0, max(0.0, g)), min(255.0, max(0.0, bl))


@jit
def _hex2(v):
    return round(min(255.0, max(0.0, v)))


@jit
def rgb_code(r, g, b):
    """Color code of the hex string the site receives (channels rounded like toHex)."""
    return (_hex2(r) << 16) | (_hex2(g) << 8) | _hex2(b)


@jit
def code_from_oklab(L, a, b):
    r, g, bl = from_oklab(L, a, b)
    return rgb_code(r, g, bl)


def to_hex(code: int) -> str:
    return f'#{int(code):06x}'


def from_hex(h: str) -> int:
    return int(h[1:7], 16)


def hex_of(r: float, g: float, b: float) -> str:
    return to_hex(rgb_code(r, g, b))
