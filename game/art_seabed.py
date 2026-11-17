import math
import random
import pygame
from .canvas import Px, mix, shade

CW = 320
CH = 160
K = 4
FOG = (8, 26, 62)
CORAL_COLS = [(236, 96, 150), (250, 150, 80), (176, 108, 232), (60, 204, 190), (244, 210, 80), (228, 70, 82), (132, 214, 110), (96, 150, 250)]


def _noise(seed, base, comps):
    """Membuat fungsi tinggi permukaan dari jumlah gelombang sinus acak sehingga kontur tanah naik turun tidak beraturan."""
    rs = random.Random(seed)
    parts = [(rs.uniform(0, 6.283), f * rs.uniform(0.85, 1.15), a) for f, a in comps]

    def h(x):
        return base + sum(a * math.sin(x * f + p) for p, f, a in parts)

    return h


def _gauss(x, c, w, a):
    return a * math.exp(-(((x - c) / w) ** 2))


def _far_fn():
    """Membuat kontur punggung bukit terjauh dengan menara batu yang menjulang."""
    base = _noise(3, 76, [(0.021, 12), (0.055, 6), (0.14, 2.5)])
    spires = [(30, 17, 36), (88, 12, 50), (150, 22, 42), (214, 15, 32), (266, 19, 46), (308, 11, 56)]

    def h(x):
        y = base(x)
        for sx, hw, top in spires:
            d = abs(x - sx)
            if d < hw:
                y = min(y, top + (d / hw) ** 1.3 * (base(x) - top))
        return y

    return h


def _mid_fn():
    """Membuat kontur punggung bukit tengah dengan bukit kecil dan cekungan."""
    base = _noise(7, 110, [(0.024, 10), (0.075, 5), (0.19, 2)])
    return lambda x: base(x) + _gauss(x, 70, 26, -11) + _gauss(x, 188, 30, -9) + _gauss(x, 262, 22, 8) + _gauss(x, 130, 20, 6)


def _near_fn():
    """Membuat kontur pasir terdekat dengan bukit landai cekungan dan permukaan bergelombang."""
    base = _noise(13, 140, [(0.017, 8), (0.049, 4.5), (0.12, 2)])
    return lambda x: base(x) + _gauss(x, 246, 30, -12) + _gauss(x, 62, 24, 7) + _gauss(x, 298, 16, -6) + _gauss(x, 150, 34, -5)


def _tones(col, dim=0.0):
    g = sum(col) // 3
    col = mix(col, (g, g, g), dim * 0.55)
    col = mix(col, FOG, dim * 0.6)
    return shade(col, -0.5), shade(col, -0.22), col, shade(col, 0.38)


def _fill_ground(c, fn, top, mid, bot, depth):
    for x in range(CW):
        y0 = max(0, int(fn(x)))
        slope = fn(x + 2) - fn(x - 2)
        f = max(-0.3, min(0.4, -slope * 0.1))
        for y in range(y0, CH):
            d = y - y0
            if d < depth:
                col = mix(top, mid, d / depth)
            else:
                col = mix(mid, bot, min(1.0, (d - depth) / max(1, CH - y0 - depth)))
            if d < 4:
                col = shade(col, f * (1 - d / 4.0))
            c.surf.set_at((x, y), col)


def _ripples(c, fn, rs, count, amt):
    for _ in range(count):
        x0 = rs.uniform(0, CW - 20)
        off = rs.uniform(5, 38)
        ln = rs.uniform(8, 26)
        ph = rs.uniform(0, 6)
        for i in range(int(ln)):
            x = int(x0 + i)
            y = int(fn(x) + off + math.sin(i * 0.5 + ph) * 1.2)
            if 0 <= x < CW and 0 <= y < CH - 1:
                a = c.surf.get_at((x, y))
                if a[3] == 0:
                    continue
                c.surf.set_at((x, y), shade(a[:3], amt))
                b = c.surf.get_at((x, y + 1))
                if b[3]:
                    c.surf.set_at((x, y + 1), shade(b[:3], -amt * 0.9))


