"""Cleaning the color map from noise."""

import math

import numpy as np

from itd.banner.jit import jit

N8X = np.array([-1, 0, 1, -1, 1, -1, 0, 1], dtype=np.int64)
N8Y = np.array([-1, -1, -1, 0, 0, 1, 1, 1], dtype=np.int64)
PX = np.array([-1, 1, 0, 0, -1, 1, -1, 1], dtype=np.int64)
PY = np.array([0, 0, -1, 1, -1, -1, 1, 1], dtype=np.int64)
PW = np.array([1, 1, 1, 1, math.sqrt(0.5), math.sqrt(0.5), math.sqrt(0.5), math.sqrt(0.5)])

# transition: the color lies on the segment between the neighbour colors no closer than EDGE_T of its length to the ends
# and no farther than EDGE_PERP of the length from it
EDGE_T = 0.12
EDGE_PERP = 0.25
# a piece is thin if this share of its cells has a neighbour of another color
EDGE_THIN = 0.85
# the sides must differ at least by this (OKLab), otherwise it is a step of a smooth gradient, not an antialiased edge
EDGE_SIDES = 0.3

# visibility cleaning: a spot with contrast MERGE_DREF goes away below minArea, twice as contrasting - below half of it;
# the contrast influence is limited by MERGE_BOOST both ways
MERGE_DREF = 0.0125
MERGE_BOOST = 16


@jit
def despeckle(cols, rows, label, K):
    """Клетка, у которой в окне 3×3 почти нет своего цвета, берёт цвет большинства (тонкие линии не трогает)."""
    out = label.copy()
    cnt = np.zeros(K, dtype=np.int64)
    for y in range(rows):
        for x in range(cols):
            i = y * cols + x
            own = label[i]
            y0 = max(0, y - 1)
            y1 = min(rows - 1, y + 1)
            x0 = max(0, x - 1)
            x1 = min(cols - 1, x + 1)
            best = own
            best_n = 0
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    l = label[yy * cols + xx]
                    cnt[l] += 1
                    c = cnt[l]
                    if l != own and c > best_n:
                        best_n = c
                        best = l
            if cnt[own] <= 2 and best_n >= 5:
                out[i] = best
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    cnt[label[yy * cols + xx]] = 0
    return out


@jit
def smooth_labels(cols, rows, label, K, min_votes=0):
    """Фильтр большинства 3×3; min_votes > 0 — мягкий проход: цвет меняется, только если чужой цвет занимает не меньше min_votes клеток окна."""
    out = label.copy()
    cnt = np.zeros(K, dtype=np.int64)
    for y in range(rows):
        for x in range(cols):
            i = y * cols + x
            y0 = max(0, y - 1)
            y1 = min(rows - 1, y + 1)
            x0 = max(0, x - 1)
            x1 = min(cols - 1, x + 1)
            best = label[i]
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    l = label[yy * cols + xx]
                    cnt[l] += 1
                    if cnt[l] > cnt[best]:
                        best = l
            if cnt[best] >= min_votes:
                out[i] = best
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    cnt[label[yy * cols + xx]] = 0
    return out


@jit
def _nb4(i, k, cols, total):
    x = i % cols
    if k == 0:
        return i - 1 if x > 0 else -1
    if k == 1:
        return i + 1 if x < cols - 1 else -1
    if k == 2:
        return i - cols if i >= cols else -1
    return i + cols if i + cols < total else -1


@jit
def _between(c, a, b, lab):
    # squared distance of color c from the segment a-b in shares of its length, or inf if c does not lie between them
    ux = lab[b * 3] - lab[a * 3]
    uy = lab[b * 3 + 1] - lab[a * 3 + 1]
    uz = lab[b * 3 + 2] - lab[a * 3 + 2]
    u2 = ux * ux + uy * uy + uz * uz
    if u2 < EDGE_SIDES * EDGE_SIDES:
        return np.inf
    vx = lab[c * 3] - lab[a * 3]
    vy = lab[c * 3 + 1] - lab[a * 3 + 1]
    vz = lab[c * 3 + 2] - lab[a * 3 + 2]
    t = (vx * ux + vy * uy + vz * uz) / u2
    if t < EDGE_T or t > 1 - EDGE_T:
        return np.inf
    px = vx - t * ux
    py = vy - t * uy
    pz = vz - t * uz
    p2 = (px * px + py * py + pz * pz) / u2
    return p2 if p2 <= EDGE_PERP * EDGE_PERP else np.inf


