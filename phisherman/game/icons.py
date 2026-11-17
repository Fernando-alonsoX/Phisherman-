import math
import pygame
from .canvas import aa_surface

_CACHE = {}


def _play(d, s, col):
    pygame.draw.polygon(d, col, [(s * 0.34, s * 0.2), (s * 0.34, s * 0.8), (s * 0.82, s * 0.5)])


def _home(d, s, col):
    pygame.draw.polygon(d, col, [(s * 0.5, s * 0.12), (s * 0.94, s * 0.52), (s * 0.82, s * 0.52), (s * 0.82, s * 0.88), (s * 0.18, s * 0.88), (s * 0.18, s * 0.52), (s * 0.06, s * 0.52)])
    pygame.draw.rect(d, (0, 0, 0, 0), (s * 0.42, s * 0.58, s * 0.16, s * 0.3))
    pygame.draw.rect(d, col, (s * 0.66, s * 0.16, s * 0.1, s * 0.2))


def _exit(d, s, col):
    w = max(2, int(s * 0.09))
    pygame.draw.lines(d, col, False, [(s * 0.46, s * 0.14), (s * 0.14, s * 0.14), (s * 0.14, s * 0.86), (s * 0.46, s * 0.86)], w)
    pygame.draw.line(d, col, (s * 0.38, s * 0.5), (s * 0.8, s * 0.5), w)
    pygame.draw.polygon(d, col, [(s * 0.66, s * 0.3), (s * 0.92, s * 0.5), (s * 0.66, s * 0.7)])


def _send(d, s, col):
    pygame.draw.polygon(d, col, [(s * 0.1, s * 0.12), (s * 0.94, s * 0.5), (s * 0.1, s * 0.88), (s * 0.24, s * 0.54), (s * 0.7, s * 0.5), (s * 0.24, s * 0.46)])


def _check(d, s, col):
    w = max(3, int(s * 0.14))
    pygame.draw.lines(d, col, False, [(s * 0.16, s * 0.54), (s * 0.4, s * 0.76), (s * 0.86, s * 0.24)], w)


def _cross(d, s, col):
    w = max(3, int(s * 0.14))
    pygame.draw.line(d, col, (s * 0.2, s * 0.2), (s * 0.8, s * 0.8), w)
    pygame.draw.line(d, col, (s * 0.8, s * 0.2), (s * 0.2, s * 0.8), w)


def _warning(d, s, col):
    pygame.draw.polygon(d, col, [(s * 0.5, s * 0.08), (s * 0.96, s * 0.9), (s * 0.04, s * 0.9)])
    pygame.draw.rect(d, (0, 0, 0, 0), (s * 0.45, s * 0.36, s * 0.1, s * 0.3))
    pygame.draw.circle(d, (0, 0, 0, 0), (s * 0.5, s * 0.77), s * 0.06)


def _shield(d, s, col):
    pygame.draw.polygon(d, col, [(s * 0.5, s * 0.06), (s * 0.88, s * 0.2), (s * 0.84, s * 0.58), (s * 0.5, s * 0.94), (s * 0.16, s * 0.58), (s * 0.12, s * 0.2)])


def _retrain(d, s, col):
    w = max(3, int(s * 0.12))
    rect = pygame.Rect(s * 0.16, s * 0.16, s * 0.68, s * 0.68)
    pygame.draw.arc(d, col, rect, 0.5, 3.4, w)
    pygame.draw.arc(d, col, rect, 3.64, 6.5, w)
    pygame.draw.polygon(d, col, [(s * 0.86, s * 0.22), (s * 0.9, s * 0.52), (s * 0.62, s * 0.38)])
    pygame.draw.polygon(d, col, [(s * 0.14, s * 0.78), (s * 0.1, s * 0.48), (s * 0.38, s * 0.62)])


def _envelope(d, s, col):
    pygame.draw.rect(d, col, (s * 0.08, s * 0.22, s * 0.84, s * 0.58), border_radius=int(s * 0.06))
    w = max(2, int(s * 0.07))
    pygame.draw.lines(d, (0, 0, 0, 0), False, [(s * 0.1, s * 0.26), (s * 0.5, s * 0.58), (s * 0.9, s * 0.26)], w)


def _robot(d, s, col):
    pygame.draw.rect(d, col, (s * 0.16, s * 0.26, s * 0.68, s * 0.56), border_radius=int(s * 0.12))
    pygame.draw.line(d, col, (s * 0.5, s * 0.26), (s * 0.5, s * 0.1), max(2, int(s * 0.07)))
    pygame.draw.circle(d, col, (s * 0.5, s * 0.1), s * 0.07)
    pygame.draw.circle(d, (0, 0, 0, 0), (s * 0.34, s * 0.5), s * 0.09)
    pygame.draw.circle(d, (0, 0, 0, 0), (s * 0.66, s * 0.5), s * 0.09)
    pygame.draw.rect(d, (0, 0, 0, 0), (s * 0.36, s * 0.68, s * 0.28, s * 0.06))


