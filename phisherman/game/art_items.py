import math
import random
import pygame
from .canvas import Px, mix, shade, radial_glow
from . import pixelfont

_CACHE = {}


def banknote(scale=3, hue="green"):
    """Menggambar lembar uang pixel art dengan ornamen dan simbol dolar."""
    key = ("bill", scale, hue)
    if key in _CACHE:
        return _CACHE[key]
    c = Px(30, 15)
    dark = (24, 84, 48)
    mid = (84, 176, 98)
    light = (150, 222, 150)
    if hue == "gold":
        dark, mid, light = (130, 88, 18), (232, 184, 58), (255, 232, 140)
    c.rect(0, 0, 30, 15, dark)
    c.rect(1, 1, 28, 13, mid)
    c.vgrad(1, 1, 28, 13, shade(mid, 0.12), shade(mid, -0.12))
    c.rect(2, 2, 26, 11, shade(mid, 0.18))
    c.rect(3, 3, 24, 9, mid)
    for i in range(3, 27, 2):
        c.px(i, 3, light)
        c.px(i + 1, 11, light)
    c.ellipse(10, 3, 11, 9, light)
    c.ellipse(11, 4, 9, 7, mid)
    pixelfont.stamp(c, "$", 13, 4, dark)
    for (x, y) in ((4, 5), (4, 9), (25, 5), (25, 9)):
        c.circle(x, y, 1, light)
    c.px(0, 0, (0, 0, 0, 0))
    c.px(29, 0, (0, 0, 0, 0))
    c.px(0, 14, (0, 0, 0, 0))
    c.px(29, 14, (0, 0, 0, 0))
    s = c.scaled(scale)
    _CACHE[key] = s
    return s


def coin(scale=3):
    """Menggambar koin emas pixel art berlambang dolar."""
    key = ("coin", scale)
    if key in _CACHE:
        return _CACHE[key]
    c = Px(14, 14)
    c.circle(7, 7, 7, (130, 84, 14))
    c.circle(7, 7, 6, (250, 196, 56))
    c.circle(7, 7, 4, (255, 226, 120))
    c.circle(7, 7, 3, (240, 184, 44))
    pixelfont.stamp(c, "$", 4, 3, (130, 84, 14))
    c.px(3, 3, (255, 255, 230))
    c.px(4, 2, (255, 255, 230))
    s = c.scaled(scale)
    _CACHE[key] = s
    return s


def bill_frames(scale=3, n=24, hue="green"):
    """Membuat banyak frame rotasi lembar uang untuk efek hujan uang tanpa biaya rotasi saat main."""
    key = ("frames", scale, n, hue)
    if key in _CACHE:
        return _CACHE[key]
    base = banknote(scale, hue)
    frames = [pygame.transform.rotate(base, i * 360 / n) for i in range(n)]
    _CACHE[key] = frames
    return frames


def coin_frames(scale=3):
    """Membuat frame koin berputar dengan memipihkan lebar koin secara berkala."""
    key = ("coinframes", scale)
    if key in _CACHE:
        return _CACHE[key]
    base = coin(scale)
    w, h = base.get_size()
    frames = []
    for i in range(12):
        f = abs(math.cos(i / 12 * math.pi))
        frames.append(pygame.transform.scale(base, (max(3, int(w * f)), h)))
    _CACHE[key] = frames
    return frames


def money_plate():
    """Membuat plat uang bergaya lembar dolar untuk HUD kanan atas dan mengembalikan surface beserta area teks."""
    if "plate" in _CACHE:
        return _CACHE["plate"]
    c = Px(62, 17)
    dark = (20, 76, 42)
    mid = (74, 166, 92)
    light = (160, 228, 158)
    c.rect(0, 0, 62, 17, dark)
    c.rect(1, 1, 60, 15, mid)
    c.vgrad(1, 1, 60, 15, shade(mid, 0.14), shade(mid, -0.16))
    c.rect(2, 2, 58, 13, shade(mid, 0.2))
    c.rect(3, 3, 56, 11, mid)
    c.vgrad(3, 3, 56, 11, shade(mid, 0.06), shade(mid, -0.1))
    for i in range(3, 59, 3):
        c.px(i, 3, light)
        c.px(i + 1, 13, light)
    c.circle(10, 8, 6, dark)
    c.circle(10, 8, 5, light)
    c.circle(10, 8, 4, mid)
    pixelfont.stamp(c, "$", 8, 5, dark)
    c.rect(20, 4, 38, 9, (22, 70, 40))
    c.rect(21, 5, 36, 7, (14, 44, 28))
    c.rect(20, 13, 38, 1, (100, 190, 110))
    for (x, y) in ((58, 2), (4, 2), (58, 14), (4, 14)):
        c.px(x, y, light)
    c.px(0, 0, (0, 0, 0, 0))
    c.px(61, 0, (0, 0, 0, 0))
    c.px(0, 16, (0, 0, 0, 0))
    c.px(61, 16, (0, 0, 0, 0))
    s = c.scaled(4)
    res = (s, pygame.Rect(21 * 4, 5 * 4, 36 * 4, 7 * 4))
    _CACHE["plate"] = res
    return res


