"""How close the result is to the target: ΔE in OKLab ×100 (around 2 is nearly invisible)."""

from dataclasses import dataclass

import numpy as np

from itd.banner.color import oklab_code
from itd.banner.jit import jit
from itd.banner.jsmath import hypot3, js_round


@dataclass
class Quality:
    dE: float
    """Средний ΔE×100 по всем пикселям."""
    bad: float
    """Доля пикселей с заметным отличием, ΔE×100 > 5."""
    map: np.ndarray
    """ΔE×100 на пиксель, обрезано до 255 (для тепловой карты)."""


@jit
def _codes(rgb, n):
    out = np.empty(n, dtype=np.int64)
    for i in range(n):
        out[i] = (int(js_round(rgb[i * 3])) << 16) | (int(js_round(rgb[i * 3 + 1])) << 8) | int(js_round(rgb[i * 3 + 2]))
    return out


@jit
def _compare(lab, inv, target, n, out):
    s = 0.0
    bad = 0
    for i in range(n):
        k = inv[i]
        d = hypot3(lab[k, 0] - target[i * 3], lab[k, 1] - target[i * 3 + 1], lab[k, 2] - target[i * 3 + 2]) * 100
        s += d
        if d > 5:
            bad += 1
        out[i] = 255 if d > 255 else int(d)
    return s, bad


@jit
def _lab_codes_f64(codes, out):
    for k in range(codes.shape[0]):
        out[k, 0], out[k, 1], out[k, 2] = oklab_code(codes[k])


def compare(rgb: np.ndarray, target: np.ndarray, n: int) -> Quality:
    codes = _codes(rgb, n)
    uniq, inv = np.unique(codes, return_inverse=True)
    lab = np.zeros((uniq.shape[0], 3))
    _lab_codes_f64(uniq, lab)
    out = np.zeros(n, dtype=np.uint8)
    s, bad = _compare(lab, inv.reshape(-1).astype(np.int64), target, n, out)
    return Quality(s / n, bad / n, out)