def _magnifier(d, s, col):
    w = max(3, int(s * 0.1))
    pygame.draw.circle(d, col, (s * 0.42, s * 0.42), s * 0.28, w)
    pygame.draw.line(d, col, (s * 0.62, s * 0.62), (s * 0.9, s * 0.9), w + 2)


def _info(d, s, col):
    pygame.draw.circle(d, col, (s * 0.5, s * 0.5), s * 0.44)
    pygame.draw.rect(d, (0, 0, 0, 0), (s * 0.45, s * 0.42, s * 0.1, s * 0.3))
    pygame.draw.circle(d, (0, 0, 0, 0), (s * 0.5, s * 0.3), s * 0.06)


def _back(d, s, col):
    w = max(3, int(s * 0.12))
    pygame.draw.lines(d, col, False, [(s * 0.62, s * 0.18), (s * 0.28, s * 0.5), (s * 0.62, s * 0.82)], w)


def _power(d, s, col):
    w = max(3, int(s * 0.11))
    pygame.draw.arc(d, col, (s * 0.14, s * 0.16, s * 0.72, s * 0.72), -1.0, 4.14, w)
    pygame.draw.line(d, col, (s * 0.5, s * 0.08), (s * 0.5, s * 0.5), w)


def _star(d, s, col):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = s * (0.46 if i % 2 == 0 else 0.2)
        pts.append((s * 0.5 + math.cos(a) * r, s * 0.52 + math.sin(a) * r))
    pygame.draw.polygon(d, col, pts)


def _speaker_body(d, s, col):
    pygame.draw.polygon(d, col, [(s * 0.1, s * 0.38), (s * 0.28, s * 0.38), (s * 0.5, s * 0.18), (s * 0.5, s * 0.82), (s * 0.28, s * 0.62), (s * 0.1, s * 0.62)])


def _speaker(d, s, col):
    _speaker_body(d, s, col)
    w = max(2, int(s * 0.08))
    pygame.draw.arc(d, col, pygame.Rect(s * 0.38, s * 0.3, s * 0.4, s * 0.4), -0.9, 0.9, w)
    pygame.draw.arc(d, col, pygame.Rect(s * 0.3, s * 0.18, s * 0.6, s * 0.64), -0.9, 0.9, w)


def _speaker_off(d, s, col):
    _speaker_body(d, s, col)
    w = max(2, int(s * 0.1))
    pygame.draw.line(d, col, (s * 0.64, s * 0.34), (s * 0.92, s * 0.66), w)
    pygame.draw.line(d, col, (s * 0.92, s * 0.34), (s * 0.64, s * 0.66), w)


def _note(d, s, col):
    w = max(2, int(s * 0.1))
    pygame.draw.circle(d, col, (s * 0.32, s * 0.74), s * 0.16)
    pygame.draw.circle(d, col, (s * 0.76, s * 0.66), s * 0.16)
    pygame.draw.line(d, col, (s * 0.46, s * 0.72), (s * 0.46, s * 0.2), w)
    pygame.draw.line(d, col, (s * 0.9, s * 0.64), (s * 0.9, s * 0.12), w)
    pygame.draw.polygon(d, col, [(s * 0.46, s * 0.2), (s * 0.9, s * 0.1), (s * 0.9, s * 0.28), (s * 0.46, s * 0.38)])


def _user(d, s, col):
    pygame.draw.circle(d, col, (s * 0.5, s * 0.32), s * 0.19)
    pygame.draw.ellipse(d, col, (s * 0.16, s * 0.56, s * 0.68, s * 0.5))


def _users(d, s, col):
    pygame.draw.circle(d, col, (s * 0.62, s * 0.3), s * 0.15)
    pygame.draw.ellipse(d, col, (s * 0.36, s * 0.5, s * 0.58, s * 0.46))
    pygame.draw.circle(d, (0, 0, 0, 0), (s * 0.36, s * 0.38), s * 0.2)
    pygame.draw.circle(d, col, (s * 0.34, s * 0.36), s * 0.17)
    pygame.draw.ellipse(d, (0, 0, 0, 0), (s * 0.04, s * 0.58, s * 0.64, s * 0.5))
    pygame.draw.ellipse(d, col, (s * 0.07, s * 0.6, s * 0.56, s * 0.44))


def _trophy(d, s, col):
    w = max(2, int(s * 0.08))
    pygame.draw.polygon(d, col, [(s * 0.26, s * 0.12), (s * 0.74, s * 0.12), (s * 0.68, s * 0.46), (s * 0.58, s * 0.6), (s * 0.42, s * 0.6), (s * 0.32, s * 0.46)])
    pygame.draw.arc(d, col, (s * 0.04, s * 0.14, s * 0.32, s * 0.32), math.pi / 2, math.pi * 1.5, w)
    pygame.draw.arc(d, col, (s * 0.64, s * 0.14, s * 0.32, s * 0.32), -math.pi / 2, math.pi / 2, w)
    pygame.draw.rect(d, col, (s * 0.45, s * 0.58, s * 0.1, s * 0.16))
    pygame.draw.rect(d, col, (s * 0.28, s * 0.74, s * 0.44, s * 0.12), border_radius=int(s * 0.03))


