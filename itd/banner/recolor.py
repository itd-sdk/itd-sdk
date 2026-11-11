"""Recoloring after any engine: same stroke shapes, color closest to the target where the strokes are visible on top.

The palette is shared by the whole picture while a region lies in one place, where the real color is slightly different.
Touching strokes of one color are recolored together: a region drawn with many strokes (wide band, narrow fills, bridges)
would otherwise show a grid of straight seams.
"""

import math

import numpy as np

from itd.banner.color import code_from_oklab, oklab_code
from itd.banner.jit import jit
from itd.banner.limits import Op
from itd.banner.raster import T_ERASER, Coverage, _clear, cover_op, pack


@jit
def _find(parent, k):
    while parent[k] != k:
        parent[k] = parent[parent[k]]
        k = parent[k]
    return k


@jit
def _join(parent, colors, tools, a, b):
    if b < 0 or a == b or colors[a] != colors[b] or tools[b] == T_ERASER:
        return
    ra = _find(parent, a)
    rb = _find(parent, b)
    if ra != rb:
        parent[ra] = rb


@jit
def _err(lst, a, b, target, L, A, B):
    s = 0.0
    for q in range(a, b):
        j = lst[q] * 3
        dl = target[j] - L
        da = target[j + 1] - A
        db = target[j + 2] - B
        s += math.sqrt(dl * dl + da * da + db * db)
    return s


@jit
def _recolor(tools, colors, widths, starts, pts, target, w, h, cov, touched):
    n = w * h
    m = tools.shape[0]
    owner = np.full(n, -1, dtype=np.int64)
    top = np.full(n, -1, dtype=np.int64)
    # top - the last stroke that touched the pixel; owner - the same one if it covered the pixel fully (mixed edges belong to nobody)
    for k in range(m):
        c = cover_op(cov, touched, 0, w, h, tools[k], widths[k], pts[starts[k] : starts[k + 1]])
        for t in range(c):
            i = touched[t]
            top[i] = k
            owner[i] = k if cov[i] >= 0.999 else -1
        _clear(cov, touched, c)
    # groups: strokes of one color lying on top in neighbouring pixels
    parent = np.arange(m)
    i = 0
    for y in range(h):
        for x in range(w):
            a = top[i]
            if a >= 0 and tools[a] != T_ERASER:
                if x + 1 < w:
                    _join(parent, colors, tools, a, top[i + 1])
                if y + 1 < h:
                    _join(parent, colors, tools, a, top[i + w])
            i += 1
    group = np.empty(m, dtype=np.int64)
    for k in range(m):
        group[k] = _find(parent, k)
    start = np.zeros(m + 1, dtype=np.int64)
    for i in range(n):
        if owner[i] >= 0:
            start[group[owner[i]] + 1] += 1
    for k in range(m):
        start[k + 1] += start[k]
    fill = start[:m].copy()
    lst = np.zeros(start[m], dtype=np.int64)
    for i in range(n):
        if owner[i] >= 0:
            g = group[owner[i]]
            lst[fill[g]] = i
            fill[g] += 1

    color = colors.copy()
    for g in range(m):
        a = start[g]
        b = start[g + 1]
        if group[g] != g or a == b or tools[g] == T_ERASER:
            continue
        L0, A0, B0 = oklab_code(colors[g])
        # geometric median (Weiszfeld): ΔE is a sum of distances, a plain mean is pulled by foreign pixels under the strokes
        L, A, B = L0, A0, B0
        for _ in range(5):
            sw = sl = sa = sb = 0.0
            for q in range(a, b):
                j = lst[q] * 3
                dl = target[j] - L
                da = target[j + 1] - A
                db = target[j + 2] - B
                wt = 1 / max(0.004, math.sqrt(dl * dl + da * da + db * db))
                sw += wt
                sl += target[j] * wt
                sa += target[j + 1] * wt
                sb += target[j + 2] * wt
            L = sl / sw
            A = sa / sw
            B = sb / sw
        code = code_from_oklab(L, A, B)
        if code != colors[g]:
            L1, A1, B1 = oklab_code(code)
            if _err(lst, a, b, target, L1, A1, B1) < _err(lst, a, b, target, L0, A0, B0):
                color[g] = code
    out = np.empty(m, dtype=np.int64)
    for k in range(m):
        out[k] = color[group[k]]
    return out


def recolor(ops: list[Op], target_lab: np.ndarray, w: int, h: int) -> list[Op]:
    """target_lab: OKLab оригинала, 3 числа на пиксель. Возвращает новые штрихи; группа без своих пикселей не меняется."""
    from itd.banner.color import to_hex

    if not ops:
        return []
    p = pack(ops)
    cv = Coverage(w, h)
    codes = _recolor(p.tools, p.colors, p.widths, p.starts, p.pts, target_lab, w, h, cv.cov, cv.touched)
    return [o if codes[k] == p.colors[k] else Op(o.tool, to_hex(codes[k]), o.width, o.points) for k, o in enumerate(ops)]
