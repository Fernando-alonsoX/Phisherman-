import math
import random
import pygame
from .canvas import Px, mix, radial_glow

_CACHE = {}
HORIZON = 250


def _body_lines(c, pts, col):
    """Menggambar garis lipatan amplop pada badan ikan dari daftar titik."""
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], col)


def _common():
    c = Px(30, 18)
    c.poly([(21, 9), (28, 3), (28, 15)], (150, 158, 176))
    c.poly([(21, 9), (26, 5), (26, 13)], (196, 204, 220))
    c.poly([(10, 15), (14, 15), (12, 18)], (150, 158, 176))
    c.rect(2, 3, 20, 13, (52, 58, 74))
    c.vgrad(3, 4, 18, 11, (240, 242, 248), (184, 192, 210))
    _body_lines(c, [(3, 4), (12, 10), (20, 4)], (126, 136, 160))
    c.rect(4, 6, 3, 3, (255, 255, 255))
    c.rect(5, 7, 2, 2, (20, 24, 34))
    c.px(3, 12, (126, 136, 160))
    return c


def _uncommon():
    c = Px(34, 21)
    c.poly([(24, 11), (33, 3), (30, 11), (33, 19)], (50, 150, 84))
    c.poly([(24, 11), (30, 6), (28, 11), (30, 16)], (140, 226, 150))
    c.poly([(6, 5), (12, 0), (19, 5)], (60, 170, 96))
    c.line(9, 4, 12, 1, (170, 240, 180))
    c.line(13, 4, 14, 1, (170, 240, 180))
    c.poly([(10, 18), (15, 18), (12, 21)], (60, 170, 96))
    c.rect(2, 4, 23, 14, (22, 72, 42))
    c.vgrad(3, 5, 21, 12, (184, 244, 176), (84, 186, 104))
    _body_lines(c, [(3, 5), (13, 11), (23, 5)], (44, 126, 68))
    c.rect(17, 7, 5, 5, (188, 44, 44))
    c.rect(18, 8, 3, 3, (255, 238, 190))
    c.px(19, 9, (188, 44, 44))
    c.rect(4, 7, 3, 3, (255, 255, 255))
    c.rect(5, 8, 2, 2, (16, 40, 24))
    return c


def _rare():
    c = Px(42, 26)
    c.poly([(29, 13), (41, 2), (37, 13), (41, 24)], (36, 88, 196))
    c.poly([(29, 13), (37, 7), (34, 13), (37, 19)], (130, 188, 255))
    c.poly([(6, 6), (9, 1), (12, 6)], (60, 120, 220))
    c.poly([(12, 6), (16, 0), (20, 6)], (60, 120, 220))
    c.poly([(20, 6), (24, 1), (28, 6)], (60, 120, 220))
    c.poly([(14, 19), (23, 19), (17, 25)], (110, 170, 250))
    c.rect(2, 6, 28, 15, (14, 36, 96))
    c.vgrad(3, 7, 26, 13, (160, 208, 255), (58, 118, 222))
    _body_lines(c, [(3, 7), (16, 14), (28, 7)], (36, 84, 168))
    c.rect(3, 9, 12, 5, (16, 20, 38))
    c.rect(5, 10, 4, 3, (255, 255, 255))
    c.rect(6, 11, 2, 2, (200, 30, 40))
    c.rect(11, 10, 3, 3, (60, 70, 100))
    c.circle(22, 14, 3, (255, 255, 255))
    c.circle(22, 14, 1, (14, 36, 96))
    c.px(13, 17, (220, 240, 255))
    return c


def _epic():
    c = Px(54, 24)
    c.poly([(41, 12), (53, 1), (48, 12), (53, 23)], (104, 44, 186))
    c.poly([(41, 12), (49, 6), (45, 12), (49, 18)], (190, 124, 255))
    c.poly([(10, 5), (20, 0), (34, 0), (39, 5)], (126, 66, 210))
    c.line(16, 4, 20, 1, (210, 170, 255))
    c.line(24, 4, 27, 1, (210, 170, 255))
    c.line(31, 4, 33, 1, (210, 170, 255))
    c.poly([(18, 17), (28, 17), (20, 23)], (150, 90, 232))
    c.poly([(1, 12), (7, 5), (41, 5), (41, 19), (7, 19)], (118, 58, 198))
    c.poly([(7, 6), (40, 6), (40, 10), (4, 11)], (166, 106, 240))
    c.poly([(5, 15), (40, 15), (40, 18), (8, 18)], (82, 36, 150))
    for x in (26, 31, 36):
        c.rect(x, 6, 1, 12, (96, 44, 170))
    _body_lines(c, [(9, 6), (23, 12), (38, 6)], (226, 204, 255))
    c.line(1, 12, 12, 13, (24, 8, 46))
    for x in (3, 5, 7, 9, 11):
        c.poly([(x, 12), (x + 2, 12), (x + 1, 15)], (255, 255, 255))
    c.circle(11, 9, 2, (255, 226, 70))
    c.px(11, 9, (200, 20, 20))
    c.circle(31, 12, 2, (210, 40, 60))
    c.px(30, 11, (255, 150, 150))
    c.outline((22, 8, 44))
    return c


