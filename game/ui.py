import math
import re
import time
import pygame
from . import config as C
from .canvas import mix, shade

HOT = {"hand": False, "text": False}
_FONTS = {}
_FAMILIES = "segoeui,tahoma,verdana,dejavusans,liberationsans,arial,helvetica,freesans"
_TEXT_CACHE = {}
_CLIP = {"text": ""}


def font(size, bold=False):
    """Mengambil font sistem bergaya Windows dengan cache."""
    key = (size, bold)
    if key not in _FONTS:
        try:
            _FONTS[key] = pygame.font.SysFont(_FAMILIES, size, bold=bold)
        except Exception:
            _FONTS[key] = pygame.font.Font(None, int(size * 1.2))
    return _FONTS[key]


def mono(size, bold=False):
    """Mengambil font monospasi untuk tampilan terminal pemindai AI."""
    key = ("mono", size, bold)
    if key not in _FONTS:
        try:
            _FONTS[key] = pygame.font.SysFont("consolas,couriernew,dejavusansmono,liberationmono,monospace", size, bold=bold)
        except Exception:
            _FONTS[key] = pygame.font.Font(None, int(size * 1.2))
    return _FONTS[key]


def text_surf(f, text, color):
    """Merender teks dengan cache sederhana agar tidak boros."""
    key = (id(f), text, color)
    s = _TEXT_CACHE.get(key)
    if s is None:
        if len(_TEXT_CACHE) > 900:
            _TEXT_CACHE.clear()
        s = f.render(text, True, color)
        _TEXT_CACHE[key] = s
    return s


def draw_text(surf, text, f, color, pos, anchor="topleft", shadow=None, glow=None):
    """Menggambar teks dengan anchor, bayangan, atau glow gelap ala judul jendela Windows 7."""
    s = text_surf(f, text, color)
    r = s.get_rect(**{anchor: pos})
    if glow:
        g = text_surf(f, text, glow)
        g = g.copy()
        g.set_alpha(70)
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if dx or dy:
                    surf.blit(g, (r.x + dx, r.y + dy))
    if shadow:
        sh = text_surf(f, text, shadow)
        surf.blit(sh, (r.x + 1, r.y + 1))
    surf.blit(s, r)
    return r


def wrap_lines(f, text, width):
    """Memecah teks menjadi baris yang muat pada lebar tertentu."""
    out = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            trial = w if not cur else cur + " " + w
            if f.size(trial)[0] <= width or not cur:
                cur = trial
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


def clip_get():
    """Membaca teks dari clipboard sistem dengan cadangan internal."""
    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        raw = pygame.scrap.get(pygame.SCRAP_TEXT)
        if raw:
            return raw.decode("utf-8", "ignore").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    except Exception:
        pass
    return _CLIP["text"]


def clip_put(text):
    """Menyalin teks ke clipboard sistem dengan cadangan internal."""
    _CLIP["text"] = text
    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))
    except Exception:
        pass


def nav_key(e):
    """Mengenali tombol Home atau End dari kode tombol atau kode fisik termasuk keypad tanpa Num Lock lalu mengembalikan home end atau None."""
    k = e.key
    sc = getattr(e, "scancode", -1)
    if k == pygame.K_HOME or sc == pygame.KSCAN_HOME:
        return "home"
    if k == pygame.K_END or sc == pygame.KSCAN_END:
        return "end"
    if not (getattr(e, "mod", 0) & pygame.KMOD_NUM):
        if k == pygame.K_KP7:
            return "home"
        if k == pygame.K_KP1:
            return "end"
    return None


def word_span(text, i):
    """Mencari batas kata di sekitar indeks i untuk seleksi klik ganda dengan kelompok huruf dan angka atau kelompok tanda yang sama."""
    n = len(text)
    if n == 0:
        return 0, 0
    i = max(0, min(n - 1, i))

    def kind(ch):
        if ch.isalnum() or ch in "_'":
            return 1
        if ch in " \t":
            return 2
        return 3

    k = kind(text[i])
    if text[i] == "\n":
        return i, i
    a = i
    while a > 0 and text[a - 1] != "\n" and kind(text[a - 1]) == k:
        a -= 1
    b = i + 1
    while b < n and text[b] != "\n" and kind(text[b]) == k:
        b += 1
    return a, b


_MASKS = {}


def rounded_mask(w, h, r):
    """Membuat mask persegi sudut membulat untuk memotong gradien."""
    key = (w, h, r)
    m = _MASKS.get(key)
    if m is None:
        m = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(m, (255, 255, 255, 255), (0, 0, w, h), border_radius=r)
        _MASKS[key] = m
    return m


_GLASS = {}


