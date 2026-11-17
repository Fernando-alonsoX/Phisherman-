import math
import random
import pygame
from .base import Scene
from .. import ui, pixelfont, art_items, art_rooms, art_char, icons
from ..canvas import radial_glow, Px
from .. import config as C

SLIDES = [
    {
        "expr": "tired",
        "pose": "sit",
        "light": ((120, 160, 255), 0.16),
        "text": "Namaku {name}. Sudah dua tahun aku menganggur sejak pabrik tempatku bekerja tutup. Tagihan listrik menumpuk dan pinjol terus meneror tiap jam. Isi rekeningku tinggal lima dolar.",
        "mood": 70,
    },
    {
        "expr": "wide",
        "pose": "aha",
        "light": None,
        "text": "Tunggu... AHA! Aku punya ide. YuBeatEm, perusahaan besar yang emailnya dijaga sistem AI. Kalau emailku bisa menipu AI itu, uang mereka bisa mengalir ke dompet digitalku!",
        "mood": 0,
    },
    {
        "expr": "smirk",
        "pose": "type",
        "light": ((90, 200, 255), 0.14),
        "text": "Rencananya: tulis lima email jebakan. Tiap email yang lolos dari AI bernilai seratus dolar. Kalau gagal tiga kali, polisi siber akan melacakku. Ini bukan hal yang baik, tapi aku sudah kehabisan pilihan.",
        "mood": 30,
    },
]

BOX = pygame.Rect(236, 470, 808, 218)


