#!/usr/bin/env python3
"""One Strawberry - a painterly flat illustration of a single ripe strawberry.

Stdlib only. Renders 1024x1024 and writes entry.png into
$MAKEFUN_OUTPUT_DIR (fallback /output). Deterministic.
SPDX-License-Identifier: MIT
"""
import math
import os
import struct
import zlib

W = H = 1024
CX = 512


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def smoothstep(a, b, x):
    t = clamp((x - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def blend(px, idx, color, alpha):
    if alpha <= 0.0:
        return
    if alpha > 1.0:
        alpha = 1.0
    ia = 1.0 - alpha
    px[idx] = int(px[idx] * ia + color[0] * alpha + 0.5)
    px[idx + 1] = int(px[idx + 1] * ia + color[1] * alpha + 0.5)
    px[idx + 2] = int(px[idx + 2] * ia + color[2] * alpha + 0.5)


def berry_half(t):
    """Half-width factor (0..1) at vertical fraction t (0=top, 1=tip)."""
    if t < 0.0 or t > 1.0:
        return 0.0
    if t < 0.30:
        return 0.64 + 0.36 * math.sin((t / 0.30) * math.pi * 0.5) ** 0.8
    u = (t - 0.30) / 0.70
    return math.cos(u * math.pi * 0.5) ** 0.65


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img = bytearray(W * H * 3)

    # ---- background: warm radial cream gradient + soft vignette ----
    bg_cx, bg_cy = 512.0, 400.0
    maxd = 760.0
    for y in range(H):
        dy = y - bg_cy
        base = y * W * 3
        for x in range(W):
            dx = x - bg_cx
            d = math.sqrt(dx * dx + dy * dy) / maxd
            t = clamp(d)
            # cream centre -> warm peach edge
            r = int(lerp(255, 243, t))
            g = int(lerp(247, 196, t))
            b = int(lerp(224, 148, t))
            i = base + x * 3
            img[i] = r
            img[i + 1] = g
            img[i + 2] = b

    # ---- soft elliptical shadow under the berry ----
    sh_cx, sh_cy, sh_rx, sh_ry = 512.0, 852.0, 250.0, 46.0
    for y in range(int(sh_cy - sh_ry - 4), int(sh_cy + sh_ry + 4)):
        for x in range(int(sh_cx - sh_rx - 4), int(sh_cx + sh_rx + 4)):
            nx = (x - sh_cx) / sh_rx
            ny = (y - sh_cy) / sh_ry
            d2 = nx * nx + ny * ny
            if d2 < 1.3:
                a = 0.34 * (1.0 - smoothstep(0.35, 1.15, d2))
                blend(img, (y * W + x) * 3, (146, 74, 44), a)

    # ---- berry body ----
    top, bottom, wmax = 252.0, 848.0, 228.0
    height = bottom - top
    for y in range(int(top) - 2, int(bottom) + 2):
        t = (y - top) / height
        half = berry_half(t) * wmax
        if half <= 0:
            continue
        x0 = int(CX - half - 3)
        x1 = int(CX + half + 3)
        for x in range(x0, x1 + 1):
            dx = x - CX
            adx = abs(dx)
            cov = clamp((half - adx) / 1.6 + 0.5)
            if cov <= 0:
                continue
            # light from upper-left
            lx = (dx / wmax + 0.45)
            ly = t
            light = clamp(1.05 - 0.55 * math.sqrt(max(0.0, lx * lx * 0.9 + (ly - 0.25) ** 2 * 1.4)))
            rim = clamp(adx / half) if half > 0 else 1.0
            # base: deep red at rim -> bright red-orange toward light
            r = lerp(168, 244, light) - 22 * rim * rim
            g = lerp(10, 62, light * light) - 4 * rim
            b = lerp(22, 42, light) - 6 * rim
            # gentle mottling (fixed analytic pattern, deterministic)
            m = math.sin(x * 0.045 + math.sin(y * 0.021) * 2.0) * math.sin(y * 0.052)
            r += m * 7.0
            g += m * 2.0
            i = (y * W + x) * 3
            blend(img, i, (clamp(r / 255) * 255, clamp(g / 255) * 255, clamp(b / 255) * 255), cov)

    # ---- seeds: staggered rows, darker pit with pale rim ----
    seeds = []
    row_y = 348.0
    row_idx = 0
    while row_y < 760:
        t = (row_y - top) / height
        half = berry_half(t) * wmax * 0.84
        n = max(1, int(half / 44))
        for k in range(-n, n + 1):
            off = (22 if row_idx % 2 else -8)
            sx = CX + k * 46 + off
            if abs(sx - CX) < half - 6:
                # taper seed size toward the tip
                s = 1.0 - 0.35 * max(0.0, t - 0.55)
                seeds.append((sx, row_y + (10 if k % 2 else -4), s))
        row_y += 54
        row_idx += 1
    for sx, sy, s in seeds:
        rx, ry = 9.0 * s, 13.5 * s
        for y in range(int(sy - ry - 4), int(sy + ry + 4)):
            for x in range(int(sx - rx - 4), int(sx + rx + 4)):
                nx = (x - sx) / rx
                ny = (y - sy) / ry
                d2 = nx * nx + ny * ny
                i = (y * W + x) * 3
                if d2 < 1.0:
                    a = 1.0 - smoothstep(0.75, 1.0, d2)
                    blend(img, i, (250, 198, 108), a * 0.97)  # golden seed
                    if d2 < 0.42:
                        blend(img, i, (255, 226, 155), 0.5)
                elif d2 < 1.55:
                    a = (1.0 - smoothstep(1.0, 1.55, d2)) * 0.38
                    blend(img, i, (120, 4, 14), a)  # pit shadow

    # ---- big soft gloss highlight, upper left ----
    gx, gy, grx, gry = 402.0, 392.0, 86.0, 148.0
    cos_a, sin_a = math.cos(-0.42), math.sin(-0.42)
    for y in range(int(gy - gry - 8), int(gy + gry + 8)):
        for x in range(int(gx - grx - 90), int(gx + grx + 90)):
            px_, py_ = x - gx, y - gy
            rx_ = px_ * cos_a - py_ * sin_a
            ry_ = px_ * sin_a + py_ * cos_a
            d2 = (rx_ / grx) ** 2 + (ry_ / gry) ** 2
            if d2 < 1.2:
                a = 0.52 * (1.0 - smoothstep(0.15, 1.05, d2))
                blend(img, (y * W + x) * 3, (255, 244, 238), a)
    # small bright core of the gloss
    for y in range(300, 400):
        for x in range(356, 430):
            d2 = ((x - 392) / 30.0) ** 2 + ((y - 348) / 52.0) ** 2
            if d2 < 1.2:
                a = 0.65 * (1.0 - smoothstep(0.1, 1.05, d2))
                blend(img, (y * W + x) * 3, (255, 255, 252), a)

    # ---- calyx: layered green leaves + stem ----
    leaves = [
        # (cx, cy, rx, ry, angle_deg, colour)
        (398, 268, 118, 34, -24, (38, 138, 52)),
        (626, 268, 118, 34, 24, (38, 138, 52)),
        (452, 244, 112, 32, -10, (52, 164, 62)),
        (572, 244, 112, 32, 10, (52, 164, 62)),
        (512, 232, 104, 34, 0, (66, 182, 74)),
        (352, 292, 84, 26, -46, (30, 118, 46)),
        (672, 292, 84, 26, 46, (30, 118, 46)),
    ]
    for lcx, lcy, lrx, lry, ang, col in leaves:
        a_rad = math.radians(ang)
        ca, sa = math.cos(a_rad), math.sin(a_rad)
        ext = int(lrx + lry + 6)
        for y in range(lcy - ext, lcy + ext):
            for x in range(lcx - ext, lcx + ext):
                px_, py_ = x - lcx, y - lcy
                rx_ = px_ * ca + py_ * sa
                ry_ = -px_ * sa + py_ * ca
                # taper the leaf to a point at its outer end
                taper = 1.0 - 0.55 * clamp((rx_ / lrx) * 0.5 + 0.5) ** 2 if rx_ > 0 else 1.0
                d2 = (rx_ / lrx) ** 2 + (ry_ / (lry * taper)) ** 2
                if d2 < 1.15:
                    cov = 1.0 - smoothstep(0.8, 1.12, d2)
                    shade = 1.0 - 0.18 * clamp(ry_ / lry * 0.5 + 0.5)
                    c = (int(col[0] * shade), int(col[1] * shade), int(col[2] * shade))
                    blend(img, (y * W + x) * 3, c, cov)
    # stem: tapered, slightly tilted, lighter toward the tip
    for y in range(164, 254):
        tilt = (254 - y) * 0.14
        half_w = 7.0 + (y - 164) / 90.0 * 6.0
        for x in range(492, 540):
            d = abs(x - 512 - tilt)
            cov = clamp((half_w - d) / 1.4 + 0.5)
            if cov > 0:
                shade = 0.85 + 0.3 * (y - 164) / 90.0
                blend(img, (y * W + x) * 3,
                      (int(52 * shade), int(146 * shade), int(62 * shade)), cov)

    # ---- water droplets with specular dots ----
    drops = [(618, 470, 21), (376, 566, 15), (548, 648, 12)]
    for dcx, dcy, dr in drops:
        for y in range(dcy - dr - 3, dcy + dr + 3):
            for x in range(dcx - dr - 3, dcx + dr + 3):
                d2 = ((x - dcx) / dr) ** 2 + ((y - dcy) / (dr * 1.12)) ** 2
                i = (y * W + x) * 3
                if d2 < 1.1:
                    a = 1.0 - smoothstep(0.8, 1.08, d2)
                    blend(img, i, (255, 210, 204), a * 0.22)
                    blend(img, i, (255, 255, 255), a * 0.10)
        hx, hy = dcx - dr * 0.34, dcy - dr * 0.38
        for y in range(int(hy - 7), int(hy + 7)):
            for x in range(int(hx - 7), int(hx + 7)):
                if ((x - hx) / 5.0) ** 2 + ((y - hy) / 5.0) ** 2 < 1.0:
                    blend(img, (y * W + x) * 3, (255, 255, 255), 0.92)

    # ---- tiny sparkles ----
    sparkles = [(300, 330, 15), (724, 402, 12), (688, 640, 10), (322, 668, 9)]
    for scx, scy, sr in sparkles:
        for y in range(scy - sr, scy + sr):
            for x in range(scx - sr, scx + sr):
                dx, dy = abs(x - scx), abs(y - scy)
                v = max(0.0, 1.0 - dx / sr) * (1.0 if dy < 2 else 0.0)
                h_ = max(0.0, 1.0 - dy / sr) * (1.0 if dx < 2 else 0.0)
                a = max(v, h_) * 0.85
                if a > 0:
                    blend(img, (y * W + x) * 3, (255, 255, 255), a)
        blend(img, (scy * W + scx) * 3, (255, 255, 255), 0.95)

    write_png(os.path.join(out_dir, "entry.png"), img)


def write_png(path, img):
    raw = bytearray()
    row_bytes = W * 3
    for y in range(H):
        raw.append(0)
        raw.extend(img[y * row_bytes:(y + 1) * row_bytes])

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
