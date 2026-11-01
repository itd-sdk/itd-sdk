"""Engine "strokes": greedily puts a stroke where the difference from the target is largest now, with the color that fixes
that place best; the shape is found by hill climbing. No palette: every stroke has its own color. Large to small happens
by itself: while the canvas is empty large strokes pay off most, later only small errors are left.

The search runs on a half size copy of the picture in OKLab; a stroke is a polyline of a round brush, as the site draws it.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np

from itd.banner.color import code_from_oklab, lab_of, oklab, oklab_code, to_hex
from itd.banner.image import Rgba, downsample
from itd.banner.jit import jit
from itd.banner.jsmath import f32, hypot2, js_cos, js_round, js_sin
from itd.banner.limits import MAX_OPS, MAX_WIDTH, Op

SCALE = 2  # search on a half size picture: four times faster, a stroke thinner than 2 px does not pay off anyway
CANDIDATES = 32  # random strokes at a point with a large error
CLIMB = 256  # hill climbing steps for the best of them
MAX_POINTS = 8  # points in a stroke: a bend lets the stroke follow a contour
MAX_LEN = 8  # a segment is not longer than 8 radii, otherwise climbing inflates the stroke
RESAMPLE = 25  # how often to recompute where the error is

# integer state of the run
I_SEED, I_STAMP, I_COUNT, I_DONE = range(4)


@jit
def _rnd(st):
    st[I_SEED] = (st[I_SEED] * 1664525 + 1013904223) & 0xFFFFFFFF
    return st[I_SEED] / 4294967296


@jit
def _dist(C, T, i):
    j = i * 3
    dl = C[j] - T[j]
    da = C[j + 1] - T[j + 1]
    db = C[j + 2] - T[j + 2]
    return math.sqrt(dl * dl + da * da + db * db)


@jit
def _cover(P, r, w, h, idx, cov, mark, most, st):
    # pixels touched by the stroke and the share of paint on each (antialiased edge, as the site renders);
    # every segment in its own frame, on joins the larger coverage wins
    m = P.shape[0] >> 1
    e = r + 1
    lim = (r + 0.5) * (r + 0.5)
    ns = max(1, m - 1)
    k = 0
    st[I_STAMP] += 1
    stamp = st[I_STAMP]
    for j in range(ns):
        a = min(j, m - 1) * 2
        b = min(j + 1, m - 1) * 2
        ax = P[a]
        ay = P[a + 1]
        dx = P[b] - ax
        dy = P[b + 1] - ay
        l2 = dx * dx + dy * dy
        inv = 1 / l2 if l2 else 0.0
        x0 = max(0, math.floor(min(ax, P[b]) - e))
        x1 = min(w - 1, math.ceil(max(ax, P[b]) + e))
        y0 = max(0, math.floor(min(ay, P[b + 1]) - e))
        y1 = min(h - 1, math.ceil(max(ay, P[b + 1]) + e))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                px = x + 0.5
                py = y + 0.5
                t = ((px - ax) * dx + (py - ay) * dy) * inv
                t = 0.0 if t < 0 else 1.0 if t > 1 else t
                ex = ax + t * dx - px
                ey = ay + t * dy - py
                d2 = ex * ex + ey * ey
                if d2 >= lim:
                    continue
                c = min(1.0, r + 0.5 - math.sqrt(d2))
                i = y * w + x
                if mark[i] != stamp:
                    mark[i] = stamp
                    most[i] = f32(c)
                    idx[k] = i
                    k += 1
                elif c > most[i]:
                    most[i] = f32(c)
    for q in range(k):
        cov[q] = most[idx[q]]
    return k


@jit
def _score(P, r, w, h, T, C, E, idx, cov, mark, most, st):
    # best stroke color (least squares with the antialiased edge) and the gain in the sum of ΔE
    k = _cover(P, r, w, h, idx, cov, mark, most, st)
    sa = 0.0
    sl = 0.0
    sA = 0.0
    sB = 0.0
    for q in range(k):
        j = idx[q] * 3
        a = cov[q]
        b = 1 - a
        sa += a * a
        sl += a * (T[j] - b * C[j])
        sA += a * (T[j + 1] - b * C[j + 1])
        sB += a * (T[j + 2] - b * C[j + 2])
    if not sa:
        return 0.0, 0.0, 0.0, 0.0
    L = sl / sa
    A = sA / sa
    B = sB / sa
    gain = 0.0
    for q in range(k):
        i = idx[q]
        j = i * 3
        a = cov[q]
        b = 1 - a
        dl = b * C[j] + a * L - T[j]
        da = b * C[j + 1] + a * A - T[j + 1]
        db = b * C[j + 2] + a * B - T[j + 2]
        gain += E[i] - math.sqrt(dl * dl + da * da + db * db)
    return gain, L, A, B


@jit
def _fits(P, r):
    # segments not longer than MAX_LEN radii (but not shorter than 8 px of the search, so a thin stroke can follow a line)
    lim = MAX_LEN * max(1.0, r)
    lim = lim * lim
    for j in range(2, P.shape[0], 2):
        dx = P[j] - P[j - 2]
        dy = P[j + 1] - P[j - 1]
        if dx * dx + dy * dy > lim:
            return False
    return True


@jit
def _mutate(P, r, r_max, st):
    # climbing step: move a point, change the width, add a point (extend or bend) or remove one
    m = P.shape[0] >> 1
    step = max(0.5, r) * (_rnd(st) * 2 - 1)
    u = _rnd(st)
    if u < 0.15:
        return P.copy(), min(r_max, max(0.5, r * (1 + (_rnd(st) - 0.5) * 0.6)))
    if u < 0.3 and m < MAX_POINTS:
        j = math.floor(_rnd(st) * (m + 1))
        out = np.empty(P.shape[0] + 2)
        if j == 0 or j == m:
            # extend from the end in the direction of the last segment with a turn
            e = m - 1 if j else 0
            f = max(0, m - 2) if j else min(1, m - 1)
            dx = P[e * 2] - P[f * 2]
            dy = P[e * 2 + 1] - P[f * 2 + 1]
            ln = hypot2(dx, dy)
            if not ln:
                th = _rnd(st) * math.pi * 2
                dx = js_cos(th)
                dy = js_sin(th)
                ln = 1.0
            length = max(1.0, r) * (1 + _rnd(st) * 3)
            th = (_rnd(st) - 0.5) * 1.5
            c = js_cos(th)
            s = js_sin(th)
            nx = P[e * 2] + (dx * c - dy * s) / ln * length
            ny = P[e * 2 + 1] + (dx * s + dy * c) / ln * length
            if j:
                out[: P.shape[0]] = P
                out[P.shape[0]] = nx
                out[P.shape[0] + 1] = ny
            else:
                out[0] = nx
                out[1] = ny
                out[2:] = P
        else:
            # bend: the middle of a segment shifted across it
            ax = P[(j - 1) * 2]
            ay = P[(j - 1) * 2 + 1]
            bx = P[j * 2]
            by = P[j * 2 + 1]
            ln = hypot2(bx - ax, by - ay)
            if not ln:
                ln = 1.0
            out[: j * 2] = P[: j * 2]
            out[j * 2] = (ax + bx) / 2 - (by - ay) / ln * step
            out[j * 2 + 1] = (ay + by) / 2 + (bx - ax) / ln * step
            out[j * 2 + 2 :] = P[j * 2 :]
        return out, r
    if u < 0.4 and m > 2:
        j = math.floor(_rnd(st) * m) * 2
        out = np.empty(P.shape[0] - 2)
        out[:j] = P[:j]
        out[j:] = P[j + 2 :]
        return out, r
    out = P.copy()
    out[math.floor(_rnd(st) * P.shape[0])] += step
    return out, r


@jit
def _resample(E, cum, n):
    s = 0.0
    for i in range(n):
        s += E[i] * E[i]
        cum[i] = s


@jit
def _pick(cum, n, st):
    # where to start a stroke: the larger the error, the more likely
    v = _rnd(st) * cum[n - 1]
    lo = 0
    hi = n - 1
    while lo < hi:
        m = (lo + hi) >> 1
        if cum[m] < v:
            lo = m + 1
        else:
            hi = m
    return lo


@jit
def _init_e(C, T, n):
    E = np.zeros(n)
    for i in range(n):
        E[i] = f32(_dist(C, T, i))
    return E


@jit
def _run(s0, s1, w, h, T, C, E, idx, cov, cum, mark, most, st, out_color, out_width, out_pts, out_n):
    n = w * h
    r_max = MAX_WIDTH / 2 / SCALE
    for s in range(s0, s1):
        if s % RESAMPLE == 0:
            _resample(E, cum, n)
        if not cum[n - 1]:
            st[I_DONE] = 1
            return
        found = False
        best = np.empty(4)
        best_r = 0.0
        bg = 0.0
        bL = 0.0
        bA = 0.0
        bB = 0.0
        for _ in range(CANDIDATES):
            q = _pick(cum, n, st)
            x = q % w + 0.5
            y = (q - q % w) // w + 0.5
            rr = _rnd(st)
            r = max(0.5, r_max * (rr * rr))
            th = _rnd(st) * math.pi
            half = _rnd(st) * r * 2
            cand = np.empty(4)
            cand[0] = x - js_cos(th) * half
            cand[1] = y - js_sin(th) * half
            cand[2] = x + js_cos(th) * half
            cand[3] = y + js_sin(th) * half
            g, L, A, B = _score(cand, r, w, h, T, C, E, idx, cov, mark, most, st)
            if g > bg:
                bg, bL, bA, bB = g, L, A, B
                best = cand
                best_r = r
                found = True
        if not found:
            continue
        for _ in range(CLIMB):
            mp, mr = _mutate(best, best_r, r_max, st)
            if not _fits(mp, mr):
                continue
            g, L, A, B = _score(mp, mr, w, h, T, C, E, idx, cov, mark, most, st)
            if g > bg:
                bg, bL, bA, bB = g, L, A, B
                best = mp
                best_r = mr
        # the color is rounded to #rrggbb as the site takes it; the canvas is updated with that color
        code = code_from_oklab(bL, bA, bB)
        l0, l1, l2 = oklab_code(code)
        k = _cover(best, best_r, w, h, idx, cov, mark, most, st)
        for q in range(k):
            i = idx[q]
            j = i * 3
            a = cov[q]
            C[j] = f32(C[j] + (l0 - C[j]) * a)
            C[j + 1] = f32(C[j + 1] + (l1 - C[j + 1]) * a)
            C[j + 2] = f32(C[j + 2] + (l2 - C[j + 2]) * a)
            E[i] = f32(_dist(C, T, i))
        o = st[I_COUNT]
        npts = 0
        for j in range(0, best.shape[0], 2):
            px = js_round(best[j] * SCALE * 100) / 100
            py = js_round(best[j + 1] * SCALE * 100) / 100
            if not npts or out_pts[o, npts - 1, 0] != px or out_pts[o, npts - 1, 1] != py:
                out_pts[o, npts, 0] = px
                out_pts[o, npts, 1] = py
                npts += 1
        out_n[o] = npts
        out_color[o] = code
        out_width[o] = min(float(MAX_WIDTH), js_round(best_r * 2 * SCALE * 100) / 100)
        st[I_COUNT] += 1


def strokes(src: Rgba, count: int = MAX_OPS, on_progress: Callable[[float], None] | None = None) -> list[Op]:
    """Кладёт count мазков (сколько разрешает сайт по умолчанию)."""
    img = downsample(src, SCALE)
    w, h = img.width, img.height
    n = w * h
    T = lab_of(img.data, n)
    white = oklab(255, 255, 255)
    C = np.tile(np.array([f32(v) for v in white]), n)
    E = _init_e(C, T, n)
    idx = np.zeros(n, dtype=np.int64)
    cov = np.zeros(n)
    cum = np.zeros(n)
    mark = np.zeros(n, dtype=np.int64)
    most = np.zeros(n)
    st = np.zeros(4, dtype=np.int64)
    st[I_SEED] = 0x9E3779B9
    out_color = np.zeros(count, dtype=np.int64)
    out_width = np.zeros(count)
    out_pts = np.zeros((count, MAX_POINTS, 2))
    out_n = np.zeros(count, dtype=np.int64)
    chunk = RESAMPLE * 4
    for s0 in range(0, count, chunk):
        if on_progress:
            on_progress(s0 / count)
        _run(s0, min(count, s0 + chunk), w, h, T, C, E, idx, cov, cum, mark, most, st, out_color, out_width, out_pts, out_n)
        if st[I_DONE]:
            break
    if on_progress:
        on_progress(1)
    return [Op('brush', to_hex(out_color[o]), float(out_width[o]), [(float(x), float(y)) for x, y in out_pts[o, : out_n[o]]]) for o in range(int(st[I_COUNT]))]
