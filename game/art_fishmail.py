import math
import pygame
from .canvas import Px

W = 30
H = 22
BODY = (2, 6, 20, 13)
_CACHE = {}


def _body_back(c):
    c.rect(2, 6, 20, 13, (24, 36, 60))
    c.rect(3, 7, 18, 11, (46, 58, 92))
    c.vgrad(3, 7, 18, 11, (38, 50, 86), (62, 78, 120))


def _pocket(c):
    c.poly([(3, 7), (11, 13), (20, 7), (20, 17), (3, 17)], (240, 242, 248))
    c.vgrad(3, 13, 17, 5, (236, 240, 248), (196, 208, 230))
    c.poly([(3, 7), (11, 13), (3, 13)], (226, 232, 244))
    c.poly([(20, 7), (11, 13), (20, 13)], (214, 222, 238))
    c.line(3, 7, 11, 13, (130, 150, 190))
    c.line(20, 7, 11, 13, (130, 150, 190))
    c.rect(2, 6, 1, 13, (24, 36, 60))
    c.rect(21, 6, 1, 13, (24, 36, 60))
    c.rect(2, 18, 20, 1, (24, 36, 60))


def _flap(c, apex):
    if apex < 6:
        c.poly([(2, 6), (21, 6), (11, apex)], (24, 36, 60))
        c.poly([(4, 6), (19, 6), (11, apex + 1)], (226, 232, 244))
        c.line(4, 6, 11, apex + 1, (170, 184, 214))
        c.line(19, 6, 11, apex + 1, (170, 184, 214))
    else:
        c.poly([(3, 7), (20, 7), (11, apex)], (250, 251, 255))
        c.vgrad(4, 7, 16, max(1, int(apex) - 7), (252, 252, 255), (206, 218, 238))
        c.line(3, 7, 11, apex, (130, 150, 190))
        c.line(20, 7, 11, apex, (130, 150, 190))
        if apex > 11:
            c.circle(11, 11, 2, (220, 60, 56))
            c.px(10, 10, (255, 150, 140))


def layer(name, scale, k=0.0):
    """Mengambil lapisan amplop bergaya pixel art yaitu bagian belakang kantong depan atau tutup dengan k sebagai tingkat penutupan dari 0 terbuka sampai 1 tertutup."""
    key = (name, scale, round(k * 14))
    if key in _CACHE:
        return _CACHE[key]
    c = Px(W, H)
    if name == "back":
        _body_back(c)
    elif name == "pocket":
        _pocket(c)
    elif name == "flap":
        _flap(c, int(round(0 + 13 * k)))
    img = c.scaled(scale)
    _CACHE[key] = img
    return img


def _tail(scale):
    key = ("tail", scale)
    if key in _CACHE:
        return _CACHE[key]
    c = Px(W, H)
    c.poly([(21, 12), (29, 5), (29, 19)], (230, 90, 70))
    c.poly([(21, 12), (27, 7), (27, 17)], (255, 140, 110))
    img = c.scaled(scale)
    _CACHE[key] = img
    return img


def _fin(scale):
    key = ("fin", scale)
    if key in _CACHE:
        return _CACHE[key]
    c = Px(W, H)
    c.poly([(10, 18), (14, 18), (12, 21)], (230, 90, 70))
    img = c.scaled(scale)
    _CACHE[key] = img
    return img


def closed(scale):
    """Amplop tertutup lengkap dengan tutup dan segel merah."""
    key = ("closed", scale)
    if key in _CACHE:
        return _CACHE[key]
    s = pygame.Surface((W * scale, H * scale), pygame.SRCALPHA)
    s.blit(layer("back", scale), (0, 0))
    s.blit(layer("pocket", scale), (0, 0))
    s.blit(layer("flap", scale, 1.0), (0, 0))
    _CACHE[key] = s
    return s


def fish(scale, tail=1.0, eye=1.0):
    """Amplop yang tumbuh menjadi ikan dengan tail dan eye sebagai tingkat pertumbuhan ekor dan mata dari 0 sampai 1 lebih sedikit untuk efek membal."""
    full = tail >= 1.0 and eye >= 1.0
    if full and ("full", scale) in _CACHE:
        return _CACHE[("full", scale)]
    s = pygame.Surface((W * scale, H * scale), pygame.SRCALPHA)
    if tail > 0.02:
        t = _tail(scale)
        x0 = 21 * scale
        sl = t.subsurface((x0, 0, 9 * scale, H * scale))
        w = max(1, int(sl.get_width() * tail))
        s.blit(pygame.transform.scale(sl, (w, sl.get_height())), (x0 - 2, 0))
        f = _fin(scale)
        y0 = 18 * scale
        fs = f.subsurface((10 * scale, y0, 4 * scale, 3 * scale))
        hh = max(1, int(fs.get_height() * min(1.0, tail)))
        s.blit(pygame.transform.scale(fs, (fs.get_width(), hh)), (10 * scale, y0 - 2))
    s.blit(closed(scale), (0, 0))
    if eye > 0.02:
        side = int(3 * scale * eye)
        cx, cy = int(5.5 * scale), int(10.5 * scale)
        pygame.draw.rect(s, (255, 255, 255), (cx - side // 2, cy - side // 2, side, side))
        pup = max(1, int(2 * scale * eye))
        pygame.draw.rect(s, (20, 20, 30), (cx - side // 2 + int(side * 0.3), cy - pup // 2 + 1, pup, pup))
        pygame.draw.rect(s, (24, 36, 60), (cx - side // 2 - 1, cy - side // 2 - 1, side + 2, side + 2), 1)
    if full:
        _CACHE[("full", scale)] = s
    return s


def mouth_point(scale):
    """Titik mulut ikan pada permukaan hasil fish dalam piksel layar relatif terhadap pojok kiri atas."""
    return (int(2.5 * scale), int(9 * scale))
