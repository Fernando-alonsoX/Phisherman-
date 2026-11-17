import math
import random
import pygame
from .canvas import mix

BORDERS = [
    {"id": "b0", "name": "Classic Ring", "price": 0},
    {"id": "b1", "name": "Coral Ring", "price": 120},
    {"id": "b2", "name": "Kelp Wreath", "price": 200},
    {"id": "b3", "name": "Pearl Chain", "price": 300},
    {"id": "b4", "name": "Golden Hook", "price": 450},
    {"id": "b5", "name": "Neon Tide", "price": 650},
    {"id": "b6", "name": "Storm Halo", "price": 900},
    {"id": "b7", "name": "Leviathan Crown", "price": 1500},
]

BANNERS = [
    {"id": "n0", "name": "Plain Sky", "price": 0},
    {"id": "n1", "name": "Night Harbor", "price": 150},
    {"id": "n2", "name": "Sunset Pier", "price": 250},
    {"id": "n3", "name": "Coral Reef", "price": 350},
    {"id": "n4", "name": "Aurora Bay", "price": 500},
    {"id": "n5", "name": "Deep Storm", "price": 800},
    {"id": "n6", "name": "Golden Treasure", "price": 1200},
]

KINDS = {"border": BORDERS, "banner": BANNERS}
DEFAULTS = {"border": "b0", "banner": "n0"}
_CACHE = {}


def find(kind, cid):
    """Mencari data kosmetik menurut jenis dan kode dan mengembalikan None bila tidak ada."""
    for c in KINDS[kind]:
        if c["id"] == cid:
            return c
    return None


def valid(kind, cid):
    """Memeriksa apakah kode kosmetik dikenal untuk jenis tersebut."""
    return find(kind, cid) is not None


def now():
    """Mengambil waktu animasi dalam detik dari jam permainan."""
    return pygame.time.get_ticks() / 1000.0


def _ring(layer, c, r, w, col):
    pygame.draw.circle(layer, col, c, r, w)