def envelope_fish(scale=4, flip=False):
    """Menggambar amplop berbentuk ikan sebagai maskot phishing dengan mata dan sirip."""
    key = ("efish", scale, flip)
    if key in _CACHE:
        return _CACHE[key]
    c = Px(30, 18)
    c.poly([(21, 9), (29, 2), (29, 16)], (230, 90, 70))
    c.poly([(21, 9), (27, 4), (27, 14)], (255, 140, 110))
    c.rect(2, 3, 20, 13, (24, 36, 60))
    c.rect(3, 4, 18, 11, (240, 242, 248))
    c.vgrad(3, 4, 18, 11, (252, 252, 255), (200, 212, 232))
    c.line(3, 4, 12, 10, (130, 150, 190))
    c.line(20, 4, 12, 10, (130, 150, 190))
    c.circle(12, 10, 2, (220, 60, 56))
    c.px(11, 9, (255, 150, 140))
    c.rect(4, 6, 3, 3, (255, 255, 255))
    c.rect(5, 7, 2, 2, (20, 20, 30))
    c.poly([(10, 15), (14, 15), (12, 18)], (230, 90, 70))
    s = c.scaled(scale)
    if flip:
        s = pygame.transform.flip(s, True, False)
    _CACHE[key] = s
    return s


def hook(scale=4):
    """Menggambar kail pancing pixel art lengkap dengan benang."""
    key = ("hook", scale)
    if key in _CACHE:
        return _CACHE[key]
    c = Px(16, 40)
    c.rect(8, 0, 1, 24, (210, 216, 226))
    c.rect(7, 22, 3, 3, (120, 130, 150))
    for y in range(25, 34):
        c.rect(8, y, 2, 1, (190, 198, 214))
    c.circle(8, 34, 5, (190, 198, 214))
    c.circle(8, 34, 3, (0, 0, 0, 0))
    c.rect(2, 28, 6, 8, (0, 0, 0, 0))
    c.line(3, 32, 1, 28, (190, 198, 214))
    c.line(2, 28, 1, 26, (255, 255, 255))
    c.px(6, 35, (255, 255, 255))
    s = c.scaled(scale)
    _CACHE[key] = s
    return s


def _icon16(draw, scale=5):
    c = Px(16, 16)
    draw(c)
    return c.scaled(scale)


def pixel_icon(name, scale=5):
    """Menggambar ikon pixel art 16x16 untuk dialog konfirmasi seperti peringatan pintu dan disket."""
    key = ("pi", name, scale)
    if key in _CACHE:
        return _CACHE[key]

    def warn(c):
        """Segitiga peringatan kuning dengan tanda seru."""
        c.poly([(8, 1), (15, 14), (1, 14)], (60, 40, 0))
        c.poly([(8, 3), (13, 13), (3, 13)], (255, 208, 60))
        c.rect(7, 6, 2, 4, (60, 40, 0))
        c.rect(7, 11, 2, 2, (60, 40, 0))
        c.px(6, 8, (255, 240, 160))

    def door(c):
        """Pintu terbuka dengan panah keluar."""
        c.rect(1, 1, 9, 14, (70, 42, 24))
        c.rect(2, 2, 7, 12, (150, 100, 60))
        c.rect(3, 3, 5, 4, (190, 140, 90))
        c.rect(3, 9, 5, 4, (190, 140, 90))
        c.rect(7, 8, 1, 1, (255, 220, 120))
        c.rect(9, 7, 5, 2, (60, 200, 90))
        c.poly([(13, 5), (16, 8), (13, 11)], (60, 200, 90))

    def disk(c):
        """Disket penyimpanan dengan tanda sudah tersimpan."""
        c.rect(1, 1, 14, 14, (20, 40, 90))
        c.rect(2, 2, 12, 12, (50, 100, 200))
        c.rect(4, 2, 8, 5, (220, 226, 240))
        c.rect(9, 3, 2, 3, (50, 100, 200))
        c.rect(4, 9, 8, 5, (120, 140, 180))
        c.rect(5, 10, 6, 3, (210, 214, 224))
        c.px(6, 11, (60, 200, 90))
        c.px(7, 12, (60, 200, 90))
        c.px(8, 11, (60, 200, 90))
        c.px(9, 10, (60, 200, 90))

    def nodisk(c):
        """Disket dengan tanda silang merah menandakan progress tidak tersimpan."""
        disk(c)
        c.line(2, 2, 14, 14, (230, 50, 46), 2)
        c.line(14, 2, 2, 14, (230, 50, 46), 2)

    def power(c):
        """Tombol power untuk keluar dari permainan."""
        c.circle(8, 8, 7, (30, 30, 50))
        c.circle(8, 8, 6, (200, 50, 50))
        c.circle(8, 8, 4, (200, 50, 50))
        c.circle(8, 8, 3, (30, 30, 50))
        c.rect(7, 2, 2, 7, (255, 255, 255))
        c.rect(7, 8, 2, 1, (200, 50, 50))
        c.px(6, 4, (255, 160, 150))

    def brain(c):
        """Chip AI dengan sirkuit sebagai ikon model yang tersimpan."""
        c.rect(3, 3, 10, 10, (20, 60, 70))
        c.rect(4, 4, 8, 8, (40, 180, 180))
        c.rect(6, 6, 4, 4, (14, 40, 50))
        c.px(7, 7, (120, 255, 240))
        for i in (4, 7, 10):
            c.rect(1, i, 2, 1, (200, 200, 210))
            c.rect(13, i, 2, 1, (200, 200, 210))
            c.rect(i, 1, 1, 2, (200, 200, 210))
            c.rect(i, 13, 1, 2, (200, 200, 210))

    fn = {"warn": warn, "door": door, "disk": disk, "nodisk": nodisk, "power": power, "brain": brain}[name]
    s = _icon16(fn, scale)
    _CACHE[key] = s
    return s


def sparkle(size=12, color=(255, 255, 255)):
    """Membuat kilau bintang kecil untuk efek dekorasi."""
    key = ("sp", size, color)
    if key in _CACHE:
        return _CACHE[key]
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    m = size // 2
    pygame.draw.line(s, color, (m, 0), (m, size), 2)
    pygame.draw.line(s, color, (0, m), (size, m), 2)
    pygame.draw.circle(s, color, (m, m), max(2, size // 5))
    _CACHE[key] = s
    return s
