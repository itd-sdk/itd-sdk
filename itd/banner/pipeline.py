"""Pipeline: preparation -> grid -> palette -> cleaning -> engine -> limits check -> recoloring -> quality.

In auto mode it walks the detail ladder and takes the most detailed step that fits the site limits.
"strokes" knows no palette, cleaning or ladder: it puts as many strokes as the site allows.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from typing import Literal

import numpy as np

from itd.banner.color import from_hex, lab_of, oklab
from itd.banner.engines.exact import exact
from itd.banner.engines.layers import layers
from itd.banner.engines.strokes import strokes
from itd.banner.image import Adjust, Rgba, adjust, downsample
from itd.banner.jsmath import f32, js_pow, js_round
from itd.banner.limits import MAX_OPS, MAX_POINTS, Op, Stats, split_long, stats
from itd.banner.metrics import Quality, compare
from itd.banner.quantize import PaletteMode, Quantized, cohere, quantize
from itd.banner.raster import render_ops
from itd.banner.recolor import recolor
from itd.banner.segment import absorb_edges, despeckle, merge_small, smooth_labels

Engine = Literal['layers', 'exact', 'strokes']
OnProgress = Callable[[str, float], None]


@dataclass(frozen=True)
class Detail:
    cell: int
    """Размер клетки сетки в пикселях баннера."""
    colors: int
    """Цветов в палитре."""
    smooth: float
    """Проходов сглаживания карты цветов."""
    min_area: int
    """Пятна меньше этой площади в пикселях баннера сливаются с соседями."""


@dataclass
class Params:
    """Настройки расчёта (как в программе «ИТД кастом»)."""

    engine: Engine = 'layers'
    """`layers` — «Слои», `exact` — «Точный», `strokes` — «Мазки»."""
    auto: bool = True
    """Подобрать самую подробную детализацию, которая влезает в лимиты сайта (для `layers` и `exact`)."""
    palette_mode: PaletteMode = 'vivid'
    """`vivid` — «Сочная» (частым и насыщенным цветам больше оттенков), `classic` — median cut + k-means."""
    merge: float = 0
    """Связность палитры 0…100: штраф за соседей другого цвета, убирает россыпь пятен на переходах."""
    sharp_edges: bool = False
    """Резкие края: полоски сглаживания вдоль контуров отдаются соседним областям (меньше штрихов, края жёстче)."""
    cell: int = 1
    colors: int = 48
    smooth: float = 0
    min_area: int = 4
    tol: float = 0.4
    """Допуск 0…1: насколько можно задевать уже нарисованные соседние цвета там, где этого не видно."""
    route_points: int = 24
    """Сколько точек обхода дешевле нового штриха."""
    white_min: float = 245
    """Светлее этого по всем каналам = белый холст; 254 — только чисто белый; 255 и выше — выкл."""
    adjust: Adjust = field(default_factory=Adjust)

    @property
    def detail(self) -> Detail:
        return Detail(self.cell, self.colors, self.smooth, self.min_area)


DEFAULTS = Params()


def merge_lambda(v: float) -> float:
    """Связность 0…100 → штраф Поттса: 1e-4…3e-2 по логарифму, 0 = выключено."""
    return 1e-4 * js_pow(300.0, v / 100) if v > 0 else 0.0


# Detail ladder from the most detailed to the coarsest. On photos it pays off most to drop small spots with a large
# palette first, then to shrink the palette and only then to enlarge the cell.
LADDER: list[Detail] = [
    Detail(1, 256, 0, 1),
    Detail(1, 128, 0, 1),
    Detail(1, 128, 0, 2),
    Detail(1, 128, 0, 4),
    Detail(1, 128, 0, 8),
    Detail(1, 128, 1, 8),
    Detail(1, 128, 1, 16),
    Detail(1, 128, 1, 24),
    Detail(1, 128, 1, 48),
    Detail(1, 128, 2, 64),
    Detail(1, 96, 2, 96),
    Detail(1, 64, 2, 128),
    Detail(1, 48, 2, 192),
    Detail(2, 48, 1, 256),
    Detail(2, 32, 1, 384),
    Detail(2, 24, 2, 512),
    Detail(3, 24, 2, 768),
    Detail(3, 16, 2, 1024),
    Detail(4, 16, 2, 1536),
    Detail(4, 12, 2, 2048),
    Detail(6, 10, 2, 3072),
    Detail(8, 8, 2, 4096)
]


@dataclass
class Tried:
    detail: Detail
    ops: int
    points: int
    fits: bool


@dataclass
class Result:
    ops: list[Op]
    stats: Stats
    quality: Quality
    detail: Detail
    palette: list[str]
    tried: list[Tried]
    """Сколько вариантов перебрал подбор и сколько из них влезло."""


def _pal_lab(palette: list[str], white: bool) -> np.ndarray:
    lab = np.zeros((len(palette) + (1 if white else 0)) * 3)
    for k, h in enumerate(palette):
        c = from_hex(h)
        lab[k * 3 : k * 3 + 3] = [f32(v) for v in oklab(c >> 16, (c >> 8) & 255, c & 255)]
    if white:
        lab[len(palette) * 3 :] = [f32(v) for v in oklab(255, 255, 255)]
    return lab


def _ops(ok, colors, starts, pts, palette: list[str], widths) -> list[Op] | None:
    if not ok:
        return None
    return [
        Op('brush', palette[colors[k]], float(widths[k]), [(float(x), float(y)) for x, y in pts[starts[k] : starts[k + 1]]]) for k in range(colors.shape[0])
    ]


class Session:
    """Кэш промежуточных этапов в пределах одного изображения."""

    def __init__(self, src: Rgba):
        self.src = src
        self._adj_key: str | None = None
        self._target: Rgba
        self._target_lab: np.ndarray
        self._grids: dict[int, Rgba] = {}
        self._quants: dict[tuple, Quantized] = {}

    def _prepare(self, p: Params):
        key = repr(asdict(p.adjust))
        if key == self._adj_key:
            return
        self._adj_key = key
        self._target = adjust(self.src, p.adjust)
        self._target_lab = lab_of(self._target.data, self._target.width * self._target.height)
        self._grids.clear()
        self._quants.clear()

    def _grid(self, cell: int) -> Rgba:
        if cell not in self._grids:
            self._grids[cell] = downsample(self._target, cell)
        return self._grids[cell]

    def _quant(self, cell: int, colors: int, white_min: float, mode: PaletteMode = 'classic', merge: float = 0) -> Quantized:
        key = (cell, colors, white_min, mode, merge)
        q = self._quants.get(key)
        if q is None:
            if merge > 0:
                q = cohere(self._grid(cell), self._quant(cell, colors, white_min, mode), merge_lambda(merge) / cell, mode)
            else:
                q = quantize(self._grid(cell), colors, white_min, mode)
            self._quants[key] = q
        return q

    def build(self, p: Params, d: Detail, limit: bool) -> tuple[list[Op], list[str]] | None:
        """Один прогон движка; None, если явно не влезает в лимиты (прервано)."""
        self._prepare(p)
        g = self._grid(d.cell)
        q = self._quant(d.cell, d.colors, p.white_min, p.palette_mode, p.merge)
        K = len(q.palette)
        label = q.label
        if K > 1:
            lab = _pal_lab(q.palette, False)
            label = label.copy()
            if p.sharp_edges:
                absorb_edges(g.width, g.height, label, K, lab)
            if d.smooth > 0:
                label = despeckle(g.width, g.height, label, K)
            # whole passes are full; the fraction .25/.5/.75 is a soft pass that needs 8/7/6 foreign cells out of 9
            full = math.floor(d.smooth + 1e-9)
            part = d.smooth - full
            for _ in range(full):
                label = smooth_labels(g.width, g.height, label, K)
            if part > 0.01:
                label = smooth_labels(g.width, g.height, label, K, 9 - int(js_round(part * 4)))
            merge_small(g.width, g.height, label, K, max(1, int(js_round(d.min_area / (d.cell * d.cell)))), lab, True)
        abort_ops, abort_points = (MAX_OPS, MAX_POINTS) if limit else (0, 0)
        if p.engine == 'exact':
            ok, colors, starts, pts = exact(g.width, g.height, label, K, q.white, d.cell, abort_ops, abort_points)
            ops = _ops(ok, colors, starts, pts, q.palette, np.full(colors.shape[0], float(d.cell)))
        else:
            ok, colors, widths, starts, pts = layers(
                g.width, g.height, label, K, _pal_lab(q.palette, True), q.white, d.cell, float(p.tol), int(p.route_points), abort_ops, abort_points
            )
            ops = _ops(ok, colors, starts, pts, q.palette, widths)
        if ops is None:
            return None
        return split_long(ops), q.palette

    def target_image(self, p: Params) -> Rgba:
        """Картинка после тона и шумоподавления, к которой стремится движок."""
        self._prepare(p)
        return self._target

    def quality(self, ops: list[Op]) -> Quality:
        t = self._target
        return compare(render_ops(ops, t.width, t.height), self._target_lab, t.width * t.height)

    def run(self, p: Params = DEFAULTS, on_progress: OnProgress | None = None) -> Result:
        progress = on_progress or (lambda stage, done: None)
        self._prepare(p)
        tried: list[Tried] = []

        def fits(ops: list[Op]) -> bool:
            s = stats(ops)
            return s.ops <= MAX_OPS and s.points <= MAX_POINTS

        best: tuple[list[Op], list[str], Detail] | None = None
        if p.engine == 'strokes':
            d = Detail(1, 0, 0, 1)
            ops = strokes(self._target, MAX_OPS, lambda f: progress('Мазки', f))
            best = (ops, [], d)
            s = stats(ops)
            tried.append(Tried(d, s.ops, s.points, fits(ops)))
        elif not p.auto:
            d = p.detail
            progress('Штрихи', 0)
            r = self.build(p, d, False)
            assert r is not None
            best = (r[0], r[1], d)
            s = stats(r[0])
            tried.append(Tried(d, s.ops, s.points, fits(r[0])))
        else:
            # binary search for the most detailed step that fits; the size drops almost monotonically down the ladder
            lo, hi, step = 0, len(LADDER) - 1, 0
            total = math.ceil(math.log2(len(LADDER))) + 1
            while lo <= hi:
                mid = (lo + hi) >> 1
                d = LADDER[mid]
                progress(f'Подбор {step + 1}/{total}', step / total)
                r = self.build(p, d, True)
                step += 1
                ok = r is not None and fits(r[0])
                s = stats(r[0]) if r is not None else None
                tried.append(Tried(d, s.ops if s else MAX_OPS + 1, s.points if s else MAX_POINTS + 1, ok))
                if ok:
                    assert r is not None
                    best = (r[0], r[1], d)
                    hi = mid - 1
                else:
                    lo = mid + 1
            if best is None:
                d = LADDER[-1]
                r = self.build(p, d, False)
                assert r is not None
                best = (r[0], r[1], d)
        progress('Перекраска', 1)
        ops = recolor(best[0], self._target_lab, self._target.width, self._target.height)
        progress('Оценка', 1)
        return Result(ops, stats(ops), self.quality(ops), best[2], best[1], tried)


def run(src: Rgba, params: Params | None = None, on_progress: OnProgress | None = None, **overrides) -> Result:
    """Картинка 1100×380 → штрихи. overrides — поля Params (engine='strokes', colors=64…)."""
    p = replace(params or DEFAULTS, **overrides)
    return Session(src).run(p, on_progress)
