from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any
from uuid import UUID

from itd.api.files import upload_banner_drawing
from itd.core.base import ITDBaseModel

if TYPE_CHECKING:
    from itd.banner import Op, Params, Result
    from itd.core.client import Client


class BannerDrawing(ITDBaseModel):
    """Рисунок-баннер (1100×380, штрихи кистью), загруженный на сайт. Его id ставится в баннер профиля."""

    _refreshable = False

    id: UUID
    url: str | None = None

    def __init__(self, ops: list[Op] | Result, client: Client | None = None):
        """Загрузить готовые штрихи (или результат расчета `itd.banner.run`).

        Raises:
            ValueError: рисунок нарушает лимиты сайта (проверяется до отправки).
        """
        from itd.banner import Result, drawing, validate

        super().__init__(client)
        self.result: Result | None = ops if isinstance(ops, Result) else None
        self.ops: list[Op] = ops.ops if isinstance(ops, Result) else list(ops)
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
        on_progress: Callable[[str, float], None] | None = None,
        client: Client | None = None,
        **overrides: Any
    ) -> BannerDrawing:
        """Нарисовать картинку штрихами и загрузить.

        Args:
            image: путь, bytes, файл, `PIL.Image`, массив numpy (h×w×3/4) или `itd.banner.Rgba` 1100×380.
            params: настройки расчета (`itd.banner.Params`), по умолчанию `itd.banner.DEFAULTS`.
            fit: `cover` — заполнить кадр и обрезать по центру, `contain` — вписать целиком, `stretch` — растянуть.
            on_progress: `(этап, доля 0…1)`.
            **overrides: поля `Params`, например `engine='strokes'`.
        """
        return cls(render(image, params, fit=fit, on_progress=on_progress, **overrides), client)

    @property
    def dE(self) -> float | None:
        """Средний ΔE×100 превью относительно картинки (около 2 — на глаз почти не отличить)."""
        return self.result.quality.dE if self.result else None

    def __str__(self) -> str:
        return str(self.id)


def render(
    image: Any, params: Params | None = None, *, fit: str = 'cover', on_progress: Callable[[str, float], None] | None = None, **overrides: Any
) -> Result:
    """Посчитать штрихи для картинки локально, без загрузки."""
    try:
        import numpy as np

        from itd.banner import H, Rgba, W, fit_image, rgba_from_array, run
    except ModuleNotFoundError as e:
        raise ImportError(
            f'{e.name} is required for banner drawings. Install by running "uv add itd-sdk[banner]" (or "pip install itd-sdk[banner]" if you are using pip)'
        )

    if isinstance(image, Rgba):
        src = image if (image.width, image.height) == (W, H) else fit_image(_rgba_to_pil(image), fit)
    elif isinstance(image, np.ndarray):
        src = rgba_from_array(image)
        if (src.width, src.height) != (W, H):
            src = fit_image(_rgba_to_pil(src), fit)
    else:
        src = fit_image(image, fit)
    return run(src, params, on_progress, **overrides)


def _rgba_to_pil(img):
    from PIL import Image

    return Image.frombytes('RGBA', (img.width, img.height), bytes(img.data))
