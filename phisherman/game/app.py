import pygame
from . import config as C
from . import ui, icons, art_items
from .assets import Assets
from .hud import Hud
from .audio_panel import AudioPanel
from .modal import ExitModal
from .session import Session
from .players import PlayerStore
from .leaderboard import LeaderboardModal
from .sfx import Sfx
from .egg_data import EggStore


class App:
    """Inti game yang mengelola jendela skala dinamis scene transisi modal HUD dan siklus utama."""

    def __init__(self, adapter, size=None):
        pygame.init()
        pygame.key.set_repeat(380, 32)
        pygame.display.set_caption("Phisherman")
        if size is None:
            info = pygame.display.Info()
            w = min(C.BASE_W, max(800, info.current_w - 60))
            h = min(C.BASE_H, max(480, info.current_h - 110))
            size = (w, h)
        self.window = pygame.display.set_mode(size, pygame.RESIZABLE)
        try:
            pygame.display.set_icon(art_items.envelope_fish(2))
        except Exception:
            pass
        self.adapter = adapter
        self.sfx = Sfx()
        self.assets = Assets()
        self.session = Session()
        self.players = PlayerStore(persist=not getattr(adapter, "test_mode", False))
        self.player_name = ""
        self.eggs = EggStore(persist=not getattr(adapter, "test_mode", False))
        self.stage = pygame.Surface((C.BASE_W, C.BASE_H)).convert()
        self.clock = pygame.time.Clock()
        self.hud = Hud(self)
        self.scene = None
        self.modal = None
        self.fade = None
        self.running = True
        self.mouse = (0, 0)
        self.scale = 1.0
        self.offset = (0, 0)
        self.cursor = None
        self.esc_held = False
        self.backdrops = {}
        self.audio = AudioPanel(self)
        self.exit_btn = ui.Button((18, 14, 138, 46), "EXIT", self.request_exit, "danger", icon=icons.icon_fn("exit"), size=18)

    def layout(self):
        ww, wh = pygame.display.get_surface().get_size()
        self.scale = max(0.1, min(1.0, ww / C.BASE_W, wh / C.BASE_H))
        sw, sh = int(C.BASE_W * self.scale), int(C.BASE_H * self.scale)
        self.offset = ((ww - sw) // 2, (wh - sh) // 2)
        return ww, wh, sw, sh

    def to_logical(self, pos):
        return ((pos[0] - self.offset[0]) / self.scale, (pos[1] - self.offset[1]) / self.scale)

    def set_scene(self, scene):
        self.scene = scene
        self.sfx.stop_loops()
        scene.enter()
        self.hud.snap()

    def goto(self, factory):
        if self.fade is None:
            self.fade = {"phase": "out", "t": 0.0, "factory": factory}

    def go_login(self):
        from .scenes.login import LoginScene
        self.goto(lambda: LoginScene(self))

    def set_player(self, name):
        """Mengaktifkan pemain terpilih dan menandai waktu masuknya."""
        self.player_name = name
        self.eggs.use(name)
        self.session.player = name
        self.players.touch(name)

    def open_leaderboard(self, close_label="Close"):
        """Membuka popup papan peringkat dari scene mana pun dengan latar buram dan label tombol penutup yang bisa disesuaikan."""
        if self.modal or self.fade is not None:
            return
        self.audio.close()

        def close():
            self.modal = None

        self.modal = LeaderboardModal(self, self.stage.copy(), close, close_label)

    def go_menu(self):
        from .scenes.menu import MenuScene
        self.goto(lambda: MenuScene(self))

    def go_story(self):
        from .scenes.cutscene import CutsceneScene
        self.session.reset()
        self.goto(lambda: CutsceneScene(self))

    def go_live(self):
        from .scenes.live import LiveScene
        self.goto(lambda: LiveScene(self))

    def go_egg(self):
        from .scenes.egg import EggScene
        self.goto(lambda: EggScene(self))

    def request_exit(self):
        if self.scene and not self.modal and not self.fade:
            self.scene.on_exit_request()

    def open_exit(self, kind):
        if self.modal:
            return
        self.audio.close()

        def confirm():
            self.modal = None
            if kind == "menu":
                self.quit()
            else:
                self.go_menu()

        def cancel():
            self.modal = None

        self.modal = ExitModal(self, kind, confirm, cancel, self.stage.copy())

    def quit(self):
        self.running = False

    def dispatch(self, e):
        if e.type == pygame.QUIT:
            self.quit()
            return
        if e.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            e.pos = self.to_logical(e.pos)
        if e.type == pygame.KEYUP and e.key == pygame.K_ESCAPE:
            self.esc_held = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_F9:
                self.sfx.toggle_mute()
                return
        if self.fade is not None:
            return
        if self.modal:
            self.modal.event(e)
            return
        if self.audio.event(e):
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if not self.esc_held:
                self.esc_held = True
                self.scene.on_escape()
            return
        if self.scene.exit_button and self.exit_btn.handle_event(e, self):
            return
        if self.scene.hud == "home" and self.hud.handle_home(e):
            return
        self.scene.event(e)

    def update(self, dt):
        self.layout()
        self.mouse = self.to_logical(pygame.mouse.get_pos())
        ui.HOT["hand"] = False
        ui.HOT["text"] = False
        if self.fade is not None:
            f = self.fade
            f["t"] += dt / 0.24
            if f["phase"] == "out" and f["t"] >= 1.0:
                self.modal = None
                self.audio.close()
                self.set_scene(f["factory"]())
                f["phase"] = "in"
                f["t"] = 0.0
            elif f["phase"] == "in" and f["t"] >= 1.0:
                self.fade = None
        if self.modal:
            self.modal.update(dt)
        else:
            self.scene.update(dt)
            if self.scene.exit_button:
                self.exit_btn.update(dt, self.mouse)
            self.audio.update(dt)
        self.hud.update(dt)
        self.sfx.set_track(getattr(self.scene, "music_track", None))
        self.sfx.set_music_target(self.scene.music_level * (0.5 if self.modal else 1.0))
        self.sfx.update(dt)
        want = None
        if ui.HOT["hand"]:
            want = pygame.SYSTEM_CURSOR_HAND
        elif ui.HOT["text"]:
            want = pygame.SYSTEM_CURSOR_IBEAM
        else:
            want = pygame.SYSTEM_CURSOR_ARROW
        if want != self.cursor:
            self.cursor = want
            try:
                pygame.mouse.set_cursor(want)
            except pygame.error:
                pass

    def render(self):
        s = self.stage
        s.fill((0, 0, 0))
        sc = self.scene
        sc.draw(s)
        if sc.hud == "money":
            self.hud.draw_money(s)
            self.hud.draw_score(s)
            if sc.counter:
                self.hud.draw_counter(s, self.session.sent, C.TOTAL_ROUNDS)
        elif sc.hud == "home":
            self.hud.draw_home(s)
        if sc.exit_button:
            self.exit_btn.draw(s)
        if self.modal:
            self.modal.draw(s)
        else:
            self.audio.draw(s)

    def backdrop_for(self, art, size):
        key = (id(art), size)
        bd = self.backdrops.get(key)
        if bd is None:
            if len(self.backdrops) > 8:
                self.backdrops.clear()
            small = pygame.transform.smoothscale(art, (64, 36))
            f = max(size[0] / 64, size[1] / 36)
            big = pygame.transform.smoothscale(small, (int(64 * f) + 2, int(36 * f) + 2))
            bd = pygame.Surface(size).convert()
            bd.blit(big, ((size[0] - big.get_width()) // 2, (size[1] - big.get_height()) // 2))
            bd.fill((120, 124, 140), special_flags=pygame.BLEND_RGB_MULT)
            self.backdrops[key] = bd
        return bd

    def present(self):
        win = pygame.display.get_surface()
        ww, wh, sw, sh = self.layout()
        if sw < ww or sh < wh:
            art = None
            if self.modal:
                art = self.modal.bg
            elif self.scene:
                art = self.scene.backdrop_art()
            if art is None:
                art = self.stage
            win.blit(self.backdrop_for(art, (ww, wh)), (0, 0))
            frame = pygame.Rect(self.offset, (sw, sh))
            pygame.draw.rect(win, (8, 12, 24), frame.inflate(6, 6), 3)
            pygame.draw.rect(win, (120, 160, 220), frame.inflate(2, 2), 1)
        if sw == C.BASE_W and sh == C.BASE_H:
            win.blit(self.stage, self.offset)
        else:
            win.blit(pygame.transform.smoothscale(self.stage, (sw, sh)), self.offset)
        if self.fade is not None:
            f = self.fade
            a = f["t"] if f["phase"] == "out" else 1.0 - f["t"]
            ov = pygame.Surface((ww, wh))
            ov.set_alpha(int(255 * max(0.0, min(1.0, a))))
            win.blit(ov, (0, 0))
        pygame.display.flip()

    def step(self, dt, events):
        for e in events:
            self.dispatch(e)
        self.update(dt)
        self.render()
        self.present()

    def run(self):
        while self.running:
            dt = min(0.05, self.clock.tick(C.FPS) / 1000.0)
            self.step(dt, pygame.event.get())
        try:
            self.adapter.save()
        except Exception:
            pass
        pygame.quit()
