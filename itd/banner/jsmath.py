"""JS number semantics used by the drawing kernels.

V8 computes Math.cbrt, ** and Math.sin/cos with fdlibm, not with the platform libm that Python uses: about one result in ten
differs in the last bit, and the greedy engines amplify that into different strokes. These are ports of V8's fdlibm code
(src/base/ieee754.cc) so the Python version reproduces the original bit for bit.
"""

import math

import numpy as np

from itd.banner.jit import jit

_TWO52 = 1 << 52
_MANT = _TWO52 - 1


@jit
def f32(x):
    """Value as stored into a Float32Array."""
    return np.float64(np.float32(x))


@jit
def u8c(x):
    """Value as stored into a Uint8ClampedArray: clamp, round half to even."""
    if not x > 0:  # also NaN
        return 0
    if x >= 255:
        return 255
    return int(np.rint(x))


@jit
def js_round(x):
    """Math.round: half up."""
    r = math.ceil(x)
    if r - 0.5 > x:
        r -= 1
    return float(r)


@jit
def hypot2(a, b):
    """Math.hypot of two numbers, as V8 computes it (normalized Kahan sum)."""
    a = abs(a)
    b = abs(b)
    m = a if a > b else b
    if m == 0:
        return 0.0
    s = 0.0
    c = 0.0
    n = a / m
    t = n * n - c
    p = s + t
    c = (p - s) - t
    s = p
    n = b / m
    t = n * n - c
    p = s + t
    s = p
    return math.sqrt(s) * m


@jit
def hypot3(a, b, d):
    """Math.hypot of three numbers, as V8 computes it."""
    a = abs(a)
    b = abs(b)
    d = abs(d)
    m = a
    if b > m:
        m = b
    if d > m:
        m = d
    if m == 0:
        return 0.0
    s = 0.0
    c = 0.0
    n = a / m
    t = n * n - c
    p = s + t
    c = (p - s) - t
    s = p
    n = b / m
    t = n * n - c
    p = s + t
    c = (p - s) - t
    s = p
    n = d / m
    t = n * n - c
    p = s + t
    s = p
    return math.sqrt(s) * m


# IEEE 754 words of a double through frexp/ldexp (numba has no scalar bit casts); only finite values are needed


@jit
def _pattern(x):
    """Bits of |x| without the sign."""
    ax = abs(x)
    if ax == 0:
        return 0
    m, e = math.frexp(ax)
    if e >= -1021:
        return ((e + 1022) << 52) | (int(m * 9007199254740992.0) - _TWO52)
    return int(math.ldexp(ax, 1074))


@jit
def _from_pattern(p, neg):
    e = p >> 52
    frac = p & _MANT
    if e == 0:
        v = math.ldexp(float(frac), -1074)
    else:
        v = math.ldexp(float(frac + _TWO52), int(e) - 1075)
    return -v if neg else v


@jit
def _hi(x):
    """High word as int32 (with sign)."""
    h = _pattern(x) >> 32
    if x < 0 or (x == 0 and math.copysign(1.0, x) < 0):
        h -= 0x80000000
    return h


@jit
def _lo(x):
    return _pattern(x) & 0xFFFFFFFF


@jit
def _words(hi, lo):
    """INSERT_WORDS: double from a signed high word and an unsigned low word."""
    neg = hi < 0
    if neg:
        hi += 0x80000000
    return _from_pattern((hi << 32) | lo, neg)


@jit
def _clear_lo(x):
    """SET_LOW_WORD(x, 0)."""
    return _from_pattern(_pattern(x) & ~0xFFFFFFFF, x < 0)


@jit
def _set_hi(x, hi):
    """SET_HIGH_WORD(x, hi)."""
    return _words(hi, _lo(x))


