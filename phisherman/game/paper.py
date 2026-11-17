import math
import random
import numpy as np
import pygame


def _edge_points(w, h, rs, step=14, jit=2.5):
    pts = []
    for x in range(0, w, step):
        pts.append((x, rs.uniform(0, jit)))
    for y in range(0, h, step):
        pts.append((w - rs.uniform(1, jit + 1), y))
    for x in range(w, 0, -step):
        pts.append((x, h - rs.uniform(1, jit + 1)))
    for y in range(h, 0, -step):
        pts.append((rs.uniform(0, jit), y))
    for _ in range(3):
        i = rs.randrange(len(pts))
        x, y = pts[i]
        cx, cy = w / 2, h / 2
        k = rs.uniform(4, 8) / max(1.0, math.hypot(x - cx, y - cy))
        pts[i] = (x + (cx - x) * k * 3, y + (cy - y) * k * 3)
    return pts


def _facets(overlay, w, h, rs):
    step = 70
    gx = w // step + 2
    gy = h // step + 2
    grid = [[(i * step + rs.uniform(-22, 22), j * step + rs.uniform(-22, 22)) for i in range(gx)] for j in range(gy)]
    for j in range(gy - 1):
        for i in range(gx - 1):
            a, b, c, d = grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]
            for tri in ((a, b, c), (a, c, d)):
                s = rs.uniform(-1, 1)
                col = (255, 255, 255, int(20 * s)) if s > 0 else (30, 20, 0, int(-26 * s))
                pygame.draw.polygon(overlay, col, tri)


def _creases(overlay, w, h, rs, count):
    for _ in range(count):
        x, y = rs.uniform(0, w), rs.uniform(0, h)
        ang = rs.uniform(0, math.tau)
        pts = [(x, y)]
        for _ in range(rs.randrange(4, 12)):
            ang += rs.uniform(-0.4, 0.4)
            x += math.cos(ang) * rs.uniform(12, 30)
            y += math.sin(ang) * rs.uniform(12, 30)
            pts.append((x, y))
        pygame.draw.lines(overlay, (70, 56, 30, 20), False, pts, 4)
        pygame.draw.lines(overlay, (70, 56, 30, 54), False, pts, 1)
        pygame.draw.lines(overlay, (255, 255, 255, 96), False, [(px + 1, py + 1) for px, py in pts], 1)


def _blot(overlay, cx, cy, r, rs):
    pts = []
    n = 22
    for i in range(n):
        a = i * math.tau / n
        rr = r * rs.uniform(0.78, 1.12)
        pts.append((cx + math.cos(a) * rr * 1.2, cy + math.sin(a) * rr))
    pygame.draw.polygon(overlay, (112, 146, 176, 34), pts)
    pygame.draw.lines(overlay, (84, 112, 142, 70), True, pts, 2)


