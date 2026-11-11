"""Картинка → штрихи для рисунка-баннера 1100×380 (порт «ИТД кастом»).

Основные движки требуют numpy, numba и Pillow: `uv add itd-sdk[banner]` (или `pip install itd-sdk[banner]`).
Без numba они работают в чистом Python, но в десятки раз медленнее. Простой режим (`itd.banner.simple`) и проверка
лимитов работают вообще без дополнительных зависимостей.
"""

from importlib import import_module
from typing import Any

from itd.banner.limits import H, MAX_OPS, MAX_POINTS, MAX_POINTS_PER_OP, MAX_WIDTH, W, Op, Stats, drawing, split_long, stats, validate
from itd.banner.simple import SimpleResult

# numpy-based parts are imported on first use, so the package works without the banner extra
_LAZY = {
    'JIT': 'itd.banner.jit',
    'Adjust': 'itd.banner.image',
    'Rgba': 'itd.banner.image',
    'fit_image': 'itd.banner.image',
    'rgba_from_array': 'itd.banner.image',
    'Quality': 'itd.banner.metrics',
    'DEFAULTS': 'itd.banner.pipeline',
    'LADDER': 'itd.banner.pipeline',
    'OPTIMIZE': 'itd.banner.pipeline',
    'Detail': 'itd.banner.pipeline',
    'Engine': 'itd.banner.pipeline',
    'Params': 'itd.banner.pipeline',
    'Result': 'itd.banner.pipeline',
    'Session': 'itd.banner.pipeline',
    'Variant': 'itd.banner.pipeline',
    'run': 'itd.banner.pipeline',
    'render_ops': 'itd.banner.raster',
    'to_rgba': 'itd.banner.raster'
}


def __getattr__(name: str) -> Any:
    if name in _LAZY:
        return getattr(import_module(_LAZY[name]), name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


__all__ = ['W', 'H', 'MAX_OPS', 'MAX_POINTS', 'MAX_POINTS_PER_OP', 'MAX_WIDTH', 'Op', 'Stats', 'SimpleResult']
__all__ += ['drawing', 'split_long', 'stats', 'validate', *_LAZY]
