"""Copy of the site renderer: canvas 2D, white background, round caps and joins, antialiasing.

Checked against PNGs rendered by the site server. Pixel coverage is the share of its area under the brush, like canvas:
a 1 px dot covers only pi/4 of a pixel, a line end ~0.9, and the white canvas shows through the rest.
"""

import math

import numpy as np

from itd.banner.jit import jit
from itd.banner.jsmath import f32, hypot2, u8c
from itd.banner.limits import Op, Packed, pack

# subpixels per pixel side at ends and joins of a thin brush; along the body the formula is enough
SS = 10

T_BRUSH, T_LINE, T_RECT, T_CIRCLE, T_ERASER = range(5)


class Coverage:
    """Покрытие одного штриха: доля пикселя 0…1 по индексам из touched."""

    def __init__(self, w: int, h: int):
        self.w = w
        self.h = h
        self.cov = np.zeros(w * h)
        self.touched = np.zeros(w * h, dtype=np.int64)
        self.n = 0

    def clear(self):
        _clear(self.cov, self.touched, self.n)
        self.n = 0


@jit
def _clear(cov, touched, n):
    for k in range(n):
        cov[touched[k]] = 0.0


@jit
def _put(cov, touched, n, i, c):
    if c <= cov[i]:
        return n
    if cov[i] == 0:
        touched[n] = i
        n += 1
    cov[i] = f32(c)
    return n


@jit
def capsule(cov, touched, n, w, h, ax, ay, bx, by, r):
    """Капсула радиуса r вокруг отрезка; сглаживание по расстоянию от центра пикселя."""
    e = r + 1
    x0 = max(0, math.floor(min(ax, bx) - e))
    x1 = min(w - 1, math.ceil(max(ax, bx) + e))
    y0 = max(0, math.floor(min(ay, by) - e))
    y1 = min(h - 1, math.ceil(max(ay, by) + e))
    if x0 > x1 or y0 > y1:
        return n
    dx = bx - ax
    dy = by - ay
    l2 = dx * dx + dy * dy
    inv = 1 / l2 if l2 else 0.0
    lim = (r + 0.5) * (r + 0.5)
    core = (r - 0.5) * (r - 0.5) if r > 0.5 else -1.0
    for y in range(y0, y1 + 1):
        py = y + 0.5
        for x in range(x0, x1 + 1):
            px = x + 0.5
            t = ((px - ax) * dx + (py - ay) * dy) * inv
            t = 0.0 if t < 0 else 1.0 if t > 1 else t
            ex = ax + t * dx - px
            ey = ay + t * dy - py
            d2 = ex * ex + ey * ey
            if d2 >= lim:
                continue
            n = _put(cov, touched, n, y * w + x, 1.0 if d2 <= core else min(1.0, r + 0.5 - math.sqrt(d2)))
    return n


@jit
def _seg_d2(qx, qy, ax, ay, dx, dy, inv):
    t = ((qx - ax) * dx + (qy - ay) * dy) * inv
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    ex = ax + t * dx - qx
    ey = ay + t * dy - qy
    return ex * ex + ey * ey


@jit
def _near_v(x, y, vx, vy, r2):
    # the tip circle of radius r at vertex (vx, vy) touches the area of pixel (x, y)
    ex = max(abs(vx - x - 0.5) - 0.5, 0.0)
    ey = max(abs(vy - y - 0.5) - 0.5, 0.0)
    return ex * ex + ey * ey < r2


@jit
def chain(cov, touched, n, w, h, p, r):
    """Ломаная кистью радиуса r с круглыми концами и стыками (одна точка = кружок).

    У широкой кисти край почти прямой и доля = r + 0.5 − расстояние до центра. У тонкой (уже 3 px) у концов и стыков
    край круглый на масштабе пикселя: там подточки, и подточка закрыта, если её закрывает и соседнее звено.
    """
    m = p.shape[0]
    segs = max(1, m - 1)
    if r >= 1.5:
        for k in range(segs):
            b = min(k + 1, m - 1)
            n = capsule(cov, touched, n, w, h, p[k, 0], p[k, 1], p[b, 0], p[b, 1], r)
        return n
    e = r + 1
    hi = (r + 0.7072) * (r + 0.7072)
    lo = (r - 0.7072) * (r - 0.7072) if r > 0.7072 else -1.0
    r2 = r * r
    ax = np.zeros(segs)
    ay = np.zeros(segs)
    dx = np.zeros(segs)
    dy = np.zeros(segs)
    inv = np.zeros(segs)
    for k in range(segs):
        b = min(k + 1, m - 1)
        ax[k] = p[k, 0]
        ay[k] = p[k, 1]
        dx[k] = p[b, 0] - p[k, 0]
        dy[k] = p[b, 1] - p[k, 1]
        l2 = dx[k] * dx[k] + dy[k] * dy[k]
        inv[k] = 1 / l2 if l2 else 0.0
    for k in range(segs):
        bx = ax[k] + dx[k]
        by = ay[k] + dy[k]
        x0 = max(0, math.floor(min(ax[k], bx) - e))
        x1 = min(w - 1, math.ceil(max(ax[k], bx) + e))
        y0 = max(0, math.floor(min(ay[k], by) - e))
        y1 = min(h - 1, math.ceil(max(ay[k], by) + e))
        kp = k - 1 if k > 0 else -1
        kn = k + 1 if k + 1 < segs else -1
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                c2 = _seg_d2(x + 0.5, y + 0.5, ax[k], ay[k], dx[k], dy[k], inv[k])
                if c2 >= hi:
                    continue
                if c2 <= lo:
                    n = _put(cov, touched, n, y * w + x, 1.0)
                    continue
                near_a = _near_v(x, y, ax[k], ay[k], r2)
                near_b = _near_v(x, y, bx, by, r2)
                if near_a and not near_b and k > 0:
                    continue  # this join was already counted with the previous segment
                if not near_a and not near_b:
                    n = _put(cov, touched, n, y * w + x, min(1.0, r + 0.5 - math.sqrt(c2)))
                    continue
                inside = 0
                for sy in range(SS):
                    qy = y + (sy + 0.5) / SS
                    for sx in range(SS):
                        qx = x + (sx + 0.5) / SS
                        if (
                            _seg_d2(qx, qy, ax[k], ay[k], dx[k], dy[k], inv[k]) <= r2
                            or (kp >= 0 and _seg_d2(qx, qy, ax[kp], ay[kp], dx[kp], dy[kp], inv[kp]) <= r2)
                            or (kn >= 0 and _seg_d2(qx, qy, ax[kn], ay[kn], dx[kn], dy[kn], inv[kn]) <= r2)
                        ):
                            inside += 1
                if inside:
                    n = _put(cov, touched, n, y * w + x, inside / (SS * SS))
    return n