def _legend():
    c = Px(62, 40)
    c.poly([(45, 21), (61, 2), (56, 21), (61, 38)], (206, 40, 66))
    c.poly([(45, 21), (57, 9), (52, 21), (57, 33)], (255, 168, 90))
    c.poly([(12, 10), (16, 2), (21, 10)], (230, 70, 70))
    c.poly([(21, 10), (27, 1), (33, 10)], (255, 150, 70))
    c.poly([(33, 10), (38, 4), (43, 10)], (230, 70, 70))
    c.poly([(16, 31), (32, 31), (23, 40)], (230, 70, 70))
    c.poly([(30, 29), (42, 29), (38, 38)], (255, 150, 70))
    c.rect(3, 9, 42, 23, (96, 40, 0))
    c.vgrad(4, 10, 40, 21, (255, 240, 160), (240, 170, 50))
    c.rect(4, 10, 40, 2, (255, 252, 214))
    _body_lines(c, [(4, 10), (24, 21), (43, 10)], (204, 120, 30))
    c.circle(24, 22, 6, (110, 10, 24))
    c.circle(24, 22, 5, (210, 34, 50))
    c.circle(22, 20, 2, (255, 130, 120))
    c.px(26, 24, (140, 16, 30))
    for x, y in ((24, 19), (22, 22), (26, 22), (24, 24)):
        c.px(x, y, (255, 226, 120))
    c.rect(6, 6, 11, 3, (255, 214, 70))
    c.poly([(6, 6), (7, 2), (9, 6)], (255, 214, 70))
    c.poly([(9, 6), (11, 1), (13, 6)], (255, 214, 70))
    c.poly([(13, 6), (15, 2), (16, 6)], (255, 214, 70))
    c.px(11, 4, (230, 40, 60))
    c.px(7, 7, (80, 220, 255))
    c.px(15, 7, (80, 220, 255))
    c.rect(6, 14, 5, 5, (255, 255, 255))
    c.rect(7, 15, 4, 4, (50, 210, 255))
    c.rect(8, 16, 2, 2, (10, 30, 60))
    c.line(3, 25, 14, 27, (96, 40, 0))
    for x in (4, 7, 10):
        c.poly([(x, 25), (x + 2, 26), (x + 1, 29)], (255, 255, 255))
    c.outline((70, 22, 0))
    return c


_MAKERS = [_common, _uncommon, _rare, _epic, _legend]


def fishmail(idx, scale=3, flip=False):
    """Menggambar ikan fishmail menurut tingkat kelangkaan dari yang polos sampai yang bermahkota."""
    key = ("fm", idx, scale, flip)
    s = _CACHE.get(key)
    if s is None:
        s = _MAKERS[idx]().scaled(scale)
        if flip:
            s = pygame.transform.flip(s, True, False)
        _CACHE[key] = s
    return s


