import math
import random
import pygame
from .base import Scene
from .. import ui, icons, pixelfont, art_items
from ..canvas import radial_glow
from .. import config as C

CAPTION = "Polisi siber melacak jejak digitalmu. Kamu ditangkap karena penipuan online. Sekarang tidak ada lagi uang, hanya jeruji besi."


class LoseScene(Scene):
    """Ending kalah berupa ilustrasi penjara dengan jeruji turun lalu transisi shutter menuju layar GAME OVER."""

    hud = "money"
    exit_kind = "story"

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.phase = "cell"
        self.phase_t = 0.0
        self.room = app.assets.get("prison_room")
        self.bars = app.assets.get("prison_bars")
        self.man = app.assets.man("huddle", "cry")
        self.tw = None
        self.clang = False
        self.shake = 0.0
        self.btn = ui.Button((C.BASE_W // 2 - 150, C.BASE_H - 78, 300, 50), "Continue", self.go_stats, "primary", icon=icons.icon_fn("play"), size=19)
        self.btn.visible = False
        self.btn.pulse = True
        self.go_t = 0.0
        g = radial_glow(300, (255, 40, 40), 0.7)
        b = radial_glow(300, (40, 80, 255), 0.7)
        self.red, self.blue = g, b
        self.vig = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
        for i in range(60):
            a = int(150 * (1 - i / 60) ** 2)
            pygame.draw.rect(self.vig, (90, 0, 0, a), (i * 3, i * 3, C.BASE_W - i * 6, C.BASE_H - i * 6), 3)
        self.rs = random.Random(3)
        self.scan = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
        for y in range(0, C.BASE_H, 4):
            pygame.draw.line(self.scan, (0, 0, 0, 70), (0, y), (C.BASE_W, y))

    music_level = 0.0

    def enter(self):
        self.app.sfx.play("alarm")

    def backdrop_art(self):
        return self.room

    def go_stats(self):
        from .verify import BuildingScene
        self.app.goto(lambda: BuildingScene(self.app))

    def set_phase(self, name):
        self.phase = name
        self.phase_t = 0.0

    def event(self, e):
        if self.phase == "over" and self.btn.visible:
            self.btn.handle_event(e, self.app)
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.app.sfx.play("click")
                self.go_stats()
        elif self.phase == "cell" and self.tw and e.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
            if not self.tw.finished:
                self.tw.skip()
            elif e.type == pygame.MOUSEBUTTONDOWN or e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.set_phase("close")
                self.app.sfx.play("whoosh")

    def update(self, dt):
        self.t += dt
        self.phase_t += dt
        self.shake = max(0.0, self.shake - dt * 3)
        if self.phase == "cell":
            if self.t > 0.9 and not self.clang:
                self.clang = True
                self.shake = 1.0
                self.app.sfx.play("clang")
            if self.t > 2.0 and self.tw is None:
                self.tw = ui.Typewriter(CAPTION, ui.font(22), 760, (235, 240, 250), cps=30, on_tick=lambda: self.app.sfx.play("type"))
            if self.tw:
                self.tw.update(dt)
                if self.tw.finished and self.phase_t > 9.5:
                    self.set_phase("close")
                    self.app.sfx.play("whoosh")
        elif self.phase == "close":
            if self.phase_t > 0.9:
                self.set_phase("over")
                self.app.sfx.play("lose")
        elif self.phase == "over":
            self.go_t += dt
            self.btn.visible = self.phase_t > 2.2
            self.btn.update(dt, self.app.mouse)

    def bars_y(self):
        if self.t < 0.5:
            return -C.BASE_H
        k = min(1.0, (self.t - 0.5) / 0.4)
        y = -C.BASE_H * (1 - k * k)
        if k >= 1.0:
            kk = min(1.0, (self.t - 0.9) / 0.4)
            y = -math.sin(kk * math.pi) * 22 * (1 - kk)
        return y

    def draw_cell(self, surf):
        sx = int(math.sin(self.t * 60) * 7 * self.shake)
        sy = int(math.cos(self.t * 53) * 5 * self.shake)
        layer = pygame.Surface((C.BASE_W, C.BASE_H))
        layer.blit(self.room, (0, 0))
        man = self.man
        layer.blit(man, (496, 165 + math.sin(self.t * 1.5) * 2))
        wob = 0.5 + 0.5 * math.sin(self.t * 9)
        if self.t < 6:
            k = max(0.0, 1 - self.t / 6)
            r = pygame.transform.scale(self.red, (800, 520))
            b = pygame.transform.scale(self.blue, (800, 520))
            r.fill((int(255 * wob * k),) * 3, special_flags=pygame.BLEND_RGB_MULT)
            b.fill((int(255 * (1 - wob) * k),) * 3, special_flags=pygame.BLEND_RGB_MULT)
            layer.blit(r, (900, -120), special_flags=pygame.BLEND_RGB_ADD)
            layer.blit(b, (-120, -100), special_flags=pygame.BLEND_RGB_ADD)
        moon = radial_glow(260, (120, 160, 255), 0.35)
        layer.blit(moon, (1000 - 130, 120 - 130), special_flags=pygame.BLEND_RGB_ADD)
        by = self.bars_y()
        layer.blit(self.bars, (0, by))
        dark = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
        dark.fill((4, 6, 20, 70))
        layer.blit(dark, (0, 0))
        layer.blit(self.vig, (0, 0))
        surf.blit(layer, (sx, sy))
        if self.tw:
            box = pygame.Rect(0, 0, 820, 108)
            box.midbottom = (C.BASE_W // 2, C.BASE_H - 26)
            surf.blit(ui.glass(box.w, box.h, 16, (20, 30, 56), 220), box)
            self.tw.draw(surf, (box.x + 30, box.y + 18))
            if self.tw.finished:
                a = 0.5 + 0.5 * math.sin(self.t * 5)
                icons.draw_icon(surf, "play", (box.right - 34, box.bottom - 30), 22 + int(4 * a), (200, 225, 255))

    def draw_over(self, surf):
        surf.fill((6, 0, 2))
        g = radial_glow(420, (180, 20, 20), 0.5)
        surf.blit(pygame.transform.scale(g, (1280, 800)), (0, -40), special_flags=pygame.BLEND_RGB_ADD)
        k = min(1.0, self.phase_t / 0.5)
        pop = 1 + 3.0 * (k - 1) ** 3 + 2.0 * (k - 1) ** 2
        sc = 1 + (1 - min(1.0, pop)) * 1.2
        shake = max(0.0, 1 - self.phase_t * 2.2)
        for i, word in enumerate(("GAME", "OVER")):
            delay = i * 0.3
            kk = max(0.0, min(1.0, (self.phase_t - delay) / 0.45))
            if kk <= 0:
                continue
            e = 1 + 2.4 * (kk - 1) ** 3 + 1.4 * (kk - 1) ** 2
            s = 1 + (1 - min(1.0, e)) * 1.3
            img = pixelfont.render(word, 17, grad=((255, 210, 200), (230, 30, 30)), outline=(40, 0, 0), shadow=(1, 1, (90, 0, 0)))
            img = pygame.transform.scale(img, (max(1, int(img.get_width() * s)), max(1, int(img.get_height() * s))))
            ox = int(math.sin(self.phase_t * 70 + i) * 8 * shake)
            gl = self.rs.random() < 0.05
            r = img.get_rect(center=(C.BASE_W // 2 + ox, 210 + i * 170))
            if gl:
                ch = img.copy()
                ch.fill((0, 255, 255), special_flags=pygame.BLEND_RGB_MULT)
                surf.blit(ch, r.move(10, 0))
            surf.blit(img, r)
        if self.phase_t > 1.0:
            a = min(1.0, (self.phase_t - 1.0) / 0.6)
            sub = ui.text_surf(ui.font(22, True), "You failed to fool the AI.", (255, 220, 215)).copy()
            sub.set_alpha(int(255 * a))
            surf.blit(sub, sub.get_rect(center=(C.BASE_W // 2, 540)))
            sub2 = ui.text_surf(ui.font(16), "Remember: real-world phishing is a cybercrime. This is only a learning simulation.", (200, 160, 160)).copy()
            sub2.set_alpha(int(255 * a))
            surf.blit(sub2, sub2.get_rect(center=(C.BASE_W // 2, 580)))
        surf.blit(self.scan, (0, 0))
        self.btn.draw(surf)

    def draw(self, surf):
        if self.phase == "over":
            self.draw_over(surf)
            return
        self.draw_cell(surf)
        if self.phase == "close":
            k = min(1.0, self.phase_t / 0.8)
            h = int(C.BASE_H / 2 * (k * k * (3 - 2 * k)))
            pygame.draw.rect(surf, (6, 0, 2), (0, 0, C.BASE_W, h))
            pygame.draw.rect(surf, (6, 0, 2), (0, C.BASE_H - h, C.BASE_W, h))
            if h > 4:
                pygame.draw.rect(surf, (200, 50, 50), (0, h - 4, C.BASE_W, 4))
                pygame.draw.rect(surf, (200, 50, 50), (0, C.BASE_H - h, C.BASE_W, 4))
