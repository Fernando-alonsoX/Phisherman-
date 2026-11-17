import math
import pygame
from . import ui, icons, art_items, pixelfont
from .canvas import blur
from . import config as C

KINDS = {
    "menu": {
        "title": "Quit Phisherman?",
        "body": "You are about to close the game. The AI model performance is saved automatically, so your training will not be lost.",
        "cancel": "Cancel",
        "heading": "Confirm - Phisherman",
        "hint": "ESC to cancel",
        "icons": ("power", "brain"),
        "face": "sad",
        "confirm": "Yes, Quit Game",
    },
    "story": {
        "title": "Back to Main Menu?",
        "body": "Story Mode progress will not be saved. Your money and the emails you already sent will be lost.",
        "icons": ("door", "nodisk"),
        "face": "shock",
        "confirm": "Yes, Leave",
        "cancel": "Keep Playing",
        "heading": "Confirm - Phisherman",
        "hint": "ESC to cancel",
    },
    "egg": {
        "title": "Leave the Fishing Trip?",
        "body": "Your catch is saved in the inventory automatically, so every fish you caught will still be there next time.",
        "cancel": "Keep Fishing",
        "heading": "Confirm - Phisherman",
        "hint": "ESC to cancel",
        "icons": ("door", "disk"),
        "face": "sad",
        "confirm": "Yes, Leave",
    },
    "live": {
        "title": "Leave Live Simulation?",
        "body": "Your AI retraining results are saved and will be used again next session.",
        "cancel": "Keep Playing",
        "heading": "Confirm - Phisherman",
        "hint": "ESC to cancel",
        "icons": ("door", "brain"),
        "face": "sad",
        "confirm": "Yes, Leave",
    },
}


