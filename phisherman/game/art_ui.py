import math
import random
import pygame
from .canvas import mix, shade, radial_glow
from . import pixelfont
from . import ui
from . import icons


def aero_wallpaper(w, h, top=(6, 30, 84), mid=(28, 108, 188), bottom=(110, 204, 236), seed=3):
    """Membuat wallpaper bergaya Windows 7 dengan gradien biru cahaya lembut dan pita transparan."""
    s = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        c = mix(top, mid, t / 0.55) if t < 0.55 else mix(mid, bottom, (t - 0.55) / 0.45)
        pygame.draw.line(s, c, (0, y), (w, y))
    r = random.Random(seed)
    for (fx, fy, fr, col) in ((0.22, 0.78, 0.5, (90, 200, 255)), (0.72, 0.34, 0.42, (160, 230, 255)), (0.5, 0.95, 0.6, (255, 255, 255)), (0.9, 0.8, 0.35, (120, 220, 255))):
        rad = int(min(w, h) * fr)
        g = radial_glow(rad, col, 0.55)
        s.blit(g, (int(w * fx) - rad, int(h * fy) - rad), special_flags=pygame.BLEND_RGB_ADD)
    small = pygame.Surface((w // 4, h // 4), pygame.SRCALPHA)
    sw, sh = small.get_size()
    for k in range(7):
        pts = []
        ph = r.random() * 6
        amp = sh * (0.08 + 0.05 * r.random())
        base = sh * (0.25 + k * 0.1)
        for x in range(0, sw + 6, 6):
            pts.append((x, base + math.sin(x / sw * 4.2 + ph) * amp))
        pygame.draw.lines(small, (255, 255, 255, 26 + k * 4), False, pts, 5 + k * 2)
    s.blit(pygame.transform.smoothscale(small, (w, h)), (0, 0))
    beams = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(5):
        x = int(w * (0.1 + 0.2 * i + r.random() * 0.05))
        pygame.draw.polygon(beams, (255, 255, 255, 12), [(x, 0), (x + 40, 0), (x + 220, h), (x - 120, h)])
    s.blit(beams, (0, 0))
    return s


def _doc_icon(d, x, y, color, label):
    pygame.draw.rect(d, (255, 255, 255), (x + 6, y + 2, 34, 44), border_radius=3)
    pygame.draw.rect(d, (150, 160, 180), (x + 6, y + 2, 34, 44), 1, border_radius=3)
    pygame.draw.polygon(d, (210, 216, 226), [(x + 30, y + 2), (x + 40, y + 12), (x + 30, y + 12)])
    pygame.draw.rect(d, color, (x + 6, y + 26, 34, 12))
    for i in range(3):
        pygame.draw.line(d, (190, 196, 210), (x + 11, y + 12 + i * 4), (x + 28, y + 12 + i * 4))
    f = ui.font(10, True)
    t = f.render(label, True, (255, 255, 255))
    d.blit(t, t.get_rect(center=(x + 23, y + 32)))


def _bin_icon(d, x, y):
    pygame.draw.polygon(d, (190, 210, 235), [(x + 9, y + 12), (x + 37, y + 12), (x + 33, y + 44), (x + 13, y + 44)])
    pygame.draw.polygon(d, (120, 150, 190), [(x + 9, y + 12), (x + 37, y + 12), (x + 33, y + 44), (x + 13, y + 44)], 2)
    pygame.draw.rect(d, (150, 180, 215), (x + 6, y + 8, 34, 5), border_radius=2)
    for i in range(3):
        pygame.draw.line(d, (130, 160, 200), (x + 16 + i * 6, y + 18), (x + 17 + i * 5, y + 40), 2)


def desktop(w, h):
    """Menggambar desktop Windows 7 lengkap dengan ikon dan taskbar kaca untuk layar monitor karakter."""
    s = aero_wallpaper(w, h, seed=5)
    f = ui.font(13)
    for i, (label, kind) in enumerate((("Invoice.pdf", "pdf"), ("Targets.xlsx", "xls"), ("Recycle Bin", "bin"))):
        x, y = 14, 14 + i * 84
        if kind == "pdf":
            _doc_icon(s, x, y, (200, 50, 46), "PDF")
        elif kind == "xls":
            _doc_icon(s, x, y, (40, 150, 80), "XLS")
        else:
            _bin_icon(s, x, y)
        ui.draw_text(s, label, f, (255, 255, 255), (x + 23, y + 56), "midtop", shadow=(0, 20, 50))
    return s


def taskbar(w, h=40):
    """Menggambar latar taskbar kaca gelap dengan orb mulai di kiri dan lekukan tray di kanan."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.blit(ui.glass(w, h, 0, (20, 40, 70), 235, True, False), (0, 0))
    pygame.draw.line(s, (170, 210, 255, 160), (0, 0), (w, 0))
    orb = pygame.Surface((44, 44), pygame.SRCALPHA)
    pygame.draw.circle(orb, (10, 40, 90), (22, 22), 21)
    pygame.draw.circle(orb, (40, 120, 210), (22, 22), 19)
    pygame.draw.circle(orb, (110, 190, 250), (22, 26), 14)
    pygame.draw.ellipse(orb, (255, 255, 255, 140), (8, 5, 28, 15))
    t = pixelfont.render("P", 2, color=(255, 255, 255), outline=(10, 50, 110))
    orb.blit(t, t.get_rect(center=(22, 23)))
    s.blit(orb, (6, -3))
    pygame.draw.line(s, (120, 170, 230, 90), (w - 112, 6), (w - 112, h - 6))
    return s


FILE_COLORS = {
    "pdf": ((214, 58, 52), "PDF"),
    "xls": ((40, 150, 80), "XLS"),
    "doc": ((54, 100, 200), "DOC"),
    "zip": ((220, 160, 40), "ZIP"),
    "exe": ((90, 100, 130), "EXE"),
    "ppt": ((220, 100, 50), "PPT"),
    "csv": ((40, 150, 140), "CSV"),
    "img": ((150, 80, 190), "PNG"),
}


def draw_file_icon(surf, kind, center, h=30):
    """Menggambar ikon dokumen kecil berwarna sesuai jenis file dengan sudut terlipat dan label tiga huruf."""
    col, label = FILE_COLORS.get(kind, ((120, 130, 150), "FILE"))
    w = int(h * 0.78)
    x = center[0] - w // 2
    y = center[1] - h // 2
    pygame.draw.rect(surf, (255, 255, 255), (x, y, w, h), border_radius=3)
    pygame.draw.rect(surf, (140, 152, 176), (x, y, w, h), 1, border_radius=3)
    fold = max(5, w // 3)
    pygame.draw.polygon(surf, (214, 220, 232), [(x + w - fold, y), (x + w, y + fold), (x + w - fold, y + fold)])
    bar = pygame.Rect(x + 1, y + int(h * 0.5), w - 2, int(h * 0.3))
    pygame.draw.rect(surf, col, bar)
    f = ui.font(max(8, int(h * 0.26)), True)
    t = ui.text_surf(f, label, (255, 255, 255))
    surf.blit(t, t.get_rect(center=bar.center))
    for i in range(2):
        pygame.draw.line(surf, (190, 198, 214), (x + 4, y + 5 + i * 4), (x + w - fold - 2, y + 5 + i * 4))


def hex_pattern(w, h, color=(14, 40, 58)):
    """Membuat pola heksagon halus untuk latar panel gelap."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    r = 18
    dx = r * 1.5
    dy = r * math.sqrt(3)
    for i in range(int(w / dx) + 2):
        for j in range(int(h / dy) + 2):
            cx = i * dx
            cy = j * dy + (dy / 2 if i % 2 else 0)
            pts = [(cx + r * math.cos(math.radians(60 * k)), cy + r * math.sin(math.radians(60 * k))) for k in range(6)]
            pygame.draw.polygon(s, (*color, 90), pts, 1)
    return s
