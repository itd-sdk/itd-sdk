"""Image preparation: tone, edge-preserving smoothing, downsampling to the cell grid."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from itd.banner.jit import jit
from itd.banner.jsmath import f32, js_round


@dataclass
class Rgba:
    """Картинка RGBA построчно (как ImageData): data — uint8, width*height*4."""

    width: int
    height: int
    data: np.ndarray


@dataclass
class Adjust:
    brightness: float = 0
    """Яркость −1…1."""
    contrast: float = 0
    """Контраст −1…1."""
    saturation: float = 0
    """Насыщенность −1…1."""
    denoise: float = 0
    """Сглаживание с сохранением краёв (guided filter): 0 — выкл, до 3 — сила, дробная тоже."""


def _clamped(v: np.ndarray) -> np.ndarray:
    # Uint8ClampedArray: clamp and round half to even
    return np.rint(np.clip(np.nan_to_num(v, nan=0.0), 0, 255)).astype(np.uint8)


def adjust(src: Rgba, a: Adjust) -> Rgba:
    if not a.brightness and not a.contrast and not a.saturation and not a.denoise:
        return src
    data = src.data.copy()
    if a.brightness or a.contrast or a.saturation:
        c = 1 + a.contrast * 2 if a.contrast >= 0 else 1 + a.contrast
        b = a.brightness * 128
        s = 1 + a.saturation
        px = data.reshape(-1, 4).astype(np.float64)
        r, g, bl = px[:, 0], px[:, 1], px[:, 2]
        y = 0.299 * r + 0.587 * g + 0.114 * bl
        r = y + (r - y) * s
        g = y + (g - y) * s
        bl = y + (bl - y) * s
        out = data.reshape(-1, 4)
        out[:, 0] = _clamped((r - 128) * c + 128 + b)
        out[:, 1] = _clamped((g - 128) * c + 128 + b)
        out[:, 2] = _clamped((bl - 128) * c + 128 + b)
    if a.denoise > 0:
        data = _denoise(data, src.width, src.height, a.denoise)
    return Rgba(src.width, src.height, data)


# strength d -> radius 2d and threshold 0.0004*d^2; a fractional radius mixes the filters of the neighbouring integer radii
def _denoise(data: np.ndarray, w: int, h: int, d: float) -> np.ndarray:
    R = js_round(d * 2 * 1000) / 1000
    r0 = int(R // 1)
    f = R - r0
    eps = 0.0004 * d * d * 65025
    lo = _guided(data, w, h, r0, eps) if r0 > 0 else data
    if f == 0:
        return lo
    hi = _guided(data, w, h, r0 + 1, eps)
    return _clamped(lo.astype(np.float64) + (hi.astype(np.float64) - lo) * f)


@jit
def _box_mean(src, w, h, r):
    # sums over a sliding window, O(n) for any radius
    tmp = np.zeros(w * h)
    out = np.zeros(w * h)
    for y in range(h):
        s = 0.0
        o = y * w
        for x in range(-r, r + 1):
            s += src[o + min(w - 1, max(0, x))]
        for x in range(w):
            tmp[o + x] = f32(s / (2 * r + 1))
            s += src[o + min(w - 1, x + r + 1)] - src[o + max(0, x - r)]
    for x in range(w):
        s = 0.0
        for y in range(-r, r + 1):
            s += tmp[min(h - 1, max(0, y)) * w + x]
        for y in range(h):
            out[y * w + x] = f32(s / (2 * r + 1))
            s += tmp[min(h - 1, y + r + 1) * w + x] - tmp[max(0, y - r) * w + x]
    return out


@jit
def _guided_ab(m, m2, eps, A, B):
    for i in range(m.shape[0]):
        v = m2[i] - m[i] * m[i]
        a = v / (v + eps)
        A[i] = f32(a)
        B[i] = f32(m[i] - a * m[i])


def _guided(data: np.ndarray, w: int, h: int, r: int, eps: float) -> np.ndarray:
    # self-guided filter (He et al.) per channel: smooths noise, keeps edges
    n = w * h
    out = data.copy()
    px = data.reshape(-1, 4)
    for ch in range(3):
        I = px[:, ch].astype(np.float64)
        m = _box_mean(I, w, h, r)
        m2 = _box_mean(I * I, w, h, r)
        A = np.zeros(n)
        B = np.zeros(n)
        _guided_ab(m, m2, eps, A, B)
        mA = _box_mean(A, w, h, r)
        mB = _box_mean(B, w, h, r)
        out.reshape(-1, 4)[:, ch] = _clamped(mA * I + mB)
    return out


def downsample(src: Rgba, cell: int) -> Rgba:
    """Среднее по клеткам cell×cell (последняя клетка может быть неполной)."""
    if cell == 1:
        return src
    w, h = src.width, src.height
    cols, rows = -(-w // cell), -(-h // cell)
    px = src.data.reshape(h, w, 4).astype(np.int64)
    sums = np.add.reduceat(np.add.reduceat(px, np.arange(0, h, cell), axis=0), np.arange(0, w, cell), axis=1)
    ys = np.minimum(np.arange(rows) * cell + cell, h) - np.arange(rows) * cell
    xs = np.minimum(np.arange(cols) * cell + cell, w) - np.arange(cols) * cell
    cnt = (ys[:, None] * xs[None, :]).astype(np.float64)
    out = np.empty((rows, cols, 4), dtype=np.uint8)
    for k in range(3):
        out[:, :, k] = _clamped(sums[:, :, k] / cnt)
    out[:, :, 3] = 255
    return Rgba(cols, rows, out.reshape(-1))


def fit_image(image, mode: str = 'cover', width: int = 1100, height: int = 380) -> Rgba:
    """Картинка (путь, байты, файл или PIL.Image) в кадре width×height на белом фоне.

    mode: `cover` — заполнить кадр и обрезать лишнее по центру, `contain` — вписать целиком (поля белые),
    `stretch` — растянуть без сохранения пропорций.
    """
    try:
        from PIL import Image
    except ModuleNotFoundError:
        raise ImportError('Pillow is required to read images. Install by running "uv add itd-sdk[banner]" (or "pip install itd-sdk[banner]")')
    from io import BytesIO
    from pathlib import Path

    if isinstance(image, (str, Path)):
        img = Image.open(image)
    elif isinstance(image, (bytes, bytearray)):
        img = Image.open(BytesIO(image))
    elif hasattr(image, 'read'):
        img = Image.open(image)
    else:
        img = image
    img = img.convert('RGBA')
    iw, ih = img.size
    if mode == 'stretch':
        placed = img.resize((width, height), Image.Resampling.LANCZOS)
        ox = oy = 0
    else:
        scale = max(width / iw, height / ih) if mode == 'cover' else min(width / iw, height / ih)
        sw, sh = max(1, round(iw * scale)), max(1, round(ih * scale))
        placed = img.resize((sw, sh), Image.Resampling.LANCZOS)
        ox, oy = (width - sw) // 2, (height - sh) // 2
    canvas = Image.new('RGBA', (width, height), (255, 255, 255, 255))
    canvas.alpha_composite(placed, (max(0, ox), max(0, oy)), (max(0, -ox), max(0, -oy)))
    data = np.asarray(canvas.convert('RGB'), dtype=np.uint8)
    rgba = np.empty((height, width, 4), dtype=np.uint8)
    rgba[:, :, :3] = data
    rgba[:, :, 3] = 255
    return Rgba(width, height, rgba.reshape(-1))


def rgba_from_array(arr: np.ndarray) -> Rgba:
    """Rgba из массива h×w×3 или h×w×4 (uint8); прозрачное ложится на белый."""
    a = np.asarray(arr)
    h, w = a.shape[:2]
    out = np.empty((h, w, 4), dtype=np.uint8)
    if a.shape[2] == 4:
        k = a[:, :, 3:4].astype(np.float64) / 255
        out[:, :, :3] = _clamped(a[:, :, :3] * k + 255 * (1 - k))
    else:
        out[:, :, :3] = a[:, :, :3]
    out[:, :, 3] = 255
    return Rgba(w, h, out.reshape(-1))
