"""Palette from color bins in OKLab; almost white pixels are the white canvas.

Bins are 5:5:5, or finer down to exact colors when there are too few of them for the requested palette (gradient, flat
graphics): otherwise a smooth transition breaks into as many bands as bins it touches.
"classic": median cut + k-means, color = mean RGB. "vivid": see _vivid_labels.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np

from itd.banner.color import code_from_oklab, from_hex, lab_of, oklab_f, rgb_code, to_hex
from itd.banner.image import Rgba
from itd.banner.jit import jit
from itd.banner.segment import potts

PaletteMode = Literal['vivid', 'classic']


@dataclass
class Quantized:
    label: np.ndarray
    palette: list[str]
    white: int
    """Индекс белого в палитре или -1."""


# there must be at least this many bins per palette color, otherwise finer bins are taken
BINS_PER_COLOR = 8

# how much a hue difference outweighs a lightness one and how much saturated pixels outweigh grey ones
VIVID_HUE = 1.4
VIVID_SAT = 3


@jit
def _vivid_code(L, A, B, C, n):
    """Group color: mean lightness and hue, chroma = mean chroma of the pixels (the mean color washes it out)."""
    a = A / n
    b = B / n
    c = math.hypot(a, b)
    k = C / n / c if c > 1e-6 else 1.0
    return code_from_oklab(L / n, a * k, b * k)


@jit
def _vivid_labels(cnt, lab0, lab1, lab2, colors):
    """Bin weight = pixels x (1 + chroma); start from the most different colors, then weighted k-means."""
    n = cnt.shape[0]
    X = np.zeros(n * 3)
    wt = np.zeros(n)
    dist = np.full(n, np.inf)
    for i in range(n):
        c = cnt[i]
        a = lab1[i] / c
        b = lab2[i] / c
        X[i * 3] = lab0[i] / c
        X[i * 3 + 1] = a * VIVID_HUE
        X[i * 3 + 2] = b * VIVID_HUE
        wt[i] = c * (1 + VIVID_SAT * math.hypot(a, b))
    C = np.zeros(colors * 3)
    K = 0
    pick = 0
    for i in range(1, n):
        if wt[i] > wt[pick]:
            pick = i
    while K < colors:
        C[K * 3] = X[pick * 3]
        C[K * 3 + 1] = X[pick * 3 + 1]
        C[K * 3 + 2] = X[pick * 3 + 2]
        K += 1
        bv = 0.0
        j = K - 1
        for i in range(n):
            d0 = X[i * 3] - C[j * 3]
            d1 = X[i * 3 + 1] - C[j * 3 + 1]
            d2 = X[i * 3 + 2] - C[j * 3 + 2]
            d = d0 * d0 + d1 * d1 + d2 * d2
            if d < dist[i]:
                dist[i] = d
            if dist[i] * wt[i] > bv:
                bv = dist[i] * wt[i]
                pick = i
        if bv <= 0:
            break
    group = np.zeros(n, dtype=np.int64)
    acc = np.zeros(K * 4)
    for it in range(10):
        acc[:] = 0.0
        moved = 0
        for i in range(n):
            best = 0
            bd = np.inf
            for j in range(K):
                d0 = X[i * 3] - C[j * 3]
                d1 = X[i * 3 + 1] - C[j * 3 + 1]
                d2 = X[i * 3 + 2] - C[j * 3 + 2]
                d = d0 * d0 + d1 * d1 + d2 * d2
                if d < bd:
                    bd = d
                    best = j
            if group[i] != best:
                group[i] = best
                moved += 1
            w = wt[i]
            acc[best * 4] += X[i * 3] * w
            acc[best * 4 + 1] += X[i * 3 + 1] * w
            acc[best * 4 + 2] += X[i * 3 + 2] * w
            acc[best * 4 + 3] += w
        for j in range(K):
            if acc[j * 4 + 3]:
                for a in range(3):
                    C[j * 3 + a] = acc[j * 4 + a] / acc[j * 4 + 3]
        if it and not moved:
            break
    return group, K


@jit
def _vivid_palette(group, K, cnt, lab0, lab1, lab2):
    acc = np.zeros(K * 5)
    for i in range(cnt.shape[0]):
        g = group[i] * 5
        acc[g] += lab0[i]
        acc[g + 1] += lab1[i]
        acc[g + 2] += lab2[i]
        acc[g + 3] += math.hypot(lab1[i], lab2[i])
        acc[g + 4] += cnt[i]
    codes = np.full(K, -1, dtype=np.int64)
    for j in range(K):
        if acc[j * 5 + 4]:
            codes[j] = _vivid_code(acc[j * 5], acc[j * 5 + 1], acc[j * 5 + 2], acc[j * 5 + 3], acc[j * 5 + 4])
    return codes


@jit
def _analyse(lst, cnt, S0, S1, S2):
    c = 0.0
    s0 = s1 = s2 = 0.0
    q0 = q1 = q2 = 0.0
    for t in range(lst.shape[0]):
        k = lst[t]
        c += cnt[k]
        s0 += S0[k]
        q0 += S0[k] * S0[k] / cnt[k]
        s1 += S1[k]
        q1 += S1[k] * S1[k] / cnt[k]
        s2 += S2[k]
        q2 += S2[k] * S2[k] / cnt[k]
    e0 = q0 - s0 * s0 / c
    e1 = q1 - s1 * s1 / c
    e2 = q2 - s2 * s2 / c
    m = max(e0, e1, e2)
    axis = 0 if e0 == m else 1 if e1 == m else 2
    return axis, (m if lst.shape[0] > 1 else -1.0)


@jit
def _cut(sorted_, cnt):
    total = 0.0
    for t in range(sorted_.shape[0]):
        total += cnt[sorted_[t]]
    acc = 0.0
    cut = 1
    for i in range(sorted_.shape[0] - 1):
        acc += cnt[sorted_[i]]
        cut = i + 1
        if acc >= total / 2:
            break
    return cut


@jit
def _mean(lst, cnt, S0, S1, S2):
    c = x = y = z = 0.0
    for t in range(lst.shape[0]):
        k = lst[t]
        c += cnt[k]
        x += S0[k]
        y += S1[k]
        z += S2[k]
    return x / c, y / c, z / c


def _median_cut(n_keys: int, cnt, S, n: int) -> np.ndarray:
    S0, S1, S2 = S
    keys = np.arange(n_keys, dtype=np.int64)
    axis, score = _analyse(keys, cnt, S0, S1, S2)
    buckets = [(keys, axis, score)]
    while len(buckets) < n:
        bi = 0
        for i in range(1, len(buckets)):
            if buckets[i][2] > buckets[bi][2]:
                bi = i
        lst, axis, score = buckets[bi]
        if score <= 0:
            break
        A = S[axis]
        sorted_ = lst[np.argsort(A[lst] / cnt[lst], kind='stable')]
        cut = _cut(sorted_, cnt)
        a, b = sorted_[:cut], sorted_[cut:]
        buckets[bi : bi + 1] = [(a, *_analyse(a, cnt, S0, S1, S2)), (b, *_analyse(b, cnt, S0, S1, S2))]
    return np.array([_mean(lst, cnt, S0, S1, S2) for lst, _, _ in buckets], dtype=np.float64)


@jit
def _kmeans(pal, cnt, lab0, lab1, lab2, bin_label):
    P = pal.shape[0]
    for it in range(6):
        acc = np.zeros((P, 4))
        for k in range(cnt.shape[0]):
            c = cnt[k]
            L = lab0[k] / c
            A = lab1[k] / c
            B = lab2[k] / c
            best = 0
            bd = np.inf
            for p in range(P):
                d0 = L - pal[p, 0]
                d1 = A - pal[p, 1]
                d2 = B - pal[p, 2]
                d = d0 * d0 + d1 * d1 + d2 * d2
                if d < bd:
                    bd = d
                    best = p
            bin_label[k] = best
            acc[best, 0] += lab0[k]
            acc[best, 1] += lab1[k]
            acc[best, 2] += lab2[k]
            acc[best, 3] += c
        for p in range(P):
            if acc[p, 3]:
                pal[p, 0] = acc[p, 0] / acc[p, 3]
                pal[p, 1] = acc[p, 1] / acc[p, 3]
                pal[p, 2] = acc[p, 2] / acc[p, 3]


@jit
def _classic_palette(P, bin_label, cnt, sr, sg, sb):
    rgb = np.zeros((P, 4))
    for k in range(cnt.shape[0]):
        a = bin_label[k]
        rgb[a, 0] += sr[k]
        rgb[a, 1] += sg[k]
        rgb[a, 2] += sb[k]
        rgb[a, 3] += cnt[k]
    codes = np.full(P, -1, dtype=np.int64)
    for p in range(P):
        if rgb[p, 3]:
            codes[p] = rgb_code(rgb[p, 0] / rgb[p, 3], rgb[p, 1] / rgb[p, 3], rgb[p, 2] / rgb[p, 3])
    return codes


@jit
def _bin_lab(cnt, sr, sg, sb, lab0, lab1, lab2):
    for k in range(cnt.shape[0]):
        c = cnt[k]
        L, A, B = oklab_f(sr[k] / c, sg[k] / c, sb[k] / c)
        lab0[k] = L * c
        lab1[k] = A * c
        lab2[k] = B * c


def _histogram(px: np.ndarray, white_min: float, bits: int):
    """Bins of `bits` bits per channel, numbered in order of first appearance; the white canvas (-1) is not a bin."""
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    white = (r > white_min) & (g > white_min) & (b > white_min)
    sh = 8 - bits
    key = ((r >> sh) << (2 * bits)) | ((g >> sh) << bits) | (b >> sh)
    idx = np.flatnonzero(~white)
    uniq, first, inv = np.unique(key[idx], return_index=True, return_inverse=True)
    order = np.argsort(first, kind='stable')
    rank = np.empty_like(order)
    rank[order] = np.arange(order.shape[0])
    bins = np.full(px.shape[0], -1, dtype=np.int64)
    bins[idx] = rank[inv.reshape(-1)]
    n = uniq.shape[0]
    sel = bins[idx]
    cnt = np.bincount(sel, minlength=n).astype(np.float64)
    sr = np.bincount(sel, weights=r[idx], minlength=n)
    sg = np.bincount(sel, weights=g[idx], minlength=n)
    sb = np.bincount(sel, weights=b[idx], minlength=n)
    return bins, int(white.sum()), cnt, sr, sg, sb


def quantize(img: Rgba, colors: int, white_min: float = 245, mode: PaletteMode = 'classic') -> Quantized:
    total = img.width * img.height
    px = img.data.reshape(-1, 4)[:total].astype(np.int64)
    h = _histogram(px, white_min, 5)
    bits = 6
    while bits <= 8 and h[2].shape[0] < colors * BINS_PER_COLOR:
        h = _histogram(px, white_min, bits)
        bits += 1
    bins, whites, cnt, sr, sg, sb = h
    n = cnt.shape[0]
    lab0, lab1, lab2 = np.zeros(n), np.zeros(n), np.zeros(n)
    _bin_lab(cnt, sr, sg, sb, lab0, lab1, lab2)
    palette: list[str] = []
    bin_label = np.full(n, -1, dtype=np.int64)
    if n and mode == 'vivid':
        group, K = _vivid_labels(cnt, lab0, lab1, lab2, colors)
        codes = _vivid_palette(group, K, cnt, lab0, lab1, lab2)
        remap = np.full(K, -1, dtype=np.int64)
        for j in range(K):
            if codes[j] >= 0:
                palette.append(to_hex(codes[j]))
                remap[j] = len(palette) - 1
        bin_label = remap[group]
    elif n:
        pal = _median_cut(n, cnt, (lab0, lab1, lab2), colors)
        _kmeans(pal, cnt, lab0, lab1, lab2, bin_label)
        # cluster color = mean RGB of its pixels; empty clusters are dropped
        codes = _classic_palette(pal.shape[0], bin_label, cnt, sr, sg, sb)
        remap = np.full(pal.shape[0], -1, dtype=np.int64)
        for j in range(pal.shape[0]):
            if codes[j] >= 0:
                palette.append(to_hex(codes[j]))
                remap[j] = len(palette) - 1
        bin_label = remap[bin_label]
    white = -1
    if whites:
        palette.append('#ffffff')
        white = len(palette) - 1
    label = np.where(bins < 0, white, bin_label[np.maximum(bins, 0)] if n else white).astype(np.int64)
    return Quantized(label, palette, white)


def _pal_lab(palette: list[str]) -> np.ndarray:
    pal = np.zeros(len(palette) * 3)
    for i, h in enumerate(palette):
        c = from_hex(h)
        pal[i * 3 : i * 3 + 3] = list(oklab_f(float(c >> 16), float((c >> 8) & 255), float(c & 255)))
    return pal


@jit
def _cohere_vivid(label, lab, n, K, white, codes):
    acc = np.zeros(K * 5)
    for i in range(n):
        a = label[i] * 5
        A = lab[i * 3 + 1]
        B = lab[i * 3 + 2]
        acc[a] += lab[i * 3]
        acc[a + 1] += A
        acc[a + 2] += B
        acc[a + 3] += math.hypot(A, B)
        acc[a + 4] += 1
    for l in range(K):
        if l != white and acc[l * 5 + 4]:
            codes[l] = _vivid_code(acc[l * 5], acc[l * 5 + 1], acc[l * 5 + 2], acc[l * 5 + 3], acc[l * 5 + 4])


@jit
def _cohere_classic(label, data, n, K, white, codes):
    acc = np.zeros(K * 4)
    for i in range(n):
        a = label[i] * 4
        acc[a] += data[i * 4]
        acc[a + 1] += data[i * 4 + 1]
        acc[a + 2] += data[i * 4 + 2]
        acc[a + 3] += 1
    for l in range(K):
        if l != white and acc[l * 4 + 3]:
            codes[l] = rgb_code(acc[l * 4] / acc[l * 4 + 3], acc[l * 4 + 1] / acc[l * 4 + 3], acc[l * 4 + 2] / acc[l * 4 + 3])


def cohere(img: Rgba, q: Quantized, lam: float, mode: PaletteMode = 'classic', rounds: int = 3) -> Quantized:
    """Связная палитра: чередует сглаживание по Поттсу и пересчёт цветов палитры как средних своих клеток.

    lam — штраф за несовпадающего соседа в единицах квадрата расстояния OKLab. Белый холст не меняется.
    """
    n = img.width * img.height
    K = len(q.palette)
    lab = lab_of(img.data, n)
    label = q.label.copy()
    palette = list(q.palette)
    pal = _pal_lab(palette)
    data = img.data.astype(np.int64)
    for _ in range(rounds):
        potts(img.width, img.height, label, lab, pal, lam)
        codes = np.array([from_hex(h) for h in palette], dtype=np.int64)
        if mode == 'vivid':
            _cohere_vivid(label, lab, n, K, q.white, codes)
        else:
            _cohere_classic(label, data, n, K, q.white, codes)
        palette = [to_hex(c) for c in codes]
        pal = _pal_lab(palette)
    return Quantized(label, palette, q.white)
