import math
import random
import time
import pygame
from .base import Scene
from .menu import MenuScene
from .. import ui, icons, art_items, art_fishmail, paper, art_button, cosmetics
from ..ocean import Ocean, WORLD_H
from ..canvas import radial_glow
from .. import config as C

FRONT = (470, 530)
FRONT_POS = (405, 150)
PLAYERS = (900, 560)
PLAYERS_POS = (190, 124)
REST_PIVOT = (378, 142)
REST_SIZE = (486, 486)
REST_PSI = -0.04
FLIP_TIME = 0.95
CAM_LOGIN = WORLD_H - C.BASE_H
CAM_PLAYERS = 1250
CAM_TOP = -448
ENV_C = (667, 470)
SCALE = 9
ROW_H = 58

T_SH = 0.8
T_ENV0, T_ENV1 = 0.4, 1.1
T_SW0, T_SW1 = 1.1, 1.7
T_CL0, T_CL1 = 1.7, 2.05
T_GR0, T_GR1 = 2.05, 2.85
T_HK0, T_HK1 = 2.85, 3.65
T_PL0, T_PL1 = 3.9, 6.1


def ease_io(k):
    """Kurva gerak halus yang lambat di awal dan akhir."""
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def ease_out(k):
    """Kurva gerak yang cepat di awal lalu melambat."""
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


def ease_back(k):
    """Kurva gerak yang melewati target sedikit lalu kembali seperti pegas."""
    k = max(0.0, min(1.0, k))
    return 1 + 2.2 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2


def lerp(a, b, k):
    """Interpolasi linear dua angka."""
    return a + (b - a) * k


def avatar_color(name):
    """Memilih warna avatar yang konsisten dari nama pemain."""
    pal = [(70, 130, 220), (220, 110, 80), (80, 180, 120), (170, 100, 210), (230, 170, 60), (60, 180, 190)]
    return pal[sum(ord(c) for c in name) % len(pal)]


def fmt(n):
    """Mengubah angka menjadi tulisan dengan titik pemisah ribuan."""
    return f"{int(n):,}".replace(",", ".")


def date_text(ts):
    """Mengubah stempel waktu menjadi tanggal singkat atau tanda strip bila kosong."""
    if not ts:
        return "-"
    return time.strftime("%d-%m-%Y", time.localtime(ts))