def _crown(d, s, col):
    pygame.draw.polygon(d, col, [(s * 0.08, s * 0.78), (s * 0.08, s * 0.28), (s * 0.28, s * 0.52), (s * 0.5, s * 0.2), (s * 0.72, s * 0.52), (s * 0.92, s * 0.28), (s * 0.92, s * 0.78)])
    pygame.draw.rect(d, col, (s * 0.08, s * 0.8, s * 0.84, s * 0.1))


def _paperclip(d, s, col):
    w = max(2, int(s * 0.1))
    pts = [(0.50, 0.38), (0.50, 0.66)]
    for i in range(0, 13):
        a = math.pi * i / 12
        pts.append((0.40 + 0.10 * math.cos(a), 0.66 + 0.10 * math.sin(a)))
    pts.append((0.30, 0.24))
    for i in range(0, 13):
        a = math.pi + math.pi * i / 12
        pts.append((0.45 + 0.15 * math.cos(a), 0.24 + 0.15 * math.sin(a)))
    pts.append((0.60, 0.74))
    for i in range(0, 11):
        a = math.radians(150) * i / 10
        pts.append((0.45 + 0.15 * math.cos(a), 0.74 + 0.15 * math.sin(a)))
    pygame.draw.lines(d, col, False, [(x * s, y * s) for x, y in pts], w)


def _folder(d, s, col):
    pygame.draw.polygon(d, col, [(s * 0.06, s * 0.2), (s * 0.38, s * 0.2), (s * 0.46, s * 0.3), (s * 0.94, s * 0.3), (s * 0.94, s * 0.84), (s * 0.06, s * 0.84)])


def _wifi(d, s, col):
    w = max(2, int(s * 0.09))
    cx, cy = s * 0.5, s * 0.82
    for r in (0.74, 0.5, 0.26):
        pygame.draw.arc(d, col, (cx - s * r * 0.6, cy - s * r * 0.9, s * r * 1.2, s * r * 1.8), math.pi * 0.25, math.pi * 0.75, w)
    pygame.draw.circle(d, col, (cx, cy), s * 0.07)


def _chevup(d, s, col):
    w = max(2, int(s * 0.14))
    pygame.draw.lines(d, col, False, [(s * 0.2, s * 0.64), (s * 0.5, s * 0.34), (s * 0.8, s * 0.64)], w)


def _doc(d, s, col):
    pygame.draw.polygon(d, col, [(s * 0.2, s * 0.06), (s * 0.62, s * 0.06), (s * 0.82, s * 0.26), (s * 0.82, s * 0.94), (s * 0.2, s * 0.94)])
    pygame.draw.polygon(d, (0, 0, 0, 90), [(s * 0.62, s * 0.06), (s * 0.82, s * 0.26), (s * 0.62, s * 0.26)])


def _lock(d, s, col):
    w = max(3, int(s * 0.1))
    pygame.draw.rect(d, col, (s * 0.2, s * 0.44, s * 0.6, s * 0.46), border_radius=int(s * 0.06))
    pygame.draw.arc(d, col, (s * 0.28, s * 0.1, s * 0.44, s * 0.6), 0, math.pi, w)
    pygame.draw.line(d, col, (s * 0.3, s * 0.4), (s * 0.3, s * 0.46), w)
    pygame.draw.line(d, col, (s * 0.7, s * 0.4), (s * 0.7, s * 0.46), w)


REGISTRY = {
    "play": _play, "home": _home, "exit": _exit, "send": _send, "check": _check, "cross": _cross,
    "warning": _warning, "shield": _shield, "retrain": _retrain, "envelope": _envelope, "robot": _robot,
    "magnifier": _magnifier, "info": _info, "back": _back, "power": _power,
    "star": _star, "lock": _lock, "speaker": _speaker, "speaker_off": _speaker_off, "note": _note, "user": _user, "users": _users, "trophy": _trophy, "crown": _crown, "paperclip": _paperclip, "folder": _folder, "wifi": _wifi, "chevup": _chevup, "doc": _doc,
}


def icon_surface(name, size, color):
    """Mengambil ikon vektor halus dari cache berdasarkan nama ukuran dan warna."""
    key = (name, size, color)
    s = _CACHE.get(key)
    if s is None:
        fn = REGISTRY[name]
        s = aa_surface((size, size), lambda d, ss: fn(d, size * ss, color))
        _CACHE[key] = s
    return s


def draw_icon(surf, name, center, size, color):
    """Menggambar ikon vektor pada titik tengah tertentu."""
    img = icon_surface(name, int(size), tuple(color[:3]))
    surf.blit(img, img.get_rect(center=center))


def icon_fn(name):
    """Membungkus nama ikon menjadi fungsi yang dapat dipakai oleh Button."""
    def _fn(surf, center, size, color):
        """Menggambar ikon bernama pada tombol."""
        draw_icon(surf, name, center, size, color)
    return _fn
