"""Engine "layers": colors in layers from the largest to the small ones.

A layer may cover cells of colors that are drawn later (they will be painted over). Already drawn ones may be touched only
as much as it is invisible: deep on an almost equal color, almost not at all on a contrasting one (contrast tolerance).
Inside a layer wide bands go first, then narrower ones; bands are stitched into polylines with detours.
"""

import math

import numpy as np

from itd.banner.engines import to_arrays, widths_array
from itd.banner.jit import jit
from itd.banner.limits import MAX_WIDTH
from itd.banner.segment import count_parts

INF = 1e20
LEVEL_STEP = 0.35  # the next brush is about three times narrower than the previous one
WIDE_MIN_GAIN = 3  # a wide band pays off if it covers at least 3 of its widths of cells
ROUTE_VISIT_PER_POINT = 4000
# contrast tolerance: a stroke may put on a foreign already drawn pixel (or leave its own unpainted) so much paint that the
# error there stays below TOL_EPS*tol in OKLab; on an almost equal color it may go TOL_DEPTH*tol cells deep
TOL_EPS = 0.05
TOL_DEPTH = 0.5
# steps of going onto a neighbour, in cells: each has its own distance map, so there are few of them
TIER_A = np.array([0.0, 0.25, 0.5])

NX = np.array([0, 1, -1, 0, 0], dtype=np.int64)
NY = np.array([0, 0, 0, 1, -1], dtype=np.int64)

# mutable integer state shared by the helpers
S_LEFT, S_STAMP, S_COVAT, S_CUR, S_NCLAIMED = range(5)
# frame of the current color (B*), window around it where the distance map is exact (W*), reach around the frame
B_X0, B_X1, B_Y0, B_Y1, W_X0, W_X1, W_Y0, W_Y1, B_REACH = range(9)


@jit
def _delta(lab, a, b):
    """Contrast of two palette colors in OKLab; -1 is the white canvas."""
    K = lab.shape[0] // 3 - 1
    i = (K if a < 0 else a) * 3
    j = (K if b < 0 else b) * 3
    dl = lab[i] - lab[j]
    da = lab[i + 1] - lab[j + 1]
    db = lab[i + 2] - lab[j + 2]
    return math.sqrt(dl * dl + da * da + db * db)


@jit
def _edt(cols, bw, t, tier, gy, gr, env, v, z, tD, tSite):
    # exact euclidean distance to the cells of tier t (Felzenszwalb) and the nearest one, only inside the window
    wx0, wx1, wy0, wy1 = bw[W_X0], bw[W_X1], bw[W_Y0], bw[W_Y1]
    for x in range(wx0, wx1 + 1):
        last = -1
        for y in range(wy0, wy1 + 1):
            i = y * cols + x
            if tier[i] == t:
                last = y
            gy[i] = INF if last < 0 else y - last
            gr[i] = last
        last = -1
        for y in range(wy1, wy0 - 1, -1):
            i = y * cols + x
            if tier[i] == t:
                last = y
            if last >= 0 and last - y < gy[i]:
                gy[i] = last - y
                gr[i] = last
    for y in range(wy0, wy1 + 1):
        o = y * cols
        k = -1
        for q in range(wx0, wx1 + 1):
            g = gy[o + q]
            if g >= INF:
                continue
            fq = g * g + q * q
            s = 0.0
            while k >= 0:
                s = (fq - env[k]) / (2 * (q - v[k]))
                if s <= z[k]:
                    k -= 1
                else:
                    break
            k += 1
            v[k] = q
            env[k] = fq
            z[k] = s if k else -np.inf
        if k < 0:
            for x in range(wx0, wx1 + 1):
                tD[o + x] = np.inf
                tSite[o + x] = -1
            continue
        j = 0
        for x in range(wx0, wx1 + 1):
            while j < k and z[j + 1] < x:
                j += 1
            p = v[j]
            g = gy[o + p]
            tD[o + x] = math.sqrt((x - p) * (x - p) + g * g)
            tSite[o + x] = gr[o + p] * cols + p


