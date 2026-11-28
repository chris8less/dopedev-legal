#!/usr/bin/env python3
"""로로의 생일별 모험 블로그 만들기.

_src/*.txt 원고를 읽어 글 페이지, 목록(index.html), 카테고리 페이지,
RSS(feed.xml), 사이트 루트 sitemap.xml 을 다시 만든다.
외부 패키지 없이 python3 만으로 돈다.  사용법: python3 _tools/build.py
"""
import html
import json
import re
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from pathlib import Path

BLOG = Path(__file__).resolve().parent.parent          # birthday-adventure/blog
ROOT = BLOG.parent.parent                              # 저장소 루트
SITE = "https://chris8less.github.io/dopedev-legal/"
BASE = SITE + "birthday-adventure/blog/"
KST = timezone(timedelta(hours=9))

BLOG_NAME = "로로의 생일별 모험"
BLOG_DESC = ("평일 저녁 생일, 촛불만 끄고 끝나기 아쉽죠? 거실에서 바로 해 볼 수 있는 "
             "생일 이벤트 아이디어와 준비 팁, 로봇 로로가 선물 찾기를 진행하는 앱 "
             "'생일별 모험' 이야기를 올려요.")
AUTHOR = "도프데브"
APP_URL = "https://apps.apple.com/kr/app/id6838710536"

# 카테고리: 이름 -> 주소 조각. 새 카테고리는 여기에 한 줄 더한다.
CATEGORIES = {
    "생일 이벤트 아이디어": "birthday-ideas",
    "앱 소식": "app-news",
}
CATEGORY_EMPTY = "아직 쓴 글이 없어요. 앱에 새 소식이 생기면 여기에 올릴게요."

# sitemap.xml 에 함께 넣을 블로그 밖 페이지(저장소 루트 기준 경로)
STATIC_PAGES = ["", "birthday-adventure/privacy.html", "birthday-adventure/support.html"]

e = html.escape

# 손으로 그린 선물 상자(헤더에 한 번만 쓴다)
GIFT_SVG = """<svg class="sketch" viewBox="0 0 92 84" width="76" height="70" aria-hidden="true" focusable="false">
<g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M13 35.5c21-1.2 45-.4 66.5.8M14.2 35.8l1.3 37.6c18 1.6 37.8 1.4 58.9-.2l.9-36.4"/>
<path d="M10.6 27.4c23.4-1.8 46.8-1.6 71 .4l-.6 8.6c-23.8-.9-47.6-.7-70.2.4z"/>
<path d="M44.8 27.9l-.7 46.3M50.3 28l.4 45.8"/>
<path d="M46.9 26.6c-6.5-9.8-18.7-15.4-21.2-9.3-2 5 9.4 8.6 20.6 9.4"/>
<path d="M48.6 26.4c4.4-10.4 17.3-17.6 20.4-11.7 2.6 5.1-8.6 10.3-19.8 11.9"/>
<path d="M6 12.5l3.2 2.6M4.4 21l4-.3M84.5 9.8l-2.6 3.4M88 18.6l-4 .8"/>
</g></svg>"""

SQUIGGLE = ('<svg class="squiggle" viewBox="0 0 300 12" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
            '<path d="M2 7c18-6 30 5 47 0s29-6 46 0 31 4 47-1 30-5 48 1 29 5 46-1 34-4 62 1" '
            'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>')


def parse_post(path):
    text = path.read_text(encoding="utf-8")
    head, body = text.split("\n---\n", 1)
    meta = {}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    for k in ("title", "slug", "date", "category", "description"):
        if not meta.get(k):
            raise SystemExit(f"{path.name}: '{k}' 줄이 없어요")
    if meta["category"] not in CATEGORIES:
        raise SystemExit(f"{path.name}: 카테고리 '{meta['category']}' 는 build.py CATEGORIES 에 없어요")
    hh, mm = (meta.get("time") or "09:00").split(":")
    y, mo, d = map(int, meta["date"].split("-"))
    meta["dt"] = datetime(y, mo, d, int(hh), int(mm), tzinfo=KST)
    meta["tags"] = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    meta["body"] = body.strip("\n")
    meta["url"] = BASE + meta["slug"] + ".html"
    first = next(l for l in meta["body"].splitlines() if l.strip())
    meta["excerpt"] = first
    return meta


def inline(s):
    s = e(s, quote=False)
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', s)


