#!/usr/bin/env python3
"""Build the case-study pages in work/ from _tools/content.py.

Usage:  python3 _tools/build.py
Folders starting with "_" are not published by GitHub Pages (Jekyll).
"""
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import CASES  # noqa: E402

IMG = os.path.join(ROOT, "assets", "img")


def _asset_version():
    import hashlib
    h = hashlib.md5()
    for f in ("assets/css/site.css", "assets/js/site.js"):
        with open(os.path.join(ROOT, f), "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:8]


ASSET_V = _asset_version()
PENDING = []  # Figma frames still waiting for a high-res export
_dims = {}


def esc(s):
    return html.escape(s, quote=True)


def dims(src):
    if src not in _dims:
        from PIL import Image
        with Image.open(os.path.join(IMG, src)) as im:
            _dims[src] = im.size
    return _dims[src]


# ---------- blocks ----------

def fig(f, slug, eager=False):
    if f.get("pending"):
        PENDING.append({"page": slug, "node": f["pending"], "title": f["title"]})
        ar = f.get("ar", "16 / 9")
        cap = f'<figcaption>{f["cap"]}</figcaption>' if f.get("cap") else ""
        return (f'<figure data-figma="{esc(f["pending"])}"><div class="frame placeholder" style="--ar:{ar}">'
                f'<span class="tag">待匯出</span><b>{esc(f["title"])}</b><span>Figma 節點 {esc(f["pending"])}</span>'
                f'</div>{cap}</figure>')
    w, h = dims(f["src"])
    alt = esc(f.get("alt") or strip(f.get("cap", "")))
    loading = 'fetchpriority="high"' if eager else 'loading="lazy"'
    img = f'<img src="../assets/img/{f["src"]}" width="{w}" height="{h}" alt="{alt}" {loading}>'
    tall = f.get("tall", h / w > 1.6 and w >= 900)
    cls = "frame tall" if tall else "frame"
    badge = '<span class="badge-export">預覽圖・待匯出高解析</span>' if f.get("lowres") else ""
    more = '<span class="more">點擊看完整圖</span>' if tall else ""
    if f.get("lowres"):
        PENDING.append({"page": slug, "node": f["lowres"], "title": strip(f.get("cap", f["src"])), "lowres": f["src"]})
    attr = f' data-figma="{esc(f["lowres"])}"' if f.get("lowres") else ""
    inner = f'<div class="{cls}">{badge}{img}{more}</div>'
    if f.get("zoom", True):
        inner = f'<button class="zoom" type="button" aria-label="放大檢視：{alt[:40]}">{inner}</button>'
    cap = f'<figcaption>{f["cap"]}</figcaption>' if f.get("cap") else ""
    return f'<figure{attr}>{inner}{cap}</figure>'


def strip(s):
    import re
    return re.sub(r"<[^>]+>", "", s)


def render(blocks, slug):
    out = []
    for b in blocks:
        kind = b[0]
        if kind == "p":
            out.append(f"<p>{b[1]}</p>")
        elif kind == "ul":
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in b[1]) + "</ul>")
        elif kind == "h3":
            hid = f' id="{b[2]}"' if len(b) > 2 else ""
            out.append(f"<h3{hid}>{b[1]}</h3>")
        elif kind == "h4":
            out.append(f"<h4>{b[1]}</h4>")
        elif kind == "callout":
            out.append(f'<div class="callout"><p>{b[1]}</p></div>')
        elif kind == "todo":
            out.append(f'<p class="todo">{b[1]}</p>')
        elif kind == "cards":
            opts = b[2] if len(b) > 2 else {}
            cls = "cards three" if opts.get("three") else "cards"
            items = []
            for i, (t, d) in enumerate(b[1], 1):
                n = f'<span class="n">{i}</span>' if opts.get("numbered") else ""
                items.append(f"<li>{n}<b>{t}</b><span>{d}</span></li>")
            out.append(f'<ul class="{cls}">' + "".join(items) + "</ul>")
        elif kind == "fig":
            out.append(fig(b[1], slug))
        elif kind == "row":
            n = b[2] if len(b) > 2 else len(b[1])
            out.append(f'<div class="fig-row" style="--n:{n}">' + "".join(fig(f, slug) for f in b[1]) + "</div>")
        elif kind == "phones":
            out.append('<div class="phones">' + "".join(fig(f, slug) for f in b[1]) + "</div>")
        elif kind == "pair":
            before, after = b[1], b[2]
            out.append('<div class="pair">'
                       f'<div class="before"><span class="side-label">BEFORE</span>{render(before, slug)}</div>'
                       f'<div class="after"><span class="side-label">AFTER</span>{render(after, slug)}</div>'
                       "</div>")
        elif kind == "ba":
            # One row per problem: Before / After side by side, one key image each,
            # extra screens folded into <details>.
            rows = []
            for r in b[1]:
                bt, bfig, bmore = r["before"]
                at, afig, amore = r["after"]
                more = ""
                if bmore or amore:
                    n = len(bmore) + len(amore)
                    more = ('<details class="ba-more"><summary>看更多畫面（%d）</summary><div class="ba-extra">'
                            '<div>%s</div><div>%s</div></div></details>') % (
                        n, "".join(fig(f, slug) for f in bmore), "".join(fig(f, slug) for f in amore))
                rows.append(
                    f'<div class="ba-row"><h4><span class="ba-key">{r["key"]}</span>{r["title"]}</h4><div class="ba-grid">'
                    f'<div class="ba-bt"><span class="side-label">BEFORE</span><p>{bt}</p></div>'
                    f'<div class="ba-at"><span class="side-label">AFTER</span><p>{at}</p></div>'
                    f'<div class="ba-bf">{fig(bfig, slug)}</div><div class="ba-af">{fig(afig, slug)}</div>'
                    f'</div>{more}</div>')
            out.append('<div class="ba">' + "".join(rows) + "</div>")
        elif kind == "steps":
            # Numbered process flow drawn in HTML (replaces the old flow images)
            items = "".join(f'<li><span class="step-no">{i:02d}</span><b>{t}</b><span>{d}</span></li>'
                            for i, (t, d) in enumerate(b[1], 1))
            out.append(f'<ol class="steps" style="--n:{len(b[1])}">{items}</ol>')
        elif kind == "tiers":
            # Layered sitemap drawn in HTML: one card per tier, optional sub-apps.
            cards = []
            for t in b[1]:
                chips = "".join(f"<li>{c}</li>" for c in t["chips"])
                sub = ""
                if t.get("sub"):
                    sub = '<div class="tier-sub">' + "".join(
                        f'<div><b>{st}</b><ul class="chips">{"".join(f"<li>{c}</li>" for c in sc)}</ul></div>'
                        for st, sc in t["sub"]) + "</div>"
                cls = "tier main" if t.get("main") else "tier"
                cards.append(f'<div class="{cls}"><div class="tier-head"><span class="tier-n">{t["n"]}</span>'
                             f'<b>{t["title"]}</b><span class="tier-who">{t["who"]}</span></div>'
                             f'<p>{t["desc"]}</p><ul class="chips">{chips}</ul>{sub}</div>')
            cap = f"<figcaption>{b[2]}</figcaption>" if len(b) > 2 else ""
            out.append(f'<figure class="tiers-fig"><div class="tiers">{"".join(cards)}</div>{cap}</figure>')
        elif kind == "tabs":
            tabs, panels = [], []
            for i, t in enumerate(b[1]):
                key = t["key"]
                sel = "true" if i == 0 else "false"
                ti = "" if i == 0 else ' tabindex="-1"'
                tabs.append(f'<button role="tab" id="tab-{key}" aria-controls="panel-{key}" aria-selected="{sel}"{ti}>{t["label"]}</button>')
                hidden = "" if i == 0 else " hidden"
                panels.append(f'<div class="tabpanel" role="tabpanel" id="panel-{key}" aria-labelledby="tab-{key}" tabindex="0"{hidden}>'
                              f'<p class="focus"><b>關注：</b><span>{t["focus"]}</span></p>{fig(t["fig"], slug)}</div>')
            out.append(f'<div class="tabs" data-tabs><div class="tablist" role="tablist" aria-label="{b[2]}">'
                       + "".join(tabs) + "</div>" + "".join(panels) + "</div>")
        elif kind == "compare":
            c = b[1]
            wa, ha = dims(c["after"])
            wb, hb = dims(c["before"])
            out.append(
                '<div class="compare" style="--pos:50%">'
                f'<img src="../assets/img/{c["after"]}" width="{wa}" height="{ha}" alt="{esc(c["alt_after"])}" loading="lazy">'
                f'<div class="before"><img src="../assets/img/{c["before"]}" width="{wb}" height="{hb}" alt="{esc(c["alt_before"])}" loading="lazy"></div>'
                f'<div class="handle" aria-hidden="true"></div><span class="label l">{c["label_before"]}</span><span class="label r">{c["label_after"]}</span>'
                f'<input type="range" min="0" max="100" value="50" aria-label="拖曳比較{esc(c["label_before"])}與{esc(c["label_after"])}">'
                f'</div><figcaption>{c["cap"]}</figcaption>')
        elif kind == "outcome":
            o = b[1]
            big = f'<div class="big">{o["big"]}<small>{o.get("unit", "")}</small></div>' if o.get("big") else ""
            cls = "outcome" if big else "outcome plain"
            out.append(f'<div class="{cls}">{big}<div>{render(o["body"], slug)}</div></div>')
        elif kind == "quotes":
            qs = []
            for q in b[1]:
                img = f'<img src="../assets/img/{q["img"]}" alt="" width="36" height="36">' if q.get("img") else ""
                qs.append(f'<blockquote class="quote"><p>{q["text"]}</p><footer>{img}{q["who"]}</footer></blockquote>')
            out.append('<div class="quotes">' + "".join(qs) + "</div>")
        elif kind == "links":
            cards = []
            for l in b[1]:
                cards.append(f'<a class="next-card" href="{l["href"]}"><b>{l["title"]}</b><span>{l["sub"]}</span></a>')
            out.append('<div class="next-grid">' + "".join(cards) + "</div>")
        elif kind == "html":
            out.append(b[1])
        else:
            raise ValueError(kind)
    return "\n".join(out)