class ExitModal:
    """Dialog konfirmasi keluar di tengah layar dengan latar buram dan ikon beranimasi untuk semua scene."""

    def __init__(self, app, kind, on_confirm, on_cancel, snapshot):
        self.app = app
        self.kind = kind
        self.info = KINDS[kind]
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        small = pygame.transform.smoothscale(snapshot, (C.BASE_W // 8, C.BASE_H // 8))
        bg = pygame.transform.smoothscale(small, (C.BASE_W, C.BASE_H))
        dim = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
        dim.fill((8, 16, 44, 120))
        bg.blit(dim, (0, 0))
        self.bg = bg
        self.t = 0.0
        self.rect = pygame.Rect(0, 0, 700, 360)
        self.rect.center = (C.BASE_W // 2, C.BASE_H // 2)
        bx = self.rect.right - 24
        by = self.rect.bottom - 24
        self.btn_confirm = ui.Button((bx - 190, by - 50, 190, 50), self.info["confirm"], self._confirm, "danger", icon=icons.icon_fn("exit"), size=17)
        self.btn_cancel = ui.Button((bx - 190 - 16 - 210, by - 50, 210, 50), self.info["cancel"], self._cancel, "primary", icon=icons.icon_fn("play"), size=17)
        self.focus = 1
        self.close_down = False
        self.close_hover = False
        self.sparks = [(i * 1.7, 20 + (i * 37) % 90, 16 + (i * 53) % 110) for i in range(7)]
        app.sfx.play("pop")

    def _confirm(self):
        self.on_confirm()

    def _cancel(self):
        self.on_cancel()

    def event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.app.sfx.play("click")
                self._cancel()
            elif e.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                self.focus = 1 - self.focus
                self.app.sfx.play("hover")
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.app.sfx.play("click")
                (self._confirm if self.focus == 0 else self._cancel)()
            elif e.key == pygame.K_y:
                self._confirm()
            elif e.key == pygame.K_n:
                self._cancel()
            return
        if e.type == pygame.MOUSEMOTION:
            self.close_hover = self.close_rect().collidepoint(e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.close_rect().collidepoint(e.pos):
                self.close_down = True
                return
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            was = self.close_down
            self.close_down = False
            if was and self.close_rect().collidepoint(e.pos):
                self.app.sfx.play("click")
                self._cancel()
                return
        self.btn_confirm.handle_event(e, self.app)
        self.btn_cancel.handle_event(e, self.app)

    def close_rect(self):
        """Menghitung area tombol X di pojok kanan atas jendela konfirmasi pada koordinat layar."""
        return pygame.Rect(self.rect.right - 8 - 98 + 52, self.rect.y + 1, 46, 20)

    def update(self, dt):
        self.t += dt
        m = self.app.mouse
        self.btn_confirm.update(dt, m)
        self.btn_cancel.update(dt, m)
        self.close_hover = self.close_rect().collidepoint(m)
        if self.close_hover:
            ui.HOT["hand"] = True

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        k = min(1.0, self.t / 0.28)
        ease = 1 + 2.2 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2
        scale = 0.82 + 0.18 * ease
        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self._draw_panel(panel)
        if scale < 0.999:
            w, h = int(self.rect.w * scale), int(self.rect.h * scale)
            panel = pygame.transform.smoothscale(panel, (max(1, w), max(1, h)))
        panel.set_alpha(int(255 * min(1.0, k * 1.6)))
        surf.blit(panel, panel.get_rect(center=self.rect.center))

    def _draw_panel(self, p):
        r = pygame.Rect(0, 0, self.rect.w, self.rect.h)
        client = ui.draw_window(p, r, self.info["heading"], icon=lambda s, c, z, col: icons.draw_icon(s, "warning", c, z, (255, 220, 90)))
        if self.close_hover:
            cr = pygame.Rect(self.rect.w - 8 - 98 + 52, 1, 46, 20)
            hot = pygame.Surface(cr.size, pygame.SRCALPHA)
            pygame.draw.rect(hot, (255, 120, 100, 170 if not self.close_down else 230), hot.get_rect(), border_bottom_right_radius=5)
            pygame.draw.rect(hot, (255, 255, 255, 200), hot.get_rect(), 1, border_bottom_right_radius=5)
            p.blit(hot, cr)
            pygame.draw.line(p, (255, 255, 255), (cr.x + 17, cr.y + 5), (cr.x + 27, cr.y + 14), 3)
            pygame.draw.line(p, (255, 255, 255), (cr.x + 27, cr.y + 5), (cr.x + 17, cr.y + 14), 3)
        pygame.draw.rect(p, (240, 246, 255), client)
        pygame.draw.rect(p, (255, 255, 255), (client.x, client.y, client.w, 96))
        pygame.draw.rect(p, (214, 226, 244), (client.x, client.bottom - 78, client.w, 78))
        pygame.draw.line(p, (160, 180, 210), (client.x, client.bottom - 78), (client.right, client.bottom - 78))
        bob = math.sin(self.t * 3.2) * 6
        ic1, ic2 = self.info["icons"]
        big = art_items.pixel_icon(ic1, 8)
        cx, cy = client.x + 100, client.y + 118
        halo = pygame.Surface((190, 190), pygame.SRCALPHA)
        pygame.draw.circle(halo, (120, 180, 255, 70), (95, 95), 88)
        pygame.draw.circle(halo, (255, 255, 255, 90), (95, 95), 62)
        p.blit(halo, (cx - 95, cy - 95))
        p.blit(big, big.get_rect(center=(cx, cy + bob)))
        small = art_items.pixel_icon(ic2, 4)
        p.blit(small, small.get_rect(center=(cx + 70, cy - 66 - bob * 0.6)))
        for (ph, ox, oy) in self.sparks:
            a = 0.5 + 0.5 * math.sin(self.t * 4 + ph)
            sp = art_items.sparkle(10 + int(6 * a), (255, 236, 150))
            sp = sp.copy()
            sp.set_alpha(int(80 + 170 * a))
            p.blit(sp, (cx - 80 + ox, cy - 90 + oy))
        face = self.app.assets.portrait(self.info["face"], 96)
        fx, fy = client.x + 16, client.bottom - 108
        p.blit(face, (fx, fy))
        ui.draw_text(p, self.info["title"], ui.font(28, True), (20, 44, 92), (client.x + 220, client.y + 30))
        lines = ui.wrap_lines(ui.font(18), self.info["body"], client.w - 250)
        y = client.y + 84
        for ln in lines:
            ui.draw_text(p, ln, ui.font(18), (52, 64, 90), (client.x + 220, y))
            y += 26
        ui.draw_text(p, self.info["hint"], ui.font(13), (110, 124, 150), (client.x + 126, client.bottom - 26))
        for b, i in ((self.btn_confirm, 0), (self.btn_cancel, 1)):
            local = b.rect.move(-self.rect.x, -self.rect.y)
            old = b.rect
            b.rect = local
            b.draw(p)
            if self.focus == i:
                pygame.draw.rect(p, (255, 255, 255), local.inflate(8, 8), 2, border_radius=9)
                pygame.draw.rect(p, (255, 190, 60), local.inflate(12, 12), 2, border_radius=11)
            b.rect = old