def _drop(overlay, x, y, r):
    pygame.draw.ellipse(overlay, (0, 0, 0, 46), (x - r + 2, y - r + 3, r * 2 + 1, r * 2 + 2))
    pygame.draw.circle(overlay, (206, 232, 250, 84), (x, y), r)
    pygame.draw.circle(overlay, (90, 130, 170, 90), (x + max(1, r // 4), y + max(1, r // 3)), max(1, int(r * 0.7)), 2)
    pygame.draw.circle(overlay, (255, 255, 255, 120), (x, y), r, 1)
    pygame.draw.circle(overlay, (255, 255, 255, 220), (int(x - r * 0.35), int(y - r * 0.38)), max(1, int(r * 0.28)))


def make_paper(w, h, seed, tone=(243, 236, 214), ruled=False, show_through=False, wetness=1.0):
    """Membuat tekstur kertas lecek bertepi tidak rata dengan lipatan bercak air dan tetesan basah lalu mengembalikan Surface berukuran w kali h."""
    rs = random.Random(seed)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill(tone)
    ov = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        k = abs(y / h - 0.5) * 2
        pygame.draw.line(ov, (0, 0, 0, int(26 * k * k)), (0, y), (w, y))
    surf.blit(ov, (0, 0))
    ov = pygame.Surface((w, h), pygame.SRCALPHA)
    _facets(ov, w, h, rs)
    surf.blit(ov, (0, 0))
    if ruled:
        for y in range(70, h - 20, 28):
            pygame.draw.line(surf, (150, 176, 214), (0, y), (w, y), 1)
        pygame.draw.line(surf, (226, 120, 120), (46, 0), (46, h), 2)
    if show_through:
        for y in range(60, h - 40, 26):
            ln = rs.randrange(120, w - 120)
            pygame.draw.line(surf, (120, 106, 80), (60, y), (60 + ln, y), 2)
    ov = pygame.Surface((w, h), pygame.SRCALPHA)
    for _ in range(int(w * h / 180)):
        x, y = rs.randrange(w), rs.randrange(h)
        pygame.draw.line(ov, (140, 120, 90, 16), (x, y), (x + rs.randrange(-6, 7), y + rs.randrange(-3, 4)), 1)
    _creases(ov, w, h, rs, max(10, int(w * h / 22000)))
    surf.blit(ov, (0, 0))
    ov = pygame.Surface((w, h), pygame.SRCALPHA)
    wet_h = int(h * 0.16 * wetness)
    if wet_h > 6:
        pts = [(0, h)]
        for x in range(0, w + 20, 20):
            pts.append((x, h - wet_h + math.sin(x / 40.0 + seed) * 8 + rs.uniform(-4, 4)))
        pts.append((w, h))
        pygame.draw.polygon(ov, (86, 124, 160, 40), pts)
        pygame.draw.lines(ov, (70, 104, 140, 80), False, pts[1:-1], 2)
    for _ in range(int(3 * wetness) + 1):
        _blot(ov, rs.uniform(0.15, 0.85) * w, rs.uniform(0.1, 0.9) * h, rs.uniform(30, 64) * (0.6 + 0.4 * wetness), rs)
    for _ in range(int((w * h) / 16000 * wetness) + 3):
        _drop(ov, rs.randrange(8, w - 8), rs.randrange(8, h - 8), rs.choice((3, 4, 5, 6, 7, 9, 12)))
    surf.blit(ov, (0, 0))
    edge = _edge_points(w, h, rs)
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), edge)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    pygame.draw.polygon(surf, (120, 100, 70, 150), edge, 2)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return surf


def shadow_of(surf, spread=14, alpha=120):
    """Membuat bayangan lembut dari bentuk alpha sebuah Surface dengan tepi buram untuk diletakkan di bawah kertas dan mengembalikan Surface lebih besar dengan ruang tepi sebesar spread."""
    w, h = surf.get_size()
    bw, bh = w + spread * 2, h + spread * 2
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    mask.fill((2, 10, 28, alpha))
    mask.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    base = pygame.Surface((bw, bh), pygame.SRCALPHA)
    base.blit(mask, (spread, spread))
    for div in (8, 5):
        small = pygame.transform.smoothscale(base, (max(1, bw // div), max(1, bh // div)))
        base = pygame.transform.smoothscale(small, (bw, bh))
    return base


def project(pivot, w, h, theta, psi=0.0, focal=1500.0):
    """Memutar kertas bersudut kiri atas di pivot terhadap poros diagonal dari sudut itu lalu memproyeksikannya dengan perspektif dan mengembalikan empat titik layar."""
    n = math.hypot(w, h)
    ax, ay = w / n, h / n
    c, s = math.cos(theta), math.sin(theta)
    cp, sp = math.cos(psi), math.sin(psi)
    pts = []
    for x, y in ((0, 0), (w, 0), (w, h), (0, h)):
        dot = ax * x + ay * y
        rx = x * c + ax * dot * (1 - c)
        ry = y * c + ay * dot * (1 - c)
        rz = (ax * y - ay * x) * s
        k = focal / (focal - rz)
        px, py = rx * k, ry * k
        pts.append((pivot[0] + px * cp - py * sp, pivot[1] + px * sp + py * cp))
    return pts


def _homography(dst, src):
    a = []
    b = []
    for (x, y), (u, v) in zip(dst, src):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        b.append(u)
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b.append(v)
    h = np.linalg.solve(np.array(a, float), np.array(b, float))
    return np.append(h, 1.0).reshape(3, 3)


def warp(tex, quad, shade=1.0):
    """Memetakan tekstur persegi panjang ke segi empat hasil proyeksi dengan pemetaan terbalik dan mengembalikan Surface serta posisi pojok kiri atasnya atau None bila bentuknya hampir pipih."""
    xs = [p[0] for p in quad]
    ys = [p[1] for p in quad]
    x0, y0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
    x1, y1 = int(math.ceil(max(xs))), int(math.ceil(max(ys)))
    bw, bh = x1 - x0, y1 - y0
    if bw < 2 or bh < 2:
        return None
    k = 1.0
    if bw * bh > 140000:
        k = 0.5
    ow, oh = max(2, int(bw * k)), max(2, int(bh * k))
    tw, th = tex.get_size()
    dst = [((p[0] - x0) * k, (p[1] - y0) * k) for p in quad]
    src = [(0, 0), (tw, 0), (tw, th), (0, th)]
    try:
        hm = _homography(dst, src)
    except np.linalg.LinAlgError:
        return None
    gx, gy = np.meshgrid(np.arange(ow, dtype=np.float32) + 0.5, np.arange(oh, dtype=np.float32) + 0.5, indexing="ij")
    hm = hm.astype(np.float32)
    den = hm[2, 0] * gx + hm[2, 1] * gy + hm[2, 2]
    den = np.where(np.abs(den) < 1e-9, 1e-9, den)
    u = (hm[0, 0] * gx + hm[0, 1] * gy + hm[0, 2]) / den
    v = (hm[1, 0] * gx + hm[1, 1] * gy + hm[1, 2]) / den
    inside = (u >= 0) & (u < tw) & (v >= 0) & (v < th)
    ui = np.clip(u.astype(np.int32), 0, tw - 1)
    vi = np.clip(v.astype(np.int32), 0, th - 1)
    rgb = pygame.surfarray.pixels3d(tex)
    al = pygame.surfarray.pixels_alpha(tex)
    out = pygame.Surface((ow, oh), pygame.SRCALPHA)
    orgb = pygame.surfarray.pixels3d(out)
    oal = pygame.surfarray.pixels_alpha(out)
    sampled = rgb[ui, vi]
    if shade != 1.0:
        sampled = (sampled * shade).astype(np.uint8)
    orgb[:] = sampled
    oal[:] = np.where(inside, al[ui, vi], 0)
    del orgb, oal, rgb, al
    if k != 1.0:
        out = pygame.transform.smoothscale(out, (bw, bh))
    return out, (x0, y0)
