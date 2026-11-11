from __future__ import annotations

import warnings
from collections.abc import Callable
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any
from uuid import UUID

from itd.api.files import upload_banner_drawing
from itd.core.base import ITDBaseModel

if TYPE_CHECKING:
    from itd.banner import Op, Params, Result, SimpleResult
    from itd.core.client import Client


class BannerDrawing(ITDBaseModel):
    """Рисунок-баннер (1100×380, штрихи кистью), загруженный на сайт. Его id ставится в баннер профиля."""

    _refreshable = False

    id: UUID
    url: str | None = None

    def __init__(self, ops: list[Op] | Result | SimpleResult, client: Client | None = None):
        """Загрузить готовые штрихи или результат расчета (`itd.banner.run`, `itd.banner.simple.run`).

        Raises:
            ValueError: рисунок нарушает лимиты сайта (проверяется до отправки).
        """
        from itd.banner import drawing, validate

        super().__init__(client)
        self.result: Result | SimpleResult | None = None if isinstance(ops, list) else ops
        self.ops: list[Op] = list(ops) if isinstance(ops, list) else ops.ops
        errors = validate(self.ops)
        if errors:
            raise ValueError('Banner drawing is not accepted by the site: ' + '; '.join(errors))
        self._fill_from_data(upload_banner_drawing(self.client, drawing(self.ops)).json())

    @classmethod
    def from_image(
        cls,
        image: Any,
        params: Params | None = None,
        *,
        fit: str = 'cover',
        optimize: int = 0,
        on_progress: Callable[[str, float], None] | None = None,
        client: Client | None = None,
        **overrides: Any
    ) -> BannerDrawing:
        """Нарисовать картинку штрихами и загрузить.

        Args:
            image: путь, bytes, файл, `PIL.Image`, массив numpy (h×w×3/4) или `itd.banner.Rgba` 1100×380.
            params: настройки расчета (`itd.banner.Params`), по умолчанию `itd.banner.DEFAULTS`.
            fit: `cover` — заполнить кадр и обрезать по центру, `contain` — вписать целиком, `stretch` — растянуть.
            optimize: уровень оптимизации 0…3: перебрать варианты настроек и взять самый похожий, который влезает в лимиты.
            on_progress: `(этап, доля 0…1)`.
            **overrides: поля `Params`, например `engine='strokes'` или `level=0`. `engine='simple'` — простой режим
                без дополнительных зависимостей (низкое качество, из настроек только `colors` и `cell`).
        """
        return cls(render(image, params, fit=fit, optimize=optimize, on_progress=on_progress, **overrides), client)

    @property
    def dE(self) -> float | None:
        """Средний ΔE×100 превью относительно картинки (около 2 — на глаз почти не отличить); у простого режима нет."""
        quality = getattr(self.result, 'quality', None)
        return quality.dE if quality else None

    def __str__(self) -> str:
        return str(self.id)


def render(
    image: Any,
    params: Params | None = None,
    *,
    fit: str = 'cover',
    optimize: int = 0,
    on_progress: Callable[[str, float], None] | None = None,
    **overrides: Any
) -> Result | SimpleResult:
    """Посчитать штрихи для картинки локально, без загрузки.

    Без numpy и Pillow (`itd-sdk[banner]`) или с `engine='simple'` работает простой режим: только стандартная библиотека,
    низкое качество.
    """
    engine = overrides.get('engine', params.engine if params is not None else None)
    if engine == 'simple' or not _installed('numpy') or not _installed('PIL'):
        from itd.banner import simple

        if engine != 'simple':
            warnings.warn(
                'numpy or Pillow is not installed: the banner is drawn in the simple mode (low quality). Install itd-sdk[banner] for the full quality',
                stacklevel=3
            )
        return simple.run(image, fit=fit, colors=overrides.get('colors', 16), cell=overrides.get('cell'), on_progress=on_progress)

    import numpy as np

    from itd.banner import H, Rgba, W, fit_image, rgba_from_array, run

    if not _installed('numba'):
        warnings.warn('numba is not installed: drawing a banner takes minutes. Install itd-sdk[banner] to make it fast', stacklevel=3)
    if isinstance(image, Rgba):
        src = image if (image.width, image.height) == (W, H) else fit_image(_rgba_to_pil(image), fit)
    elif isinstance(image, np.ndarray):
        src = rgba_from_array(image)
        if (src.width, src.height) != (W, H):
            src = fit_image(_rgba_to_pil(src), fit)
    else:
        src = fit_image(image, fit)
    return run(src, params, on_progress, optimize, **overrides)


def _installed(name: str) -> bool:
    try:
        return find_spec(name) is not None
    except ValueError:  # module set to None in sys.modules
        return False


def _rgba_to_pil(img):
    from PIL import Image

    return Image.frombytes('RGBA', (img.width, img.height), bytes(img.data))