# ---------- page ----------

HEAD = """<!doctype html>
<html lang="zh-Hant-TW">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}｜Joseph Wu</title>
  <meta name="description" content="{desc}">
  <meta property="og:title" content="{h1}">
  <meta property="og:description" content="{desc}">
  <meta property="og:image" content="../assets/img/{og}">
  <meta name="theme-color" content="#0b1122">
  <link rel="icon" href="../images/favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+TC:wght@400;500;700;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../assets/css/site.css?v={v}">
</head>
<body>
  <a class="skip" href="#main">跳到主要內容</a>
  <header class="site-header">
    <div class="wrap">
      <a class="brand" href="../"><span class="brand-mark" aria-hidden="true">J</span>Joseph Wu</a>
      <nav class="nav" aria-label="主選單">
        <a href="../#work">作品</a>
        <a href="../#process">工作方式</a>
        <a href="../#experience">經歷</a>
        <a href="../#contact">聯絡</a>
        <a class="btn-pill" href="https://joserenfu.com/joseph_resume" target="_blank" rel="noopener">下載履歷</a>
      </nav>
    </div>
  </header>
"""

FOOT = """
  <footer class="site-footer">
    <div class="wrap">© 2026 Joseph Wu</div>
  </footer>
  <a class="to-top" href="#main" aria-label="回到頂端">↑</a>
  <script src="../assets/js/site.js?v={v}" defer></script>
</body>
</html>
"""

