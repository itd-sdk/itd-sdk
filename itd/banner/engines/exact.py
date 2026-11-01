"""Engine "exact" (the first version of the program): brush one cell wide, no cleaning.

Colors from rare to frequent; a piece of a color together with cells of later colors is walked by one line, so a small
color connects through the large ones that will cover it later.
"""

import numpy as np

from itd.banner.engines import to_arrays
from itd.banner.jit import jit


@jit
def _later(c, d, L, cols, total, rk):
    x = c % cols
    if (d == 1 and x == cols - 1) or (d == -1 and x == 0):
        return -1
    n = c + d
    return n if n >= 0 and n < total and rk[n] >= L else -1


@jit
def _tip_ext(t, d, L, cols, total, rk):
    # neighbour to extend tip t into: straight ahead along d first, then sideways
    n = _later(t, d, L, cols, total, rk)
    if abs(d) == 1:
        if n < 0:
            n = _later(t, cols, L, cols, total, rk)
        if n < 0:
            n = _later(t, -cols, L, cols, total, rk)
    else:
        if n < 0:
            n = _later(t, 1, L, cols, total, rk)
        if n < 0:
            n = _later(t, -1, L, cols, total, rk)
    return n


@jit
def _tips_out(tour, nt, L, cols, total, rk, res):
    """Tips (start, end, turn at a leaf, single cell) extended into a neighbour of a later color; returns the length of res."""
    if nt == 1:
        # single cell: through between two neighbours, otherwise a corner, otherwise at least to one side
        s = tour[0]
        u = _later(s, 1, L, cols, total, rk)
        v = _later(s, -1, L, cols, total, rk)
        if u >= 0 and v >= 0:
            res[0] = u
            res[1] = s
            res[2] = v
            return 3
        u = _later(s, cols, L, cols, total, rk)
        v = _later(s, -cols, L, cols, total, rk)
        if u >= 0 and v >= 0:
            res[0] = u
            res[1] = s
            res[2] = v
            return 3
        ns = np.empty(4, dtype=np.int64)
        k = 0
        for d in (1, -1, cols, -cols):
            n = _later(s, d, L, cols, total, rk)
            if n >= 0:
                ns[k] = n
                k += 1
        if k >= 2:
            res[0] = ns[0]
            res[1] = s
            res[2] = ns[1]
            return 3
        if k:
            res[0] = ns[0]
            res[1] = s
            return 2
        res[0] = s
        return 1
    m = 0
    head = _tip_ext(tour[0], tour[0] - tour[1], L, cols, total, rk)
    tail = _tip_ext(tour[nt - 1], tour[nt - 1] - tour[nt - 2], L, cols, total, rk)
    if head >= 0:
        res[m] = head
        m += 1
    for i in range(nt):
        res[m] = tour[i]
        m += 1
        if i > 0 and i < nt - 1 and tour[i - 1] == tour[i + 1]:
            u = _tip_ext(tour[i], tour[i] - tour[i - 1], L, cols, total, rk)
            if u >= 0:
                res[m] = u
                res[m + 1] = tour[i]
                m += 2
    if tail >= 0:
        res[m] = tail
        m += 1
    return m


@jit
def exact(cols, rows, label, K, white, cell, abort_ops, abort_points):
    """Returns (ok, color index per op, starts, points); ok is False when the limits were exceeded (abort_* > 0)."""
    total = cols * rows
    area = np.zeros(K, dtype=np.int64)
    for i in range(total):
        if label[i] != white:
            area[label[i]] += 1
    cand = np.empty(K, dtype=np.int64)
    nc = 0
    for p in range(K):
        if area[p] > 0:
            cand[nc] = p
            nc += 1
    cand = cand[:nc]
    order = cand[np.argsort(area[cand], kind='mergesort')]
    rank_of = np.full(K, -1, dtype=np.int64)
    for r in range(order.shape[0]):
        rank_of[order[r]] = r
    rk = np.full(total, -1, dtype=np.int64)
    for i in range(total):
        if label[i] != white:
            rk[i] = rank_of[label[i]]

    vis = np.zeros(total, dtype=np.int64)
    parent = np.zeros(total, dtype=np.int64)
    queue = np.zeros(total, dtype=np.int64)
    keep = np.zeros(total, dtype=np.uint8)
    head = np.zeros(total, dtype=np.int64)
    next_s = np.zeros(total, dtype=np.int64)
    stack = np.zeros(total, dtype=np.int64)
    tour = np.zeros(2 * total + 1, dtype=np.int64)
    path = np.zeros(4 * total + 4, dtype=np.int64)

    op_color = [0]
    op_start = [0]
    out_pts = [(0.0, 0.0)]
    op_color.clear()
    op_start.clear()
    out_pts.clear()
    points = 0

    for L in range(order.shape[0]):
        mark = L + 1
        for s in range(total):
            if rk[s] != L or vis[s] == mark:
                continue
            # 1) piece of cells "color L or later", BFS gives the shortest paths
            qt = 0
            qh = 0
            vis[s] = mark
            parent[s] = -1
            head[s] = -1
            queue[qt] = s
            qt += 1
            while qh < qt:
                c = queue[qh]
                qh += 1
                x = c % cols
                for nb in (c - 1 if x > 0 else -1, c + 1 if x < cols - 1 else -1, c - cols if c >= cols else -1, c + cols if c + cols < total else -1):
                    if nb >= 0 and rk[nb] >= L and vis[nb] != mark:
                        vis[nb] = mark
                        parent[nb] = c
                        head[nb] = -1
                        queue[qt] = nb
                        qt += 1
            # 2) keep only the branches leading to cells of color L
            for i in range(qt - 1, -1, -1):
                c = queue[i]
                if rk[c] == L:
                    keep[c] = 1
                if keep[c] and parent[c] >= 0:
                    keep[parent[c]] = 1
            for i in range(1, qt):
                c = queue[i]
                if keep[c]:
                    p = parent[c]
                    next_s[c] = head[p]
                    head[p] = c
            # 3) walk the tree by one line, cut the return tail
            sp = 1
            stack[0] = s
            nt = 1
            tour[0] = s
            last_new = 0
            while sp:
                c = stack[sp - 1]
                ch = head[c]
                if ch != -1:
                    head[c] = next_s[ch]
                    stack[sp] = ch
                    sp += 1
                    tour[nt] = ch
                    nt += 1
                    last_new = nt - 1
                else:
                    sp -= 1
                    if sp:
                        tour[nt] = stack[sp - 1]
                        nt += 1
            nt = last_new + 1
            for i in range(qt):
                keep[queue[i]] = 0
            # 4) tips extended into a neighbour of a later color
            npath = _tips_out(tour, nt, L, cols, total, rk, path)
            # 5) drop points on straight runs
            op_start.append(len(out_pts))
            for i in range(npath):
                if i > 0 and i < npath - 1 and path[i] - path[i - 1] == path[i + 1] - path[i]:
                    continue
                c = path[i]
                out_pts.append((((c % cols) + 0.5) * cell, ((c // cols) + 0.5) * cell))
            op_color.append(order[L])
            points += len(out_pts) - op_start[-1]
            if (abort_ops and len(op_color) > abort_ops) or (abort_points and points > abort_points):
                op_start.append(len(out_pts))
                colors, starts, pts = to_arrays(op_color, op_start, out_pts)
                return False, colors, starts, pts
    op_start.append(len(out_pts))
    colors, starts, pts = to_arrays(op_color, op_start, out_pts)
    return True, colors, starts, pts
