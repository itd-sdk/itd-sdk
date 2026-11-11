"""Рисунок-баннер: порт «ИТД кастом» (itd.banner) и загрузка (BannerDrawing, Me.update) - без сети"""

import gzip
import json
import struct
import subprocess
import sys
import zlib
from pathlib import Path
from uuid import uuid4

import pytest

np = pytest.importorskip('numpy')

from helpers import make_client, make_response, make_token  # noqa: E402

from itd import BannerDrawing, Me  # noqa: E402
from itd.banner import DEFAULTS, JIT, LADDER, MAX_POINTS_PER_OP, Adjust, Op, Params, Rgba, Session, drawing, render_ops, run, split_long, validate  # noqa: E402
from itd.banner.color import from_oklab, oklab  # noqa: E402
from itd.banner.segment import merge_small  # noqa: E402
from itd.enums import UNSET  # noqa: E402
from itd.exceptions import BannerDrawingTooComplexError  # noqa: E402

pytestmark = pytest.mark.usefixtures('keep_default_client')
# without numba the same kernels run as plain Python: same result, but a picture takes minutes
needs_jit = pytest.mark.skipif(not JIT, reason='numba is not installed')

FIXTURES = Path(__file__).parent / 'fixtures' / 'banner'
W, H = 1100, 380


def brush(points, width=20.0, color='#ff0000') -> Op:
    return Op('brush', color, width, points)


def synthetic() -> Rgba:
    """Градиент, узор, круг, прямоугольник и белые полосы 440×152 (та же картинка в эталоне на TS)."""
    w, h = 440, 152
    y, x = np.mgrid[0:h, 0:w]
    r, g, b = x * 255 // (w - 1), y * 255 // (h - 1), (x * 7 + y * 13) % 256
    for mask, color in (
        ((x - 120) ** 2 + (y - 76) ** 2 < 48**2, (220, 40, 40)),
        ((x >= 240) & (x < 360) & (y >= 32) & (y < 120), (30, 60, 200)),
        ((x + y) % 97 < 6, (250, 250, 250))
    ):
        r, g, b = (np.where(mask, c, ch) for c, ch in zip(color, (r, g, b)))
    data = np.stack([r, g, b, np.full_like(r, 255)], axis=-1).astype(np.uint8)
    return Rgba(w, h, data.reshape(-1))


def flat_banner() -> np.ndarray:
    img = np.full((H, W, 3), 255, dtype=np.uint8)
    img[40:200, 60:500] = (200, 30, 30)
    img[150:340, 600:1040] = (20, 90, 200)
    return img


# ΔE of the original TypeScript program (src/core) on the same picture; the port uses plain float math instead of
# JS number semantics, so strokes may differ slightly, quality must not
REFERENCE = {
    'layers': (Params(auto=False), 2.646),
    'layers_auto': (Params(), 1.563),
    'vivid128': (Params(auto=False, colors=128, min_area=1, tol=0), 1.949),
    'classic_merge': (
        Params(auto=False, palette_mode='classic', colors=64, merge=60, sharp_edges=True, smooth=1.25, min_area=24, tol=1, adjust=Adjust(0.1, -0.2, 0.3, 1.1)),
        2.389
    ),
    'level5': (Params(level=5), 2.068),
    'exact': (Params(engine='exact', auto=False, cell=2, colors=24, smooth=0, min_area=1), 4.357),
    'strokes': (Params(engine='strokes'), 1.760)
}


@needs_jit
@pytest.mark.parametrize('name', REFERENCE)
def test_engines_match_original_quality(name):
    params, dE = REFERENCE[name]
    r = Session(synthetic()).run(params)
    assert validate(r.ops) == []
    assert abs(r.quality.dE - dE) / dE < 0.05, f'ΔE {r.quality.dE:.3f}, original {dE}'


def test_level_is_a_ladder_step():
    p = Params(level=0).resolved()
    assert (p.auto, p.detail, p.level) == (False, LADDER[0], None)
    assert Params(level=len(LADDER) - 1).resolved().detail == LADDER[-1]
    assert Params().resolved() == Params()
    with pytest.raises(ValueError):
        Params(level=len(LADDER)).resolved()


@needs_jit
def test_optimize_takes_most_similar_fitting_variant():
    r = run(synthetic(), optimize=2)
    assert [v.name for v in r.variants] == ['Как задано', 'Мазки', 'Связность 40', 'Связность 70']
    best = min((v for v in r.variants if v.fits), key=lambda v: v.dE)
    assert r.quality.dE == best.dE
    assert r.params == best.params.resolved()
    assert validate(r.ops) == []


def test_optimize_level_is_checked():
    with pytest.raises(ValueError):
        Session(synthetic()).optimize(DEFAULTS, 4)