def draw_border(surf, center, r, bid, t=None):
    """Menggambar bingkai hias di sekeliling lingkaran avatar berjari jari r sesuai skin yang dipakai."""
    if bid == "b0" or bid is None:
        return
    t = now() if t is None else t
    w = max(3, int(r * 0.15))
    pad = int(r * 0.6) + 8
    size = (r + pad) * 2
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    c = (size // 2, size // 2)
    ro = r + w // 2 + 1
    if bid == "b1":
        _ring(layer, c, ro, w, (255, 128, 108))
        _ring(layer, c, ro + w // 2, 1, (120, 40, 40))
        _ring(layer, c, ro - w // 2, 1, (255, 214, 196))
        for i in range(12):
            a = i / 12 * math.tau + t * 0.4
            pygame.draw.circle(layer, (255, 236, 220), (int(c[0] + math.cos(a) * ro), int(c[1] + math.sin(a) * ro)), max(2, w // 2 - 1))
    elif bid == "b2":
        _ring(layer, c, ro, w, (34, 128, 76))
        _ring(layer, c, ro - w // 2, 1, (150, 224, 160))
        for i in range(10):
            a = i / 10 * math.tau + math.sin(t * 1.2 + i) * 0.05
            px, py = c[0] + math.cos(a) * (ro + w * 0.4), c[1] + math.sin(a) * (ro + w * 0.4)
            lx, ly = math.cos(a + 0.5) * w * 1.7, math.sin(a + 0.5) * w * 1.7
            pygame.draw.polygon(layer, (70, 190, 110), [(px, py), (px + lx * 0.5 - ly * 0.35, py + ly * 0.5 + lx * 0.35), (px + lx, py + ly), (px + lx * 0.5 + ly * 0.35, py + ly * 0.5 - lx * 0.35)])
    elif bid == "b3":
        _ring(layer, c, ro, w, (170, 200, 236))
        _ring(layer, c, ro - w // 2, 1, (240, 248, 255))
        n = 16
        for i in range(n):
            a = i / n * math.tau
            p = (int(c[0] + math.cos(a) * ro), int(c[1] + math.sin(a) * ro))
            pygame.draw.circle(layer, (120, 140, 190), p, max(3, w // 2 + 2))
            pygame.draw.circle(layer, (250, 248, 252), p, max(2, w // 2 + 1))
            pygame.draw.circle(layer, (255, 255, 255), (p[0] - 1, p[1] - 1), 1)
    elif bid == "b4":
        _ring(layer, c, ro, w + 1, (196, 140, 24))
        _ring(layer, c, ro, w - 1, (255, 214, 70))
        _ring(layer, c, ro - w // 2, 1, (255, 248, 200))
        hx, hy = c[0], c[1] - ro - 2
        pygame.draw.line(layer, (255, 236, 150), (hx, hy - w * 2), (hx, hy + 1), 3)
        pygame.draw.arc(layer, (255, 236, 150), (hx - w, hy - 2, w * 2, w * 2), math.pi, math.tau, 3)
        pygame.draw.circle(layer, (255, 250, 220), (hx, hy - w * 2), 3)
        a = t * 1.6
        sp = (int(c[0] + math.cos(a) * ro), int(c[1] + math.sin(a) * ro))
        pygame.draw.line(layer, (255, 255, 255), (sp[0] - 5, sp[1]), (sp[0] + 5, sp[1]), 2)
        pygame.draw.line(layer, (255, 255, 255), (sp[0], sp[1] - 5), (sp[0], sp[1] + 5), 2)
    elif bid == "b5":
        n = 28
        for i in range(n):
            a0 = i / n * math.tau + t * 1.4
            hue = (i / n + t * 0.2) % 1.0
            col = pygame.Color(0)
            col.hsva = (int(hue * 360), 80, 100, 100)
            pygame.draw.arc(layer, col, (c[0] - ro, c[1] - ro, ro * 2, ro * 2), a0, a0 + math.tau / n + 0.06, w)
        pygame.draw.circle(layer, (255, 255, 255, 90), c, ro + w // 2 + 1, 1)
    elif bid == "b6":
        _ring(layer, c, ro, w, (22, 34, 76))
        _ring(layer, c, ro + w // 2, 1, (120, 170, 255))
        _ring(layer, c, ro - w // 2, 1, (60, 90, 170))
        rs = random.Random(int(t * 8))
        for k in range(3):
            a = (k / 3) * math.tau + t * 0.7
            pts = []
            for j in range(5):
                rr = ro + w // 2 + j * (w * 0.5) - w
                aa = a + rs.uniform(-0.12, 0.12)
                pts.append((c[0] + math.cos(aa) * rr, c[1] + math.sin(aa) * rr))
            if rs.random() < 0.8:
                pygame.draw.lines(layer, (190, 220, 255), False, pts, 2)
                pygame.draw.lines(layer, (255, 255, 255), False, pts, 1)
    elif bid == "b7":
        _ring(layer, c, ro, w + 1, (150, 24, 40))
        _ring(layer, c, ro, w - 1, (255, 200, 70))
        _ring(layer, c, ro - w // 2, 1, (255, 246, 190))
        cw = int(r * 0.9)
        base = c[1] - ro - w // 2
        pts = [(c[0] - cw // 2, base), (c[0] - cw // 2, base - int(r * 0.45)), (c[0] - cw // 4, base - int(r * 0.2)), (c[0], base - int(r * 0.6)), (c[0] + cw // 4, base - int(r * 0.2)), (c[0] + cw // 2, base - int(r * 0.45)), (c[0] + cw // 2, base)]
        pygame.draw.polygon(layer, (255, 206, 70), pts)
        pygame.draw.polygon(layer, (120, 50, 0), pts, 2)
        pygame.draw.circle(layer, (226, 50, 70), (c[0], base - int(r * 0.2)), max(2, int(r * 0.09)))
        for i in range(3):
            a = t * 1.3 + i * 2.1
            sp = (int(c[0] + math.cos(a) * ro), int(c[1] + math.sin(a) * ro))
            k = 0.5 + 0.5 * math.sin(t * 5 + i)
            pygame.draw.line(layer, (255, 255, 255), (sp[0] - int(2 + 4 * k), sp[1]), (sp[0] + int(2 + 4 * k), sp[1]), 2)
            pygame.draw.line(layer, (255, 255, 255), (sp[0], sp[1] - int(2 + 4 * k)), (sp[0], sp[1] + int(2 + 4 * k)), 2)
    surf.blit(layer, layer.get_rect(center=center))


def _base(nid, w, h):
    key = ("base", nid, w, h)
    s = _CACHE.get(key)
    if s is not None:
        return s
    s = pygame.Surface((w, h))
    spec = {
        "n1": ((8, 16, 48), (46, 92, 168)),
        "n2": ((255, 190, 110), (130, 70, 150)),
        "n3": ((52, 176, 204), (8, 64, 118)),
        "n4": ((8, 18, 46), (14, 40, 74)),
        "n5": ((18, 24, 46), (70, 80, 112)),
        "n6": ((255, 232, 140), (214, 150, 36)),
    }[nid]
    for y in range(h):
        pygame.draw.line(s, mix(spec[0], spec[1], y / max(1, h - 1)), (0, y), (w, y))
    if nid == "n2":
        pygame.draw.circle(s, (255, 236, 180), (int(w * 0.78), int(h * 0.62)), int(h * 0.42))
        pygame.draw.circle(s, (255, 250, 220), (int(w * 0.78), int(h * 0.62)), int(h * 0.3))
        pygame.draw.rect(s, (90, 50, 120), (0, int(h * 0.7), w, h))
        for x in range(10, w, 46):
            pygame.draw.rect(s, (50, 26, 70), (x, int(h * 0.55), 5, h))
        pygame.draw.rect(s, (50, 26, 70), (0, int(h * 0.55), w, 4))
    elif nid == "n1":
        pygame.draw.circle(s, (250, 244, 214), (int(w * 0.84), int(h * 0.3)), int(h * 0.2))
        pygame.draw.circle(s, mix(spec[0], spec[1], 0.25), (int(w * 0.84) + int(h * 0.08), int(h * 0.3) - 3), int(h * 0.17))
        pygame.draw.polygon(s, (6, 12, 32), [(0, h), (0, int(h * 0.75)), (int(w * 0.16), int(h * 0.58)), (int(w * 0.3), int(h * 0.74)), (int(w * 0.38), h)])
    elif nid == "n3":
        rs = random.Random(4)
        for i in range(9):
            x = int(w * (i + 0.5) / 9) + rs.randint(-8, 8)
            hh = rs.randint(int(h * 0.2), int(h * 0.42))
            col = rs.choice(((255, 120, 130), (255, 170, 90), (230, 100, 170)))
            pygame.draw.rect(s, col, (x - 4, h - hh, 8, hh), border_radius=4)
            pygame.draw.circle(s, col, (x, h - hh), 8)
            pygame.draw.circle(s, (255, 230, 220), (x - 2, h - hh - 2), 2)
    elif nid == "n6":
        for i in range(14):
            x = int(w * (i + 0.5) / 14)
            y = int(h * (0.3 + 0.5 * ((i * 37) % 10) / 10))
            pygame.draw.circle(s, (176, 110, 20), (x, y), 9, 2)
            pygame.draw.circle(s, (255, 244, 170), (x - 2, y - 2), 2)
    _CACHE[key] = s
    return s


def draw_banner(surf, rect, nid, t=None):
    """Menggambar latar spanduk animasi di dalam kotak tertentu sesuai skin spanduk yang dipakai."""
    if nid == "n0" or nid is None:
        return
    t = now() if t is None else t
    w, h = rect.w, rect.h
    layer = _base(nid, w, h).copy()
    if nid == "n1":
        rs = random.Random(2)
        for _ in range(22):
            x, y, ph = rs.randrange(w), rs.randrange(int(h * 0.7)), rs.random() * 6
            c = int(110 + 140 * (0.5 + 0.5 * math.sin(t * 2.2 + ph)))
            layer.fill((c, c, 255), (x, y, 2, 2))
    if nid in ("n1", "n2"):
        for k in range(3):
            y0 = h - 8 - k * 7
            pts = [(x, y0 + math.sin(x / 26 + t * (1.2 + k * 0.3) + k) * 2.2) for x in range(0, w + 12, 12)]
            pygame.draw.lines(layer, (190, 220, 245) if nid == "n1" else (255, 214, 170), False, pts, 2)
    elif nid == "n3":
        rs = random.Random(6)
        for i in range(12):
            bx = rs.randrange(w)
            sp = 14 + rs.random() * 18
            by = (h + 10 - (t * sp + i * 17) % (h + 20))
            pygame.draw.circle(layer, (210, 244, 255), (int(bx + math.sin(t + i) * 3), int(by)), 2 + i % 3, 1)
    elif nid == "n4":
        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        for k, col in enumerate(((60, 255, 170), (80, 190, 255), (190, 110, 255))):
            pts = []
            for x in range(0, w + 8, 8):
                y = h * (0.28 + 0.16 * k) + math.sin(x / 40 + t * (0.8 + k * 0.3) + k * 2) * h * 0.14
                pts.append((x, y))
            poly = pts + [(w, pts[-1][1] + h * 0.2), (0, pts[0][1] + h * 0.2)]
            pygame.draw.polygon(ov, col + (70,), poly)
            pygame.draw.lines(ov, col + (160,), False, pts, 2)
        layer.blit(ov, (0, 0))
        rs = random.Random(9)
        for _ in range(16):
            x, y = rs.randrange(w), rs.randrange(h)
            layer.fill((220, 235, 255), (x, y, 1, 1))
    elif nid == "n5":
        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        rs = random.Random(8)
        for i in range(7):
            x = int((i * w / 6 + t * 18) % (w + 120)) - 60
            pygame.draw.ellipse(ov, (20, 26, 44, 200), (x - 50, int(h * 0.05) + (i % 3) * 8, 130, 38))
        for i in range(26):
            x = (rs.randrange(w) - t * 60 + i * 3) % w
            y = (rs.randrange(h) + t * 260 + i * 9) % h
            pygame.draw.line(ov, (170, 200, 240, 140), (x, y), (x - 3, y + 9), 1)
        layer.blit(ov, (0, 0))
        ph = (t % 3.4)
        if ph < 0.18:
            fl = pygame.Surface((w, h), pygame.SRCALPHA)
            fl.fill((220, 230, 255, int(170 * (1 - ph / 0.18))))
            layer.blit(fl, (0, 0))
            x0 = int(w * (0.3 + 0.4 * ((int(t / 3.4) * 37) % 10) / 10))
            pts = [(x0, 0), (x0 + 8, h * 0.3), (x0 - 4, h * 0.5), (x0 + 6, h * 0.8), (x0, h)]
            pygame.draw.lines(layer, (255, 255, 255), False, pts, 2)
    elif nid == "n6":
        bx = int(((t * 0.35) % 1.6 - 0.3) * w)
        band = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(band, (255, 255, 255, 90), [(bx, 0), (bx + 40, 0), (bx + 10, h), (bx - 30, h)])
        layer.blit(band, (0, 0))
        for i in range(5):
            a = 0.5 + 0.5 * math.sin(t * 3 + i * 1.9)
            x = int(w * (0.12 + i * 0.2))
            y = int(h * (0.25 + 0.5 * ((i * 3) % 5) / 5))
            k = int(2 + 4 * a)
            pygame.draw.line(layer, (255, 255, 255), (x - k, y), (x + k, y), 2)
            pygame.draw.line(layer, (255, 255, 255), (x, y - k), (x, y + k), 2)
    surf.blit(layer, rect.topleft)