def render_body(body):
    """원고 규칙: 빈 줄 = 문단 묶음 사이, '■ ' = 소제목, '1. ' = 번호 목록,
    '- ' = 점 목록, 'Q. 질문 — 답' = 묻고 답하기, '만든 사람:' = 글쓴이 줄."""
    out = []
    for block in re.split(r"\n\s*\n", body):
        lines = [l.rstrip() for l in block.splitlines() if l.strip()]
        i = 0
        group = []

        def flush():
            if group:
                out.append('<div class="para">' + "".join(f"<p>{inline(g)}</p>" for g in group) + "</div>")
                group.clear()
        while i < len(lines):
            l = lines[i]
            if l.startswith("■"):
                flush()
                out.append(f"<h2>{inline(l.lstrip('■ ').strip())}</h2>")
                i += 1
            elif re.match(r"\d+\.\s", l):
                flush()
                items = []
                while i < len(lines) and re.match(r"\d+\.\s", lines[i]):
                    items.append(re.sub(r"^\d+\.\s+", "", lines[i]))
                    i += 1
                out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            elif l.startswith("- "):
                flush()
                items = []
                while i < len(lines) and lines[i].startswith("- "):
                    items.append(lines[i][2:])
                    i += 1
                out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            elif l.startswith("Q. "):
                flush()
                items = []
                while i < len(lines) and lines[i].startswith("Q. "):
                    q, _, a = lines[i][3:].partition(" — ")
                    items.append(f'<dt>Q. {inline(q)}</dt><dd>{inline(a)}</dd>')
                    i += 1
                out.append('<dl class="faq">' + "".join(items) + "</dl>")
            elif l.startswith("만든 사람:"):
                flush()
                out.append(f'<p class="sign">{inline(l)}</p>')
                i += 1
            else:
                group.append(l)
                i += 1
        flush()
    return "\n".join(out)


def kdate(dt):
    return f"{dt.year}. {dt.month}. {dt.day}."


def page(*, title, description, canonical, og_type, body, rel, jsonld, extra_head=""):
    a = rel + "assets/"
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{e(BLOG_NAME)}">
<meta property="og:locale" content="ko_KR">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary">
{extra_head}<link rel="alternate" type="application/rss+xml" title="{e(BLOG_NAME)}" href="{BASE}feed.xml">
<link rel="preload" href="{a}nanum-pen.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{a}blog.css">
<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False, indent=1)}
</script>
</head>
<body>
{body}
</body>
</html>
"""


def masthead(rel, small=False):
    cls = "mast small" if small else "mast"
    intro = "" if small else f'\n<p class="intro">{e(BLOG_DESC)}</p>'
    tag = "p" if small else "h1"
    return f"""<header class="{cls}">
{GIFT_SVG}
<{tag} class="name"><a href="{rel}index.html">{e(BLOG_NAME)}</a></{tag}>{intro}
{SQUIGGLE}
</header>"""


def nav(rel, current):
    links = [("전체", rel + "index.html", current == "")]
    for name, slug in CATEGORIES.items():
        links.append((name, f"{rel}category/{slug}.html", current == name))
    parts = []
    for name, href, on in links:
        parts.append(f'<a href="{href}" aria-current="page">{e(name)}</a>' if on else f'<a href="{href}">{e(name)}</a>')
    return '<nav class="cats" aria-label="카테고리">' + '<span aria-hidden="true"> · </span>'.join(parts) + "</nav>"


def footer(rel):
    return f"""<footer class="foot">
<p>{e(BLOG_NAME)}은 앱 ‘생일별 모험’을 만든 {AUTHOR}가 직접 씁니다. 광고와 방문 추적 도구는 달지 않았어요.</p>
<p><a href="{rel}../support.html">앱 지원·문의</a> · <a href="{rel}../privacy.html">개인정보처리방침</a> · <a href="{BASE}feed.xml">RSS</a></p>
<p>© {AUTHOR}</p>
</footer>"""


def post_list(posts, rel, show_cat=True):
    items = []
    for p in posts:
        cat = f' · <a href="{rel}category/{CATEGORIES[p["category"]]}.html">{e(p["category"])}</a>' if show_cat else ""
        items.append(f"""<li>
<p class="when"><time datetime="{p['date']}">{kdate(p['dt'])}</time>{cat}</p>
<h2 class="t"><a href="{rel}{p['slug']}.html">{e(p['title'])}</a></h2>
<p class="ex">{e(p['excerpt'])}</p>
</li>""")
    return '<ol class="posts" reversed>\n' + "\n".join(items) + "\n</ol>"


def build():
    posts = sorted((parse_post(p) for p in sorted((BLOG / "_src").glob("*.txt"))),
                   key=lambda p: p["dt"], reverse=True)
    slugs = [p["slug"] for p in posts]
    if len(set(slugs)) != len(slugs):
        raise SystemExit("slug 가 겹치는 글이 있어요")

    org = {"@type": "Organization", "name": AUTHOR, "url": SITE}

    # 글 페이지
    for idx, p in enumerate(posts):
        others = [q for q in posts if q is not p][:5]
        more = ""
        if others:
            more = ('<section class="more"><h2>다른 글</h2><ul>' +
                    "".join(f'<li><a href="{q["slug"]}.html">{e(q["title"])}</a></li>' for q in others) +
                    "</ul></section>")
        tags = ""
        if p["tags"]:
            tags = '<p class="tags">' + " ".join(f"<span>#{e(t)}</span>" for t in p["tags"]) + "</p>"
        cat_href = f"category/{CATEGORIES[p['category']]}.html"
        body = f"""{masthead('', small=True)}
