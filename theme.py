# -*- coding: utf-8 -*-
# الشكل النهائي لموقع ناقد: قوائم منسدلة، واجهة أخبار متحركة، مقالة واسعة، أيقونات مشاركة، مصادر الخبر
import json, re
A = None
E = lambda s: A.esc(s)
PALS = [("#0b2a5b", "#2a6fdb", "#6db0ff"), ("#4a3600", "#d4af37", "#f6e08a"), ("#073b45", "#1fa294", "#8fe3d6"), ("#2c0f47", "#7a4cd1", "#c2a2ff")]
FILE_EXT = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".zip", ".pptx")
IC = {
 "fb": '<path d="M13.5 21v-8h2.7l.4-3.2h-3.1V7.900c0-.9.3-1.500 1.600-1.500h1.700V3.500c-.3 0-1.300-.1-2.400-.1-2.400 0-4 1.400-4 4.100v2.300H7.700V13h2.700v8z"/>',
 "x": '<path d="M17.800 3h2.900l-6.300 7.300L21.800 21h-5.800l-4.500-6-5.200 6H3.400l6.700-7.800L3 3h5.900l4.100 5.500zm-1 16.200h1.600L7.900 4.700H6.200z"/>',
 "wa": '<path d="M12 3a9 9 0 0 0-7.800 13.500L3 21l4.600-1.200A9 9 0 1 0 12 3zm0 1.700a7.300 7.300 0 1 1-3.900 13.500l-.3-.2-2.700.7.7-2.600-.2-.3A7.300 7.300 0 0 1 12 4.700zM9 8c-.3 0-.6.2-.8.500-.3.400-.9 1-.9 2.200s.9 2.400 1 2.600 1.800 2.800 4.400 3.800c2.200.8 2.600.7 3.100.6.500-.1 1.500-.6 1.700-1.200.2-.6.2-1.100.1-1.200l-.5-.3-1.600-.8c-.2-.1-.4-.1-.6.100l-.7.900c-.1.200-.3.200-.5.100-.3-.1-1.100-.4-2-1.200-.7-.7-1.200-1.500-1.400-1.800-.1-.2 0-.4.100-.5l.4-.5.2-.4v-.4L9.500 8.200C9.400 8 9.200 8 9 8z"/>',
 "tg": '<path d="M21.500 4.300 2.900 11.500c-.8.300-.8.800-.1 1l4.700 1.500 1.800 5.500c.2.600.1.800.7.800.5 0 .7-.2 1-.5l2.200-2.200 4.600 3.400c.8.500 1.500.2 1.700-.8l3-14.200c.3-1.300-.5-1.800-1.300-1.400zM8.400 13.200l9.200-5.800c.4-.3.800-.1.500.2l-7.600 6.900-.3 3.200z"/>',
 "mail": '<path d="M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm1.500 2L12 12.500 19.500 7zM4 9v8h16V9l-8 5.500z"/>',
 "link": '<path style="fill:none" d="M10 14a4 4 0 0 0 5.700 0l3-3a4 4 0 0 0-5.700-5.700l-1 1M14 10a4 4 0 0 0-5.700 0l-3 3a4 4 0 0 0 5.700 5.700l1-1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
 "print": '<path style="fill:none" d="M6 9V3h12v6M6 18H4a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1h16a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-2M7 14h10v7H7z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
 "pdf": '<path style="fill:none" d="M6 2h9l5 5v15H6z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><text x="13" y="18" font-size="6.500" text-anchor="middle" font-family="sans-serif">PDF</text>',
}
ic = lambda k: f'<svg viewBox="0 0 24 24" aria-hidden="true">{IC[k]}</svg>'

def root_of(nid):
    last = None
    while nid:
        n = A.q("SELECT id,parent_id FROM nodes WHERE id=?", (nid,), one=True)
        if not n: break
        last = n["id"]; nid = n["parent_id"]
    return last or 0

def art(seed, pal, v=0):
    s = (int(seed) * 7919 + v * 104729) % 233280 or 1
    def r():
        nonlocal s
        s = (s * 9301 + 49297) % 233280; return s / 233280
    p = PALS[pal % 4]; g = f"g{seed}_{pal % 4}_{v}"
    n = [(r() * 400, r() * 225, 2 + r() * 5) for _ in range(11)]
    l = "".join(f'<line x1="{int(a[0])}" y1="{int(a[1])}" x2="{int(b[0])}" y2="{int(b[1])}" stroke="{p[2]}" stroke-opacity=".35"/>' for i, a in enumerate(n) for b in n[i + 1:] if ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** .5 < 120)
    bars = "".join(f'<rect x="{20 + i * 16}" y="{215 - h}" width="9" height="{h}" fill="{p[2]}" opacity=".18"/>' for i in range(7) for h in [int(20 + r() * 70)])
    return (f'<svg viewBox="0 0 400 225" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><linearGradient id="{g}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{p[0]}"/><stop offset="1" stop-color="{p[1]}"/></linearGradient></defs><rect width="400" height="225" fill="url(#{g})"/>'
            f'<circle cx="{int(280 + r() * 80)}" cy="{int(40 + r() * 60)}" r="{int(60 + r() * 40)}" fill="{p[2]}" opacity=".16"/><circle cx="{int(60 + r() * 60)}" cy="{int(150 + r() * 50)}" r="{int(40 + r() * 30)}" fill="none" stroke="{p[2]}" stroke-opacity=".4" stroke-width="2"/>{bars}{l}'
            + "".join(f'<circle cx="{int(a[0])}" cy="{int(a[1])}" r="{a[2]:.1f}" fill="#fff" opacity=".85"/>' for a in n) + '<path d="M200 70l16 38-16 38-16-38z" fill="#fff" opacity=".12"/></svg>')

def cover(i, v=1):
    if i["image"]: return f'<img src="{E(i["image"])}" alt="{E(i["title"])}" loading="lazy">'
    return art(i["id"], root_of(i["node_id"]), v)

def status(i):
    if not i["deadline"]: return ""
    ok = i["deadline"] >= A.now()[:10]
    return f'<span class="st {"o" if ok else "c"}">{"مفتوحة" if ok else "مغلقة"} — آخر موعد {E(i["deadline"])}</span>'

def card(i):
    return (f'<a class="card" href="/a/{i["id"]}"><div class="cv">{cover(i)}</div><div class="cb"><span class="tag">{E(i["type"])}</span><h3>{E(i["title"])}</h3><p>{E(i["summary"])}</p>{status(i)}'
            f'<small><span>{E(i["author"])}</span><span>{E((i["pub_at"] or "")[:10])}</span></small></div></a>')