def glass(w, h, r=10, tint=(110, 165, 225), alpha=150, gloss=True, border=True):
    """Panel kaca translusen bergaya Windows 7 Aero dengan kilau diagonal."""
    key = (w, h, r, tint, alpha, gloss, border)
    s = _GLASS.get(key)
    if s is not None:
        return s
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    top = shade(tint, 0.38)
    bot = shade(tint, -0.22)
    for y in range(h):
        t = y / max(1, h - 1)
        c = mix(top, bot, t)
        a = int(alpha * (0.85 + 0.3 * t))
        pygame.draw.line(s, (*c, min(255, a)), (0, y), (w, y))
    if gloss:
        hl = pygame.Surface((w, h), pygame.SRCALPHA)
        pts = [(0, 0), (w, 0), (w, int(h * 0.18)), (int(w * 0.35), int(h * 0.52)), (0, int(h * 0.58))]
        pygame.draw.polygon(hl, (255, 255, 255, 46), pts)
        pygame.draw.polygon(hl, (255, 255, 255, 22), [(int(w * 0.5), 0), (w, 0), (w, int(h * 0.3)), (int(w * 0.7), int(h * 0.3))])
        s.blit(hl, (0, 0))
    s.blit(rounded_mask(w, h, r), (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    if border:
        pygame.draw.rect(s, (8, 20, 40, 150), (0, 0, w, h), 1, border_radius=r)
        pygame.draw.rect(s, (255, 255, 255, 170), (1, 1, w - 2, h - 2), 1, border_radius=max(1, r - 1))
    _GLASS[key] = s
    return s


STYLES = {
    "default": {
        "normal": ((246, 246, 246), (236, 236, 236), (222, 222, 222), (208, 208, 208), (112, 112, 112)),
        "hover": ((236, 247, 253), (218, 241, 253), (190, 230, 253), (167, 217, 245), (60, 127, 177)),
        "pressed": ((229, 244, 252), (196, 229, 246), (152, 209, 239), (104, 179, 219), (44, 98, 139)),
        "text": (24, 24, 24),
    },
    "primary": {
        "normal": ((150, 200, 245), (98, 165, 232), (44, 128, 214), (60, 150, 232), (24, 84, 150)),
        "hover": ((176, 218, 255), (122, 188, 248), (62, 148, 232), (84, 172, 250), (24, 84, 150)),
        "pressed": ((100, 160, 220), (66, 128, 200), (30, 96, 176), (40, 116, 200), (16, 60, 120)),
        "text": (255, 255, 255),
    },
    "danger": {
        "normal": ((246, 160, 142), (232, 98, 78), (200, 50, 34), (222, 76, 54), (120, 26, 16)),
        "hover": ((255, 186, 170), (244, 122, 100), (214, 66, 46), (236, 96, 72), (120, 26, 16)),
        "pressed": ((200, 110, 96), (186, 70, 54), (150, 34, 22), (176, 52, 36), (90, 18, 10)),
        "text": (255, 255, 255),
    },
    "success": {
        "normal": ((170, 236, 160), (110, 206, 100), (50, 160, 60), (72, 184, 78), (24, 96, 32)),
        "hover": ((196, 250, 188), (134, 224, 124), (64, 178, 74), (92, 204, 96), (24, 96, 32)),
        "pressed": ((120, 190, 112), (80, 160, 76), (36, 120, 44), (52, 140, 56), (16, 70, 22)),
        "text": (255, 255, 255),
    },
    "dark": {
        "normal": ((70, 96, 128), (44, 66, 96), (22, 40, 66), (30, 54, 86), (10, 20, 36)),
        "hover": ((96, 130, 170), (62, 94, 132), (32, 58, 92), (44, 76, 116), (120, 200, 255)),
        "pressed": ((40, 60, 88), (28, 44, 66), (14, 26, 44), (20, 36, 58), (120, 200, 255)),
        "text": (225, 240, 255),
    },
    "disabled": {
        "normal": ((240, 240, 240), (232, 232, 232), (224, 224, 224), (216, 216, 216), (170, 170, 170)),
        "hover": ((240, 240, 240), (232, 232, 232), (224, 224, 224), (216, 216, 216), (170, 170, 170)),
        "pressed": ((240, 240, 240), (232, 232, 232), (224, 224, 224), (216, 216, 216), (170, 170, 170)),
        "text": (150, 150, 150),
    },
}

_BTN = {}


def button_surface(w, h, style, state, r=5):
    """Membuat gambar tombol glossy dua nada seperti tombol Windows 7."""
    key = (w, h, style, state, r)
    s = _BTN.get(key)
    if s is not None:
        return s
    st = STYLES[style][state]
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    half = h // 2
    for y in range(h):
        if y < half:
            c = mix(st[0], st[1], y / max(1, half - 1))
        else:
            c = mix(st[2], st[3], (y - half) / max(1, h - half - 1))
        pygame.draw.line(s, c, (0, y), (w, y))
    s.blit(rounded_mask(w, h, r), (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    pygame.draw.rect(s, st[4], (0, 0, w, h), 1, border_radius=r)
    pygame.draw.rect(s, (255, 255, 255, 150), (1, 1, w - 2, h - 2), 1, border_radius=max(1, r - 1))
    _BTN[key] = s
    return s


class Button:
    """Tombol bergaya Windows 7 dengan ikon opsional, hover, dan efek tekan."""

    def __init__(self, rect, label, callback, style="default", icon=None, size=17, bold=True, sound="click"):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.callback = callback
        self.style = style
        self.icon = icon
        self.size = size
        self.bold = bold
        self.enabled = True
        self.hover = False
        self.press = False
        self.sound = sound
        self.visible = True
        self.pulse = False
        self.t = 0.0

    def handle_event(self, e, app):
        if not self.visible or not self.enabled:
            return False
        if e.type == pygame.MOUSEMOTION:
            was = self.hover
            self.hover = self.rect.collidepoint(e.pos)
            if self.hover and not was:
                app.sfx.play("hover")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect.collidepoint(e.pos):
                self.press = True
                return True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            was = self.press
            self.press = False
            if was and self.rect.collidepoint(e.pos):
                app.sfx.play(self.sound)
                self.callback()
                return True
        return False

    def update(self, dt, mouse):
        self.t += dt
        self.hover = self.visible and self.enabled and self.rect.collidepoint(mouse)
        if self.hover:
            HOT["hand"] = True

    def draw(self, surf):
        if not self.visible:
            return
        style = self.style if self.enabled else "disabled"
        state = "pressed" if (self.press and self.hover) else ("hover" if self.hover else "normal")
        img = button_surface(self.rect.w, self.rect.h, style, state)
        surf.blit(img, self.rect)
        if self.pulse and self.enabled and not self.hover:
            a = int(60 + 60 * math.sin(self.t * 4))
            g = pygame.Surface((self.rect.w + 12, self.rect.h + 12), pygame.SRCALPHA)
            pygame.draw.rect(g, (255, 255, 255, max(0, a)), g.get_rect(), 3, border_radius=9)
            surf.blit(g, (self.rect.x - 6, self.rect.y - 6))
        f = font(self.size, self.bold)
        col = STYLES[style]["text"]
        label = text_surf(f, self.label, col)
        iw = 0
        if self.icon:
            iw = self.size + 8
        total = iw + label.get_width()
        x = self.rect.centerx - total // 2
        cy = self.rect.centery
        if self.icon:
            self.icon(surf, (x + self.size // 2, cy), self.size + 2, col)
            x += iw
        if col == (255, 255, 255) or style == "dark":
            sh = text_surf(f, self.label, (0, 0, 0))
            sh = sh.copy()
            sh.set_alpha(110)
            surf.blit(sh, (x, cy - label.get_height() // 2 + 1))
        surf.blit(label, (x, cy - label.get_height() // 2))


def draw_window(surf, rect, title, active=True, controls=True, tint=(86, 146, 214), body=(247, 249, 252), icon=None):
    """Menggambar jendela Windows 7 dengan bingkai kaca dan mengembalikan area klien."""
    x, y, w, h = rect
    sh = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
    for i in range(10):
        pygame.draw.rect(sh, (0, 0, 0, 5 + i * 2), (12 - i, 14 - i, w + i * 2, h + i * 2), border_radius=10 + i)
    surf.blit(sh, (x - 12, y - 10))
    fr = glass(w, h, 9, tint if active else (150, 165, 185), 255 if active else 235, True, True)
    surf.blit(fr, (x, y))
    tf = font(15, False)
    tx = x + 12
    if icon:
        icon(surf, (x + 20, y + 16), 16, (255, 255, 255))
        tx = x + 34
    draw_text(surf, title, tf, (255, 255, 255), (tx, y + 7), glow=(0, 20, 60))
    if controls:
        bx = x + w - 8 - 98
        by = y + 1
        pill = pygame.Surface((98, 20), pygame.SRCALPHA)
        pygame.draw.rect(pill, (200, 220, 245, 200), (0, 0, 52, 20), border_bottom_left_radius=5)
        pygame.draw.rect(pill, (90, 120, 160, 220), (0, 0, 52, 20), 1, border_bottom_left_radius=5)
        pygame.draw.line(pill, (90, 120, 160, 220), (26, 2), (26, 18))
        pygame.draw.rect(pill, (226, 90, 70, 255), (52, 0, 46, 20), border_bottom_right_radius=5)
        pygame.draw.rect(pill, (140, 30, 20, 255), (52, 0, 46, 20), 1, border_bottom_right_radius=5)
        pygame.draw.rect(pill, (255, 150, 130, 160), (53, 1, 44, 8), border_top_left_radius=0)
        pygame.draw.line(pill, (30, 40, 60), (9, 13), (17, 13), 2)
        pygame.draw.rect(pill, (30, 40, 60), (34, 5, 9, 9), 1)
        pygame.draw.line(pill, (255, 255, 255), (69, 5), (79, 14), 2)
        pygame.draw.line(pill, (255, 255, 255), (79, 5), (69, 14), 2)
        surf.blit(pill, (bx, by))
    client = pygame.Rect(x + 8, y + 32, w - 16, h - 40)
    pygame.draw.rect(surf, body, client)
    pygame.draw.rect(surf, (36, 60, 98), client, 1)
    return client


class History:
    """Riwayat undo dan redo untuk kolom teks yang menyimpan teks beserta posisi kursor dan seleksi dengan penggabungan ketikan beruntun."""

    def __init__(self):
        self.undo = []
        self.redo = []
        self.kind = None
        self.stamp = 0.0

    def clear(self):
        """Mengosongkan seluruh riwayat."""
        self.undo = []
        self.redo = []
        self.kind = None

    def push(self, state, kind, merge):
        """Menyimpan keadaan sebelum perubahan kecuali ketikan sejenis yang berdekatan waktunya digabung ke satu langkah."""
        now = time.monotonic()
        if merge and self.kind == kind and now - self.stamp < 1.0 and self.undo:
            self.stamp = now
            return
        self.undo.append(state)
        del self.undo[:-300]
        self.redo = []
        self.kind = kind
        self.stamp = now

    def step(self, current, forward):
        """Mengambil keadaan undo atau redo sambil menyimpan keadaan sekarang ke tumpukan lawannya lalu mengembalikan keadaan tujuan atau None."""
        src, dst = (self.redo, self.undo) if forward else (self.undo, self.redo)
        if not src:
            return None
        dst.append(current)
        self.kind = None
        return src.pop()


class TextArea:
    """Editor teks multi-baris dengan wrap, seleksi, clipboard, scroll mouse, dan scrollbar."""

    SB_W = 14

    def __init__(self, rect, f, color=(28, 32, 44), placeholder="", max_chars=2400, pad=12, line_gap=5):
        self.rect = pygame.Rect(rect)
        self.font = f
        self.color = color
        self.placeholder = placeholder
        self.max_chars = max_chars
        self.pad = pad
        self.line_h = f.get_linesize() + line_gap
        self.text = ""
        self.cursor = 0
        self.anchor = 0
        self.scroll = 0.0
        self.target = 0.0
        self.focus = True
        self.dragging = False
        self.sb_drag = None
        self.blink = 0.0
        self.pref_x = None
        self._lines = []
        self._key = None
        self.on_type = None
        self.enabled = True
        self.bg = None
        self.clicks = (0.0, 0, 0)
        self.hist = History()

    def set_rect(self, rect):
        self.rect = pygame.Rect(rect)
        self._key = None

    def text_width(self):
        return self.rect.w - self.pad * 2 - self.SB_W

    def view_h(self):
        return self.rect.h - self.pad * 2

    def lines(self):
        key = (self.text, self.text_width())
        if key != self._key:
            self._key = key
            self._lines = self._wrap()
        return self._lines

    def _split_long(self, out, cur, cur_start, width):
        """Memotong kata yang lebih lebar dari area teks menjadi beberapa baris."""
        while self.font.size(cur.rstrip())[0] > width and len(cur) > 1:
            cut = len(cur) - 1
            while cut > 1 and self.font.size(cur[:cut])[0] > width:
                cut -= 1
            out.append((cur_start, cur_start + cut, False))
            cur_start += cut
            cur = cur[cut:]
        return cur, cur_start

    def _wrap(self):
        width = self.text_width()
        out = []
        idx = 0
        for para in self.text.split("\n"):
            cur_start = idx
            cur = ""
            for tok in re.findall(r"\S+\s*|\s+", para):
                trial = cur + tok
                if self.font.size(trial.rstrip())[0] <= width or not cur:
                    cur = trial
                else:
                    out.append((cur_start, cur_start + len(cur), False))
                    cur_start += len(cur)
                    cur = tok
                cur, cur_start = self._split_long(out, cur, cur_start, width)
            out.append((cur_start, cur_start + len(cur), True))
            idx += len(para) + 1
        return out

    def total_h(self):
        return len(self.lines()) * self.line_h

    def max_scroll(self):
        return max(0, self.total_h() - self.view_h())

    def locate(self, idx):
        lines = self.lines()
        for li, (s, e, hard) in enumerate(lines):
            if s <= idx < e or (idx == e and hard):
                x = self.font.size(self.text[s:idx])[0]
                return li, x
        li = len(lines) - 1
        s, e, _ = lines[li]
        return li, self.font.size(self.text[s:e])[0]

    def index_at(self, li, x):
        lines = self.lines()
        li = max(0, min(len(lines) - 1, li))
        s, e, hard = lines[li]
        seg = self.text[s:e]
        best = s
        prev = 0
        for i in range(1, len(seg) + 1):
            w = self.font.size(seg[:i])[0]
            if x < (prev + w) / 2:
                break
            best = s + i
            prev = w
        if not hard and best >= e:
            best = max(s, e - 1)
        return best

    def sel_range(self):
        return min(self.cursor, self.anchor), max(self.cursor, self.anchor)

    def has_sel(self):
        return self.cursor != self.anchor

    def selected_text(self):
        a, b = self.sel_range()
        return self.text[a:b]

    def delete_sel(self):
        a, b = self.sel_range()
        if a != b:
            self.text = self.text[:a] + self.text[b:]
            self.cursor = self.anchor = a

    def snap(self, kind, merge=False):
        """Merekam keadaan teks dan kursor sebelum perubahan agar bisa dibatalkan dengan Ctrl+Z."""
        self.hist.push((self.text, self.cursor, self.anchor), kind, merge)

    def restore(self, forward):
        """Mengembalikan keadaan undo atau redo lengkap dengan posisi kursor dan seleksi sebelumnya."""
        st = self.hist.step((self.text, self.cursor, self.anchor), forward)
        if st is None:
            return
        self.text, self.cursor, self.anchor = st
        self.pref_x = None
        self.blink = 0.0
        self._ensure_visible()

    def insert(self, s):
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        s = "".join(ch for ch in s if ch == "\n" or ch >= " ")
        if not s:
            return
        if len(s) == 1 and not self.has_sel():
            self.snap("space" if s in " \n" else "type", True)
        else:
            self.snap("paste")
        self.delete_sel()
        room = self.max_chars - len(self.text)
        if room <= 0:
            return
        s = s[:room]
        self.text = self.text[: self.cursor] + s + self.text[self.cursor :]
        self.cursor += len(s)
        self.anchor = self.cursor
        self.pref_x = None
        self.blink = 0.0
        self._ensure_visible()
        if self.on_type:
            self.on_type(s)

    def set_text(self, t):
        self.text = t[: self.max_chars]
        self.cursor = self.anchor = len(self.text)
        self.scroll = self.target = 0.0
        self.hist.clear()
        self._ensure_visible()

    def _move(self, new, shift):
        self.cursor = max(0, min(len(self.text), new))
        if not shift:
            self.anchor = self.cursor
        self.blink = 0.0
        self._ensure_visible()

    def _ensure_visible(self):
        li, _ = self.locate(self.cursor)
        top = li * self.line_h
        bot = top + self.line_h
        if top < self.target:
            self.target = top
        elif bot > self.target + self.view_h():
            self.target = bot - self.view_h()
        self.target = max(0, min(self.max_scroll(), self.target))

    def _word_left(self, i):
        while i > 0 and self.text[i - 1] in " \n":
            i -= 1
        while i > 0 and self.text[i - 1] not in " \n":
            i -= 1
        return i

    def _word_right(self, i):
        n = len(self.text)
        while i < n and self.text[i] in " \n":
            i += 1
        while i < n and self.text[i] not in " \n":
            i += 1
        return i

    def _sb_track(self):
        return pygame.Rect(self.rect.right - self.SB_W - 2, self.rect.y + 2, self.SB_W, self.rect.h - 4)

    def _sb_thumb(self):
        tr = self._sb_track()
        total = max(1, self.total_h())
        ratio = min(1.0, self.view_h() / total)
        th = max(34, int(tr.h * ratio))
        ms = self.max_scroll()
        ty = tr.y + (int((tr.h - th) * (self.scroll / ms)) if ms > 0 else 0)
        return pygame.Rect(tr.x, ty, tr.w, th)

    def _pos_to_index(self, pos):
        lx = pos[0] - self.rect.x - self.pad
        ly = pos[1] - self.rect.y - self.pad + self.scroll
        li = int(ly // self.line_h)
        return self.index_at(li, lx)

    def handle_event(self, e, mouse):
        if not self.enabled:
            return False
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect.collidepoint(e.pos):
                self.focus = True
                if self.max_scroll() > 0 and self._sb_track().collidepoint(e.pos):
                    th = self._sb_thumb()
                    if th.collidepoint(e.pos):
                        self.sb_drag = e.pos[1] - th.y
                    else:
                        self.target = max(0, min(self.max_scroll(), self.target + (self.view_h() if e.pos[1] > th.y else -self.view_h())))
                    return True
                shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                idx = self._pos_to_index(e.pos)
                now = time.monotonic()
                n = self.clicks[2] + 1 if (now - self.clicks[0] < 0.45 and abs(idx - self.clicks[1]) <= 1) else 1
                self.clicks = (now, idx, n)
                if n == 2:
                    a, b = word_span(self.text, idx)
                    self.anchor, self.cursor = a, b
                    self.dragging = False
                    self.blink = 0.0
                    return True
                if n >= 3:
                    a = self.text.rfind("\n", 0, idx) + 1
                    b = self.text.find("\n", idx)
                    self.anchor, self.cursor = a, (len(self.text) if b < 0 else b)
                    self.dragging = False
                    self.blink = 0.0
                    return True
                self._move(idx, shift)
                self.dragging = True
                return True
            self.focus = False
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
            self.sb_drag = None
        elif e.type == pygame.MOUSEMOTION:
            if self.sb_drag is not None:
                tr = self._sb_track()
                th = self._sb_thumb()
                span = max(1, tr.h - th.h)
                t = (e.pos[1] - self.sb_drag - tr.y) / span
                self.target = self.scroll = max(0, min(self.max_scroll(), t * self.max_scroll()))
                return True
            if self.dragging:
                self.cursor = self._pos_to_index(e.pos)
                self.blink = 0.0
                self._ensure_visible()
                return True
        elif e.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(mouse):
                self.target = max(0, min(self.max_scroll(), self.target - e.y * self.line_h * 2))
                return True
        elif self.focus and e.type == pygame.TEXTINPUT:
            self.insert(e.text)
            return True
        elif self.focus and e.type == pygame.KEYDOWN:
            return self._key_down(e)
        return False

    def _key_down(self, e):
        mods = e.mod
        ctrl = bool(mods & (pygame.KMOD_CTRL | pygame.KMOD_META))
        shift = bool(mods & pygame.KMOD_SHIFT)
        k = e.key
        if ctrl:
            if k == pygame.K_a:
                self.anchor = 0
                self.cursor = len(self.text)
                return True
            if k == pygame.K_c:
                if self.has_sel():
                    clip_put(self.selected_text())
                return True
            if k == pygame.K_x:
                if self.has_sel():
                    clip_put(self.selected_text())
                    self.snap("cut")
                    self.delete_sel()
                    self._ensure_visible()
                return True
            if k == pygame.K_v:
                self.insert(clip_get())
                return True
            if k == pygame.K_z and not shift:
                self.restore(False)
                return True
            if k == pygame.K_y or (k == pygame.K_z and shift):
                self.restore(True)
                return True
            if k == pygame.K_LEFT:
                self._move(self._word_left(self.cursor), shift)
                return True
            if k == pygame.K_RIGHT:
                self._move(self._word_right(self.cursor), shift)
                return True
            if k == pygame.K_BACKSPACE:
                self.snap("wordbs")
                if not self.has_sel():
                    self.anchor = self._word_left(self.cursor)
                self.delete_sel()
                self._ensure_visible()
                return True
            if nav_key(e) == "home":
                self._move(0, shift)
                self.pref_x = None
                return True
            if nav_key(e) == "end":
                self._move(len(self.text), shift)
                self.pref_x = None
                return True
            return False
        if k == pygame.K_BACKSPACE:
            if self.has_sel():
                self.snap("delsel")
                self.delete_sel()
            elif self.cursor > 0:
                self.snap("bs", True)
                self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
                self.cursor -= 1
                self.anchor = self.cursor
            self.blink = 0.0
            self._ensure_visible()
            return True
        if k == pygame.K_DELETE:
            if self.has_sel():
                self.snap("delsel")
                self.delete_sel()
            elif self.cursor < len(self.text):
                self.snap("del", True)
                self.text = self.text[: self.cursor] + self.text[self.cursor + 1 :]
            self._ensure_visible()
            return True
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.insert("\n")
            return True
        if k == pygame.K_TAB:
            self.insert("    ")
            return True
        if k == pygame.K_LEFT:
            if self.has_sel() and not shift:
                self._move(self.sel_range()[0], False)
            else:
                self._move(self.cursor - 1, shift)
            self.pref_x = None
            return True
        if k == pygame.K_RIGHT:
            if self.has_sel() and not shift:
                self._move(self.sel_range()[1], False)
            else:
                self._move(self.cursor + 1, shift)
            self.pref_x = None
            return True
        if k in (pygame.K_UP, pygame.K_DOWN, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
            li, x = self.locate(self.cursor)
            if self.pref_x is None:
                self.pref_x = x
            step = {pygame.K_UP: -1, pygame.K_DOWN: 1, pygame.K_PAGEUP: -max(1, self.view_h() // self.line_h - 1), pygame.K_PAGEDOWN: max(1, self.view_h() // self.line_h - 1)}[k]
            nl = max(0, min(len(self.lines()) - 1, li + step))
            self._move(self.index_at(nl, self.pref_x), shift)
            return True
        if nav_key(e) == "home":
            li, _ = self.locate(self.cursor)
            self._move(self.lines()[li][0], shift)
            self.pref_x = None
            return True
        if nav_key(e) == "end":
            li, _ = self.locate(self.cursor)
            s, e, hard = self.lines()[li]
            self._move(e if hard else max(s, e - 1), shift)
            self.pref_x = None
            return True
        return False

    def update(self, dt, mouse=None):
        self.blink += dt
        self.scroll += (self.target - self.scroll) * min(1.0, dt * 16)
        if abs(self.target - self.scroll) < 0.4:
            self.scroll = self.target
        self.scroll = max(0, min(self.max_scroll(), self.scroll))
        if mouse is not None and self.enabled and self.rect.collidepoint(mouse):
            HOT["text"] = True

    def draw(self, surf):
        if self.bg:
            pygame.draw.rect(surf, self.bg, self.rect)
        old = surf.get_clip()
        inner = pygame.Rect(self.rect.x, self.rect.y + 2, self.rect.w - self.SB_W - 2, self.rect.h - 4)
        surf.set_clip(inner.clip(old) if old else inner)
        lines = self.lines()
        oy = self.rect.y + self.pad - self.scroll
        ox = self.rect.x + self.pad
        a, b = self.sel_range()
        first = max(0, int(self.scroll // self.line_h) - 1)
        last = min(len(lines), int((self.scroll + self.view_h()) // self.line_h) + 2)
        if not self.text and self.placeholder:
            y = oy
            for ln in wrap_lines(self.font, self.placeholder, self.text_width()):
                surf.blit(text_surf(self.font, ln, (150, 156, 170)), (ox, y))
                y += self.line_h
        for li in range(first, last):
            s, e, hard = lines[li]
            y = oy + li * self.line_h
            if a != b and not (b <= s or a >= e + (1 if hard else 0)):
                sa = max(a, s)
                sb = min(b, e)
                x1 = ox + self.font.size(self.text[s:sa])[0]
                x2 = ox + self.font.size(self.text[s:sb])[0]
                if b > e and hard:
                    x2 += 6
                hl = pygame.Surface((max(3, x2 - x1), self.line_h - 2), pygame.SRCALPHA)
                hl.fill((51, 153, 255, 110))
                surf.blit(hl, (x1, y))
            if e > s:
                surf.blit(text_surf(self.font, self.text[s:e].rstrip("\n"), self.color), (ox, y))
        if self.focus and self.enabled and int(self.blink * 2) % 2 == 0:
            li, x = self.locate(self.cursor)
            y = oy + li * self.line_h
            pygame.draw.rect(surf, self.color, (ox + x, y, 2, self.line_h - 3))
        surf.set_clip(old)
        if self.max_scroll() > 0:
            tr = self._sb_track()
            pygame.draw.rect(surf, (232, 236, 242), tr, border_radius=4)
            pygame.draw.rect(surf, (178, 186, 200), tr, 1, border_radius=4)
            th = self._sb_thumb()
            img = button_surface(th.w, th.h, "default", "hover" if (self.sb_drag is not None) else "normal", 4)
            surf.blit(img, th)


class LineInput:
    """Kolom isian satu baris dengan kursor, seleksi, clipboard, batas karakter, dan tombol Enter."""

    def __init__(self, rect, f, placeholder="", max_chars=14, color=(28, 32, 44), on_submit=None, on_change=None):
        self.rect = pygame.Rect(rect)
        self.font = f
        self.placeholder = placeholder
        self.max_chars = max_chars
        self.color = color
        self.on_submit = on_submit
        self.on_change = on_change
        self.text = ""
        self.cursor = 0
        self.anchor = 0
        self.focus = False
        self.blink = 0.0
        self.dragging = False
        self.shake = 0.0
        self.clicks = (0.0, 0, 0)
        self.hist = History()

    def sel_range(self):
        return (min(self.cursor, self.anchor), max(self.cursor, self.anchor))

    def has_sel(self):
        return self.cursor != self.anchor

    def set_text(self, t):
        self.text = t[: self.max_chars]
        self.cursor = self.anchor = len(self.text)
        self.hist.clear()
        if self.on_change:
            self.on_change(self.text)

    def snap(self, kind, merge=False):
        """Merekam keadaan teks dan kursor sebelum perubahan agar bisa dibatalkan dengan Ctrl+Z."""
        self.hist.push((self.text, self.cursor, self.anchor), kind, merge)

    def restore(self, forward):
        """Mengembalikan keadaan undo atau redo lengkap dengan posisi kursor dan seleksi sebelumnya."""
        st = self.hist.step((self.text, self.cursor, self.anchor), forward)
        if st is None:
            return
        self.text, self.cursor, self.anchor = st
        self.blink = 0.0
        if self.on_change:
            self.on_change(self.text)

    def insert(self, s):
        s = s.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        a, b = self.sel_range()
        room = self.max_chars - (len(self.text) - (b - a))
        s = s[: max(0, room)]
        if not s and not (b - a):
            self.shake = 0.3
            return
        if len(s) == 1 and a == b:
            self.snap("space" if s == " " else "type", True)
        else:
            self.snap("paste")
        self.text = self.text[:a] + s + self.text[b:]
        self.cursor = self.anchor = a + len(s)
        self.blink = 0.0
        if self.on_change:
            self.on_change(self.text)

    def delete_sel(self):
        a, b = self.sel_range()
        self.text = self.text[:a] + self.text[b:]
        self.cursor = self.anchor = a
        if self.on_change:
            self.on_change(self.text)

    def index_at(self, x):
        lx = x - (self.rect.x + 12)
        best = 0
        for i in range(len(self.text) + 1):
            if self.font.size(self.text[:i])[0] <= lx + 2:
                best = i
        return best

    def move(self, new, shift):
        self.cursor = max(0, min(len(self.text), new))
        if not shift:
            self.anchor = self.cursor
        self.blink = 0.0

    def handle_event(self, e, mouse):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect.collidepoint(e.pos):
                self.focus = True
                idx = self.index_at(e.pos[0])
                now = time.monotonic()
                n = self.clicks[2] + 1 if (now - self.clicks[0] < 0.45 and abs(idx - self.clicks[1]) <= 1) else 1
                self.clicks = (now, idx, n)
                if n == 2:
                    a, b = word_span(self.text, idx)
                    self.anchor, self.cursor = a, b
                    self.dragging = False
                    return True
                if n >= 3:
                    self.anchor, self.cursor = 0, len(self.text)
                    self.dragging = False
                    return True
                self.move(idx, bool(pygame.key.get_mods() & pygame.KMOD_SHIFT))
                self.dragging = True
                return True
            self.focus = False
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            self.cursor = max(0, min(len(self.text), self.index_at(e.pos[0])))
            return True
        elif self.focus and e.type == pygame.TEXTINPUT:
            self.insert(e.text)
            return True
        elif self.focus and e.type == pygame.KEYDOWN:
            return self.key_down(e)
        return False

    def key_down(self, e):
        ctrl = bool(e.mod & (pygame.KMOD_CTRL | pygame.KMOD_META))
        shift = bool(e.mod & pygame.KMOD_SHIFT)
        k = e.key
        if ctrl:
            if k == pygame.K_a:
                self.anchor = 0
                self.cursor = len(self.text)
            elif k == pygame.K_c and self.has_sel():
                a, b = self.sel_range()
                clip_put(self.text[a:b])
            elif k == pygame.K_x and self.has_sel():
                a, b = self.sel_range()
                clip_put(self.text[a:b])
                self.snap("cut")
                self.delete_sel()
            elif k == pygame.K_v:
                self.insert(clip_get())
            elif k == pygame.K_z and not shift:
                self.restore(False)
            elif k == pygame.K_y or (k == pygame.K_z and shift):
                self.restore(True)
            elif nav_key(e) == "home":
                self.move(0, shift)
            elif nav_key(e) == "end":
                self.move(len(self.text), shift)
            else:
                return False
            return True
        if k == pygame.K_BACKSPACE:
            if self.has_sel():
                self.snap("delsel")
                self.delete_sel()
            elif self.cursor > 0:
                self.snap("bs", True)
                self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
                self.cursor = self.anchor = self.cursor - 1
                if self.on_change:
                    self.on_change(self.text)
            return True
        if k == pygame.K_DELETE:
            if self.has_sel():
                self.snap("delsel")
                self.delete_sel()
            elif self.cursor < len(self.text):
                self.snap("del", True)
                self.text = self.text[: self.cursor] + self.text[self.cursor + 1 :]
                if self.on_change:
                    self.on_change(self.text)
            return True
        if k == pygame.K_LEFT:
            if self.has_sel() and not shift:
                self.move(self.sel_range()[0], False)
            else:
                self.move(self.cursor - 1, shift)
            return True
        if k == pygame.K_RIGHT:
            if self.has_sel() and not shift:
                self.move(self.sel_range()[1], False)
            else:
                self.move(self.cursor + 1, shift)
            return True
        if nav_key(e) == "home":
            self.move(0, shift)
            return True
        if nav_key(e) == "end":
            self.move(len(self.text), shift)
            return True
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.on_submit:
                self.on_submit()
            return True
        return False

    def update(self, dt, mouse=None):
        self.blink += dt
        self.shake = max(0.0, self.shake - dt)
        if mouse is not None and self.rect.collidepoint(mouse):
            HOT["text"] = True

    def draw(self, surf, state="normal"):
        dx = int(math.sin(self.shake * 70) * 4) if self.shake > 0 else 0
        r = self.rect.move(dx, 0)
        border = {"normal": (126, 148, 184), "bad": (214, 70, 60), "good": (58, 170, 90)}[state]
        if self.focus and state == "normal":
            border = (60, 130, 220)
        pygame.draw.rect(surf, (255, 255, 255), r, border_radius=5)
        pygame.draw.rect(surf, border, r, 2 if self.focus or state != "normal" else 1, border_radius=5)
        old = surf.get_clip()
        surf.set_clip(r.inflate(-10, -4).clip(old) if old else r.inflate(-10, -4))
        ox = r.x + 12
        cy = r.centery
        if not self.text and self.placeholder:
            ps = text_surf(self.font, self.placeholder, (150, 156, 170))
            surf.blit(ps, ps.get_rect(midleft=(ox, cy)))
        a, b = self.sel_range()
        if a != b:
            x1 = ox + self.font.size(self.text[:a])[0]
            x2 = ox + self.font.size(self.text[:b])[0]
            hl = pygame.Surface((max(2, x2 - x1), r.h - 12), pygame.SRCALPHA)
            hl.fill((51, 153, 255, 110))
            surf.blit(hl, (x1, r.y + 6))
        if self.text:
            ts = text_surf(self.font, self.text, self.color)
            surf.blit(ts, ts.get_rect(midleft=(ox, cy)))
        if self.focus and int(self.blink * 2) % 2 == 0:
            cx = ox + self.font.size(self.text[: self.cursor])[0]
            pygame.draw.rect(surf, self.color, (cx, r.y + 8, 2, r.h - 16))
        surf.set_clip(old)


class Typewriter:
    """Menampilkan teks cerita bertahap dengan efek mesin ketik dan jeda tanda baca."""

    def __init__(self, text, f, width, color, cps=36, line_gap=8, on_tick=None):
        self.font = f
        self.color = color
        self.lines = wrap_lines(f, text, width)
        self.full = "\n".join(self.lines)
        self.shown = 0
        self.acc = 0.0
        self.cps = cps
        self.line_h = f.get_linesize() + line_gap
        self.on_tick = on_tick
        self.pause = 0.0

    @property
    def finished(self):
        return self.shown >= len(self.full)

    def skip(self):
        self.shown = len(self.full)

    def update(self, dt):
        if self.finished:
            return
        self.acc += dt
        while self.acc > 0 and not self.finished:
            if self.pause > 0:
                use = min(self.pause, self.acc)
                self.pause -= use
                self.acc -= use
                if self.pause > 0:
                    break
                continue
            step = 1.0 / self.cps
            if self.acc < step:
                break
            self.acc -= step
            ch = self.full[self.shown]
            self.shown += 1
            if ch in ".!?":
                self.pause = 0.28
            elif ch == ",":
                self.pause = 0.12
            if ch not in " \n" and self.on_tick and self.shown % 2 == 0:
                self.on_tick()

    def draw(self, surf, pos, shadow=None):
        text = self.full[: self.shown]
        y = pos[1]
        for ln in text.split("\n"):
            if shadow:
                surf.blit(text_surf(self.font, ln, shadow), (pos[0] + 1, y + 1))
            surf.blit(text_surf(self.font, ln, self.color), (pos[0], y))
            y += self.line_h
