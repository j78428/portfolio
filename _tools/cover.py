#!/usr/bin/env python3
"""Compose the 托幼加 cover: desktop dashboard + teacher & parent mini-program.

Usage:  python3 _tools/cover.py
Inputs (assets/img/tuoyoujia/):
  dash-admin.webp   desktop screen
  app-parent.webp   parent mini-program home
  app-teacher-new.webp  teacher mini-program home (new version). Until it is
                    exported from Figma (node 8355:88545), a marked placeholder is drawn.
Output: assets/img/tuoyoujia/cover-hero.webp (2400×1350)
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "assets", "img", "tuoyoujia")
W, H = 2400, 1350
NAVY_DEEP, NAVY, YELLOW = (12, 34, 80), (20, 51, 110), (245, 196, 69)
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"


def rounded(im, r):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], r, fill=255)
    out = Image.new("RGBA", im.size)
    out.paste(im, (0, 0), mask)
    return out


def shadow(canvas, box, r, blur=40, offset=(0, 24), alpha=110):
    x0, y0, x1, y1 = box
    pad = blur * 3
    sh = Image.new("RGBA", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad, pad + x1 - x0, pad + y1 - y0], r, fill=(4, 12, 32, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(sh, (x0 - pad + offset[0], y0 - pad + offset[1]))


def phone(screen, width):
    """Phone with a dark bezel; screen is cropped to a 375×812 ratio from the top."""
    bezel = int(width * 0.035)
    sw = width - bezel * 2
    sh = int(sw * 812 / 375)
    s = screen.convert("RGB")
    s = s.resize((sw, int(s.height * sw / s.width)), Image.LANCZOS).crop((0, 0, sw, sh))
    body = Image.new("RGBA", (width, sh + bezel * 2), (0, 0, 0, 0))
    ImageDraw.Draw(body).rounded_rectangle([0, 0, width - 1, body.height - 1], int(width * 0.16), fill=(17, 22, 33, 255))
    body.alpha_composite(rounded(s, int(width * 0.13)), (bezel, bezel))
    return body


def placeholder_screen(w=375, h=812):
    im = Image.new("RGB", (w, h), (243, 245, 249))
    d = ImageDraw.Draw(im)
    for x in range(-h, w, 24):
        d.line([(x, h), (x + h, 0)], fill=(234, 238, 245), width=10)
    f1, f2 = ImageFont.truetype(FONT, 26), ImageFont.truetype(FONT, 18)
    d.rounded_rectangle([w // 2 - 62, h // 2 - 70, w // 2 + 62, h // 2 - 30], 20, fill=YELLOW)
    d.text((w // 2, h // 2 - 50), "待匯出", font=f2, fill=NAVY_DEEP, anchor="mm")
    d.text((w // 2, h // 2 + 6), "老師端主頁（新版）", font=f1, fill=NAVY_DEEP, anchor="mm")
    d.text((w // 2, h // 2 + 44), "Figma 8355:88545", font=f2, fill=(106, 115, 137), anchor="mm")
    return im


def main():
    c = Image.new("RGBA", (W, H))
    # background: navy gradient + yellow accent circle
    grad = Image.linear_gradient("L").rotate(-35, expand=True).resize((W, H))
    bg = Image.composite(Image.new("RGBA", (W, H), NAVY + (255,)), Image.new("RGBA", (W, H), NAVY_DEEP + (255,)), grad)
    c.alpha_composite(bg)
    d = ImageDraw.Draw(c)
    d.ellipse([W - 520, -260, W + 160, 420], fill=YELLOW + (235,))
    d.ellipse([-220, H - 260, 260, H + 220], outline=(255, 255, 255, 40), width=3)

    # desktop window
    dash = Image.open(os.path.join(DIR, "dash-admin.webp")).convert("RGB")
    dw = 1640
    dh = int(dash.height * dw / dash.width)
    bar = 46
    win = Image.new("RGBA", (dw, dh + bar), (255, 255, 255, 255))
    wd = ImageDraw.Draw(win)
    wd.rectangle([0, 0, dw, bar], fill=(236, 239, 245))
    for i, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        wd.ellipse([22 + i * 26, 15, 38 + i * 26, 31], fill=col)
    win.paste(dash.resize((dw, dh), Image.LANCZOS), (0, bar))
    win = rounded(win, 18)
    x0, y0 = 150, 170
    shadow(c, (x0, y0, x0 + dw, y0 + win.height), 18, blur=50, alpha=140)
    c.alpha_composite(win, (x0, y0))

    # phones: teacher (back) + parent (front)
    tpath = os.path.join(DIR, "app-teacher-new.webp")
    teacher = Image.open(tpath) if os.path.exists(tpath) else placeholder_screen()
    parent = Image.open(os.path.join(DIR, "app-parent.webp"))
    pw = 400
    t = phone(teacher, pw)
    p = phone(parent, pw)
    tx, ty = 1440, 330
    px, py = 1800, 250
    shadow(c, (tx, ty, tx + t.width, ty + t.height), 60, blur=45, alpha=150)
    c.alpha_composite(t, (tx, ty))
    shadow(c, (px, py, px + p.width, py + p.height), 60, blur=45, alpha=150)
    c.alpha_composite(p, (px, py))

    out = os.path.join(DIR, "cover-hero.webp")
    c.convert("RGB").save(out, "WEBP", quality=86)
    print("saved", out, "(teacher placeholder)" if not os.path.exists(tpath) else "")


if __name__ == "__main__":
    main()