@jit
def _distance_field(cols, bw, tiers, ntiers, tier, D, site, sb, gy, gr, env, v, z, tD, tSite):
    # distance map with tolerance: minimum over tiers (distance to a cell of the tier + how deep it may be entered)
    wx0, wx1, wy0, wy1 = bw[W_X0], bw[W_X1], bw[W_Y0], bw[W_Y1]
    for y in range(wy0, wy1 + 1):
        for x in range(wx0, wx1 + 1):
            i = y * cols + x
            D[i] = np.inf
            site[i] = -1
            sb[i] = 0.0
    for ti in range(ntiers):
        t = tiers[ti]
        _edt(cols, bw, t, tier, gy, gr, env, v, z, tD, tSite)
        a = TIER_A[t - 1]
        for y in range(wy0, wy1 + 1):
            for x in range(wx0, wx1 + 1):
                i = y * cols + x
                e = tD[i] + a
                if e < D[i]:
                    D[i] = e
                    site[i] = tSite[i]
                    sb[i] = a
    max_d = 0.0
    reach = bw[B_REACH]
    x0 = max(wx0, bw[B_X0] - reach)
    x1 = min(wx1, bw[B_X1] + reach)
    for y in range(max(wy0, bw[B_Y0] - reach), min(wy1, bw[B_Y1] + reach) + 1):
        for i in range(y * cols + x0, y * cols + x1 + 1):
            if D[i] > max_d:
                max_d = D[i]
    return max_d


@jit
def _forb2(cols, rows, site, sb, px, py):
    # distance from a point to the nearest forbidden cell with its tolerance (by the nearest cells of neighbouring centers)
    cx = round(px)
    cy = round(py)
    best = np.inf
    for k in range(5):
        nx = cx + NX[k]
        ny = cy + NY[k]
        if nx < 0 or ny < 0 or nx >= cols or ny >= rows:
            continue
        n = ny * cols + nx
        s = site[n]
        if s < 0:
            continue
        sx = s % cols
        dx = px - sx
        dy = py - (s - sx) // cols
        best = min(best, math.sqrt(dx * dx + dy * dy) + sb[n])
    return best


@jit
def _safe_seg(cols, rows, D, site, sb, ax, ay, bx, by, rr):
    # the segment between cell centers does not come closer than rr to forbidden cells (with their tolerance)
    if rr <= 0:
        return True
    ln = math.hypot(bx - ax, by - ay)
    if (D[ay * cols + ax] + D[by * cols + bx] - ln) / 2 >= rr:
        return True
    n = math.ceil(ln * 2)
    lim = rr - 1e-6
    for i in range(n + 1):
        t = i / n if n else 0.0
        if _forb2(cols, rows, site, sb, ax + (bx - ax) * t, ay + (by - ay) * t) < lim:
            return False
    return True