def silhouette(idx, scale=3):
    """Membuat versi ikan yang gelap kebiruan dan samar seperti terlihat dari bawah permukaan air."""
    key = ("sil", idx, scale)
    s = _CACHE.get(key)
    if s is None:
        s = fishmail(idx, scale).copy()
        s.fill((34, 84, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)
        s.fill((20, 50, 90, 0), special_flags=pygame.BLEND_RGB_ADD)
        _CACHE[key] = s
    return s


def boat():
    """Menggambar perahu kayu kecil bermata tajam di kiri dengan lentera dan dudukan joran."""
    s = _CACHE.get("boat")
    if s is None:
        c = Px(84, 44)
        c.poly([(0, 15), (83, 19), (75, 40), (14, 40)], (40, 22, 14))
        c.poly([(2, 17), (81, 21), (74, 38), (15, 38)], (122, 76, 44))
        for i, y in enumerate((24, 30, 35)):
            c.line(5 + i * 3, y - 2 + i, 79 - i * 2, y + 2, (82, 48, 28))
        c.line(2, 16, 82, 20, (190, 140, 88), 2)
        c.line(2, 15, 82, 19, (230, 190, 130))
        for x in range(10, 76, 11):
            c.px(x, 27, (210, 170, 110))
        c.rect(70, 4, 2, 15, (60, 40, 30))
        c.rect(66, 1, 10, 9, (60, 40, 30))
        c.rect(67, 2, 8, 7, (255, 214, 96))
        c.rect(68, 3, 3, 3, (255, 248, 200))
        c.rect(48, 8, 6, 10, (70, 46, 30))
        c.rect(49, 9, 4, 3, (110, 76, 50))
        c.rect(30, 12, 14, 7, (70, 46, 30))
        c.rect(31, 13, 12, 5, (140, 92, 56))
        c.line(31, 15, 42, 15, (96, 60, 36))
        s = c.scaled(3)
        _CACHE["boat"] = s
    return s


def bobber(scale=3):
    """Menggambar pelampung merah putih pixel art."""
    key = ("bob", scale)
    s = _CACHE.get(key)
    if s is None:
        c = Px(9, 13)
        c.rect(4, 0, 1, 3, (230, 236, 244))
        c.circle(4, 6, 4, (36, 28, 36))
        c.circle(4, 6, 3, (236, 54, 54))
        c.rect(1, 6, 7, 3, (250, 250, 250))
        c.rect(2, 9, 5, 1, (240, 240, 240))
        c.px(3, 4, (255, 170, 160))
        c.rect(4, 10, 1, 3, (60, 60, 70))
        s = c.scaled(scale)
        _CACHE[key] = s
    return s


def tackle_icon(scale=3):
    """Menggambar kotak perkakas pancing kecil dengan ekor ikan mencuat sebagai ikon inventaris."""
    key = ("tackle", scale)
    s = _CACHE.get(key)
    if s is None:
        c = Px(16, 16)
        c.rect(5, 1, 6, 2, (60, 40, 30))
        c.rect(4, 2, 1, 3, (60, 40, 30))
        c.rect(11, 2, 1, 3, (60, 40, 30))
        c.rect(1, 5, 14, 10, (30, 24, 40))
        c.vgrad(2, 6, 12, 8, (236, 150, 60), (196, 92, 40))
        c.rect(2, 9, 12, 1, (120, 60, 24))
        c.rect(7, 8, 2, 3, (250, 220, 120))
        c.px(7, 9, (140, 90, 20))
        c.rect(2, 6, 12, 1, (255, 200, 130))
        c.poly([(12, 5), (15, 1), (15, 5)], (130, 190, 240))
        s = c.scaled(scale)
        _CACHE[key] = s
    return s


def build_backdrop(w, h):
    """Membangun latar statis langit malam bergradasi dengan bulan, pulau bermercusuar, dan laut luas yang gelap."""
    s = pygame.Surface((w, h)).convert()
    for y in range(HORIZON):
        t = y / HORIZON
        pygame.draw.line(s, mix((4, 8, 30), (30, 52, 108), t ** 1.5), (0, y), (w, y))
    for y in range(HORIZON, h):
        t = (y - HORIZON) / (h - HORIZON)
        pygame.draw.line(s, mix((18, 44, 92), (3, 10, 30), t ** 0.8), (0, y), (w, y))
    glow = radial_glow(150, (120, 140, 190), 0.7)
    s.blit(glow, (930 - 150, 96 - 150), special_flags=pygame.BLEND_RGB_ADD)
    pygame.draw.circle(s, (250, 244, 214), (930, 96), 38)
    pygame.draw.circle(s, (226, 218, 186), (916, 84), 8)
    pygame.draw.circle(s, (226, 218, 186), (948, 108), 6)
    pygame.draw.circle(s, (232, 224, 194), (940, 76), 5)
    hz = pygame.Surface((w, 40), pygame.SRCALPHA)
    for i in range(40):
        pygame.draw.line(hz, (130, 170, 230, int(70 * (i / 39) ** 2)), (0, i), (w, i))
    s.blit(hz, (0, HORIZON - 36))
    island = [(110, HORIZON + 2), (150, HORIZON - 22), (200, HORIZON - 36), (250, HORIZON - 30), (300, HORIZON - 16), (350, HORIZON + 2)]
    pygame.draw.polygon(s, (8, 16, 36), island)
    pygame.draw.rect(s, (14, 24, 48), (214, HORIZON - 72, 12, 38))
    pygame.draw.rect(s, (228, 232, 244), (214, HORIZON - 68, 12, 6))
    pygame.draw.rect(s, (200, 60, 60), (214, HORIZON - 58, 12, 6))
    pygame.draw.rect(s, (228, 232, 244), (214, HORIZON - 48, 12, 6))
    pygame.draw.rect(s, (255, 226, 130), (216, HORIZON - 82, 8, 10))
    pygame.draw.polygon(s, (14, 24, 48), [(212, HORIZON - 82), (220, HORIZON - 92), (228, HORIZON - 82)])
    pygame.draw.line(s, (4, 8, 30), (0, HORIZON), (w, HORIZON), 2)
    return s


def stars(n=70):
    """Menghasilkan daftar bintang tetap berisi posisi, fase kedip, dan ukuran untuk langit malam."""
    rs = random.Random(21)
    out = []
    for _ in range(n):
        x = rs.randrange(1280)
        y = rs.randrange(6, HORIZON - 40)
        if (x - 930) ** 2 + (y - 96) ** 2 < 70 ** 2:
            continue
        out.append((x, y, rs.random() * 6, rs.choice((2, 2, 3))))
    return out


def clouds():
    """Membuat beberapa awan gelap lembut yang dipakai saat cuaca memburuk."""
    key = "clouds"
    got = _CACHE.get(key)
    if got is None:
        got = []
        rs = random.Random(5)
        for i in range(5):
            w, h = 520, 150
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            for _ in range(16):
                r = rs.randint(34, 62)
                x = rs.randint(r, w - r)
                y = rs.randint(r // 2 + 20, h - r // 2)
                pygame.draw.circle(s, (30, 38, 62, 70), (x, y), r)
                pygame.draw.circle(s, (46, 56, 86, 44), (x, y - 8), int(r * 0.8))
            got.append(s)
        _CACHE[key] = got
    return got
