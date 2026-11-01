# :material-brush: Баннер-рисунок
Баннер профиля — рисунок 1100×380 из штрихов кистью (`POST /api/files/banner-drawing`). SDK сам превращает картинку в штрихи: это порт программы «ИТД кастом» (`itd.banner`), результат совпадает с ней до последнего бита — те же штрихи, те же цвета, тот же ΔE.

Нужны `numpy`, `numba` и `Pillow`:

```
uv add itd-sdk[banner]
```

или через pip:

```
pip install itd-sdk[banner]
```

!!! note
    Без `numba` тот же код работает в чистом Python: результат такой же, но расчет идет в десятки раз дольше. Первый расчет с `numba` компилирует ядра (до минуты), потом они берутся из кэша.

## :material-image-edit: Поставить картинку баннером
```python
from itd import Me

me = Me()
me.update(banner='picture.jpg')  # нарисовать штрихами, загрузить и поставить
```

Картинка вписывается в кадр 1100×380 «заполнением» (лишнее обрезается по центру), прозрачное ложится на белый. Принимается путь, `bytes`, открытый файл, `PIL.Image`, массив numpy (h×w×3 или h×w×4) или `itd.banner.Rgba`.

`me.update` возвращает загруженный [`BannerDrawing`](#bannerdrawing) (или `None`, если баннер не рисовался).

### Другие значения `banner`
```python
from itd.enums import UNSET

me.update(banner=drawing)  # уже загруженный BannerDrawing
me.update(banner='5b1c6a0e-...')  # id загруженного рисунка (UUID или строка)
me.update(banner=UNSET)  # убрать баннер
```

!!! warning "banner_id"
    Параметра `banner_id` у `Me.update` больше нет, вместо него `banner` (см. [Migration Guide](../migration.md)). Строка, похожая на UUID, считается id, любая другая — путем к картинке.

## :material-tune: Свои настройки
```python
from itd.banner import Params

drawing = me.update_banner('picture.jpg', engine='strokes')  # поля Params ключевыми словами
drawing = me.update_banner('logo.png', Params(engine='layers', colors=16), fit='contain')
print(drawing.id, drawing.url, drawing.dE)
```

#### image <span class="mdx-badge"><span class="mdx-badge__icon">:material-image:</span><span class="mdx-badge__text">str | Path | bytes | PIL.Image | ndarray | Rgba</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Картинка.

#### params <span class="mdx-badge"><span class="mdx-badge__icon">:material-cog:</span><span class="mdx-badge__text">[Params](#params)</span></span>
Настройки расчета. По умолчанию `itd.banner.DEFAULTS`.

#### fit <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Как вписать картинку в 1100×380: `cover` (по умолчанию) — заполнить и обрезать по центру, `contain` — вписать целиком с белыми полями, `stretch` — растянуть.

#### on_progress <span class="mdx-badge"><span class="mdx-badge__icon">:material-function:</span><span class="mdx-badge__text">Callable[[str, float], None]</span></span>
Вызывается с названием этапа и долей 0…1.

#### **overrides
Поля [`Params`](#params) поверх `params`, например `engine='strokes'`, `colors=64`.

## :material-engine: Движки
| `engine` | Название | Что делает |
|---|---|---|
| `layers` | «Слои» | Цвета слоями от большого к мелкому, сначала широкие полосы, потом всё уже. Допуск по контрасту: на похожий цвет штрих заходит, на контрастный — почти нет. С `auto=True` подбирает самую подробную детализацию, которая влезает в лимиты сайта. Лучше всего для графики, логотипов, манги. |
| `strokes` | «Мазки» | Жадно кладет мазок туда, где отличие от картинки сейчас больше всего, с лучшим для этого места цветом; форму (ломаная до 8 точек) подбирает восхождением. Палитры и чистки нет, в лимиты укладывается сам. Лучше всего для фото и рисунков. |
| `exact` | «Точный» | Кисть шириной в клетку без чистки. |

Средний ΔE на 14 тестовых картинках программы: «Слои» — 2.06, «Мазки» — 1.49 (около 2 на глаз почти не отличить).

## :material-cog: Params
Настройки расчета (`itd.banner.Params`), такие же, как в программе. Для «Мазков» важен только `engine` и `adjust`.

#### engine <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">'layers' | 'exact' | 'strokes'</span></span>
Движок. По умолчанию `layers`.

#### auto <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Подобрать детализацию под лимиты сайта (лестница `itd.banner.LADDER`, двоичный поиск). Тогда `cell`, `colors`, `smooth` и `min_area` не используются. По умолчанию `True`.

#### palette_mode <span class="mdx-badge"><span class="mdx-badge__icon">:material-palette:</span><span class="mdx-badge__text">'vivid' | 'classic'</span></span>
`vivid` — «Сочная»: частым и насыщенным цветам больше оттенков, насыщенность не вымывается. `classic` — median cut + k-means.

#### cell, colors, smooth, min_area
Клетка сетки (px), цветов в палитре, проходов сглаживания карты цветов, площадь пятна (px²), меньше которой незаметные пятна сливаются с соседями.

#### merge <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Связность палитры 0…100 (модель Поттса): убирает россыпь пятен на переходах — главный способ уменьшить число штрихов. 0 — выкл.

#### sharp_edges <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Резкие края: полоски сглаживания вдоль контуров отдаются соседним областям. На графике штрихов в 2–5 раз меньше, края жестче.

#### tol <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Допуск 0…1: насколько штрих может задевать уже нарисованные соседние цвета там, где этого не видно.

#### route_points <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Сколько точек обхода дешевле нового штриха.

#### white_min <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Светлее этого по всем каналам — белый холст (не рисуется). 254 — только чисто белый, 255 и выше — выкл.

#### adjust <span class="mdx-badge"><span class="mdx-badge__icon">:material-image-filter-center-focus:</span><span class="mdx-badge__text">Adjust</span></span>
Тон картинки перед расчетом: `Adjust(brightness, contrast, saturation, denoise)`, первые три −1…1, `denoise` — сглаживание с сохранением краев 0…3.

## :material-calculator: Без загрузки
Посчитать и посмотреть, что получится, не отправляя на сайт:

```python
from PIL import Image
from itd.banner import W, H, fit_image, render_ops, run, to_rgba

result = run(fit_image('picture.jpg'), engine='strokes')
print(result.stats.ops, result.stats.points, result.quality.dE)

preview = to_rgba(render_ops(result.ops, W, H), W * H)  # так рисует сервер сайта
Image.frombytes('RGBA', (W, H), preview.tobytes()).save('preview.png')
```

Потом результат можно загрузить: `BannerDrawing(result)`.

---

# :material-brush: BannerDrawing
Загруженный рисунок-баннер.

```python
from itd import BannerDrawing

drawing = BannerDrawing.from_image('picture.jpg', engine='strokes')  # нарисовать и загрузить
drawing = BannerDrawing(result)  # загрузить результат itd.banner.run
drawing = BannerDrawing([Op('brush', '#ff0000', 20, [(100, 100), (300, 100)])])  # свои штрихи
me.update(banner=drawing)
```

Перед отправкой рисунок проверяется на лимиты сайта, при нарушении — `ValueError`.

## Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID рисунка. Его ставят в баннер.

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-link:</span><span class="mdx-badge__text">str</span></span>
PNG, который нарисовал сервер.

#### ops <span class="mdx-badge"><span class="mdx-badge__icon">:material-format-list-bulleted:</span><span class="mdx-badge__text">list[Op]</span></span>
Отправленные штрихи.

#### result <span class="mdx-badge"><span class="mdx-badge__icon">:material-calculator:</span><span class="mdx-badge__text">Result | None</span></span>
Результат расчета (штрихи, статистика, качество, детализация), если рисунок посчитан SDK.

#### dE <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float | None</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Средний ΔE×100 превью относительно картинки.

## Лимиты сайта
Замерены пробными загрузками 30.10.2026.

| Что | Предел |
|---|---|
| Штрихов | ≤ 2000 |
| Точек всего | ≤ 60 000 |
| Точек в одном штрихе | ≤ 4096 |
| Ширина кисти | ≤ 100, дробная можно |
| Цвет | только `#rrggbb` |

Штрих из одной точки сайт рисует кружком. Инструменты: `brush`, `line`, `rectangle`, `circle`, `eraser`.

## Ошибки при загрузке
 - `ValueError` - рисунок нарушает лимиты (проверка до отправки).
 - `BannerDrawingTooComplexError` - сайт посчитал рисунок слишком сложным (413).
 - `BannerDrawingRateLimitError` - слишком частые загрузки; с включенными повторами SDK сам подождет `retry_after` секунд.
 - `ValidationError`, `UploadError` - сайт не принял рисунок.