@jit
def _seg_d2(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    l2 = dx * dx + dy * dy
    t = ((px - ax) * dx + (py - ay) * dy) / l2 if l2 else 0.0
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    ex = ax + t * dx - px
    ey = ay + t * dy - py
    return ex * ex + ey * ey


@jit
def _claim_seg(cols, rows, T, st, claimed, under, under0, ax, ay, bx, by, cov, apply):
    # target cells whose center is not farther than cov from the segment: counted, and with apply taken off the target
    c2 = cov * cov + 1e-6
    e = math.ceil(cov)
    x0 = max(0, min(ax, bx) - e)
    x1 = min(cols - 1, max(ax, bx) + e)
    y0 = max(0, min(ay, by) - e)
    y1 = min(rows - 1, max(ay, by) + e)
    n = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            i = y * cols + x
            if not T[i] or _seg_d2(x, y, ax, ay, bx, by) > c2:
                continue
            n += 1
            if apply:
                T[i] = 0
                st[S_LEFT] -= 1
                claimed[st[S_NCLAIMED]] = i
                st[S_NCLAIMED] += 1
                under0[i] = under[i]
    return n


@jit
def _paint_seg(cols, rows, cell, T, touched, under, cov, cov_stamp, st, d_white, eps, ax, ay, bx, by, m):
    # final segment of brush level m: takes covered cells off the target, accumulates coverage, marks touched white
    # (the white layer will repaint it) if the paint on it is noticeable, and remembers whose stroke is on top
    R = m + 1 + 0.71 * (1 - 1 / cell)
    e = math.ceil(R)
    c2 = m * m + 1e-6
    x0 = max(0, min(ax, bx) - e)
    x1 = min(cols - 1, max(ax, bx) + e)
    y0 = max(0, min(ay, by) - e)
    y1 = min(rows - 1, max(ay, by) + e)
    cov_at = st[S_COVAT]
    cur = st[S_CUR]
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d2 = _seg_d2(x, y, ax, ay, bx, by)
            if d2 >= R * R:
                continue
            i = y * cols + x
            c = min(1.0, max(0.0, (m + 0.5 - math.sqrt(d2)) * cell + 0.5))
            if T[i] and d2 <= c2:
                T[i] = 0
                st[S_LEFT] -= 1
            if cov_stamp[i] != cov_at:
                cov_stamp[i] = cov_at
                cov[i] = c
            elif c > cov[i]:
                cov[i] = c
            if c >= 0.5:
                under[i] = cur
            if c * d_white > eps:
                touched[i] = 1


@jit
def _restore_uncovered(lab, T, st, claimed, cov, cov_stamp, under0, eps):
    # level cells left partly uncovered after straightening go back to the target if the gap is noticeable
    cov_at = st[S_COVAT]
    for q in range(st[S_NCLAIMED]):
        i = claimed[q]
        c = cov[i] if cov_stamp[i] == cov_at else 0.0
        if c < 0.999 and (1 - c) * _delta(lab, st[S_CUR], under0[i]) > eps:
            T[i] = 1
            st[S_LEFT] += 1
    st[S_NCLAIMED] = 0


@jit
def _heap_push(hg, ho, hl, ha, hb, size, g, o, l, a, b):
    hg[size] = g
    ho[size] = o
    hl[size] = l
    ha[size] = a
    hb[size] = b
    i = size
    while i:
        p = (i - 1) >> 1
        if hg[p] >= hg[i]:
            break
        hg[p], hg[i] = hg[i], hg[p]
        ho[p], ho[i] = ho[i], ho[p]
        hl[p], hl[i] = hl[i], hl[p]
        ha[p], ha[i] = ha[i], ha[p]
        hb[p], hb[i] = hb[i], hb[p]
        i = p
    return size + 1


@jit
def _heap_pop(hg, ho, hl, ha, hb, size):
    top = (hg[0], ho[0], hl[0], ha[0], hb[0])
    size -= 1
    if size:
        hg[0] = hg[size]
        ho[0] = ho[size]
        hl[0] = hl[size]
        ha[0] = ha[size]
        hb[0] = hb[size]
        i = 0
        while True:
            l = 2 * i + 1
            r = l + 1
            b = i
            if l < size and hg[l] > hg[b]:
                b = l
            if r < size and hg[r] > hg[b]:
                b = r
            if b == i:
                break
            hg[b], hg[i] = hg[i], hg[b]
            ho[b], ho[i] = ho[i], ho[b]
            hl[b], hl[i] = hl[i], hl[b]
            ha[b], ha[i] = ha[i], ha[b]
            hb[b], hb[i] = hb[i], hb[b]
            i = b
    return top, size


@jit
def _has(cols, rows, T, m, o, l, a):
    hi = min((cols if o else rows) - 1, l + m)
    for k in range(max(0, l - m), hi + 1):
        if T[a * cols + k if o else k * cols + a]:
            return True
    return False


@jit
def _level_segments(cols, rows, bw, D, T, P, Q, st, claimed, under, under0, hg, ho, hl, ha, hb, m):
    # level m: brush 2m+1 cells wide. Candidates are straight horizontal and vertical runs of cells where the brush does
    # not touch forbidden cells; greedily take the one that covers most of the target
    B = 2 * m + 1
    thr = m + 1
    step = max(1, B >> 2)
    min_gain = WIDE_MIN_GAIN * B if m else 1
    # everything that can touch cells of the color lies in the color frame +- m
    x0 = max(0, bw[B_X0] - m)
    x1 = min(cols - 1, bw[B_X1] + m)
    y0 = max(0, bw[B_Y0] - m)
    y1 = min(rows - 1, bw[B_Y1] + m)
    for x in range(x0, x1 + 1):
        P[x * (rows + 1) + y0] = 0
    for y in range(y0, y1 + 1):
        Q[y * (cols + 1) + x0] = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            t = T[y * cols + x]
            P[x * (rows + 1) + y + 1] = P[x * (rows + 1) + y] + t
            Q[y * (cols + 1) + x + 1] = Q[y * (cols + 1) + x] + t
    size = 0
    line_buf = np.empty(max(x1 - x0, y1 - y0) + 2, dtype=np.int64)
    for o in range(2):
        lines = cols if o else rows
        line_step = 1 if o else cols
        stride = cols if o else 1
        l0 = x0 if o else y0
        l1 = x1 if o else y1
        a0w = y0 if o else x0
        a1w = y1 if o else x1
        # lines l0, l0 + step, ... and always l1 (counted up front: a variable-step loop makes LLVM emit 128-bit division)
        nlines = (l1 - l0) // step + 1
        for li in range(nlines):
            line_buf[li] = l0 + li * step
        if line_buf[nlines - 1] != l1:
            line_buf[nlines] = l1
            nlines += 1
        for li in range(nlines):
            l = line_buf[li]
            lo = max(l0, l - m)
            hi = min(l1 + 1, l + m + 1)
            a = a0w
            while a <= a1w:
                if D[l * line_step + a * stride] < thr:
                    a += 1
                    continue
                a0 = a
                g = 0
                while a <= a1w and D[l * line_step + a * stride] >= thr:
                    if o:
                        g += Q[a * (lines + 1) + hi] - Q[a * (lines + 1) + lo]
                    else:
                        g += P[a * (lines + 1) + hi] - P[a * (lines + 1) + lo]
                    a += 1
                if g >= min_gain:
                    size = _heap_push(hg, ho, hl, ha, hb, size, g, o, l, a0, a - 1)
    segs = [(0, 0, 0, 0)]
    segs.clear()
    while size:
        top, size = _heap_pop(hg, ho, hl, ha, hb, size)
        o = top[1]
        l = top[2]
        s = top[3]
        e = top[4]
        while s <= e and not _has(cols, rows, T, m, o, l, s):
            s += 1
        if s > e:
            continue
        while not _has(cols, rows, T, m, o, l, e):
            e -= 1
        if o:
            ax, ay, bx, by = l, s, l, e
        else:
            ax, ay, bx, by = s, l, e, l
        g = _claim_seg(cols, rows, T, st, claimed, under, under0, ax, ay, bx, by, m, False)
        if g < min_gain:
            continue
        if size and g < hg[0]:
            size = _heap_push(hg, ho, hl, ha, hb, size, g, o, l, s, e)
            continue
        _claim_seg(cols, rows, T, st, claimed, under, under0, ax, ay, bx, by, m, True)
        segs.append((ax, ay, bx, by))
    return segs


@jit
def _ends_first(e_head, e_id, e_next, cell, used):
    k = e_head[cell]
    while k >= 0:
        if not used[e_id[k]]:
            return e_id[k]
        k = e_next[k]
    return -1


@jit
def _route(cols, rows, bw, D, site, sb, mark, parent, queue, st, route_visit, route_points, e_head, e_id, e_next, used, sx, sy, rr):
    # path over safe cells to the nearest end of a free segment, straightened to at most route_points points
    st[S_STAMP] += 1
    stamp = st[S_STAMP]
    start = sy * cols + sx
    reach = bw[B_REACH]
    rx0 = max(0, bw[B_X0] - reach)
    rx1 = min(cols - 1, bw[B_X1] + reach)
    ry0 = max(0, bw[B_Y0] - reach)
    ry1 = min(rows - 1, bw[B_Y1] + reach)
    via = [(0, 0)]
    via.clear()
    qh = 0
    qt = 0
    hit = -1
    mark[start] = stamp
    parent[start] = -1
    queue[qt] = start
    qt += 1
    while qh < qt and qt < route_visit:
        c = queue[qh]
        qh += 1
        if c != start and e_head[c] >= 0 and _ends_first(e_head, e_id, e_next, c, used) >= 0:
            hit = c
            break
        x = c % cols
        y = (c - x) // cols
        if x > rx0:
            n = c - 1
            if mark[n] != stamp and D[n] >= rr:
                mark[n] = stamp
                parent[n] = c
                queue[qt] = n
                qt += 1
        if x < rx1:
            n = c + 1
            if mark[n] != stamp and D[n] >= rr:
                mark[n] = stamp
                parent[n] = c
                queue[qt] = n
                qt += 1
        if y > ry0:
            n = c - cols
            if mark[n] != stamp and D[n] >= rr:
                mark[n] = stamp
                parent[n] = c
                queue[qt] = n
                qt += 1
        if y < ry1:
            n = c + cols
            if mark[n] != stamp and D[n] >= rr:
                mark[n] = stamp
                parent[n] = c
                queue[qt] = n
                qt += 1
    if hit < 0:
        return -1, via
    cells = [(0, 0)]
    cells.clear()
    c = hit
    while c >= 0:
        cells.append((c % cols, (c - c % cols) // cols))
        c = parent[c]
    cells.reverse()
    nc = len(cells)
    i = 0
    while i < nc - 1:
        j = i + 1
        for k in range(i + 2, nc):
            if _safe_seg(cols, rows, D, site, sb, cells[i][0], cells[i][1], cells[k][0], cells[k][1], rr):
                j = k
        if j < nc - 1:
            via.append(cells[j])
        if len(via) > route_points:
            return -1, via
        i = j
    return hit, via


@jit
def _chain_segments(cols, rows, bw, D, site, sb, mark, parent, queue, st, route_visit, route_points, e_head, segs, rr, B):
    # segments of one level stitched into polylines: the nearest segment is attached to the end of the chain if it can be
    # reached straight or by a detour; one polyline = one stroke
    ns = len(segs)
    bs = max(8, 2 * B)
    gx = -(-cols // bs) + 1
    # ends of segments per cell: linked lists on arrays, the BFS of a detour asks every cell
    e_id = np.empty(2 * ns, dtype=np.int64)
    e_next = np.empty(2 * ns, dtype=np.int64)
    e_cells = np.empty(2 * ns, dtype=np.int64)
    ne = 0
    nec = 0
    for sid in range(ns):
        s = segs[sid]
        for cell in (s[1] * cols + s[0], s[3] * cols + s[2]):
            if e_head[cell] < 0:
                e_cells[nec] = cell
                nec += 1
            e_id[ne] = sid
            e_next[ne] = e_head[cell]
            e_head[cell] = ne
            ne += 1
    # bucket grid of segment ends, ids in insertion order
    nkeys = ((rows - 1) // bs + 1) * gx
    gcount = np.zeros(nkeys + 1, dtype=np.int64)
    for sid in range(ns):
        s = segs[sid]
        gcount[(s[1] // bs) * gx + s[0] // bs + 1] += 1
        gcount[(s[3] // bs) * gx + s[2] // bs + 1] += 1
    for k in range(nkeys):
        gcount[k + 1] += gcount[k]
    gfill = gcount[:nkeys].copy()
    gitems = np.empty(2 * ns, dtype=np.int64)
    for sid in range(ns):
        s = segs[sid]
        k = (s[1] // bs) * gx + s[0] // bs
        gitems[gfill[k]] = sid
        gfill[k] += 1
        k = (s[3] // bs) * gx + s[2] // bs
        gitems[gfill[k]] = sid
        gfill[k] += 1
    used = np.zeros(ns, dtype=np.uint8)
    keys_x = np.empty(ns, dtype=np.int64)
    keys_y = np.empty(ns, dtype=np.int64)
    for sid in range(ns):
        keys_x[sid] = segs[sid][0]
        keys_y[sid] = segs[sid][1]
    order = np.argsort(keys_x, kind='mergesort')
    order = order[np.argsort(keys_y[order], kind='mergesort')]
    cd = np.empty(2 * ns + 2, dtype=np.float64)
    cid = np.empty(2 * ns + 2, dtype=np.int64)
    crev = np.empty(2 * ns + 2, dtype=np.int64)

    paths = [[(0, 0)]]
    paths.clear()
    for start in order:
        if used[start]:
            continue
        used[start] = 1
        s = segs[start]
        path = [(s[0], s[1]), (s[2], s[3])]
        for side in range(2):
            while True:
                cx, cy = path[-1]
                bx0 = cx // bs
                by0 = cy // bs
                nc = 0
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        k = (by0 + dy) * gx + bx0 + dx
                        if k < 0 or k >= nkeys:
                            continue
                        for t in range(gcount[k], gcount[k + 1]):
                            sid = gitems[t]
                            if used[sid]:
                                continue
                            g = segs[sid]
                            d0 = (g[0] - cx) * (g[0] - cx) + (g[1] - cy) * (g[1] - cy)
                            d1 = (g[2] - cx) * (g[2] - cx) + (g[3] - cy) * (g[3] - cy)
                            cd[nc] = d0 if d0 <= d1 else d1
                            cid[nc] = sid
                            crev[nc] = 0 if d0 <= d1 else 1
                            nc += 1
                srt = np.argsort(cd[:nc], kind='mergesort')
                linked = False
                tries = 0
                for t in range(nc):
                    if tries >= 8:
                        break
                    sid = cid[srt[t]]
                    rev = crev[srt[t]]
                    if used[sid]:
                        continue
                    tries += 1
                    g = segs[sid]
                    if rev:
                        px, py, qx, qy = g[2], g[3], g[0], g[1]
                    else:
                        px, py, qx, qy = g[0], g[1], g[2], g[3]
                    if not _safe_seg(cols, rows, D, site, sb, cx, cy, px, py, rr):
                        continue
                    used[sid] = 1
                    path.append((px, py))
                    path.append((qx, qy))
                    linked = True
                    break
                if linked:
                    continue
                hit, via = _route(cols, rows, bw, D, site, sb, mark, parent, queue, st, route_visit, route_points, e_head, e_id, e_next, used, cx, cy, rr)
                if hit < 0:
                    break
                sid = _ends_first(e_head, e_id, e_next, hit, used)
                g = segs[sid]
                rev = g[0] + g[1] * cols != hit
                used[sid] = 1
                for p in via:
                    path.append(p)
                if rev:
                    path.append((g[2], g[3]))
                    path.append((g[0], g[1]))
                else:
                    path.append((g[0], g[1]))
                    path.append((g[2], g[3]))
            if side == 0:
                path.reverse()
        paths.append(path)
    for k in range(nec):
        e_head[e_cells[k]] = -1
    return paths


@jit
def _simplify(cols, rows, D, site, sb, pts, rr, delta):
    # vertices are dropped if the line to the far vertex passes no farther than delta from them and is safe
    p = [(0, 0)]
    p.clear()
    for q in pts:
        if not len(p) or p[-1][0] != q[0] or p[-1][1] != q[1]:
            p.append(q)
    if len(p) <= 2:
        return p
    out = [p[0]]
    d2 = delta * delta + 1e-9
    n = len(p)
    i = 0
    while i < n - 1:
        j = i + 1
        k = i + 2
        while k < n and k <= i + 96:
            ok = True
            t = i + 1
            while t < k and ok:
                ok = _seg_d2(p[t][0], p[t][1], p[i][0], p[i][1], p[k][0], p[k][1]) <= d2
                t += 1
            if not ok or not _safe_seg(cols, rows, D, site, sb, p[i][0], p[i][1], p[k][0], p[k][1], rr):
                break
            j = k
            k += 1
        out.append(p[j])
        i = j
    return out


@jit
def _tip_ok(cols, rows, D, site, sb, x, y, fx, fy):
    return x >= 0 and y >= 0 and x < cols and y < rows and D[y * cols + x] >= 1 and _safe_seg(cols, rows, D, site, sb, fx, fy, x, y, 1.0)


@jit
def _tip(cols, rows, D, site, sb, t, prev):
    dx = t[0] - prev[0]
    dy = t[1] - prev[1]
    ln = max(abs(dx), abs(dy))
    ex = t[0] + round(dx / ln)
    ey = t[1] + round(dy / ln)
    return (ex, ey) if _tip_ok(cols, rows, D, site, sb, ex, ey, t[0], t[1]) else (-1 << 40, 0)


@jit
def _extend_tips(cols, rows, D, site, sb, pts):
    # the tip of a thin brush does not cover its cell fully, the canvas shows through. The tip is extended by a cell where
    # the brush may go (own color or not yet drawn): the own cell ends up inside the line
    if len(pts) == 1:
        x, y = pts[0]
        for ax, ay in ((1, 0), (0, 1)):
            if _tip_ok(cols, rows, D, site, sb, x + ax, y + ay, x, y) and _tip_ok(cols, rows, D, site, sb, x - ax, y - ay, x, y):
                return [(x + ax, y + ay), (x, y), (x - ax, y - ay)]
        for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if _tip_ok(cols, rows, D, site, sb, x + ax, y + ay, x, y):
                return [(x + ax, y + ay), (x, y)]
        return [(x, y)]
    head = _tip(cols, rows, D, site, sb, pts[0], pts[1])
    tail = _tip(cols, rows, D, site, sb, pts[-1], pts[-2])
    out = [(0, 0)]
    out.clear()
    if head[0] != -1 << 40:
        out.append(head)
    for p in pts:
        out.append(p)
    if tail[0] != -1 << 40:
        out.append(tail)
    return out


@jit
def _dot_wide(cols, rows, D, lab, label, under, cur, x, y):
    # a dot that can not be extended may be drawn larger, sqrt(2) cells: it covers its cell fully and gives each of the
    # 4 neighbours ~14% of its color; larger if that error is smaller than the gap of (1 - pi/4) of a one cell dot
    i = y * cols + x
    hole = (1 - math.pi / 4) * _delta(lab, cur, under[i])
    bleed = 0.0
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx = x + dx
        ny = y + dy
        n = ny * cols + nx
        if nx >= 0 and ny >= 0 and nx < cols and ny < rows and D[n] < 1:
            bleed += 0.143 * _delta(lab, cur, label[n])
    return bleed < hole


@jit
def layers(cols, rows, label, K, lab_pal, white, cell, tol, route_points, abort_ops, abort_points):
    """Color map of the grid -> strokes in banner coordinates.

    Returns arrays (ok, palette index per op, width per op, op starts, points); ok is False when the limits were exceeded.
    """
    N = cols * rows
    # layer order: the largest color first (it may be smeared anywhere), then by area, but fragmented colors earlier:
    # while their neighbours are not drawn the pieces connect through them
    area = np.zeros(K, dtype=np.int64)
    for i in range(N):
        area[label[i]] += 1
    parts = count_parts(cols, rows, label, K)
    present_c = np.empty(K, dtype=np.int64)
    nk = 0
    for c in range(K):
        if area[c]:
            present_c[nk] = c
            nk += 1
    present_c = present_c[:nk]
    order = present_c[np.argsort(-area[present_c], kind='mergesort')]
    if nk > 1:
        rest = order[1:]
        key = np.empty(rest.shape[0])
        for t in range(rest.shape[0]):
            key[t] = area[rest[t]] * math.sqrt(parts[rest[t]])
        order[1:] = rest[np.argsort(-key, kind='mergesort')]

    lab = lab_pal  # OKLab of the palette (Float32 precision), the white canvas last
    eps = TOL_EPS * tol
    depth = TOL_DEPTH * tol

    gy = np.zeros(N)
    gr = np.zeros(N, dtype=np.int64)
    env = np.zeros(cols)
    v = np.zeros(cols, dtype=np.int64)
    z = np.zeros(cols + 1)
    D = np.zeros(N)
    site = np.zeros(N, dtype=np.int64)
    sb = np.zeros(N)
    tier = np.zeros(N, dtype=np.uint8)
    tD = np.zeros(N)
    tSite = np.zeros(N, dtype=np.int64)
    T = np.zeros(N, dtype=np.uint8)
    touched = np.zeros(N, dtype=np.uint8)
    mark = np.zeros(N, dtype=np.int64)
    parent = np.zeros(N, dtype=np.int64)
    queue = np.zeros(N, dtype=np.int64)
    P = np.zeros(cols * (rows + 1), dtype=np.int64)
    Q = np.zeros(rows * (cols + 1), dtype=np.int64)
    e_head = np.full(N, -1, dtype=np.int64)
    route_visit = min(N, max(6000, route_points * ROUTE_VISIT_PER_POINT))
    under = np.full(N, -1, dtype=np.int64)
    under0 = np.zeros(N, dtype=np.int64)
    claimed = np.zeros(N, dtype=np.int64)
    cov = np.zeros(N)
    cov_stamp = np.zeros(N, dtype=np.int64)
    hcap = N + cols + rows + 16
    hg = np.zeros(hcap, dtype=np.int64)
    ho = np.zeros(hcap, dtype=np.int64)
    hl = np.zeros(hcap, dtype=np.int64)
    ha = np.zeros(hcap, dtype=np.int64)
    hb = np.zeros(hcap, dtype=np.int64)
    st = np.zeros(5, dtype=np.int64)
    bw = np.zeros(9, dtype=np.int64)

    slack = 0.8 * tol
    levels = [0]
    levels.clear()
    m = math.floor((MAX_WIDTH / cell - 1) / 2)
    while m >= 1:
        levels.append(m)
        m = math.floor(m * LEVEL_STEP)
    levels.append(0)
    # a stroke of level m lies in the color frame +- m; the distance map is needed m+1 farther
    bw[B_REACH] = levels[0] + 1
    margin = 2 * bw[B_REACH] + 2

    forb = np.zeros(N, dtype=np.uint8)
    tier_of = np.zeros(K, dtype=np.uint8)
    tiers = np.zeros(3, dtype=np.int64)
    op_color = [0]
    op_color.clear()
    op_width = [0.0]
    op_width.clear()
    op_start = [0]
    out_pts = [(0.0, 0.0)]
    out_pts.clear()

    for c in order:
        left = 0
        bx0 = cols
        bx1 = -1
        by0 = rows
        by1 = -1
        i = 0
        for y in range(rows):
            for x in range(cols):
                t = 1 if label[i] == c and (c != white or touched[i]) else 0
                T[i] = t
                if t:
                    left += 1
                    if x < bx0:
                        bx0 = x
                    if x > bx1:
                        bx1 = x
                    if y < by0:
                        by0 = y
                    if y > by1:
                        by1 = y
                i += 1
        if left:
            st[S_LEFT] = left
            st[S_CUR] = c
            d_white = _delta(lab, c, -1)
            bw[B_X0] = bx0
            bw[B_X1] = bx1
            bw[B_Y0] = by0
            bw[B_Y1] = by1
            bw[W_X0] = max(0, bx0 - margin)
            bw[W_X1] = min(cols - 1, bx1 + margin)
            bw[W_Y0] = max(0, by0 - margin)
            bw[W_Y1] = min(rows - 1, by1 + margin)
            # tolerance tier of every drawn color: the closer it is to the current one, the deeper it may be entered
            for k in range(K):
                d = _delta(lab, c, k)
                a = min(depth, eps / d) if d > 1e-9 else depth
                t = 0
                while t + 1 < 3 and TIER_A[t + 1] <= a + 1e-9:
                    t += 1
                tier_of[k] = t + 1
            ntiers = 0
            for y in range(bw[W_Y0], bw[W_Y1] + 1):
                for x in range(bw[W_X0], bw[W_X1] + 1):
                    i = y * cols + x
                    t = tier_of[label[i]] if forb[i] else 0
                    tier[i] = t
                    if t:
                        seen = False
                        for q in range(ntiers):
                            if tiers[q] == t:
                                seen = True
                        if not seen:
                            tiers[ntiers] = t
                            ntiers += 1
            max_d = _distance_field(cols, bw, tiers, ntiers, tier, D, site, sb, gy, gr, env, v, z, tD, tSite)
            # the levels, then what the gap check returned on the last level is painted by the thin brush without straightening
            nl = len(levels)
            li = 0
            extra = 0
            while True:
                if li < nl:
                    m = levels[li]
                    li += 1
                    if not st[S_LEFT]:
                        li = nl
                        continue
                    if m and max_d < m + 1:
                        continue  # a brush this wide fits nowhere
                    sl = slack
                else:
                    if not (st[S_LEFT] > 0 and extra < 2):
                        break
                    extra += 1
                    m = 0
                    sl = 0.0
                # one level
                st[S_NCLAIMED] = 0
                segs = _level_segments(cols, rows, bw, D, T, P, Q, st, claimed, under, under0, hg, ho, hl, ha, hb, m)
                if not len(segs):
                    continue
                thr = m + 1
                st[S_COVAT] += 1
                paths = _chain_segments(cols, rows, bw, D, site, sb, mark, parent, queue, st, route_visit, route_points, e_head, segs, thr, 2 * m + 1)
                for path in paths:
                    pts = _simplify(cols, rows, D, site, sb, path, thr, sl)
                    wide = False
                    if m == 0:
                        pts = _extend_tips(cols, rows, D, site, sb, pts)
                        wide = len(pts) == 1 and _dot_wide(cols, rows, D, lab, label, under, c, pts[0][0], pts[0][1])
                    npts = len(pts)
                    for q in range(npts):
                        a = pts[q]
                        b = pts[min(q + 1, npts - 1)]
                        _paint_seg(cols, rows, cell, T, touched, under, cov, cov_stamp, st, d_white, eps, a[0], a[1], b[0], b[1], m)
                    # with a 1 px cell an odd width needs centers on .5, otherwise the cell center
                    n0 = len(out_pts)
                    for q in range(npts):
                        px = (pts[q][0] + 0.5) * cell
                        py = (pts[q][1] + 0.5) * cell
                        if len(out_pts) == n0 or out_pts[-1][0] != px or out_pts[-1][1] != py:
                            out_pts.append((px, py))
                    op_color.append(c)
                    op_width.append(round(math.sqrt(2) * cell * 100) / 100 if wide else float((2 * m + 1) * cell))
                    op_start.append(len(out_pts))
                _restore_uncovered(lab, T, st, claimed, cov, cov_stamp, under0, eps)
                if (abort_ops and len(op_color) > abort_ops) or (abort_points and len(out_pts) > abort_points):
                    colors, starts, pts = to_arrays(op_color, op_start, out_pts)
                    return False, colors, widths_array(op_width), starts, pts
        for i in range(N):
            if label[i] == c:
                forb[i] = 1
    colors, starts, pts = to_arrays(op_color, op_start, out_pts)
    return True, colors, widths_array(op_width), starts, pts