@jit
def _part(s, cols, rows, label, seen, queue):
    """8-connected piece of one color from cell s into queue; returns its length."""
    L = label[s]
    qh = 0
    qt = 0
    seen[s] = 1
    queue[qt] = s
    qt += 1
    while qh < qt:
        c = queue[qh]
        qh += 1
        x = c % cols
        y = (c - x) // cols
        for k in range(8):
            nx = x + N8X[k]
            ny = y + N8Y[k]
            if nx < 0 or ny < 0 or nx >= cols or ny >= rows:
                continue
            n = ny * cols + nx
            if not seen[n] and label[n] == L:
                seen[n] = 1
                queue[qt] = n
                qt += 1
    return qt


@jit
def absorb_edges(cols, rows, label, K, lab):
    """Поглощение переходов: тонкий кусок, чей цвет лежит между цветами двух соседних областей, делится между ними.

    Сглаживание на границе двух цветов даёт вдоль контура нить промежуточного цвета в 1–2 клетки; каждый её обрывок был бы
    отдельным штрихом, а край штриха сайт сглаживает сам. Меняет label на месте.
    """
    total = cols * rows
    edge = np.zeros(total, dtype=np.uint8)
    take = np.full(total, -1, dtype=np.int64)
    for i in range(total):
        for k in range(4):
            n = _nb4(i, k, cols, total)
            if n >= 0 and label[n] != label[i]:
                edge[i] = 1
                break
    cnt = np.zeros(K, dtype=np.int64)
    q2 = np.zeros(total, dtype=np.int64)
    near = np.zeros(K, dtype=np.int64)
    seen = np.zeros(total, dtype=np.uint8)
    part = np.zeros(total, dtype=np.int64)
    for s in range(total):
        if seen[s]:
            continue
        c = label[s]
        qt = _part(s, cols, rows, label, seen, part)
        thin = 0
        for q in range(qt):
            thin += edge[part[q]]
        if thin < qt * EDGE_THIN:
            continue
        # neighbour colors of the piece and the best pair its color lies between
        nn = 0
        for q in range(qt):
            for k in range(4):
                n = _nb4(part[q], k, cols, total)
                if n >= 0 and label[n] != c:
                    l = label[n]
                    if cnt[l] == 0:
                        near[nn] = l
                        nn += 1
                    cnt[l] += 1
        a = -1
        b = -1
        best = np.inf
        for p in range(nn):
            for r in range(p + 1, nn):
                d = _between(c, near[p], near[r], lab)
                if d < best:
                    best = d
                    a = near[p]
                    b = near[r]
        for p in range(nn):
            cnt[near[p]] = 0
        if a < 0:
            continue
        # cells at the edge with a or b take that color; the rest from neighbours that already took one (nearest side)
        for q in range(qt):
            take[part[q]] = -2
        qh = 0
        qe = 0
        for q in range(qt):
            i = part[q]
            for k in range(4):
                n = _nb4(i, k, cols, total)
                if n >= 0 and take[n] == -1 and (label[n] == a or label[n] == b):
                    take[i] = label[n]
                    q2[qe] = i
                    qe += 1
                    break
        while qh < qe:
            i = q2[qh]
            qh += 1
            for k in range(4):
                n = _nb4(i, k, cols, total)
                if n >= 0 and take[n] == -2:
                    take[n] = take[i]
                    q2[qe] = n
                    qe += 1
        for q in range(qt):
            i = part[q]
            if take[i] >= 0:
                label[i] = take[i]
            take[i] = -1