def _speckle(c, fn, rs, n, amt):
    for _ in range(n):
        x = rs.randrange(CW)
        y = int(fn(x)) + rs.randrange(2, 70)
        if 0 <= y < CH:
            a = c.surf.get_at((x, y))
            if a[3]:
                c.surf.set_at((x, y), shade(a[:3], amt * rs.choice((-1, 1)) * rs.uniform(0.4, 1.0)))


def _rock(c, x, y, w, h, col, rs, dim=0.0):
    deep, dark, base, light = _tones(col, dim)
    n = 8
    pts = []
    for i in range(n + 1):
        a = math.pi * i / n
        r = rs.uniform(0.84, 1.08)
        pts.append((x + math.cos(a) * w / 2 * r, y - math.sin(a) * h * r))
    body = pts + [(x - w / 2, y + 1), (x + w / 2, y + 1)]
    c.poly(body, dark)
    lit = pts[n // 2 - 1:] + [(x - w / 2 + 1, y + 1), (x - w * 0.12, y + 1)]
    c.poly(lit, base)
    top = pts[n // 2 + 1:]
    if len(top) > 1 and dim < 0.7:
        c.line(top[0][0], top[0][1], top[-1][0], top[-1][1], light)
    sh = pts[:n // 3 + 1] + [(x + w / 2, y + 1), (x + w * 0.15, y + 1)]
    c.poly(sh, deep)
    if dim < 0.6 and w > 8:
        cx = x - w * 0.1
        c.line(cx, y - h * 0.8, cx + rs.uniform(-2, 2), y - h * 0.3, deep)
        c.px(x - w * 0.25, y - h * 0.5, light)


def _shell(c, x, y, col):
    deep, dark, base, light = _tones(col, 0.0)
    c.poly([(x - 2, y), (x - 3, y - 2), (x - 1, y - 3), (x + 1, y - 3), (x + 3, y - 2), (x + 2, y)], base)
    c.line(x, y, x - 2, y - 2, dark)
    c.line(x, y, x, y - 3, dark)
    c.line(x, y, x + 2, y - 2, dark)
    c.px(x - 1, y - 3, light)


def _star(c, x, y, r, col):
    deep, dark, base, light = _tones(col, 0.0)
    for i in range(5):
        a = -math.pi / 2 + i * math.tau / 5
        c.line(x, y, x + math.cos(a) * r, y + math.sin(a) * r, dark, 2)
    for i in range(5):
        a = -math.pi / 2 + i * math.tau / 5
        c.line(x, y, x + math.cos(a) * r, y + math.sin(a) * r, base)
    c.px(x, y, light)


def _urchin(c, x, y):
    for i in range(10):
        a = math.pi + i * math.pi / 9
        c.line(x, y, x + math.cos(a) * 4, y + math.sin(a) * 4, (70, 40, 96))
    c.ellipse(x - 2, y - 2, 5, 4, (110, 70, 150))
    c.px(x - 1, y - 1, (180, 140, 220))


def _pebbles(c, x, y, rs):
    for _ in range(rs.randrange(2, 5)):
        px = x + rs.randrange(-6, 7)
        w = rs.choice((2, 3, 3, 4))
        c.ellipse(px, y - 1, w, 2, (66, 80, 100))
        c.px(px, y - 1, (120, 138, 160))


def _branch(c, x, y, h, col, rs, dim=0.0):
    deep, dark, base, light = _tones(col, dim)
    stack = [(x, y, -math.pi / 2 + rs.uniform(-0.25, 0.25), h * 0.4, 3, 0)]
    segs = []
    while stack:
        px, py, a, ln, w, d = stack.pop()
        nx, ny = px + math.cos(a) * ln, py + math.sin(a) * ln
        segs.append((px, py, nx, ny, w, d, d >= 3 or ln <= 3))
        if d < 3 and ln > 3:
            for da in (-rs.uniform(0.4, 0.85), rs.uniform(0.4, 0.85)):
                if d == 0 or rs.random() < 0.82:
                    stack.append((nx, ny, a + da, ln * rs.uniform(0.62, 0.82), max(1, w - 1), d + 1))
            if rs.random() < 0.45:
                stack.append((nx, ny, a + rs.uniform(-0.2, 0.2), ln * 0.7, max(1, w - 1), d + 1))
    for px, py, nx, ny, w, d, leaf in segs:
        c.line(px, py, nx, ny, deep, w + 1)
    for px, py, nx, ny, w, d, leaf in segs:
        c.line(px, py, nx, ny, base, w)
    if dim < 0.75:
        for px, py, nx, ny, w, d, leaf in segs:
            if w >= 2:
                c.line(px - 1, py, nx - 1, ny, light)
            if leaf:
                c.px(nx, ny, light)
                c.px(nx, ny - 1, light)


def _dome(c, x, y, w, h, col, rs, dim=0.0):
    deep, dark, base, light = _tones(col, dim)

    def arc(k, off=(0, 0), ww=1.0):
        return [(x + math.cos(math.pi * i / 14) * w / 2 * k * ww + off[0], y - math.sin(math.pi * i / 14) * h * k + off[1]) for i in range(15)]

    c.poly(arc(1.0) + [(x - w / 2, y + 1)], deep)
    c.poly(arc(0.94, (0, 0)), dark)
    c.poly(arc(0.82, (-1, -1)), base)
    c.poly(arc(0.5, (-w * 0.1, -h * 0.18)), light if dim < 0.7 else base)
    if dim < 0.75:
        for k in (0.9, 0.7):
            pts = arc(k, (-1, -1))
            for i in range(0, len(pts) - 1, 2):
                if (i * 7 + int(w)) % 5:
                    c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], dark)
        for _ in range(int(w // 3)):
            c.px(x + rs.uniform(-w * 0.3, w * 0.3), y - rs.uniform(h * 0.2, h * 0.8), deep)


def _fan(c, x, y, h, col, rs, dim=0.0):
    deep, dark, base, light = _tones(col, dim)
    cy = y - h * 0.16
    c.line(x, y, x, cy, deep, 2)
    n = 13
    span = 1.05
    for ring in (0.45, 0.7, 0.95):
        pts = [(x + math.cos(-math.pi / 2 + (i / n * 2 - 1) * span) * h * ring, cy + math.sin(-math.pi / 2 + (i / n * 2 - 1) * span) * h * ring) for i in range(n + 1)]
        pygame.draw.lines(c.surf, dark, False, pts, 1)
    for i in range(n + 1):
        a = -math.pi / 2 + (i / n * 2 - 1) * span
        ex, ey = x + math.cos(a) * h, cy + math.sin(a) * h
        c.line(x, cy, ex, ey, deep, 2)
    for i in range(n + 1):
        a = -math.pi / 2 + (i / n * 2 - 1) * span
        ex, ey = x + math.cos(a) * h, cy + math.sin(a) * h
        c.line(x, cy, ex, ey, base)
        if i % 2 == 0 and dim < 0.75:
            c.px(ex, ey, light)
            c.px(x + math.cos(a) * h * 0.7, cy + math.sin(a) * h * 0.7, light)


def _tubes(c, x, y, h, col, rs, dim=0.0):
    deep, dark, base, light = _tones(col, dim)
    n = rs.randrange(3, 6)
    items = []
    for i in range(n):
        tw = rs.choice((3, 4, 4, 5))
        th = h * rs.uniform(0.45, 1.0)
        items.append((x + (i - n / 2) * 4 + rs.uniform(-1, 1), th, tw))
    items.sort(key=lambda t: -t[1])
    for tx, th, tw in items:
        c.rect(tx, y - th, tw, th + 1, base)
        c.rect(tx, y - th, 1, th + 1, light if dim < 0.7 else base)
        c.rect(tx + tw - 1, y - th, 1, th + 1, dark)
        c.ellipse(tx, y - th - 1, tw, 3, light if dim < 0.7 else base)
        c.ellipse(tx + 1, y - th, max(1, tw - 2), 2, deep)
        c.rect(tx, y - 1, tw, 2, deep)


def _table(c, x, y, w, h, col, rs, dim=0.0):
    deep, dark, base, light = _tones(col, dim)
    top = y - h
    c.rect(x - 1, top + 2, 3, h - 1, deep)
    c.rect(x - 1, top + 2, 1, h - 1, dark)
    c.poly([(x - w / 2, top + 1), (x + w / 2, top + 1), (x + w * 0.3, top + 5), (x - w * 0.3, top + 5)], dark)
    c.ellipse(x - w / 2, top - 2, w, 6, base)
    c.ellipse(x - w / 2 + 2, top - 2, w - 6, 3, light if dim < 0.7 else base)
    c.line(x - w / 2 + 1, top + 1, x + w / 2 - 1, top + 1, dark)
    for i in range(int(w // 4)):
        c.px(x - w / 2 + 3 + i * 4, top, deep)


def _anemone(c, x, y, r, col, rs, dim=0.0):
    deep, dark, base, light = _tones(col, dim)
    c.ellipse(x - r * 0.55, y - r * 0.5, r * 1.1, r * 0.7, deep)
    n = int(r * 1.6)
    for i in range(n):
        a = -math.pi / 2 + (i / max(1, n - 1) * 2 - 1) * 1.15
        ln = r * rs.uniform(0.8, 1.3)
        ex, ey = x + math.cos(a) * ln, y - r * 0.3 + math.sin(a) * ln
        c.line(x + (i - n / 2) * 0.5, y - r * 0.3, ex, ey, base)
        if dim < 0.75:
            c.px(ex, ey, light)
            c.px(ex, ey - 1, light)


def _vase(c, x, y, w, h, col, rs, dim=0.0):
    deep, dark, base, light = _tones(col, dim)
    pts = [(x - w * 0.3, y), (x - w * 0.5, y - h * 0.7), (x - w * 0.42, y - h), (x + w * 0.42, y - h), (x + w * 0.5, y - h * 0.7), (x + w * 0.3, y)]
    c.poly(pts, dark)
    c.poly([(x - w * 0.25, y), (x - w * 0.42, y - h * 0.7), (x - w * 0.36, y - h), (x - w * 0.05, y - h), (x - w * 0.05, y)], base)
    c.ellipse(x - w * 0.42, y - h - 1, w * 0.84, 4, light if dim < 0.7 else base)
    c.ellipse(x - w * 0.3, y - h, w * 0.6, 2, deep)
    for i in range(int(h // 3)):
        c.px(x - w * 0.15 + (i % 3) * 2, y - 2 - i * 3, deep)


def _blobs(c, x, y, h, col, rs, dim=0.0):
    deep, dark, base, light = _tones(col, dim)
    items = []
    for _ in range(rs.randrange(5, 9)):
        r = rs.uniform(2.2, 4.4) * h / 14
        items.append((x + rs.uniform(-h * 0.45, h * 0.45), y - r - rs.uniform(0, h * 0.5), r))
    items.sort(key=lambda t: -t[1])
    for bx, by, r in items:
        c.circle(bx, by, r + 1, deep)
    for bx, by, r in items:
        c.circle(bx, by, r, base)
        if dim < 0.75:
            c.circle(bx - r * 0.3, by - r * 0.3, max(1, r * 0.5), light)
            c.px(bx - r * 0.4, by - r * 0.4, (255, 255, 255))


KINDS = ("branch", "dome", "fan", "tubes", "table", "anemone", "vase", "blobs")


def _coral(c, kind, x, y, size, col, rs, dim):
    if kind == "branch":
        _branch(c, x, y, size, col, rs, dim)
    elif kind == "dome":
        _dome(c, x, y, size * 1.15, size * 0.62, col, rs, dim)
    elif kind == "fan":
        _fan(c, x, y, size * 0.85, col, rs, dim)
    elif kind == "tubes":
        _tubes(c, x, y, size * 0.7, col, rs, dim)
    elif kind == "table":
        _table(c, x, y, size * 1.3, size * 0.6, col, rs, dim)
    elif kind == "anemone":
        _anemone(c, x, y, size * 0.45, col, rs, dim)
    elif kind == "vase":
        _vase(c, x, y, size * 0.6, size * 0.75, col, rs, dim)
    else:
        _blobs(c, x, y, size * 0.8, col, rs, dim)


def _spots(rs, x0, x1, lo, hi, skip):
    xs = []
    x = x0
    while x < x1:
        x += rs.uniform(lo, hi)
        if rs.random() > skip:
            xs.append(x)
        else:
            x += rs.uniform(16, 40)
    return xs


def _reef(c, fn, rs, dim, size_lo, size_hi, kinds, gap, skip, cols):
    for cx in _spots(rs, -6, CW + 6, gap[0], gap[1], skip):
        n = rs.randrange(2, 6)
        members = []
        main = rs.choice(cols)
        for i in range(n):
            dx = rs.uniform(-17, 17)
            k = 1.0 - abs(dx) / 30.0
            size = rs.uniform(size_lo, size_hi) * max(0.45, k)
            col = main if rs.random() < 0.6 else rs.choice(cols)
            members.append((cx + dx, size, rs.choice(kinds), col))
        members.sort(key=lambda m: (fn(m[0]), rs.random()))
        for x, size, kind, col in members:
            _coral(c, kind, x, fn(x) + rs.uniform(0.5, 2.0), size, col, rs, dim)


def _vshade(c, top, bot, y0, y1):
    for y in range(CH):
        t = max(0.0, min(1.0, (y - y0) / max(1, y1 - y0)))
        col = mix(top, bot, t)
        for x in range(CW):
            a = c.surf.get_at((x, y))
            if a[3]:
                c.surf.set_at((x, y), col)


def _rim(c, light):
    m = pygame.mask.from_surface(c.surf, 10)
    for x in range(CW):
        for y in range(1, CH):
            if m.get_at((x, y)) and not m.get_at((x, y - 1)):
                c.surf.set_at((x, y), light)
                if y + 1 < CH and m.get_at((x, y + 1)):
                    c.surf.set_at((x, y + 1), mix(light, c.surf.get_at((x, y + 1))[:3], 0.55))


def _wreck(c, x, y):
    hull = (10, 26, 54)
    c.poly([(x - 20, y - 4), (x + 22, y - 10), (x + 18, y + 2), (x - 14, y + 4)], hull)
    c.poly([(x - 20, y - 4), (x - 24, y - 12), (x - 16, y - 6)], hull)
    c.rect(x - 4, y - 18, 2, 12, hull)
    c.rect(x + 8, y - 24, 2, 16, hull)
    c.line(x - 3, y - 16, x + 9, y - 22, hull)
    c.poly([(x + 10, y - 22), (x + 17, y - 18), (x + 10, y - 12)], (14, 32, 62))
    c.px(x + 4, y - 7, (50, 90, 130))
    c.px(x + 8, y - 8, (50, 90, 130))


def _arch(c, x, y):
    col = (16, 40, 78)
    c.poly([(x - 28, y + 8), (x - 26, y - 22), (x - 16, y - 32), (x + 4, y - 34), (x + 20, y - 24), (x + 26, y + 8)], col)
    pygame.draw.ellipse(c.surf, (0, 0, 0, 0), (x - 13, y - 20, 26, 30))
    c.line(x - 26, y - 22, x - 16, y - 32, (34, 70, 116))
    c.line(x - 16, y - 32, x + 4, y - 34, (34, 70, 116))


def _build_far():
    c = Px(CW, CH)
    fn = _far_fn()
    rs = random.Random(31)
    for x in range(CW):
        y0 = max(0, int(fn(x)))
        c.rect(x, y0, 1, CH - y0, (40, 70, 110))
    _arch(c, 122, 78)
    _vshade(c, (34, 66, 112), (10, 26, 58), 30, 130)
    _rim(c, (66, 104, 154))
    _wreck(c, 238, 70)
    for cx in _spots(rs, 0, CW, 10, 30, 0.35):
        _coral(c, rs.choice(("branch", "branch", "dome", "fan", "blobs")), cx, fn(cx) + 1, rs.uniform(12, 24), rs.choice(CORAL_COLS), rs, 0.9)
    return c


def _build_mid():
    c = Px(CW, CH)
    fn = _mid_fn()
    rs = random.Random(41)
    _fill_ground(c, fn, (72, 108, 146), (28, 56, 94), (8, 20, 46), 26)
    _rim(c, (112, 150, 190))
    _ripples(c, fn, rs, 34, 0.12)
    _speckle(c, fn, rs, 900, 0.16)
    for _ in range(16):
        x = rs.uniform(4, CW - 4)
        _rock(c, x, fn(x) + 2, rs.uniform(7, 20), rs.uniform(4, 11), (70, 92, 122), rs, 0.35)
    _reef(c, fn, rs, 0.45, 12, 28, ("branch", "dome", "fan", "tubes", "table", "blobs", "vase"), (12, 28), 0.1, CORAL_COLS)
    return c, fn


def _vent(c, x, y):
    c.poly([(x - 8, y + 2), (x - 5, y - 6), (x - 2, y - 9), (x + 2, y - 9), (x + 5, y - 6), (x + 8, y + 2)], (44, 54, 78))
    c.poly([(x - 8, y + 2), (x - 5, y - 6), (x - 2, y - 9), (x - 3, y + 2)], (78, 94, 124))
    c.ellipse(x - 3, y - 10, 6, 3, (10, 14, 30))
    c.px(x - 3, y - 10, (90, 230, 210))
    c.px(x + 2, y - 10, (90, 230, 210))
    c.line(x - 5, y - 4, x - 3, y - 6, (110, 128, 160))


def _build_near(vents):
    c = Px(CW, CH)
    fn = _near_fn()
    rs = random.Random(53)
    _fill_ground(c, fn, (124, 142, 158), (70, 88, 112), (12, 22, 46), 30)
    _ripples(c, fn, rs, 46, 0.13)
    _speckle(c, fn, rs, 1400, 0.16)
    big = [rs.uniform(10, CW - 10) for _ in range(9)]
    for x in big:
        _rock(c, x, fn(x) + 3, rs.uniform(10, 30), rs.uniform(6, 17), (92, 108, 132), rs, 0.0)
    for x, _ in vents:
        _vent(c, x, fn(x) + 3)
    _reef(c, fn, rs, 0.12, 14, 34, KINDS, (16, 38), 0.2, CORAL_COLS)
    for _ in range(30):
        x = rs.uniform(4, CW - 4)
        _pebbles(c, x, fn(x) + rs.uniform(2, 14), rs)
    for _ in range(8):
        x = rs.uniform(6, CW - 6)
        _shell(c, int(x), int(fn(x) + rs.uniform(4, 22)), rs.choice(((250, 220, 200), (240, 190, 170), (220, 230, 240))))
    for _ in range(5):
        x = rs.uniform(6, CW - 6)
        _star(c, int(x), int(fn(x) + rs.uniform(5, 24)), rs.choice((4, 5, 6)), rs.choice(((250, 140, 70), (240, 96, 120), (250, 190, 80))))
    for _ in range(4):
        x = rs.uniform(6, CW - 6)
        _urchin(c, int(x), int(fn(x) + rs.uniform(6, 24)))
    return c, fn


class Seabed:
    """Dasar laut berlapis dengan punggung bukit jauh tengah dan pasir terdekat lengkap dengan karang aneka bentuk batu cangkang serta rumput laut yang berakar tepat pada tinggi tanah di tiap posisi."""

    def __init__(self, world_h, vents, seed=5):
        self.top = world_h - CH * K
        far = _build_far()
        mid, self.mid_fn = _build_mid()
        near, self.near_fn = _build_near([(v[0] / K, 0) for v in vents])
        self.far_fn = _far_fn()
        self.far = far.scaled(K).convert_alpha()
        self.mid = mid.scaled(K).convert_alpha()
        self.near = near.scaled(K).convert_alpha()
        rs = random.Random(seed)
        self.back = []
        for _ in range(9):
            x = rs.uniform(20, 1260)
            self.back.append((x, self.mid_ground(x) + 4, rs.uniform(0, 6.28), rs.uniform(90, 170), mix(rs.choice([(26, 110, 96), (30, 120, 100), (20, 96, 90)]), FOG, 0.4), rs.randrange(2, 4)))
        self.front = []
        for _ in range(13):
            x = rs.uniform(10, 1270)
            self.front.append((x, self.ground(x) + 3, rs.uniform(0, 6.28), rs.uniform(80, 190), rs.choice([(26, 140, 100), (40, 160, 110), (20, 120, 96), (50, 150, 90)]), rs.randrange(2, 4)))
        self.grass = []
        for _ in range(26):
            x = rs.uniform(10, 1270)
            self.grass.append((x, self.ground(x) + 3, rs.uniform(0, 6.28), rs.uniform(26, 58), rs.choice([(60, 170, 110), (90, 190, 120), (40, 150, 120)]), rs.randrange(3, 6)))

    def ground(self, x):
        """Mengembalikan koordinat y dunia permukaan pasir terdekat pada posisi x layar."""
        return self.top + self.near_fn(max(0, min(CW - 1, x / K))) * K

    def mid_ground(self, x):
        """Mengembalikan koordinat y dunia permukaan bukit tengah pada posisi x layar."""
        return self.top + self.mid_fn(max(0, min(CW - 1, x / K))) * K

    def blade(self, surf, x, y, ln, w, col, ph, t, amp):
        """Menggambar satu helai rumput laut meruncing yang berayun dari akar di x y layar."""
        n = 10
        pts = []
        for k in range(n + 1):
            f = k / n
            sway = math.sin(t * 1.2 + ph + f * 2.4) * amp * f
            pts.append((x + sway, y - f * ln))
        light = tuple(min(255, v + 60) for v in col)
        for k in range(n):
            f = k / n
            ww = max(2, int(w * (1 - f * 0.65)))
            pygame.draw.line(surf, mix(col, (0, 0, 0), 0.25 * (1 - f)), pts[k], pts[k + 1], ww)
            pygame.draw.circle(surf, mix(col, (0, 0, 0), 0.25 * (1 - f)), (int(pts[k + 1][0]), int(pts[k + 1][1])), ww // 2)
        pygame.draw.lines(surf, light, False, [(px - 1, py) for px, py in pts[1:]], 2)

    def plant(self, surf, item, cam, t, w, amp):
        x, ry, ph, ln, col, blades = item
        sy = ry - cam
        if sy < -40 or sy - ln > surf.get_height() + 20 or sy > surf.get_height() + 60:
            return
        for b in range(blades):
            bx = x + (b - (blades - 1) / 2) * w * 0.8
            self.blade(surf, bx, sy, ln * (0.65 + 0.35 * ((b * 5 + int(x)) % 7) / 6.0), w, col, ph + b * 0.9, t, amp)
        pygame.draw.ellipse(surf, mix(col, (0, 0, 0), 0.55), (int(x - w * 1.3), int(sy - 3), int(w * 2.6), 7))

    def draw_back(self, surf, cam, t):
        """Menggambar punggung bukit jauh dan tengah beserta rumput laut latar belakang."""
        y = self.top - cam
        if y > surf.get_height():
            return
        surf.blit(self.far, (0, y))
        surf.blit(self.mid, (0, y))
        for item in self.back:
            self.plant(surf, item, cam, t, 5, 10)

    def draw_front(self, surf, cam, t):
        """Menggambar pasir terdekat dengan karang batu dan rumput laut depan."""
        y = self.top - cam
        if y > surf.get_height():
            return
        surf.blit(self.near, (0, y))
        for item in self.grass:
            self.plant(surf, item, cam, t, 3, 6)
        for item in self.front:
            self.plant(surf, item, cam, t, 6, 16)
