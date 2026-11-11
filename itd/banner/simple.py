"""Simple mode without extra dependencies (standard library only): low quality, but works on a plain `pip install itd-sdk`.

The picture is averaged into a coarse grid, reduced to a small palette and painted with horizontal brush runs, one row
of cells per run. Colors go from the most frequent to the rarest; a run of a color may pass over cells of colors painted
later, they cover it afterwards, so a row needs few strokes. The grid gets coarser until the drawing fits the site limits.
PNG is read without dependencies; other formats need Pillow.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

from itd.banner.limits import MAX_OPS, MAX_POINTS, H, Op, Stats, W, stats

CELLS = (4, 5, 6, 8, 10, 12, 16, 20, 24, 32)
SAMPLES = 3  # samples per cell side when averaging the picture into the grid
WHITE_MIN = 245  # lighter than this in every channel = white canvas, not painted


@dataclass
class SimpleResult:
    ops: list[Op]
    stats: Stats
    cell: int
    """Размер клетки сетки в пикселях баннера."""
    palette: list[str] = field(default_factory=list)


@dataclass
class _Image:
    width: int
    height: int
    rgb: bytes  # 3 bytes per pixel, transparency already put on white


def _read_png(data: bytes) -> _Image:
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG')
    p, width, height, ctype, plte, trns, idat = 8, 0, 0, 0, b'', b'', []
    while p < len(data):
        (length,) = struct.unpack('>I', data[p : p + 4])
        name, chunk = data[p + 4 : p + 8], data[p + 8 : p + 8 + length]
        if name == b'IHDR':
            width, height, depth, ctype, _, _, interlace = struct.unpack('>IIBBBBB', chunk)
            if depth != 8 or interlace:
                raise ValueError('only 8-bit non-interlaced PNG is supported without Pillow')
        elif name == b'PLTE':
            plte = chunk
        elif name == b'tRNS':
            trns = chunk
        elif name == b'IDAT':
            idat.append(chunk)
        p += 12 + length
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    stride = width * bpp
    raw = zlib.decompress(b''.join(idat))
    px = bytearray(height * stride)
    prev = bytearray(stride)
    for y in range(height):
        f = raw[y * (stride + 1)]
        cur = bytearray(raw[y * (stride + 1) + 1 : (y + 1) * (stride + 1)])
        if f == 1:
            for i in range(bpp, stride):
                cur[i] = (cur[i] + cur[i - bpp]) & 255
        elif f == 2:
            cur = bytearray((a + b) & 255 for a, b in zip(cur, prev))
        elif f == 3:
            for i in range(stride):
                cur[i] = (cur[i] + ((cur[i - bpp] if i >= bpp else 0) + prev[i]) // 2) & 255
        elif f == 4:
            for i in range(stride):
                a = cur[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                q = a + b - c
                pa, pb, pc = abs(q - a), abs(q - b), abs(q - c)
                cur[i] = (cur[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        px[y * stride : (y + 1) * stride] = cur
        prev = cur
    rgb = bytearray(width * height * 3)
    for i in range(width * height):
        o = i * bpp
        if ctype == 3:
            k = px[o]
            r, g, b = plte[k * 3 : k * 3 + 3]
            al = trns[k] if k < len(trns) else 255
        elif ctype in (0, 4):
            r = g = b = px[o]
            al = px[o + 1] if ctype == 4 else 255
        else:
            r, g, b = px[o], px[o + 1], px[o + 2]
            al = px[o + 3] if ctype == 6 else 255
        if al < 255:
            r, g, b = ((v * al + 255 * (255 - al)) // 255 for v in (r, g, b))
        rgb[i * 3 : i * 3 + 3] = bytes((r, g, b))
    return _Image(width, height, bytes(rgb))


def _load(image: Any) -> _Image:
    if hasattr(image, 'width') and hasattr(image, 'height') and hasattr(image, 'data') and not hasattr(image, 'convert'):
        # itd.banner.Rgba
        data = bytes(image.data)
        rgb = bytearray(image.width * image.height * 3)
        rgb[0::3], rgb[1::3], rgb[2::3] = data[0::4], data[1::4], data[2::4]
        return _Image(image.width, image.height, bytes(rgb))
    if hasattr(image, 'shape') and hasattr(image, 'tobytes'):
        # numpy array h x w x 3/4 (uint8)
        h, w, ch = image.shape
        data = image.astype('uint8').tobytes()
        rgb = bytearray(w * h * 3)
        for c in range(3):
            rgb[c::3] = data[c::ch]
        if ch == 4:
            for i, al in enumerate(data[3::4]):
                if al < 255:
                    for c in range(3):
                        rgb[i * 3 + c] = (rgb[i * 3 + c] * al + 255 * (255 - al)) // 255
        return _Image(w, h, bytes(rgb))
    if isinstance(image, (str, Path)):
        image = Path(image).read_bytes()
    elif hasattr(image, 'read'):
        image = image.read()
    if isinstance(image, (bytes, bytearray)):
        if bytes(image[:8]) == b'\x89PNG\r\n\x1a\n':
            try:
                return _read_png(bytes(image))
            except ValueError:
                pass
        try:
            from PIL import Image
        except ModuleNotFoundError:
            raise ImportError('Without Pillow only 8-bit non-interlaced PNG can be read. Install Pillow or itd-sdk[banner]')
        image = Image.open(BytesIO(bytes(image)))
    if hasattr(image, 'convert'):  # PIL.Image
        from PIL import Image

        img = image.convert('RGBA')
        canvas = Image.new('RGBA', img.size, (255, 255, 255, 255))
        canvas.alpha_composite(img)
        return _Image(img.width, img.height, canvas.convert('RGB').tobytes())
    raise TypeError(f'unsupported image: {type(image).__name__}')


def _grid(img: _Image, cell: int, fit: str) -> tuple[int, int, list[tuple[int, int, int]]]:
    """Mean color of every cell of the banner grid, the picture placed into the banner by fit."""
    cols, rows = -(-W // cell), -(-H // cell)
    if fit == 'stretch':
        sx, sy, ox, oy = img.width / W, img.height / H, 0.0, 0.0
    else:
        k = max(W / img.width, H / img.height) if fit == 'cover' else min(W / img.width, H / img.height)
        sx = sy = 1 / k
        ox, oy = (W - img.width * k) / 2, (H - img.height * k) / 2
    rgb = img.rgb
    out = []
    for gy in range(rows):
        for gx in range(cols):
            r = g = b = 0
            for j in range(SAMPLES):
                py = (gy * cell + (j + 0.5) * cell / SAMPLES - oy) * sy
                for i in range(SAMPLES):
                    px = (gx * cell + (i + 0.5) * cell / SAMPLES - ox) * sx
                    if 0 <= px < img.width and 0 <= py < img.height:
                        o = (int(py) * img.width + int(px)) * 3
                        r += rgb[o]
                        g += rgb[o + 1]
                        b += rgb[o + 2]
                    else:  # outside the picture (contain): white
                        r += 255
                        g += 255
                        b += 255
            n = SAMPLES * SAMPLES
            out.append((r // n, g // n, b // n))
    return cols, rows, out


def _palette(cells: list[tuple[int, int, int]], colors: int) -> tuple[list[tuple[int, int, int]], list[int]]:
    """Median cut, then a few k-means rounds. Returns the palette and the palette index of every cell."""
    boxes = [list(range(len(cells)))]
    while len(boxes) < colors:
        best, axis, spread = -1, 0, 0
        for k, box in enumerate(boxes):
            for a in range(3):
                vals = [cells[i][a] for i in box]
                if len(box) > 1 and max(vals) - min(vals) > spread:
                    best, axis, spread = k, a, max(vals) - min(vals)
        if best < 0:
            break
        box = sorted(boxes.pop(best), key=lambda i: cells[i][axis])
        boxes += [box[: len(box) // 2], box[len(box) // 2 :]]
    pal = [tuple(sum(cells[i][a] for i in box) / len(box) for a in range(3)) for box in boxes if box]
    label = [0] * len(cells)
    for _ in range(4):
        acc = [[0.0, 0.0, 0.0, 0] for _ in pal]
        for i, (r, g, b) in enumerate(cells):
            k = min(range(len(pal)), key=lambda k: (r - pal[k][0]) ** 2 + (g - pal[k][1]) ** 2 + (b - pal[k][2]) ** 2)
            label[i] = k
            a = acc[k]
            a[0] += r
            a[1] += g
            a[2] += b
            a[3] += 1
        pal = [(a[0] / a[3], a[1] / a[3], a[2] / a[3]) if a[3] else p for a, p in zip(acc, pal)]
    return [(round(r), round(g), round(b)) for r, g, b in pal], label


def _draw(cols: int, rows: int, cell: int, pal: list[tuple[int, int, int]], label: list[int]) -> list[Op]:
    area = [0] * len(pal)
    for k in label:
        area[k] += 1
    order = sorted((k for k in range(len(pal)) if area[k]), key=lambda k: -area[k])
    rank = [0] * len(pal)
    for r, k in enumerate(order):
        rank[k] = r
    white = [all(v > WHITE_MIN for v in c) for c in pal]
    hexes = ['#%02x%02x%02x' % c for c in pal]
    ops: list[Op] = []
    for r, k in enumerate(order):
        if r == 0:
            # the most frequent color fills the whole canvas (white is the canvas itself)
            if not white[k]:
                ops += [Op('brush', hexes[k], 100, [(0, y), (W, y)]) for y in range(50, H + 50, 100)]
            continue
        for gy in range(rows):
            y = (gy + 0.5) * cell
            gx = 0
            while gx < cols:
                # a run over cells of this or later colors, from its first to its last cell of this color
                if rank[label[gy * cols + gx]] < r:
                    gx += 1
                    continue
                a = b = -1
                while gx < cols and rank[label[gy * cols + gx]] >= r:
                    if label[gy * cols + gx] == k:
                        b = gx
                        if a < 0:
                            a = gx
                    gx += 1
                if a >= 0:
                    ops.append(Op('brush', hexes[k], cell, [((a + 0.5) * cell, y), ((b + 0.5) * cell, y)]))
    return ops


def run(image: Any, *, fit: str = 'cover', colors: int = 16, cell: int | None = None, on_progress: Callable[[str, float], None] | None = None) -> SimpleResult:
    """Картинка → штрихи без дополнительных зависимостей (низкое качество).

    Args:
        image: путь, bytes, файл (PNG, с Pillow — любой формат), `PIL.Image` или `itd.banner.Rgba`.
        fit: `cover` — заполнить кадр и обрезать по центру, `contain` — вписать целиком, `stretch` — растянуть.
        colors: цветов в палитре.
        cell: размер клетки в пикселях; по умолчанию самая мелкая, при которой рисунок влезает в лимиты сайта.
    """
    img = _load(image)
    cells = [cell] if cell else list(CELLS)
    result = None
    for i, c in enumerate(cells):
        if on_progress:
            on_progress(f'Клетка {c} px', i / len(cells))
        cols, rows, grid = _grid(img, c, fit)
        pal, label = _palette(grid, colors)
        ops = _draw(cols, rows, c, pal, label)
        result = SimpleResult(ops, stats(ops), c, ['#%02x%02x%02x' % p for p in pal])
        if result.stats.ops <= MAX_OPS and result.stats.points <= MAX_POINTS:
            break
    if on_progress:
        on_progress('Готово', 1)
    assert result is not None
    return result
