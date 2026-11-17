import math
import random
import pygame
from .base import Scene
from .. import ui, icons, pixelfont, art_items, art_rooms
from ..canvas import radial_glow
from ..effects import MoneyRain
from .. import config as C


class WinScene(Scene):
    """Ending menang dengan hujan uang notifikasi transfer kripto di layar komputer dan banner misi berhasil."""

    hud = "money"
    exit_kind = "story"

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.rain = MoneyRain(64, 3)
        self.mon, self.scr_local = art_rooms.pixel_monitor(660, 372)
        self.mon_pos = (C.BASE_W // 2 - self.mon.get_width() // 2, 176)
        self.scr = self.scr_local.move(self.mon_pos)
        self.bg = pygame.Surface((C.BASE_W, C.BASE_H))
        for y in range(C.BASE_H):
            t = y / C.BASE_H
            self.bg.fill((int(22 + 40 * t), int(10 + 16 * t), int(70 + 60 * t)), (0, y, C.BASE_W, 1))
        g = radial_glow(520, (120, 70, 220), 0.5)
        self.bg.blit(pygame.transform.scale(g, (1300, 800)), (-10, -40), special_flags=pygame.BLEND_RGB_ADD)
        self.aero = pygame.transform.smoothscale(app.assets.get("aero"), self.scr.size)
        self.gain = app.session.wins * C.REWARD
        self.btn = ui.Button((C.BASE_W // 2 - 150, C.BASE_H - 62, 300, 48), "Continue", self.go_stats, "primary", icon=icons.icon_fn("play"), size=19)
        self.btn.visible = False
        self.btn.pulse = True
        self.toasts = [(1.0 + i * 0.7) for i in range(app.session.wins)]
        self.coin_clock = 0.0
        self.hash = "0x9b2d7f31c8a4e5106ad3"

    music_level = 0.4

    def enter(self):
        self.app.sfx.play("win", 0.7)

    def backdrop_art(self):
        return self.bg

    def go_stats(self):
        from .verify import BuildingScene
        self.app.goto(lambda: BuildingScene(self.app))

    def event(self, e):
        if self.btn.visible:
            self.btn.handle_event(e, self.app)
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.app.sfx.play("click")
                self.go_stats()

    def update(self, dt):
        self.t += dt
        self.rain.update(dt)
        self.coin_clock += dt
        if self.coin_clock > 1.6 and self.t < 5:
            self.coin_clock = 0.0
            self.app.sfx.play("coin", 0.45)
        self.btn.visible = self.t > 3.0
        self.btn.update(dt, self.app.mouse)

    def draw_rays(self, surf):
        cx, cy = C.BASE_W // 2, 420
        n = 18
        for i in range(n):
            a = self.t * 0.25 + i * math.tau / n
            w = 0.09
            pts = [(cx, cy), (cx + math.cos(a - w) * 1000, cy + math.sin(a - w) * 1000), (cx + math.cos(a + w) * 1000, cy + math.sin(a + w) * 1000)]
            if i % 2 == 0:
                ov = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
                pygame.draw.polygon(ov, (255, 230, 140, 22), pts)
                surf.blit(ov, (0, 0))

    def draw_wallet(self, surf):
        scr = self.scr
        old = surf.get_clip()
        surf.set_clip(scr)
        surf.blit(self.aero, scr.topleft)
        w = pygame.Rect(scr.x + 34, scr.y + 18, scr.w - 68, scr.h - 60)
        cl = ui.draw_window(surf, w, "CryptoWallet - Dompet Digital", tint=(60, 120, 190), icon=lambda s, c, z, col: icons.draw_icon(s, "lock", c, z, (255, 255, 255)))
        pygame.draw.rect(surf, (245, 250, 255), cl)
        k = min(1.0, max(0.0, (self.t - 0.4) / 0.4))
        pop = 1 + 2.0 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2
        cc = (cl.x + 70, cl.y + 78)
        r = int(48 * pop)
        if r > 2:
            pygame.draw.circle(surf, (30, 130, 70), cc, r + 4)
            pygame.draw.circle(surf, (70, 200, 110), cc, r)
            pygame.draw.circle(surf, (150, 235, 170), (cc[0] - r // 4, cc[1] - r // 4), r // 2)
            icons.draw_icon(surf, "check", cc, int(r * 1.2), (255, 255, 255))
        ui.draw_text(surf, "INCOMING TRANSFER", ui.font(24, True), (28, 130, 70), (cl.x + 140, cl.y + 20))
        val = pixelfont.render(f"+${self.gain} USDT", 5, grad=((255, 232, 120), (240, 170, 30)), outline=(100, 60, 0), shadow=(1, 1, (60, 30, 0)))
        surf.blit(val, (cl.x + 134, cl.y + 50))
        rows = (("From", "YuBeatEm Treasury  (0x7f3a...c91e)"), ("To", "Anonymous Wallet  (" + self.hash[:6] + "..." + self.hash[-4:] + ")"), ("Confirmations", "12/12 network blocks"))
        for i, (a, b) in enumerate(rows):
            y = cl.y + 138 + i * 28
            ui.draw_text(surf, a, ui.font(15, True), (80, 96, 124), (cl.x + 28, y))
            ui.draw_text(surf, b, ui.font(15), (30, 40, 64), (cl.x + 130, y))
        bar = pygame.Rect(cl.x + 28, cl.bottom - 36, cl.w - 56, 14)
        pygame.draw.rect(surf, (214, 224, 238), bar, border_radius=7)
        fw = int(bar.w * min(1.0, max(0.0, (self.t - 0.6) / 1.2)))
        if fw > 4:
            pygame.draw.rect(surf, (60, 190, 90), (bar.x, bar.y, fw, bar.h), border_radius=7)
            pygame.draw.rect(surf, (150, 235, 160), (bar.x, bar.y, fw, bar.h // 2), border_radius=7)
        pygame.draw.rect(surf, (130, 150, 180), bar, 1, border_radius=7)
        tb = pygame.Rect(scr.x, scr.bottom - 30, scr.w, 30)
        surf.blit(ui.glass(tb.w, tb.h, 0, (20, 40, 70), 235, True, False), tb)
        ui.draw_text(surf, "Crypto transfers are hard to trace, which is why scammers love them.", ui.font(13), (210, 228, 250), (tb.centerx, tb.centery), "center")
        surf.set_clip(old)

    def draw_toasts(self, surf):
        for i, t0 in enumerate(self.toasts):
            age = self.t - t0
            if age < 0:
                continue
            k = min(1.0, age / 0.35)
            ease = 1 - (1 - k) ** 3
            w, h = 262, 62
            x = C.BASE_W + 10 - (w + 24) * ease
            y = 176 + i * 74
            card = pygame.Surface((w, h), pygame.SRCALPHA)
            card.blit(ui.glass(w, h, 10, (230, 242, 255), 236, False), (0, 0))
            pygame.draw.rect(card, (50, 190, 90), (0, 0, 8, h), border_top_left_radius=10, border_bottom_left_radius=10)
            bill = art_items.banknote(2)
            card.blit(bill, (18, 12))
            ui.draw_text(card, "Balance increased", ui.font(13), (60, 80, 110), (92, 10))
            ui.draw_text(card, f"+${C.REWARD}", ui.font(22, True), (28, 130, 70), (92, 26))
            surf.blit(card, (x, y))

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        self.draw_rays(surf)
        self.rain.draw(surf, False)
        surf.blit(self.mon, self.mon_pos)
        self.draw_wallet(surf)
        g = radial_glow(380, (90, 160, 255), 0.22)
        surf.blit(pygame.transform.scale(g, (1000, 640)), g.get_rect(center=(C.BASE_W // 2, 420)).move(-60, -30), special_flags=pygame.BLEND_RGB_ADD)
        k = min(1.0, self.t / 0.5)
        pop = 1 + 2.4 * (k - 1) ** 3 + 1.4 * (k - 1) ** 2
        title = pixelfont.render("MISI BERHASIL!", 8, grad=((255, 250, 190), (255, 190, 40)), outline=(110, 40, 0), shadow=(1, 1, (60, 20, 0)))
        title = pygame.transform.scale(title, (max(1, int(title.get_width() * pop)), max(1, int(title.get_height() * pop))))
        surf.blit(title, title.get_rect(center=(C.BASE_W // 2, 98 + math.sin(self.t * 3) * 3)))
        sub = pygame.Rect(0, 0, 500, 36)
        sub.center = (C.BASE_W // 2, 160)
        surf.blit(ui.glass(sub.w, sub.h, 10, (90, 70, 190), 190), sub)
        ui.draw_text(surf, f"You fooled the AI {self.app.session.wins} of {C.TOTAL_ROUNDS} times!", ui.font(18, True), (255, 255, 255), sub.center, "center", shadow=(20, 10, 60))
        self.rain.draw(surf, True)
        self.draw_toasts(surf)
        self.btn.draw(surf)