<main class="wrap">
<article>
<p class="crumb"><a href="index.html">{e(BLOG_NAME)}</a> › <a href="{cat_href}">{e(p['category'])}</a></p>
<h1 class="title">{e(p['title'])}</h1>
<p class="when"><time datetime="{p['dt'].isoformat()}">{kdate(p['dt'])}</time> · 글 {AUTHOR}</p>
<div class="body">
{render_body(p['body'])}
</div>
{tags}
</article>
{more}
</main>
{footer('')}"""
        jsonld = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": p["title"],
            "description": p["description"],
            "datePublished": p["dt"].isoformat(),
            "dateModified": p["dt"].isoformat(),
            "inLanguage": "ko-KR",
            "articleSection": p["category"],
            "keywords": p["tags"],
            "author": org,
            "publisher": org,
            "mainEntityOfPage": {"@type": "WebPage", "@id": p["url"]},
            "url": p["url"],
            "isPartOf": {"@type": "Blog", "name": BLOG_NAME, "url": BASE},
        }
        extra = (f'<meta property="article:published_time" content="{p["dt"].isoformat()}">\n'
                 f'<meta property="article:section" content="{e(p["category"])}">\n' +
                 "".join(f'<meta property="article:tag" content="{e(t)}">\n' for t in p["tags"]))
        (BLOG / f"{p['slug']}.html").write_text(page(
            title=f"{p['title']} | {BLOG_NAME}", description=p["description"], canonical=p["url"],
            og_type="article", body=body, rel="", jsonld=jsonld, extra_head=extra), encoding="utf-8")

    # 목록
    blog_ld = {"@context": "https://schema.org", "@type": "Blog", "name": BLOG_NAME,
               "description": BLOG_DESC, "url": BASE, "inLanguage": "ko-KR", "publisher": org,
               "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": p["url"],
                             "datePublished": p["dt"].isoformat()} for p in posts]}
    body = f"""{masthead('')}
<main class="wrap">
{nav('', '')}
{post_list(posts, '')}
<aside class="about">
<h2>쓰는 사람</h2>
<p>안녕하세요, 앱 ‘생일별 모험’을 만든 {AUTHOR}입니다. 우리 집 거실에서 해 본 생일 아이디어와 앱을 만들며 알게 된 것들을 천천히 적어 둘게요.</p>
<p>앱이 궁금하면 <a href="{APP_URL}">App Store의 생일별 모험</a>에서 볼 수 있어요.</p>
</aside>
</main>
{footer('')}"""
    (BLOG / "index.html").write_text(page(
        title=BLOG_NAME, description=BLOG_DESC, canonical=BASE, og_type="website",
        body=body, rel="", jsonld=blog_ld), encoding="utf-8")

    # 카테고리
    for name, slug in CATEGORIES.items():
        sel = [p for p in posts if p["category"] == name]
        lst = post_list(sel, "../", show_cat=False) if sel else f'<p class="empty">{CATEGORY_EMPTY}</p>'
        url = f"{BASE}category/{slug}.html"
        body = f"""{masthead('../', small=True)}
<main class="wrap">
{nav('../', name)}
<h1 class="catname">{e(name)}</h1>
{lst}
</main>
{footer('../')}"""
        ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{name} | {BLOG_NAME}",
              "url": url, "inLanguage": "ko-KR", "isPartOf": {"@type": "Blog", "name": BLOG_NAME, "url": BASE}}
        (BLOG / "category" / f"{slug}.html").write_text(page(
            title=f"{name} | {BLOG_NAME}", description=f"{BLOG_NAME}의 '{name}' 글 모음. {BLOG_DESC}",
            canonical=url, og_type="website", body=body, rel="../", jsonld=ld), encoding="utf-8")

    # RSS
    now = posts[0]["dt"] if posts else datetime.now(KST)
    items = "".join(f"""
<item>
<title>{e(p['title'])}</title>
<link>{p['url']}</link>
<guid isPermaLink="true">{p['url']}</guid>
<pubDate>{format_datetime(p['dt'])}</pubDate>
<category>{e(p['category'])}</category>
<description>{e(p['description'])}</description>
</item>""" for p in posts)
    (BLOG / "feed.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>{e(BLOG_NAME)}</title>
<link>{BASE}</link>
<atom:link href="{BASE}feed.xml" rel="self" type="application/rss+xml"/>
<description>{e(BLOG_DESC)}</description>
<language>ko</language>
<lastBuildDate>{format_datetime(now)}</lastBuildDate>{items}
</channel>
</rss>
""", encoding="utf-8")

    # sitemap (사이트 루트)
    latest = posts[0]["date"] if posts else None
    urls = [(SITE + s, None) for s in STATIC_PAGES]
    urls.append((BASE, latest))
    urls += [(f"{BASE}category/{s}.html", None) for s in CATEGORIES.values()]
    urls += [(p["url"], p["date"]) for p in posts]
    rows = "".join(f"\n<url><loc>{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>" for u, d in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}\n</urlset>\n',
        encoding="utf-8")
    print(f"글 {len(posts)}편, 카테고리 {len(CATEGORIES)}개, feed.xml, sitemap.xml 을 만들었어요.")


if __name__ == "__main__":
    build()