def grid(rows): return '<div class="grid">' + "".join(map(card, rows)) + "</div>" if rows else '<p class="note">لا توجد مواد هنا بعد.</p>'

def share_bar(url, title):
    from urllib.parse import quote
    u, t = quote(url, safe=""), quote(title, safe="")
    L = [("fb", "Facebook", f"https://www.facebook.com/sharer/sharer.php?u={u}"), ("x", "X", f"https://twitter.com/intent/tweet?url={u}&text={t}"), ("wa", "WhatsApp", f"https://wa.me/?text={t}%20{u}"),
         ("tg", "Telegram", f"https://t.me/share/url?url={u}&text={t}"), ("mail", "البريد الإلكتروني", f"mailto:?subject={t}&body={u}")]
    return ('<div class="share" aria-label="مشاركة">' + "".join(f'<a class="ic {k}" href="{h}" target="_blank" rel="noopener" title="{n}" aria-label="{n}">{ic(k)}</a>' for k, n, h in L)
            + f'<button class="ic" type="button" data-copy="{E(url)}" title="نسخ الرابط" aria-label="نسخ الرابط">{ic("link")}</button><button class="ic" type="button" onclick="window.print()" title="طباعة" aria-label="طباعة">{ic("print")}</button>'
            + f'<button class="ic" type="button" onclick="window.print()" title="حفظ PDF" aria-label="حفظ PDF">{ic("pdf")}</button></div>')

def sources_html(m):
    out = []
    for ln in (m.get("sources") or "").splitlines():
        ln = ln.strip()
        if not ln: continue
        t, u = ln.split("|", 1) if "|" in ln else (ln, ln if ln.startswith(("http", "/")) else "")
        t, u = t.strip(), u.strip()
        if not u: out.append(f'<li class="src"><span>{E(t)}</span></li>'); continue
        isf = u.lower().split("?")[0].endswith(FILE_EXT) or u.startswith("/uploads/")
        ext = u.startswith("http")
        out.append(f'<li><a class="src {"file" if isf else "lnk"}" href="{E(u)}" {"download" if isf and not ext else ""} {"target=_blank rel=noopener" if ext else ""}><b>{"FILE" if isf else "LINK"}</b><span>{E(t)}</span></a></li>')
    return f'<section class="srcs"><h2 class="h"><span>مصادر الخبر</span></h2><ul>{"".join(out)}</ul></section>' if out else ""

def layout(title, body, desc="", head="", s=None, plain=False, raw=False, tab=None):
    if plain:
        import admin
        return admin.shell(title, body)
    s = s or A.S()
    menu = ""
    for n in A.q("SELECT * FROM nodes WHERE parent_id IS NULL AND visible=1 ORDER BY sort,id"):
        href = "/" if n["kind"] == "home" else "/search" if n["kind"] == "search" else f"/n/{n['id']}"
        kids = A.q("SELECT * FROM nodes WHERE parent_id=? AND visible=1 ORDER BY sort,id", (n["id"],)); mm = ""
        if kids:
            cols = "".join(f'<div class="mc"><a class="mh" href="/n/{k["id"]}">{E(k["title"])}</a>' + "".join(f'<a href="/n/{g["id"]}">{E(g["title"])}</a>' for g in A.q("SELECT * FROM nodes WHERE parent_id=? AND visible=1 ORDER BY sort,id", (k["id"],))) + "</div>" for k in kids)
            mm = f'<div class="mm" style="--cols:{2 if len(kids) > 4 else 1}">{cols}</div>'
        menu += f'<div class="ti" data-id="{n["id"]}"><a href="{href}">{E(n["icon"] or "")} {E(n["title"])}{"<i class=ch></i>" if kids else ""}</a>{mm}</div>'
    logo = f'<img class="nib" src="{E(s["logo"])}" alt="">' if s["logo"] else '<svg class="nib" viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="22" fill="#0b2a5b" stroke="#d4af37" stroke-width="2"/><path d="M24 8l8 16-8 16-8-16z" fill="#fff"/><circle cx="24" cy="24" r="2.600" fill="#0b2a5b"/><path d="M24 26v12" stroke="#0b2a5b" stroke-width="1.400"/></svg>'
    tk = ""
    if not plain:
        rows = A.q(f"SELECT id,title FROM items WHERE {A.PUB} ORDER BY pub_at DESC LIMIT 10", (A.now(),))
        if rows: tk = '<div class="tk"><b>آخر الأخبار</b><div class="tkr"><div class="tkt">' + ("".join(f'<a href="/a/{r["id"]}">{E(r["title"])}</a>' for r in rows)) * 2 + "</div></div></div>"
    cols = {}
    for ln in s.get("footer_links", "").splitlines():
        p_ = ln.split("|")
        if len(p_) == 3: cols.setdefault(p_[0], []).append(f'<a href="{E(p_[2])}">{E(p_[1])}</a>')
    fcols = '<div class="cols">' + "".join(f"<div><b>{E(k)}</b>" + "".join(v) + "</div>" for k, v in cols.items()) + "</div>"
    org = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": [{"@type": "Organization", "name": s["site_name"], "alternateName": s.get("site_name_en", ""), "url": s["base_url"]}, {"@type": "WebSite", "name": s["site_name"], "url": s["base_url"], "inLanguage": "ar"}]}, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    ff = f"@font-face{{font-family:'NaqidFont';src:url('{E(s['font_url'])}')}}body,h1,h2,h3,.ui,button,label{{font-family:'NaqidFont',sans-serif!important}}" if s.get("font_url") else ""
    wrapped = body if raw else f'<div class="wrap page">{body}</div>'
    return f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)} — {E(s['site_name'])}</title><meta name="description" content="{E(desc or s['site_desc'])}"><link rel="alternate" type="application/rss+xml" href="/rss.xml">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@500;700;800&family=Noto+Naskh+Arabic:wght@400;600&display=swap"><link rel="stylesheet" href="/static/theme.css">{head}{org}
<style>:root{{--navy:{E(s['primary'])};--gold:{E(s['secondary'])}}}{ff}</style><script src="/static/theme.js" defer></script></head>
<body data-tab="{tab or ''}"><div id="pg"></div><header id="hd"><div class="wrap"><div class="bar0">{logo}<a class="bt" href="/"><b>{E(s['site_name'])}</b><small>{E(s.get('site_name_en', ''))}</small></a><nav id="tabs" aria-label="التبويبات">{menu}</nav>
<div class="tools"><button id="th" type="button" aria-label="تبديل المظهر">◐</button><button id="bg" type="button" aria-label="القائمة">☰</button></div></div></div></header>{tk}
<main>{wrapped}</main><footer><div class="wrap">{fcols}<div>{E(s['footer'])}</div></div></footer><div id="toast" role="status"></div><button id="top" type="button" aria-label="إلى الأعلى">↑</button></body></html>"""

def home(self, s):
    now = A.now(); F = list(A.q(f"SELECT * FROM items WHERE {A.PUB} AND featured=1 ORDER BY pub_at DESC LIMIT 6", (now,)))
    if len(F) < 6:
        have = {x["id"] for x in F}
        for x in A.q(f"SELECT * FROM items WHERE {A.PUB} ORDER BY pub_at DESC LIMIT 12", (now,)):
            if x["id"] not in have and len(F) < 6: F.append(x)
    cnt = lambda *t: A.q(f"SELECT COUNT(*) c FROM items WHERE type IN ({','.join('?' * len(t))}) AND {A.PUB}", (*t, now), one=True)["c"]
    slides = "".join(f'<div class="s{"" if k else " on"}"><div class="bgc">{cover(i, 1)}</div><div class="sc"><span class="tag">{E(i["type"])}</span><h2>{E(i["title"])}</h2><p>{E(i["summary"])}</p><a class="btn gold" href="/a/{i["id"]}">اقرأ المادة</a></div></div>' for k, i in enumerate(F))
    rail = "".join(f'<button type="button" class="{"" if k else "on"}" data-k="{k}"><em>{k + 1}</em>{E(i["title"])}<i></i></button>' for k, i in enumerate(F))
    hero = (f'<section class="hero" id="hero"><canvas id="cv"></canvas><div class="wrap hg"><div class="hl"><h1>{E(s["site_name"])}</h1><p>{E(s["site_desc"])}</p></div>'
            + (f'<div class="sl" id="sl">{slides}<button class="arr p" aria-label="السابق">›</button><button class="arr n" aria-label="التالي">‹</button></div><div class="rail" id="rail">{rail}</div>' if F else '<div class="note" style="grid-column:1/-1;color:#000">أضف مواد من لوحة التحكم وحدّد «مميزة» لتظهر هنا.</div>') + "</div></section>")
    stats = "".join(f'<div><b data-n="{n}">0</b>{l}</div>' for n, l in [(cnt("تحقيق"), "تحقيقات"), (cnt("قصة", "قصة بيانات", "تقرير"), "قصص وتقارير"), (cnt("فرصة", "دورة"), "فرص ودورات"), (cnt("دليل", "مورد", "ملف"), "أدلة وموارد")])
    hs = [l.split("|") for l in s.get("home_sections", "").splitlines() if l.count("|") == 2 and l.split("|")[0].strip().isdigit()]
    secs = [(A.q("SELECT * FROM nodes WHERE id=?", (int(x[0]),), one=True), int(x[1] or 3), x[2]) for x in hs] if hs else [(t, 3, t["title"]) for t in A.q("SELECT * FROM nodes WHERE parent_id IS NULL AND kind='list' AND visible=1 ORDER BY sort")]
    body = f'<div class="stats">{stats}</div>'
    for t, lim, ttl in secs:
        if not t: continue
        r = A.items_in(A.desc_ids(t["id"]), lim)
        if r: body += f'<div class="rv"><h2 class="h"><span>{E(ttl)}</span><a href="/n/{t["id"]}">عرض الكل ←</a></h2>{grid(r)}</div>'
    body += (f'<div class="cta rv"><div><h3>انضم إلى الشبكة</h3><p>أنواع عضوية ومزايا ومعايير واضحة.</p><a class="btn" href="/join">قدّم طلب عضوية</a></div><div><h3>تواصل معنا</h3><p>للشراكات والتعاون الإعلامي والاستفسارات.</p><a class="btn" href="/contact">أرسل رسالة</a></div>'
             f'<div><h3>ادعم الصحافة المستقلة</h3><p>ساهم في وصول الصحفيين إلى المعرفة والفرص والحماية.</p><a class="btn" href="{E(s.get("donate_url", "/contact"))}">تبرع</a></div></div>'
             '<p class="rv" style="margin-top:30px"><a class="btn line" href="/subscribe">اشترك في النشرة البريدية</a> <a class="btn line" href="/rss.xml">RSS</a></p>')
    self.out(layout("الرئيسية", hero + f'<div class="wrap page" style="padding-top:0">{body}</div>', s=s, raw=True, tab="home"))

def node(self, nid, s):
    n = A.q("SELECT * FROM nodes WHERE id=? AND visible=1", (nid,), one=True)
    if not n: return A.extra.nf(self, s)
    path, c = [], n
    while c:
        path.append(c); c = A.q("SELECT * FROM nodes WHERE id=?", (c["parent_id"],), one=True) if c["parent_id"] else None
    path.reverse(); rt = path[0]["id"]; ids = [p["id"] for p in path]
    kids = lambda pid: A.q("SELECT * FROM nodes WHERE parent_id=? AND visible=1 ORDER BY sort,id", (pid,))
    rows = ""
    for k, p_ in enumerate(path):
        ch = kids(p_["id"])
        if not ch: continue
        nxt = ids[k + 1] if k + 1 < len(ids) else None
        rows += (f'<div class="chips l{min(k, 2)}"><a href="/n/{p_["id"]}" class="{"on" if nxt is None else ""}">الكل</a>'
                 + "".join(f'<a href="/n/{x["id"]}" class="{"on" if x["id"] == nxt else ""}">{E(x["title"])}</a>' for x in ch) + "</div>")
    its = A.items_in(A.desc_ids(nid), 60); own = kids(nid)
    if its: content = f'<h2 class="h"><span>المواد</span></h2>{grid(its)}'
    elif own: content = '<div class="grid">' + "".join(f'<a class="card" href="/n/{x["id"]}"><div class="cb"><h3>{E(x["icon"] or "")} {E(x["title"])}</h3><p>{E(x["descr"])}</p></div></a>' for x in own) + "</div>"
    else: content = '<p class="note">لا توجد مواد في هذه النافذة بعد. ستظهر هنا فور نشرها.</p>'
    band = (f'<section class="ph"><div class="wrap"><div class="meta">{A.crumbs(nid)}</div><h1>{E(n["icon"] or "")} {E(n["title"])}</h1>' + (f'<p>{E(n["descr"])}</p>' if n["descr"] else "")
            + f'<a class="rssb" href="/rss/{nid}.xml">RSS</a></div></section>')
    self.out(layout(n["seo_title"] or n["title"], band + f'<div class="wrap page" style="padding-top:20px">{rows}{content}</div>', n["seo_desc"] or n["descr"], s=s, raw=True, tab=rt))

def article(self, iid, s):
    i = A.q(f"SELECT * FROM items WHERE id=? AND {A.PUB}", (iid, A.now()), one=True)
    if not i: return A.extra.nf(self, s)
    b = s["base_url"].rstrip("/"); url = f"{b}/a/{iid}"; m = json.loads(i["meta"] or "{}")
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": i["title"], "author": {"@type": "Person", "name": i["author"] or ""}, "datePublished": i["pub_at"], "dateModified": i["updated_at"], "publisher": {"@type": "Organization", "name": s["site_name"]}}
    if i["image"]: ld["image"] = i["image"]
    if i["type"] == "دورة": ld = {"@context": "https://schema.org", "@type": "Course", "name": i["title"], "description": i["summary"] or i["title"], "provider": {"@type": "Organization", "name": s["site_name"]}}
    head = (f'<meta property="og:title" content="{E(i["title"])}"><meta property="og:description" content="{E(i["summary"])}"><meta property="og:image" content="{E(i["image"])}"><meta property="og:type" content="article"><link rel="canonical" href="{E(url)}">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")}</script>')
    facts = "".join(f"<b>{v}</b><span>{E(m[k])}</span>" for k, v in A.META.items() if m.get(k) and k != "sources")
    if i["deadline"]: facts = f"<b>الموعد النهائي</b><span>{E(i['deadline'])}</span>" + facts
    words = len(re.sub(r"<[^>]+>", " ", i["body"] or "").split())
    rel = A.items_in([i["node_id"]] if i["node_id"] else [0], 3, f"AND id!={iid}")
    rt = root_of(i["node_id"])
    o = (f'<article class="post"><div class="pcv">{cover(i, 1)}</div><div class="pb"><div class="meta">{A.crumbs(i["node_id"])}</div><span class="tag">{E(i["type"])}</span><h1>{E(i["title"])}</h1>'
         f'<p class="sub2">{E(i["subtitle"] or i["summary"])}</p><div class="pm"><span>{E(i["author"])}</span><span>نُشر {E((i["pub_at"] or "")[:10])}</span><span>حُدّث {E((i["updated_at"] or "")[:10])}</span><span>{max(1, words // 180)} دقيقة قراءة</span></div>'
         f'<div class="ptools">{share_bar(url, i["title"])}<span><button class="chip" type="button" data-fz="-1">أ−</button><button class="chip" type="button" data-fz="1">أ+</button><button class="chip" type="button" id="rd">وضع القراءة</button></span></div>'
         + (f'<div class="facts">{facts}</div>' if facts else "") + f'<div class="body" id="body">{i["body"] or ""}</div>{sources_html(m)}'
         + (f'<a class="btn gold" href="{E(i["link"])}" rel="noopener">رابط التقديم / المصدر</a>' if i["link"] else "") + f'<div class="ptools" style="margin-top:26px">{share_bar(url, i["title"])}</div></div></article>')
    if rel: o += f'<h2 class="h" style="margin-top:40px"><span>مواد مرتبطة</span></h2>{grid(rel)}'
    self.out(layout(i["seo_title"] or i["title"], o, i["seo_desc"] or i["summary"], head, s, tab=rt))

def install():
    A.layout = layout; A.card = card; A.H.home = home; A.H.node = node; A.H.article = article

CSS = r"""
:root{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);--deep:#06172f;--blue:#2a6fdb;--sky:#6db0ff;--paper:#f2f5fb;--card:#fff;--ink:#13203b;--mute:#5a6985;--line:#d6deec;--soft:#e7eefb;--ok:#1d7a46;--bad:#b3261e;--sh:0 10px 30px -12px #0b2a5b55}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--paper:#08111f;--card:#101c33;--ink:#e8edf7;--mute:#9db0cf;--line:#243452;--soft:#16243f;--ok:#58c487;--bad:#ff8a80;--sh:0 10px 30px -12px #000a}}
:root[data-theme="dark"]{color-scheme:dark;--paper:#08111f;--card:#101c33;--ink:#e8edf7;--mute:#9db0cf;--line:#243452;--soft:#16243f;--ok:#58c487;--bad:#ff8a80;--sh:0 10px 30px -12px #000a}
html{height:100%;scroll-padding-top:calc(env(safe-area-inset-top,0px) + 70px);scroll-behavior:smooth}*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:400 1.05rem/2 "Noto Naskh Arabic",Tahoma,serif;overflow-x:hidden}
h1,h2,h3,.ui,button,label,nav a{font-family:"Noto Kufi Arabic",Tahoma,sans-serif}h1,h2,h3{line-height:1.5}a{color:inherit}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);background:var(--deep);z-index:60}
.wrap{max-width:1160px;margin:auto;padding:0 18px}.page{padding:30px 0 70px}main{min-height:60vh}
#pg{position:fixed;top:env(safe-area-inset-top,0px);right:0;height:3px;width:0;background:linear-gradient(90deg,var(--gold),var(--sky));z-index:70}
header{position:sticky;top:env(safe-area-inset-top,0px);z-index:50;background:#06172fd9;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);color:#fff;border-bottom:1px solid #ffffff1f}
.bar0{display:flex;align-items:center;gap:14px;padding:8px 0}.nib{width:46px;height:46px;flex:none;object-fit:contain;filter:drop-shadow(0 0 10px #d4af3766)}
.bt{text-decoration:none;color:#fff}.bt b{font:800 1.05rem "Noto Kufi Arabic",sans-serif;display:block;line-height:1.5}.bt small{opacity:.75;font:500 .72rem "Noto Kufi Arabic",sans-serif;direction:ltr;display:block;text-align:right}
nav{display:flex;gap:2px;margin-inline-start:auto}.ti{position:relative}
.ti>a{white-space:nowrap;display:flex;align-items:center;gap:6px;color:#dbe6fb;text-decoration:none;padding:14px;font:500 .93rem "Noto Kufi Arabic",sans-serif;position:relative}
.ti>a::after{content:"";position:absolute;inset:auto 14px 6px;height:2px;background:var(--gold);transform:scaleX(0);transition:transform .25s}.ti:hover>a::after,.ti.cur>a::after{transform:scaleX(1)}.ti:hover>a,.ti.cur>a{color:#fff}
.ch{width:7px;height:7px;border:solid currentColor;border-width:0 2px 2px 0;transform:rotate(45deg) translateY(-2px);transition:transform .2s}.ti:hover .ch,.ti.open .ch{transform:rotate(225deg)}
.mm{display:none;position:absolute;top:100%;inset-inline-start:0;min-width:270px;background:var(--card);color:var(--ink);border:1px solid var(--line);border-top:3px solid var(--gold);border-radius:0 0 10px 10px;box-shadow:var(--sh);padding:10px;gap:4px 18px;grid-template-columns:repeat(var(--cols,1),minmax(220px,1fr))}
.ti:hover .mm,.ti:focus-within .mm,.ti.open .mm{display:grid;animation:drop .22s ease-out}@keyframes drop{from{opacity:0;transform:translateY(-6px)}}
.mc{display:flex;flex-direction:column}.mm a{padding:5px 10px;border-radius:6px;color:var(--ink);text-decoration:none;font:400 .86rem "Noto Kufi Arabic",sans-serif}.mm a:hover{background:var(--soft);color:var(--blue)}.mm .mh{font-weight:700;font-size:.93rem}
.tools{display:flex;gap:8px}.tools button{background:#ffffff14;color:#fff;border:1px solid #ffffff33;border-radius:8px;width:38px;height:38px;cursor:pointer}#bg{display:none}
.tk{background:var(--gold);color:#1b1500;display:flex;align-items:center;overflow:hidden;font:500 .9rem "Noto Kufi Arabic",sans-serif}.tk b{background:#1b1500;color:var(--gold);padding:6px 16px;position:relative;z-index:2;white-space:nowrap}
.tkr{flex:1;overflow:hidden}.tkt{display:flex;width:max-content;animation:tk 60s linear infinite}.tkr:hover .tkt{animation-play-state:paused}.tkt a{padding:0 28px;text-decoration:none;white-space:nowrap}.tkt a::before{content:"◆";margin-inline-end:14px;font-size:.6rem}@keyframes tk{to{transform:translateX(50%)}}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.hero{position:relative;background:radial-gradient(1200px 500px at 85% -10%,#1b4a9c 0,transparent 60%),radial-gradient(900px 500px at 0% 110%,#0f3a7a 0,transparent 60%),var(--deep);color:#fff;overflow:hidden}.hero canvas{position:absolute;inset:0;width:100%;height:100%}
.hg{position:relative;display:grid;grid-template-columns:1fr 330px;gap:22px;padding:34px 18px 44px;align-items:stretch}.hl{grid-column:1/-1}.hl h1{font:800 clamp(1.5rem,4vw,2.5rem) "Noto Kufi Arabic",sans-serif;margin:0}.hl p{margin:4px 0 0;color:#b9cbea;max-width:62ch}
.sl{position:relative;min-height:380px;border-radius:14px;overflow:hidden;box-shadow:0 30px 60px -25px #000,0 0 0 1px #ffffff22}.sl .s{position:absolute;inset:0;opacity:0;visibility:hidden;transition:opacity .9s,visibility .9s}.sl .s.on{opacity:1;visibility:visible}
.bgc{position:absolute;inset:0;transform:scale(1.02)}.s.on .bgc{animation:kb 9s ease-out forwards}@keyframes kb{to{transform:scale(1.12)}}.bgc svg,.bgc img{width:100%;height:100%;display:block;object-fit:cover}
.sl .s::after{content:"";position:absolute;inset:0;background:linear-gradient(0deg,#06172ff2 5%,#06172f66 55%,transparent)}.sc{position:absolute;inset:auto 0 0;padding:26px 28px;z-index:2}
.sc .tag{background:var(--gold);color:#1b1500}.sc h2{font:800 clamp(1.3rem,3vw,2rem) "Noto Kufi Arabic",sans-serif;margin:8px 0;color:#fff}.sc p{margin:0 0 12px;color:#cfdcf3;max-width:56ch;line-height:1.9}
.s.on .sc>*{animation:up .7s both}.s.on .sc>*:nth-child(2){animation-delay:.1s}.s.on .sc>*:nth-child(3){animation-delay:.2s}.s.on .sc>*:nth-child(4){animation-delay:.3s}@keyframes up{from{opacity:0;transform:translateY(16px)}}
.arr{position:absolute;top:50%;z-index:3;width:40px;height:40px;border-radius:50%;border:1px solid #ffffff55;background:#06172f99;color:#fff;cursor:pointer;transform:translateY(-50%)}.arr.p{right:12px}.arr.n{left:12px}
.rail{display:flex;flex-direction:column;gap:8px}.rail button{position:relative;flex:1;text-align:right;background:#ffffff0f;border:1px solid #ffffff22;border-radius:10px;color:#cfdcf3;padding:8px 12px 12px;cursor:pointer;font:500 .84rem/1.6 "Noto Kufi Arabic",sans-serif;overflow:hidden;transition:background .25s,transform .25s}
.rail button:hover{background:#ffffff1c}.rail button.on{background:#ffffff24;color:#fff;transform:translateX(-4px)}.rail i{position:absolute;inset:auto 0 0;height:3px;background:#ffffff22}.rail i::after{content:"";position:absolute;inset:0;background:var(--gold);transform-origin:right;transform:scaleX(0)}
.rail .on i::after{animation:fill 6s linear forwards}.pz .rail .on i::after{animation-play-state:paused}@keyframes fill{to{transform:scaleX(1)}}.rail em{color:var(--gold);font-style:normal;margin-inline-end:6px}
.stats{display:flex;flex-wrap:wrap;margin:-30px 0 34px;position:relative;z-index:3;background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:var(--sh)}.stats div{flex:1 1 130px;padding:16px 20px;border-inline-start:1px solid var(--line)}.stats div:first-child{border:0}
.stats b{font:800 2.2rem "Noto Kufi Arabic",sans-serif;background:linear-gradient(135deg,var(--gold),#f3dc8a);-webkit-background-clip:text;background-clip:text;color:transparent;display:block;line-height:1.3}
h2.h{font:800 1.4rem "Noto Kufi Arabic",sans-serif;margin:34px 0 16px;display:flex;justify-content:space-between;align-items:center;color:var(--navy)}
:root[data-theme="dark"] h2.h{color:#fff}@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) h2.h{color:#fff}}
h2.h::before{content:"";width:6px;height:26px;background:linear-gradient(var(--gold),var(--blue));border-radius:3px;margin-inline-end:12px}h2.h span{flex:1}h2.h a{font:500 .85rem "Noto Kufi Arabic",sans-serif;color:var(--blue);text-decoration:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(285px,1fr));gap:20px}
.card{position:relative;display:flex;flex-direction:column;background:var(--card);border:1px solid var(--line);border-radius:12px;text-decoration:none;overflow:hidden;transition:box-shadow .3s,border-color .3s;transform:perspective(900px) rotateX(var(--rx,0)) rotateY(var(--ry,0))}.card:hover{box-shadow:var(--sh);border-color:var(--sky)}
.cv{aspect-ratio:16/9;overflow:hidden;background:var(--navy)}.cv svg,.cv img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .6s}.card:hover .cv svg,.card:hover .cv img{transform:scale(1.08)}
.cb{padding:14px 16px 16px;display:flex;flex-direction:column;gap:3px;flex:1}.card h3{margin:2px 0;font-size:1.02rem}.card p{margin:0;color:var(--mute);font-size:.93rem;line-height:1.8}.card small{display:flex;gap:14px;color:var(--mute);margin-top:auto;padding-top:8px;font-size:.82rem}
.tag{align-self:flex-start;background:var(--soft);color:var(--blue);padding:0 11px;border-radius:99px;font:700 .72rem "Noto Kufi Arabic",sans-serif;display:inline-block}.st{font:700 .78rem "Noto Kufi Arabic",sans-serif}.st.o{color:var(--ok)}.st.c{color:var(--bad)}
.rv{opacity:0;transform:translateY(22px);transition:opacity .7s,transform .7s}.rv.in{opacity:1;transform:none}
.cta{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px;margin-top:44px}.cta div{padding:24px;border-radius:14px;background:linear-gradient(145deg,var(--navy),#123d85);color:#fff;position:relative;overflow:hidden}
.cta div:nth-child(2){background:linear-gradient(145deg,#0e2f2f,#1a6b64)}.cta div:nth-child(3){background:linear-gradient(145deg,#4a1730,#a3314f)}.cta h3{margin:0 0 6px}.cta p{margin:0 0 14px;color:#dbe6fb;font-size:.95rem;line-height:1.8}.cta .btn{background:#fff;color:#0b2a5b}
.btn,.page form button,.noprint button,.page table button{display:inline-block;background:var(--navy);color:#fff;border:0;border-radius:9px;padding:9px 20px;font:500 .92rem "Noto Kufi Arabic",sans-serif;text-decoration:none;cursor:pointer;margin-inline-end:8px;transition:transform .2s,box-shadow .2s}
.btn:hover{transform:translateY(-2px);box-shadow:0 8px 18px -8px #000a}.btn.gold{background:var(--gold);color:#1b1500}.btn.line{background:transparent;color:var(--ink);border:1px solid var(--line)}
.split{display:grid;grid-template-columns:270px 1fr;gap:28px}.side{display:flex;flex-direction:column;gap:2px;align-self:start;position:sticky;top:90px}
.side a{padding:7px 14px;border-inline-start:3px solid var(--line);font:500 .93rem "Noto Kufi Arabic",sans-serif;text-decoration:none;transition:all .2s}.side a:hover{border-color:var(--sky)}.side a[aria-current]{border-color:var(--gold);background:var(--soft)}.side .sub{padding-inline-start:14px;display:flex;flex-direction:column}.side .sub a{font-weight:400;font-size:.85rem}
.ph{background:radial-gradient(900px 300px at 90% -20%,#1b4a9c 0,transparent 60%),var(--deep);color:#fff;padding:22px 0 20px;border-bottom:3px solid var(--gold)}.ph h1{font:800 clamp(1.4rem,5vw,2.3rem) "Noto Kufi Arabic",sans-serif;margin:6px 0}.ph p{color:#b9cbea;margin:0 0 10px;max-width:70ch;line-height:1.9}.ph .meta,.ph .meta a{color:#9fb7e0}
.rssb{display:inline-block;border:1px solid #ffffff44;color:#fff;border-radius:99px;padding:0 14px;font:500 .78rem "Noto Kufi Arabic",sans-serif;text-decoration:none}.rssb:hover{background:var(--gold);color:#1b1500;border-color:var(--gold)}
.chips{display:flex;gap:8px;overflow-x:auto;padding:4px 2px 10px;scrollbar-width:none;margin-bottom:4px}.chips::-webkit-scrollbar{display:none}.chips a{flex:none;white-space:nowrap;padding:4px 16px;border-radius:99px;border:1px solid var(--line);background:var(--card);text-decoration:none;font:500 .85rem "Noto Kufi Arabic",sans-serif;transition:.2s}
.chips a:hover{border-color:var(--sky)}.chips a.on{background:var(--navy);color:#fff;border-color:var(--navy)}.chips.l1 a,.chips.l2 a{font-size:.8rem;padding:3px 14px}.chips.l1 a.on,.chips.l2 a.on{background:var(--gold);color:#1b1500;border-color:var(--gold)}
@media (min-width:900px){.chips{flex-wrap:wrap;overflow:visible}}.meta{color:var(--mute);font-size:.88rem}.meta a{color:var(--blue);text-decoration:none}
/* المقالة */
.post{max-width:1080px;margin:auto;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:var(--sh)}.pcv{aspect-ratio:21/8;overflow:hidden;background:var(--navy)}.pcv svg,.pcv img{width:100%;height:100%;object-fit:cover;display:block}
.pb{padding:clamp(18px,4.5vw,56px)}.post h1{font-size:clamp(1.6rem,4vw,2.4rem);margin:8px 0}.sub2{color:var(--mute);font-size:1.15rem;margin:0 0 10px}
.pm{display:flex;flex-wrap:wrap;gap:6px 22px;color:var(--mute);font-size:.88rem;border-block:1px solid var(--line);padding:6px 0;margin:12px 0}
.ptools{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;margin:12px 0 22px}.share{display:flex;gap:8px;flex-wrap:wrap}
.ic{width:40px;height:40px;border-radius:50%;display:inline-grid;place-items:center;background:var(--soft);color:var(--ink);border:1px solid var(--line);cursor:pointer;transition:transform .2s,background .2s,color .2s;padding:0}
.ic svg{width:20px;height:20px;fill:currentColor}.ic:hover{transform:translateY(-3px);color:#fff;background:var(--navy)}.ic.fb:hover{background:#1877f2}.ic.x:hover{background:#000}.ic.wa:hover{background:#25d366}.ic.tg:hover{background:#229ed9}.ic.mail:hover{background:#c0392b}
.chip{background:var(--soft);color:var(--ink);border:1px solid var(--line);border-radius:99px;padding:3px 14px;cursor:pointer;font:500 .8rem "Noto Kufi Arabic",sans-serif;margin-inline-start:6px}
.facts{display:grid;grid-template-columns:auto 1fr;gap:2px 18px;background:var(--soft);padding:14px 18px;border-radius:10px;margin:14px 0;border-inline-start:4px solid var(--gold)}.facts b{font:500 .88rem "Noto Kufi Arabic",sans-serif}
.body{font-size:1.16rem;line-height:2.15}.body p{margin:0 0 1.15em}.body h2{font:800 1.5rem "Noto Kufi Arabic",sans-serif;margin:1.8em 0 .6em;color:var(--navy);border-inline-start:5px solid var(--gold);padding-inline-start:12px}.body h3{font:700 1.2rem "Noto Kufi Arabic",sans-serif;margin:1.5em 0 .5em}
:root[data-theme="dark"] .body h2{color:#fff}@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .body h2{color:#fff}}
.body img,.body video,.body iframe{max-width:100%;height:auto;border-radius:10px}.body figure{margin:1.6em auto;text-align:center;max-width:100%}.body figure.mid{max-width:70%}.body figure.sm{max-width:40%}.body figure.start{float:right;margin:.3em 0 1em 1.4em}.body figure.end{float:left;margin:.3em 1.4em 1em 0}
.body figcaption{color:var(--mute);font-size:.88rem;margin-top:6px}.body blockquote{margin:1.5em 0;padding:8px 20px;border-inline-start:4px solid var(--gold);background:var(--soft);border-radius:0 10px 10px 0;font-size:1.2rem}.body table{display:block;overflow-x:auto;border-collapse:collapse}.body td,.body th{border:1px solid var(--line);padding:6px 10px}
.body img{cursor:zoom-in}.body a{color:var(--blue)}.body::after{content:"";display:block;clear:both}
.filecard,.src{display:inline-flex;align-items:center;gap:12px;background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:8px 14px;color:var(--ink);text-decoration:none;font:500 .9rem "Noto Kufi Arabic",sans-serif;margin:4px 0}.filecard::before{content:"FILE";background:var(--blue);color:#fff;border-radius:6px;font-size:.65rem;padding:2px 6px}.filecard:hover,.src:hover{border-color:var(--gold)}
.srcs ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}.src{display:flex;margin:0}.src b{background:var(--blue);color:#fff;border-radius:6px;font-size:.65rem;padding:2px 8px}.src.lnk b{background:var(--gold);color:#1b1500}
.toc{position:fixed;top:110px;inset-inline-start:max(12px,calc((100vw - 1080px)/2 - 230px));width:210px;font:500 .82rem/1.7 "Noto Kufi Arabic",sans-serif;display:none}.toc a{display:block;padding:3px 10px;border-inline-start:2px solid var(--line);text-decoration:none;color:var(--mute)}.toc a.on{border-color:var(--gold);color:var(--ink)}@media (min-width:1500px){.toc.on{display:block}}
.reading header,.reading .tk,.reading footer{display:none}.reading .post{max-width:860px;border:0;box-shadow:none;background:transparent}.reading .pcv{display:none}.reading .body{font-size:1.28rem}
.lb{position:fixed;inset:0;background:#030b18ee;z-index:100;display:none;place-items:center;padding:20px}.lb.on{display:grid}.lb img{max-width:92vw;max-height:84vh;border-radius:10px}.lb button{position:absolute;background:#ffffff22;color:#fff;border:0;width:44px;height:44px;border-radius:50%;cursor:pointer;font-size:1.2rem}.lb .x{top:20px;left:20px}.lb .a{top:50%;right:20px}.lb .b{top:50%;left:20px}.lb p{position:absolute;bottom:18px;color:#cfdcf3;margin:0}
form{display:grid;gap:4px;max-width:900px}label{font:500 .9rem "Noto Kufi Arabic",sans-serif;margin-top:8px}input,select,textarea{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink);font:inherit}input[type=checkbox]{width:auto}
.filters{display:grid;grid-template-columns:2fr 1fr 1fr;gap:10px;margin-bottom:18px}.note{background:var(--soft);padding:10px 14px;border-radius:9px;color:var(--mute)}
.art{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:clamp(18px,3vw,36px);max-width:900px}table{width:100%;border-collapse:collapse;background:var(--card)}td,th{border:1px solid var(--line);padding:6px;text-align:right}
#toast{position:fixed;bottom:24px;inset-inline:0;margin:auto;width:max-content;max-width:90vw;background:var(--deep);color:#fff;padding:10px 20px;border-radius:99px;border:1px solid var(--gold);font:500 .88rem "Noto Kufi Arabic",sans-serif;z-index:120;opacity:0;transform:translateY(20px);transition:.3s;pointer-events:none}#toast.on{opacity:1;transform:none}
#top{position:fixed;bottom:22px;left:22px;width:44px;height:44px;border-radius:50%;border:0;background:var(--gold);color:#1b1500;cursor:pointer;opacity:0;pointer-events:none;transition:.3s;z-index:40}#top.on{opacity:1;pointer-events:auto}
footer{background:var(--deep);color:#c4d3ee;padding:34px 0 22px;border-top:3px solid var(--gold)}footer .cols{display:flex;flex-wrap:wrap;gap:30px 70px;margin-bottom:18px}footer b{font-family:"Noto Kufi Arabic",sans-serif;color:var(--gold);display:block}footer a{display:block;text-decoration:none;font-size:.93rem}footer a:hover{color:#fff}
@media (max-width:900px){.hg{grid-template-columns:1fr}.rail{flex-direction:row;overflow-x:auto}.rail button{min-width:190px}.sl{min-height:340px}.split{grid-template-columns:1fr}.side{position:static}.filters{grid-template-columns:1fr}.body figure.mid,.body figure.sm{max-width:100%}.body figure.start,.body figure.end{float:none;margin:1em auto}}
@media (max-width:1100px){.bt b{font-size:.84rem;line-height:1.5}.bt small{display:none}.nib{width:36px;height:36px}.bar0{gap:10px;padding:6px 0}#bg{display:block}.tools{margin-inline-start:auto}nav{display:none;position:absolute;top:100%;inset-inline:0;flex-direction:column;background:#06172ff7;padding:6px 18px 14px;max-height:75vh;overflow:auto}.menu-open nav{display:flex}
 .mm{position:static;display:none;border:0;box-shadow:none;background:#ffffff0d;color:#fff;border-radius:8px;grid-template-columns:1fr!important}.mm a{color:#dbe6fb}.ti:hover .mm{display:none}.ti.open .mm{display:grid}}
@media print{header,footer,.tk,.ptools,.side,#top,#pg,.toc,body::before{display:none!important}body{background:#fff;color:#000}.post{border:0;box-shadow:none}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.rv{opacity:1;transform:none}}
"""

JS = r"""
(function(){var $=function(s,r){return(r||document).querySelector(s)},$$=function(s,r){return[].slice.call((r||document).querySelectorAll(s))};
function toast(m){var t=$('#toast');t.textContent=m;t.classList.add('on');clearTimeout(toast.t);toast.t=setTimeout(function(){t.classList.remove('on')},2400)}
var tab=document.body.dataset.tab;$$('.ti').forEach(function(t){if(t.dataset.id===tab||(tab==='home'&&t.firstChild.getAttribute('href')==='/'))t.classList.add('cur');
 t.firstChild.addEventListener('click',function(e){if(innerWidth<=1100&&$('.mm',t)){e.preventDefault();$$('.ti.open').forEach(function(x){x!==t&&x.classList.remove('open')});t.classList.toggle('open')}})});
$('#bg').onclick=function(){$('#hd').classList.toggle('menu-open')};
$('#th').onclick=function(){var d=document.documentElement,dk=d.dataset.theme?d.dataset.theme==='dark':matchMedia('(prefers-color-scheme:dark)').matches;d.dataset.theme=dk?'light':'dark'};
$('#top').onclick=function(){scrollTo({top:0})};
var pg=$('#pg');addEventListener('scroll',function(){$('#top').classList.toggle('on',scrollY>600);if($('#body')){var h=document.documentElement;pg.style.width=(scrollY/(h.scrollHeight-innerHeight)*100||0)+'%'}});
if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.08});$$('.rv').forEach(function(r){io.observe(r)})}else $$('.rv').forEach(function(r){r.classList.add('in')});
$$('[data-n]').forEach(function(b){var n=+b.dataset.n,k=0,t=setInterval(function(){k++;b.textContent=Math.round(n*k/24);if(k>=24)clearInterval(t)},30)});
$$('.card').forEach(function(c){c.addEventListener('pointermove',function(e){if(e.pointerType!=='mouse')return;var b=c.getBoundingClientRect();c.style.setProperty('--ry',((e.clientX-b.left)/b.width-.5)*6+'deg');c.style.setProperty('--rx',(.5-(e.clientY-b.top)/b.height)*6+'deg')});c.addEventListener('pointerleave',function(){c.style.setProperty('--rx','0deg');c.style.setProperty('--ry','0deg')})});
$$('[data-copy]').forEach(function(b){b.onclick=function(){try{navigator.clipboard.writeText(b.dataset.copy);toast('نُسخ الرابط')}catch(e){toast('انسخ الرابط من شريط العنوان')}}});
/* الواجهة */
var sl=$('#sl');if(sl){var S=$$('.s',sl),R=$$('#rail button'),H=$('#hero'),k=0,t;
 function go(n){k=(n+S.length)%S.length;S.forEach(function(s,i){s.classList.toggle('on',i===k)});R.forEach(function(b,i){b.classList.remove('on');void b.offsetWidth;b.classList.toggle('on',i===k)});clearTimeout(t);t=setTimeout(function(){go(k+1)},6000)}
 R.forEach(function(b){b.onclick=function(){go(+b.dataset.k)}});$('.arr.p').onclick=function(){go(k-1)};$('.arr.n').onclick=function(){go(k+1)};
 H.onmouseenter=function(){clearTimeout(t);H.classList.add('pz')};H.onmouseleave=function(){H.classList.remove('pz');go(k)};go(0)}
var cv=$('#cv');if(cv){var x=cv.getContext('2d'),m={x:-999,y:-999},rm=matchMedia('(prefers-reduced-motion:reduce)').matches,W,Hh,P;
 function rs(){var d=devicePixelRatio||1,b=cv.getBoundingClientRect();W=b.width;Hh=b.height;cv.width=W*d;cv.height=Hh*d;x.setTransform(d,0,0,d,0,0);P=[];for(var i=0;i<Math.round(W*Hh/15000);i++)P.push({x:Math.random()*W,y:Math.random()*Hh,vx:(Math.random()-.5)*.35,vy:(Math.random()-.5)*.35})}
 function f(){x.clearRect(0,0,W,Hh);P.forEach(function(p){p.x+=p.vx;p.y+=p.vy;if(p.x<0||p.x>W)p.vx*=-1;if(p.y<0||p.y>Hh)p.vy*=-1;var dx=p.x-m.x,dy=p.y-m.y;if(dx*dx+dy*dy<16000){p.x+=dx*.01;p.y+=dy*.01}});
  for(var i=0;i<P.length;i++){for(var j=i+1;j<P.length;j++){var d=Math.hypot(P[i].x-P[j].x,P[i].y-P[j].y);if(d<130){x.strokeStyle='rgba(109,176,255,'+.28*(1-d/130)+')';x.beginPath();x.moveTo(P[i].x,P[i].y);x.lineTo(P[j].x,P[j].y);x.stroke()}}x.fillStyle='rgba(212,175,55,.85)';x.beginPath();x.arc(P[i].x,P[i].y,1.8,0,7);x.fill()}
  if(!rm)requestAnimationFrame(f)}
 rs();f();addEventListener('resize',rs);$('#hero').addEventListener('pointermove',function(e){var b=cv.getBoundingClientRect();m.x=e.clientX-b.left;m.y=e.clientY-b.top})}
/* المقالة */
var body=$('#body');if(body){var fs=0;$$('[data-fz]').forEach(function(b){b.onclick=function(){fs=Math.max(-3,Math.min(5,fs+ +b.dataset.fz));body.style.fontSize=(18.5+fs*2)+'px'}});
 $('#rd').onclick=function(){document.body.classList.toggle('reading')};
 var hs=$$('h2,h3',body);if(hs.length>=3){var tc=document.createElement('aside');tc.className='toc on';tc.innerHTML=hs.map(function(h,i){h.id='h'+i;return'<a href="#h'+i+'">'+h.textContent+'</a>'}).join('');document.body.appendChild(tc);
  addEventListener('scroll',function(){var c=0;hs.forEach(function(h,i){if(h.getBoundingClientRect().top<160)c=i});$$('a',tc).forEach(function(a,i){a.classList.toggle('on',i===c)})})}
 var im=$$('img',body);if(im.length){var lb=document.createElement('div');lb.className='lb';lb.innerHTML='<button class="x" aria-label="إغلاق">✕</button><button class="a">›</button><button class="b">‹</button><img alt=""><p></p>';document.body.appendChild(lb);var c=0;
  function sh(n){c=(n+im.length)%im.length;$('img',lb).src=im[c].src;$('p',lb).textContent=(im[c].alt||'')+' '+(c+1)+'/'+im.length}
  im.forEach(function(g,i){g.onclick=function(){sh(i);lb.classList.add('on')}});$('.x',lb).onclick=function(){lb.classList.remove('on')};$('.a',lb).onclick=function(){sh(c-1)};$('.b',lb).onclick=function(){sh(c+1)};lb.onclick=function(e){if(e.target===lb)lb.classList.remove('on')};
  addEventListener('keydown',function(e){if(!lb.classList.contains('on'))return;if(e.key==='Escape')lb.classList.remove('on');if(e.key==='ArrowRight')sh(c-1);if(e.key==='ArrowLeft')sh(c+1)})}}
})();
"""