class CutsceneScene(Scene):
    """Cutscene pembuka Story Mode di kamar kumuh dengan tiga ilustrasi berganti PC desktop textbox typewriter potret bulat dan tombol play."""

    hud = "money"
    exit_kind = "story"

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.idx = 0
        self.name = app.player_name or "Pemain"
        self.room = app.assets.get("slum_room")
        base = radial_glow(300, (255, 208, 110), 0.55)
        self.glows = []
        for k in (120, 165, 210, 255):
            g = base.copy()
            g.fill((k, k, k, 255), special_flags=pygame.BLEND_RGB_MULT)
            self.glows.append(g)
        self.vignette = self._vignette()
        rs = random.Random(5)
        self.rain = [[rs.randrange(166, 394), rs.randrange(102, 318), 220 + rs.random() * 160] for _ in range(46)]
        self.flash = 0.0
        self.slide_t = 0.0
        self.tw = None
        self.play_t = 0.0
        self.font = ui.font(22)
        self.laptop = self._desktop()
        self.hacker_back = art_char.back_view_hacker("type")
        self.env = art_rooms._mini_envelope()
        self.start_slide()

    def _vignette(self):
        small = pygame.Surface((64, 36), pygame.SRCALPHA)
        for y in range(36):
            for x in range(64):
                d = math.hypot((x - 31.5) / 32, (y - 17.5) / 18)
                a = max(0.0, min(1.0, (d - 0.55) * 1.9))
                small.set_at((x, y), (4, 6, 18, int(a * 190)))
        return pygame.transform.smoothscale(small, (C.BASE_W, C.BASE_H))

    def _desktop(self):
        c = Px(88, 58)
        c.rect(0, 0, 64, 48, (20, 22, 30))
        c.rect(1, 1, 62, 46, (52, 56, 72))
        c.rect(3, 3, 58, 42, (6, 10, 24))
        c.vgrad(3, 3, 58, 42, (8, 24, 58), (6, 12, 34))
        for x in range(3, 61, 4):
            c.rect(x, 3, 1, 42, (10, 30, 66))
        pts = [(9, 14), (15, 14), (18, 8), (22, 20), (26, 12), (30, 14), (37, 14)]
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1], b[0], b[1], (60, 220, 240))
        for i, ch in enumerate("YUBEATEM"):
            pixelfont.stamp(c, ch, 8 + i * 6, 25, (255, 255, 255))
        c.rect(8, 36, 48, 5, (10, 40, 30))
        c.rect(9, 37, 22, 3, (60, 220, 120))
        c.rect(28, 48, 8, 6, (84, 88, 104))
        c.rect(18, 54, 28, 3, (130, 134, 150))
        c.rect(18, 57, 28, 1, (60, 64, 80))
        c.rect(68, 8, 19, 50, (30, 34, 46))
        c.rect(69, 9, 17, 48, (74, 80, 100))
        c.rect(69, 9, 17, 2, (120, 128, 150))
        c.rect(71, 14, 13, 3, (24, 28, 38))
        c.rect(71, 20, 13, 3, (24, 28, 38))
        c.circle(77, 40, 3, (36, 40, 52))
        c.circle(77, 40, 1, (60, 230, 120))
        c.rect(70, 53, 15, 2, (40, 44, 58))
        return c.scaled(3)

    def start_slide(self):
        s = SLIDES[self.idx]
        self.slide_t = 0.0
        self.tw = ui.Typewriter(s["text"].format(name=self.name), self.font, BOX.w - 214, (30, 36, 52), cps=34, on_tick=lambda: self.app.sfx.play("type"))
        self.play_t = 0.0
        if self.idx == 1:
            self.app.sfx.play("aha")
        elif self.idx > 0:
            self.app.sfx.play("pop")

    def backdrop_art(self):
        return self.room

    def next_slide(self):
        self.flash = 1.0
        if self.idx + 1 >= len(SLIDES):
            self.app.goto(lambda: self.make_compose())
            return
        self.idx += 1
        self.start_slide()

    def make_compose(self):
        from .tutorial import TutorialScene
        return TutorialScene(self.app)

    def play_rect(self):
        return pygame.Rect(0, 0, 60, 60).move(BOX.right - 82, BOX.bottom - 82)

    def event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.tw.finished and self.play_rect().collidepoint(e.pos):
                self.app.sfx.play("click")
                self.next_slide()
            elif BOX.collidepoint(e.pos) and not self.tw.finished:
                self.tw.skip()
        elif e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            if self.tw.finished:
                self.app.sfx.play("click")
                self.next_slide()
            else:
                self.tw.skip()

    def update(self, dt):
        self.t += dt
        self.slide_t += dt
        self.flash = max(0.0, self.flash - dt * 2.6)
        self.tw.update(dt)
        if self.tw.finished:
            self.play_t += dt
            if self.play_rect().collidepoint(self.app.mouse):
                ui.HOT["hand"] = True
        for r in self.rain:
            r[0] -= r[2] * dt * 0.12
            r[1] += r[2] * dt
            if r[1] > 318 or r[0] < 166:
                r[0] = random.randrange(180, 394)
                r[1] = 102

    def flicker_idx(self):
        if self.idx == 0:
            v = math.sin(self.t * 17) * math.sin(self.t * 5.3) + math.sin(self.t * 31) * 0.4
            return 0 if v > 0.95 else (1 if v > 0.3 else 2)
        return 3 if self.idx == 1 else 2

    def draw_rain(self, surf):
        clip = surf.get_clip()
        surf.set_clip(pygame.Rect(166, 102, 228, 216))
        for x, y, v in self.rain:
            pygame.draw.line(surf, (150, 185, 235), (x, y), (x - 6, y + 14), 2)
        surf.set_clip(clip)

    def draw_phone(self, surf):
        px, py = 262, 342
        r = pygame.Rect(0, 0, 36, 58)
        r.midtop = (px, py)
        pygame.draw.rect(surf, (10, 10, 14), r, border_radius=6)
        scr = r.inflate(-6, -8)
        pygame.draw.rect(surf, (200, 226, 255), scr, border_radius=4)
        pygame.draw.rect(surf, (230, 60, 54), (scr.x, scr.y, scr.w, 12), border_top_left_radius=4, border_top_right_radius=4)
        for i in range(3):
            pygame.draw.rect(surf, (120, 140, 180), (scr.x + 4, scr.y + 18 + i * 9, scr.w - 8 - i * 4, 4))
        glow = radial_glow(70, (150, 190, 255), 0.5)
        surf.blit(glow, glow.get_rect(center=r.center), special_flags=pygame.BLEND_RGB_ADD)
        for (hx, hy) in ((px - 14, py + 48), (px + 14, py + 48)):
            pygame.draw.rect(surf, (208, 154, 114), (hx - 5, hy - 4, 10, 8))

    def draw_notifs(self, surf):
        items = (("PINJOL CEPAT", "Jatuh tempo hari ini. Segera bayar!", (230, 70, 60), 0.9),
                 ("PLN", "Tagihan listrik 3 bulan belum dibayar", (240, 150, 40), 1.9),
                 ("Saldo Rekening", "Tersisa $5", (90, 130, 190), 2.9))
        for i, (title, body, col, t0) in enumerate(items):
            k = (self.slide_t - t0) / 0.35
            if k <= 0:
                continue
            k = min(1.0, k)
            ease = 1 + 2.0 * (k - 1) ** 3 + 1.0 * (k - 1) ** 2
            w, h = 290, 58
            card = pygame.Surface((w, h), pygame.SRCALPHA)
            card.blit(ui.glass(w, h, 10, (230, 240, 255), 230, False), (0, 0))
            pygame.draw.rect(card, col, (0, 0, 8, h), border_top_left_radius=10, border_bottom_left_radius=10)
            icons.draw_icon(card, "warning", (30, h // 2), 22, col)
            ui.draw_text(card, title, ui.font(14, True), (30, 40, 70), (50, 9))
            ui.draw_text(card, body, ui.font(13), (60, 70, 96), (50, 30))
            sc = max(0.05, ease)
            card = pygame.transform.smoothscale(card, (int(w * sc), int(h * sc)))
            card.set_alpha(int(255 * min(1.0, k * 2)))
            bob = math.sin(self.t * 2 + i) * 3
            surf.blit(card, (400, 238 + i * 66 + bob))

    def draw_aha(self, surf):
        cx, cy = 640, 170
        k = min(1.0, self.slide_t / 0.4)
        rays = 14
        for i in range(rays):
            a = self.t * 0.6 + i * math.tau / rays
            r1 = 52
            r2 = 52 + 80 * k * (0.7 + 0.3 * math.sin(self.t * 6 + i))
            pygame.draw.line(surf, (255, 240, 140), (cx + math.cos(a) * r1, cy + math.sin(a) * r1), (cx + math.cos(a) * r2, cy + math.sin(a) * r2), 6)
            pygame.draw.line(surf, (255, 255, 230), (cx + math.cos(a) * r1, cy + math.sin(a) * r1), (cx + math.cos(a) * (r2 - 18), cy + math.sin(a) * (r2 - 18)), 2)
        g = radial_glow(190, (255, 230, 120), 0.8)
        surf.blit(g, g.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_RGB_ADD)

    def draw_burst(self, surf):
        k = min(1.0, max(0.0, (self.slide_t - 0.12) / 0.3))
        if k <= 0:
            return
        sc = (1 + 2.4 * (k - 1) ** 3 + 1.6 * (k - 1) ** 2) * (1 + 0.04 * math.sin(self.t * 8))
        cx, cy = 872, 150
        pts = []
        for i in range(24):
            a = i * math.tau / 24 + 0.1
            r = (96 if i % 2 == 0 else 58) * sc
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.8))
        pygame.draw.polygon(surf, (120, 20, 20), [(x + 4, y + 5) for x, y in pts])
        pygame.draw.polygon(surf, (255, 214, 60), pts)
        pygame.draw.polygon(surf, (255, 120, 40), pts, 4)
        t = pixelfont.render("AHA!", 7, grad=((255, 255, 255), (255, 240, 150)), outline=(160, 30, 20), shadow=(1, 1, (80, 10, 10)))
        t = pygame.transform.rotate(t, 6)
        t = pygame.transform.smoothscale(t, (max(1, int(t.get_width() * sc)), max(1, int(t.get_height() * sc))))
        surf.blit(t, t.get_rect(center=(cx, cy)))

    def draw_slide(self, surf):
        s = SLIDES[self.idx]
        man = self.app.assets.man(s["pose"], s["expr"], s["light"])
        if self.idx == 0:
            y = 141
            bob = math.sin(self.t * 1.4) * 2
            surf.blit(man, (118, y + bob))
            self.draw_phone(surf)
            self.draw_notifs(surf)
        elif self.idx == 1:
            self.draw_aha(surf)
            y = 132 + abs(math.sin(self.slide_t * 7)) * -6 * max(0.0, 1 - self.slide_t)
            surf.blit(man, (496, y))
            surf.blit(self.laptop, (852, 183))
            k = (self.t * 1.6) % 1.0
            cx, cy = 948, 243
            for j in range(3):
                kk = (k + j / 3.0) % 1.0
                pygame.draw.circle(surf, (255, 70, 70), (cx, cy), int(10 + kk * 52), 2)
            pygame.draw.line(surf, (255, 70, 70), (cx - 70, cy), (cx + 70, cy), 1)
            pygame.draw.line(surf, (255, 70, 70), (cx, cy - 56), (cx, cy + 56), 1)
            gl = radial_glow(150, (40, 160, 230), 0.4)
            surf.blit(gl, gl.get_rect(center=(948, 263)), special_flags=pygame.BLEND_RGB_ADD)
            self.draw_burst(surf)
        else:
            surf.blit(self.laptop, (880, 189))
            gl = radial_glow(190, (60, 180, 255), 0.5)
            surf.blit(gl, gl.get_rect(center=(976, 261)), special_flags=pygame.BLEND_RGB_ADD)
            surf.blit(self.hacker_back, (886, 176 + math.sin(self.t * 5) * 1.5))
            for i in range(5):
                ph = self.t * 0.9 + i * 0.37
                k = ph % 1.0
                x = 924 + i * 24 + math.sin(ph * 5) * 10
                y = 215 - k * 130
                img = pygame.transform.scale(self.env, (self.env.get_width() * 2, self.env.get_height() * 2))
                img = img.copy()
                img.set_alpha(int(255 * min(1.0, k * 5) * (1 - k * 0.6)))
                surf.blit(img, (x, y))
            ui.draw_text(surf, "5x EMAIL", ui.font(20, True), (255, 226, 100), (1112, 150), "midtop", shadow=(0, 0, 0))

    def draw_box(self, surf):
        sh = pygame.Surface((BOX.w + 40, BOX.h + 40), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 70), (20, 28, BOX.w, BOX.h), border_radius=22)
        surf.blit(sh, (BOX.x - 20, BOX.y - 20))
        panel = ui.glass(BOX.w, BOX.h, 20, (190, 220, 252), 232, True)
        surf.blit(panel, BOX)
        pygame.draw.rect(surf, (255, 255, 255), BOX.inflate(-8, -8), 1, border_radius=17)
        tag = pygame.Rect(BOX.x + 96, BOX.y - 16, 110, 32)
        pygame.draw.rect(surf, (20, 40, 84), tag, border_radius=10)
        pygame.draw.rect(surf, (255, 206, 80), tag, 2, border_radius=10)
        ui.draw_text(surf, self.name.upper(), ui.font(18, True), (255, 226, 120), tag.center, "center")
        self.tw.draw(surf, (BOX.x + 106, BOX.y + 28))
        s = SLIDES[self.idx]
        por = self.app.assets.portrait(s["expr"], 120)
        c = (BOX.x + 28, BOX.bottom - 46)
        pr = por.get_rect(center=c)
        shd = pygame.Surface((132, 132), pygame.SRCALPHA)
        pygame.draw.circle(shd, (0, 0, 0, 80), (66, 70), 62)
        surf.blit(shd, shd.get_rect(center=(c[0], c[1] + 6)))
        surf.blit(por, pr)
        if self.tw.finished:
            pr2 = self.play_rect()
            hover = pr2.collidepoint(self.app.mouse)
            pulse = 0.5 + 0.5 * math.sin(self.play_t * 5)
            ring = pygame.Surface((110, 110), pygame.SRCALPHA)
            pygame.draw.circle(ring, (120, 190, 255, int(60 + 80 * pulse)), (55, 55), int(32 + 14 * pulse), 4)
            surf.blit(ring, ring.get_rect(center=pr2.center))
            k = min(1.0, self.play_t / 0.25)
            d = int(60 * (1 + 0.1 * (1 if hover else 0)) * (0.6 + 0.4 * k))
            img = ui.button_surface(60, 60, "primary", "hover" if hover else "normal", 30)
            img = pygame.transform.smoothscale(img, (d, d))
            surf.blit(img, img.get_rect(center=pr2.center))
            icons.draw_icon(surf, "play", (pr2.centerx + 2, pr2.centery), int(32 * k + 4), (255, 255, 255))

    def draw(self, surf):
        s = SLIDES[self.idx]
        surf.blit(self.room, (0, 0))
        g = self.glows[self.flicker_idx()]
        surf.blit(g, g.get_rect(center=(640, 168)), special_flags=pygame.BLEND_RGB_ADD)
        self.draw_rain(surf)
        self.draw_slide(surf)
        if s["mood"]:
            dark = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
            dark.fill((6, 10, 30, s["mood"]))
            surf.blit(dark, (0, 0))
        surf.blit(self.vignette, (0, 0))
        self.draw_box(surf)
        if self.flash > 0:
            f = pygame.Surface((C.BASE_W, C.BASE_H))
            f.fill((255, 255, 255))
            f.set_alpha(int(200 * self.flash))
            surf.blit(f, (0, 0))
