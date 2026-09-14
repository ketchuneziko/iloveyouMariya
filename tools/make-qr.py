#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор красивых QR-кодов для сайта «до тебя — после тебя».

Делает милые, но полностью читаемые картинки со ссылкой на сайт:
  • qr-night.png   — ночная карточка (как фотография на столике), 1200×1500
  • qr-blush.png   — светлая карточка в розовую «пыль», для печати, 1200×1500
  • qr-embed.png   — квадратный QR без текста, для вставки на сайт, 1080×1080
  • qr.svg         — вектор (печать в любом размере, прозрачный фон)
  • qr-plain.png   — строгий ч/б запасной вариант (для старых камер)

Запуск:
    python3 tools/make-qr.py                       # обычной ссылкой GitHub Pages
    python3 tools/make-qr.py --url https://...     # своей ссылкой
    python3 tools/make-qr.py --module heart        # модули-сердечки (по умолчанию)

Нужны пакеты: qrcode, pillow  (проверка читаемости: opencv-python-headless)
    pip install qrcode pillow opencv-python-headless

Шрифты (Cormorant Garamond / Manrope) ищутся в ./assets/fonts,
потом в ~/.fonts, потом берётся любой доступный DejaVu.
"""
from __future__ import annotations

import argparse
import math
import os
import random
import sys

import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIRS = [os.path.join(ROOT, "assets", "fonts"), os.path.expanduser("~/.fonts"), "/usr/share/fonts"]

# ── палитра сайта ───────────────────────────────────────────────────────────
NIGHT = "#05060d"
INK = "#f3efe8"
COLD = "#93a7d6"
ROSE = "#ff7ea8"
ROSE_SOFT = "#ffc2d4"
ROSE_PALE = "#ffd9e4"
GOLD = "#ffd27d"
VIOLET = "#b38bff"
CREAM = "#fffaf6"


# ══════════════════════════════════════════════════════════════════════════
#  мелочи
# ══════════════════════════════════════════════════════════════════════════

def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def grad(stops, t):
    """stops = [(0, rgb), (0.5, rgb), ...], t в [0,1] -> цвет"""
    t = min(max(t, 0.0), 1.0)
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if t <= p1 or i == len(stops) - 2:
            k = 0 if p1 == p0 else (t - p0) / (p1 - p0)
            return mix(c0, c1, min(max(k, 0.0), 1.0))
    return stops[-1][1]


def find_font(needles, fallback=("DejaVuSerif", "DejaVuSans")):
    """Ищет TTF/OTF/TTC по подстрокам имени файла, рекурсивно по FONT_DIRS."""
    exts = (".ttf", ".otf", ".ttc")
    for d in FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for dirpath, _dirs, files in os.walk(d):
            for n in needles:
                for f in files:
                    if f.lower().endswith(exts) and n.lower() in f.lower():
                        return os.path.join(dirpath, f)
    for d in FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for dirpath, _dirs, files in os.walk(d):
            for n in fallback:
                for f in files:
                    if f.lower().endswith(exts) and n.lower() in f.lower():
                        return os.path.join(dirpath, f)
    return None


class Text:
    """Шрифт + межбуквенный интервал + рисование по центру."""

    def __init__(self, path, size, weight=None, spacing=0.0):
        self.f = ImageFont.truetype(path, size) if path else ImageFont.load_default(size)
        self.spacing = spacing * size
        if weight:
            try:
                self.f.set_variation_by_axes([weight])
            except Exception:
                pass

    def width(self, s):
        if not s:
            return 0
        w = sum(self.f.getlength(ch) + self.spacing for ch in s) - self.spacing
        return w

    def draw(self, dr, xy, s, fill, anchor_center=False, rot=0):
        x, y = xy
        if rot:
            pad = int(self.f.size * 2)
            box = max(1, int(self.width(s) + pad * 2)), int(self.f.size * 2.4 + pad)
            tmp = Image.new("RGBA", box, (0, 0, 0, 0))
            td = ImageDraw.Draw(tmp)
            cx = box[0] / 2 - (self.width(s) / 2 if anchor_center else 0)
            self._chars(td, cx, box[1] / 2 - self.f.size * 0.42, s, fill, "la")
            tmp = tmp.rotate(rot, resample=Image.BICUBIC, expand=True)
            return tmp
        if anchor_center:
            self._chars(dr, x - self.width(s) / 2, y, s, fill, "la")
        else:
            self._chars(dr, x, y, s, fill, "la")
        return None

    def _chars(self, dr, x, y, s, fill, anchor):
        cur = x
        for ch in s:
            dr.text((cur, y), ch, font=self.f, fill=fill, anchor=anchor)
            cur += self.f.getlength(ch) + self.spacing
        return cur - x


def rounded(draw, box, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def heart_points(scale=1.0, cx=0.0, cy=0.0, n=72, squash=1.0):
    """Классическое параметрическое сердечко, остриём вниз."""
    pts = []
    for i in range(n):
        t = math.pi * 2 * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * scale, cy - y * scale * squash))
    return pts


def heart(draw, cx, cy, size, fill, squash=1.0):
    draw.polygon(heart_points(size / 32.0, cx, cy + size * 0.06, 96, squash), fill=fill)


def sparkle(draw, cx, cy, r, color, arms=4):
    """Искорка ✦ — 4 (или 6) лучей с мягким сужением."""
    pts = []
    for i in range(arms * 2):
        a = math.pi * i / arms - math.pi / 2
        rad = r if i % 2 == 0 else r * 0.17
        pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
    draw.polygon(pts, fill=color)


def stars(img, n, seed, box=None, tint=(255, 255, 255)):
    """Мелкие звёзды + пара крупных с крестом."""
    rnd = random.Random(seed)
    w, h = img.size
    x0, y0, x1, y1 = box or (0, 0, w, h)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        a = rnd.randint(40, 210)
        r = rnd.choice([0.8, 1.0, 1.0, 1.4, 1.8, 2.4])
        dr.ellipse([x - r, y - r, x + r, y + r], fill=tint + (a,))
    for _ in range(int(n * 0.06)):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        r = rnd.uniform(3.5, 8.0)
        c = tint + (rnd.randint(120, 200),)
        sparkle(dr, x, y, r * 2.6, c, 4)
        dr.ellipse([x - r * 0.55, y - r * 0.55, x + r * 0.55, y + r * 0.55], fill=tint + (235,))
    layer = layer.filter(ImageFilter.GaussianBlur(0.4))
    img.alpha_composite(layer)
    return img


def nebula(img, cx, cy, rad, color, alpha, blur=90):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    dr.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)
    return img


def vertical_gradient(size, top, bottom):
    w, h = size
    base = Image.new("RGB", (1, h))
    px = base.load()
    for y in range(h):
        px[0, y] = mix(top, bottom, y / max(1, h - 1))
    return base.resize((w, h)).convert("RGBA")


# ══════════════════════════════════════════════════════════════════════════
#  QR-матрица
# ══════════════════════════════════════════════════════════════════════════

ECC_LEVELS = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M, "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H}


def build_matrix(url, ecc="Q", min_version=None):
    qr = qrcode.QRCode(
        version=min_version,
        error_correction=ECC_LEVELS.get(ecc, ERROR_CORRECT_Q),
        box_size=10,
        border=0,  # тихую зону сами нарисуем
    )
    qr.add_data(url)
    qr.make(fit=True)
    m = qr.get_matrix()
    return [[1 if c else 0 for c in row] for row in m], qr.version


def is_finder(r, c, n):
    return (r < 7 and c < 7) or (r < 7 and c >= n - 7) or (r >= n - 7 and c < 7)


def is_alignment(r, c, n):
    if n < 45:  # v6+ их несколько — их тоже стилизуем «в лоб»
        ar, ac = n - 9, n - 9
        return abs(r - (ar + 2)) <= 2 and abs(c - (ac + 2)) <= 2
    return False


def is_timing(r, c, n):
    return (r == 6 or c == 6) and not (r < 8 and c < 8) and not (r < 8 and c >= n - 8) and not (r >= n - 8 and c < 8)


# ══════════════════════════════════════════════════════════════════════════
#  отрисовка модулей: маска + градиент
# ══════════════════════════════════════════════════════════════════════════

def module_shape(dr, shape, x, y, cell, color, fill_ratio):
    """Один модуль. shape: heart | round | square | dot"""
    pad = cell * (1 - fill_ratio) / 2
    box = [x + pad, y + pad, x + cell - pad - 1, y + cell - pad - 1]
    if shape == "square":
        dr.rectangle(box, fill=color)
    elif shape == "round":
        dr.rounded_rectangle(box, radius=cell * 0.30 * fill_ratio, fill=color)
    elif shape == "dot":
        r = (box[2] - box[0]) / 2
        dr.ellipse([x + cell / 2 - r, y + cell / 2 - r, x + cell / 2 + r, y + cell / 2 + r], fill=color)
    else:  # heart
        heart(dr, x + cell / 2, y + cell / 2, cell * fill_ratio * 1.16, color, squash=0.94)


def draw_finder(dr, x, y, cell, color=255, hole=0, rf=0.6):
    """
    7×7 «глаз»: кольцо + ядро 3×3.
    rf — сила скругления (в модулях). Больше 0.8 камеры уже путаются,
    поэтому 0.6:squircle-уголок есть, а структура 1:1:3:1:1 цела.
    """
    outer = [x, y, x + 7 * cell - 1, y + 7 * cell - 1]
    dr.rounded_rectangle(outer, radius=cell * rf, fill=color)
    inner = [x + cell, y + cell, x + 6 * cell - 1, y + 6 * cell - 1]
    dr.rounded_rectangle(inner, radius=cell * max(0.0, rf - 0.45), fill=hole)
    core = [x + 2 * cell, y + 2 * cell, x + 5 * cell - 1, y + 5 * cell - 1]
    dr.rounded_rectangle(core, radius=cell * rf * 0.42, fill=color)


def draw_alignment(dr, x, y, cell, color, hole=255, rf=0.45):
    outer = [x, y, x + 5 * cell - 1, y + 5 * cell - 1]
    dr.rounded_rectangle(outer, radius=cell * rf, fill=color)
    inner = [x + cell, y + cell, x + 4 * cell - 1, y + 4 * cell - 1]
    dr.rounded_rectangle(inner, radius=cell * max(0.0, rf - 0.3), fill=hole)
    core = [x + 2 * cell, y + 2 * cell, x + 3 * cell - 1, y + 3 * cell - 1]
    dr.rounded_rectangle(core, radius=cell * rf * 0.5, fill=color)


def qr_mask_layers(matrix, px, shape, fill_ratio, finder_color, logo_ratio=0.0, finder_round=0.6):
    """
    Возвращает (data_mask, finder_mask): два режима L для будущих градиентов.
    data_mask рисует всё, кроме finder-паттернов.
    """
    n = len(matrix)
    cell = px / n
    data = Image.new("L", (px, px), 0)
    finders = Image.new("L", (px, px), 0)
    dd = ImageDraw.Draw(data)
    fd = ImageDraw.Draw(finders)

    for r in range(n):
        for c in range(n):
            if not matrix[r][c]:
                continue
            x, y = c * cell, r * cell
            if is_finder(r, c, n):
                continue  # дорисуем целыми блоками
            elif is_alignment(r, c, n):
                if r == n - 9 and c == n - 9:
                    draw_alignment(dd, x, y, cell, 255, 0, finder_round * 0.75)
                continue
            ratio = fill_ratio
            if is_timing(r, c, n) and shape == "heart":
                ratio = min(1.0, fill_ratio * 1.08)
            module_shape(dd, shape, x, y, cell, 255, ratio)

    for (r, c) in [(0, 0), (0, n - 7), (n - 7, 0)]:
        draw_finder(fd, c * cell, r * cell, cell, 255, 0, finder_round)

    # «дырка» под центральный бейдж — в него не лезут ни модули, ни градиент
    if logo_ratio:
        d = px * logo_ratio
        box = [(px - d) / 2, (px - d) / 2, (px + d) / 2, (px + d) / 2]
        dd.rounded_rectangle(box, radius=d * 0.34, fill=0)
        fd.rounded_rectangle(box, radius=d * 0.34, fill=0)
    return data, finders, cell


def gradient_layer(px, stops, diagonal=True):
    """Диагональный градиент размера px×px из остановок [(pos, rgb)]."""
    small = 256
    g = Image.new("RGB", (small, small))
    gp = g.load()
    for y in range(small):
        for x in range(small):
            t = (x / (small - 1) * 0.55 + y / (small - 1) * 0.45) if diagonal else y / (small - 1)
            gp[x, y] = grad(stops, t)
    return g.resize((px, px))


def colored_qr(matrix, px, shape, fill_ratio, data_stops, finder_rgb, logo_ratio=0.0, bg=None, finder_round=0.6):
    data_m, find_m, cell = qr_mask_layers(matrix, px, shape, fill_ratio, finder_rgb, logo_ratio, finder_round)
    out = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    data_g = gradient_layer(px, data_stops).convert("RGBA")
    data_g.putalpha(data_m)
    out = Image.alpha_composite(out, data_g)
    find_g = Image.new("RGBA", (px, px), tuple(finder_rgb) + (0,))
    find_g.putalpha(find_m)
    out = Image.alpha_composite(out, find_g)
    return out, cell


# ══════════════════════════════════════════════════════════════════════════
#  центральный бейдж-сердечко
# ══════════════════════════════════════════════════════════════════════════

def heart_badge(px, cell, n, ring_rgb=(255, 255, 255), ratio=0.0):
    d = px * (ratio or 0.185)
    img = Image.new("RGBA", (int(d * 2.2), int(d * 2.2)), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    cx = cy = img.size[0] / 2
    dr.ellipse([cx - d, cy - d, cx + d, cy + d], fill=ring_rgb + (255,))
    dr.ellipse([cx - d * 0.87, cy - d * 0.87, cx + d * 0.87, cy + d * 0.87],
               fill=mix(ring_rgb, (255, 255, 255), 0.0) + (255,))
    # сердечко с градиентом
    hs = d * 1.18
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon(heart_points(hs / 32.0, cx, cy + hs * 0.05, 128, 0.95), fill=255)
    g = Image.new("RGBA", img.size)
    gp = g.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            gp[x, y] = grad([(0, hexrgb(ROSE)), (1, hexrgb(VIOLET))], (x + y) / (img.size[0] * 2))
    g.putalpha(mask)
    img = Image.alpha_composite(img, g)
    return img, (cx, cy)


# ══════════════════════════════════════════════════════════════════════════
#  карточки
# ══════════════════════════════════════════════════════════════════════════

def compose_qr_panel(matrix, cfg):
    """
    Печатаемая (light) подложка + сам QR + бейдж.
    Возвращает RGBA-изображение px×px, готовое вставить в карточку.
    """
    px = cfg["qr_px"]
    panel = Image.new("RGBA", (px, px), cfg["panel"] + (255,))
    dr = ImageDraw.Draw(panel)
    rounded(dr, [0, 0, px - 1, px - 1], px * 0.055, fill=cfg["panel"] + (255,))
    quiet = int(px * cfg["quiet"])
    inner = px - quiet * 2
    qr_img, cell = colored_qr(
        matrix, inner, cfg["shape"], cfg["fill"], cfg["data_stops"], cfg["finder"], cfg["logo"],
        finder_round=cfg.get("finder_round", 0.6),
    )
    panel.alpha_composite(qr_img, (quiet, quiet))
    if cfg["logo"]:
        badge, (bcx, bcy) = heart_badge(inner, cell, len(matrix), cfg["panel"], cfg["logo"])
        panel.alpha_composite(badge, (int(round(quiet + inner / 2 - bcx)), int(round(quiet + inner / 2 - bcy))))
    if cfg.get("corners"):
        col = cfg["corners"] + (235,)
        inset = quiet * 0.42
        ln = px * 0.075
        wd = max(4, int(px * 0.0075))
        pts = [
            (inset, inset, 1, 1), (px - inset, inset, -1, 1),
            (inset, px - inset, 1, -1), (px - inset, px - inset, -1, -1),
        ]
        for (x, y, dx, dy) in pts:
            dr.line([x, y, x + dx * ln, y], fill=col, width=wd)
            dr.line([x, y, x, y + dy * ln], fill=col, width=wd)
    return panel



def stamp(size, text_a, text_b, fonts, ink, rot=-13):
    """Резиновый штамп: пунктирный круг + две строки. Мило и «по-домашнему»."""
    S = int(size * 2.6)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    c = S / 2
    r_out, r_in = size, size * 0.82
    # пунктирный внешний круг
    steps = 46
    for i in range(steps):
        if i % 2:
            continue
        a0 = math.tau * i / steps
        a1 = math.tau * (i + 0.78) / steps
        dr.arc([c - r_out, c - r_out, c + r_out, c + r_out], math.degrees(a0), math.degrees(a1), fill=ink + (215,), width=4)
    dr.ellipse([c - r_in, c - r_in, c + r_in, c + r_in], outline=ink + (150,), width=2)
    fonts["stamp_a"].draw(dr, (c, c - r_in * 0.62), text_a, ink + (235,), anchor_center=True)
    heart(dr, c, c + r_in * 0.055, r_in * 0.30, ink + (225,), squash=0.95)
    fonts["stamp_b"].draw(dr, (c, c + r_in * 0.44), text_b, ink + (215,), anchor_center=True)
    img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
    # лёгкая «неровность» печати
    noize = Image.new("L", img.size, 255)
    nd = ImageDraw.Draw(noize)
    rnd = random.Random(7)
    for _ in range(240):
        x, y = rnd.uniform(0, img.size[0]), rnd.uniform(0, img.size[1])
        r = rnd.uniform(1.2, 4.2)
        nd.ellipse([x - r, y - r, x + r, y + r], fill=rnd.randint(150, 235))
    a = img.getchannel("A")
    img.putalpha(ImageChops.multiply(a, noize))
    return img


def note(size, text, fonts, bg, fg, rot=-5):
    """Открыточная записка-стикер с надписью от руки."""
    pad_x, pad_y = size * 0.34, size * 0.2
    tw = fonts["note"].width(text)
    img = Image.new("RGBA", (int(tw + pad_x * 2), int(size * 1.25)), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    rounded(dr, [0, 0, img.size[0] - 1, img.size[1] - 1], img.size[1] * 0.28, fill=bg + (250,))
    dr.line([pad_x * 0.6, img.size[1] - pad_y * 0.55, img.size[0] - pad_x * 0.6, img.size[1] - pad_y * 0.55],
            fill=fg + (60,), width=2)
    fonts["note"].draw(dr, (img.size[0] / 2, img.size[1] * 0.30), text, fg + (255,), anchor_center=True)
    return img.rotate(rot, resample=Image.BICUBIC, expand=True)


def tape(dr, cx, cy, w, h, angle, color):
    tmp = Image.new("RGBA", (int(w * 1.6), int(h * 2)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.rounded_rectangle([tmp.size[0] / 2 - w / 2, tmp.size[1] / 2 - h / 2,
                         tmp.size[0] / 2 + w / 2, tmp.size[1] / 2 + h / 2], 6, fill=color)
    tmp = tmp.rotate(angle, resample=Image.BICUBIC)
    return tmp, (cx - tmp.size[0] / 2, cy - tmp.size[1] / 2)


def caption(dr, panel_bottom, cfg, fonts, W):
    """Текстовый блок под QR (для больших карточек)."""
    t = cfg["text"]
    y = panel_bottom + 30
    if t.get("pre"):
        txt = t["pre"]
        fonts["pre"].draw(dr, (W / 2, y), txt, cfg["pre_col"], anchor_center=True)
        half = fonts["pre"].width(txt) / 2 + 34
        for sgn in (-1, 1):
            sparkle(dr, W / 2 + sgn * half, y + 15, 11, cfg["pre_col"] + (220,), 4)
            sparkle(dr, W / 2 + sgn * (half + 26), y + 15, 5, cfg["pre_col"] + (120,), 4)
        y += 46
    fonts["title"].draw(dr, (W / 2, y), t["title"], cfg["title_col"], anchor_center=True)
    y += 78
    fonts["sub"].draw(dr, (W / 2, y), t["sub"], cfg["sub_col"], anchor_center=True)
    y += 52
    fonts["tiny"].draw(dr, (W / 2, y), t["code"], cfg["code_col"], anchor_center=True)
    # разделитель: ♥ ✦ ♥
    ry = y + 62
    col = cfg["divider_col"] + (200,)
    for i, (dx, kind) in enumerate([(-58, "h"), (0, "s"), (58, "h")]):
        if kind == "h":
            heart(dr, W / 2 + dx, ry, 16, cfg["divider_col"] + (185,), squash=0.95)
        else:
            sparkle(dr, W / 2 + dx, ry, 17, cfg["divider_col"] + (190,), 4)
    dr.line([W / 2 - 150, ry, W / 2 - 78, ry], fill=cfg["divider_col"] + (90,), width=2)
    dr.line([W / 2 + 78, ry, W / 2 + 150, ry], fill=cfg["divider_col"] + (90,), width=2)


def make_card(cfg, matrix, fonts, path):
    W, H = cfg["size"]
    img = Image.new("RGBA", (W, H))
    dr = ImageDraw.Draw(img)

    # ── фон ──
    img.alpha_composite(vertical_gradient((W, H), cfg["bg_top"], cfg["bg_bottom"]))
    for (cx, cy, rad, col, a, b) in cfg["nebulas"]:
        nebula(img, cx * W, cy * H, rad, hexrgb(col), a, b)
    if cfg["stars"]:
        stars(img, cfg["stars"], cfg["seed"], tint=cfg["star_tint"])
    dr = ImageDraw.Draw(img)

    # ── карточка-«полароид» ──
    cx0, cy0 = cfg["card"]
    cw, ch = cfg["card_size"]
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    rounded(sd, [cx0 + 8, cy0 + 26, cx0 + cw + 8, cy0 + ch + 26], 34, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(26))
    img.alpha_composite(shadow)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    rounded(gd, [cx0 - 18, cy0 - 18, cx0 + cw + 18, cy0 + ch + 18], 44, fill=cfg["glow"] + (120,))
    glow = glow.filter(ImageFilter.GaussianBlur(48))
    img.alpha_composite(glow)

    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    rounded(cd, [cx0, cy0, cx0 + cw, cy0 + ch], 30, fill=cfg["card_bg"] + (255,))
    rounded(cd, [cx0 + 1, cy0 + 1, cx0 + cw - 2, cy0 + ch - 2], 29, outline=cfg["card_border"] + (120,), width=2)
    img.alpha_composite(card)

    # ── QR-панель ──
    qr_img = compose_qr_panel(matrix, cfg)
    qpx = cfg["qr_px"]
    qx, qy = cx0 + (cw - qpx) / 2, cy0 + cfg["qr_top"]
    img.alpha_composite(qr_img, (int(qx), int(qy)))

    dr = ImageDraw.Draw(img)
    # ── тексты ──
    caption(dr, qy + qpx, cfg, fonts, W)
    # ── штамп и записка ──
    st = cfg.get("stamp")
    if st:
        simg = stamp(st["r"], st["a"], st["b"], fonts, st["col"], st["rot"])
        img.alpha_composite(simg, (int(cx0 + cw - simg.size[0] * 0.62), int(cy0 - simg.size[1] * 0.18)))
    nt = cfg.get("note")
    if nt:
        nimg = note(nt["size"], nt["text"], fonts, nt["bg"], nt["col"], nt["rot"])
        img.alpha_composite(nimg, (int(cx0 + cw * nt["x"]), int(cy0 + ch * nt["y"])))
    # URL-чип
    chip_w = fonts["url"].width(cfg["url"]) + 78
    chip_h = 54
    chx, chy = W / 2 - chip_w / 2, cy0 + ch - chip_h - 34
    rounded(dr, [chx, chy, chx + chip_w, chy + chip_h], chip_h / 2,
            fill=cfg["chip_bg"] + (255,), outline=cfg["chip_border"] + (190,), width=2)
    heart(dr, chx + 26, chy + chip_h / 2, 15, cfg["chip_heart"] + (255,), squash=0.95)
    heart(dr, chx + chip_w - 26, chy + chip_h / 2, 15, cfg["chip_heart"] + (255,), squash=0.95)
    fonts["url"].draw(dr, (W / 2, chy + 13), cfg["url"], cfg["url_col"], anchor_center=True)

    # ── декор: скотч + искорки ──
    for (tcx, tcy, ang, col) in cfg["tapes"]:
        t, pos = tape(dr, tcx * W, tcy * H, cfg["tape_w"], 58, ang, col)
        img.alpha_composite(t, tuple(int(round(v)) for v in pos))
    dec = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dec)
    for (sx, sy, sr, sa) in cfg["sparkles"]:
        sparkle(dd, sx * W, sy * H, sr, cfg["sparkle_col"] + (sa,), 4)
    for (hx, hy, hs, ha) in cfg["float_hearts"]:
        heart(dd, hx * W, hy * H, hs, cfg["float_col"] + (ha,), squash=0.95)
    dec = dec.filter(ImageFilter.GaussianBlur(0.3))
    img.alpha_composite(dec)

    img.convert("RGB").save(path, optimize=True)
    print("  •", os.path.relpath(path, ROOT), img.size)


def make_embed(cfg, matrix, path):
    """Квадратная картинка для сайта: только QR + мягкое свечение (без текста)."""
    S = cfg["size"][0]
    pad = int(S * 0.06)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    rounded(gd, [pad - 14, pad - 14, S - pad + 14, S - pad + 14], S * 0.07, fill=hexrgb(ROSE) + (110,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(34)))
    panel = compose_qr_panel(matrix, cfg)
    img.alpha_composite(panel, (int(pad), int(pad)))
    img.convert("RGBA").save(path, optimize=True)
    print("  •", os.path.relpath(path, ROOT), img.size)


def make_plain(matrix, path, px=900, border_modules=4):
    """Строгий ч/б вариант — на случай капризной камеры."""
    n = len(matrix)
    cell = px // (n + border_modules * 2)
    total = cell * (n + border_modules * 2)
    img = Image.new("RGB", (total, total), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    for r in range(n):
        for c in range(n):
            if matrix[r][c]:
                dr.rectangle([cell * (c + border_modules), cell * (r + border_modules),
                              cell * (c + border_modules + 1) - 1, cell * (r + border_modules + 1) - 1],
                             fill=(10, 10, 16))
    img.save(path, optimize=True)
    print("  •", os.path.relpath(path, ROOT), img.size)


# ══════════════════════════════════════════════════════════════════════════
#  SVG (вектор: печать без потерь, прозрачный фон)
# ══════════════════════════════════════════════════════════════════════════

def svg_heart_path(cell, fill_ratio):
    pad = cell * (1 - fill_ratio) / 2
    pts = heart_points((cell * fill_ratio * 1.16) / 32.0, cell / 2, cell / 2 + cell * 0.06 * fill_ratio, 40, 0.94)
    d = "M" + " L".join(f"{x - pad:.2f} {y - pad:.2f}" for x, y in pts) + " Z"
    return d


def svg_finder(cell, rf=0.6):
    """
    Кольцо + ядро 3×3, как в PNG-рендере (скругление деликатное — иначе камеры путаются).
    Дырку внутри не закрашиваем: под «глазами» всё равно нет модулей, а прозрачность
    позволяет положить код на любой фон.
    """
    ring = (f'<path d="M{cell*rf:.2f} 0 H{7*cell-cell*rf:.2f} A{cell*rf:.2f} {cell*rf:.2f} 0 0 1 {7*cell:.2f} {cell*rf:.2f} '
            f'V{7*cell-cell*rf:.2f} A{cell*rf:.2f} {cell*rf:.2f} 0 0 1 {7*cell-cell*rf:.2f} {7*cell:.2f} '
            f'H{cell*rf:.2f} A{cell*rf:.2f} {cell*rf:.2f} 0 0 1 0 {7*cell-cell*rf:.2f} '
            f'V{cell*rf:.2f} A{cell*rf:.2f} {cell*rf:.2f} 0 0 1 {cell*rf:.2f} 0 Z" fill="url(#qd)"/>')
    core = (f'<rect x="{2*cell:.2f}" y="{2*cell:.2f}" width="{3*cell:.2f}" height="{3*cell:.2f}" '
            f'rx="{cell*rf*0.42:.2f}" fill="url(#qd)"/>')
    return ring + core


def make_svg(matrix, path, shape="heart", fill_ratio=0.94, logo=True, px=1000, rf=0.6, plate=True):
    """
    Векторная версия: сердечки-модули, скруглённые «глаза», сердце в центре.
    Фон прозрачный — код можно класть на любую подложку (тихую зону даёт белый круг).
    """
    n = len(matrix)
    cell = px / n
    stops = [
        (0, hexrgb(ROSE)),
        (0.42, hexrgb(VIOLET)),
        (0.78, mix(hexrgb(ROSE), hexrgb(GOLD), 0.55)),
        (1, hexrgb(GOLD)),
    ]
    grad_stops = "".join(
        f'<stop offset="{p*100:.0f}%" stop-color="#{c[0]:02x}{c[1]:02x}{c[2]:02x}"/>' for p, c in stops
    )

    # зона центра, куда не заходят модули (под неё рисуем белый круг + сердечко)
    lr = px * 0.185 * 1.18 if logo else 0.0
    cc_x = cc_y = px / 2

    parts = []
    unit = svg_heart_path(cell, fill_ratio) if shape == "heart" else None
    for r in range(n):
        for c in range(n):
            if not matrix[r][c] or is_finder(r, c, n) or is_alignment(r, c, n):
                continue
            mx, my = c * cell + cell / 2, r * cell + cell / 2
            if lr and math.hypot(mx - cc_x, my - cc_y) < lr:
                continue
            if unit is not None:
                parts.append(f'<g transform="translate({c*cell:.2f} {r*cell:.2f})"><path d="{unit}"/></g>')
            else:
                pad = cell * (1 - fill_ratio) / 2
                rad = cell * 0.3 if shape in ("round", "dot") else 0
                parts.append(
                    f'<rect x="{c*cell+pad:.2f}" y="{r*cell+pad:.2f}" width="{cell*fill_ratio:.2f}" '
                    f'height="{cell*fill_ratio:.2f}" rx="{rad:.2f}"/>'
                )
    for (r, c) in [(0, 0), (0, n - 7), (n - 7, 0)]:
        parts.append(f'<g transform="translate({c*cell:.2f} {r*cell:.2f})">{svg_finder(cell, rf)}</g>')
    if n < 45:
        ar = ac = n - 9
        inner = (
            f'<rect x="0" y="0" width="{5*cell:.2f}" height="{5*cell:.2f}" rx="{cell*rf*0.75:.2f}" fill="url(#qd)"/>'
            f'<rect x="{2*cell:.2f}" y="{2*cell:.2f}" width="{cell:.2f}" height="{cell:.2f}" '
            f'rx="{cell*rf*0.375:.2f}" fill="url(#qd)"/>'
        )
        parts.append(f'<g transform="translate({ac*cell:.2f} {ar*cell:.2f})">{inner}</g>')
    body = "".join(parts)

    badge = ""
    if logo:
        d = px * 0.185
        hs = d * 0.95
        hp = "M" + " L".join(
            f"{x:.2f} {y:.2f}" for x, y in heart_points(hs / 32.0 * 1.06, cc_x, cc_y + hs * 0.06, 96, 0.95)
        ) + " Z"
        badge = (
            f'<circle cx="{cc_x:.1f}" cy="{cc_y:.1f}" r="{d*1.18:.1f}" fill="{CREAM}"/>'
            f'<path d="{hp}" fill="url(#bd)"/>'
            f'<circle cx="{cc_x-d*0.3:.1f}" cy="{cc_y-d*0.3:.1f}" r="{d*0.09:.1f}" fill="#ffffff" fill-opacity="0.75"/>'
        )
    quiet = cell * 2
    bg = ""
    if plate:
        # белая «тарелка» = тихая зона: без неё на тёмном фоне камеры могут не взять код
        m = quiet * 1.15
        bg = (f'<rect x="{-m:.1f}" y="{-m:.1f}" width="{px+2*m:.1f}" height="{px+2*m:.1f}" '
              f'rx="{px*0.055:.1f}" fill="{CREAM}"/>')
    out = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-quiet:.1f} {-quiet:.1f} {px+2*quiet:.1f} {px+2*quiet:.1f}" '
        f'width="{px+2*quiet:.0f}" height="{px+2*quiet:.0f}" shape-rendering="geometricPrecision">'
        f"{bg}"
        f'<defs><linearGradient id="qd" x1="0" y1="0" x2="{px}" y2="{px}" gradientUnits="userSpaceOnUse">'
        f'{grad_stops}</linearGradient>'
        f'<linearGradient id="bd" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{ROSE}"/><stop offset="100%" stop-color="{VIOLET}"/></linearGradient></defs>'
        f'<g fill="url(#qd)">{body}</g>{badge}</svg>'
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print("  •", os.path.relpath(path, ROOT), f"{os.path.getsize(path)/1024:.0f} KB")


# ══════════════════════════════════════════════════════════════════════════
#  конфиг карточек
# ══════════════════════════════════════════════════════════════════════════

def card_configs(url):
    W, H = 1200, 1500
    base = dict(
        size=(W, H),
        seed=1402,
        stars=0,
        star_tint=(255, 255, 255),
        nebulas=[],
        tape_w=230,
        tapes=[],
        sparkles=[],
        float_hearts=[],
        url=url,
        card=(100, 96, 1000, 1310)[:2],
        card_size=(1000, 1310),
        qr_top=44,
        qr_px=840,
        quiet=0.10,
        shape="heart",
        fill=0.97,
        logo=0.185,
        finder_round=0.6,
        dashed=None,
        text=dict(pre="для Марии",
                  title="до тебя — после тебя",
                  sub="наведи камеру телефона — и наша история откроется",
                  code="143 ♥ 520"),
        stamp=None,
        note=None,
    )
    night = dict(base)
    night.update(
        bg_top=hexrgb("#04050c"),
        bg_bottom=hexrgb("#150c22"),
        nebulas=[(0.2, 0.14, 420, ROSE, 90, 130), (0.85, 0.3, 360, VIOLET, 80, 150), (0.5, 0.92, 460, GOLD, 42, 160)],
        stars=520,
        card_bg=hexrgb(CREAM),
        card_border=hexrgb(GOLD),
        glow=hexrgb(ROSE),
        panel=hexrgb(CREAM),
        data_stops=[(0, hexrgb("#d63f78")), (0.4, hexrgb("#8b5fe0")), (0.72, hexrgb("#c47a24")), (1, hexrgb("#c14f6c"))],
        finder=hexrgb("#c23a6d"),
        sparkle_col=hexrgb(GOLD),
        float_col=hexrgb(ROSE_PALE),
        sparkles=[(0.11, 0.05, 22, 190), (0.9, 0.08, 16, 150), (0.07, 0.9, 18, 160), (0.93, 0.87, 26, 200), (0.5, 0.035, 12, 130)],
        float_hearts=[(0.13, 0.955, 20, 150), (0.88, 0.945, 26, 170), (0.06, 0.5, 14, 110), (0.95, 0.52, 16, 120)],
        tapes=[],
        chip_bg=hexrgb("#ffeff5"),
        chip_border=hexrgb(ROSE),
        chip_heart=hexrgb(ROSE),
        url_col=hexrgb("#9c3964"),
        corners=hexrgb(ROSE_SOFT),
        pre_col=hexrgb("#c23a6d"),
        divider_col=hexrgb(ROSE),
        stamp=dict(r=86, a="143", b="520", col=hexrgb("#d1477f"), rot=-14),
        note=dict(size=54, text="♥ навсегда", bg=hexrgb(GOLD), col=hexrgb("#4a2740"), rot=-4, x=-0.055, y=0.985),
    )
    night_fonts = dict(title_col=hexrgb("#3b2340"), sub_col=hexrgb("#8a6f7f"), code_col=hexrgb("#c23a6d"))
    night.update(night_fonts)

    blush = dict(base)
    blush.update(
        bg_top=hexrgb("#fff3f8"),
        bg_bottom=hexrgb("#f0e8ff"),
        nebulas=[(0.15, 0.1, 380, ROSE_SOFT, 120, 120), (0.9, 0.75, 420, VIOLET, 45, 150)],
        star_tint=(255, 255, 255),
        card_bg=(255, 255, 255),
        card_border=hexrgb(ROSE_SOFT),
        glow=hexrgb(ROSE_PALE),
        panel=(255, 255, 255),
        data_stops=[(0, hexrgb("#cf3a73")), (0.4, hexrgb("#7f52d8")), (0.72, hexrgb("#b8721e")), (1, hexrgb("#b8435f"))],
        finder=hexrgb("#b93568"),
        sparkle_col=hexrgb("#ffc2d4"),
        float_col=hexrgb(ROSE_SOFT),
        sparkles=[(0.1, 0.06, 18, 170), (0.92, 0.1, 14, 150), (0.08, 0.93, 20, 170), (0.93, 0.9, 16, 150)],
        float_hearts=[(0.1, 0.28, 18, 150), (0.91, 0.35, 22, 160), (0.14, 0.72, 16, 140), (0.88, 0.68, 20, 150)],
        tapes=[],
        chip_bg=hexrgb("#fff3f8"),
        chip_border=hexrgb(ROSE_SOFT),
        chip_heart=hexrgb(ROSE),
        url_col=hexrgb("#a13d68"),
        corners=hexrgb(ROSE_SOFT),
        pre_col=hexrgb("#c23a6d"),
        divider_col=hexrgb(ROSE),
        stamp=dict(r=86, a="143", b="520", col=hexrgb("#d1477f"), rot=-14),
        note=dict(size=54, text="я тебя люблю ♥", bg=hexrgb(ROSE_PALE), col=hexrgb("#a13d68"), rot=-4, x=-0.055, y=0.985),
    )
    blush.update(dict(title_col=hexrgb("#4a2740"), sub_col=hexrgb("#8f7286"), code_col=hexrgb("#c23a6d")))
    return night, blush


def embed_config(url, shape, fill):
    return dict(
        size=(1080,),
        qr_px=980,
        quiet=0.10,
        shape=shape,
        fill=fill,
        logo=0.185,
        finder_round=0.6,
        panel=hexrgb(CREAM),
        data_stops=[(0, hexrgb("#d63f78")), (0.4, hexrgb("#8b5fe0")), (0.72, hexrgb("#c47a24")), (1, hexrgb("#c14f6c"))],
        finder=hexrgb("#c23a6d"),
        corners=None,
        text=None,
        card=None,
    )


def load_fonts(cfg, path_hints):
    serif = path_hints.get("serif") or find_font(["CormorantGaramond", "Cormorant", "Playfair", "EB Garamond", "Georgia"])
    sans = path_hints.get("sans") or find_font(["Manrope", "Inter", "Montserrat", "Nunito"])
    serif_it = path_hints.get("serif_it") or find_font(["CormorantGaramond-Italic", "Italic", "Oblique"]) or serif
    f = {
        "pre": Text(sans, 23, 600, spacing=0.22),
        "title": Text(serif_it or serif, 62, 600, spacing=0.02),
        "stamp_a": Text(sans, 30, 700, spacing=0.06),
        "stamp_b": Text(sans, 26, 700, spacing=0.06),
        "note": Text(serif_it or serif, 34, 600, spacing=0.02),
        "sub": Text(sans, 27, 500, spacing=0.08),
        "tiny": Text(serif_it or serif, 40, 500, spacing=0.14),
        "url": Text(sans, 27, 600, spacing=0.03),
    }
    return f


# ══════════════════════════════════════════════════════════════════════════
#  проверка читаемости
# ══════════════════════════════════════════════════════════════════════════

def verify(paths, url, log=print):
    """
    Эмуляция «камеры из кармана»: сжимаем, крутим, блюрим, затемняем, JPEG-им.
    OK = декодер читает код вплоть до указанной доли исходного размера.
    """
    try:
        import cv2
        import numpy as np
    except Exception:
        log("  (opencv не найден — пропускаю автотест читаемости)")
        return None
    det = cv2.QRCodeDetector()

    def decode(img):
        try:
            data, _p, _s = det.detectAndDecode(img)
            return data == url
        except Exception:
            return False

    ok_all = True
    for p in paths:
        img = cv2.imread(p)
        if img is None:
            continue
        h, w = img.shape[:2]
        scales, min_ok = (1.0, 0.6, 0.45, 0.32, 0.24, 0.18, 0.14), 0.0
        for sc in scales:
            im = cv2.resize(img, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
            if decode(im):
                min_ok = min(min_ok, sc) if min_ok else sc
        rot = cv2.warpAffine(
            cv2.resize(img, (520, 520), interpolation=cv2.INTER_AREA),
            cv2.getRotationMatrix2D((260, 260), 7, 0.97), (520, 520), borderValue=(250, 250, 250))
        blur = cv2.GaussianBlur(cv2.resize(img, (520, 520), interpolation=cv2.INTER_AREA), (5, 5), 0)
        dark = cv2.convertScaleAbs(cv2.resize(img, (520, 520), interpolation=cv2.INTER_AREA), alpha=0.55, beta=8)
        ok_, buf = cv2.imencode(".jpg", cv2.resize(img, (520, 520), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 35])
        jpeg = decode(cv2.imdecode(buf, cv2.IMREAD_COLOR)) if ok_ else False
        tests = {
            "520px": decode(cv2.resize(img, (520, 520), interpolation=cv2.INTER_AREA)),
            "поворот 7°": decode(rot),
            "размытие": decode(blur),
            "темно": decode(dark),
            "jpeg35": jpeg,
        }
        good = min_ok > 0
        ok_all &= good and all(tests.values())
        log(f"  {os.path.basename(p):16s} читается до {min_ok*100:3.0f}% размера | " +
            " ".join(f"{k}:{'+' if v else '−'}" for k, v in tests.items()))
    log("  (телефонные камеры обычно заметно добрее этого эмулятора)")
    return ok_all


# ══════════════════════════════════════════════════════════════════════════
#  main
# ══════════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description="красивые QR-карточки для сайта")
    ap.add_argument("--url", default="https://ketchuneziko.github.io/iloveyouMariya/", help="ссылка в QR")
    ap.add_argument("--out", default=os.path.join(ROOT, "assets", "qr"), help="куда класть файлы")
    ap.add_argument("--module", choices=["heart", "round", "square", "dot"], default="heart", help="форма модулей")
    ap.add_argument("--fill", type=float, default=0.94, help="заполнение ячейки модулем, 0.7–1.0")
    ap.add_argument("--logo", type=float, default=0.185, help="размер сердечка в центре (доля QR), 0 — убрать")
    ap.add_argument("--ecc", choices=list("LMQH"), default="Q", help="запас коррекции ошибок (Q — чтобы сердце влезло)")
    ap.add_argument("--svg-transparent", action="store_true", help="в .svg не рисовать белую подложку (тихую зону сам нарисуешь)")
    ap.add_argument("--finder-round", type=float, default=0.6, help="скругление «глаз»: до ~0.8 камеры ещё читают")
    ap.add_argument("--serif", default=None)
    ap.add_argument("--sans", default=None)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    matrix, version = build_matrix(args.url, args.ecc)
    n = len(matrix)
    print(f"ссылка: {args.url}")
    print(f"QR: версия {version}, матрица {n}×{n}, ECC = {args.ecc} (избыточность позволяет спрятать сердечко в центре)\n")

    cfg_night, cfg_blush = card_configs(args.url)
    rf = max(0.0, min(1.6, args.finder_round))
    for c in (cfg_night, cfg_blush):
        c["shape"] = args.module
        c["fill"] = max(0.6, min(1.0, args.fill))
        c["logo"] = args.logo
        c["finder_round"] = rf
    fonts = load_fonts(cfg_night, {"serif": args.serif, "sans": args.sans})

    print("карточки:")
    make_card(cfg_night, matrix, fonts, os.path.join(args.out, "qr-night.png"))
    make_card(cfg_blush, matrix, fonts, os.path.join(args.out, "qr-blush.png"))
    ec = embed_config(args.url, args.module, args.fill)
    ec["logo"] = args.logo
    ec["finder_round"] = rf
    make_embed(ec, matrix, os.path.join(args.out, "qr-embed.png"))
    make_plain(matrix, os.path.join(args.out, "qr-plain.png"))
    make_svg(
        matrix,
        os.path.join(args.out, "qr.svg"),
        shape=args.module if args.module in ("heart", "round", "square") else "round",
        fill_ratio=args.fill,
        logo=bool(args.logo),
        rf=args.finder_round,
        plate=not args.svg_transparent,
    )

    print("\nтест читаемости:")
    ok = verify([os.path.join(args.out, f) for f in ("qr-night.png", "qr-blush.png", "qr-embed.png", "qr-plain.png")], args.url)
    if ok is False:
        print("\n⚠️  не все кода читаются эмулятором — попробуй --module round --logo 0.14")
        sys.exit(1)
    print("\nготово ♥")


if __name__ == "__main__":
    main()
