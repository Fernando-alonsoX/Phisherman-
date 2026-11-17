import math
import random
import pygame
from .canvas import Px, mix, shade, radial_glow
from . import pixelfont, paper
from .art_char import draw_head
from . import config as C

RW = 428
RH = 240
K = 3


def _finish(c):
    out = pygame.Surface((C.BASE_W, C.BASE_H)).convert()
    out.fill((0, 0, 0))
    out.blit(c.scaled(K), (-(RW * K - C.BASE_W) // 2, 0))
    return out


def _planks(c, x0, y0, x1, y1, base, dark, seed=1, rows=(0, 8, 18, 30, 44, 60, 78, 98)):
    r = random.Random(seed)
    c.rect(x0, y0, x1 - x0, y1 - y0, base)
    for i, off in enumerate(rows):
        y = y0 + off
        if y >= y1:
            break
        c.rect(x0, y, x1 - x0, 1, dark)
        step = 24 + i * 6
        sx = x0 + r.randrange(step)
        while sx < x1:
            c.rect(sx, y, 1, (rows[i + 1] - off) if i + 1 < len(rows) else 12, dark)
            sx += step + r.randrange(-4, 8)
    for _ in range(90):
        c.px(r.randrange(x0, x1), r.randrange(y0, y1), shade(base, r.choice((-0.25, 0.15))))


def _stain(c, x, y, w, h, col, seed=2):
    r = random.Random(seed)
    c.ellipse(x, y, w, h, col)
    c.dither(x - 2, y + h // 3, w + 4, h // 2, col, 0)
    for _ in range(w):
        c.px(x + r.randrange(w), y + h + r.randrange(6), col)


def _peel(c, x, y, w, h, wall, seed=3):
    r = random.Random(seed)
    plaster = (116, 108, 94)
    plaster_d = (78, 72, 64)
    pts = []
    n = 9
    for i in range(n):
        a = i / n * 2 * math.pi
        rr = 0.5 + r.random() * 0.5
        pts.append((x + w / 2 + math.cos(a) * w / 2 * rr, y + h / 2 + math.sin(a) * h / 2 * rr))
    c.poly([(px + 1, py + 1) for px, py in pts], plaster_d)
    c.poly(pts, plaster)
    for _ in range(int(w * h / 18)):
        c.px(x + r.randrange(int(w)), y + r.randrange(int(h)), plaster_d)
    c.line(pts[0][0], pts[0][1], pts[3][0], pts[3][1], shade(wall, 0.15))


def _crack(c, x, y, length, seed=5, col=(26, 26, 28)):
    r = random.Random(seed)
    cx, cy = x, y
    for _ in range(length):
        c.px(cx, cy, col)
        cy += 1
        cx += r.choice((-1, 0, 0, 1))
        if r.random() < 0.12:
            for k in range(r.randrange(2, 6)):
                c.px(cx + k, cy + k // 2, col)


def _paper(c, x, y, w, h, red=True, tilt=0, text=None, seed=1):
    r = random.Random(seed)
    c.rect(x + 1, y + 1, w, h, (24, 22, 22))
    c.rect(x, y, w, h, (216, 212, 196))
    c.rect(x, y + h - 2, w, 2, (190, 184, 166))
    for i in range(3, h - 6, 4):
        c.rect(x + 2, y + i, w - 4 - r.randrange(0, 6), 1, (120, 116, 108))
    if red:
        c.rect(x + 2, y + 2, w - 4, 2, (186, 48, 44))
    if text:
        for i, ch in enumerate(text):
            pixelfont.stamp(c, ch, x + 2 + i * 6, y + h // 2 - 3, (196, 40, 40))
    c.rect(x + w // 2 - 1, y - 1, 2, 2, (180, 180, 190))


def _window(c, x, y, w, h, seed=6):
    r = random.Random(seed)
    c.rect(x - 3, y - 3, w + 6, h + 6, (34, 26, 22))
    c.rect(x - 2, y - 2, w + 4, h + 4, (66, 50, 40))
    c.vgrad(x, y, w, h, (10, 18, 40), (30, 40, 70))
    bx = x
    while bx < x + w:
        bw = r.randrange(8, 16)
        bh = r.randrange(int(h * 0.35), int(h * 0.7))
        c.rect(bx, y + h - bh, bw, bh, (12, 14, 26))
        for wy in range(y + h - bh + 3, y + h - 3, 5):
            for wx in range(bx + 2, bx + bw - 2, 4):
                if r.random() < 0.22:
                    c.rect(wx, wy, 2, 2, (230, 198, 110))
        bx += bw + 1
    for _ in range(int(w * h / 22)):
        sx = r.randrange(x, x + w - 3)
        sy = r.randrange(y, y + h - 3)
        c.line(sx, sy, sx - 2, sy + 4, (110, 140, 190))
    c.rect(x + w // 2 - 1, y, 2, h, (66, 50, 40))
    c.rect(x, y + h // 2 - 1, w, 2, (66, 50, 40))
    c.rect(x - 4, y + h + 2, w + 8, 3, (74, 56, 44))
    c.rect(x - 4, y + h + 5, w + 8, 1, (30, 22, 18))
    c.rect(x - 5, y - 4, 7, h + 10, (62, 30, 34))
    c.rect(x - 5, y - 4, 7, 3, (90, 44, 46))
    for i in range(0, h + 10, 4):
        c.px(x - 4 + (i // 4) % 2, y + i, (40, 18, 22))
    c.poly([(x - 5, y + h + 6), (x + 2, y + h + 6), (x, y + h + 12), (x - 3, y + h + 9)], (62, 30, 34))


def _bulb(c, x, y_top, y_bulb):
    c.rect(x, 0, 1, y_bulb - 4, (20, 18, 18))
    c.rect(x - 2, y_bulb - 5, 5, 5, (42, 38, 34))
    c.rect(x - 2, y_bulb - 5, 5, 1, (80, 74, 66))
    c.circle(x, y_bulb + 2, 4, (255, 238, 170))
    c.circle(x, y_bulb + 2, 3, (255, 250, 220))
    c.px(x - 1, y_bulb, (255, 255, 255))


def _mattress(c, x, y, w):
    c.ellipse(x - 4, y + 18, w + 8, 8, (20, 16, 16))
    c.rect(x, y + 6, w, 14, (126, 118, 102))
    c.rect(x, y + 17, w, 3, (88, 80, 68))
    c.rect(x, y + 6, w, 2, (154, 146, 128))
    c.rect(x + w // 2 - 1, y + 7, 1, 12, (104, 96, 82))
    for sx in range(x + 4, x + w - 3, 9):
        c.px(sx, y + 10, (96, 88, 74))
    _stain(c, x + 14, y + 8, 14, 6, (96, 82, 62), 4)
    _stain(c, x + w - 34, y + 9, 10, 5, (92, 78, 60), 7)
    c.ellipse(x + w - 36, y - 4, 32, 12, (150, 148, 140))
    c.ellipse(x + w - 36, y - 4, 32, 5, (172, 170, 162))
    c.rect(x + w - 30, y + 2, 20, 2, (118, 116, 108))
    c.ellipse(x + 2, y - 1, 40, 14, (52, 70, 76))
    c.ellipse(x + 4, y - 1, 30, 6, (70, 92, 98))
    for i in range(5):
        c.line(x + 8 + i * 7, y + 3, x + 11 + i * 7, y + 8, (38, 52, 58))
    c.rect(x + 28, y + 9, 12, 1, (38, 52, 58))
    c.rect(x + 3, y + 7, 7, 4, (156, 80, 60))


def _crate(c, x, y, w, h):
    c.rect(x - 2, y + h, w + 4, 3, (16, 12, 12))
    c.rect(x, y, w, h, (96, 68, 46))
    for i in range(0, h, 9):
        c.rect(x, y + i, w, 1, (52, 36, 26))
    c.rect(x, y, 4, h, (68, 46, 32))
    c.rect(x + w - 4, y, 4, h, (68, 46, 32))
    c.rect(x, y, w, 3, (130, 96, 68))
    c.rect(x, y, w, 1, (160, 124, 90))
    for nx, ny in ((x + 1, y + 2), (x + w - 3, y + 2), (x + 1, y + h - 3), (x + w - 3, y + h - 3)):
        c.px(nx, ny, (190, 190, 200))
    c.line(x + 6, y + 12, x + w - 6, y + h - 4, (66, 46, 32))


def _noodle_cup(c, x, y):
    c.poly([(x, y), (x + 12, y), (x + 10, y + 13), (x + 2, y + 13)], (232, 226, 210))
    c.rect(x, y + 3, 12, 3, (196, 52, 44))
    c.rect(x + 1, y + 7, 10, 1, (196, 52, 44))
    c.rect(x - 1, y - 1, 14, 2, (250, 248, 240))
    c.px(x + 5, y + 4, (255, 220, 90))
    c.line(x + 3, y - 4, x + 5, y - 1, (150, 150, 150))


def _roach(c, x, y):
    c.ellipse(x, y, 5, 3, (70, 40, 24))
    c.px(x + 1, y, (110, 70, 40))
    c.px(x - 1, y + 1, (40, 24, 16))
    c.px(x + 5, y - 1, (40, 24, 16))
    c.px(x - 1, y - 1, (40, 24, 16))
    c.px(x + 2, y + 3, (40, 24, 16))
    c.px(x + 4, y + 3, (40, 24, 16))


def slum_room():
    """Menggambar ruangan kumuh pixel art tempat si karakter tinggal dan mengembalikan Surface 1280x720."""
    c = Px(RW, RH)
    WALL_A = (66, 74, 76)
    WALL_B = (58, 66, 70)
    for x in range(0, RW, 12):
        c.rect(x, 0, 6, 140, WALL_A)
        c.rect(x + 6, 0, 6, 140, WALL_B)
    for x in range(0, RW, 12):
        for y in range(6, 140, 14):
            c.px(x + 3, y, (82, 92, 90))
            c.px(x + 9, y + 7, (48, 56, 60))
    c.rect(0, 0, RW, 16, (30, 28, 32))
    c.rect(0, 14, RW, 2, (20, 18, 20))
    c.rect(0, 5, RW, 5, (92, 62, 48))
    c.rect(0, 5, RW, 1, (130, 90, 66))
    c.rect(0, 9, RW, 1, (54, 34, 28))
    for bx in range(30, RW, 90):
        c.rect(bx, 3, 3, 9, (60, 44, 38))
    c.dither(40, 6, 18, 3, (170, 90, 40), 0)
    _stain(c, 20, 18, 70, 36, (52, 56, 54), 1)
    _stain(c, 250, 20, 60, 30, (54, 58, 56), 2)
    _stain(c, 140, 80, 40, 22, (56, 60, 58), 3)
    c.dither(0, 22, 14, 60, (40, 52, 44), 0)
    c.dither(RW - 18, 30, 18, 50, (40, 52, 44), 1)
    _peel(c, 150, 22, 34, 26, WALL_A, 1)
    _peel(c, 236, 68, 26, 34, WALL_A, 2)
    _peel(c, 16, 96, 30, 24, WALL_A, 3)
    _peel(c, 380, 80, 24, 30, WALL_A, 4)
    _peel(c, 300, 18, 22, 18, WALL_A, 5)
    _crack(c, 176, 16, 50, 2)
    _crack(c, 262, 20, 36, 3)
    _crack(c, 396, 40, 28, 4)
    _window(c, 56, 34, 76, 72)
    c.line(0, 14, 24, 14, (190, 190, 190))
    c.line(0, 14, 14, 24, (180, 180, 180))
    c.line(0, 14, 6, 30, (170, 170, 170))
    c.line(0, 14, 28, 22, (170, 170, 170))
    c.px(24, 14, (210, 210, 210))
    c.rect(168, 34, 26, 34, (212, 208, 190))
    c.rect(168, 34, 26, 7, (150, 40, 40))
    for gy in range(44, 66, 6):
        for gx in range(170, 192, 6):
            c.rect(gx, gy, 5, 5, (190, 186, 168))
    for (gx, gy) in ((171, 46), (183, 46), (177, 52), (171, 58), (189, 52), (183, 64)):
        c.line(gx, gy, gx + 3, gy + 3, (190, 40, 40))
        c.line(gx + 3, gy, gx, gy + 3, (190, 40, 40))
    _paper(c, 230, 40, 32, 32, True, text="UTANG", seed=1)
    _paper(c, 264, 50, 32, 30, True, text="TELAT", seed=2)
    _paper(c, 300, 36, 34, 30, True, text="BAYAR", seed=3)
    c.line(246, 40, 276, 50, (160, 40, 40))
    c.rect(0, 138, RW, 4, (30, 24, 22))
    c.rect(0, 138, RW, 1, (70, 58, 50))
    _planks(c, 0, 142, RW, RH, (60, 46, 38), (36, 27, 22), 3)
    c.vgrad(0, 142, RW, 10, (28, 20, 18), (60, 46, 38))
    _mattress(c, 22, 134, 130)
    _crate(c, 282, 118, 110, 40)
    _noodle_cup(c, 374, 105)
    _stain(c, 190, 164, 40, 8, (36, 40, 52), 8)
    c.ellipse(190, 160, 40, 10, (26, 30, 44))
    c.ellipse(194, 161, 32, 5, (52, 62, 84))
    c.rect(204, 150, 1, 2, (110, 150, 200))
    c.rect(208, 120, 1, 36, (60, 100, 150))
    c.px(208, 156, (130, 180, 230))
    for (bx, by) in ((260, 154), (270, 160), (330, 164), (110, 166), (404, 152)):
        c.circle(bx, by, 3, (186, 184, 176))
        c.px(bx - 1, by - 1, (230, 230, 224))
        c.px(bx + 1, by + 1, (120, 118, 112))
    for i in range(6):
        c.rect(340 + (i % 3) * 7, 160 - (i // 3) * 4, 20, 3, (212, 208, 190) if i % 2 else (190, 186, 168))
    c.rect(340, 156, 24, 2, (186, 48, 44))
    _noodle_cup(c, 350, 148)
    _roach(c, 280, 168)
    c.rect(150, 168, 14, 4, (60, 90, 50))
    c.rect(151, 166, 12, 2, (96, 140, 80))
    c.rect(2, 120, 6, 8, (90, 90, 96))
    c.ellipse(2, 118, 6, 3, (120, 120, 128))
    c.line(14, 146, 40, 146, (40, 40, 44))
    _bulb(c, 214, 0, 52)
    return _finish(c)


def slum_front_props():
    """Props depan ruangan yang digambar di atas karakter seperti kaki crate dan tumpukan tagihan."""
    c = Px(RW, RH)
    return c


def room_glow(bulb_x=214, bulb_y=54, radius=220):
    """Membuat glow bohlam telanjang berwarna kuning hangat untuk blending aditif."""
    g = radial_glow(radius, (255, 214, 120), 0.9)
    return g, (bulb_x * K - 2 - radius, bulb_y * K - radius)


def pixel_monitor(inner_w, inner_h):
    """Menggambar monitor pixel art lengkap dengan bezel dan penyangga lalu mengembalikan surface dan rect layar."""
    k = 3
    iw = inner_w // k
    ih = inner_h // k
    bz = 8
    chin = 10
    w = iw + bz * 2
    h = ih + bz + chin + 20
    c = Px(w, h)
    c.rect(w // 2 - 15, bz + ih + chin - 2, 30, 14, (30, 32, 40))
    c.rect(w // 2 - 15, bz + ih + chin - 2, 4, 14, (46, 50, 62))
    c.rect(w // 2 - 15, bz + ih + chin + 12, 30, 2, (20, 22, 28))
    c.ellipse(w // 2 - 32, bz + ih + chin + 10, 64, 10, (22, 24, 30))
    c.ellipse(w // 2 - 30, bz + ih + chin + 10, 60, 6, (46, 50, 62))
    c.rect(0, 0, w, bz + ih + chin, (18, 20, 26))
    c.rect(1, 1, w - 2, bz + ih + chin - 2, (34, 38, 48))
    c.rect(2, 2, w - 4, bz + ih + chin - 4, (22, 24, 32))
    c.rect(1, 1, w - 2, 1, (74, 82, 100))
    c.rect(1, 1, 1, bz + ih + chin - 2, (60, 68, 84))
    c.rect(w - 2, 2, 1, bz + ih + chin - 4, (12, 14, 18))
    c.rect(bz - 1, bz - 1, iw + 2, ih + 2, (6, 8, 12))
    c.rect(bz, bz, iw, ih, (0, 0, 0))
    c.rect(w // 2 - 2, bz + ih + 4, 4, 2, (60, 220, 110))
    c.rect(w - 24, bz + ih + 4, 2, 2, (200, 60, 50))
    c.rect(w - 20, bz + ih + 4, 6, 2, (50, 56, 70))
    c.rect(18, bz + ih + 3, 10, 4, (14, 16, 22))
    c.line(19, bz + ih + 5, 26, bz + ih + 5, (80, 90, 110))
    return c.scaled(k), pygame.Rect(bz * k, bz * k, inner_w, inner_h)


WINDOW_RECT = pygame.Rect((RW - 54) * K - 2, 42 * K, 40 * K, 62 * K)


def _wall(c, dy):
    """Menggambar dinding malam bergaris rak buku jendela kota di kanan dan permukaan meja kayu dari baris dy ke bawah."""
    c.vgrad(0, 0, RW, dy, (34, 34, 52), (24, 24, 38))
    for x in range(0, RW, 14):
        c.rect(x, 0, 7, dy, (38, 38, 58))
    for x in range(0, RW, 14):
        for y in range(4, dy, 16):
            c.px(x + 3, y, (50, 50, 74))
    c.rect(0, 0, RW, 6, (16, 14, 22))
    _stain(c, 8, 20, 40, 20, (30, 30, 44), 3)
    c.rect(4, 74, 44, 3, (84, 60, 44))
    c.rect(4, 77, 44, 1, (36, 24, 18))
    c.rect(6, 62, 3, 12, (46, 90, 150))
    c.rect(10, 60, 4, 14, (170, 60, 60))
    c.rect(15, 64, 3, 10, (200, 170, 70))
    c.rect(19, 61, 4, 13, (70, 150, 110))
    c.rect(24, 65, 3, 9, (150, 90, 170))
    c.rect(29, 62, 3, 12, (90, 130, 180))
    c.rect(38, 50, 8, 8, (60, 44, 34))
    c.ellipse(36, 42, 12, 10, (46, 110, 60))
    c.px(40, 44, (90, 170, 90))
    c.rect(RW - 56, 40, 44, 66, (14, 14, 24))
    c.vgrad(RW - 54, 42, 40, 62, (30, 18, 60), (70, 24, 90))
    r = random.Random(4)
    bx = RW - 54
    while bx < RW - 14:
        bw = r.randrange(5, 9)
        bh = r.randrange(10, 26)
        c.rect(bx, 104 - bh, bw, bh, (18, 12, 40))
        for wy in range(104 - bh + 3, 101, 5):
            for wx in range(bx + 1, bx + bw - 1, 3):
                if r.random() < 0.3:
                    c.rect(wx, wy, 1, 2, (236, 200, 120))
        bx += bw + 1
    c.rect(RW - 36, 42, 2, 62, (14, 14, 24))
    c.rect(RW - 54, 72, 40, 2, (14, 14, 24))
    c.rect(RW - 58, 106, 48, 3, (60, 44, 36))
    c.rect(RW - 60, 36, 6, 76, (90, 36, 60))
    c.rect(0, dy - 2, RW, 2, (12, 10, 16))
    _planks(c, 0, dy, RW, RH, (82, 56, 40), (46, 30, 22), 5, rows=(0, 6, 14, 24, 40, 60))
    c.rect(0, dy, RW, 2, (122, 88, 62))
    c.rect(0, dy + 2, RW, 1, (56, 38, 28))


def compose_room():
    """Menggambar ruangan karakter dari sudut pandang meja dengan monitor besar dan jendela di kanan lalu mengembalikan surface dan rect layar."""
    c = Px(RW, RH)
    _wall(c, 214)
    mon, scr = pixel_monitor(900, 480)
    stage = _finish(c)
    mx = 55 * K - 2
    my = 25 * K
    stage.blit(mon, (mx, my))
    _desk_setup(stage)
    return stage, pygame.Rect(mx + scr.x, my + scr.y, scr.w, scr.h)


def _tower(c, x, y):
    """Menggambar casing PC desktop tegak dengan bay drive tombol daya dan lampu LED dalam pixel art."""
    w, h = 40, 62
    c.rect(x + 2, y + h, w - 2, 3, (10, 10, 16))
    c.rect(x, y, w, h, (16, 18, 26))
    c.rect(x + 1, y + 1, w - 2, h - 2, (52, 58, 74))
    c.rect(x + 1, y + 1, w - 2, 1, (110, 120, 146))
    c.rect(x + 1, y + 1, 1, h - 2, (86, 96, 120))
    c.rect(x + w - 3, y + 2, 2, h - 3, (30, 34, 46))
    for i in range(2):
        c.rect(x + 6, y + 7 + i * 9, w - 12, 6, (20, 22, 30))
        c.rect(x + 7, y + 8 + i * 9, w - 14, 1, (70, 76, 94))
        c.rect(x + w - 14, y + 10 + i * 9, 5, 1, (10, 10, 14))
    for gy in range(y + 30, y + h - 14, 3):
        c.rect(x + 7, gy, w - 14, 1, (30, 34, 46))
    c.circle(x + w // 2, y + h - 8, 3, (14, 16, 22))
    c.circle(x + w // 2, y + h - 8, 2, (60, 200, 255))
    c.px(x + w // 2 - 1, y + h - 9, (220, 250, 255))
    c.rect(x + 6, y + 24, 3, 2, (60, 230, 120))
    c.rect(x + 11, y + 24, 3, 2, (230, 90, 70))


def story_room():
    """Menggambar kamar cerita dengan meja menghadap dinding PC desktop tower jendela hujan di kanan dan tagihan di dinding lalu mengembalikan surface dan rect layar monitor."""
    c = Px(RW, RH)
    dy = 168
    _wall(c, dy)
    _paper(c, 288, 20, 34, 28, True, text="UTANG", seed=1)
    _paper(c, 326, 32, 34, 26, True, text="TELAT", seed=2)
    c.rect(300, 62, 26, 32, (212, 208, 190))
    c.rect(300, 62, 26, 7, (150, 40, 40))
    for gy in range(72, 92, 6):
        for gx in range(302, 324, 6):
            c.rect(gx, gy, 5, 5, (190, 186, 168))
    for (gx, gy) in ((303, 74), (315, 74), (309, 80)):
        c.line(gx, gy, gx + 3, gy + 3, (190, 40, 40))
        c.line(gx + 3, gy, gx, gy + 3, (190, 40, 40))
    _tower(c, 292, 104)
    c.rect(86, dy - 4, 200, 4, (10, 10, 16))
    mon, scr = pixel_monitor(540, 300)
    stage = _finish(c)
    mx = 255
    my = 112
    stage.blit(mon, (mx, my))
    _desk_setup(stage)
    return stage, pygame.Rect(mx + scr.x, my + scr.y, scr.w, scr.h)


HOOD_D2 = (14, 14, 22)

KEY_ALPHA = ((214, 200, 240), (176, 162, 214), (110, 98, 160))
KEY_MOD = ((170, 150, 204), (132, 114, 176), (84, 72, 124))
KEY_ACCENT = ((255, 196, 214), (236, 130, 168), (150, 70, 110))
KEY_ROWS = (
    [(1, "a")] + [(1, "p")] * 12 + [(2, "m")],
    [(1.5, "m")] + [(1, "p")] * 12 + [(1.5, "m")],
    [(1.75, "m")] + [(1, "p")] * 11 + [(2.25, "a")],
    [(2.25, "m")] + [(1, "p")] * 10 + [(2.75, "m")],
    [(1.25, "m")] * 3 + [(6.25, "p")] + [(1.25, "m")] * 4,
)


def _ring(c, cx, cy, col):
    for dx, dy in ((-1, -2), (0, -2), (1, -2), (-2, -1), (2, -1), (-2, 0), (2, 0), (-2, 1), (2, 1), (-1, 2), (0, 2), (1, 2)):
        c.px(cx + dx, cy + dy, col)


def _desk_setup(stage):
    """Menggambar alas meja bertelinga kucing, keyboard pastel berkeycap bertingkat, dan mouse dengan kisi piksel halus lalu menempelkannya ke dasar ruangan."""
    f = 2
    origin = 624
    c = Px(RW * K // f, 46)
    mx0, mx1 = 123, 513
    mat = (62, 48, 92)
    edge = (26, 18, 42)
    stitch = (122, 104, 166)
    bottom = c.h
    for ex in (mx0 + 14, mx1 - 34):
        c.poly([(ex, 6), (ex + 6, 0), (ex + 20, 6)], edge)
        c.poly([(ex + 3, 6), (ex + 7, 1), (ex + 16, 6)], mat)
        c.poly([(ex + 6, 6), (ex + 9, 3), (ex + 13, 6)], (150, 96, 150))
    c.rect(mx0, 6, mx1 - mx0, bottom - 6, edge)
    c.rect(mx0 + 2, 8, mx1 - mx0 - 4, bottom - 12, mat)
    c.rect(mx0 + 2, bottom - 4, mx1 - mx0 - 4, 1, (40, 30, 62))
    c.rect(mx0 + 2, 8, mx1 - mx0 - 4, 1, (104, 88, 142))
    c.rect(mx0 + 2, 9, mx1 - mx0 - 4, 1, (80, 64, 112))
    for x in range(mx0 + 8, mx1 - 8, 6):
        c.px(x, 12, stitch)
    for y in range(16, bottom - 8, 6):
        c.px(mx0 + 7, y, stitch)
        c.px(mx1 - 8, y, stitch)
    for x in (mx0, mx1 - 1):
        c.px(x, 6, (0, 0, 0, 0))
    for x in range(mx0 + 8, mx0 + 14):
        c.px(x, 16, (84, 68, 118))
    _ring(c, mx0 + 22, 28, (140, 120, 186))
    _ring(c, mx0 + 40, 36, (110, 94, 152))
    _ring(c, mx0 + 18, 38, (96, 80, 134))
    _ring(c, mx1 - 22, 36, (140, 120, 186))
    for (x, y) in ((mx1 - 44, 22), (mx0 + 62, 22), (mx1 - 60, 40), (mx0 + 34, 20)):
        c.px(x, y, (178, 158, 218))
        c.px(x + 1, y, (178, 158, 218))
    pitch = 16
    kx0 = 318 - (15 * pitch) // 2
    ky0 = 10
    rowp = 5
    case_w = 15 * pitch + 4
    case_h = 5 * rowp + 5
    c.rect(kx0 - 3, ky0 - 3, case_w, case_h + 1, (14, 10, 24))
    c.rect(kx0 - 2, ky0 - 2, case_w - 2, case_h - 1, (46, 38, 72))
    c.rect(kx0 - 2, ky0 - 2, case_w - 2, 1, (116, 100, 164))
    c.rect(kx0 - 2, ky0 - 1, case_w - 2, 1, (74, 62, 112))
    c.rect(kx0 - 2, ky0 + case_h - 3, case_w - 2, 1, (26, 20, 44))
    for ri, row in enumerate(KEY_ROWS):
        acc = 0.0
        for w, kind in row:
            kx = kx0 + int(round(acc * pitch))
            kw = int(round(w * pitch)) - 1
            acc += w
            pal = KEY_ALPHA if kind == "p" else (KEY_MOD if kind == "m" else KEY_ACCENT)
            ky = ky0 + ri * rowp
            c.rect(kx, ky, kw, 1, pal[0])
            c.rect(kx, ky + 1, kw, 2, pal[1])
            c.rect(kx, ky + 3, kw, 1, pal[2])
            c.px(kx, ky, (46, 38, 72))
            c.px(kx + kw - 1, ky, (46, 38, 72))
            c.px(kx, ky + 3, (46, 38, 72))
            c.px(kx + kw - 1, ky + 3, (46, 38, 72))
            c.rect(kx + 2, ky + 1, max(1, min(4, kw // 3)), 1, shade(pal[0], 0.3))
            if kind == "p" and kw > 40:
                c.rect(kx + kw // 2 - 6, ky + 2, 12, 1, pal[2])
    c.rect(kx0 + 4, ky0 - 2, 44, 1, (255, 120, 170))
    c.rect(kx0 + case_w - 56, ky0 - 2, 44, 1, (120, 220, 255))
    mx = mx1 - 52
    my = 11
    c.ellipse(mx, my, 26, 34, (20, 14, 34))
    c.ellipse(mx + 2, my + 2, 22, 30, (200, 188, 232))
    c.ellipse(mx + 2, my + 2, 22, 13, (230, 222, 250))
    c.rect(mx + 12, my + 2, 2, 15, (110, 96, 150))
    c.rect(mx + 2, my + 17, 22, 1, (110, 96, 150))
    c.rect(mx + 12, my + 5, 2, 6, (236, 130, 168))
    c.ellipse(mx + 6, my + 22, 8, 5, (180, 166, 214))
    glow = pygame.transform.smoothscale(radial_glow(100, (255, 90, 150), 0.55), (920, 160))
    stage.blit(glow, (RW * K // 2 - 460, origin + 20), special_flags=pygame.BLEND_RGB_ADD)
    stage.blit(c.scaled(f), (0, origin))



def _fish_logo():
    c = Px(30, 18)
    c.ellipse(2, 3, 18, 12, (255, 200, 90))
    c.poly([(18, 9), (26, 3), (26, 15)], (255, 200, 90))
    c.px(6, 8, (20, 20, 30))
    c.line(8, 4, 8, 14, (220, 150, 50))
    return c.surf


def prison_room():
    """Menggambar sel penjara dingin dengan jendela berjeruji tempat si karakter ditahan dan mengembalikan surface."""
    c = Px(RW, RH)
    c.vgrad(0, 0, RW, 150, (86, 92, 104), (62, 66, 78))
    for row in range(0, 150, 10):
        c.rect(0, row, RW, 1, (46, 50, 60))
        off = 12 if (row // 10) % 2 else 0
        for bx in range(off, RW, 24):
            c.rect(bx, row, 1, 10, (46, 50, 60))
    r = random.Random(8)
    for _ in range(500):
        c.px(r.randrange(RW), r.randrange(150), (104, 110, 122) if r.random() < 0.5 else (52, 56, 66))
    _stain(c, 90, 10, 50, 40, (58, 64, 74), 2)
    _stain(c, 20, 70, 36, 30, (56, 60, 70), 5)
    _crack(c, 200, 0, 60, 3, (36, 40, 48))
    c.rect(0, 148, RW, 3, (40, 44, 52))
    c.vgrad(0, 151, RW, RH - 151, (68, 70, 82), (30, 32, 42))
    for y in (160, 176, 198, 224):
        c.rect(0, y, RW, 1, (44, 46, 58))
    for x in range(0, RW, 46):
        c.rect(x, 151, 1, 9, (44, 46, 58))
    wx, wy, ww, wh = 330, 26, 66, 54
    c.rect(wx - 4, wy - 4, ww + 8, wh + 8, (36, 40, 50))
    c.vgrad(wx, wy, ww, wh, (10, 16, 40), (24, 36, 70))
    for _ in range(14):
        c.px(wx + r.randrange(ww), wy + r.randrange(wh // 2), (220, 224, 255))
    c.circle(wx + 48, wy + 14, 7, (240, 240, 220))
    c.circle(wx + 51, wy + 12, 6, (24, 34, 66))
    for bx in range(wx + 8, wx + ww, 14):
        c.rect(bx, wy, 3, wh, (110, 116, 130))
        c.rect(bx, wy, 1, wh, (170, 176, 190))
    c.rect(wx - 4, wy + wh + 4, ww + 8, 3, (30, 34, 42))
    for g in range(4):
        gx = 296 + g * 5
        for t in range(4):
            c.rect(gx, 70 + t * 0, 1, 12, (30, 30, 36))
        c.line(gx - 2, 80, gx + 6, 72, (30, 30, 36))
    for g in range(3):
        gx = 296 + g * 5
        c.rect(gx, 90, 1, 12, (30, 30, 36))
    c.line(294, 100, 312, 92, (30, 30, 36))
    c.rect(18, 92, 118, 4, (60, 64, 74))
    for (lx, ly) in ((22, 96), (130, 96)):
        c.rect(lx, ly, 3, 56, (74, 78, 90))
        c.rect(lx, ly, 1, 56, (108, 112, 126))
    c.rect(18, 124, 118, 4, (60, 64, 74))
    c.rect(20, 96, 114, 28, (24, 26, 34))
    c.rect(22, 118, 110, 6, (120, 124, 132))
    c.rect(22, 118, 110, 1, (160, 164, 172))
    c.ellipse(24, 110, 34, 10, (160, 160, 152))
    c.rect(18, 148, 118, 5, (28, 30, 38))
    c.rect(150, 142, 18, 14, (84, 88, 100))
    c.rect(150, 142, 18, 2, (126, 130, 144))
    c.rect(152, 156, 2, 4, (60, 64, 76))
    c.rect(164, 156, 2, 4, (60, 64, 76))
    c.ellipse(300, 148, 24, 8, (72, 76, 88))
    c.ellipse(304, 148, 16, 5, (130, 100, 70))
    c.line(212, 0, 212, 38, (34, 34, 40))
    c.rect(207, 36, 11, 3, (44, 44, 52))
    c.circle(212, 44, 6, (255, 236, 160))
    c.circle(212, 44, 4, (255, 252, 230))
    for a in range(0, 360, 45):
        c.line(212 + math.cos(math.radians(a)) * 8, 44 + math.sin(math.radians(a)) * 8, 212 + math.cos(math.radians(a + 45)) * 8, 44 + math.sin(math.radians(a + 45)) * 8, (60, 60, 70))
    return _finish(c)


def prison_bars():
    """Membuat lapisan jeruji besi depan dengan balok atas dan bawah yang dapat diturunkan sebagai animasi."""
    s = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
    n = 12
    gap = C.BASE_W // n
    for i in range(n + 1):
        x = i * gap + gap // 2 - 8
        pygame.draw.rect(s, (14, 16, 22), (x - 2, 0, 20, C.BASE_H))
        pygame.draw.rect(s, (52, 58, 70), (x, 0, 16, C.BASE_H))
        pygame.draw.rect(s, (96, 104, 120), (x + 2, 0, 4, C.BASE_H))
        pygame.draw.rect(s, (28, 32, 42), (x + 11, 0, 5, C.BASE_H))
        for y in range(0, C.BASE_H, 18):
            pygame.draw.line(s, (36, 40, 52), (x + 2, y), (x + 14, y + 6), 1)
    for y in (70, C.BASE_H - 92):
        pygame.draw.rect(s, (12, 14, 20), (0, y - 2, C.BASE_W, 30))
        pygame.draw.rect(s, (60, 66, 80), (0, y, C.BASE_W, 24))
        pygame.draw.rect(s, (110, 118, 136), (0, y + 2, C.BASE_W, 5))
        pygame.draw.rect(s, (30, 34, 44), (0, y + 17, C.BASE_W, 7))
        for x in range(30, C.BASE_W, gap):
            pygame.draw.circle(s, (150, 156, 170), (x, y + 12), 4)
            pygame.draw.circle(s, (30, 34, 44), (x, y + 12), 2)
    return s


def cyber_bg():
    """Menggambar latar ruang server gelap bertema keamanan untuk layar analisis AI agar berbeda dari layar menulis email."""
    c = Px(320, 180)
    c.vgrad(0, 0, 320, 180, (4, 12, 24), (6, 34, 48))
    for x in range(0, 320, 8):
        c.rect(x, 0, 1, 180, (8, 26, 40))
    for y in range(0, 180, 8):
        c.rect(0, y, 320, 1, (8, 26, 40))
    r = random.Random(12)
    for _ in range(26):
        x = r.randrange(0, 320, 8)
        y = r.randrange(0, 180, 8)
        pts = [(x, y)]
        for _ in range(r.randrange(2, 5)):
            if r.random() < 0.5:
                x += r.choice((-1, 1)) * r.randrange(2, 7) * 8
            else:
                y += r.choice((-1, 1)) * r.randrange(2, 5) * 8
            pts.append((x, y))
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1], b[0], b[1], (14, 80, 92))
        c.rect(pts[-1][0] - 1, pts[-1][1] - 1, 3, 3, (40, 200, 200))
        c.px(pts[0][0], pts[0][1], (90, 255, 230))
    for side in (0, 1):
        x0 = 0 if side == 0 else 320 - 50
        c.rect(x0, 0, 50, 180, (10, 18, 30))
        c.rect(x0 + (49 if side == 0 else 0), 0, 1, 180, (30, 80, 100))
        for ry in range(6, 176, 22):
            c.rect(x0 + 5, ry, 40, 18, (16, 28, 44))
            c.rect(x0 + 6, ry + 1, 38, 16, (22, 38, 58))
            for i in range(5):
                c.rect(x0 + 9 + i * 6, ry + 4, 4, 2, (10, 20, 34))
            for i in range(4):
                led = r.choice(((60, 255, 140), (255, 190, 60), (60, 200, 255), (30, 60, 70)))
                c.rect(x0 + 9 + i * 4, ry + 11, 2, 2, led)
            c.rect(x0 + 34, ry + 4, 8, 8, (10, 20, 34))
            c.rect(x0 + 35, ry + 5, 6, 6, (30, 54, 80))
    return _scale4(c)


def _scale4(c):
    out = pygame.Surface((C.BASE_W, C.BASE_H)).convert()
    out.blit(c.scaled(4), (0, 0))
    return out


def menu_bg():
    """Menggambar latar menu utama berupa laut malam dengan bulan kota jauh dan mercusuar bergaya pixel art."""
    c = Px(320, 180)
    c.vgrad(0, 0, 320, 112, (6, 12, 44), (24, 84, 128))
    r = random.Random(21)
    for _ in range(90):
        y = r.randrange(0, 80)
        c.px(r.randrange(320), y, (255, 255, 255) if r.random() < 0.4 else (170, 200, 255))
    c.circle(250, 38, 17, (60, 100, 150))
    c.circle(250, 38, 15, (232, 238, 220))
    c.circle(255, 35, 13, (220, 226, 210))
    for (mx, my, mr) in ((244, 34, 3), (252, 44, 2), (258, 32, 2), (246, 44, 2)):
        c.circle(mx, my, mr, (190, 198, 186))
    x = 0
    while x < 320:
        w = r.randrange(8, 18)
        h = r.randrange(8, 22)
        c.rect(x, 112 - h, w, h, (12, 20, 44))
        for wy in range(112 - h + 2, 110, 4):
            for wx in range(x + 2, x + w - 2, 4):
                if r.random() < 0.3:
                    c.rect(wx, wy, 2, 2, (255, 214, 120))
        x += w
    c.rect(24, 62, 6, 50, (210, 206, 196))
    for yy in range(66, 112, 10):
        c.rect(24, yy, 6, 4, (190, 60, 60))
    c.rect(22, 56, 10, 6, (30, 36, 56))
    c.rect(24, 58, 6, 3, (255, 244, 170))
    c.rect(20, 54, 14, 2, (180, 60, 60))
    c.vgrad(0, 112, 320, 68, (24, 78, 118), (4, 16, 40))
    for i in range(14):
        y = 116 + i * 4
        c.rect(236 + (i % 3) * 2, y, 28 - i, 1, (170, 200, 200))
        c.rect(244 + (i % 2) * 3, y + 2, 14 - i // 2, 1, (120, 160, 170))
    return _scale4(c)


def story_card_art():
    """Menggambar ilustrasi tombol Play Storymode berupa Dito berhoodie di meja dengan PC desktop menyala di dekat jendela hujan."""
    c = Px(110, 66)
    c.vgrad(0, 0, 110, 66, (22, 18, 46), (46, 34, 70))
    r = random.Random(5)
    for _ in range(18):
        c.px(r.randrange(110), r.randrange(30), (190, 190, 255))
    c.rect(78, 8, 28, 30, (10, 12, 28))
    c.vgrad(79, 9, 26, 28, (30, 44, 90), (60, 70, 120))
    c.rect(91, 9, 1, 28, (10, 12, 28))
    c.rect(79, 22, 26, 1, (10, 12, 28))
    for _ in range(14):
        sx = 79 + r.randrange(24)
        sy = 9 + r.randrange(26)
        c.line(sx, sy, sx - 1, sy + 2, (150, 170, 230))
    c.rect(76, 38, 32, 2, (70, 52, 44))
    c.rect(0, 52, 110, 14, (50, 36, 34))
    c.rect(0, 52, 110, 1, (84, 62, 52))
    for x in range(0, 110, 16):
        c.rect(x, 53, 1, 13, (34, 24, 24))
    c.ellipse(4, 49, 100, 8, (24, 16, 20))
    c.rect(2, 46, 100, 4, (96, 66, 46))
    c.rect(2, 46, 100, 1, (140, 104, 74))
    c.rect(6, 50, 3, 12, (70, 48, 34))
    c.rect(94, 50, 3, 12, (70, 48, 34))
    c.rect(66, 36, 20, 10, (30, 32, 44))
    c.rect(67, 37, 18, 8, (46, 50, 64))
    c.rect(69, 40, 14, 1, (90, 220, 250))
    c.rect(69, 42, 10, 1, (90, 220, 250))
    c.rect(9, 12, 34, 26, (20, 22, 30))
    c.rect(10, 13, 32, 24, (60, 66, 84))
    c.rect(12, 15, 28, 20, (8, 12, 24))
    c.vgrad(12, 15, 28, 20, (90, 220, 250), (30, 130, 200))
    c.rect(14, 17, 24, 3, (230, 244, 255))
    c.rect(14, 22, 24, 1, (255, 255, 255))
    c.rect(14, 25, 18, 1, (255, 255, 255))
    c.rect(14, 28, 21, 1, (255, 255, 255))
    c.rect(24, 37, 4, 6, (46, 50, 64))
    c.rect(18, 43, 16, 3, (36, 40, 52))
    c.rect(18, 43, 16, 1, (70, 78, 96))
    draw_head(c, 56, 24, "tired", ((90, 160, 220), 0.2))
    c.poly([(38, 40), (76, 40), (82, 50), (32, 50)], (30, 30, 44))
    c.rect(48, 40, 2, 8, (200, 200, 210))
    c.rect(60, 40, 2, 7, (200, 200, 210))
    c.rect(36, 44, 40, 2, (46, 50, 64))
    c.rect(38, 44, 36, 1, (70, 78, 96))
    for i in range(7):
        c.rect(39 + i * 5, 44, 3, 1, (130, 144, 170))
    c.rect(34, 45, 7, 4, (28, 28, 40))
    c.rect(72, 45, 7, 4, (28, 28, 40))
    for (x, y) in ((72, 20), (46, 6), (14, 6)):
        c.rect(x, y, 5, 1, (255, 220, 90))
        c.rect(x + 2, y - 2, 1, 5, (255, 220, 90))
    return c.scaled(3)


HOOD_D3 = (12, 12, 20)


def _mini_envelope():
    c = Px(14, 9)
    c.rect(0, 0, 14, 9, (24, 36, 60))
    c.rect(1, 1, 12, 7, (240, 242, 248))
    c.line(1, 1, 7, 5, (130, 150, 190))
    c.line(12, 1, 7, 5, (130, 150, 190))
    c.px(7, 5, (220, 60, 56))
    c.px(2, 3, (20, 20, 30))
    return c.surf


def _mini_hook():
    c = Px(12, 30)
    c.rect(6, 0, 1, 18, (210, 216, 226))
    c.rect(5, 18, 3, 6, (190, 198, 214))
    c.circle(6, 24, 4, (190, 198, 214))
    c.circle(6, 24, 2, (0, 0, 0, 0))
    c.rect(2, 20, 4, 5, (0, 0, 0, 0))
    c.px(2, 21, (190, 198, 214))
    c.px(1, 20, (190, 198, 214))
    return c.surf


def live_card_art():
    """Menggambar ilustrasi tombol Live Simulation berupa robot AI yang memindai amplop dengan perisai keamanan."""
    c = Px(110, 66)
    c.vgrad(0, 0, 110, 66, (4, 20, 34), (8, 52, 66))
    for x in range(0, 110, 6):
        c.rect(x, 0, 1, 66, (8, 34, 48))
    for y in range(0, 66, 6):
        c.rect(0, y, 110, 1, (8, 34, 48))
    r = random.Random(3)
    for _ in range(10):
        pixelfont.stamp(c, r.choice("01"), r.randrange(0, 104), r.randrange(0, 60), (16, 96, 100))
    c.rect(26, 6, 58, 40, (20, 24, 32))
    c.rect(27, 7, 56, 38, (60, 70, 90))
    c.rect(29, 9, 52, 34, (8, 30, 44))
    c.vgrad(29, 9, 52, 34, (10, 48, 66), (6, 24, 40))
    c.poly([(55, 12), (68, 16), (67, 28), (55, 38), (43, 28), (42, 16)], (20, 120, 70))
    c.poly([(55, 14), (66, 17), (65, 27), (55, 35), (45, 27), (44, 17)], (60, 220, 130))
    c.line(49, 25, 53, 29, (255, 255, 255), 2)
    c.line(53, 29, 61, 20, (255, 255, 255), 2)
    c.rect(48, 46, 14, 5, (40, 46, 60))
    c.rect(38, 51, 34, 3, (60, 68, 86))
    c.rect(30, 56, 50, 6, (24, 28, 38))
    c.rect(31, 57, 48, 4, (60, 70, 90))
    for i in range(10):
        c.rect(33 + i * 4.6, 58, 3, 1, (130, 144, 170))
    c.rect(2, 22, 22, 22, (24, 40, 60))
    c.rect(3, 23, 20, 20, (100, 160, 200))
    c.rect(3, 23, 20, 3, (160, 210, 240))
    c.rect(5, 28, 16, 10, (10, 24, 40))
    c.rect(7, 30, 4, 4, (90, 255, 230))
    c.rect(15, 30, 4, 4, (90, 255, 230))
    c.rect(9, 36, 8, 1, (90, 255, 230))
    c.rect(12, 18, 2, 5, (180, 200, 220))
    c.circle(13, 17, 2, (90, 255, 230))
    c.rect(8, 44, 10, 5, (70, 120, 160))
    c.blit(_mini_envelope(), 86, 28)
    for (bx, by, sx, sy) in ((84, 24, 1, 1), (104, 24, -1, 1), (84, 40, 1, -1), (104, 40, -1, -1)):
        c.rect(bx if sx > 0 else bx - 5, by, 5, 1, (90, 255, 230))
        c.rect(bx if sx > 0 else bx - 1, by if sy > 0 else by - 5 + 1, 1, 5, (90, 255, 230))
    for k in range(4):
        c.px(30 + k * 3, 33, (90, 255, 230))
    c.circle(96, 12, 5, (230, 240, 255))
    c.circle(96, 12, 3, (8, 30, 44))
    c.line(99, 15, 104, 20, (230, 240, 255), 2)
    c.rect(88, 50, 18, 8, (20, 24, 32))
    c.rect(89, 51, 16, 6, (60, 200, 240))
    c.rect(91, 53, 12, 1, (255, 255, 255))
    c.rect(91, 55, 8, 1, (255, 255, 255))
    return c.scaled(3)


def company_building():
    """Menggambar gedung YuBeatEm dari sudut pandang rendah dengan dua sisi berperspektif sehingga jendela berbentuk jajar genjang dan papan nama ikut miring lalu mengembalikan surface setinggi 1100 piksel."""
    W, H = C.BASE_W, 1100
    s = pygame.Surface((W, H))
    for y in range(H):
        t = y / H
        c = (int(4 + 22 * t), int(10 + 36 * t), int(30 + 60 * t))
        pygame.draw.line(s, c, (0, y), (W, y))
    r = random.Random(12)
    for _ in range(80):
        x, y = r.randrange(W), r.randrange(0, 560)
        col = r.choice(((200, 210, 255), (255, 240, 200), (150, 170, 230)))
        s.fill(col, (x, y, 2, 2))
    for i in range(6):
        cx, cy0 = r.randrange(0, W), r.randrange(80, 560)
        cl = pygame.Surface((420, 90), pygame.SRCALPHA)
        for k in range(6):
            pygame.draw.ellipse(cl, (50, 70, 120, 34), (k * 52, r.randrange(10, 40), 150, 46))
        s.blit(cl, (cx - 200, cy0))
    for cx0, top, wid in ((70, 420, 260), (1210, 380, 280), (-90, 560, 320), (1370, 520, 340)):
        pts = [(cx0 - wid // 2, H), (cx0 - wid // 2, top + 30), (cx0 - wid // 3, top), (cx0 + wid // 3, top), (cx0 + wid // 2, top + 30), (cx0 + wid // 2, H)]
        pygame.draw.polygon(s, (14, 22, 44), pts)
        for k in range(12):
            y = top + 40 + k * (H - top) / 12
            for x in range(int(cx0 - wid // 3), int(cx0 + wid // 3), 34):
                if r.random() < 0.22:
                    s.fill((230, 200, 120), (x + 6, y, 10, 8))
    yv, yb, kk = -2200.0, 1090.0, 0.4 / 26
    vpl, vpr = (-3360.0, 1600.0), (4640.0, 1600.0)
    floors = 26

    def cy(h):
        return yv + (yb - yv) / (1 + kk * h)

    def inter(p1, p2, p3, p4):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        a1 = x1 * y2 - y1 * x2
        a2 = x3 * y4 - y3 * x4
        return ((a1 * (x3 - x4) - (x1 - x2) * a2) / den, (a1 * (y3 - y4) - (y1 - y2) * a2) / den)

    def pt(side, u, h):
        vp = vpl if side < 0 else vpr
        fmax = 0.16 if side < 0 else 0.14
        f = fmax * (u * 1.9 / (1 + 0.9 * u))
        q = (640 + (vp[0] - 640) * f, yb + (vp[1] - yb) * f)
        return inter((640, cy(h)), vp, (640, yv), q)

    def face(side, top_col, bot_col, nb, lit_p):
        poly = [pt(side, 0, 0), pt(side, 1, 0), pt(side, 1, floors), pt(side, 0, floors)]
        grad = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(0, H, 2):
            t = min(1.0, max(0.0, (y - 120) / (H - 120)))
            pygame.draw.line(grad, (int(top_col[0] + (bot_col[0] - top_col[0]) * t), int(top_col[1] + (bot_col[1] - top_col[1]) * t), int(top_col[2] + (bot_col[2] - top_col[2]) * t), 255), (0, y), (W, y), 2)
        mask = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), poly)
        grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(grad, (0, 0))
        for j in range(3, floors):
            for i in range(nb):
                u0, u1 = i / nb + 0.1 / nb, (i + 1) / nb - 0.1 / nb
                h0, h1 = j + 0.2, j + 0.8
                quad = [pt(side, u0, h1), pt(side, u1, h1), pt(side, u1, h0), pt(side, u0, h0)]
                if r.random() < lit_p:
                    col = r.choice(((255, 226, 140), (255, 214, 110), (150, 220, 255), (255, 240, 190)))
                else:
                    col = (16, 30, 62)
                pygame.draw.polygon(s, col, quad)
                if col == (16, 30, 62):
                    pygame.draw.line(s, (34, 62, 110), quad[0], quad[1], 1)
        for j in range(0, floors + 1):
            pygame.draw.line(s, (8, 18, 42), pt(side, 0, j), pt(side, 1, j), 2)
        for i in range(nb + 1):
            pygame.draw.line(s, (8, 18, 42), pt(side, i / nb, 0), pt(side, i / nb, floors), 2)
        for i in range(nb):
            quad = [pt(side, i / nb + 0.04, 2.7), pt(side, (i + 1) / nb - 0.04, 2.7), pt(side, (i + 1) / nb - 0.04, 0.1), pt(side, i / nb + 0.04, 0.1)]
            pygame.draw.polygon(s, (255, 236, 170), quad)
            pygame.draw.polygon(s, (90, 70, 40), quad, 3)
        sheen = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(sheen, (255, 255, 255, 16), [pt(side, 0, 0), pt(side, 0.18, 0), pt(side, 0.18, floors), pt(side, 0, floors)])
        s.blit(sheen, (0, 0))

    face(-1, (52, 92, 156), (26, 50, 100), 12, 0.42)
    face(1, (26, 48, 94), (12, 26, 60), 10, 0.34)
    pygame.draw.line(s, (170, 210, 255), (640, cy(floors)), (640, cy(0)), 3)
    for side in (-1, 1):
        cap = [pt(side, 0, floors), pt(side, 1, floors), pt(side, 1, floors + 0.9), pt(side, 0, floors + 0.9)]
        pygame.draw.polygon(s, (8, 16, 36), cap)
        pygame.draw.polygon(s, (60, 90, 140), cap, 2)
    top_y = cy(floors + 0.9)
    pygame.draw.line(s, (180, 200, 230), (640, top_y), (640, 64), 4)
    pygame.draw.line(s, (180, 200, 230), (618, top_y), (640, 92), 2)
    pygame.draw.line(s, (180, 200, 230), (662, top_y), (640, 92), 2)
    tw, th = 440, 120
    tex = pygame.Surface((tw, th), pygame.SRCALPHA)
    pygame.draw.rect(tex, (6, 12, 28), (0, 0, tw, th), border_radius=12)
    pygame.draw.rect(tex, (14, 28, 60), (8, 8, tw - 16, th - 16), border_radius=10)
    pygame.draw.rect(tex, (90, 200, 255), (8, 8, tw - 16, th - 16), 4, border_radius=10)
    logo = pixelfont.render("YUBEATEM", 7, grad=((255, 255, 255), (130, 220, 255)), outline=(6, 40, 90), shadow=(1, 1, (2, 14, 40)), thick=1)
    if logo.get_width() > tw - 50:
        k = (tw - 50) / logo.get_width()
        logo = pygame.transform.smoothscale(logo, (int(logo.get_width() * k), int(logo.get_height() * k)))
    tex.blit(logo, logo.get_rect(center=(tw // 2, th // 2)))
    quad = [pt(-1, 0.94, 23.6), pt(-1, 0.08, 23.6), pt(-1, 0.08, 17.6), pt(-1, 0.94, 17.6)]
    cxq = sum(p[0] for p in quad) / 4
    cyq = sum(p[1] for p in quad) / 4
    g = radial_glow(260, (60, 170, 255), 0.5)
    s.blit(pygame.transform.scale(g, (700, 300)), (cxq - 350, cyq - 150), special_flags=pygame.BLEND_RGB_ADD)
    res = paper.warp(tex, quad)
    if res:
        s.blit(res[0], res[1])
    pygame.draw.polygon(s, (90, 200, 255), quad, 3)
    gl = radial_glow(300, (255, 220, 150), 0.7)
    s.blit(pygame.transform.scale(gl, (900, 300)), (640 - 450, H - 200), special_flags=pygame.BLEND_RGB_ADD)
    return s


def _office_wall(c, dy):
    """Menggambar dinding kantor keamanan siber bernuansa biru keabuan dengan jendela kota papan tulis jam dan lantai meja abu."""
    c.vgrad(0, 0, RW, dy, (46, 60, 82), (30, 40, 58))
    for x in range(0, RW, 42):
        c.rect(x, 0, 1, dy, (24, 32, 48))
        c.rect(x + 1, 0, 1, dy, (62, 78, 104))
    c.rect(0, 0, RW, 8, (18, 22, 32))
    for x in range(20, RW, 90):
        c.rect(x, 6, 40, 3, (210, 226, 255))
    c.rect(0, dy - 22, RW, 22, (24, 32, 48))
    c.rect(0, dy - 22, RW, 1, (70, 90, 120))
    r = random.Random(21)
    c.rect(6, 28, 72, 82, (10, 14, 22))
    c.vgrad(8, 30, 68, 78, (12, 20, 44), (36, 46, 84))
    bx = 8
    while bx < 74:
        bw = r.randrange(6, 12)
        bh = r.randrange(16, 50)
        c.rect(bx, 108 - bh, bw, bh, (14, 18, 36))
        for wy in range(108 - bh + 3, 105, 5):
            for wx in range(bx + 1, bx + bw - 1, 3):
                if r.random() < 0.3:
                    c.rect(wx, wy, 1, 2, (236, 210, 130))
        bx += bw + 1
    c.rect(41, 30, 2, 78, (10, 14, 22))
    c.rect(8, 68, 68, 2, (10, 14, 22))
    c.rect(4, 110, 80, 3, (92, 104, 130))
    c.rect(RW - 96, 30, 84, 56, (220, 226, 236))
    c.rect(RW - 96, 30, 84, 56, (220, 226, 236))
    c.rect(RW - 98, 28, 88, 2, (120, 130, 150))
    c.rect(RW - 98, 86, 88, 2, (120, 130, 150))
    c.rect(RW - 98, 28, 2, 60, (120, 130, 150))
    c.rect(RW - 12, 28, 2, 60, (120, 130, 150))
    for i in range(4):
        c.line(RW - 90, 40 + i * 10, RW - 30 - r.randrange(30), 40 + i * 10, (60, 90, 160))
    for (sx, sy, col) in ((RW - 40, 38, (255, 214, 90)), (RW - 26, 56, (255, 120, 120)), (RW - 50, 66, (120, 220, 160))):
        c.rect(sx, sy, 10, 10, col)
    c.circle(RW - 130, 40, 14, (14, 18, 26))
    c.circle(RW - 130, 40, 12, (236, 240, 248))
    c.line(RW - 130, 40, RW - 130, 32, (30, 34, 44))
    c.line(RW - 130, 40, RW - 124, 42, (30, 34, 44))
    c.rect(RW - 150, 108, 12, 14, (70, 54, 44))
    c.ellipse(RW - 154, 90, 20, 22, (40, 120, 70))
    c.ellipse(RW - 148, 80, 14, 18, (60, 150, 90))
    c.rect(0, dy - 2, RW, 2, (12, 14, 20))
    _planks(c, 0, dy, RW, RH, (98, 104, 116), (64, 70, 82), 9, rows=(0, 8, 18, 30, 46, 64))
    c.rect(0, dy, RW, 2, (160, 170, 190))


def office_room():
    """Menggambar kantor operasi keamanan dengan dua monitor di meja dan lampu sirene di atas lalu mengembalikan surface dan rect layar monitor utama."""
    c = Px(RW, RH)
    dy = 170
    _office_wall(c, dy)
    c.rect(180, 14, 60, 14, (28, 32, 42))
    c.rect(184, 18, 52, 6, (180, 20, 20))
    c.rect(86, dy - 4, 200, 4, (10, 12, 18))
    mon, scr = pixel_monitor(480, 270)
    stage = _finish(c)
    mx = 320
    my = 124
    stage.blit(mon, (mx, my))
    side, sscr = pixel_monitor(210, 150)
    stage.blit(side, (mx + 520, my + 90))
    _desk_setup(stage)
    return stage, pygame.Rect(mx + scr.x, my + scr.y, scr.w, scr.h)


def analyst_room():
    """Menggambar kantor keamanan dari sudut pandang meja dengan monitor besar untuk layar konsol analis lalu mengembalikan surface dan rect layar."""
    c = Px(RW, RH)
    _office_wall(c, 214)
    mon, scr = pixel_monitor(900, 480)
    stage = _finish(c)
    mx = 55 * K - 2
    my = 25 * K
    stage.blit(mon, (mx, my))
    _desk_setup(stage)
    return stage, pygame.Rect(mx + scr.x, my + scr.y, scr.w, scr.h)