@jit
def potts(cols, rows, label, lab, pal, lam, iters=6):
    """Связная палитра (модель Поттса, ICM): клетка берёт цвет соседа, если он почти так же близок к оригиналу.

    Цена = квадрат расстояния в OKLab до цвета палитры + lam за каждого несовпадающего соседа.
    """
    if lam <= 0:
        return
    cand = np.zeros(5, dtype=np.int64)
    for _ in range(iters):
        changed = 0
        for y in range(rows):
            for x in range(cols):
                i = y * cols + x
                own = label[i]
                nc = 1
                cand[0] = own
                for k in range(4):
                    nx = x + PX[k]
                    ny = y + PY[k]
                    if nx < 0 or ny < 0 or nx >= cols or ny >= rows:
                        continue
                    l = label[ny * cols + nx]
                    j = 0
                    while j < nc and cand[j] != l:
                        j += 1
                    if j == nc:
                        cand[nc] = l
                        nc += 1
                if nc == 1:
                    continue
                L = lab[i * 3]
                A = lab[i * 3 + 1]
                B = lab[i * 3 + 2]
                best = own
                bc = np.inf
                for j in range(nc):
                    c = cand[j]
                    d0 = L - pal[c * 3]
                    d1 = A - pal[c * 3 + 1]
                    d2 = B - pal[c * 3 + 2]
                    cost = d0 * d0 + d1 * d1 + d2 * d2
                    for k in range(8):
                        nx = x + PX[k]
                        ny = y + PY[k]
                        if nx >= 0 and ny >= 0 and nx < cols and ny < rows and label[ny * cols + nx] != c:
                            cost += lam * PW[k]
                    if cost < bc:
                        bc = cost
                        best = c
                if best != own:
                    label[i] = best
                    changed += 1
        if not changed:
            break


@jit
def _delta(a, b, lab):
    d0 = lab[a * 3] - lab[b * 3]
    d1 = lab[a * 3 + 1] - lab[b * 3 + 1]
    d2 = lab[a * 3 + 2] - lab[b * 3 + 2]
    return math.sqrt(d0 * d0 + d1 * d1 + d2 * d2)


@jit
def merge_small(cols, rows, label, K, min_area, lab, has_lab):
    """Мелкие пятна перекрашиваются в цвет соседа.

    Без палитры пятна меньше min_area клеток уходят в соседа с самой длинной общей границей. С палитрой (lab — OKLab,
    3 числа на цвет) решает заметность = площадь × контраст с самым похожим соседом: контрастная точка остаётся,
    а пятно почти того же цвета уходит.
    """
    if min_area <= 1:
        return
    total = cols * rows
    nb = np.zeros(K, dtype=np.int64)
    touched = np.zeros(K, dtype=np.int64)
    limit = min_area * MERGE_BOOST if has_lab else min_area
    queue = np.zeros(total, dtype=np.int64)
    nbs = np.zeros(4, dtype=np.int64)
    for _ in range(2):
        changed = False
        seen = np.zeros(total, dtype=np.uint8)
        for s in range(total):
            if seen[s]:
                continue
            L = label[s]
            qt = _part(s, cols, rows, label, seen, queue)
            if qt >= limit:
                continue
            nt = 0
            for q in range(qt):
                c = queue[q]
                x = c % cols
                nbs[0] = c - 1 if x > 0 else -1
                nbs[1] = c + 1 if x < cols - 1 else -1
                nbs[2] = c - cols
                nbs[3] = c + cols
                for t in range(4):
                    n = nbs[t]
                    if n < 0 or n >= total or label[n] == L:
                        continue
                    l = label[n]
                    if nb[l] == 0:
                        touched[nt] = l
                        nt += 1
                    nb[l] += 1
            best = -1
            bd = np.inf
            for t in range(nt):
                l = touched[t]
                if not has_lab:
                    if best < 0 or nb[l] > nb[best]:
                        best = l
                    continue
                d = _delta(L, l, lab)
                if d < bd - 1e-9 or (d < bd + 1e-9 and best >= 0 and nb[l] > nb[best]):
                    bd = d
                    best = l
            for t in range(nt):
                nb[touched[t]] = 0
            if best < 0:
                continue
            if has_lab and qt * min(MERGE_BOOST, max(1 / MERGE_BOOST, bd / MERGE_DREF)) >= min_area:
                continue
            for q in range(qt):
                label[queue[q]] = best
            changed = True
        if not changed:
            break


@jit
def count_parts(cols, rows, label, K):
    """Сколько отдельных 8-связных кусков у каждого цвета."""
    total = cols * rows
    parts = np.zeros(K, dtype=np.int64)
    seen = np.zeros(total, dtype=np.uint8)
    queue = np.zeros(total, dtype=np.int64)
    for s in range(total):
        if seen[s]:
            continue
        _part(s, cols, rows, label, seen, queue)
        parts[label[s]] += 1
    return parts