@jit
def cbrt(x):
    """Math.cbrt."""
    B1 = 715094163
    B2 = 696219795
    P0 = 1.87595182427177009643
    P1 = -1.88497979543377169875
    P2 = 1.621429720105354466140
    P3 = -0.758397934778766047437
    P4 = 0.145996192886612446982
    if x != x or x == math.inf or x == -math.inf or x == 0:
        return x + x if x != 0 else x
    neg = x < 0
    hx = _pattern(x) >> 32
    sign = -0x80000000 if neg else 0
    if hx < 0x00100000:
        t = math.ldexp(1.0, 54) * x
        high = _pattern(t) >> 32
        t = _words(sign + (high // 3 + B2), 0)
    else:
        t = _words(sign + (hx // 3 + B1), 0)
    r = (t * t) * (t / x)
    t = t * ((P0 + r * (P1 + r * P2)) + ((r * r) * r) * (P3 + r * P4))
    # bits = (bits + 0x80000000) & 0xffffffffc0000000
    t = _from_pattern((_pattern(t) + 0x80000000) & ~0x3FFFFFFF, neg)
    s = t * t
    r = x / s
    w = t + t
    r = (r - t) / (w + r)
    t = t + t * r
    return t


@jit
def js_pow(x, y):
    """x ** y (fdlibm e_pow.c)."""
    two53 = 9007199254740992.0
    huge = 1.0e300
    tiny = 1.0e-300
    L1 = 5.99999999999994648725e-01
    L2 = 4.28571428578550184252e-01
    L3 = 3.33333329818377432918e-01
    L4 = 2.72728123808534006489e-01
    L5 = 2.30660745775561754067e-01
    L6 = 2.06975017800338417784e-01
    P1 = 1.66666666666666019037e-01
    P2 = -2.77777777770155933842e-03
    P3 = 6.61375632143793436117e-05
    P4 = -1.65339022054652515390e-06
    P5 = 4.13813679705723846039e-08
    lg2 = 6.93147180559945286227e-01
    lg2_h = 6.93147182464599609375e-01
    lg2_l = -1.90465429995776804525e-09
    ovt = 8.0085662595372944372e-17
    cp = 9.61796693925975554329e-01
    cp_h = 9.61796700954437255859e-01
    cp_l = -7.02846165095275826516e-09
    ivln2 = 1.44269504088896338700e00
    ivln2_h = 1.44269502162933349609e00
    ivln2_l = 1.92596299112661746887e-08

    if y != y or x != x:
        return math.nan
    if (y == math.inf or y == -math.inf) and (x == 1 or x == -1):
        return math.nan

    hx = _hi(x)
    lx = _lo(x)
    hy = _hi(y)
    ly = _lo(y)
    ix = hx & 0x7FFFFFFF
    iy = hy & 0x7FFFFFFF

    if (iy | ly) == 0:
        return 1.0

    yisint = 0
    if hx < 0:
        if iy >= 0x43400000:
            yisint = 2
        elif iy >= 0x3FF00000:
            k = (iy >> 20) - 0x3FF
            if k > 20:
                j = ly >> (52 - k)
                if (j << (52 - k)) == ly:
                    yisint = 2 - (j & 1)
            elif ly == 0:
                j = iy >> (20 - k)
                if (j << (20 - k)) == iy:
                    yisint = 2 - (j & 1)

    if ly == 0:
        if iy == 0x7FF00000:
            if ((ix - 0x3FF00000) | lx) == 0:
                return y - y
            elif ix >= 0x3FF00000:
                return y if hy >= 0 else 0.0
            else:
                return -y if hy < 0 else 0.0
        if iy == 0x3FF00000:
            if hy < 0:
                return 1.0 / x
            return x
        if hy == 0x40000000:
            return x * x
        if hy == 0x3FE00000:
            if hx >= 0:
                return math.sqrt(x)

    ax = abs(x)
    if lx == 0:
        if ix == 0x7FF00000 or ix == 0 or ix == 0x3FF00000:
            z = ax
            if hy < 0:
                z = 1.0 / z
            if hx < 0:
                if ((ix - 0x3FF00000) | yisint) == 0:
                    z = math.nan
                elif yisint == 1:
                    z = -z
            return z

    n = 0 if hx < 0 else 1
    if (n | yisint) == 0:
        return math.nan

    s = 1.0
    if (n | (yisint - 1)) == 0:
        s = -1.0

    if iy > 0x41E00000:
        if iy > 0x43F00000:
            if ix <= 0x3FEFFFFF:
                return huge * huge if hy < 0 else tiny * tiny
            if ix >= 0x3FF00000:
                return huge * huge if hy > 0 else tiny * tiny
        if ix < 0x3FEFFFFF:
            return s * huge * huge if hy < 0 else s * tiny * tiny
        if ix > 0x3FF00000:
            return s * huge * huge if hy > 0 else s * tiny * tiny
        t = ax - 1.0
        w = (t * t) * (0.5 - t * (0.3333333333333333333333 - t * 0.25))
        u = ivln2_h * t
        v = t * ivln2_l - w * ivln2
        t1 = _clear_lo(u + v)
        t2 = v - (t1 - u)
    else:
        n = 0
        if ix < 0x00100000:
            ax *= two53
            n -= 53
            ix = _hi(ax)
        n += (ix >> 20) - 0x3FF
        j = ix & 0x000FFFFF
        ix = j | 0x3FF00000
        if j <= 0x3988E:
            k = 0
        elif j < 0xBB67A:
            k = 1
        else:
            k = 0
            n += 1
            ix -= 0x00100000
        ax = _set_hi(ax, ix)
        bp = 1.5 if k else 1.0
        dp_h = 5.84962487220764160156e-01 if k else 0.0
        dp_l = 1.35003920212974897128e-08 if k else 0.0

        u = ax - bp
        v = 1.0 / (ax + bp)
        ss = u * v
        s_h = _clear_lo(ss)
        t_h = _words(((ix >> 1) | 0x20000000) + 0x00080000 + (k << 18), 0)
        t_l = ax - (t_h - bp)
        s_l = v * ((u - s_h * t_h) - s_h * t_l)
        s2 = ss * ss
        r = s2 * s2 * (L1 + s2 * (L2 + s2 * (L3 + s2 * (L4 + s2 * (L5 + s2 * L6)))))
        r += s_l * (s_h + ss)
        s2 = s_h * s_h
        t_h = _clear_lo(3.0 + s2 + r)
        t_l = r - ((t_h - 3.0) - s2)
        u = s_h * t_h
        v = s_l * t_h + t_l * ss
        p_h = _clear_lo(u + v)
        p_l = v - (p_h - u)
        z_h = cp_h * p_h
        z_l = cp_l * p_h + p_l * cp + dp_l
        t = float(n)
        t1 = _clear_lo(((z_h + z_l) + dp_h) + t)
        t2 = z_l - (((t1 - t) - dp_h) - z_h)

    y1 = _clear_lo(y)
    p_l = (y - y1) * t1 + y * t2
    p_h = y1 * t1
    z = p_l + p_h
    j = _hi(z)
    i = _lo(z)
    if j >= 0x40900000:
        if ((j - 0x40900000) | i) != 0:
            return s * huge * huge
        if p_l + ovt > z - p_h:
            return s * huge * huge
    elif (j & 0x7FFFFFFF) >= 0x4090CC00:
        if ((j - (0xC090CC00 - 0x100000000)) | i) != 0:
            return s * tiny * tiny
        if p_l <= z - p_h:
            return s * tiny * tiny

    i = j & 0x7FFFFFFF
    k = (i >> 20) - 0x3FF
    n = 0
    if i > 0x3FE00000:
        n = j + (0x00100000 >> (k + 1))
        k = ((n & 0x7FFFFFFF) >> 20) - 0x3FF
        t = _words(n & ~(0x000FFFFF >> k), 0)
        n = ((n & 0x000FFFFF) | 0x00100000) >> (20 - k)
        if j < 0:
            n = -n
        p_h -= t
    t = _clear_lo(p_l + p_h)
    u = t * lg2_h
    v = (p_l - (t - p_h)) * lg2 + t * lg2_l
    z = u + v
    w = v - (z - u)
    t = z * z
    t1 = z - t * (P1 + t * (P2 + t * (P3 + t * (P4 + t * P5))))
    r = (z * t1) / ((t1 - 2.0) - (w + z * w))
    z = 1.0 - (r - z)
    j = _hi(z)
    j += n << 20
    if (j >> 20) <= 0:
        z = math.ldexp(z, n)
    else:
        z = _set_hi(z, _hi(z) + (n << 20))
    return s * z


@jit
def _ksin(x, y, iy):
    S1 = -1.66666666666666324348e-01
    S2 = 8.33333333332248946124e-03
    S3 = -1.98412698298579493134e-04
    S4 = 2.75573137070700676789e-06
    S5 = -2.50507602534068634195e-08
    S6 = 1.58969099521155010221e-10
    ix = _hi(x) & 0x7FFFFFFF
    if ix < 0x3E400000:
        if int(x) == 0:
            return x
    z = x * x
    v = z * x
    r = S2 + z * (S3 + z * (S4 + z * (S5 + z * S6)))
    if iy == 0:
        return x + v * (S1 + z * r)
    return x - ((z * (0.5 * y - v * r) - y) - v * S1)


@jit
def _kcos(x, y):
    C1 = 4.16666666666666019037e-02
    C2 = -1.38888888888741095749e-03
    C3 = 2.48015872894767294178e-05
    C4 = -2.75573143513906633035e-07
    C5 = 2.08757232129817482790e-09
    C6 = -1.13596475577881948265e-11
    ix = _hi(x) & 0x7FFFFFFF
    if ix < 0x3E400000:
        if int(x) == 0:
            return 1.0
    z = x * x
    r = z * (C1 + z * (C2 + z * (C3 + z * (C4 + z * (C5 + z * C6)))))
    if ix < 0x3FD33333:
        return 1.0 - (0.5 * z - (z * r - x * y))
    if ix > 0x3FE90000:
        qx = 0.28125
    else:
        qx = _words(ix - 0x00200000, 0)
    iz = 0.5 * z - qx
    a = 1.0 - qx
    return a - (iz - (z * r - x * y))


# high words of n*pi/2, n = 1..32
_NPIO2_HW = np.array(
    [
        0x3FF921FB, 0x400921FB, 0x4012D97C, 0x401921FB, 0x401F6A7A, 0x4022D97C, 0x4025FDBB, 0x402921FB,
        0x402C463A, 0x402F6A7A, 0x4031475C, 0x4032D97C, 0x40346B9C, 0x4035FDBB, 0x40378FDB, 0x403921FB,
        0x403AB41B, 0x403C463A, 0x403DD85A, 0x403F6A7A, 0x40407E4C, 0x4041475C, 0x4042106C, 0x4042D97C,
        0x4043A28C, 0x40446B9C, 0x404534AC, 0x4045FDBB, 0x4046C6CB, 0x40478FDB, 0x404858EB, 0x404921FB
    ],
    dtype=np.int64
)  # fmt: skip


@jit
def _rem_pio2(x):
    """Argument reduction for |x| < 2^19*pi/2: (n, y0, y1)."""
    invpio2 = 6.36619772367581382433e-01
    pio2_1 = 1.57079632673412561417e00
    pio2_1t = 6.07710050650619224932e-11
    pio2_2 = 6.07710050630396597660e-11
    pio2_2t = 2.02226624879595063154e-21
    pio2_3 = 2.02226624871116645580e-21
    pio2_3t = 8.47842766036889956997e-32
    hx = _hi(x)
    ix = hx & 0x7FFFFFFF
    if ix <= 0x3FE921FB:
        return 0, x, 0.0
    if ix < 0x4002D97C:
        if hx > 0:
            z = x - pio2_1
            if ix != 0x3FF921FB:
                y0 = z - pio2_1t
                y1 = (z - y0) - pio2_1t
            else:
                z -= pio2_2
                y0 = z - pio2_2t
                y1 = (z - y0) - pio2_2t
            return 1, y0, y1
        z = x + pio2_1
        if ix != 0x3FF921FB:
            y0 = z + pio2_1t
            y1 = (z - y0) + pio2_1t
        else:
            z += pio2_2
            y0 = z + pio2_2t
            y1 = (z - y0) + pio2_2t
        return -1, y0, y1
    # medium size; the engines never pass anything larger
    t = abs(x)
    n = int(t * invpio2 + 0.5)
    fn = float(n)
    r = t - fn * pio2_1
    w = fn * pio2_1t
    if n < 32 and ix != _NPIO2_HW[n - 1]:
        y0 = r - w
    else:
        j = ix >> 20
        y0 = r - w
        i = j - ((_hi(y0) >> 20) & 0x7FF)
        if i > 16:
            t = r
            w = fn * pio2_2
            r = t - w
            w = fn * pio2_2t - ((t - r) - w)
            y0 = r - w
            i = j - ((_hi(y0) >> 20) & 0x7FF)
            if i > 49:
                t = r
                w = fn * pio2_3
                r = t - w
                w = fn * pio2_3t - ((t - r) - w)
                y0 = r - w
    y1 = (r - y0) - w
    if hx < 0:
        return -n, -y0, -y1
    return n, y0, y1


@jit
def js_sin(x):
    """Math.sin."""
    if (_hi(x) & 0x7FFFFFFF) <= 0x3FE921FB:
        return _ksin(x, 0.0, 0)
    n, y0, y1 = _rem_pio2(x)
    q = n & 3
    if q == 0:
        return _ksin(y0, y1, 1)
    if q == 1:
        return _kcos(y0, y1)
    if q == 2:
        return -_ksin(y0, y1, 1)
    return -_kcos(y0, y1)


@jit
def js_cos(x):
    """Math.cos."""
    if (_hi(x) & 0x7FFFFFFF) <= 0x3FE921FB:
        return _kcos(x, 0.0)
    n, y0, y1 = _rem_pio2(x)
    q = n & 3
    if q == 0:
        return _kcos(y0, y1)
    if q == 1:
        return -_ksin(y0, y1, 1)
    if q == 2:
        return -_kcos(y0, y1)
    return _ksin(y0, y1, 1)