@jit
def ring(cov, touched, n, w, h, cx, cy, R, r):
    """Кольцо: окружность радиуса R, обведённая кистью ширины 2r."""
    e = R + r + 1
    x0 = max(0, math.floor(cx - e))
    x1 = min(w - 1, math.ceil(cx + e))
    y0 = max(0, math.floor(cy - e))
    y1 = min(h - 1, math.ceil(cy + e))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = abs(hypot2(x + 0.5 - cx, y + 0.5 - cy) - R)
            if d < r + 0.5:
                n = _put(cov, touched, n, y * w + x, min(1.0, r + 0.5 - d))
    return n


@jit
def cover_op(cov, touched, n, w, h, tool, width, p):
    r = width / 2
    last = p.shape[0] - 1
    if tool == T_CIRCLE:
        return ring(cov, touched, n, w, h, p[0, 0], p[0, 1], hypot2(p[last, 0] - p[0, 0], p[last, 1] - p[0, 1]), r)
    if tool == T_RECT:
        x0 = p[0, 0]
        y0 = p[0, 1]
        x1 = p[last, 0]
        y1 = p[last, 1]
        n = capsule(cov, touched, n, w, h, x0, y0, x1, y0, r)
        n = capsule(cov, touched, n, w, h, x1, y0, x1, y1, r)
        n = capsule(cov, touched, n, w, h, x1, y1, x0, y1, r)
        return capsule(cov, touched, n, w, h, x0, y1, x0, y0, r)
    return chain(cov, touched, n, w, h, p, r)  # one point is a dot, as the server draws it


@jit
def composite(rgb, cov, touched, n, c):
    """Накладывает покрытие цветом 0xRRGGBB на холст RGB (3 числа на пиксель, 0…255)."""
    cr = (c >> 16) & 255
    cg = (c >> 8) & 255
    cb = c & 255
    for k in range(n):
        i = touched[k]
        a = cov[i]
        j = i * 3
        rgb[j] = f32(rgb[j] + (cr - rgb[j]) * a)
        rgb[j + 1] = f32(rgb[j + 1] + (cg - rgb[j + 1]) * a)
        rgb[j + 2] = f32(rgb[j + 2] + (cb - rgb[j + 2]) * a)


@jit
def _render(tools, colors, widths, starts, pts, w, h, cov, touched):
    rgb = np.full(w * h * 3, 255.0)
    for k in range(tools.shape[0]):
        n = cover_op(cov, touched, 0, w, h, tools[k], widths[k], pts[starts[k] : starts[k + 1]])
        composite(rgb, cov, touched, n, 0xFFFFFF if tools[k] == T_ERASER else colors[k])
        _clear(cov, touched, n)
    return rgb


def render_packed(p: Packed, w: int, h: int) -> np.ndarray:
    cv = Coverage(w, h)
    return _render(p.tools, p.colors, p.widths, p.starts, p.pts, w, h, cv.cov, cv.touched)


def render_ops(ops: list[Op], w: int, h: int) -> np.ndarray:
    """Рисует штрихи на белом холсте w×h: RGB, 3 числа на пиксель (точность Float32)."""
    return render_packed(pack(ops), w, h)


@jit
def _to_rgba(rgb, n):
    out = np.empty(n * 4, dtype=np.uint8)
    for i in range(n):
        out[i * 4] = u8c(rgb[i * 3])
        out[i * 4 + 1] = u8c(rgb[i * 3 + 1])
        out[i * 4 + 2] = u8c(rgb[i * 3 + 2])
        out[i * 4 + 3] = 255
    return out


def to_rgba(rgb: np.ndarray, n: int) -> np.ndarray:
    """RGB → RGBA байты (для превью и сравнения)."""
    return _to_rgba(rgb, n)