SECTION_LABELS = ["背景與目標", "挑戰", "解法", "成果"]
SECTION_IDS = ["goal", "challenge", "process", "result"]


def page(c):
    slug = c["slug"]
    summary = "".join(
        f'<div{" class=stat" if len(s) > 2 and s[2] else ""}><dt>{s[0]}</dt><dd>{s[1]}</dd></div>'
        for s in c["summary"])
    cover = c.get("cover")
    cover_html = ""
    if cover:
        cover_html = '<div class="case-cover">' + fig(cover, slug, eager=True).replace("<figure", "<figure style=\"margin:0\"", 1) + "</div>"

    toc, secs = [], []
    for i, sec in enumerate(c["sections"]):
        if c.get("free"):
            # Older works: topics come from the original write-up, heading = topic
            label, blocks = sec
            sid = f"s{i + 1}"
            toc.append(f'<li><a href="#{sid}">{label}</a></li>')
            secs.append(f'<section id="{sid}"><h2 class="topic"><span class="num">{i + 1:02d}</span>{label}</h2>\n'
                        f'{render(blocks, slug)}\n</section>')
            continue
        _, headline, blocks = sec
        label, sid = SECTION_LABELS[i], SECTION_IDS[i]
        toc.append(f'<li><a href="#{sid}">{label}</a></li>')
        secs.append(f'<section id="{sid}"><p class="sec-label"><span class="num">0{i + 1}</span>{label}</p>'
                    f'<h2>{headline}</h2>\n{render(blocks, slug)}\n</section>')

    nxt = c["next"]
    body = f"""
  <main id="main">
    <div class="wrap">
      <header class="case-hero">
        <a class="back" href="../#work"><span aria-hidden="true">←</span> 所有作品</a>
        <span class="eyebrow">{c["eyebrow"]}</span>
        <h1>{c["h1"]}</h1>
        {f'<p class="lead">{c["lead"]}</p>' if c.get("lead") else ""}
        <dl class="summary" style="--cols:{len(c["summary"])}">{summary}</dl>
        {cover_html}
      </header>
    </div>
    <div class="wrap case-layout">
      <nav class="toc" aria-label="本頁目錄"><p>目錄</p><ol>{"".join(toc)}</ol></nav>
      <article class="prose">
{"".join(secs)}
        <a class="next-project" href="{nxt["href"]}"><span>下一個作品</span><b>{nxt["title"]} →</b></a>
      </article>
    </div>
  </main>"""
    og = c.get("og") or (cover or {}).get("src", "tuoyoujia/dash-admin.webp")
    head = HEAD.format(title=esc(c["title"]), desc=esc(c["desc"]), h1=esc(strip(c["h1"])), og=og, v=ASSET_V)
    with open(os.path.join(ROOT, "work", f"{slug}.html"), "w", encoding="utf-8") as fh:
        fh.write(head + body + FOOT.replace("{v}", ASSET_V))


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
    for c in CASES:
        page(c)
        print("built work/%s.html" % c["slug"])
    with open(os.path.join(ROOT, "_tools", "figma-pending.json"), "w", encoding="utf-8") as fh:
        json.dump(PENDING, fh, ensure_ascii=False, indent=1)
    import re
    idx = os.path.join(ROOT, "index.html")
    with open(idx, encoding="utf-8") as fh:
        html_ = fh.read()
    html_ = re.sub(r'assets/(css/site\.css|js/site\.js)(\?v=\w+)?', lambda m: f"assets/{m.group(1)}?v={ASSET_V}", html_)
    with open(idx, "w", encoding="utf-8") as fh:
        fh.write(html_)
    print("%d Figma frames waiting for export -> _tools/figma-pending.json" % len(PENDING))
