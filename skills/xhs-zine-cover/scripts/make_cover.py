#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书「模型大评测」系列封面生成器（极简独立杂志 Zine 风格）

风格规范（不可擅改，保证系列风格统一）：
- 3:4 竖版（默认 1620x2160）
- 浅灰蓝旧纸背景 #D1DCE2，带纸张纤维、扫描颗粒、复印柔化、撕纸边缘、
  Risograph 印刷颗粒、轻微套色偏移
- 左上大号深海军蓝黑 #182A3A 凸版标题「模型大评测」
- 标题下方展示本期模型完整名称
- 打字机字体次要信息：MODEL REVIEW / {期号}、生产实测 {天数} 天
- 下半部分六张竖向撕边纸条：本期模型纸条深灰蓝 #214E78，
  面积比其他大约 20%，向前向上错位；其余暖灰白/浅灰蓝交替
- 留白 58%~65%；禁止人物/机器人/Logo/图标/渐变/水印/额外文案

用法：
python make_cover.py --featured "GLM-5.3 Flash AA" \
  --models "GLM-5.3 Flash AA,GPT-5.6,Claude Opus 4.8,Gemini 3.5,Qwen3.8-Flash,DeepSeek-V4" \
  --issue 01 --days 3 --out cover.png
"""
import argparse
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1620, 2160  # 3:4

BG = (209, 220, 226)          # 浅灰蓝旧纸 #D1DCE2
NAVY = (24, 42, 58)           # 深海军蓝黑 #182A3A（主标题/正文）
FEATURE_BLUE = (33, 78, 120)  # 深灰蓝 #214E78（本期模型纸条）
WARM_WHITE = (239, 237, 230)  # 暖灰白纸条
LIGHT_BLUE = (197, 211, 221)  # 浅灰蓝纸条
SHADOW = (96, 110, 124)       # 纸条投影
MISPRINT = (168, 84, 72)      # Risograph 套色偏移色（低透明度）
STRIP_TEXT_LIGHT = (236, 240, 244)  # 深纸条上的浅字

CJK_FONTS = [
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyh.ttf",
]
MONO_FONTS = [
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\cour.ttf",
]


def pick(candidates):
    for p in candidates:
        if os.path.exists(p):
            return p
    raise SystemExit("找不到可用字体: %s" % candidates)


def cjk(size):
    return ImageFont.truetype(pick(CJK_FONTS), size)


def mono(size):
    return ImageFont.truetype(pick(MONO_FONTS), size)


def torn_polygon(x, y, w, h, seed):
    """撕纸边缘多边形：四条边都带随机毛边"""
    rnd = random.Random(seed)
    amp = max(6, w // 34)
    step = 16
    pts = []
    xs = list(range(int(x), int(x + w), step)) + [int(x + w)]
    ys = list(range(int(y), int(y + h), step * 2)) + [int(y + h)]
    for px in xs:  # 上边缘
        pts.append((px, y + rnd.uniform(-amp, amp)))
    for py in ys:  # 右边缘
        pts.append((x + w + rnd.uniform(-amp * 0.4, amp * 0.4), py))
    for px in reversed(xs):  # 下边缘
        pts.append((px, y + h + rnd.uniform(-amp, amp)))
    for py in reversed(ys):  # 左边缘
        pts.append((x + rnd.uniform(-amp * 0.4, amp * 0.4), py))
    return pts


def vertical_text(text, font, fill):
    """竖排文字（自下而上阅读），返回裁好的 RGBA 图"""
    tmp = Image.new('RGBA', (2200, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.text((0, 0), text, font=font, fill=fill)
    bbox = d.textbbox((0, 0), text, font=font)
    tmp = tmp.crop((0, 0, bbox[2] + 8, bbox[3] + 8))
    return tmp.rotate(90, expand=True)


def paper_texture(img, seed=42):
    """纸张纤维 + 扫描颗粒 + Risograph 颗粒"""
    rnd = random.Random(seed)
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # 纸张纤维：少量浅色短划线
    for _ in range(160):
        x = rnd.randint(0, W)
        y = rnd.randint(0, H)
        ln = rnd.randint(6, 26)
        ang = rnd.uniform(-0.6, 0.6)
        d.line([(x, y), (x + ln, y + int(ln * ang))],
               fill=(255, 255, 255, rnd.randint(10, 26)), width=1)
    for _ in range(90):
        x = rnd.randint(0, W)
        y = rnd.randint(0, H)
        ln = rnd.randint(4, 14)
        d.line([(x, y), (x + ln, y + rnd.randint(-2, 2))],
               fill=(120, 135, 150, rnd.randint(8, 20)), width=1)
    img.paste(overlay, (0, 0), overlay)
    # 扫描/Riso 颗粒：明暗两层噪点，低透明度
    n = Image.effect_noise(img.size, 26)
    dark = Image.new('RGBA', img.size, (52, 64, 76, 0))
    dark.putalpha(n.point(lambda v: 16 if v > 128 else 0))
    img.paste(dark, (0, 0), dark)
    light = Image.new('RGBA', img.size, (255, 255, 255, 0))
    light.putalpha(n.point(lambda v: 14 if v <= 128 else 0))
    img.paste(light, (0, 0), light)
    return img


def draw_offset_text(layer, xy, text, font, fill, misprint_alpha=80):
    """凸版字 + 轻微套色偏移（先画错位色，再画主色）"""
    d = ImageDraw.Draw(layer)
    x, y = xy
    d.text((x + 4, y + 3), text, font=font, fill=MISPRINT + (misprint_alpha,))
    d.text((x, y), text, font=font, fill=fill)


def main():
    ap = argparse.ArgumentParser(description='模型大评测系列封面生成器')
    ap.add_argument('--featured', required=True, help='本期被评测模型完整名称')
    ap.add_argument('--models', required=True,
                    help='六张纸条的模型名，英文逗号分隔（含本期模型，共6个）')
    ap.add_argument('--issue', default='01', help='系列期号，如 01')
    ap.add_argument('--days', default='3', help='生产实测天数')
    ap.add_argument('--title', default='模型大评测', help='系列大标题')
    ap.add_argument('--out', default='cover.png')
    args = ap.parse_args()

    models = [m.strip() for m in args.models.split(',') if m.strip()]
    if len(models) != 6:
        raise SystemExit('必须恰好 6 个模型名，当前 %d 个' % len(models))
    if args.featured not in models:
        raise SystemExit('本期模型必须包含在六个模型名中')

    img = Image.new('RGBA', (W, H), BG + (255,))
    paper_texture(img)

    # ---------- 纸条层（先画，位于画面下半部分） ----------
    strips = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadows = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadows)
    td = ImageDraw.Draw(strips)

    reg_w, feat_w = 148, 178            # 本期纸条大约 20%
    gap = 50
    reg_h, feat_h = 688, 772
    base_y = 1216
    total = feat_w + 5 * reg_w + 5 * gap
    x0 = (W - total) // 2

    cx = x0
    palette = [WARM_WHITE, LIGHT_BLUE]
    for i, name in enumerate(models):
        featured = (name == args.featured)
        w = feat_w if featured else reg_w
        h = feat_h if featured else reg_h
        y = base_y - 58 if featured else base_y  # 向上错位
        color = FEATURE_BLUE if featured else palette[i % 2]
        poly = torn_polygon(cx, y, w, h, seed=hash(name) % 10000 + i)
        sd.polygon([(px + 7, py + 9) for px, py in poly], fill=SHADOW + (52,))
        td.polygon(poly, fill=color + (255,))
        # 撕边纸条上的竖排模型名
        tf = cjk(52 if featured else 44)
        fill = STRIP_TEXT_LIGHT if featured else NAVY
        vt = vertical_text(name, tf, fill)
        if vt.height <= h - 60:
            strips.paste(vt, (cx + (w - vt.width) // 2,
                              y + (h - vt.height) // 2), vt)
        cx += w + gap

    shadows = shadows.filter(ImageFilter.GaussianBlur(5))
    img = Image.alpha_composite(img, shadows)
    img = Image.alpha_composite(img, strips)

    # ---------- 文字层（左上信息区） ----------
    texts = Image.new('RGBA', (W, H), (0, 0, 0, 0))

    # 系列大标题（大号凸版）
    draw_offset_text(texts, (108, 148), args.title, cjk(196), NAVY + (255,))
    # 本期模型完整名称
    draw_offset_text(texts, (116, 430), args.featured, cjk(92), NAVY + (255,),
                     misprint_alpha=60)
    # 打字机次要信息
    draw_offset_text(texts, (120, 596), 'MODEL REVIEW / %s' % args.issue,
                     mono(46), NAVY + (255,), misprint_alpha=50)
    draw_offset_text(texts, (120, 664), '生产实测 %s 天' % args.days,
                     cjk(46), NAVY + (255,), misprint_alpha=50)
    # 细装饰线（克制，一条）
    d = ImageDraw.Draw(texts)
    d.line([(122, 570), (560, 570)], fill=NAVY + (120,), width=3)

    texts = texts.filter(ImageFilter.GaussianBlur(0.55))  # 复印柔化
    img = Image.alpha_composite(img, texts)

    # ---------- 收尾：整体轻颗粒 + 轻微复印模糊 ----------
    n2 = Image.effect_noise(img.size, 18)
    soft = Image.new('RGBA', img.size, (70, 82, 94, 0))
    soft.putalpha(n2.point(lambda v: 8 if v > 128 else 0))
    img = Image.alpha_composite(img, soft)
    img = img.filter(ImageFilter.GaussianBlur(0.3))

    img.convert('RGB').save(args.out, quality=95)
    print(args.out)


if __name__ == '__main__':
    main()