def test_validate_catches_what_the_site_rejects():
    assert validate([brush([(1, 1), (2, 2)])]) == []
    assert 'Ширина' in ''.join(validate([brush([(1, 1)], 101)]))
    assert '#rrggbb' in ''.join(validate([brush([(1, 1)], 10, '#f00')]))
    assert 'Штрихов 2001' in ''.join(validate([brush([(1, 1)]) for _ in range(2001)]))
    assert '4097' in ''.join(validate([brush([(i % 1000, 1) for i in range(4097)])]))
    assert 'Точек 64000' in ''.join(validate([brush([(i % 1000, 1) for i in range(4000)]) for _ in range(16)]))
    assert 'пустой' in ''.join(validate([]))


def test_split_long_keeps_every_segment():
    pts = [(i % 1000, i // 1000) for i in range(10000)]
    parts = split_long([brush(pts)])
    assert all(len(p.points) <= MAX_POINTS_PER_OP for p in parts)
    for a, b in zip(parts, parts[1:]):
        assert b.points[0] == a.points[-1]
    assert sum(len(p.points) for p in parts) - (len(parts) - 1) == len(pts)


def test_drawing_payload_is_like_json_stringify():
    body = drawing([brush([(100.0, 100.5)], 20.0)])
    assert body == {'version': 1, 'width': 1100, 'height': 380, 'ops': [{'tool': 'brush', 'color': '#ff0000', 'width': 20, 'points': [[100, 100.5]]}]}


def test_render_shapes():
    def px(rgb, x, y):  # green channel of red is 0 where painted
        return round(rgb[(y * W + x) * 3 + 1])

    rgb = render_ops([brush([(100, 100)], 20)], W, H)
    assert px(rgb, 100, 100) == 0 and px(rgb, 100, 115) == 255
    rgb = render_ops([Op('circle', '#ff0000', 10, [(300, 190), (380, 190)])], W, H)
    assert px(rgb, 380, 190) == 0 and px(rgb, 300, 190) == 255
    rgb = render_ops([Op('rectangle', '#ff0000', 10, [(100, 100), (400, 200)])], W, H)
    assert px(rgb, 250, 100) == 0 and px(rgb, 250, 150) == 255 and px(rgb, 95, 95) == 255
    rgb = render_ops([brush([(0, 190), (1100, 190)], 100), Op('eraser', '#000000', 10, [(500, 190), (600, 190)])], W, H)
    assert px(rgb, 550, 190) == 255


def test_render_matches_site_server_png():
    cases = json.loads((FIXTURES / 'server_ops.json').read_text())
    for name, ops in cases.items():
        server = np.frombuffer(gzip.decompress((FIXTURES / f'server_{name}.rgb.gz').read_bytes()), dtype=np.uint8).astype(np.float64).reshape(-1, 3)
        ours = render_ops([Op.from_dict(o) for o in ops], W, H).reshape(-1, 3)
        d = np.abs(ours - server).max(axis=1)
        ink = (d > 0) | (server < 255).any(axis=1)
        assert d[ink].sum() / ink.sum() < 8, name
        assert (d > 96).sum() / ink.sum() < 0.01, name


def test_merge_small_keeps_contrasting_dot():
    label = np.zeros(25, dtype=np.int64)
    label[12], label[0] = 1, 2
    merge_small(5, 5, label, 3, 4, np.array([0.5, 0, 0, 0, 0, 0, 0.505, 0, 0]), True)
    assert label[12] == 1  # black dot on grey stays
    assert label[0] == 0  # almost the same grey goes away


def test_oklab_roundtrip():
    for c in ((0, 0, 0), (255, 255, 255), (255, 0, 0), (12, 200, 90), (70, 30, 240)):
        back = from_oklab(*oklab(*c))
        assert all(abs(a - b) < 1 for a, b in zip(back, c))
    assert all(0 <= v <= 255 for v in from_oklab(0.6, 0.5, 0.5))


@pytest.fixture
def site(monkeypatch):
    """Подменить сайт: загрузка рисунка отвечает id и адресом, остальное - пустым ответом"""
    calls = []
    reply = {'status': 200, 'body': None}

    def fake_fetch(client, method, url, params={}, files={}, sse=False):
        calls.append({'method': method, 'url': url, 'params': params})
        if url == 'files/banner-drawing':
            return make_response(reply['status'], reply['body'] or {'id': str(uuid4()), 'url': 'https://cdn.xn--d1ah4a.com/b.png'})
        return make_response(200, {})

    monkeypatch.setattr('itd.core.client.fetch', fake_fetch)
    return calls, reply


def test_banner_drawing_uploads_ops(site):
    calls, _ = site
    client = make_client(make_token(900))
    banner = BannerDrawing([brush([(10, 10), (200, 10)])], client)
    assert calls == [{'method': 'post', 'url': 'files/banner-drawing', 'params': drawing([brush([(10, 10), (200, 10)])])}]
    assert banner.url == 'https://cdn.xn--d1ah4a.com/b.png'


def test_banner_drawing_is_checked_before_upload(site):
    calls, _ = site
    with pytest.raises(ValueError, match='Ширина'):
        BannerDrawing([brush([(1, 1)], 150)], make_client(make_token(900)))
    assert calls == []


def test_too_complex_drawing_error(site):
    _, reply = site
    reply.update(status=413, body={'error': {'code': 'BANNER_DRAWING_TOO_COMPLEX', 'message': 'too complex'}})
    with pytest.raises(BannerDrawingTooComplexError):
        BannerDrawing([brush([(1, 1)])], make_client(make_token(900)))


def test_me_update_removes_banner(site):
    calls, _ = site
    Me(make_client(make_token(900))).update(banner=UNSET)
    assert calls[-1] == {'method': 'put', 'url': 'users/me', 'params': {'bannerId': None}}


def test_me_update_sets_banner_by_id(site):
    calls, _ = site
    id = uuid4()
    Me(make_client(make_token(900))).update(banner=str(id))
    assert calls[-1] == {'method': 'put', 'url': 'users/me', 'params': {'bannerId': str(id)}}


@needs_jit
def test_me_update_draws_image(site):
    calls, _ = site
    banner = Me(make_client(make_token(900))).update(banner=flat_banner())
    assert isinstance(banner, BannerDrawing)
    assert [c['url'] for c in calls] == ['files/banner-drawing', 'users/me']
    assert calls[1]['params'] == {'bannerId': str(banner.id)}
    assert validate(banner.ops) == []
    assert banner.dE is not None and banner.dE < 0.5


@needs_jit
def test_me_update_banner_with_params(site, tmp_path):
    calls, _ = site
    from PIL import Image

    path = tmp_path / 'banner.png'
    Image.fromarray(flat_banner()[::2, ::2]).save(path)  # 550×190: fitted to 1100×380
    stages = []
    banner = Me(make_client(make_token(900))).update_banner(
        path, DEFAULTS, engine='exact', auto=False, cell=4, colors=4, on_progress=lambda s, f: stages.append(s)
    )
    assert calls[0]['params']['ops'] == [o.to_dict() for o in banner.ops]
    assert all(o['width'] == 4 for o in calls[0]['params']['ops'])
    assert calls[1]['params'] == {'bannerId': str(banner.id)}
    assert 'Оценка' in stages


def test_simple_mode_fits_limits():
    from itd.banner import simple

    r = simple.run(flat_banner())
    assert validate(r.ops) == [] and r.cell == simple.CELLS[0]
    rgb = render_ops(r.ops, W, H).reshape(H, W, 3)
    assert np.abs(rgb[100, 200] - (200, 30, 30)).max() < 2  # red block
    assert np.abs(rgb[300, 100] - 255).max() < 2  # white canvas


def test_simple_mode_reads_png_without_pillow(tmp_path):
    from itd.banner.simple import _read_png

    # 3x2 RGBA PNG: red, half transparent green, blue / white, black, grey; rows use filters None and Sub
    rows = [bytes([255, 0, 0, 255, 0, 255, 0, 128, 0, 0, 255, 255]), bytes([255, 255, 255, 255, 0, 0, 0, 255, 128, 128, 128, 255])]
    sub = bytes(rows[1][:4]) + bytes((rows[1][i] - rows[1][i - 4]) & 255 for i in range(4, 12))
    raw = b'\x00' + rows[0] + b'\x01' + sub

    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data))

    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 3, 2, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
    img = _read_png(png)
    assert (img.width, img.height) == (3, 2)
    assert list(img.rgb) == [255, 0, 0, 127, 255, 127, 0, 0, 255, 255, 255, 255, 0, 0, 0, 128, 128, 128]


def test_banner_without_extra_dependencies(tmp_path):
    """Без numpy, numba и Pillow картинка рисуется простым режимом с предупреждением"""
    path = tmp_path / 'banner.png'
    from PIL import Image

    Image.fromarray(flat_banner()).save(path)
    code = f"""
import sys, warnings
for m in ('numpy', 'numba', 'PIL'):
    sys.modules[m] = None
sys.path.insert(0, {str(Path(__file__).parent)!r})
from uuid import uuid4
from helpers import make_client, make_response, make_token  # noqa: E402
import itd.core.client as c  # noqa: E402
calls = []
c.fetch = lambda client, method, url, params={{}}, files={{}}, sse=False: (calls.append(url), make_response(200, {{'id': str(uuid4()), 'url': 'u'}}))[1]
from itd import Me  # noqa: E402
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter('always')
    banner = Me(make_client(make_token(900))).update(banner={str(path)!r})
assert calls == ['files/banner-drawing', 'users/me'], calls
assert any('simple mode' in str(x.message) for x in w)
assert banner.dE is None and len(banner.ops) > 2
print('ok')
"""
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
    assert out.stdout.strip() == 'ok', out.stderr
