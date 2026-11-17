import math
import random
import pygame
from .canvas import Px, mix, radial_glow
from .art_seabed import Seabed
from . import config as C

WORLD_H = 2700
SCREEN_W = C.BASE_W
SCREEN_H = C.BASE_H

SHALLOW = [((255, 170, 40), (255, 232, 130), (255, 110, 30)), ((255, 214, 60), (255, 246, 176), (240, 140, 20)), ((255, 120, 90), (255, 210, 190), (230, 70, 50))]
MIDDLE = [((90, 170, 255), (196, 228, 255), (50, 100, 210)), ((120, 222, 200), (214, 250, 240), (60, 150, 150)), ((170, 200, 255), (236, 244, 255), (100, 130, 220))]
DARKFISH = [((22, 58, 100), (34, 84, 124), (14, 40, 76)), ((26, 66, 98), (40, 92, 120), (16, 46, 74))]
DEEP = [((122, 100, 206), (194, 172, 244), (70, 50, 140)), ((70, 134, 156), (146, 196, 206), (40, 84, 104)), ((150, 90, 170), (222, 170, 236), (90, 50, 110))]


def _column():
    surf = pygame.Surface((SCREEN_W, WORLD_H)).convert()
    stops = [(0.0, (60, 188, 214)), (0.12, (34, 150, 200)), (0.3, (20, 100, 170)), (0.52, (10, 58, 122)), (0.76, (5, 30, 82)), (1.0, (3, 12, 40))]
    for y in range(WORLD_H):
        d = y / WORLD_H
        for i in range(len(stops) - 1):
            if stops[i][0] <= d <= stops[i + 1][0]:
                t = (d - stops[i][0]) / (stops[i + 1][0] - stops[i][0])
                col = mix(stops[i][1], stops[i + 1][1], t)
                break
        pygame.draw.line(surf, col, (0, y), (SCREEN_W, y))
    return surf


def _fish_small(pal, k=3):
    body, belly, fin = pal
    c = Px(14, 8)
    c.poly([(0, 1), (4, 4), (0, 7)], fin)
    c.ellipse(3, 1, 10, 6, body)
    c.rect(5, 4, 6, 2, belly)
    c.poly([(6, 1), (9, 0), (9, 2)], fin)
    c.px(11, 3, (255, 255, 255))
    c.px(12, 3, (14, 14, 28))
    return c.scaled(k)


def _fish_big(pal):
    body, belly, fin = pal
    c = Px(30, 14)
    c.poly([(0, 1), (7, 7), (0, 13)], fin)
    c.ellipse(5, 1, 25, 12, body)
    c.ellipse(9, 7, 18, 5, belly)
    c.poly([(12, 2), (18, 0), (20, 3)], fin)
    c.poly([(14, 10), (18, 13), (19, 10)], fin)
    c.rect(23, 4, 2, 2, (255, 255, 255))
    c.px(24, 5, (10, 10, 20))
    c.line(21, 3, 21, 11, mix(body, (0, 0, 0), 0.3))
    return c.scaled(4)


def _puffer():
    c = Px(16, 14)
    c.circle(8, 7, 6, (240, 200, 70))
    c.ellipse(4, 8, 8, 5, (255, 244, 190))
    for a in range(0, 360, 40):
        x = 8 + math.cos(math.radians(a)) * 7
        y = 7 + math.sin(math.radians(a)) * 7
        c.px(x, y, (190, 140, 40))
    c.poly([(0, 5), (3, 7), (0, 10)], (220, 150, 40))
    c.px(11, 5, (255, 255, 255))
    c.px(12, 5, (10, 10, 20))
    c.rect(13, 8, 2, 1, (180, 90, 50))
    return c.scaled(4)


