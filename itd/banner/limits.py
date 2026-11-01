"""Drawing format of the site and its limits (measured by test uploads on 30.10.2026)."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from json import dumps
from typing import Literal

import numpy as np

W = 1100
H = 380

MAX_OPS = 2000  # 2001 -> 400
MAX_POINTS = 60000  # 60001 -> 413 BANNER_DRAWING_TOO_COMPLEX
MAX_POINTS_PER_OP = 4096  # 4097 -> 400
MAX_WIDTH = 100  # 101 -> 400, fractional width is allowed
MAX_BODY_BYTES = 2 << 20  # 2 MB passes, 8 MB does not; never reached because of the points limit

Tool = Literal['brush', 'line', 'rectangle', 'circle', 'eraser']
TOOLS: tuple[Tool, ...] = ('brush', 'line', 'rectangle', 'circle', 'eraser')

_HEX = re.compile(r'^#[0-9a-f]{6}$', re.IGNORECASE)


@dataclass
class Op:
    """Штрих рисунка баннера."""

    tool: Tool
    color: str
    """Цвет `#rrggbb`."""
    width: float
    """Ширина кисти, 0 < width ≤ 100."""
    points: list[tuple[float, float]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {'tool': self.tool, 'color': self.color, 'width': _num(self.width), 'points': [[_num(x), _num(y)] for x, y in self.points]}

    @classmethod
    def from_dict(cls, data: dict) -> Op:
        return cls(data['tool'], data['color'], data['width'], [(p[0], p[1]) for p in data['points']])


@dataclass
class Stats:
    ops: int
    points: int
    bytes: int
    max_points_per_op: int


def _num(v: float) -> int | float:
    # JSON.stringify writes 100 for 100.0
    return int(v) if isinstance(v, float) and v.is_integer() and abs(v) < 1e21 else v


def drawing(ops: list[Op]) -> dict:
    """Тело запроса загрузки рисунка."""
    return {'version': 1, 'width': W, 'height': H, 'ops': [o.to_dict() for o in ops]}


def _json_len(ops: list[Op]) -> int:
    text = dumps(drawing(ops), separators=(',', ':'), ensure_ascii=False)
    # JS writes exponents as 1e-7 / 1e+21, Python as 1e-07 / 1e+21
    return len(re.sub(r'e([+-])0(\d)', r'e\1\2', text))


def stats(ops: list[Op]) -> Stats:
    points = sum(len(o.points) for o in ops)
    return Stats(len(ops), points, _json_len(ops), max((len(o.points) for o in ops), default=0))


def validate(ops: list[Op]) -> list[str]:
    """Нарушения лимитов сайта; пустой список, если сайт должен принять рисунок."""
    s = stats(ops)
    errs: list[str] = []
    if not ops:
        errs.append('Рисунок пустой')
    if s.ops > MAX_OPS:
        errs.append(f'Штрихов {s.ops}, можно {MAX_OPS}')
    if s.points > MAX_POINTS:
        errs.append(f'Точек {s.points}, можно {MAX_POINTS}')
    if s.max_points_per_op > MAX_POINTS_PER_OP:
        errs.append(f'В штрихе {s.max_points_per_op} точек, можно {MAX_POINTS_PER_OP}')
    if s.bytes > MAX_BODY_BYTES:
        errs.append(f'Запрос {s.bytes / 1048576:.1f} МБ, можно 2 МБ')
    for o in ops:
        if not isinstance(o.color, str) or not _HEX.match(o.color):
            errs.append(f'Цвет {o.color} не в формате #rrggbb')
            break
        if not (o.width > 0 and o.width <= MAX_WIDTH):
            errs.append(f'Ширина {o.width} вне 0…100')
            break
        if not o.points or any(not (math.isfinite(p[0]) and math.isfinite(p[1])) for p in o.points):
            errs.append('Штрих без точек или с неверной координатой')
            break
    return errs


def split_long(ops: list[Op]) -> list[Op]:
    """Режет штрихи кисти длиннее лимита на куски с общей точкой на стыке."""
    out: list[Op] = []
    n = MAX_POINTS_PER_OP
    for o in ops:
        if len(o.points) <= n or o.tool != 'brush':
            out.append(o)
            continue
        for i in range(0, len(o.points) - 1, n - 1):
            out.append(Op(o.tool, o.color, o.width, o.points[i : i + n]))
    return out


@dataclass
class Packed:
    """Штрихи в массивах для ядер: инструмент, цвет 0xRRGGBB, ширина, начало точек штриха в pts."""

    tools: np.ndarray
    colors: np.ndarray
    widths: np.ndarray
    starts: np.ndarray
    pts: np.ndarray

    def __len__(self) -> int:
        return self.tools.shape[0]


def pack(ops: list[Op]) -> Packed:
    from itd.banner.color import from_hex

    starts = np.zeros(len(ops) + 1, dtype=np.int64)
    for k, o in enumerate(ops):
        starts[k + 1] = starts[k] + len(o.points)
    pts = np.zeros((int(starts[-1]), 2))
    for k, o in enumerate(ops):
        if o.points:
            pts[starts[k] : starts[k + 1]] = o.points
    return Packed(
        np.array([TOOLS.index(o.tool) for o in ops], dtype=np.int64),
        np.array([from_hex(o.color) for o in ops], dtype=np.int64),
        np.array([float(o.width) for o in ops], dtype=np.float64),
        starts,
        pts
    )
