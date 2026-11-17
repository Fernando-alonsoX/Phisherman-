import math
import random
import pygame
from .canvas import Px, mix, shade

HOOD_D = (10, 10, 16)
HOOD = (26, 26, 36)
HOOD_L = (44, 44, 58)
HOOD_HL = (70, 72, 92)
SKIN = (208, 154, 114)
SKIN_S = (176, 122, 88)
SKIN_D = (134, 88, 64)
HAIR = (38, 27, 23)
HAIR_L = (62, 46, 38)
STRING = (206, 206, 216)
EYE_W = (238, 234, 226)
PUPIL = (22, 18, 26)
BAG = (124, 92, 122)
STUBBLE = (98, 68, 54)
JEANS = (44, 62, 98)
JEANS_L = (64, 88, 130)
JEANS_D = (26, 38, 66)
SHOE = (84, 64, 56)
SHOE_D = (50, 38, 34)
MOUTH = (96, 48, 48)
TEETH = (240, 238, 230)

EXPRESSIONS = ("tired", "wide", "smirk", "sad", "happy", "shock", "cry")


def _tint(c, light):
    if not light:
        return c
    col, k = light
    return mix(c, col, k)


def draw_head(c, cx, cy, expr="tired", light=None, hood_up=True, seed=3):
    """Menggambar kepala pria berhoodie dengan wajah lusuh sesuai ekspresi pada kanvas piksel."""
    t = lambda col: _tint(col, light)
    r = random.Random(seed)
    if hood_up:
        c.ellipse(cx - 16, cy - 18, 32, 35, HOOD_D)
        c.ellipse(cx - 15, cy - 17, 30, 33, HOOD)
        c.ellipse(cx - 14, cy - 17, 12, 8, HOOD_L)
        for i in range(6):
            c.px(cx - 11 + i, cy - 16 + (i // 3), HOOD_HL)
        c.ellipse(cx - 11, cy - 11, 22, 27, HOOD_D)
    else:
        c.ellipse(cx - 11, cy - 15, 22, 30, HAIR)
    c.ellipse(cx - 8, cy - 9, 16, 22, t(SKIN))
    c.rect(cx - 7, cy + 6, 14, 6, t(SKIN))
    c.ellipse(cx - 7, cy + 4, 14, 11, t(SKIN))
    c.rect(cx + 3, cy - 4, 5, 15, t(SKIN_S))
    c.rect(cx + 4, cy + 8, 3, 5, t(SKIN_S))
    for i in range(16):
        c.px(cx - 8 + i, cy - 9, t(SKIN_D))
    for i in range(14):
        c.px(cx - 7 + i, cy - 8, t(SKIN_D))
    for i in range(10):
        c.px(cx - 5 + i, cy - 7, t(SKIN_S))
    for (dx, dy, w) in ((-8, -9, 5), (-3, -9, 4), (2, -9, 5), (-6, -8, 3), (-1, -8, 3), (4, -8, 3), (-8, -7, 2), (6, -7, 2)):
        c.rect(cx + dx, cy + dy, w, 1, HAIR)
    c.px(cx - 4, cy - 7, HAIR)
    c.px(cx + 1, cy - 7, HAIR)
    c.px(cx - 7, cy - 6, HAIR)
    c.px(cx + 6, cy - 6, HAIR)
    c.px(cx - 2, cy - 6, HAIR_L)
    lx, rx = cx - 6, cx + 2
    ey = cy - 1
    if expr in ("tired", "sad", "cry"):
        for ex in (lx, rx):
            c.rect(ex, ey, 4, 3, EYE_W)
            c.rect(ex, ey, 4, 1, t(SKIN_D))
            c.rect(ex + (1 if expr != "sad" else 1), ey + 1, 2, 2, PUPIL)
            c.rect(ex, ey + 3, 4, 1, BAG)
            c.px(ex, ey + 4, BAG)
            c.px(ex + 2, ey + 4, BAG)
            c.px(ex + 3, ey + 4, t(SKIN_S))
        if expr == "tired":
            c.rect(lx, ey - 3, 4, 1, HAIR)
            c.px(lx + 4, ey - 2, HAIR)
            c.rect(rx, ey - 2, 4, 1, HAIR)
            c.px(rx - 1, ey - 3, HAIR)
        else:
            c.px(lx, ey - 2, HAIR)
            c.px(lx + 1, ey - 2, HAIR)
            c.px(lx + 2, ey - 3, HAIR)
            c.px(lx + 3, ey - 3, HAIR)
            c.px(rx, ey - 3, HAIR)
            c.px(rx + 1, ey - 3, HAIR)
            c.px(rx + 2, ey - 2, HAIR)
            c.px(rx + 3, ey - 2, HAIR)
        if expr == "cry":
            for (tx, ty) in ((lx + 1, ey + 5), (lx + 1, ey + 7), (rx + 2, ey + 6), (rx + 2, ey + 8)):
                c.px(tx, ty, (150, 200, 245))
    elif expr == "wide" or expr == "shock":
        for ex in (lx, rx):
            c.rect(ex, ey - 1, 4, 5, EYE_W)
            c.rect(ex + 1, ey + 1, 2, 2, PUPIL)
            c.px(ex + 1, ey + 1, (255, 255, 255))
            c.rect(ex - 1 if ex == lx else ex + 4, ey, 1, 3, t(SKIN_S))
        c.rect(lx - 1, ey - 4, 5, 1, HAIR)
        c.px(lx - 2, ey - 3, HAIR)
        c.rect(rx, ey - 4, 5, 1, HAIR)
        c.px(rx + 5, ey - 3, HAIR)
        c.px(lx, ey + 5, BAG)
        c.px(rx + 3, ey + 5, BAG)
    elif expr == "smirk":
        for ex in (lx, rx):
            c.rect(ex, ey, 4, 3, EYE_W)
            c.rect(ex, ey, 4, 1, t(SKIN_D))
            c.rect(ex + 2, ey + 1, 2, 2, PUPIL)
            c.rect(ex, ey + 3, 4, 1, BAG)
            c.px(ex + 1, ey + 4, BAG)
        c.rect(lx, ey - 3, 4, 1, HAIR)
        c.px(lx + 4, ey - 4, HAIR)
        c.rect(rx, ey - 2, 4, 1, HAIR)
        c.px(rx - 1, ey - 2, HAIR)
    elif expr == "happy":
        for ex in (lx, rx):
            c.px(ex, ey + 2, PUPIL)
            c.rect(ex + 1, ey + 1, 2, 1, PUPIL)
            c.px(ex + 3, ey + 2, PUPIL)
            c.rect(ex, ey - 3, 4, 1, HAIR)
            c.px(ex + 1, ey + 3, BAG)
            c.px(ex + 2, ey + 3, BAG)
    c.px(cx - 1, cy + 3, t(SKIN_D))
    c.px(cx - 1, cy + 4, t(SKIN_D))
    c.px(cx, cy + 5, t(SKIN_D))
    c.px(cx - 2, cy + 5, t(SKIN_D))
    c.px(cx - 3, cy + 5, t(SKIN_D))
    c.px(cx - 1, cy + 2, t(shade(SKIN, 0.25)))
    my = cy + 9
    if expr == "tired":
        c.rect(cx - 3, my, 7, 1, MOUTH)
        c.px(cx + 4, my + 1, MOUTH)
        c.rect(cx - 2, my + 1, 4, 1, t(SKIN_S))
    elif expr == "wide" or expr == "happy":
        c.rect(cx - 4, my - 1, 9, 1, MOUTH)
        c.rect(cx - 3, my, 7, 3, TEETH)
        c.rect(cx - 2, my + 3, 5, 1, MOUTH)
        c.px(cx - 5, my - 2, t(SKIN_D))
        c.px(cx + 5, my - 2, t(SKIN_D))
        c.rect(cx - 3, my + 1, 7, 1, (200, 196, 190))
    elif expr == "smirk":
        c.rect(cx - 3, my + 1, 6, 1, MOUTH)
        c.px(cx + 3, my, MOUTH)
        c.px(cx + 4, my - 1, MOUTH)
        c.px(cx + 5, my - 2, t(SKIN_D))
        c.px(cx - 4, my + 1, t(SKIN_S))
    elif expr in ("sad", "cry"):
        c.rect(cx - 2, my, 5, 1, MOUTH)
        c.px(cx - 3, my + 1, MOUTH)
        c.px(cx + 3, my + 1, MOUTH)
        c.px(cx - 4, my + 2, t(SKIN_D))
        c.px(cx + 4, my + 2, t(SKIN_D))
    elif expr == "shock":
        c.rect(cx - 2, my - 1, 5, 4, MOUTH)
        c.rect(cx - 1, my, 3, 2, (60, 20, 28))
    for i in range(18):
        sx = cx - 7 + r.randrange(15)
        sy = cy + 5 + r.randrange(9)
        if abs(sx - cx) > 2 or sy > my + 1 or sy < my - 3:
            c.px(sx, sy, STUBBLE)
    c.px(cx - 8, cy + 3, STUBBLE)
    c.px(cx + 7, cy + 3, STUBBLE)


def _legs_stand(c, cx, top, light=None):
    t = lambda col: _tint(col, light)
    for sx in (-1, 1):
        x0 = cx + (-13 if sx < 0 else 1)
        c.rect(x0, top, 12, 30, t(JEANS))
        c.rect(x0 + (8 if sx < 0 else 0), top, 4, 30, t(JEANS_D) if sx < 0 else t(JEANS_L))
        c.rect(x0 + 2, top + 12, 5, 4, t(JEANS_L))
        c.rect(x0 + 3, top + 13, 3, 2, t(shade(JEANS, 0.5)))
        c.px(x0 + 8, top + 20, t(JEANS_L))
        c.px(x0 + 4, top + 28, t(JEANS_D))
        c.px(x0 + 6, top + 29, t(JEANS_D))
        fx = x0 - (2 if sx < 0 else 0)
        c.rect(fx, top + 30, 14, 6, t(SHOE))
        c.rect(fx, top + 34, 14, 2, t(SHOE_D))
        c.rect(fx + (0 if sx < 0 else 3), top + 30, 4, 1, t(shade(SHOE, 0.3)))


def _torso_front(c, cx, top, light=None, width=17):
    t = lambda col: _tint(col, light)
    pts = [(cx - width, top), (cx + width, top), (cx + width - 3, top + 34), (cx - width + 3, top + 34)]
    c.poly(pts, t(HOOD))
    c.poly([(cx + 5, top), (cx + width, top), (cx + width - 3, top + 34), (cx + 4, top + 34)], t(HOOD_D))
    c.poly([(cx - width, top), (cx - width + 5, top), (cx - width + 7, top + 34), (cx - width + 3, top + 34)], t(HOOD_L))
    c.ellipse(cx - 11, top - 3, 22, 9, t(HOOD_L))
    c.ellipse(cx - 8, top - 1, 16, 7, t(HOOD_D))
    c.poly([(cx - 11, top + 22), (cx + 11, top + 22), (cx + 13, top + 33), (cx - 13, top + 33)], t(HOOD_D))
    c.line(cx - 11, top + 22, cx - 13, top + 33, t(HOOD_L))
    c.line(cx + 11, top + 22, cx + 13, top + 33, t(HOOD_L))
    c.line(cx - 1, top + 22, cx - 1, top + 33, t(HOOD_L))
    c.rect(cx - 4, top + 4, 2, 15, STRING)
    c.rect(cx + 3, top + 4, 2, 12, STRING)
    c.rect(cx - 4, top + 17, 2, 2, shade(STRING, -0.4))
    c.rect(cx + 3, top + 14, 2, 2, shade(STRING, -0.4))
    c.px(cx - 10, top + 8, t(HOOD_HL))
    c.px(cx - 11, top + 9, t(HOOD_HL))
    c.rect(cx + 8, top + 10, 4, 3, t(shade(HOOD, 0.2)))
    c.px(cx + 9, top + 11, t(HOOD_D))
    c.speckle(cx - 14, top + 2, 28, 30, t(HOOD_L), 10, 5)


def _arm(c, x1, y1, x2, y2, light=None, w=7, cuff=True):
    t = lambda col: _tint(col, light)
    pygame.draw.line(c.surf, t(HOOD_D), (x1 + 1, y1), (x2 + 1, y2), w)
    pygame.draw.line(c.surf, t(HOOD), (x1, y1), (x2, y2), w)
    pygame.draw.line(c.surf, t(HOOD_L), (x1 - w // 3, y1), (x2 - w // 3, y2), 1)
    if cuff:
        c.circle(x2, y2, w // 2 + 1, t(HOOD_L))
        c.circle(x2, y2 + 1, w // 2 - 1, t(HOOD_D))


def _hand(c, x, y, light=None, s=5):
    t = lambda col: _tint(col, light)
    c.rect(x - s // 2, y - s // 2, s, s, t(SKIN))
    c.rect(x - s // 2, y + s // 2 - 1, s, 1, t(SKIN_S))


def draw_man(pose="stand", expr="tired", light=None, w=96, h=130):
    """Menggambar seluruh badan karakter pada pose tertentu lalu mengembalikan Surface piksel."""
    c = Px(w, h)
    cx = w // 2
    if pose == "stand":
        _legs_stand(c, cx, 80, light)
        _torso_front(c, cx, 42, light)
        _arm(c, cx - 17, 46, cx - 22, 78, light)
        _arm(c, cx + 17, 46, cx + 22, 78, light)
        _hand(c, cx - 22, 82, light)
        _hand(c, cx + 22, 82, light)
        draw_head(c, cx, 24, expr, light)
    elif pose == "aha":
        _legs_stand(c, cx, 80, light)
        _torso_front(c, cx, 42, light)
        _arm(c, cx - 17, 46, cx - 24, 70, light)
        _arm(c, cx + 17, 46, cx + 25, 24, light)
        _hand(c, cx - 22, 74, light)
        c.rect(cx + 22, 14, 7, 7, SKIN)
        c.rect(cx + 22, 19, 7, 2, SKIN_S)
        c.rect(cx + 24, 14, 1, 4, SKIN_S)
        c.rect(cx + 26, 14, 1, 4, SKIN_S)
        draw_head(c, cx, 24, expr, light)
    elif pose == "sit":
        c.rect(cx - 10, 84, 20, 16, JEANS)
        pygame.draw.line(c.surf, JEANS_D, (cx - 6, 92), (cx - 30, 98), 14)
        pygame.draw.line(c.surf, JEANS, (cx - 6, 90), (cx - 30, 96), 13)
        pygame.draw.line(c.surf, JEANS_L, (cx - 6, 86), (cx - 30, 92), 2)
        pygame.draw.line(c.surf, JEANS_D, (cx + 6, 92), (cx + 30, 98), 14)
        pygame.draw.line(c.surf, JEANS, (cx + 6, 90), (cx + 30, 96), 13)
        pygame.draw.line(c.surf, JEANS_L, (cx + 6, 86), (cx + 30, 92), 2)
        pygame.draw.line(c.surf, JEANS_D, (cx - 30, 100), (cx + 8, 108), 11)
        pygame.draw.line(c.surf, JEANS, (cx - 30, 98), (cx + 8, 106), 10)
        pygame.draw.line(c.surf, JEANS_L, (cx - 28, 94), (cx + 4, 101), 2)
        pygame.draw.line(c.surf, JEANS_D, (cx + 30, 100), (cx - 8, 108), 11)
        pygame.draw.line(c.surf, JEANS, (cx + 30, 98), (cx - 8, 106), 9)
        c.rect(cx - 4, 103, 8, 1, JEANS_D)
        c.ellipse(cx + 2, 104, 14, 9, SHOE)
        c.rect(cx + 3, 110, 12, 2, SHOE_D)
        c.ellipse(cx - 16, 104, 14, 9, SHOE)
        c.rect(cx - 15, 110, 12, 2, SHOE_D)
        c.rect(cx - 33, 93, 4, 3, JEANS_L)
        c.px(cx - 32, 94, shade(JEANS, 0.6))
        _torso_front(c, cx, 50, light, width=16)
        _arm(c, cx - 16, 54, cx - 12, 82, light)
        _arm(c, cx + 16, 54, cx + 12, 82, light)
        _hand(c, cx - 8, 82, light)
        _hand(c, cx + 8, 82, light)
        draw_head(c, cx, 34, expr, light)
    elif pose == "type":
        _torso_front(c, cx, 48, light, width=18)
        _arm(c, cx - 18, 52, cx - 15, 86, light)
        _arm(c, cx + 18, 52, cx + 15, 86, light)
        draw_head(c, cx, 30, expr, light)
    elif pose == "huddle":
        _torso_front(c, cx, 46, light, width=18)
        for sx in (-1, 1):
            x0 = cx + sx * 14 - 8
            c.rect(x0, 70, 16, 32, JEANS)
            c.rect(x0 + (10 if sx < 0 else 0), 70, 6, 32, JEANS_D)
            c.rect(x0, 70, 6 if sx < 0 else 5, 32, JEANS_L if sx < 0 else JEANS)
            c.ellipse(x0 - 1, 64, 18, 14, JEANS_L)
            c.ellipse(x0 + 2, 66, 12, 7, shade(JEANS_L, 0.25))
            c.ellipse(x0 - 3, 99, 22, 10, SHOE)
            c.rect(x0 - 2, 105, 20, 3, SHOE_D)
            c.rect(x0 + 3, 78, 5, 4, JEANS_L)
        c.rect(cx - 5, 76, 10, 20, JEANS_D)
        _arm(c, cx - 19, 54, cx - 3, 70, light, w=8)
        _arm(c, cx + 19, 54, cx + 3, 70, light, w=8)
        c.rect(cx - 26, 66, 52, 9, HOOD)
        c.rect(cx - 26, 66, 52, 2, HOOD_L)
        c.rect(cx - 26, 73, 52, 2, HOOD_D)
        c.ellipse(cx - 29, 65, 10, 11, HOOD)
        c.ellipse(cx + 19, 65, 10, 11, HOOD)
        _hand(c, cx - 4, 71, light, 6)
        _hand(c, cx + 4, 71, light, 6)
        draw_head(c, cx, 38, expr, light)
    return c.surf


def draw_portrait(expr="tired", size=120, bg=(46, 62, 92), ring=True, light=None):
    """Membuat ikon potret bulat karakter dengan bingkai kaca untuk textbox dan statistik."""
    k = 4
    n = 48
    c = Px(n, n)
    for y in range(n):
        t = y / n
        c.rect(0, y, n, 1, mix(shade(bg, 0.25), shade(bg, -0.35), t))
    c.speckle(0, 0, n, n, shade(bg, 0.4), 14, 2)
    hw = int(n * 0.86)
    c.ellipse(n // 2 - hw // 2, n - int(n * 0.24), hw, int(n * 0.7), HOOD)
    c.rect(n // 2 - 4, n - int(n * 0.24), 2, 6, STRING)
    c.rect(n // 2 + 3, n - int(n * 0.24), 2, 4, STRING)
    draw_head(c, n // 2, int(n * 0.47), expr, light)
    img = pygame.transform.smoothscale(c.scaled(k), (size, size))
    out = pygame.Surface((size, size), pygame.SRCALPHA)
    out.blit(img, (0, 0))
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (size // 2, size // 2), size // 2 - 3)
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    if ring:
        pygame.draw.circle(out, (14, 28, 54), (size // 2, size // 2), size // 2 - 1, 4)
        pygame.draw.circle(out, (150, 200, 255), (size // 2, size // 2), size // 2 - 4, 2)
        pygame.draw.circle(out, (255, 255, 255), (size // 2, size // 2), size // 2 - 6, 1)
        hl = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.arc(hl, (255, 255, 255, 140), (10, 8, size - 20, size - 20), 2.2, 3.4, 3)
        out.blit(hl, (0, 0))
    return out


def back_view(pose="slump"):
    """Menggambar tokoh dari belakang memakai hoodie dan rambut acak dengan pose slump up atau type lalu mengembalikan surface berskala 3."""
    c = Px(110, 96)
    dy = 6 if pose == "slump" else (-2 if pose == "up" else 2)
    if pose == "up":
        for side in (-1, 1):
            bx = 55 + side * 44
            tx = 55 + side * 52
            c.poly([(bx - 8, 52), (bx + 8, 52), (tx + 5, 6), (tx - 5, 6)], HOOD)
            c.poly([(bx - 8, 52), (bx - 3, 52), (tx - 1, 6), (tx - 5, 6)], HOOD_L)
            c.rect(tx - 5, 6, 10, 3, STRING)
            c.ellipse(tx - 6, -2, 12, 11, SKIN)
            c.ellipse(tx - 5, -1, 10, 5, (228, 176, 134))
    c.ellipse(2, 44 + dy, 106, 80, HOOD_D)
    c.ellipse(3, 45 + dy, 104, 78, HOOD)
    c.ellipse(10, 47 + dy, 70, 30, HOOD_L)
    c.ellipse(12, 50 + dy, 40, 14, HOOD_HL)
    c.ellipse(34, 28 + dy, 42, 26, HOOD_D)
    c.ellipse(35, 29 + dy, 40, 24, HOOD)
    c.line(55, 52 + dy, 55, 96, HOOD_D)
    c.line(30, 60 + dy, 24, 96, HOOD_D)
    c.line(80, 60 + dy, 86, 96, HOOD_D)
    c.rect(48, 55 + dy, 2, 8, STRING)
    c.rect(60, 55 + dy, 2, 8, STRING)
    tilt = -2 if pose == "slump" else 0
    hy = 4 + dy
    c.ellipse(34 + tilt, hy, 42, 40, (14, 10, 12))
    c.ellipse(35 + tilt, hy + 1, 40, 38, HAIR)
    c.ellipse(38 + tilt, hy + 3, 28, 16, HAIR_L)
    r = random.Random(11)
    for _ in range(38):
        x = 38 + tilt + r.randrange(30)
        y = hy + 6 + r.randrange(30)
        c.line(x, y, x + r.choice((-1, 0, 1)), y + r.randrange(2, 6), HAIR_L if r.random() < 0.5 else (22, 16, 14))
    for sx in (33 + tilt, 74 + tilt):
        c.ellipse(sx, hy + 18, 5, 10, SKIN_S)
        c.px(sx + 1, hy + 21, SKIN_D)
    c.rect(44 + tilt, hy + 34, 22, 4, SKIN_S)
    for i in range(8):
        c.px(36 + tilt + i * 4, hy + 2 + (i % 3), (88, 70, 62))
    return c.scaled(3)


def _back_figure(pose, outfit, hair, headset, hood, scale=3):
    """Menggambar sosok utuh dari belakang di kursi kantor dengan kepala bahu lengan sandaran dudukan celana sepatu tiang dan roda lalu mengembalikan surface berskala 3."""
    c = Px(60, 100)
    suit, suit_d, suit_l = outfit
    hair_c, hair_l = hair
    dy = 1 if pose in ("sit", "type") else (-2 if pose == "alert" else 2)
    cx = 30
    chair = (30, 34, 46)
    chair_l = (58, 64, 84)
    chair_d = (16, 18, 26)
    metal = (200, 206, 222)
    trousers = (28, 32, 50)
    shoe = (14, 14, 20)
    for sx in (20, 34):
        c.rect(sx, 74, 7, 18, trousers)
        c.rect(sx, 74, 2, 18, (44, 50, 72))
    for sx in (18, 33):
        c.rect(sx, 91, 10, 5, shoe)
        c.rect(sx, 91, 10, 1, (60, 62, 76))
    c.rect(28, 78, 4, 12, (60, 64, 80))
    c.rect(28, 78, 1, 12, metal)
    for (x2, y2) in ((10, 95), (50, 95), (19, 98), (41, 98)):
        c.line(cx, 90, x2, y2, chair_d, 3)
        c.line(cx, 89, x2, y2 - 1, (52, 58, 76), 1)
        c.circle(x2, y2 + 1, 2, (10, 10, 14))
        c.px(x2 - 1, y2, (120, 126, 146))
    c.ellipse(11, 70, 38, 10, chair_d)
    c.ellipse(12, 69, 36, 9, chair)
    c.rect(16, 70, 28, 1, chair_l)
    if pose == "alert":
        for side in (-1, 1):
            sx = cx + side * 12
            hx = cx + side * 19
            c.poly([(sx - 3, 46), (sx + 3, 46), (hx + 2, 22), (hx - 2, 22)], suit_d)
            c.poly([(sx - 2, 46), (sx + 3, 46), (hx + 2, 22), (hx - 1, 22)], suit)
            c.ellipse(hx - 3, 15, 6, 7, SKIN)
    else:
        for side in (-1, 1):
            sx = cx + side * 17 - 2
            c.rect(sx, 38 + dy, 5, 28, suit_d)
            c.rect(sx + (0 if side < 0 else 1), 38 + dy, 3, 28, suit)
            c.rect(sx, 63 + dy, 5, 4, SKIN_S)
    c.ellipse(14, 34 + dy, 32, 14, suit_d)
    c.ellipse(15, 35 + dy, 30, 12, suit)
    c.ellipse(17, 35 + dy, 14, 5, suit_l)
    hy = 7 + dy
    c.rect(cx - 4, hy + 20, 8, 12, SKIN_S)
    if hood:
        c.ellipse(18, hy + 16, 24, 18, suit_d)
        c.ellipse(19, hy + 17, 22, 16, suit)
        c.ellipse(21, hy + 18, 10, 6, suit_l)
    else:
        c.rect(cx - 5, 34 + dy, 10, 2, (226, 230, 240))
    c.ellipse(19, hy, 22, 25, (12, 8, 8))
    c.ellipse(20, hy + 1, 20, 23, hair_c)
    c.ellipse(22, hy + 2, 14, 8, hair_l)
    r = random.Random(5)
    for _ in range(14):
        x = 23 + r.randrange(15)
        y = hy + 5 + r.randrange(14)
        c.line(x, y, x + r.choice((-1, 0, 1)), y + r.randrange(2, 4), hair_l)
    if hood:
        c.ellipse(19, hy + 12, 22, 14, suit_d)
        c.ellipse(20, hy + 13, 20, 12, suit)
        c.rect(cx - 1, hy + 14, 2, 10, suit_d)
    for sx in (17, 40):
        if not hood:
            c.ellipse(sx, hy + 10, 3, 7, SKIN_S)
    if headset:
        for k in range(0, 181, 6):
            ang = math.radians(180 + k)
            c.rect(int(round(cx + math.cos(ang) * 11.5)), int(round(hy + 12 + math.sin(ang) * 14)), 1, 2, metal)
        for sx in (16, 41):
            c.rect(sx, hy + 8, 3, 9, metal)
            c.rect(sx + (1 if sx == 16 else 0), hy + 9, 2, 7, (150, 158, 180))
        c.line(17, hy + 16, 22, hy + 22, (40, 44, 56))
        c.rect(21, hy + 21, 3, 3, (40, 44, 56))
    c.ellipse(13, 42, 34, 12, chair_d)
    c.rect(13, 48, 34, 24, chair_d)
    c.ellipse(14, 42, 32, 11, chair)
    c.rect(14, 48, 32, 23, chair)
    c.rect(14, 46, 2, 25, chair_l)
    c.rect(44, 46, 2, 25, (20, 22, 32))
    c.rect(18, 50, 24, 18, (36, 40, 54))
    c.rect(18, 50, 24, 1, (62, 68, 90))
    c.rect(cx - 1, 44, 2, 26, chair_d)
    return c.scaled(scale)


def back_view_analyst(pose="sit", k=3):
    """Menggambar analis keamanan ramping dari belakang berjas biru dengan headset duduk di kursi kantor lengkap dari kepala sampai roda lalu mengembalikan surface berskala 3."""
    return _back_figure(pose, ((44, 58, 92), (22, 30, 54), (70, 90, 138)), ((24, 18, 18), (52, 40, 38)), True, False, k)


def back_view_hacker(pose="type"):
    """Menggambar pelaku berhoodie gelap dari belakang duduk di kursi menghadap meja dengan sosok utuh dari kepala sampai roda lalu mengembalikan surface berskala 3."""
    return _back_figure(pose, ((40, 42, 58), (14, 14, 22), (66, 70, 96)), ((20, 14, 12), (44, 32, 28)), False, True)