def _jelly(col, frame):
    c = Px(18, 26)
    w = (14, 13, 11, 12)[frame % 4]
    h = (9, 10, 11, 10)[frame % 4]
    x0 = 9 - w // 2
    c.ellipse(x0, 1, w, h * 2 - 2, col)
    c.rect(0, 1 + h - 1, 18, 8, (0, 0, 0, 0))
    c.rect(x0, h, w, 2, mix(col, (255, 255, 255), 0.25))
    c.ellipse(x0 + 2, 2, w // 2, 3, mix(col, (255, 255, 255), 0.6))
    for i in range(5):
        tx = x0 + 1 + i * (w - 2) // 4
        for y in range(h + 1, 25):
            off = int(math.sin(y * 0.55 + i + frame * 1.5) * 1.5)
            c.px(tx + off, y, mix(col, (255, 255, 255), 0.2) if y % 3 else col)
    return c.scaled(4)


def _angler():
    c = Px(30, 24)
    body = (44, 34, 78)
    body_l = (66, 52, 108)
    dark = (30, 22, 56)
    c.poly([(0, 5), (7, 13), (0, 21)], dark)
    c.poly([(2, 7), (7, 13), (2, 19)], (54, 42, 92))
    c.ellipse(3, 6, 23, 16, dark)
    c.ellipse(4, 7, 21, 14, body)
    c.ellipse(6, 8, 14, 6, body_l)
    c.ellipse(11, 12, 16, 9, dark)
    c.ellipse(12, 12, 14, 8, body)
    c.poly([(18, 16), (29, 9), (29, 22)], (22, 6, 20))
    c.poly([(20, 16), (28, 11), (28, 20)], (120, 30, 54))
    c.line(18, 16, 29, 9, dark, 1)
    c.line(18, 16, 29, 22, dark, 1)
    for t in (0.18, 0.46, 0.74):
        x = int(18 + 11 * t)
        y = int(16 - 7 * t)
        c.poly([(x - 1, y + 1), (x + 1, y), (x, y + 4)], (250, 250, 240))
    for t in (0.2, 0.5, 0.8):
        x = int(18 + 11 * t)
        y = int(16 + 6 * t)
        c.poly([(x - 1, y - 1), (x + 1, y), (x, y - 4)], (250, 250, 240))
    c.circle(16, 10, 3, (255, 240, 150))
    c.circle(16, 10, 1, (10, 10, 20))
    c.px(15, 9, (255, 255, 255))
    c.line(13, 7, 15, 2, (110, 90, 150))
    c.line(15, 2, 20, 1, (110, 90, 150))
    c.line(20, 1, 25, 3, (110, 90, 150))
    c.circle(26, 4, 2, (255, 246, 170))
    c.px(25, 3, (255, 255, 255))
    return c.scaled(4)


def _manta(frame):
    ph = frame * math.tau / 6
    a = math.sin(ph)
    c = Px(64, 40)
    cy = 20
    body = (30, 56, 104)
    back = (20, 38, 78)
    tailc = (52, 88, 148)
    light = (70, 112, 176)
    belly = (170, 206, 236)
    tail = [(14 - i * 1.6, cy + 1 + math.sin(ph + i * 0.7) * (1 + i * 0.25)) for i in range(9)]
    for i in range(len(tail) - 1):
        c.line(tail[i][0], tail[i][1], tail[i + 1][0], tail[i + 1][1], tailc, 2 if i < 4 else 1)

    def wing(tx, ty, col, edge, spread):
        lead = [(46, cy - 3), (40, cy - 4 - spread * 0.2), (30, cy + (ty - cy) * 0.55 - 2), (tx + 6, ty), (tx, ty)]
        trail = [(tx - 1, ty + (1 if ty < cy else -1)), (tx + 10, cy + (ty - cy) * 0.55 + (4 if ty < cy else -4)), (22, cy + 3), (14, cy + 2)]
        c.poly(lead + trail, col)
        c.line(46, cy - 3, tx, ty, edge)

    far_ty = cy - 10 * math.sin(ph - 0.9) - 2
    wing(8 + 2 * (1 - abs(math.sin(ph - 0.9))), far_ty, back, (40, 70, 120), 8)
    c.ellipse(10, cy - 5, 40, 11, body)
    c.ellipse(16, cy + 1, 30, 6, belly)
    c.ellipse(20, cy - 5, 24, 5, light)
    c.poly([(48, cy - 3), (58, cy - 5), (60, cy - 2), (56, cy + 1), (49, cy + 2)], body)
    c.poly([(54, cy + 1), (62, cy + 2), (57, cy + 4)], back)
    tip_y = cy - 15 * a
    tip_x = 6 + 3 * (1 - abs(a))
    wing(tip_x, tip_y, body, light, 12)
    for (sx, k) in ((30, 0.55), (23, 0.7), (35, 0.42), (17, 0.8)):
        yy = cy - 4 + (tip_y - cy + 4) * k * 0.55
        c.px(sx, yy, (210, 232, 255))
    c.px(54, cy - 3, (255, 255, 255))
    c.px(55, cy - 3, (14, 14, 28))
    return c.scaled(4)


def _turtle(frame):
    c = Px(24, 16)
    sw = (2, -2)[frame % 2]
    c.poly([(14, 11), (18, 14 + sw), (15, 14 + sw)], (110, 170, 90))
    c.poly([(8, 11), (4, 14 - sw), (7, 14 - sw)], (110, 170, 90))
    c.ellipse(4, 3, 14, 10, (56, 120, 84))
    c.ellipse(5, 4, 12, 7, (86, 156, 100))
    for (x, y) in ((8, 6), (12, 6), (10, 9)):
        c.rect(x, y, 3, 2, (60, 110, 70))
    c.ellipse(17, 5, 6, 5, (130, 190, 100))
    c.px(21, 6, (10, 10, 20))
    c.poly([(3, 7), (0, 9), (3, 10)], (110, 170, 90))
    return c.scaled(4)


def _whale():
    c = Px(64, 24)
    c.ellipse(8, 4, 50, 17, (12, 34, 70))
    c.ellipse(14, 12, 40, 8, (22, 52, 96))
    c.poly([(10, 12), (0, 2), (6, 12), (0, 22)], (12, 34, 70))
    c.poly([(30, 18), (38, 23), (40, 17)], (12, 34, 70))
    c.px(52, 10, (230, 240, 255))
    return c.scaled(6)


def _crab():
    c = Px(16, 10)
    c.ellipse(3, 3, 10, 6, (220, 84, 60))
    c.rect(1, 1, 3, 3, (240, 110, 80))
    c.rect(12, 1, 3, 3, (240, 110, 80))
    for i in range(3):
        c.px(2 - 1, 6 + i // 2, (180, 60, 40))
        c.px(14, 6 + i // 2, (180, 60, 40))
    c.px(5, 3, (255, 255, 255))
    c.px(10, 3, (255, 255, 255))
    return c.scaled(4)


class Creature:
    """Satu makhluk laut dengan posisi dunia kecepatan jenis dan fase animasi."""

    def __init__(self, kind, x, y, vx, phase, variant=0, size=1.0):
        self.kind = kind
        self.x = x
        self.y = y
        self.vx = vx
        self.phase = phase
        self.variant = variant
        self.size = size


class Ocean:
    """Latar laut vertikal yang hidup dari permukaan terang sampai dasar gelap dengan ikan ubur-ubur gelembung sinar cahaya dan rumput laut yang bergerak."""

    def __init__(self, seed=11):
        self.t = 0.0
        self.rs = random.Random(seed)
        self.column = _column()
        self.cache = {}
        self.vig = self._vignette()
        self.snow = [[self.rs.uniform(0, SCREEN_W), self.rs.uniform(0, WORLD_H), self.rs.uniform(1, 3), self.rs.uniform(0.5, 1.0)] for _ in range(260)]
        self.vents = [(240, 14), (780, 12), (1120, 10)]
        self.seabed = Seabed(WORLD_H, self.vents)
        self.creatures = self._populate()
        self.shafts = [(i * 230 - 120 + self.rs.uniform(-30, 30), self.rs.uniform(40, 90), self.rs.uniform(0, 6.28)) for i in range(7)]
        self.rays = pygame.Surface((SCREEN_W, SCREEN_H)).convert()

    def _vignette(self):
        small = pygame.Surface((64, 36), pygame.SRCALPHA)
        for y in range(36):
            for x in range(64):
                d = math.hypot((x - 31.5) / 32, (y - 17.5) / 18)
                a = max(0.0, min(1.0, (d - 0.5) * 1.7))
                small.set_at((x, y), (2, 6, 22, int(a * 200)))
        return pygame.transform.smoothscale(small, (SCREEN_W, SCREEN_H))

    def _populate(self):
        rs = self.rs
        out = []

        def school(kind, pal, y0, y1, n, count, size=1.0):
            for s in range(n):
                cy = rs.uniform(y0, y1)
                cx = rs.uniform(0, SCREEN_W)
                v = rs.choice((-1, 1)) * rs.uniform(26, 60)
                var = rs.randrange(len(pal))
                for k in range(count):
                    out.append(Creature(kind, cx + rs.uniform(-90, 90), cy + rs.uniform(-40, 40), v * rs.uniform(0.9, 1.1), rs.uniform(0, 6.28), (var, pal), size))

        school("fish", SHALLOW, 90, 650, 5, 8)
        school("fish", MIDDLE, 650, 1350, 5, 8)
        school("fish", DEEP, 1350, 2200, 5, 7)
        school("fish", DEEP, 1980, 2300, 3, 7)
        for y in (260, 520):
            out.append(Creature("puffer", rs.uniform(0, SCREEN_W), y, rs.choice((-1, 1)) * 18, rs.uniform(0, 6.28)))
        for y, pal in ((420, SHALLOW), (900, MIDDLE), (1180, MIDDLE), (1560, MIDDLE), (2040, DEEP)):
            out.append(Creature("big", rs.uniform(0, SCREEN_W), y, rs.choice((-1, 1)) * 40, rs.uniform(0, 6.28), (rs.randrange(3), pal)))
        for y in (760, 1040):
            out.append(Creature("turtle", rs.uniform(0, SCREEN_W), y, rs.choice((-1, 1)) * 22, rs.uniform(0, 6.28)))
        for y, col in ((1100, 0), (1300, 1), (1440, 0), (1620, 1), (1760, 0), (2010, 1), (2140, 0), (2240, 1)):
            out.append(Creature("jelly", rs.uniform(0, SCREEN_W), y, rs.uniform(-8, 8), rs.uniform(0, 6.28), col))
        for y in (950, 1500, 2060):
            out.append(Creature("manta", rs.uniform(0, SCREEN_W), y, rs.choice((-1, 1)) * 34, rs.uniform(0, 6.28)))
        for y in (2140, 2270):
            out.append(Creature("angler", rs.uniform(200, SCREEN_W - 200), y, rs.choice((-1, 1)) * 14, rs.uniform(0, 6.28)))
        out.append(Creature("whale", 900, 1880, -10, 0.0))
        out.append(Creature("whale", 300, 1330, 8, 1.0))
        school("fish", DARKFISH, 2040, 2400, 4, 9, 0.67)
        school("fish", SHALLOW, 2400, 2560, 3, 5)
        school("fish", MIDDLE, 2330, 2480, 2, 6)
        out.append(Creature("whale", 560, 2130, 6, 2.0))
        out.append(Creature("manta", 300, 2250, 22, 1.3))
        for x in (140, 330, 520, 760, 960, 1180):
            out.append(Creature("crab", x, 0, rs.choice((-1, 1)) * 12, rs.uniform(0, 6.28)))
        return out

    def update(self, dt):
        self.t += dt
        for c in self.creatures:
            c.x += c.vx * dt
            if c.x > SCREEN_W + 260:
                c.x = -260
            elif c.x < -260:
                c.x = SCREEN_W + 260
        for s in self.snow:
            s[0] += math.sin(self.t * 0.3 + s[2]) * 6 * dt
            s[1] -= 5 * s[3] * dt
            if s[1] < 0:
                s[1] = WORLD_H

    def sprite(self, key, build, flip=False):
        k = (key, flip)
        if k not in self.cache:
            base = self.cache.get((key, False))
            if base is None:
                base = build()
                self.cache[(key, False)] = base
            self.cache[k] = pygame.transform.flip(base, True, False) if flip else base
        return self.cache[k]

    def draw_sky(self, surf, sy, sky):
        h = max(0, int(sy)) + 12
        if sky is not None:
            surf.blit(sky, (0, 0), (0, 0, SCREEN_W, h))
        else:
            surf.fill((14, 24, 70), (0, 0, SCREEN_W, h))

    def draw_waves(self, surf, sy):
        pts = []
        for x in range(0, SCREEN_W + 16, 16):
            pts.append((x, sy + math.sin(x / 70.0 + self.t * 1.6) * 6 + math.sin(x / 31.0 + self.t * 2.3) * 2))
        band = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for k in range(4):
            lp = [(x, y + 8 + k * 14) for x, y in pts]
            pygame.draw.lines(band, (200, 244, 252, 120 - k * 28), False, lp, 3)
        surf.blit(band, (0, 0))
        pygame.draw.lines(surf, (236, 252, 255), False, pts, 4)

    def draw(self, surf, cam, sky=None):
        """Menggambar seluruh laut untuk kamera dengan sumbu y dunia cam di tepi atas layar dan permukaan air berada di y dunia nol."""
        sy = -cam
        top = max(0, int(cam))
        dest = max(0, int(sy))
        h = SCREEN_H - dest
        if sy > 0:
            self.draw_sky(surf, sy, sky)
        if h > 0:
            surf.blit(self.column, (0, dest), (0, top, SCREEN_W, min(h, WORLD_H - top)))
        if -40 < sy < SCREEN_H:
            self.draw_waves(surf, sy)
        if cam < 1500:
            self.draw_rays(surf, cam)
        self.draw_snow(surf, cam)
        vis = [c for c in self.creatures if -200 < c.y - cam < SCREEN_H + 200 and c.kind != "crab"]
        for c in vis:
            if c.kind == "whale":
                self.draw_creature(surf, c, cam)
        near_floor = cam > WORLD_H - SCREEN_H - 700
        if near_floor:
            self.seabed.draw_back(surf, cam, self.t)
        for c in vis:
            if c.kind != "whale":
                self.draw_creature(surf, c, cam)
        if near_floor:
            self.seabed.draw_front(surf, cam, self.t)
            for c in self.creatures:
                if c.kind == "crab":
                    self.draw_creature(surf, c, cam)
        self.draw_bubbles(surf, cam)
        depth = max(0.0, min(1.0, cam / WORLD_H))
        self.vig.set_alpha(int(110 + 120 * depth))
        surf.blit(self.vig, (0, 0))

    def draw_rays(self, surf, cam):
        self.rays.fill((0, 0, 0))
        fade = max(0.0, min(1.0, 1 - cam / 1500))
        for (x0, w, ph) in self.shafts:
            sway = math.sin(self.t * 0.35 + ph) * 40
            for k, length in enumerate((1300, 900, 520)):
                a = int((9 + k * 5) * fade)
                col = (a, int(a * 1.5), int(a * 1.7))
                bot = length - cam
                top = -cam
                pts = [(x0 + sway, top), (x0 + w + sway, top), (x0 + w * 2.6 + sway + 140, bot), (x0 - w * 1.2 + sway + 140, bot)]
                pygame.draw.polygon(self.rays, col, pts)
        surf.blit(self.rays, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def draw_snow(self, surf, cam):
        for x, y, s, par in self.snow:
            sy = y - cam
            if 0 <= sy < SCREEN_H:
                a = int(40 + 70 * par)
                surf.fill((a + 60, a + 90, a + 110), (int(x % SCREEN_W), int(sy), int(s), int(s)))

    def draw_bubbles(self, surf, cam):
        for vi, (vx, n) in enumerate(self.vents):
            for i in range(n):
                v = 60 + (i * 37) % 50
                ph = i * 211.7 + vi * 97
                base = self.seabed.ground(vx) - 36
                y = base - ((self.t * v + ph) % (base + 60))
                sy = y - cam
                if sy < -20 or sy > SCREEN_H + 20:
                    continue
                x = vx + math.sin(self.t * 1.7 + i) * (6 + (base - y) * 0.01) + ((i * 13) % 20 - 10)
                r = 3 + (i * 5) % 6
                pygame.draw.circle(surf, (190, 235, 250), (int(x), int(sy)), r, 1)
                pygame.draw.circle(surf, (240, 252, 255), (int(x - r * 0.35), int(sy - r * 0.35)), max(1, r // 3))

    def draw_creature(self, surf, c, cam):
        sy = c.y - cam
        t = self.t
        if c.kind == "fish":
            var, pal = c.variant
            img = self.sprite(("fish", id(pal), var), lambda: _fish_small(pal[var]), c.vx < 0)
            bob = math.sin(t * 2 + c.phase) * 5
            if c.size != 1.0:
                img = self.sprite(("fish", id(pal), var, c.size), lambda: _fish_small(pal[var], max(1, int(round(3 * c.size)))), c.vx < 0)
            surf.blit(img, (c.x - img.get_width() // 2, sy + bob))
        elif c.kind == "big":
            var, pal = c.variant
            img = self.sprite(("big", id(pal), var), lambda: _fish_big(pal[var]), c.vx < 0)
            surf.blit(img, (c.x - img.get_width() // 2, sy + math.sin(t + c.phase) * 8))
        elif c.kind == "puffer":
            img = self.sprite("puffer", _puffer, c.vx < 0)
            k = 1 + 0.04 * math.sin(t * 3 + c.phase)
            img = pygame.transform.scale(img, (int(img.get_width() * k), int(img.get_height() * k)))
            surf.blit(img, (c.x - img.get_width() // 2, sy + math.sin(t + c.phase) * 6))
        elif c.kind == "turtle":
            f = int(t * 2 + c.phase) % 2
            img = self.sprite(("turtle", f), lambda: _turtle(f), c.vx < 0)
            surf.blit(img, (c.x - img.get_width() // 2, sy + math.sin(t * 0.8 + c.phase) * 10))
        elif c.kind == "manta":
            f = int(t * 5 + c.phase * 2) % 6
            img = self.sprite(("manta", f), lambda: _manta(f), c.vx < 0)
            surf.blit(img, (c.x - img.get_width() // 2, sy + math.sin(t * 0.7 + c.phase) * 12))
        elif c.kind == "jelly":
            f = int(t * 2.4 + c.phase) % 4
            col = ((255, 140, 200), (120, 230, 255))[c.variant]
            img = self.sprite(("jelly", c.variant, f), lambda: _jelly(col, f))
            cy = sy + math.sin(t * 1.1 + c.phase) * 24
            g = radial_glow(64, col, 0.5)
            surf.blit(g, g.get_rect(center=(c.x, cy + 30)), special_flags=pygame.BLEND_RGB_ADD)
            img = img.copy()
            img.set_alpha(215)
            surf.blit(img, (c.x - img.get_width() // 2, cy))
        elif c.kind == "angler":
            img = self.sprite("angler", _angler, c.vx < 0)
            cy = sy + math.sin(t * 0.9 + c.phase) * 10
            surf.blit(img, (c.x - img.get_width() // 2, cy))
            lx = c.x - img.get_width() // 2 + (14 if c.vx < 0 else 106)
            g = radial_glow(70, (255, 240, 140), 0.6 + 0.3 * math.sin(t * 4 + c.phase))
            surf.blit(g, g.get_rect(center=(lx, cy + 18)), special_flags=pygame.BLEND_RGB_ADD)
        elif c.kind == "whale":
            img = self.sprite("whale", _whale, c.vx < 0)
            img = img.copy()
            img.set_alpha(70)
            surf.blit(img, (c.x - img.get_width() // 2, sy + math.sin(t * 0.3 + c.phase) * 14))
        elif c.kind == "crab":
            img = self.sprite("crab", _crab, c.vx < 0)
            c.x = max(40, min(SCREEN_W - 40, c.x))
            if c.x <= 40 or c.x >= SCREEN_W - 40:
                c.vx = -c.vx
            gy = self.seabed.ground(c.x) - cam - 34
            surf.blit(img, (c.x - img.get_width() // 2, gy + abs(math.sin(t * 3 + c.phase)) * -3))
