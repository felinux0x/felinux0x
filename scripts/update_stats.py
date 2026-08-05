#!/usr/bin/env python3
"""Gera cards de stats do GitHub (PNG 400x180, dark) via PIL.

Roda localmente ou num GitHub Action para atualizar os cards automaticamente
sem depender de servicos externos (ex: github-readme-stats.vercel.app).

Uso: python3 scripts/update_stats.py
"""
import json
import os
import urllib.request

from PIL import Image, ImageDraw, ImageFont

USER = "fxlpz"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "img")
W, H = 400, 180
BG = (13, 17, 23)          # #0d1117
GRAY_TITLE = (143, 143, 143)  # #8f8f8f
WHITE = (237, 237, 237)    # #ededed
GRAY_LABEL = (102, 102, 102)  # #666666
GRAY_NAME = (201, 201, 201)   # #c9c9c9
BAR = (90, 90, 90)         # #5a5a5a
GRAY_COUNT = (111, 111, 111)  # #6f6f6f
BAR_TEXT = (22, 22, 22)    # #161616


def find_font(name):
    for base in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu"):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"fonte nao encontrada: {name}")


def load_font(size, bold=False):
    name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    return ImageFont.truetype(find_font(name), size)


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "fxlpz-stats-bot", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_data():
    u = fetch_json(f"https://api.github.com/users/{USER}")
    repos = fetch_json(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=updated")
    langs = {}
    for r in repos:
        l = r.get("language")
        if l:
            langs[l] = langs.get(l, 0) + 1
    top = sorted(langs.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
    return {
        "repos": u.get("public_repos", 0),
        "followers": u.get("followers", 0),
        "following": u.get("following", 0),
        "langs": top,
    }


def draw_tracked(draw, xy, text, font, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def make_stats(data):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = load_font(13)
    f_num = load_font(42, bold=True)
    f_label = load_font(12)
    draw_tracked(d, (16, 24), "GITHUB STATS", f_title, GRAY_TITLE, tracking=2)
    for (num, label), x in zip(
        [
            (str(data["repos"]), "REPOS"),
            (str(data["followers"]), "FOLLOWERS"),
            (str(data["following"]), "FOLLOWING"),
        ],
        [16, 150, 292],
    ):
        d.text((x, 88), num, font=f_num, fill=WHITE)
        draw_tracked(d, (x, 140), label, f_label, GRAY_LABEL, tracking=1)
    img.save(os.path.join(OUT_DIR, "stats.png"))


def make_langs(data):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = load_font(13)
    f_name = load_font(12)
    f_pct = load_font(10, bold=True)
    f_count = load_font(12)
    draw_tracked(d, (16, 24), "TOP LANGUAGES", f_title, GRAY_TITLE, tracking=2)
    total = sum(c for _, c in data["langs"]) or 1
    y = 62
    for name, c in data["langs"]:
        pct = c * 100.0 / total
        barw = max(4, int(pct * 3.0))
        d.text((16, y), name, font=f_name, fill=GRAY_NAME)
        d.rounded_rectangle([112, y - 8, 112 + barw, y + 2], radius=3, fill=BAR)
        d.text((118, y - 7), f"{int(pct)}%", font=f_pct, fill=BAR_TEXT)
        d.text((368, y), f"{c} repos", font=f_count, fill=GRAY_COUNT, anchor="rs")
        y += 20
    img.save(os.path.join(OUT_DIR, "langs.png"))


if __name__ == "__main__":
    data = fetch_data()
    make_stats(data)
    make_langs(data)
    print(
        "ok: "
        f"{data['repos']} repos, {data['followers']} followers, "
        f"{data['following']} following, langs={[l for l, _ in data['langs']]}"
    )
