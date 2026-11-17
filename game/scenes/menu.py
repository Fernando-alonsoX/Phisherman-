import math
import random
import pygame
from .base import Scene
from .. import ui, pixelfont, art_items, icons, cosmetics
from ..canvas import radial_glow
from ..splash import Splash
from .. import config as C


class Card:
    """Kartu pilihan menu dengan ilustrasi yang membesar dan menyala saat kursor diarahkan."""

    def __init__(self, rect, title, subtitle, art, tint, callback, tag):
        self.rect = pygame.Rect(rect)
        self.title = title
        self.subtitle = subtitle
        self.art = art
        self.tint = tint
        self.callback = callback
        self.tag = tag
        self.hover_t = 0.0
        self.hover = False
        self.press = False
        self.art_rect = pygame.Rect(self.rect.x + 14, self.rect.y + 14, self.rect.w - 28, 228)

    def update(self, dt, mouse, forced):
        self.hover = self.rect.collidepoint(mouse) or forced
        if self.rect.collidepoint(mouse):
            ui.HOT["hand"] = True
        target = 1.0 if self.hover else 0.0
        self.hover_t += (target - self.hover_t) * min(1.0, dt * 11)

    def draw(self, surf, t):
        h = self.hover_t
        lift = int(10 * h)
        r = self.rect.move(0, -lift + (4 if self.press else 0))
        if h > 0.02:
            gs = pygame.Surface((r.w + 80, r.h + 80), pygame.SRCALPHA)
            for i in range(8):
                a = int((14 + 10 * math.sin(t * 4)) * h * (8 - i) / 8)
                pygame.draw.rect(gs, (*self.tint, max(0, a)), (i * 4, i * 4, gs.get_width() - i * 8, gs.get_height() - i * 8), border_radius=30)
            surf.blit(gs, (r.x - 40, r.y - 40))
        shadow = pygame.Surface((r.w, 26), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, int(80 - 30 * h)), shadow.get_rect())
        surf.blit(shadow, (r.x, r.bottom - 6 + lift))
        tint = tuple(int(c * (0.75 + 0.25 * h)) for c in self.tint)
        surf.blit(ui.glass(r.w, r.h, 18, tint, int(165 + 60 * h)), r)
        ar = pygame.Rect(r.x + 14, r.y + 14, r.w - 28, 228)
        k = 1.14 * (1 + 0.16 * h)
        aw, ah = self.art.get_size()
        scaled = pygame.transform.scale(self.art, (int(aw * k), int(ah * k)))
        tmp = pygame.Surface(ar.size, pygame.SRCALPHA)
        tmp.blit(scaled, scaled.get_rect(center=(ar.w // 2, ar.h // 2)))
        tmp.blit(ui.rounded_mask(ar.w, ar.h, 12), (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(tmp, ar)
        pygame.draw.rect(surf, (6, 14, 34), ar, 3, border_radius=12)
        pygame.draw.rect(surf, (255, 255, 255) if h > 0.5 else (170, 205, 245), ar.inflate(-2, -2), 1, border_radius=11)
        tag = ui.font(13, True)
        ts = ui.text_surf(tag, self.tag, (255, 255, 255))
        pill = pygame.Rect(ar.x + 10, ar.y + 10, ts.get_width() + 20, 24)
        pygame.draw.rect(surf, (10, 24, 56), pill, border_radius=12)
        pygame.draw.rect(surf, (140, 200, 255), pill, 1, border_radius=12)
        surf.blit(ts, ts.get_rect(center=pill.center))
        ui.draw_text(surf, self.title, ui.font(30, True), (255, 255, 255), (r.centerx, ar.bottom + 18), "midtop", glow=(0, 20, 70), shadow=(0, 30, 80))
        ui.draw_text(surf, self.subtitle, ui.font(16), (226, 238, 255), (r.centerx, ar.bottom + 58), "midtop", shadow=(0, 20, 60))
        arrow = pygame.Rect(0, 0, 44, 44)
        arrow.center = (r.right - 36, r.bottom - 34)
        a = int(255 * (0.35 + 0.65 * h))
        pygame.draw.circle(surf, (255, 255, 255, a), arrow.center, 20)
        icons.draw_icon(surf, "play", (arrow.centerx + 2, arrow.centery), 24, (30, 90, 170))


class MenuScene(Scene):
    """Menu utama dengan judul pixel art dua kartu pilihan dan animasi laut malam."""

    exit_button = False
    hud = None
    exit_kind = "menu"

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.bg = app.assets.get("menu_bg")
        self.focus = -1
        rs = random.Random(8)
        self.stars = [(rs.randrange(C.BASE_W), rs.randrange(10, 440), rs.random() * 6) for _ in range(34)]
        self.fish = [[rs.randrange(C.BASE_W), (606, 628, 614, 636)[i], 30 + rs.random() * 40, rs.random() * 6, 1 if i % 2 else -1] for i in range(4)]
        self.dive = [None] * len(self.fish)
        self.splash = Splash()
        self.pull = None
        self.unlock_t = 0.0
        self.cards = [
            Card((210, 232, 400, 372), "PLAY STORYMODE", "Become a hacker and fool the AI in 5 emails", app.assets.get("story_card"), (70, 120, 220), app.go_story, "MISSION"),
            Card((670, 232, 400, 372), "LIVE SIMULATION", "Test and train the AI with unlimited messages", app.assets.get("live_card"), (30, 170, 170), app.go_live, "LAB"),
        ]
        self.shine = 0.0
        self.switch = ui.Button((0, 0, 92, 30), "Switch", app.go_login, "default", icon=icons.icon_fn("users"), size=14)
        self.title = pixelfont.render("PHISHERMAN", 10, grad=((255, 255, 255), (130, 205, 255)), outline=(8, 22, 70), shadow=(1, 1, (4, 10, 44)), thick=1)

    def backdrop_art(self):
        return self.bg

    def on_escape(self):
        self.app.go_login()

    def fish_pos(self, f):
        """Menghitung titik tengah ikan laut saat ini termasuk goyangan naik turun."""
        return f[0], f[1] + math.sin(self.t * 2 + f[3]) * 8 + 36

    def fish_hit(self, i, pos):
        """Memeriksa apakah titik berada pada ikan laut ke i yang sedang berenang mengikuti gerakannya."""
        if self.dive[i] is not None:
            return False
        x, y = self.fish_pos(self.fish[i])
        return pygame.Rect(x - 66, y - 42, 132, 84).collidepoint(pos)

    def over_card(self, pos):
        """Memeriksa apakah titik berada di atas kartu atau tombol ganti pemain yang harus diutamakan."""
        return any(c.rect.collidepoint(pos) for c in self.cards) or self.switch.rect.collidepoint(pos)

    def all_gone(self):
        """Memeriksa apakah semua ikan laut sudah menyelam sehingga ikan di kail terbuka."""
        return all(d is not None and d >= 0.9 for d in self.dive)

    def hook_hit(self, pos):
        """Memeriksa apakah titik mengenai ikan amplop di kail yang baru bisa diklik setelah semua ikan laut hilang."""
        if not self.all_gone() or self.pull is not None:
            return False
        c = self.hook_pose()[1]
        return pygame.Rect(c[0] - 62, c[1] - 46, 124, 92).collidepoint(pos)

    def dive_fish(self, i):
        """Membuat ikan laut ke i menyelam ke bawah air dengan percikan."""
        x, y = self.fish_pos(self.fish[i])
        self.dive[i] = 0.0
        self.splash.add(x, y + 14, 1.1)
        self.app.sfx.play("splash")

    def event(self, e):
        if self.pull is not None:
            return
        if self.switch.handle_event(e, self.app):
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and not self.over_card(e.pos):
            for i in range(len(self.fish)):
                if self.fish_hit(i, e.pos):
                    self.dive_fish(i)
                    return
            if self.hook_hit(e.pos):
                self.pull = {"t": 0.0, "whoosh": False}
                self.app.sfx.play("bite")
                return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for c in self.cards:
                if c.rect.collidepoint(e.pos):
                    c.press = True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            for c in self.cards:
                was = c.press
                c.press = False
                if was and c.rect.collidepoint(e.pos):
                    self.app.sfx.play("confirm")
                    c.callback()
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.focus = 0 if self.focus < 0 else 1 - self.focus
                self.app.sfx.play("hover")
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.focus >= 0:
                self.app.sfx.play("confirm")
                self.cards[self.focus].callback()
            elif e.key == pygame.K_1:
                self.app.sfx.play("confirm")
                self.cards[0].callback()
            elif e.key == pygame.K_2:
                self.app.sfx.play("confirm")
                self.cards[1].callback()
        if e.type == pygame.MOUSEMOTION:
            self.focus = -1

    def tick(self, dt):
        """Memajukan waktu animasi latar dan ikan tanpa memproses kartu agar bisa dipakai scene login."""
        self.t += dt
        self.shine = (self.shine + dt * 0.45) % 2.2
        for f in self.fish:
            f[0] += f[4] * f[2] * dt
            if f[0] > C.BASE_W + 120:
                f[0] = -120
            elif f[0] < -120:
                f[0] = C.BASE_W + 120
        for i, d in enumerate(self.dive):
            if d is not None and d < 1.2:
                self.dive[i] = d + dt
        self.splash.update(dt)
        if self.all_gone():
            self.unlock_t += dt

    def update(self, dt):
        self.tick(dt)
        self.switch.update(dt, self.app.mouse)
        if self.pull is not None:
            p = self.pull
            p["t"] += dt
            if p["t"] > 0.55 and not p["whoosh"]:
                p["whoosh"] = True
                self.app.sfx.play("whoosh")
            if p["t"] > 1.35 and not p.get("go"):
                p["go"] = True
                self.app.go_egg()
            return
        m = self.app.mouse
        if not self.over_card(m) and (any(self.fish_hit(i, m) for i in range(len(self.fish))) or self.hook_hit(m)):
            ui.HOT["hand"] = True
        for i, c in enumerate(self.cards):
            was = c.hover
            c.update(dt, self.app.mouse, self.focus == i)
            if c.hover and not was:
                self.app.sfx.play("hover")

    def draw_sea(self, surf):
        sea = pygame.Surface((C.BASE_W, 280), pygame.SRCALPHA)
        for k in range(7):
            pts = []
            base = 14 + k * 38
            for x in range(0, C.BASE_W + 16, 16):
                pts.append((x, base + math.sin(x / 90 + self.t * (0.9 + k * 0.12) + k) * (4 + k)))
            pygame.draw.lines(sea, (170, 215, 240, 26 + k * 6), False, pts, 3)
        surf.blit(sea, (0, 448))
        for (x, y, ph) in self.stars:
            a = 0.5 + 0.5 * math.sin(self.t * 2.4 + ph)
            c = int(120 + 135 * a)
            surf.fill((c, c, 255), (x, y, 4, 4))
            if a > 0.85:
                surf.fill((c, c, 255), (x - 4, y + 1, 12, 2))
                surf.fill((c, c, 255), (x + 1, y - 4, 2, 12))

    def draw_backdrop(self, surf):
        """Menggambar langit malam laut dan ikan amplop yang berenang."""
        surf.blit(self.bg, (0, 0))
        self.draw_sea(surf)
        for i, f in enumerate(self.fish):
            img = art_items.envelope_fish(4, flip=f[4] > 0)
            bob = math.sin(self.t * 2 + f[3]) * 8
            d = self.dive[i]
            if d is None:
                surf.blit(img, (f[0] - img.get_width() // 2, f[1] + bob))
            elif d < 0.9:
                k = d / 0.9
                tilt = (68 if f[4] < 0 else -68) * min(1.0, k * 1.6)
                spr = pygame.transform.rotate(img, tilt)
                spr.set_alpha(int(255 * (1 - k ** 2)))
                surf.blit(spr, spr.get_rect(center=(f[0], f[1] + bob + 36 + 70 * k * k)))
        self.splash.draw(surf)

    def hook_pose(self):
        """Menghitung posisi kait dan ikan amplop pada menu utama yang menjadi tujuan animasi login."""
        sway = math.sin(self.t * 1.3) * 5
        mx = 112 + int(sway * -1.5)
        top, cy, ang = -52, 128 + math.sin(self.t * 3) * 3, -35 + sway * 2
        if self.pull is not None:
            t = self.pull["t"]
            if t < 0.55:
                cy += 22 * math.sin(math.pi * t / 0.55) + math.sin(t * 70) * 3
            else:
                k = min(1.0, (t - 0.55) / 0.7) ** 2.2
                top -= 560 * k
                cy -= 640 * k
        elif self.all_gone():
            ang += math.sin(self.t * 11) * 9
            cy += math.sin(self.t * 7) * 3
        return (mx, top), (mx + 22, cy), ang, sway

    def draw_hook(self, surf, pose=None):
        """Menggambar kait dengan ikan amplop pada pose menu atau pose khusus untuk transisi."""
        top, center, ang, sway = pose or self.hook_pose()
        rot = pygame.transform.rotate(art_items.hook(4), sway)
        surf.blit(rot, rot.get_rect(midtop=top))
        if pose is None and self.all_gone():
            pulse = 0.5 + 0.5 * math.sin(self.t * 5)
            gl = radial_glow(78, (255, 214, 110), 0.35 + 0.35 * pulse)
            surf.blit(gl, gl.get_rect(center=center), special_flags=pygame.BLEND_RGB_ADD)
        fish = pygame.transform.rotate(art_items.envelope_fish(3), ang)
        surf.blit(fish, fish.get_rect(center=center))
        if pose is None and self.all_gone() and self.pull is None:
            for j in range(3):
                a = 0.5 + 0.5 * math.sin(self.t * 4 + j * 2.1)
                sp = art_items.sparkle(8 + int(8 * a), (255, 236, 150))
                surf.blit(sp, sp.get_rect(center=(center[0] + math.cos(self.t * 1.8 + j * 2.1) * 56, center[1] + math.sin(self.t * 1.8 + j * 2.1) * 36)))

    def draw_ui(self, surf):
        """Menggambar judul kartu pilihan dan chip status di atas latar menu."""
        bob = math.sin(self.t * 1.6) * 5
        tr = self.title.get_rect(midtop=(C.BASE_W // 2, 14 + bob))
        gl = radial_glow(260, (60, 110, 200), 0.16)
        gl = pygame.transform.scale(gl, (700, 220))
        surf.blit(gl, gl.get_rect(center=tr.center), special_flags=pygame.BLEND_RGB_ADD)
        surf.blit(self.title, tr)
        tw, th = self.title.get_size()
        band = pygame.Surface((tw, th), pygame.SRCALPHA)
        bx = int((self.shine / 2.2) * (tw + 200)) - 100
        pygame.draw.polygon(band, (255, 255, 255, 235), [(bx, 0), (bx + 36, 0), (bx - 4, th), (bx - 40, th)])
        shine = self.title.copy()
        shine.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        shine.blit(band, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(shine, tr)
        tag = pygame.Rect(0, 0, 560, 40)
        tag.midtop = (C.BASE_W // 2, tr.bottom - 4)
        surf.blit(ui.glass(tag.w, tag.h, 12, (60, 110, 190), 170), tag)
        ui.draw_text(surf, "Fool the email guard AI. Learn to spot phishing!", ui.font(19, True), (255, 255, 255), tag.center, "center", shadow=(0, 20, 60))
        for c in self.cards:
            c.draw(surf, self.t)
        chip = pygame.Rect(22, C.BASE_H - 54, 270, 36)
        surf.blit(ui.glass(chip.w, chip.h, 10, (40, 80, 130), 190), chip)
        st = self.app.adapter.status
        col = {"ready": (90, 230, 120), "loading": (255, 210, 80), "demo": (90, 230, 120), "error": (240, 90, 80)}.get(st, (200, 200, 200))
        pygame.draw.circle(surf, col, (chip.x + 20, chip.centery), 7)
        pygame.draw.circle(surf, (255, 255, 255), (chip.x + 18, chip.centery - 2), 2)
        ui.draw_text(surf, self.app.adapter.label, ui.font(15, True), (240, 248, 255), (chip.x + 38, chip.centery), "midleft", shadow=(0, 10, 40))
        self.draw_player(surf)
        hint = "ESC Login    F9 Sound"
        hs = ui.text_surf(ui.font(14), hint, (210, 226, 250))
        hr = pygame.Rect(0, 0, hs.get_width() + 28, 32)
        hr.bottomright = (C.BASE_W - 22, C.BASE_H - 22)
        surf.blit(ui.glass(hr.w, hr.h, 10, (40, 80, 130), 170), hr)
        surf.blit(hs, hs.get_rect(center=hr.center))

    def draw(self, surf):
        self.draw_backdrop(surf)
        self.draw_hook(surf)
        self.draw_ui(surf)

    def draw_player(self, surf):
        """Menggambar chip nama pemain aktif di kanan atas lengkap dengan tombol ganti pemain."""
        name = self.app.player_name or "Guest"
        if len(name) > 12:
            name = name[:11] + ".."
        f = ui.font(18, True)
        nw = max(f.size(name)[0], ui.font(12).size("Active player")[0])
        chip = pygame.Rect(0, 0, 52 + nw + 14 + self.switch.rect.w + 8, 46)
        chip.topright = (C.BASE_W - 22, 16)
        surf.blit(ui.glass(chip.w, chip.h, 12, (40, 80, 130), 190), chip)
        pygame.draw.circle(surf, (255, 255, 255), (chip.x + 26, chip.centery), 17)
        icons.draw_icon(surf, "user", (chip.x + 26, chip.centery), 22, (50, 110, 190))
        cosmetics.draw_border(surf, (chip.x + 26, chip.centery), 17, self.app.eggs.look(self.app.player_name)["border"])
        ui.draw_text(surf, name, f, (255, 255, 255), (chip.x + 52, chip.centery - 9), "midleft", shadow=(0, 20, 60))
        ui.draw_text(surf, "Active player", ui.font(12), (190, 214, 245), (chip.x + 52, chip.centery + 11), "midleft")
        self.switch.rect.midright = (chip.right - 8, chip.centery)
        self.switch.draw(surf)