class LoginScene(Scene):
    """Layar pertama di laut dalam dengan dua kertas lecek bertumpuk berisi isian nama daftar pemain dan papan peringkat lalu animasi amplop melahap kertas menjadi ikan yang dipancing ke permukaan menuju menu utama."""

    exit_button = True
    exit_kind = "menu"
    hud = None

    def __init__(self, app):
        super().__init__(app)
        self.menu = MenuScene(app)
        self.ocean = Ocean()
        self.t = 0.0
        self.view = "login"
        self.view_t = 0.0
        self.state = "idle"
        self.go_t = 0.0
        self.go_img = None
        self.go_view = "login"
        self.go_cam0 = CAM_LOGIN
        self.go_flags = set()
        self.skip = False
        self.drops = []
        self.bubbles = []
        self.base = pygame.Surface((C.BASE_W, C.BASE_H)).convert()
        self.tex_front = paper.make_paper(FRONT[0], FRONT[1], 3)
        self.tex_players = paper.make_paper(PLAYERS[0], PLAYERS[1], 5, wetness=0.8)
        self.tex_reverse = paper.make_paper(PLAYERS[0], PLAYERS[1], 7, tone=(226, 218, 190), show_through=True)
        self.shadow_front = paper.shadow_of(self.tex_front)
        self.shadow_players = paper.shadow_of(self.tex_players)
        self.surf_front = pygame.Surface(FRONT, pygame.SRCALPHA)
        self.surf_players = pygame.Surface(PLAYERS, pygame.SRCALPHA)
        self.rest = None
        self.rest_shadow = None
        self.art = pygame.Surface((C.BASE_W, C.BASE_H)).convert()
        self.ocean.draw(self.art, CAM_LOGIN)
        self.valid = False
        self.msg = ""
        self.input = ui.LineInput((35, 170, 400, 48), ui.font(21), "Type your name here", C.MAX_NAME + 6, on_submit=self.start, on_change=self.on_name)
        self.input.focus = True
        self.btn_start = ui.Button((35, 276, 400, 58), "Start Mission", self.start, "success", icon=icons.icon_fn("play"), size=21)
        self.btn_list = art_button.ArtButton((35, 346, 400, 58), "Player List", self.open_players, "primary", art_button.people_art, (14, 48, 112), size=20)
        self.btn_board = art_button.ArtButton((35, 416, 400, 58), "Leaderboard", lambda: app.open_leaderboard("Back"), "default", art_button.board_art, (255, 255, 255), size=20)
        self.list_rect = pygame.Rect(18, 66, 300, 390)
        self.prof_rect = pygame.Rect(332, 66, 550, 390)
        self.btn_back = ui.Button((18, 478, 190, 50), "Back", self.close_players, "default", icon=icons.icon_fn("back"), size=18)
        self.btn_login = ui.Button((PLAYERS[0] - 18 - 360, 478, 360, 50), "Log In", self.login_selected, "success", icon=icons.icon_fn("play"), size=18)
        self.sel = ""
        self.scroll = 0.0
        self.target = 0.0
        self.drag = None
        self.last_click = (0.0, "")
        self.names = []
        self.on_name("")

    def backdrop_art(self):
        return self.art

    def cam_now(self):
        """Posisi kamera laut yang mengikuti tampilan login atau daftar pemain."""
        return lerp(CAM_LOGIN, CAM_PLAYERS, ease_io(self.view_t))

    def email_origin(self):
        return FRONT_POS

    def players_origin(self):
        return PLAYERS_POS

    def on_name(self, text):
        t = text.strip()
        if not t:
            self.valid, self.msg = False, ""
        else:
            self.valid, self.msg = self.app.players.validate_new(t)
            if self.valid:
                self.msg = "Name available. Ready to start!"
        self.btn_start.enabled = self.valid
        self.btn_start.pulse = self.valid
        self.app.sfx.play("type")

    def start(self):
        """Mendaftarkan nama baru lalu memulai animasi amplop melahap kertas dan ikan ditarik ke permukaan."""
        if self.state != "idle" or self.view != "login" or not self.valid or self.view_t > 0.001:
            return
        name = self.app.players.add(self.input.text)
        self.app.set_player(name)
        self.begin_go("login")

    def open_players(self):
        if self.state != "idle" or self.view_t > 0.001:
            return
        self.names = self.app.players.names()
        if self.app.player_name and self.app.player_name in self.names:
            self.sel = self.app.player_name
        else:
            self.sel = self.names[0] if self.names else ""
        self.scroll = self.target = 0.0
        self.view = "players"
        self.input.focus = False
        self.app.sfx.play("whoosh")

    def close_players(self):
        if self.view_t < 0.999:
            return
        self.view = "login"
        self.app.sfx.play("whoosh")

    def login_selected(self):
        """Masuk sebagai pemain terpilih dari daftar tanpa kata sandi lalu memulai animasi menuju menu."""
        if self.state != "idle" or self.view != "players" or not self.sel or self.view_t < 0.999:
            return
        self.app.set_player(self.sel)
        self.begin_go("players")

    def begin_go(self, view):
        self.state = "go"
        self.go_t = 0.0
        self.go_view = view
        self.go_img = (self.surf_front if view == "login" else self.surf_players).copy()
        self.go_cam0 = self.cam_now()
        self.go_flags = set()
        self.input.focus = False
        self.app.sfx.play("whoosh")

    def local_event(self, e, origin):
        if hasattr(e, "pos"):
            d = dict(e.dict)
            d["pos"] = (e.pos[0] - origin[0], e.pos[1] - origin[1])
            return pygame.event.Event(e.type, d)
        return e

    def local_mouse(self, origin):
        m = self.app.mouse
        return (m[0] - origin[0], m[1] - origin[1])

    def event(self, e):
        if self.state == "go":
            if e.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                self.skip = True
            return
        if 0.001 < self.view_t < 0.999:
            return
        if self.view == "login":
            le = self.local_event(e, FRONT_POS)
            lm = self.local_mouse(FRONT_POS)
            if self.input.handle_event(le, lm):
                return
            for b in (self.btn_start, self.btn_list, self.btn_board):
                if b.handle_event(le, self.app):
                    return
        else:
            self.players_event(e)

    def players_event(self, e):
        le = self.local_event(e, PLAYERS_POS)
        lm = self.local_mouse(PLAYERS_POS)
        for b in (self.btn_back, self.btn_login):
            if b.handle_event(le, self.app):
                return
        if e.type == pygame.MOUSEWHEEL:
            if self.list_rect.collidepoint(lm):
                self.target = max(0, min(self.max_scroll(), self.target - e.y * ROW_H))
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            p = le.pos
            if self.max_scroll() > 0 and self.track().collidepoint(p):
                th = self.thumb()
                if th.collidepoint(p):
                    self.drag = p[1] - th.y
                else:
                    self.target = max(0, min(self.max_scroll(), self.target + (self.list_rect.h if p[1] > th.y else -self.list_rect.h)))
                return
            if self.list_rect.collidepoint(p):
                i = int((p[1] - self.list_rect.y - 4 + self.scroll) // ROW_H)
                if 0 <= i < len(self.names):
                    name = self.names[i]
                    now = time.time()
                    if self.sel == name and now - self.last_click[0] < 0.45 and self.last_click[1] == name:
                        self.login_selected()
                        return
                    self.sel = name
                    self.last_click = (now, name)
                    self.app.sfx.play("click")
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.drag = None
        elif e.type == pygame.MOUSEMOTION and self.drag is not None:
            tr = self.track()
            th = self.thumb()
            span = max(1, tr.h - th.h)
            t = (le.pos[1] - self.drag - tr.y) / span
            self.target = self.scroll = max(0, min(self.max_scroll(), t * self.max_scroll()))
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_DOWN) and self.names:
                i = self.names.index(self.sel) if self.sel in self.names else 0
                i = max(0, min(len(self.names) - 1, i + (1 if e.key == pygame.K_DOWN else -1)))
                self.sel = self.names[i]
                top = i * ROW_H
                if top < self.target:
                    self.target = top
                elif top + ROW_H > self.target + self.list_rect.h - 8:
                    self.target = min(self.max_scroll(), top + ROW_H - self.list_rect.h + 8)
                self.app.sfx.play("hover")
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.login_selected()
            elif e.key == pygame.K_BACKSPACE:
                self.close_players()

    def max_scroll(self):
        return max(0, len(self.names) * ROW_H + 8 - self.list_rect.h)

    def track(self):
        r = self.list_rect
        return pygame.Rect(r.right - 12, r.y + 4, 8, r.h - 8)

    def thumb(self):
        tr = self.track()
        ms = self.max_scroll()
        total = len(self.names) * ROW_H + 8
        h = max(36, int(tr.h * self.list_rect.h / max(1, total)))
        y = tr.y + int((tr.h - h) * (self.scroll / ms)) if ms else tr.y
        return pygame.Rect(tr.x, y, tr.w, h)

    def update(self, dt):
        if self.state == "go" and self.skip:
            dt *= 3.0
        self.t += dt
        self.ocean.update(dt)
        self.menu.tick(dt)
        goal = 1.0 if self.view == "players" else 0.0
        if self.view_t != goal:
            step = dt / FLIP_TIME
            self.view_t = min(goal, self.view_t + step) if goal > self.view_t else max(goal, self.view_t - step)
        if self.state == "go":
            self.update_go(dt)
            return
        if self.view == "login" and self.view_t < 0.01:
            lm = self.local_mouse(FRONT_POS)
            self.input.update(dt, lm)
            for b in (self.btn_start, self.btn_list, self.btn_board):
                b.update(dt, lm)
        elif self.view == "players" and self.view_t > 0.99:
            lm = self.local_mouse(PLAYERS_POS)
            for b in (self.btn_back, self.btn_login):
                b.update(dt, lm)
            self.scroll += (self.target - self.scroll) * min(1.0, dt * 16)
            if abs(self.target - self.scroll) < 0.4:
                self.scroll = self.target
            if self.list_rect.collidepoint(lm):
                ui.HOT["hand"] = True
        self.btn_login.enabled = bool(self.sel)
        self.btn_login.label = f"Log in as {self.sel}" if self.sel else "Log In"

    def flag(self, name, at, sound):
        if name not in self.go_flags and self.go_t >= at:
            self.go_flags.add(name)
            self.app.sfx.play(sound)
            return True
        return False

    def update_go(self, dt):
        self.go_t += dt
        gt = self.go_t
        self.flag("env", T_ENV0 + 0.2, "pop")
        self.flag("swallow", T_SW0 + 0.3, "confirm")
        self.flag("close", T_CL0 + 0.2, "pop")
        self.flag("grow", T_GR0 + 0.1, "aha")
        self.flag("hit", T_HK1, "clang")
        self.flag("pull", T_PL0, "whoosh")
        for d in self.drops:
            d[0] += d[2] * dt
            d[1] += d[3] * dt
            d[3] += 900 * dt
            d[4] -= dt
        self.drops = [d for d in self.drops if d[4] > 0]
        for b in self.bubbles:
            b[1] += b[3] * dt
            b[0] += math.sin(self.t * 5 + b[4]) * 20 * dt
            b[5] -= dt
        self.bubbles = [b for b in self.bubbles if b[5] > 0]
        if gt >= T_PL0 and gt < T_PL1 - 0.8:
            fx, fy = self.fish_pose(gt)[:2]
            if random.random() < dt * 40:
                self.bubbles.append([fx + 70 + random.uniform(-20, 20), fy + random.uniform(-10, 20), random.uniform(3, 8), random.uniform(180, 380), random.uniform(0, 6), 0.9])
        if "splash" not in self.go_flags and gt >= T_PL0:
            sy = -self.pull_cam(gt)
            if sy >= 360:
                self.go_flags.add("splash")
                self.app.sfx.play("pop")
                fx, fy = self.fish_pose(gt)[:2]
                for _ in range(46):
                    a = random.uniform(-2.5, -0.6)
                    v = random.uniform(160, 460)
                    self.drops.append([fx, sy, math.cos(a) * v, math.sin(a) * v, random.uniform(0.5, 0.9)])
        if gt >= T_PL1:
            self.state = "done"
            self.app.set_scene(self.menu)

    def pull_cam(self, gt):
        p = max(0.0, min(1.0, (gt - T_PL0) / (T_PL1 - T_PL0)))
        e = p * p * (3 - 2 * p)
        e = lerp(e, p * p, 0.35)
        return lerp(self.go_cam0, CAM_TOP, e)

    def hook_bite(self):
        return (ENV_C[0] - 112, ENV_C[1] - 18)

    def fish_pose(self, gt):
        """Menghitung posisi pusat ikan sudut skala dan titik kait pada animasi tarikan ke permukaan."""
        p = max(0.0, min(1.0, (gt - T_PL0) / (T_PL1 - T_PL0)))
        bx, by = self.hook_bite()
        ang = -35 * ease_io(p * 3.5)
        vx, vy = ENV_C[0] - bx, ENV_C[1] - by
        r = math.radians(ang)
        cx = bx + vx * math.cos(r) + vy * math.sin(r)
        cy = by - vx * math.sin(r) + vy * math.cos(r)
        sway = math.sin(self.t * 7) * 4 * min(1.0, p * 4)
        cx += sway
        scale = SCALE
        hx, hy = bx, by
        q = ease_io((p - 0.72) / 0.28)
        if q > 0:
            top, center, mang, msway = self.menu.hook_pose()
            mb = (top[0], top[1] + 34 * 4)
            scale = lerp(SCALE, 3, q)
            hx, hy = lerp(bx, mb[0], q), lerp(by, mb[1], q)
            cx, cy = lerp(cx, center[0], q), lerp(cy, center[1], q)
            ang = lerp(ang, mang, q)
        return cx, cy, ang, scale, hx, hy, q

    def draw_background(self, surf, cam, blend=0.0):
        self.ocean.draw(surf, cam, self.menu.bg)
        if blend > 0.01:
            self.menu.draw_backdrop(self.base)
            self.base.set_alpha(int(255 * blend))
            surf.blit(self.base, (0, 0))
            self.base.set_alpha(255)

    def draw_title(self, surf, rise=0.0):
        title = self.menu.title
        bob = math.sin(self.t * 1.6) * 4
        tr = title.get_rect(midtop=(C.BASE_W // 2, 12 + bob - rise))
        if tr.bottom < -20:
            return
        gl = radial_glow(260, (60, 140, 220), 0.22)
        gl = pygame.transform.scale(gl, (760, 240))
        surf.blit(gl, gl.get_rect(center=tr.center), special_flags=pygame.BLEND_RGB_ADD)
        surf.blit(title, tr)
        tw, th = title.get_size()
        band = pygame.Surface((tw, th), pygame.SRCALPHA)
        bx = int((self.menu.shine / 2.2) * (tw + 200)) - 100
        pygame.draw.polygon(band, (255, 255, 255, 235), [(bx, 0), (bx + 36, 0), (bx - 4, th), (bx - 40, th)])
        shine = title.copy()
        shine.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        shine.blit(band, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(shine, tr)

    def draw_front(self):
        s = self.surf_front
        s.blit(self.tex_front, (0, 0))
        ui.draw_text(s, "Hello, player!", ui.font(30, True), (26, 44, 92), (FRONT[0] // 2, 24), "midtop")
        lines = ui.wrap_lines(ui.font(16), "You will write phishing emails to fool the AI email guard. Type your name to start the mission.", 380)
        for i, ln in enumerate(lines):
            ui.draw_text(s, ln, ui.font(16, True), (44, 34, 24), (FRONT[0] // 2, 72 + i * 22), "midtop")
        ui.draw_text(s, "PLAYER NAME", ui.font(13, True), (112, 98, 70), (37, 150))
        state = "normal"
        if self.input.text.strip():
            state = "good" if self.valid else "bad"
        self.input.draw(s, state)
        if self.msg:
            col = (30, 130, 66) if self.valid else (190, 52, 44)
            ic = "check" if self.valid else "warning"
            icons.draw_icon(s, ic, (46, 238), 18, col)
            ui.draw_text(s, self.msg, ui.font(14, True), col, (64, 238), "midleft")
        for b in (self.btn_start, self.btn_list, self.btn_board):
            b.draw(s)
        self.draw_drip(s)

    def draw_drip(self, s):
        cyc = self.t % 8.0
        if cyc > 3.4:
            return
        k = cyc / 3.4
        y = 10 + (k ** 1.6) * (FRONT[1] - 70)
        x = FRONT[0] - 22
        ov = pygame.Surface((24, FRONT[1]), pygame.SRCALPHA)
        pygame.draw.line(ov, (120, 160, 196, 60), (12, 8), (12, int(y)), 3)
        pygame.draw.circle(ov, (206, 232, 250, 150), (12, int(y)), 6)
        pygame.draw.circle(ov, (90, 130, 170, 150), (13, int(y) + 2), 4, 1)
        pygame.draw.circle(ov, (255, 255, 255, 230), (10, int(y) - 2), 2)
        s.blit(ov, (x - 12, 0))

    def draw_players(self):
        s = self.surf_players
        s.blit(self.tex_players, (0, 0))
        ui.draw_text(s, "Player List", ui.font(30, True), (26, 44, 92), (26, 16))
        cnt = f"{len(self.names)} player" + ("" if len(self.names) == 1 else "s")
        cs = ui.text_surf(ui.font(14, True), cnt, (255, 255, 255))
        pill = pygame.Rect(26 + 236, 24, cs.get_width() + 22, 26)
        pygame.draw.rect(s, (70, 130, 214), pill, border_radius=13)
        s.blit(cs, cs.get_rect(center=pill.center))
        self.draw_list(s)
        self.draw_profile(s)
        for b in (self.btn_back, self.btn_login):
            b.draw(s)

    def draw_list(self, surf):
        r = self.list_rect
        pygame.draw.rect(surf, (253, 252, 248), r, border_radius=6)
        old = surf.get_clip()
        surf.set_clip(r.inflate(-2, -2))
        lm = self.local_mouse(PLAYERS_POS)
        board = {row["name"].lower(): i for i, row in enumerate(self.app.players.leaderboard(1000))}
        if not self.names:
            icons.draw_icon(surf, "users", (r.centerx, r.centery - 30), 56, (190, 204, 228))
            ui.draw_text(surf, "No players registered yet", ui.font(16, True), (90, 104, 136), (r.centerx, r.centery + 14), "midtop")
            ui.draw_text(surf, "Go back and create your name", ui.font(14), (130, 142, 166), (r.centerx, r.centery + 40), "midtop")
        for i, name in enumerate(self.names):
            y = r.y + 4 + i * ROW_H - int(self.scroll)
            if y > r.bottom or y + ROW_H < r.y:
                continue
            row = pygame.Rect(r.x + 4, y, r.w - (22 if self.max_scroll() else 8), ROW_H - 4)
            sel = name == self.sel
            hov = row.collidepoint(lm) and r.collidepoint(lm)
            look = self.app.eggs.look(name)
            if sel:
                pygame.draw.rect(surf, (214, 232, 255), row, border_radius=8)
            elif hov:
                pygame.draw.rect(surf, (238, 244, 254), row, border_radius=8)
            if look["banner"] != "n0":
                tmp = pygame.Surface(row.size, pygame.SRCALPHA)
                cosmetics.draw_banner(tmp, pygame.Rect(0, 0, row.w, row.h), look["banner"])
                veil = pygame.Surface(row.size, pygame.SRCALPHA)
                veil.fill((255, 255, 255, 70 if sel else 40))
                tmp.blit(veil, (0, 0))
                tmp.blit(ui.rounded_mask(row.w, row.h, 8), (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                surf.blit(tmp, row)
            if sel:
                pygame.draw.rect(surf, (70, 130, 214), row, 2, border_radius=8)
            ac = (row.x + 30, row.centery)
            pygame.draw.circle(surf, avatar_color(name), ac, 21)
            pygame.draw.circle(surf, (255, 255, 255), ac, 21, 2)
            icons.draw_icon(surf, "user", ac, 26, (255, 255, 255))
            cosmetics.draw_border(surf, ac, 21, look["border"])
            plate = look["banner"] != "n0"
            st = self.app.players.stats(name)
            label = name if len(name) <= 14 else name[:13] + ".."
            sub = f"Best {fmt(st['best'])}  |  {st['games']}x played" if st["games"] else "Never played"
            if plate:
                pw = max(ui.font(17, True).size(label)[0], ui.font(13).size(sub)[0]) + 16
                pl = pygame.Surface((pw, 44), pygame.SRCALPHA)
                pygame.draw.rect(pl, (255, 255, 255, 205), pl.get_rect(), border_radius=8)
                surf.blit(pl, (row.x + 56, row.y + 3))
            ui.draw_text(surf, label, ui.font(17, True), (24, 40, 78), (row.x + 62, row.y + 9))
            ui.draw_text(surf, sub, ui.font(13), (96, 110, 140), (row.x + 62, row.y + 31))
            rank = board.get(name.lower())
            if rank is not None and rank < 3:
                icons.draw_icon(surf, "crown", (row.right - 22, row.centery), 22, [(240, 190, 30), (150, 164, 190), (196, 118, 60)][rank])
            if name == self.app.player_name:
                tag = pygame.Rect(0, 0, 44, 16)
                tag.topright = (row.right - 8, row.y + 4)
                pygame.draw.rect(surf, (60, 170, 100), tag, border_radius=8)
                ui.draw_text(surf, "ACTIVE", ui.font(10, True), (255, 255, 255), tag.center, "center")
        surf.set_clip(old)
        pygame.draw.rect(surf, (126, 148, 184), r, 1, border_radius=6)
        if self.max_scroll() > 0:
            tr = self.track()
            pygame.draw.rect(surf, (232, 236, 242), tr, border_radius=4)
            th = self.thumb()
            surf.blit(ui.button_surface(th.w, th.h, "default", "hover" if self.drag is not None else "normal", 4), th)

    def draw_profile(self, surf):
        r = self.prof_rect
        pygame.draw.rect(surf, (253, 252, 248), r, border_radius=6)
        pygame.draw.rect(surf, (126, 148, 184), r, 1, border_radius=6)
        if not self.sel:
            ui.draw_text(surf, "Select a player to view the profile", ui.font(17), (130, 142, 166), r.center, "center")
            return
        st = self.app.players.stats(self.sel)
        top = pygame.Rect(r.x + 1, r.y + 1, r.w - 2, 112)
        for yy in range(top.h):
            c = tuple(int(a + (b - a) * yy / top.h) for a, b in zip((226, 238, 255), (250, 252, 255)))
            pygame.draw.line(surf, c, (top.x, top.y + yy), (top.right - 1, top.y + yy))
        look = self.app.eggs.look(self.sel)
        if look["banner"] != "n0":
            cosmetics.draw_banner(surf, top, look["banner"])
            pl = pygame.Surface((r.w - 130, 100), pygame.SRCALPHA)
            pygame.draw.rect(pl, (255, 255, 255, 205), pl.get_rect(), border_radius=12)
            surf.blit(pl, (r.x + 118, r.y + 8))
        face = self.app.assets.portrait("happy", 96)
        surf.blit(face, (r.x + 16, r.y + 8))
        cosmetics.draw_border(surf, (r.x + 64, r.y + 56), 46, look["border"])
        ui.draw_text(surf, st["name"], ui.font(28, True), (20, 44, 92), (r.x + 128, r.y + 14))
        ui.draw_text(surf, f"Registered {date_text(st['created'])}   |   Last played {date_text(st['last'])}", ui.font(13), (96, 110, 140), (r.x + 128, r.y + 52))
        rank = f"Rank #{st['rank']}" if st["rank"] else "Unranked"
        col = (236, 170, 30) if st["rank"] else (150, 160, 182)
        rs = ui.text_surf(ui.font(14, True), rank, (255, 255, 255))
        pill = pygame.Rect(r.x + 128, r.y + 76, rs.get_width() + 44, 26)
        pygame.draw.rect(surf, col, pill, border_radius=13)
        icons.draw_icon(surf, "trophy", (pill.x + 16, pill.centery), 16, (255, 255, 255))
        surf.blit(rs, rs.get_rect(midleft=(pill.x + 30, pill.centery)))
        tiles = (("Games played", fmt(st["games"]), (70, 130, 214)), ("Best score", fmt(st["best"]), (236, 170, 30)), ("Average score", fmt(st["avg"]), (60, 180, 190)), ("Missions won", fmt(st["won"]), (80, 180, 120)), ("Best money", "$" + fmt(st["money_best"]), (170, 100, 210)), ("Malware jackpots", fmt(st["jackpots"]), (220, 110, 80)))
        for i, (lab, val, c) in enumerate(tiles):
            tx = r.x + 16 + (i % 3) * 172
            ty = r.y + 126 + (i // 3) * 88
            tile = pygame.Rect(tx, ty, 162, 76)
            pygame.draw.rect(surf, (244, 247, 252), tile, border_radius=8)
            pygame.draw.rect(surf, (206, 216, 234), tile, 1, border_radius=8)
            pygame.draw.rect(surf, c, (tile.x, tile.y + 8, 5, tile.h - 16), border_radius=3)
            ui.draw_text(surf, lab, ui.font(13), (96, 110, 140), (tile.x + 16, tile.y + 10))
            ui.draw_text(surf, val, ui.font(28, True), (24, 40, 78), (tile.x + 16, tile.y + 32))
        by = r.y + 126 + 2 * 88 + 6
        ui.draw_text(surf, "Emails passed vs caught", ui.font(13, True), (96, 110, 140), (r.x + 16, by))
        bar = pygame.Rect(r.x + 16, by + 22, 514, 18)
        pygame.draw.rect(surf, (226, 232, 244), bar, border_radius=9)
        total = st["passed"] + st["caught"]
        if total:
            w = int(bar.w * st["passed"] / total)
            if w > 0:
                pygame.draw.rect(surf, (80, 190, 120), (bar.x, bar.y, w, bar.h), border_radius=9)
            if bar.w - w > 8:
                pygame.draw.rect(surf, (226, 100, 84), (bar.x + max(w, 9), bar.y, bar.w - max(w, 9), bar.h), border_top_right_radius=9, border_bottom_right_radius=9)
            ui.draw_text(surf, f"Passed {st['passed']}", ui.font(13, True), (36, 130, 70), (bar.x, bar.bottom + 4))
            ui.draw_text(surf, f"Caught {st['caught']}", ui.font(13, True), (196, 70, 56), (bar.right, bar.bottom + 4), "topright")
        else:
            ui.draw_text(surf, "No game data yet", ui.font(13), (130, 142, 166), (bar.centerx, bar.centery), "center")

    def back_paper(self, u):
        """Merender kertas belakang yang terbalik dengan tepi bertumpu pada sudut kiri atas pada progres flip u lalu mengembalikan Surface dan posisinya atau None."""
        e = ease_io(u)
        theta = math.pi * (1 - e)
        pivot = (lerp(REST_PIVOT[0], PLAYERS_POS[0], e), lerp(REST_PIVOT[1], PLAYERS_POS[1], e))
        w = lerp(REST_SIZE[0], PLAYERS[0], e)
        h = lerp(REST_SIZE[1], PLAYERS[1], e)
        quad = paper.project(pivot, w, h, theta, REST_PSI * (1 - e))
        tex = self.tex_reverse if math.cos(theta) < 0 else self.surf_players
        shade = 0.62 + 0.38 * abs(math.cos(theta))
        res = paper.warp(tex, quad, shade)
        return res, quad

    def draw_flat(self, surf, tex, shadow, pos):
        surf.blit(shadow, (pos[0] - 14 + 8, pos[1] - 14 + 14))
        surf.blit(tex, pos)

    def draw_papers(self, surf):
        u = self.view_t
        if u < 0.003:
            if self.rest is None:
                self.rest = self.back_paper(0.0)
                self.rest_shadow = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
                pygame.draw.polygon(self.rest_shadow, (2, 10, 28, 90), [(x + 10, y + 14) for x, y in self.rest[1]])
            res, quad = self.rest
            if res:
                surf.blit(self.rest_shadow, (0, 0))
                surf.blit(res[0], res[1])
            self.draw_flat(surf, self.surf_front, self.shadow_front, FRONT_POS)
            return
        if u > 0.997:
            self.draw_flat(surf, self.surf_players, self.shadow_players, PLAYERS_POS)
            return
        res, quad = self.back_paper(u)
        e = ease_io(u)

        def paint_flip():
            sh = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
            pygame.draw.polygon(sh, (2, 10, 28, 80), [(x + 12, y + 16) for x, y in quad])
            surf.blit(sh, (0, 0))
            if res:
                surf.blit(res[0], res[1])
            else:
                pygame.draw.polygon(surf, (236, 228, 204), quad)

        if e < 0.12:
            paint_flip()
            self.draw_flat(surf, self.surf_front, self.shadow_front, FRONT_POS)
        else:
            self.draw_flat(surf, self.surf_front, self.shadow_front, FRONT_POS)
            paint_flip()

    def draw_envelope_stack(self, surf, gt, paper_img, paper_center, paper_scale):
        rise = ease_back((gt - T_ENV0) / (T_ENV1 - T_ENV0))
        yoff = (1 - rise) * 560
        tl = (ENV_C[0] - 15 * SCALE, ENV_C[1] - 11 * SCALE + yoff)
        closing = ease_io((gt - T_CL0) / (T_CL1 - T_CL0))
        back = art_fishmail.layer("back", SCALE)
        pocket = art_fishmail.layer("pocket", SCALE)
        flap = art_fishmail.layer("flap", SCALE, closing)
        glow = radial_glow(200, (120, 190, 255), 0.4)
        surf.blit(glow, glow.get_rect(center=(ENV_C[0], ENV_C[1] + yoff)), special_flags=pygame.BLEND_RGB_ADD)
        surf.blit(back, tl)
        if closing <= 0.0:
            surf.blit(flap, tl)
        if paper_img is not None:
            w, h = paper_img.get_size()
            img = pygame.transform.smoothscale(paper_img, (max(2, int(w * paper_scale)), max(2, int(h * paper_scale))))
            surf.blit(img, img.get_rect(center=paper_center))
        surf.blit(pocket, tl)
        if closing > 0.0:
            surf.blit(flap, tl)

    def draw_go(self, surf):
        gt = self.go_t
        pull_started = gt >= T_PL0
        cam = self.pull_cam(gt) if pull_started else self.go_cam0
        blend = 0.0
        p = max(0.0, min(1.0, (gt - T_PL0) / (T_PL1 - T_PL0)))
        if pull_started:
            blend = ease_io((p - 0.86) / 0.14)
        self.draw_background(surf, cam, blend)
        self.draw_title(surf, ease_io(gt / 1.1) * 240)
        if gt < T_GR0:
            u1 = ease_io(gt / T_SH)
            big = self.go_view == "players"
            c0 = (PLAYERS_POS[0] + PLAYERS[0] / 2, PLAYERS_POS[1] + PLAYERS[1] / 2) if big else (FRONT_POS[0] + FRONT[0] / 2, FRONT_POS[1] + FRONT[1] / 2)
            s0 = 1.0
            s1 = 0.3 if not big else 0.2
            sw = ease_io((gt - T_SW0) / (T_SW1 - T_SW0))
            sc = lerp(lerp(s0, s1, u1), 0.14 if not big else 0.09, sw)
            cy = lerp(lerp(c0[1], 300, u1), 488, sw)
            cx = lerp(c0[0], 640, u1)
            if self.go_view == "login" and gt < T_SH and self.rest is not None and self.rest[0]:
                img = self.rest[0][0].copy()
                img.set_alpha(int(255 * (1 - u1)))
                surf.blit(img, self.rest[0][1])
            if gt < T_ENV0 + 0.05:
                self.draw_shrinking(surf, sc, (cx, cy))
            else:
                self.draw_envelope_stack(surf, gt, self.go_img, (cx, cy), sc)
        else:
            self.draw_fish_sequence(surf, gt)
        for b in self.bubbles:
            a = max(0.0, min(1.0, b[5] / 0.9))
            pygame.draw.circle(surf, (200, 240, 255), (int(b[0]), int(b[1])), int(b[2]), 1)
        if pull_started:
            self.draw_speed(surf, gt, p)
        for d in self.drops:
            pygame.draw.circle(surf, (210, 240, 255), (int(d[0]), int(d[1])), 3)
        if blend > 0.01:
            layer = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
            self.menu.draw_ui(layer)
            layer.set_alpha(int(255 * blend ** 1.5))
            surf.blit(layer, (0, 0))

    def draw_shrinking(self, surf, sc, center):
        w, h = self.go_img.get_size()
        img = pygame.transform.smoothscale(self.go_img, (max(2, int(w * sc)), max(2, int(h * sc))))
        sh = paper.shadow_of(img, 6, 90)
        surf.blit(sh, (center[0] - sh.get_width() // 2 + 4, center[1] - sh.get_height() // 2 + 8))
        surf.blit(img, img.get_rect(center=center))

    def draw_fish_sequence(self, surf, gt):
        ex = 0.0
        if gt < T_PL0:
            g = (gt - T_GR0) / (T_GR1 - T_GR0)
            tail = ease_back(g)
            eye = ease_back((g - 0.3) / 0.7)
            sq = 1 + 0.07 * math.sin(max(0.0, g) * math.pi * 3) * (1 - min(1.0, g))
            img = art_fishmail.fish(SCALE, tail, eye)
            wig = math.sin(self.t * 6) * 3 if g > 0.8 else 0
            if gt >= T_HK1:
                k = (gt - T_HK1) / (T_PL0 - T_HK1)
                wig = math.sin(k * 20) * 6 * (1 - k)
                sq = 1 + 0.08 * math.sin(k * 14) * (1 - k)
            img = pygame.transform.smoothscale(img, (int(img.get_width() * (2 - sq)), int(img.get_height() * sq)))
            img = pygame.transform.rotate(img, wig)
            if 0 < g < 0.6:
                r = int(40 + g * 400)
                ring = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
                pygame.draw.circle(ring, (200, 235, 255, int(200 * (1 - g / 0.6))), (r + 3, r + 3), r, 4)
                surf.blit(ring, ring.get_rect(center=ENV_C))
            surf.blit(img, img.get_rect(center=ENV_C))
            if gt >= T_HK0:
                hk = ease_out((gt - T_HK0) / (T_HK1 - T_HK0))
                bx, by = self.hook_bite()
                sprite = art_items.hook(6)
                y_final = by - 34 * 6
                y = lerp(-260, y_final, hk)
                pygame.draw.rect(surf, (210, 216, 226), (int(bx), 0, 6, max(0, int(y) + 4)))
                surf.blit(sprite, (bx - 8 * 6, y))
                if gt >= T_HK1:
                    k = (gt - T_HK1) / (T_PL0 - T_HK1)
                    fl = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
                    pygame.draw.circle(fl, (255, 255, 255, int(220 * (1 - k))), (bx, by), int(20 + 80 * k))
                    surf.blit(fl, (0, 0))
            return
        cx, cy, ang, scale, hx, hy, q = self.fish_pose(gt)
        img = art_fishmail.fish(SCALE, 1.0, 1.0)
        f = scale / SCALE
        if abs(f - 1) > 0.01:
            img = pygame.transform.smoothscale(img, (max(2, int(img.get_width() * f)), max(2, int(img.get_height() * f))))
        img = pygame.transform.rotate(img, ang)
        hs = lerp(6, 4, q)
        sprite = art_items.hook(6)
        sprite = pygame.transform.smoothscale(sprite, (max(2, int(sprite.get_width() * hs / 6)), max(2, int(sprite.get_height() * hs / 6))))
        top_y = hy - 34 * hs
        pygame.draw.rect(surf, (210, 216, 226), (int(hx), 0, max(2, int(hs)), max(0, int(top_y) + 4)))
        surf.blit(sprite, (hx - sprite.get_width() / 2, top_y))
        surf.blit(img, img.get_rect(center=(cx, cy)))

    def draw_speed(self, surf, gt, p):
        speed = math.sin(min(1.0, p / 0.72) * math.pi)
        rs = random.Random(int(gt * 40))
        layer = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
        for _ in range(int(34 * speed)):
            x = rs.randrange(C.BASE_W)
            y = rs.randrange(-100, C.BASE_H)
            ln = rs.randrange(60, 220)
            pygame.draw.line(layer, (220, 245, 255, int(90 * speed)), (x, y), (x, y + ln), 2)
        surf.blit(layer, (0, 0))

    def draw(self, surf):
        if self.state == "go":
            self.draw_go(surf)
            return
        cam = self.cam_now()
        self.ocean.draw(surf, cam)
        if self.view_t < 0.999:
            self.draw_front()
        if self.view_t > 0.001:
            self.draw_players()
        self.draw_papers(surf)
        self.draw_title(surf)
