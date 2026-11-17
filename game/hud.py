import math
import pygame
from . import pixelfont, ui, icons, art_items
from . import config as C

PLATE_POS = (C.BASE_W - 248 - 18, 6)


class Hud:
    """Tampilan uang di pojok kanan atas counter email dan tombol home yang tampil di atas semua scene."""

    def __init__(self, app):
        self.app = app
        self.shown = float(C.START_MONEY)
        self.pop = 0.0
        self.floats = []
        self.t = 0.0
        self.home_hover = False
        self.home_rect = pygame.Rect(C.BASE_W - 18 - 64, 10, 64, 64)
        self.home_press = False

    def snap(self):
        self.shown = float(self.app.session.money)
        self.shown_score = float(self.app.session.score)
        self.pop = 0.0
        self.floats = []

    def gain(self, amount):
        self.floats.append([f"+${amount}", 0.0])
        self.pop = 1.0

    def update(self, dt):
        self.t += dt
        target = self.app.session.money
        if abs(self.shown - target) > 0.5:
            step = max(1.0, abs(target - self.shown) * min(1.0, dt * 6))
            self.shown += step if self.shown < target else -step
            if abs(self.shown - target) < 1:
                self.shown = float(target)
        ts = self.app.session.score
        if abs(self.shown_score - ts) > 0.5:
            self.shown_score += max(1.0, abs(ts - self.shown_score) * min(1.0, dt * 5)) * (1 if ts > self.shown_score else -1)
            if abs(self.shown_score - ts) < 1:
                self.shown_score = float(ts)
        self.pop = max(0.0, self.pop - dt * 2.2)
        for f in self.floats:
            f[1] += dt
        self.floats = [f for f in self.floats if f[1] < 1.6]

    def handle_home(self, e):
        if e.type == pygame.MOUSEMOTION:
            self.home_hover = self.home_rect.collidepoint(e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.home_rect.collidepoint(e.pos):
            self.home_press = True
            return True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            was = self.home_press
            self.home_press = False
            if was and self.home_rect.collidepoint(e.pos):
                self.app.sfx.play("click")
                self.app.go_menu()
                return True
        return False

    def draw_money(self, surf):
        plate, slot = art_items.money_plate()
        x, y = PLATE_POS
        bob = int(math.sin(self.t * 2) * 1.5)
        sh = pygame.Surface((plate.get_width(), 12), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
        surf.blit(sh, (x, y + plate.get_height() - 4 + bob))
        surf.blit(plate, (x, y + bob))
        val = f"${int(round(self.shown)):,}"
        scale = 3
        txt = pixelfont.render(val, scale, color=(176, 255, 176), outline=(6, 40, 20), thick=1)
        if self.pop > 0:
            k = 1 + 0.28 * math.sin(self.pop * math.pi)
            txt = pygame.transform.scale(txt, (int(txt.get_width() * k), int(txt.get_height() * k)))
        r = txt.get_rect(midright=(x + slot.right - 6, y + slot.centery + bob))
        surf.blit(txt, r)
        for label, age in self.floats:
            a = max(0, 255 - int(age / 1.6 * 255))
            t = pixelfont.render(label, 3, color=(255, 226, 90), outline=(90, 50, 0))
            t = t.copy()
            t.set_alpha(a)
            surf.blit(t, t.get_rect(midright=(x - 6, y + 32 - age * 34)))

    def draw_score(self, surf):
        """Menggambar chip skor dengan ikon bintang yang menempel di sebelah kiri tampilan uang."""
        r = pygame.Rect(PLATE_POS[0] - 6 - 148, 14, 148, 52)
        surf.blit(ui.glass(r.w, r.h, 12, (150, 110, 40), 200), r)
        icons.draw_icon(surf, "star", (r.x + 28, r.centery), 28, (255, 226, 120))
        t = pixelfont.render(f"{int(round(self.shown_score))}", 3, color=(255, 240, 180), outline=(70, 40, 4))
        surf.blit(t, t.get_rect(midright=(r.right - 12, r.centery)))

    def draw_counter(self, surf, sent, total):
        x = PLATE_POS[0] - 6 - 148 - 8 - 134
        r = pygame.Rect(x, 14, 134, 52)
        surf.blit(ui.glass(r.w, r.h, 12, (60, 110, 170), 190), r)
        icons.draw_icon(surf, "envelope", (r.x + 28, r.centery), 28, (255, 255, 255))
        t = pixelfont.render(f"{sent}/{total}", 3, color=(255, 255, 255), outline=(10, 30, 70))
        surf.blit(t, t.get_rect(midright=(r.right - 10, r.centery)))

    def draw_home(self, surf):
        r = self.home_rect
        pulse = 0.5 + 0.5 * math.sin(self.t * 3)
        g = pygame.Surface((r.w + 30, r.h + 30), pygame.SRCALPHA)
        pygame.draw.circle(g, (140, 210, 255, int(40 + 50 * (1 if self.home_hover else pulse * 0.4))), g.get_rect().center, r.w // 2 + 12)
        surf.blit(g, (r.x - 15, r.y - 15))
        style = "primary"
        state = "pressed" if self.home_press else ("hover" if self.home_hover else "normal")
        img = ui.button_surface(r.w, r.h, style, state, 32)
        surf.blit(img, r)
        icons.draw_icon(surf, "home", r.center, 34, (255, 255, 255))
        if self.home_hover:
            ui.HOT["hand"] = True
            ui.draw_text(surf, "Main Menu", ui.font(14, True), (255, 255, 255), (r.centerx, r.bottom + 6), "midtop", shadow=(0, 0, 0))
