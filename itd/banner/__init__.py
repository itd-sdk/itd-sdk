"""Картинка → штрихи для рисунка-баннера 1100×380 (порт «ИТД кастом»).

Нужны numpy, numba и Pillow: `uv add itd-sdk[banner]` (или `pip install itd-sdk[banner]`).
Без numba тот же код работает в чистом Python: результат тот же, но в десятки раз медленнее.
"""

from itd.banner.jit import JIT
from itd.banner.image import Adjust, Rgba, fit_image, rgba_from_array
from itd.banner.limits import H, MAX_OPS, MAX_POINTS, MAX_POINTS_PER_OP, MAX_WIDTH, W, Op, Stats, drawing, split_long, stats, validate
from itd.banner.metrics import Quality
from itd.banner.pipeline import DEFAULTS, LADDER, Detail, Engine, Params, Result, Session, run
from itd.banner.raster import render_ops, to_rgba

__all__ = [
    'JIT',
    'W',
    'H',
    'MAX_OPS',
    'MAX_POINTS',
    'MAX_POINTS_PER_OP',
    'MAX_WIDTH',
    'Adjust',
    'Rgba',
    'Op',
    'Stats',
    'Quality',
    'Detail',
    'Engine',
    'Params',
    'Result',
    'Session',
    'DEFAULTS',
    'LADDER',
    'drawing',
    'split_long',
    'stats',
    'validate',
    'fit_image',
    'rgba_from_array',
    'render_ops',
    'to_rgba',
    'run'
]
