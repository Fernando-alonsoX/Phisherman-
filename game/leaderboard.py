import math
import pygame
from . import ui, icons, art_items, pixelfont, cosmetics
from . import config as C

PALETTE = [
    ((255, 214, 84), (206, 140, 16)),
    ((226, 234, 246), (136, 150, 178)),
    ((232, 156, 98), (152, 84, 38)),
    ((122, 178, 246), (46, 96, 178)),
    ((96, 216, 196), (28, 128, 118)),
]
HEIGHTS = [214, 178, 146, 120, 96]
BLOCK_W = 124
GAP = 8


def fmt(n):
    """Mengubah angka menjadi tulisan dengan pemisah titik ribuan gaya Indonesia."""
    return f"{int(n):,}".replace(",", ".")


def blurred(snapshot):
    """Membuat salinan layar yang buram dan digelapkan sebagai latar jendela popup."""
    small = pygame.transform.smoothscale(snapshot, (C.BASE_W // 8, C.BASE_H // 8))
    bg = pygame.transform.smoothscale(small, (C.BASE_W, C.BASE_H))
    dim = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
    dim.fill((8, 16, 44, 130))
    bg.blit(dim, (0, 0))
    return bg


def ease_out_back(k):
    """Kurva gerak naik yang melewati target sedikit lalu kembali seperti pegas."""
    k = max(0.0, min(1.0, k))
    return 1 + 2.4 * (k - 1) ** 3 + 1.4 * (k - 1) ** 2


class LeaderboardModal:
    """Popup papan peringkat lima besar berbentuk podium tangga dengan animasi muncul berurutan dan animasi diam yang terus hidup."""

    def __init__(self, app, snapshot, on_close, close_label="Close"):
        self.app = app
        self.on_close = on_close
        self.bg = blurred(snapshot)
        self.rows = app.players.leaderboard(5)
        self.me = (app.player_name or "").lower()
        self.rect = pygame.Rect(0, 0, 800, 520)
        self.rect.center = (C.BASE_W // 2, C.BASE_H // 2)
        self.t = 0.0
        self.replay_at = 0.0
        self.reveal = {}
        self.sq = [0.0] * 5
        self.hover = -1
        self.close_down = False
        self.close_hover = False
        self.cache = {}
        self.stars = [((i * 97) % 770 + 10, (i * 53) % 330 + 40, i * 0.7) for i in range(26)]
        self.sparks = [(i * 1.3, 24 + (i * 29) % 40, 0.6 + (i % 3) * 0.25) for i in range(7)]
        self.heard = set()
        if self.rows:
            app.sfx.play("pop")

    def close(self):
        self.on_close()

    def start_of(self, i):
        """Menghitung waktu mulai blok peringkat ke-i dengan peringkat terbawah naik lebih dulu."""
        order = 4 - i
        return self.replay_at + 0.4 + order * 0.55 + (0.35 if i == 0 else 0.0)

    def rise(self, i):
        return max(0.0, min(1.0, (self.t - self.start_of(i)) / 0.6))

    def entry(self, i):
        return max(0.0, min(1.0, (self.t - self.start_of(i) - 0.5) / 0.45))

    def block_x(self, i):
        total = 5 * BLOCK_W + 4 * GAP
        return 8 + (784 - total) // 2 + i * (BLOCK_W + GAP)

    def baseline(self):
        return 494

    def hit_rect(self, i):
        h = HEIGHTS[i]
        x = self.block_x(i)
        top = self.baseline() - h - 130
        return pygame.Rect(x, top, BLOCK_W, h + 130)

    def event(self, e):
        local = None
        if hasattr(e, "pos"):
            local = (e.pos[0] - self.rect.x, e.pos[1] - self.rect.y)
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.app.sfx.play("click")
                self.close()
            return
        if e.type == pygame.MOUSEMOTION:
            self.close_hover = self.close_rect().collidepoint(e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.close_rect().collidepoint(e.pos):
                self.close_down = True
                return
            for i in range(len(self.rows)):
                if self.rise(i) >= 1.0 and self.hit_rect(i).collidepoint(local):
                    self.sq[i] = 0.3
                    self.app.sfx.play("pop")
                    break
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            was = self.close_down
            self.close_down = False
            if was and self.close_rect().collidepoint(e.pos):
                self.app.sfx.play("click")
                self.close()

    def close_rect(self):
        """Menghitung area tombol X di pojok kanan atas jendela papan peringkat pada koordinat layar."""
        return pygame.Rect(self.rect.right - 8 - 98 + 52, self.rect.y + 1, 46, 20)

    def update(self, dt):
        self.t += dt
        m = self.app.mouse
        self.close_hover = self.close_rect().collidepoint(m)
        if self.close_hover:
            ui.HOT["hand"] = True
        local = (m[0] - self.rect.x, m[1] - self.rect.y)
        self.hover = -1
        for i in range(len(self.rows)):
            if self.rise(i) >= 1.0 and self.hit_rect(i).collidepoint(local):
                self.hover = i
                ui.HOT["hand"] = True
        for i in range(5):
            self.sq[i] = max(0.0, self.sq[i] - dt)
            if i < len(self.rows) and i not in self.heard and self.t >= self.start_of(i):
                self.heard.add(i)
                if i == 0:
                    self.app.sfx.play("win")
                else:
                    self.app.sfx.play("pop")

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        k = min(1.0, self.t / 0.28)
        ease = 1 + 2.2 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2
        scale = 0.82 + 0.18 * ease
        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.draw_panel(panel)
        if scale < 0.999:
            w, h = int(self.rect.w * scale), int(self.rect.h * scale)
            panel = pygame.transform.smoothscale(panel, (max(1, w), max(1, h)))
        panel.set_alpha(int(255 * min(1.0, k * 1.6)))
        surf.blit(panel, panel.get_rect(center=self.rect.center))

    def draw_panel(self, p):
        r = pygame.Rect(0, 0, self.rect.w, self.rect.h)
        client = ui.draw_window(p, r, "Leaderboard - Phisherman", icon=lambda s, c, z, col: icons.draw_icon(s, "trophy", c, z, (255, 224, 110)))
        if self.close_hover:
            cr = pygame.Rect(self.rect.w - 8 - 98 + 52, 1, 46, 20)
            hot = pygame.Surface(cr.size, pygame.SRCALPHA)
            pygame.draw.rect(hot, (255, 120, 100, 170 if not self.close_down else 230), hot.get_rect(), border_bottom_right_radius=5)
            pygame.draw.rect(hot, (255, 255, 255, 200), hot.get_rect(), 1, border_bottom_right_radius=5)
            p.blit(hot, cr)
            pygame.draw.line(p, (255, 255, 255), (cr.x + 17, cr.y + 5), (cr.x + 27, cr.y + 14), 3)
            pygame.draw.line(p, (255, 255, 255), (cr.x + 27, cr.y + 5), (cr.x + 17, cr.y + 14), 3)
        self.draw_sky(p, client)
        title = self.cache.get("title")
        if title is None:
            title = pixelfont.render("TOP 5", 6, grad=((255, 246, 190), (255, 196, 60)), outline=(70, 36, 6), shadow=(1, 1, (30, 16, 2)), thick=1)
            self.cache["title"] = title
        bob = math.sin(self.t * 2) * 2
        p.blit(title, title.get_rect(midtop=(client.centerx, client.y + 8 + bob)))
        ui.draw_text(p, "Each player's best score. Click a block for details." if self.rows else "", ui.font(14), (190, 214, 246), (client.centerx, client.y + 90), "midtop")
        if self.rows:
            self.draw_podium(p, client)
        else:
            self.draw_empty(p, client)
        if self.hover >= 0 and self.hover < len(self.rows):
            self.draw_tip(p, self.hover)

    def draw_empty(self, p, client):
        """Menggambar keadaan kosong berupa piala redup dan ajakan menamatkan Story Mode saat belum ada pemain berskor."""
        cx, cy = client.centerx, client.y + 250
        bob = math.sin(self.t * 2) * 5
        glow = pygame.Surface((260, 260), pygame.SRCALPHA)
        pygame.draw.circle(glow, (120, 160, 230, 36), (130, 130), 120)
        p.blit(glow, glow.get_rect(center=(cx, cy + bob)))
        icons.draw_icon(p, "trophy", (cx, int(cy + bob)), 120, (120, 142, 190))
        ui.draw_text(p, "No scores yet", ui.font(26, True), (230, 240, 255), (cx, cy + 90), "midtop")
        ui.draw_text(p, "Finish Story Mode to put your name on the board.", ui.font(16), (170, 196, 236), (cx, cy + 128), "midtop")

    def draw_sky(self, p, client):
        old = p.get_clip()
        p.set_clip(client)
        for y in range(client.y, client.bottom, 4):
            t = (y - client.y) / client.h
            c = (int(10 + 26 * t), int(20 + 56 * t), int(56 + 84 * t))
            pygame.draw.rect(p, c, (client.x, y, client.w, 4))
        for (x, y, ph) in self.stars:
            a = 0.5 + 0.5 * math.sin(self.t * 2.2 + ph)
            c = int(110 + 140 * a)
            p.fill((c, c, 255), (client.x + x, y, 3, 3))
        cx, cy = self.block_x(0) + BLOCK_W // 2, self.baseline() - HEIGHTS[0] - 64
        if self.rows and self.entry(0) >= 1.0:
            ray = pygame.Surface((520, 520), pygame.SRCALPHA)
            for i in range(10):
                a0 = self.t * 0.35 + i * math.pi / 5
                a1 = a0 + 0.17
                pts = [(260, 260), (260 + math.cos(a0) * 300, 260 + math.sin(a0) * 300), (260 + math.cos(a1) * 300, 260 + math.sin(a1) * 300)]
                pygame.draw.polygon(ray, (255, 226, 130, 26), pts)
            p.blit(ray, (cx - 260, cy - 260))
        if self.rows:
            floor = pygame.Rect(client.x, self.baseline(), client.w, client.bottom - self.baseline())
            pygame.draw.rect(p, (14, 30, 70), floor)
            pygame.draw.line(p, (96, 150, 230), floor.topleft, floor.topright, 2)
        p.set_clip(old)

    def block_surface(self, i):
        key = ("block", i, bool(i < len(self.rows)))
        s = self.cache.get(key)
        if s is not None:
            return s
        h = HEIGHTS[i]
        w = BLOCK_W
        real = i < len(self.rows)
        c1, c2 = PALETTE[i] if real else ((92, 104, 132), (52, 62, 88))
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            t = y / max(1, h - 1)
            col = tuple(int(c1[k] * (1 - t) + c2[k] * t) for k in range(3))
            pygame.draw.line(s, col, (0, y), (w, y))
        for y in range(0, h, 8):
            pygame.draw.line(s, (255, 255, 255, 22), (0, y), (w, y))
        pygame.draw.rect(s, (255, 255, 255, 120), (0, 0, w, 8))
        pygame.draw.rect(s, (255, 255, 255, 70), (0, 0, 4, h))
        pygame.draw.rect(s, (0, 0, 0, 60), (w - 5, 0, 5, h))
        pygame.draw.rect(s, (14, 24, 52), (0, 0, w, h), 3)
        num = pixelfont.render(str(i + 1), 6 if i < 3 else 4, grad=((255, 255, 255), (230, 240, 255)), outline=(16, 28, 66), shadow=(1, 1, (8, 14, 40)), thick=1)
        s.blit(num, num.get_rect(midtop=(w // 2, 12)))
        if real:
            row = self.rows[i]
            ui.draw_text(s, f"{fmt(row['score'])} pts", ui.font(17, True), (255, 255, 255), (w // 2, 12 + num.get_height() + 6), "midtop", shadow=(10, 20, 50))
        else:
            ui.draw_text(s, "Empty", ui.font(15, True), (196, 206, 226), (w // 2, 12 + num.get_height() + 6), "midtop")
        self.cache[key] = s
        return s

    def draw_podium(self, p, client):
        base = self.baseline()
        for i in (4, 3, 2, 1, 0):
            x = self.block_x(i)
            full = HEIGHTS[i]
            k = self.rise(i)
            if k <= 0:
                continue
            hh = full * min(1.12, ease_out_back(k))
            hh = max(1, hh)
            idle = 1.0
            if k >= 1.0:
                idle = 1 + 0.012 * math.sin(self.t * 2.0 + i)
            if self.sq[i] > 0:
                idle *= 1 - 0.14 * math.sin(math.pi * (1 - self.sq[i] / 0.3))
            hh *= idle
            blk = self.block_surface(i)
            if hh <= full:
                vis = max(1, int(hh))
                part = blk.subsurface((0, full - vis, BLOCK_W, vis))
                p.blit(part, (x, base - vis))
                top = base - vis
            else:
                img = pygame.transform.scale(blk, (BLOCK_W, int(hh)))
                p.blit(img, (x, base - int(hh)))
                top = base - int(hh)
            if k >= 1.0 and i < len(self.rows):
                self.draw_shine(p, blk, i, x, base - full)
            self.draw_entry(p, i, x, top)

    def draw_shine(self, p, blk, i, x, y):
        cyc = (self.t * 0.55 + i * 0.37) % 3.0
        if cyc > 1.0:
            return
        w, h = blk.get_size()
        sh = blk.copy()
        sh.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        band = pygame.Surface((w, h), pygame.SRCALPHA)
        bx = int(cyc * (w + h)) - h
        pygame.draw.polygon(band, (255, 255, 255, 120), [(bx, h), (bx + 26, h), (bx + 26 + h, 0), (bx + h, 0)])
        sh.blit(band, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        p.blit(sh, (x, y))

    def draw_entry(self, p, i, x, top):
        e = self.entry(i)
        if e <= 0 or i >= len(self.rows):
            if e > 0:
                ph = pygame.Surface((60, 60), pygame.SRCALPHA)
                for a in range(0, 360, 30):
                    pygame.draw.circle(ph, (160, 176, 210, 150), (30 + math.cos(math.radians(a)) * 24, 30 + math.sin(math.radians(a)) * 24), 2)
                icons.draw_icon(ph, "user", (30, 30), 26, (120, 134, 168))
                p.blit(ph, ph.get_rect(center=(x + BLOCK_W // 2, top - 40)))
            return
        row = self.rows[i]
        drop = (1 - ease_out_back(e)) * -60
        bob = math.sin(self.t * 2.4 + i * 0.9) * 4 if e >= 1.0 else 0
        cx = x + BLOCK_W // 2
        plate_y = top - 30 + drop + bob
        ac = (cx, int(plate_y - 40))
        c1, c2 = PALETTE[i]
        mine = row["name"].lower() == self.me
        if i == 0:
            glow = pygame.Surface((120, 120), pygame.SRCALPHA)
            a = int(60 + 30 * math.sin(self.t * 3))
            pygame.draw.circle(glow, (255, 220, 100, a), (60, 60), 58)
            p.blit(glow, glow.get_rect(center=ac))
        pygame.draw.circle(p, (10, 20, 50), ac, 31)
        pygame.draw.circle(p, c1, ac, 29)
        pygame.draw.circle(p, c2, ac, 25)
        pygame.draw.circle(p, (255, 255, 255), ac, 25, 2)
        icons.draw_icon(p, "user", ac, 34, (255, 255, 255))
        look = self.app.eggs.look(row["name"])["border"]
        cosmetics.draw_border(p, ac, 30, look)
        if i == 0:
            cb = math.sin(self.t * 3) * 3
            lift = 0 if look == "b0" else (32 if look in ("b4", "b7") else 8)
            icons.draw_icon(p, "crown", (ac[0], ac[1] - 44 + cb - lift), 36, (255, 214, 70))
            for (ph, rr, sp) in self.sparks:
                a = self.t * sp + ph
                sx = ac[0] + math.cos(a) * (rr + 22)
                sy = ac[1] + math.sin(a) * (rr + 8) - 6
                tw = 0.5 + 0.5 * math.sin(self.t * 5 + ph)
                spk = art_items.sparkle(8 + int(8 * tw), (255, 236, 150)).copy()
                spk.set_alpha(int(90 + 160 * tw))
                p.blit(spk, spk.get_rect(center=(sx, sy)))
        name = row["name"]
        f = ui.font(15, True)
        while f.size(name)[0] > BLOCK_W - 12 and len(name) > 3:
            name = name[:-2]
        label = name if name == row["name"] else name + ".."
        pl = pygame.Rect(0, 0, BLOCK_W - 4, 26)
        pl.center = (cx, int(plate_y + 13))
        plate = ui.glass(pl.w, pl.h, 8, (30, 60, 120) if not mine else (170, 120, 20), 235)
        p.blit(plate, pl)
        ui.draw_text(p, label, f, (255, 255, 255), pl.center, "center", shadow=(0, 10, 40))
        if mine:
            pulse = int(160 + 90 * math.sin(self.t * 5))
            pygame.draw.rect(p, (255, 220, 90, pulse), pl.inflate(6, 6), 2, border_radius=10)
            tag = pygame.Rect(0, 0, 50, 18)
            tag.midleft = (ac[0] + 18, ac[1] - 34 + bob * 0.3)
            pygame.draw.rect(p, (255, 200, 60), tag, border_radius=9)
            ui.draw_text(p, "YOU", ui.font(12, True), (70, 40, 4), tag.center, "center")

    def draw_tip(self, p, i):
        row = self.rows[i]
        lines = [row["name"], f"Best score  {fmt(row['score'])}", f"Money  ${fmt(row['money'])}", f"Games played  {row['games']}x"]
        w = 210
        h = 18 + 22 * len(lines)
        x = self.block_x(i) + BLOCK_W // 2 - w // 2
        x = max(14, min(self.rect.w - w - 14, x))
        y = self.baseline() - HEIGHTS[i] // 2 - h // 2
        y = max(100, y)
        p.blit(ui.glass(w, h, 10, (14, 30, 76), 240), (x, y))
        pygame.draw.rect(p, (150, 200, 255), (x, y, w, h), 1, border_radius=10)
        for n, ln in enumerate(lines):
            ui.draw_text(p, ln, ui.font(16, n == 0), (255, 236, 150) if n == 0 else (230, 240, 255), (x + 14, y + 10 + n * 22))
