import math
import random
import pygame
from .base import Scene
from .. import ui, icons, art_egg, egg_data
from ..canvas import radial_glow, mix
from ..splash import Splash
from ..egg_inventory import InventoryModal
from .. import config as C

PIVOT = (1166, 598)
ROD_LEN = 350
BAR = pygame.Rect(320, 556, 640, 42)
FISH = egg_data.FISH


def clamp(v, a=0.0, b=1.0):
    """Membatasi nilai pada rentang tertentu."""
    return max(a, min(b, v))


def lerp(a, b, k):
    """Interpolasi linear dua angka."""
    return a + (b - a) * k


def ease_out(k):
    """Kurva gerak melambat di akhir."""
    k = clamp(k)
    return 1 - (1 - k) ** 3


def ease_back(k):
    """Kurva muncul yang melewati target sedikit lalu kembali."""
    k = clamp(k)
    return 1 + 2.2 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2


class EggScene(Scene):
    """Mini game memancing malam hari dengan joran, indikator waktu, cuaca yang memburuk menurut kelangkaan ikan, popup tangkapan, dan inventaris tersimpan."""

    exit_kind = "egg"
    music_level = 1.0
    music_track = C.FISHING_MUSIC_PATH
    hud = None

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.st = 0.0
        self.state = "idle"
        self.idx = 0
        self.done = 0
        self.force_idx = None
        self.bg = art_egg.build_backdrop(C.BASE_W, C.BASE_H)
        self.stars = art_egg.stars()
        self.world = pygame.Surface((C.BASE_W, C.BASE_H)).convert()
        self.splash = Splash()
        self.w = 0.0
        self.goal = 0.0
        self.ang = 62.0
        self.bend = 0.0
        self.lure = [700.0, 450.0]
        self.target = [700.0, 450.0]
        self.lure_on = False
        self.lure_from = (0.0, 0.0)
        self.release = (0.0, 0.0)
        self.wait_for = 2.0
        self.fish_a = 0.0
        self.reel_k = 0.0
        self.dart = 0.0
        self.bar_a = 0.0
        self.marker_ph = 0.0
        self.bar_t = 0.0
        self.green = 0.4
        self.remain = 0.0
        self.limit = 1.0
        self.miss = 0.0
        self.hit_flash = 0.0
        self.stage_flash = 0.0
        self.popup = None
        self.popup_t = 0.0
        self.fresh = False
        self.space_down = False
        self.rs = random.Random()
        self.splashed = False
        self.drops = [[self.rs.uniform(0, C.BASE_W + 200), self.rs.uniform(0, C.BASE_H), self.rs.uniform(0.8, 1.25)] for _ in range(460)]
        self.bubbles = []
        self.gust = 0.0
        self.ratchet_t = 0.0
        self.creak_t = 0.0
        self.wiggle_t = 0.0
        self.wallet_rect = pygame.Rect(290, 14, 124, 46)
        self.jingle = False
        self.double = 0.0
        self.sky_dark = None
        self.flash = 0.0
        self.bolt = []
        self.bolt_t = 0.0
        self.lt_timer = 2.0
        self.thunder_in = -1.0
        self.ripple_t = 0.0
        self.shake = (0.0, 0.0)
        self.start_btn = ui.Button((540, 626, 200, 60), "START", self.start, "success", icon=icons.icon_fn("play"), size=24)
        self.start_btn.pulse = True
        self.bag_rect = pygame.Rect(222, 14, 58, 46)
        self.bag_hover = False
        self.bag_down = False
        self.ok_btn = ui.Button((0, 0, 150, 48), "Nice!", self.close_popup, "success", icon=icons.icon_fn("check"), size=19)
        self.glows = {}
        self.lantern = radial_glow(90, (255, 190, 80), 0.55)

    def enter(self):
        self.app.sfx.play("whoosh", 0.5)

    def backdrop_art(self):
        return self.bg

    def start(self):
        """Memulai satu lemparan dengan mengundi ikan tersembunyi lalu memutar joran ke belakang dan melempar umpan."""
        if self.state != "idle" or self.popup:
            return
        self.idx = self.force_idx if self.force_idx is not None else egg_data.roll(self.rs)
        self.done = 0
        self.state = "cast"
        self.st = 0.0
        self.lure_on = False
        self.target = [self.rs.uniform(500, 780), self.rs.uniform(410, 470)]
        self.app.sfx.play("cast", 0.8)

    def open_inventory(self):
        """Membuka popup inventaris dengan latar buram dari layar saat ini."""
        if self.app.modal or self.app.fade is not None:
            return
        self.app.audio.close()
        self.app.sfx.play("pop")

        def close():
            self.app.modal = None

        self.app.modal = InventoryModal(self.app, self.app.stage.copy(), close)

    def close_popup(self):
        """Menutup popup tangkapan lalu kembali ke keadaan awal siap melempar."""
        if self.popup:
            self.popup = None
            self.state = "idle"
            self.st = 0.0
            self.fish_a = 0.0

    def tip(self, a=None, bend=None):
        """Menghitung ujung joran pada sudut dan lengkung tertentu."""
        pts = self.rod_points(self.ang if a is None else a, self.bend if bend is None else bend)
        return pts[-1]

    def rod_points(self, a, bend):
        """Menghitung titik sepanjang joran yang melengkung ke arah laut."""
        r = math.radians(a)
        dx, dy = -math.cos(r), -math.sin(r)
        px, py = -math.sin(r), math.cos(r)
        pv = self.pivot()
        out = []
        for i in range(17):
            s = i / 16
            out.append((pv[0] + dx * ROD_LEN * s + px * bend * s * s, pv[1] + dy * ROD_LEN * s + py * bend * s * s))
        return out

    def pivot(self):
        """Mengambil titik pangkal joran yang ikut naik turun mengikuti ayunan perahu."""
        return (PIVOT[0], PIVOT[1] + self.rock()[0])

    def rock(self):
        """Menghitung ayunan perahu berupa geser vertikal dan sudut putar yang membesar saat cuaca buruk."""
        w = self.w
        dy = math.sin(self.t * 1.7) * (2.0 + 13.0 * w) + math.sin(self.t * 4.1) * 3.0 * w
        ang = math.sin(self.t * 1.3 + 1.0) * (0.7 + 6.0 * w)
        return dy, ang

    def event(self, e):
        if self.popup:
            self.ok_btn.handle_event(e, self.app)
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) and not self.space_down:
                self.space_down = True
                self.app.sfx.play("click")
                self.close_popup()
            elif e.type == pygame.KEYUP and e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.space_down = False
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.close_x().collidepoint(e.pos):
                self.app.sfx.play("click")
                self.close_popup()
            return
        if e.type == pygame.KEYUP and e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            self.space_down = False
            return
        if e.type == pygame.MOUSEMOTION:
            self.bag_hover = self.bag_rect.collidepoint(e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.bag_rect.collidepoint(e.pos):
            self.bag_down = True
            return
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            was = self.bag_down
            self.bag_down = False
            if was and self.bag_rect.collidepoint(e.pos):
                self.open_inventory()
                return
        if self.start_btn.handle_event(e, self.app):
            return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.space_down:
                    return
                self.space_down = True
                if self.state == "idle":
                    self.app.sfx.play("click")
                    self.start()
                else:
                    self.press()
            elif e.key == pygame.K_i:
                self.open_inventory()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.press()

    def new_stage(self):
        """Menyiapkan satu tahap indikator dengan zona hijau baru yang menyempit menurut kelangkaan ikan dan waktu yang cukup untuk beberapa lintasan."""
        f = FISH[self.idx]
        gw = f["green"]
        prev = self.green
        for _ in range(8):
            g = self.rs.uniform(0.05, 0.95 - gw)
            if abs(g - prev) > 0.18:
                break
        self.green = g
        self.limit = f["passes"] * f["period"]
        self.remain = self.limit
        self.start_mania()
        self.bar_t = 0.0
        self.marker_ph = self.rs.random()
        self.miss = 0.0
        self.state = "bar"
        self.st = 0.0

    def marker(self):
        """Menghitung posisi penanda merah antara nol dan satu dengan gerak bolak balik beraturan."""
        f = FISH[self.idx]
        u = (self.bar_t / f["period"] + self.marker_ph) % 1.0
        u = u + f["wobble"] * math.sin(4 * math.pi * u + self.marker_ph * 6.28) / (4 * math.pi)
        return 1 - abs(2 * (u % 1.0) - 1)

    def press(self):
        """Memproses satu tekanan pemain pada indikator dengan hasil kena zona hijau atau meleset yang memangkas waktu tersembunyi."""
        if self.state != "bar" or self.bar_a < 0.6:
            return
        f = FISH[self.idx]
        m = self.marker()
        gw = f["green"]
        if self.green - 0.01 <= m <= self.green + gw + 0.01:
            self.done += 1
            self.hit_flash = 1.0
            self.stage_flash = 1.0
            self.app.sfx.play("ding")
            if self.done >= f["stages"]:
                self.state = "reel"
                self.st = 0.0
                self.reel_k = 0.0
            else:
                self.state = "pause"
                self.st = 0.0
                self.target[0] = clamp(self.target[0] + self.rs.choice((-1, 1)) * self.rs.uniform(40, 110), 380, 840)
                self.target[1] = clamp(self.target[1] + self.rs.uniform(-24, 24), 405, 485)
                self.app.sfx.play("pop", 0.6)
        else:
            self.remain -= f["miss"]
            self.miss = 1.0
            self.app.sfx.play("error", 0.5)
            if self.remain <= 0:
                self.fail()

    def start_mania(self):
        """Memulai lagu Mancing Mania berulang saat ikan tersangkut dan mengecilkan musik latar."""
        if not self.jingle:
            self.jingle = True
            self.app.sfx.set_loop("mania", 0.22)

    def stop_mania(self):
        """Menghentikan lagu Mancing Mania dengan memudar lalu mengembalikan musik latar."""
        self.jingle = False
        self.app.sfx.set_loop("mania", 0.0)

    def fail(self):
        """Mengakhiri percobaan tanpa teks gagal dengan menarik umpan kembali dan membiarkan cuaca mereda perlahan."""
        self.stop_mania()
        self.state = "fail"
        self.st = 0.0
        self.lure_from = (self.lure[0], self.lure[1])

    def finish_catch(self):
        """Menyimpan ikan ke koleksi dan membuka popup informasi tanpa latar buram."""
        self.fresh = self.app.eggs.add(self.idx)
        self.popup = {"idx": self.idx, "total": len(self.app.eggs.catches)}
        self.popup_t = 0.0
        self.state = "popup"
        self.st = 0.0
        self.lure_on = False
        self.stop_mania()
        self.app.sfx.play("win" if self.idx < 3 else "fanfare", 0.35)

    def glow(self, idx):
        """Mengambil cahaya radial berwarna kelangkaan dari cache."""
        g = self.glows.get(idx)
        if g is None:
            g = radial_glow(100, FISH[idx]["color"], 0.8)
            self.glows[idx] = g
        return g

    def update(self, dt):
        self.t += dt
        self.st += dt
        m = self.app.mouse
        self.bag_hover = self.bag_rect.collidepoint(m)
        if self.bag_hover:
            ui.HOT["hand"] = True
        self.start_btn.visible = self.state == "idle" and not self.popup
        self.start_btn.update(dt, m)
        if self.popup:
            self.popup_t += dt
            self.place_popup()
            self.ok_btn.update(dt, m)
        self.splash.update(dt)
        self.hit_flash = max(0.0, self.hit_flash - dt * 3.5)
        self.stage_flash = max(0.0, self.stage_flash - dt * 2.0)
        self.miss = max(0.0, self.miss - dt * 4.0)
        self.step_state(dt)
        self.step_weather(dt)
        self.step_water(dt)
        self.music_level = 0.3 if self.jingle else 1.0
        self.step_rod(dt)

    def step_state(self, dt):
        """Menjalankan mesin keadaan permainan dari idle hingga lempar menunggu gigitan indikator tarik dan hasil."""
        s = self.state
        f = FISH[self.idx]
        if s == "cast":
            if self.st >= 0.52 and not self.lure_on:
                self.lure_on = True
                self.release = self.tip()
            if self.lure_on:
                e = clamp((self.st - 0.52) / 0.6)
                x = lerp(self.release[0], self.target[0], e)
                y = lerp(self.release[1], self.target[1], e) - 150 * 4 * e * (1 - e)
                self.lure = [x, y]
                if e >= 1.0:
                    self.lure = list(self.target)
                    self.splash.add(self.lure[0], self.lure[1], 0.9)
                    self.app.sfx.play("plop", 0.9)
                    self.app.sfx.play("splash", 0.6)
                    self.state = "wait"
                    self.st = 0.0
                    self.wait_for = self.rs.uniform(1.4, 3.0)
                    self.ripple_t = 0.0
        elif s == "wait":
            self.ripple_t += dt
            if self.ripple_t > 1.3:
                self.ripple_t = 0.0
                self.splash.ripple(self.lure[0], self.lure[1], 0.35)
            self.follow(dt)
            if self.st >= self.wait_for:
                self.state = "bite"
                self.st = 0.0
                self.app.sfx.play("bite")
        elif s == "bite":
            self.follow(dt)
            self.fish_a = min(1.0, self.fish_a + dt * 2.5)
            if self.st >= 0.9:
                self.new_stage()
        elif s == "bar":
            self.follow(dt)
            self.fish_a = min(1.0, self.fish_a + dt * 3)
            self.bar_t += dt
            self.remain -= dt
            self.creak_t -= dt
            if self.remain < self.limit * 0.4 and self.creak_t <= 0:
                self.creak_t = 0.55
                self.app.sfx.play("creak", 0.5)
            if self.remain <= 0:
                self.fail()
        elif s == "pause":
            self.follow(dt, 6.0)
            self.dart = ease_out(1 - self.st / max(0.1, f["pause"]))
            if self.st >= f["pause"]:
                self.new_stage()
        elif s == "reel":
            self.follow(dt)
            self.reel_k = clamp(self.st / 1.5)
            self.ratchet_t -= dt
            if self.ratchet_t <= 0:
                self.ratchet_t = 0.085
                self.app.sfx.play("ratchet", 0.6)
            if self.st > 0.62 and not self.splashed:
                self.splashed = True
                self.stop_mania()
                self.splash.add(self.lure[0], self.lure[1], 1.3)
                self.app.sfx.play("splash", 0.55)
            if self.st >= 1.6:
                self.splashed = False
                self.finish_catch()
        elif s == "fail":
            self.fish_a = max(0.0, self.fish_a - dt * 2.2)
            e = clamp((self.st - 0.3) / 0.9)
            self.ratchet_t -= dt
            if 0 < e < 1 and self.ratchet_t <= 0:
                self.ratchet_t = 0.07
                self.app.sfx.play("ratchet", 0.5)
            tip = self.tip()
            k = e * e
            self.lure = [lerp(self.lure_from[0], tip[0], k), lerp(self.lure_from[1], tip[1], k) - 40 * math.sin(math.pi * e)]
            if e >= 1.0:
                self.lure_on = False
                self.state = "idle"
                self.st = 0.0
        elif s == "popup":
            self.fish_a = max(0.0, self.fish_a - dt * 3)
        if s in ("idle", "cast", "popup"):
            self.dart = 0.0
        if s not in ("bite", "bar", "pause", "reel", "wait", "fail"):
            self.fish_a = max(0.0, self.fish_a - dt * 3)
        bar_on = s == "bar"
        self.bar_a = clamp(self.bar_a + (dt / 0.22 if bar_on else -dt / 0.25))

    def follow(self, dt, rate=3.5):
        """Menggeser posisi umpan perlahan menuju titik target baru."""
        self.lure[0] += (self.target[0] - self.lure[0]) * min(1.0, dt * rate)
        self.lure[1] += (self.target[1] - self.lure[1]) * min(1.0, dt * rate)

    def step_rod(self, dt):
        """Mengatur sudut dan lengkung joran menurut keadaan dengan putaran pelontar saat melempar."""
        s = self.state
        if s == "cast":
            st = self.st
            if st < 0.35:
                self.ang = lerp(62, 108, ease_out(st / 0.35))
            elif st < 0.58:
                k = (st - 0.35) / 0.23
                self.ang = lerp(108, 30, k * k)
            else:
                self.ang = lerp(30, 34, clamp((st - 0.58) / 0.5))
            tb = 28.0 + 14 * math.sin(math.pi * clamp((self.st - 0.3) / 0.3))
        else:
            if s in ("wait", "bite", "bar", "pause", "reel", "fail"):
                ta = 34.0
            else:
                ta = 62.0 + math.sin(self.t * 1.4) * 1.2
            self.ang += (ta - self.ang) * min(1.0, dt * 6)
            tb = 28.0 + math.sin(self.t * 1.1) * 2.0
            if s in ("bar", "pause"):
                tb = 36 + 7 * self.idx + math.sin(self.t * 24) * (1.5 + self.idx * 0.6)
                if s == "bar":
                    fr = self.remain / max(0.01, self.limit)
                    tb += math.sin(self.t * 50) * clamp((0.4 - fr) / 0.4) * 5
            elif s == "reel":
                tb = 54 + 6 * self.idx
            elif s == "bite":
                tb = 32 + math.sin(self.t * 20) * 3
        self.bend += (tb - self.bend) * min(1.0, dt * 8)

    def step_weather(self, dt):
        """Menggeser tingkat cuaca halus menuju target naik cepat dan reda perlahan lalu mengatur hujan angin petir guncangan dan suara latar."""
        s = self.state
        f = FISH[self.idx]
        if s in ("bar", "pause", "reel", "bite"):
            prog = (self.done + (1 if s == "reel" else 0)) / f["stages"]
            self.goal = f["storm"] * clamp(0.5 + 0.5 * prog)
            if s == "bite":
                self.goal = f["storm"] * 0.35
        else:
            self.goal = 0.0
        if self.goal > self.w:
            self.w = min(self.goal, self.w + 0.7 * dt)
        else:
            self.w = max(self.goal, self.w - 0.3 * dt)
        w = self.w
        amount = clamp((w - 0.08) / 0.92)
        self.gust = 0.5 + 0.5 * math.sin(self.t * 0.7) * math.sin(self.t * 1.9 + 1.0)
        wind = 140 + 420 * w * (0.6 + 0.4 * self.gust)
        n = int(len(self.drops) * amount)
        for d in self.drops[:n]:
            d[1] += (900 + 760 * w) * d[2] * dt
            d[0] -= wind * dt
            if d[1] > C.BASE_H + 20:
                d[1] = self.rs.uniform(-80, -10)
                d[0] = self.rs.uniform(0, C.BASE_W + 500)
        self.flash = max(0.0, self.flash - dt * 3.2)
        self.bolt_t = max(0.0, self.bolt_t - dt)
        if self.double > 0:
            self.double -= dt
            if self.double <= 0:
                self.flash = 0.9
                self.bolt_t = 0.16
        if w > 0.55:
            self.lt_timer -= dt
            if self.lt_timer <= 0:
                heavy = clamp((w - 0.55) / 0.45)
                self.lt_timer = self.rs.uniform(0.7, 1.4) * lerp(3.4, 1.0, heavy)
                self.strike()
                if self.rs.random() < 0.35 + 0.4 * heavy:
                    self.double = 0.14
        if self.thunder_in > 0:
            self.thunder_in -= dt
            if self.thunder_in <= 0:
                self.app.sfx.play("thunder", 1.0)
        self.app.sfx.set_loop("rain", amount * 0.95)
        if s == "idle" and self.jingle:
            self.stop_mania()
        amp = max(0.0, w - 0.15) * 22 * (0.7 + 0.5 * self.gust)
        self.shake = (math.sin(self.t * 47) * amp * 0.6 + math.sin(self.t * 29 + 1) * amp * 0.4, math.sin(self.t * 41 + 2) * amp * 0.5 + math.sin(self.t * 23) * amp * 0.3)

    def strike(self):
        """Memunculkan satu sambaran petir bercabang dengan kilatan layar dan gemuruh yang menyusul."""
        self.flash = 1.0
        self.bolt_t = 0.24
        x = self.rs.uniform(120, 1060)
        pts = [(x, 0)]
        y = 0
        while y < art_egg.HORIZON + 10:
            y += self.rs.uniform(24, 46)
            x += self.rs.uniform(-40, 40)
            pts.append((x, y))
        lines = [pts]
        for i in self.rs.sample(range(2, len(pts) - 1), 2):
            bx, by = pts[i]
            d = self.rs.choice((-1, 1))
            br = [(bx, by)]
            for _ in range(3):
                bx += d * self.rs.uniform(14, 34)
                by += self.rs.uniform(16, 32)
                br.append((bx, by))
            lines.append(br)
        self.bolt = lines
        self.thunder_in = self.rs.uniform(0.15, 0.6)

    def draw_world(self, surf):
        """Menggambar langit laut perahu joran umpan dan efek cuaca badai pada satu permukaan dunia."""
        w = self.w
        surf.blit(self.bg, (0, 0))
        for (x, y, ph, sz) in self.stars:
            a = (0.5 + 0.5 * math.sin(self.t * 2.2 + ph)) * (1 - w * 0.95)
            c = int(90 + 165 * a)
            if a > 0.05:
                surf.fill((c, c, 255), (x, y, sz, sz))
        if w > 0.03:
            for i, cl in enumerate(art_egg.clouds()):
                x = (i * 330 + self.t * (14 + w * 60)) % (C.BASE_W + 520) - 520
                cl.set_alpha(int(min(255, w * 380)))
                surf.blit(cl, (x, 2 + i * 34))
            if self.sky_dark is None:
                self.sky_dark = pygame.Surface((C.BASE_W, art_egg.HORIZON + 30), pygame.SRCALPHA)
                for y in range(art_egg.HORIZON + 30):
                    pygame.draw.line(self.sky_dark, (4, 8, 22, int(255 * (1 - y / (art_egg.HORIZON + 30)) ** 1.2)), (0, y), (C.BASE_W, y))
            self.sky_dark.set_alpha(int(w * 230))
            surf.blit(self.sky_dark, (0, 0))
        self.draw_sea(surf)
        self.splash.draw(surf)
        self.draw_bubbles(surf)
        self.draw_fish(surf)
        self.draw_boat(surf)
        self.draw_line_and_lure(surf)
        self.draw_front(surf)
        amount = clamp((w - 0.08) / 0.92)
        n = int(len(self.drops) * amount)
        if n:
            wind = 140 + 420 * w * (0.6 + 0.4 * self.gust)
            col = mix((120, 150, 200), (200, 222, 250), w)
            ln = 18 + 28 * w
            wd = 2 if w > 0.6 else 1
            for d in self.drops[:n]:
                pygame.draw.line(surf, col, (d[0], d[1]), (d[0] - wind * 0.03, d[1] + ln), wd)
        if w > 0.45:
            col = mix((60, 80, 120), (170, 195, 235), w)
            for i in range(14):
                x = (self.t * (900 + 40 * i) + i * 211) % (C.BASE_W + 500) - 250
                y = (i * 97 + 40) % C.BASE_H
                pygame.draw.line(surf, col, (C.BASE_W - x, y), (C.BASE_W - x + 90 + 4 * i, y + 3), 1)
        if w > 0.02:
            dark = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
            dark.fill((0, 4, 18, int(w * 150)))
            surf.blit(dark, (0, 0))
        if self.bolt_t > 0 and self.bolt:
            for ln in self.bolt:
                pygame.draw.lines(surf, (150, 190, 255), False, ln, 9 if ln is self.bolt[0] else 5)
                pygame.draw.lines(surf, (255, 255, 255), False, ln, 4 if ln is self.bolt[0] else 2)
        if self.flash > 0.01:
            fl = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
            fl.fill((220, 230, 255, int(200 * self.flash)))
            surf.blit(fl, (0, 0))

    def sea_color(self, y):
        """Memperkirakan warna air pada ketinggian tertentu untuk mewarnai gelombang."""
        t = clamp((y - art_egg.HORIZON) / (C.BASE_H - art_egg.HORIZON))
        return mix((18, 44, 92), (3, 10, 30), t ** 0.8)

    def draw_sea(self, surf):
        """Menggambar barisan gelombang bergerak dengan pantulan bulan yang membesar amplitudenya saat cuaca buruk."""
        w = self.w
        hz = art_egg.HORIZON
        speed = 1.0 + w * 2.8
        for k in range(13):
            y0 = hz + 8 + (k ** 1.55) * 9.2
            amp = (1.0 + k * 0.5) * (1 + w * 4.6)
            wl = 70 + k * 28
            pts = []
            for x in range(-20, C.BASE_W + 40, 20):
                pts.append((x, y0 + math.sin(x / wl * 2 + self.t * speed * (0.8 + k * 0.1) + k * 1.7) * amp))
            base = self.sea_color(y0)
            crest = mix(base, (120, 170, 230), 0.2 + 0.025 * k)
            trough = mix(base, (0, 6, 20), 0.35)
            pygame.draw.lines(surf, trough, False, [(x, y + 3 + k * 0.4) for x, y in pts], 2 + k // 4)
            pygame.draw.lines(surf, crest, False, pts, 1 + k // 5)
            if w > 0.4:
                fr = random.Random(k * 7)
                for i in range(int(8 + 14 * w)):
                    fx = (fr.randrange(C.BASE_W) + self.t * 30 * (1 + k * 0.2)) % C.BASE_W
                    fy = y0 + math.sin(fx / wl * 2 + self.t * speed * (0.8 + k * 0.1) + k * 1.7) * amp - 1
                    if math.sin(self.t * 5 + i + k) > 0.1:
                        surf.fill((214, 232, 250), (fx, fy, 2 + k // 3, 2))
            if w < 0.75:
                gl = 1 - w * 1.3
                for i in range(6):
                    gx = 930 + math.sin(self.t * 0.9 + i * 2.1 + k) * (8 + k * 3) + (i - 3) * (2 + k * 0.7)
                    gy = y0 + math.sin(gx / wl * 2 + self.t * speed * (0.8 + k * 0.1) + k * 1.7) * amp
                    gwid = int((4 + k * 2.4) * (0.5 + 0.5 * math.sin(self.t * 3 + i + k)))
                    if gwid > 1:
                        c = mix(base, (236, 232, 200), clamp(0.9 * gl))
                        surf.fill(c, (gx - gwid // 2, gy, gwid, 2))

    def draw_bubbles(self, surf):
        """Menggambar gelembung yang naik dari bawah umpan sebagai tanda ada sesuatu yang meronta tanpa memperlihatkan ikannya."""
        for b in self.bubbles:
            a = clamp(b[4] * 2.2)
            ring = pygame.Surface((b[3] * 2 + 4, b[3] * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (200, 232, 255, int(170 * a)), (b[3] + 2, b[3] + 2), b[3], 1)
            surf.blit(ring, (b[0] - b[3] - 2, b[1] - b[3] - 2))

    def step_water(self, dt):
        """Memunculkan gelembung dan riak di sekitar umpan selama ikan tersangkut agar gerak ikan terasa tanpa terlihat."""
        for b in self.bubbles:
            b[1] -= b[2] * dt
            b[0] += math.sin(self.t * 6 + b[3]) * 10 * dt
            b[4] -= dt * 0.9
        self.bubbles = [b for b in self.bubbles if b[4] > 0 and b[1] > self.lure[1]]
        if self.state in ("bite", "bar", "pause") and self.lure_on:
            rate = 5 + 5 * self.idx + (8 if self.state == "pause" else 0)
            if self.rs.random() < rate * dt:
                self.bubbles.append([self.lure[0] + self.rs.uniform(-30, 30), self.lure[1] + self.rs.uniform(30, 80), self.rs.uniform(40, 80), self.rs.randint(2, 5), 1.0])
            self.wiggle_t += dt
            if self.wiggle_t > max(0.22, 0.7 - 0.1 * self.idx):
                self.wiggle_t = 0.0
                self.splash.ripple(self.lure[0] + self.rs.uniform(-20, 20), self.lure[1] + self.rs.uniform(-3, 5), 0.3 + 0.1 * self.idx)

    def draw_fish(self, surf):
        """Menggambar ikan hanya setelah ditarik keluar dari air lalu menggelepar di atas permukaan dengan kilau warna kelangkaan."""
        if self.state != "reel" or not self.lure_on:
            return
        idx = self.idx
        lx, ly = self.lure
        k = clamp(self.st / 1.4)
        e = k * k * (3 - 2 * k)
        fy = lerp(ly + 60, ly - 80, e)
        fx = lx - 20 * e
        ang = math.sin(self.t * 20) * (24 - 10 * e)
        clip = surf.get_clip()
        surf.set_clip(pygame.Rect(0, 0, C.BASE_W, int(ly + 2)))
        if idx >= 2 and fy < ly:
            g = pygame.transform.smoothscale(self.glow(idx), (260, 200))
            g.fill((int(160 * clamp((ly - fy) / 60)),) * 3, special_flags=pygame.BLEND_RGB_MULT)
            surf.blit(g, g.get_rect(center=(fx, fy)), special_flags=pygame.BLEND_RGB_ADD)
        spr = pygame.transform.rotate(art_egg.fishmail(idx, 3), ang)
        surf.blit(spr, spr.get_rect(center=(fx, fy)))
        surf.set_clip(clip)

    def draw_boat(self, surf):
        """Menggambar perahu berlentera yang berayun lalu joran yang melengkung bersama penggulung."""
        dy, ang = self.rock()
        b = art_egg.boat()
        bx, by = 1010, 560
        img = pygame.transform.rotate(b, ang) if abs(ang) > 0.05 else b
        r = img.get_rect(center=(bx + b.get_width() // 2, by + b.get_height() // 2 + dy))
        surf.blit(img, r)
        fl = 0.8 + 0.2 * math.sin(self.t * 9) * math.sin(self.t * 4.3)
        lg = self.lantern.copy()
        lg.fill((int(255 * fl),) * 3, special_flags=pygame.BLEND_RGB_MULT)
        surf.blit(lg, lg.get_rect(center=(bx + 71 * 3, by + 5 * 3 + dy)), special_flags=pygame.BLEND_RGB_ADD)
        pts = self.rod_points(self.ang, self.bend)
        n = len(pts)
        for i in range(n - 1):
            wd = max(2, int(lerp(8, 2, i / (n - 2))))
            col = (84, 52, 30) if i < 3 else (26, 30, 42)
            pygame.draw.line(surf, col, pts[i], pts[i + 1], wd)
            if i >= 3:
                pygame.draw.line(surf, (120, 132, 156), (pts[i][0] - 1, pts[i][1] - 2), (pts[i + 1][0] - 1, pts[i + 1][1] - 2), 1)
        for i in (5, 8, 11, 14):
            pygame.draw.circle(surf, (210, 214, 224), (int(pts[i][0]), int(pts[i][1]) + 3), 2, 1)
        rp = pts[2]
        pygame.draw.circle(surf, (40, 44, 56), (int(rp[0]), int(rp[1]) + 8), 9)
        pygame.draw.circle(surf, (190, 196, 210), (int(rp[0]), int(rp[1]) + 8), 7)
        pygame.draw.circle(surf, (70, 80, 100), (int(rp[0]), int(rp[1]) + 8), 3)

    def draw_line_and_lure(self, surf):
        """Menggambar benang dari ujung joran ke pelampung dengan kendur yang berubah menurut ketegangan lalu pelampung yang terendam sebagian."""
        if not self.lure_on:
            tip = self.tip()
            pygame.draw.line(surf, (216, 228, 242), tip, (tip[0] - 4, tip[1] + 34), 1)
            return
        tip = self.tip()
        lx, ly = self.lure
        s = self.state
        if s in ("bar", "pause"):
            lx += math.sin(self.t * 31) * (1.5 + 0.8 * self.idx)
            ly += math.sin(self.t * 23) * 1.5
        dip = 0.0
        if s == "bite":
            dip = max(0.0, math.sin(self.st * 16)) * 12
        elif s in ("bar", "pause"):
            dip = 9 + math.sin(self.t * 26) * 2.5
        elif s == "reel":
            dip = 14
        sag = 26.0
        if s == "cast":
            sag = 0.0
        elif s in ("bar", "pause", "reel"):
            sag = 5.0
        elif s == "bite":
            sag = 12.0
        bob = math.sin(self.t * 2.2) * 2
        top = ly + bob + dip - 24
        pts = []
        for i in range(21):
            u = i / 20
            x = lerp(tip[0], lx, u)
            y = lerp(tip[1], top, u) + math.sin(math.pi * u) * sag
            pts.append((x, y))
        pygame.draw.lines(surf, (220, 232, 246), False, pts, 1)
        if s == "cast" and self.st < 0.52:
            return
        bob_img = art_egg.bobber(3)
        vis = max(8, 26 - int(dip))
        part = bob_img.subsurface((0, 0, bob_img.get_width(), min(vis, bob_img.get_height()))).copy()
        surf.blit(part, (lx - part.get_width() // 2, ly + bob + dip - part.get_height()))
        ring = pygame.Surface((46, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (210, 235, 255, 150), (2, 2, 42, 8), 1)
        surf.blit(ring, ring.get_rect(center=(lx, ly + bob + dip)))

    def draw_front(self, surf):
        """Menggambar gelombang terdepan yang menutupi dasar perahu agar terlihat mengapung di air."""
        w = self.w
        base = 676
        amp = 3 + w * 9
        pts = [(x, base + math.sin(x / 70 + self.t * (2.0 + w * 2)) * amp) for x in range(-20, C.BASE_W + 40, 20)]
        poly = pts + [(C.BASE_W + 40, C.BASE_H), (-20, C.BASE_H)]
        pygame.draw.polygon(surf, (6, 18, 44), poly)
        pygame.draw.lines(surf, (70, 120, 190), False, pts, 2)

    def place_popup(self):
        """Mengatur posisi tombol popup tangkapan di dalam jendela."""
        r = self.popup_rect()
        self.ok_btn.rect.bottomright = (r.right - 28, r.bottom - 24)

    def popup_rect(self):
        """Menghitung kotak jendela popup tangkapan di tengah layar."""
        r = pygame.Rect(0, 0, 640, 380)
        r.center = (C.BASE_W // 2, 330)
        return r

    def close_x(self):
        """Menghitung area tombol X jendela popup tangkapan pada koordinat layar."""
        r = self.popup_rect()
        return pygame.Rect(r.right - 8 - 98 + 52, r.y + 1, 46, 20)

    def draw_popup(self, surf):
        """Menggambar popup tangkapan berisi gambar ikan nama kelangkaan keterangan dan tips tanpa mengaburkan latar."""
        p = self.popup
        f = FISH[p["idx"]]
        r = self.popup_rect()
        k = ease_back(self.popup_t / 0.4)
        panel = pygame.Surface(r.size, pygame.SRCALPHA)
        client = ui.draw_window(panel, pygame.Rect(0, 0, r.w, r.h), "New Catch - Phisherman", icon=lambda s, c, z, col: icons.draw_icon(s, "star", c, z, (255, 224, 110)))
        hot = pygame.Rect(r.w - 8 - 98 + 52, 1, 46, 20)
        if self.close_x().collidepoint(self.app.mouse):
            pygame.draw.rect(panel, (255, 120, 100), hot, border_bottom_right_radius=5)
            pygame.draw.line(panel, (255, 255, 255), (hot.x + 17, hot.y + 5), (hot.x + 27, hot.y + 14), 3)
            pygame.draw.line(panel, (255, 255, 255), (hot.x + 27, hot.y + 5), (hot.x + 17, hot.y + 14), 3)
        pygame.draw.rect(panel, (244, 248, 255), client)
        art = pygame.Rect(client.x + 14, client.y + 14, 230, 230)
        sky = pygame.Surface(art.size)
        for y in range(art.h):
            pygame.draw.line(sky, mix((10, 22, 56), (30, 62, 120), y / art.h), (0, y), (art.w, y))
        gl = radial_glow(120, f["color"], 0.9)
        gl.fill((int(150 + 80 * math.sin(self.t * 3)),) * 3, special_flags=pygame.BLEND_RGB_MULT)
        sky.blit(gl, gl.get_rect(center=(art.w // 2, art.h // 2)), special_flags=pygame.BLEND_RGB_ADD)
        rs = random.Random(3)
        for _ in range(16):
            sx, sy = rs.randrange(art.w), rs.randrange(art.h)
            c = int(120 + 120 * (0.5 + 0.5 * math.sin(self.t * 3 + sx)))
            sky.fill((c, c, 255), (sx, sy, 2, 2))
        idx = p["idx"]
        img = art_egg.fishmail(idx, 4 if idx < 3 else 3)
        if img.get_width() > art.w - 20:
            img = pygame.transform.smoothscale(img, (art.w - 20, int(img.get_height() * (art.w - 20) / img.get_width())))
        bob = math.sin(self.t * 2.6) * 6
        sky.blit(img, img.get_rect(center=(art.w // 2, art.h // 2 + bob)))
        panel.blit(sky, art)
        pygame.draw.rect(panel, (20, 40, 80), art, 2)
        x0 = art.right + 22
        pill = ui.text_surf(ui.font(15, True), f["rarity"].upper(), (255, 255, 255))
        pr = pygame.Rect(x0, client.y + 18, pill.get_width() + 24, 26)
        pygame.draw.rect(panel, tuple(int(c * 0.62) for c in f["color"]), pr, border_radius=13)
        pygame.draw.rect(panel, f["color"], pr, 2, border_radius=13)
        panel.blit(pill, pill.get_rect(center=pr.center))
        if self.fresh:
            nb = ui.text_surf(ui.font(14, True), "NEW", (255, 255, 255))
            nr = pygame.Rect(pr.right + 8, pr.y, nb.get_width() + 18, 26)
            pygame.draw.rect(panel, (226, 70, 60), nr, border_radius=13)
            panel.blit(nb, nb.get_rect(center=nr.center))
        ui.draw_text(panel, f["name"], ui.font(26, True), (20, 44, 92), (x0, pr.bottom + 12))
        y = pr.bottom + 56
        for ln in ui.wrap_lines(ui.font(17), f["info"], client.right - x0 - 16):
            ui.draw_text(panel, ln, ui.font(17), (52, 64, 90), (x0, y))
            y += 24
        tip = pygame.Rect(x0, y + 8, client.right - x0 - 14, 66)
        pygame.draw.rect(panel, (255, 246, 214), tip, border_radius=8)
        pygame.draw.rect(panel, (220, 180, 70), tip, 1, border_radius=8)
        ui.draw_text(panel, "TIP", ui.font(13, True), (176, 120, 20), (tip.x + 12, tip.y + 8))
        yy = tip.y + 26
        for ln in ui.wrap_lines(ui.font(15), f["tip"], tip.w - 24):
            ui.draw_text(panel, ln, ui.font(15), (80, 60, 20), (tip.x + 12, yy))
            yy += 20
        ui.draw_text(panel, f"Sell value: ${f['price']}   |   Fish in your inventory: {p['total']}", ui.font(14), (100, 112, 140), (client.x + 18, client.bottom - 40))
        panel.set_alpha(int(255 * clamp(self.popup_t * 5)))
        if k < 0.999:
            ww, hh = max(1, int(r.w * (0.84 + 0.16 * k))), max(1, int(r.h * (0.84 + 0.16 * k)))
            panel = pygame.transform.smoothscale(panel, (ww, hh))
        sh = pygame.Surface((r.w + 40, r.h + 40), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 34), sh.get_rect().inflate(-18, -18), border_radius=18)
        surf.blit(sh, (r.x - 20, r.y - 12))
        surf.blit(panel, panel.get_rect(center=r.center))
        if k >= 0.999:
            self.ok_btn.draw(surf)

    def draw_bar(self, surf):
        """Menggambar indikator persegi panjang dengan zona hijau dan penanda merah yang bergetar makin kuat saat waktu menipis tanpa menampilkan sisa waktu."""
        a = self.bar_a
        if a <= 0.01:
            return
        f = FISH[self.idx]
        fr = clamp(self.remain / max(0.01, self.limit))
        sk = clamp((0.45 - fr) / 0.45)
        amp = (sk ** 1.4) * 16 + self.miss * 6
        ox = math.sin(self.t * 70) * amp + math.sin(self.t * 43) * amp * 0.5
        oy = math.sin(self.t * 61 + 1) * amp * 0.4
        r = BAR.move(int(ox), int(oy))
        scale = 0.9 + 0.1 * ease_back(a)
        layer = pygame.Surface((BAR.w + 60, BAR.h + 90), pygame.SRCALPHA)
        lr = pygame.Rect(30, 56, BAR.w, BAR.h)
        ui.draw_text(layer, "Press SPACE or click when the red mark is in the green zone", ui.font(15, True), (230, 244, 255), (lr.centerx, 22), "center", shadow=(0, 12, 40))
        pygame.draw.rect(layer, (0, 0, 0, 90), lr.inflate(10, 12).move(0, 5), border_radius=14)
        layer.blit(ui.glass(lr.w + 10, lr.h + 10, 12, (30, 56, 100), 235), (lr.x - 5, lr.y - 5))
        inner = lr.inflate(-6, -6)
        pygame.draw.rect(layer, (8, 16, 38), inner, border_radius=8)
        for i in range(1, 16):
            x = inner.x + int(inner.w * i / 16)
            pygame.draw.line(layer, (30, 48, 86), (x, inner.y + 6), (x, inner.bottom - 6))
        gx = inner.x + int(inner.w * self.green)
        gw = int(inner.w * f["green"])
        zone = pygame.Rect(gx, inner.y, gw, inner.h)
        pulse = 0.5 + 0.5 * math.sin(self.t * 6)
        glow = pygame.Surface((zone.w + 24, zone.h + 24), pygame.SRCALPHA)
        pygame.draw.rect(glow, (90, 255, 140, int(60 + 50 * pulse + 120 * self.hit_flash)), glow.get_rect(), border_radius=14)
        layer.blit(glow, (zone.x - 12, zone.y - 12))
        for y in range(zone.h):
            c = mix((110, 244, 150), (24, 150, 70), y / max(1, zone.h - 1))
            pygame.draw.line(layer, c, (zone.x, zone.y + y), (zone.right - 1, zone.y + y))
        pygame.draw.rect(layer, (255, 255, 255, 120), (zone.x, zone.y, zone.w, 5))
        pygame.draw.rect(layer, (220, 255, 230), zone, 2, border_radius=3)
        mx = inner.x + int(inner.w * self.marker())
        mc = (255, 255, 255) if self.miss > 0.4 else (240, 50, 46)
        pygame.draw.rect(layer, (255, 80, 70, 90), (mx - 8, inner.y - 6, 16, inner.h + 12), border_radius=6)
        pygame.draw.rect(layer, mc, (mx - 3, inner.y - 5, 6, inner.h + 10), border_radius=2)
        pygame.draw.rect(layer, (255, 190, 180), (mx - 1, inner.y - 5, 2, inner.h + 10))
        pygame.draw.polygon(layer, mc, [(mx - 8, inner.y - 10), (mx + 8, inner.y - 10), (mx, inner.y - 2)])
        pygame.draw.polygon(layer, mc, [(mx - 8, inner.bottom + 10), (mx + 8, inner.bottom + 10), (mx, inner.bottom + 2)])
        if self.miss > 0:
            ov = pygame.Surface(lr.size, pygame.SRCALPHA)
            pygame.draw.rect(ov, (255, 60, 50, int(90 * self.miss)), ov.get_rect(), border_radius=10)
            layer.blit(ov, lr)
        if scale < 0.999:
            layer = pygame.transform.smoothscale(layer, (int(layer.get_width() * scale), int(layer.get_height() * scale)))
        layer.set_alpha(int(255 * a))
        surf.blit(layer, layer.get_rect(center=(r.centerx, r.centery - 10)))

    def draw_wallet(self, surf):
        """Menggambar jumlah uang hasil jual ikan milik pemain aktif di samping tombol inventaris."""
        txt = ui.text_surf(ui.font(19, True), f"${self.app.eggs.money}", (255, 246, 210))
        r = pygame.Rect(self.wallet_rect.x, self.wallet_rect.y, 52 + txt.get_width() + 14, self.wallet_rect.h)
        surf.blit(ui.glass(r.w, r.h, 12, (60, 50, 20), 205), r)
        pygame.draw.circle(surf, (232, 168, 20), (r.x + 26, r.centery), 14)
        pygame.draw.circle(surf, (255, 240, 170), (r.x + 26, r.centery), 10, 2)
        ui.draw_text(surf, "$", ui.font(15, True), (140, 90, 0), (r.x + 26, r.centery), "center")
        surf.blit(txt, txt.get_rect(midleft=(r.x + 48, r.centery)))

    def draw_ui(self, surf):
        """Menggambar tombol inventaris tombol mulai indikator dan popup tangkapan di atas dunia permainan."""
        st = "pressed" if self.bag_down and self.bag_hover else ("hover" if self.bag_hover else "normal")
        surf.blit(ui.button_surface(self.bag_rect.w, self.bag_rect.h, "dark", st), self.bag_rect)
        ic = art_egg.tackle_icon(2)
        surf.blit(ic, ic.get_rect(center=(self.bag_rect.centerx - 2, self.bag_rect.centery + 1)))
        total = len(self.app.eggs.catches)
        if total:
            txt = str(min(total, 99)) + ("+" if total > 99 else "")
            ts = ui.text_surf(ui.font(12, True), txt, (255, 255, 255))
            br = pygame.Rect(0, 0, max(20, ts.get_width() + 10), 20)
            br.center = (self.bag_rect.right - 6, self.bag_rect.y + 6)
            pygame.draw.rect(surf, (226, 70, 60), br, border_radius=10)
            pygame.draw.rect(surf, (255, 255, 255), br, 1, border_radius=10)
            surf.blit(ts, ts.get_rect(center=br.center))
        self.draw_wallet(surf)
        if self.state == "idle" and not self.popup:
            ui.draw_text(surf, "Cast your line and wait for a bite", ui.font(17, True), (220, 238, 255), (C.BASE_W // 2, 604), "center", shadow=(0, 12, 40))
            self.start_btn.draw(surf)
        self.draw_bar(surf)
        if self.popup:
            self.draw_popup(surf)

    def draw(self, surf):
        self.draw_world(self.world)
        surf.blit(self.world, (0, 0))
        if abs(self.shake[0]) + abs(self.shake[1]) > 0.3:
            surf.blit(self.world, (int(self.shake[0]), int(self.shake[1])))
        self.draw_ui(surf)
