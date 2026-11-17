import array
import json
import math
import os
import random
import pygame
from . import config as C


class Sfx:
    """Efek suara 8-bit yang disintesis lewat kode tanpa file audio eksternal."""

    RATE = 22050
    MUSIC_VOL = 0.45

    def __init__(self):
        self.enabled = False
        self.muted = False
        self.sounds = {}
        self.music_ready = False
        self.music_started = False
        self.track = None
        self.want_track = C.MUSIC_PATH
        self.track_fade = 1.0
        self.loops = {}
        self.music_level = 1.0
        self.music_target = 1.0
        self.music_on = True
        self.sfx_on = True
        self.music_vol = 0.67
        self.sfx_vol = 1.0
        self.load_settings()
        try:
            pygame.mixer.init(frequency=self.RATE, size=-16, channels=1, buffer=512)
            self.enabled = True
        except pygame.error:
            self.enabled = False
        if self.enabled:
            self._build()
            self._load_music()

    def load_settings(self):
        """Membaca pengaturan volume dan bisu yang tersimpan dari sesi sebelumnya."""
        try:
            with open(C.SETTINGS_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
            self.music_on = bool(d.get("music_on", True))
            self.sfx_on = bool(d.get("sfx_on", True))
            self.music_vol = max(0.0, min(1.0, float(d.get("music_vol", 0.67))))
            self.sfx_vol = max(0.0, min(1.0, float(d.get("sfx_vol", 1.0))))
        except Exception:
            pass

    def save_settings(self):
        """Menyimpan pengaturan volume dan bisu agar dipakai lagi saat game dibuka berikutnya."""
        try:
            os.makedirs(C.DATA_DIR, exist_ok=True)
            with open(C.SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump({"music_on": self.music_on, "sfx_on": self.sfx_on, "music_vol": round(self.music_vol, 3), "sfx_vol": round(self.sfx_vol, 3)}, f)
        except Exception:
            pass

    def _load_music(self):
        """Memuat berkas musik latar mp3 sebagai aliran agar hemat memori dan siap diputar berulang."""
        try:
            pygame.mixer.music.load(self.want_track)
            self.track = self.want_track
            self.music_ready = True
        except Exception:
            self.music_ready = False

    def set_track(self, path):
        """Menentukan berkas musik latar yang diinginkan scene aktif agar ditukar dengan memudar."""
        self.want_track = path if isinstance(path, str) and path else C.MUSIC_PATH

    def set_loop(self, name, level):
        """Menentukan volume tujuan suara latar berulang seperti ombak dan hujan yang bergerak halus."""
        if not self.enabled:
            return
        lp = self.loops.get(name)
        if lp is None:
            snd = self.sounds.get("loop_" + name)
            if snd is None:
                return
            lp = {"snd": snd, "ch": None, "vol": 0.0, "target": 0.0}
            self.loops[name] = lp
        lp["target"] = max(0.0, min(1.0, level))

    def stop_loops(self):
        """Menurunkan semua suara latar berulang ke nol saat berpindah scene."""
        for lp in self.loops.values():
            lp["target"] = 0.0

    def _update_loops(self, dt):
        for lp in self.loops.values():
            diff = lp["target"] - lp["vol"]
            lp["vol"] += max(-1.2 * dt, min(1.2 * dt, diff))
            if lp["vol"] <= 0.001 and lp["target"] <= 0.0:
                if lp["ch"] is not None:
                    lp["ch"].stop()
                    lp["ch"] = None
                continue
            if lp["ch"] is None or not lp["ch"].get_busy():
                lp["ch"] = lp["snd"].play(loops=-1)
            if lp["ch"] is not None:
                audible = not (self.muted or not self.sfx_on)
                lp["ch"].set_volume(lp["vol"] * self.sfx_vol * (1.0 if audible else 0.0))

    def stop(self, name):
        """Menghentikan suara efek bernama yang sedang diputar."""
        snd = self.sounds.get(name)
        if snd:
            snd.stop()

    def set_music_target(self, level):
        """Menentukan tingkat volume musik yang dituju lalu dicapai halus oleh update."""
        self.music_target = max(0.0, min(1.0, level))

    def update(self, dt):
        """Memulai musik saat siap dan menggeser volumenya perlahan menuju target."""
        if not self.enabled:
            return
        if self.music_ready and not self.music_started:
            self.music_started = True
            try:
                pygame.mixer.music.play(loops=-1)
            except pygame.error:
                self.music_ready = False
        diff = self.music_target - self.music_level
        step = 1.2 * dt
        self.music_level += max(-step, min(step, diff))
        if self.music_started:
            if self.want_track != self.track:
                self.track_fade = max(0.0, self.track_fade - dt / 0.5)
                if self.track_fade <= 0.01:
                    try:
                        pygame.mixer.music.load(self.want_track)
                        pygame.mixer.music.play(loops=-1)
                    except Exception:
                        pass
                    self.track = self.want_track
            else:
                self.track_fade = min(1.0, self.track_fade + dt / 0.6)
        vol = 0.0 if (self.muted or not self.music_on) else self.MUSIC_VOL * self.music_vol * self.music_level * self.track_fade
        if self.music_started:
            pygame.mixer.music.set_volume(vol)
        self._update_loops(dt)

    def _wave(self, kind, phase):
        if kind == "square":
            return 1.0 if (phase % 1.0) < 0.5 else -1.0
        if kind == "saw":
            return 2.0 * (phase % 1.0) - 1.0
        if kind == "tri":
            return 4.0 * abs((phase % 1.0) - 0.5) - 1.0
        return math.sin(phase * 2 * math.pi)

    def _render(self, notes, vol=0.35, kind="square", decay=3.0, slide=0.0, noise=0.0):
        data = array.array("h")
        rng = random.Random(7)
        for freq, dur in notes:
            n = int(self.RATE * dur)
            phase = 0.0
            for i in range(n):
                t = i / max(1, n)
                f = freq * (1 + slide * t) if freq > 0 else 0
                phase += f / self.RATE
                v = self._wave(kind, phase) if freq > 0 else 0.0
                if noise:
                    v = v * (1 - noise) + rng.uniform(-1, 1) * noise
                env = math.exp(-decay * t) * min(1.0, i / 40.0)
                data.append(int(max(-1, min(1, v * env * vol)) * 32000))
        return pygame.mixer.Sound(buffer=data.tobytes())

    def _noise_loop(self, seconds, cutoff, cycles, gain, high=False):
        """Membuat derau berulang tanpa sambungan terdengar dengan filter dan denyut amplitudo untuk ombak atau hujan."""
        n = int(self.RATE * seconds)
        rng = random.Random(11)
        raw = [rng.uniform(-1, 1) for _ in range(n)]
        y = 0.0
        out = []
        for i in range(n):
            y += cutoff * (raw[i] - y)
            v = raw[i] - y if high else y
            mod = 0.65 + 0.35 * math.sin(2 * math.pi * cycles * i / n)
            out.append(v * mod * gain)
        fade = int(self.RATE * 0.15)
        for i in range(fade):
            k = i / fade
            out[i] = out[i] * k + out[n - fade + i] * (1 - k)
        data = array.array("h", [int(max(-1, min(1, v)) * 32000) for v in out[: n - fade]])
        return pygame.mixer.Sound(buffer=data.tobytes())

    def _file_sound(self, path):
        """Memuat berkas suara pendek dari disk dan mengembalikan None bila tidak ditemukan."""
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            return None

    def _build(self):
        r = self._render
        self.sounds = {
            "hover": r([(1500, 0.025)], 0.12, "square", 4),
            "click": r([(740, 0.03), (990, 0.05)], 0.28, "square", 3),
            "type": r([(260, 0.018)], 0.10, "square", 5, noise=0.6),
            "confirm": r([(523, 0.07), (659, 0.07), (784, 0.12)], 0.28, "square", 2),
            "error": r([(220, 0.12), (165, 0.2)], 0.30, "saw", 2),
            "coin": r([(988, 0.07), (1319, 0.3)], 0.28, "square", 3.5),
            "win": r([(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.4)], 0.3, "square", 2),
            "lose": r([(392, 0.2), (330, 0.2), (262, 0.2), (196, 0.6)], 0.3, "tri", 1.5),
            "clang": r([(140, 0.5)], 0.45, "saw", 4, noise=0.35),
            "aha": r([(440, 0.25)], 0.3, "square", 1.2, slide=1.2),
            "scan": r([(300, 0.4)], 0.16, "tri", 1.0, slide=1.5),
            "alarm": r([(880, 0.14), (660, 0.14), (880, 0.14), (660, 0.14)], 0.22, "square", 1.2),
            "pop": r([(400, 0.08)], 0.25, "sine", 3, slide=1.5),
            "whoosh": r([(200, 0.3)], 0.2, "saw", 3, slide=-0.6, noise=0.8),
            "plop": r([(260, 0.09)], 0.3, "sine", 3.5, slide=-0.5),
            "ratchet": r([(2200, 0.012), (0, 0.012), (1700, 0.012)], 0.2, "square", 3, noise=0.3),
            "creak": r([(110, 0.28)], 0.16, "saw", 2, slide=0.35, noise=0.25),
            "ding": r([(1318, 0.05), (1760, 0.22)], 0.26, "sine", 4),
            "cast": r([(300, 0.28)], 0.24, "saw", 2.5, slide=2.4, noise=0.7),
            "splash": r([(520, 0.22)], 0.3, "saw", 4, slide=-0.7, noise=0.9),
            "thunder": r([(70, 0.9)], 0.5, "saw", 2.2, slide=-0.4, noise=0.85),
            "bite": r([(330, 0.06), (250, 0.08), (330, 0.06)], 0.25, "tri", 2),
            "fanfare": r([(523, 0.1), (659, 0.1), (784, 0.1), (1047, 0.1), (784, 0.1), (1047, 0.1), (1319, 0.5)], 0.3, "square", 1.6),
        }
        self.sounds["loop_rain"] = self._noise_loop(3.0, 0.22, 3, 1.1, True)
        mania = self._file_sound(C.MANIA_PATH)
        if mania is not None:
            self.sounds["loop_mania"] = mania

    def play(self, name, vol=1.0):
        """Memainkan efek suara berdasarkan nama dengan pengali volume opsional."""
        if not self.enabled or self.muted or not self.sfx_on or self.sfx_vol <= 0:
            return
        snd = self.sounds.get(name)
        if snd:
            ch = snd.play()
            if ch is not None:
                ch.set_volume(vol * self.sfx_vol)

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted
