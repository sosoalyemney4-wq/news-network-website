#!/usr/bin/env python3
# شبكة الصحفيين المستقلين في اليمن — نواة CMS (بايثون فقط + SQLite، بلا تبعيات)
import sys, extra, theme, sqlite3, os, html, json, secrets, hashlib, hmac, time, re
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from email.utils import format_datetime

DB = os.environ.get("YJN_DB", "yjn.db")
PORT = int(os.environ.get("PORT", 8000))
SESS = {}
esc = lambda s: html.escape(str(s if s is not None else ""), quote=True)
now = lambda: datetime.now().strftime("%Y-%m-%d %H:%M")

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def q(sql, a=(), one=False, commit=False):
    c = db(); cur = c.execute(sql, a)
    r = cur.fetchone() if one else cur.fetchall()
    if commit: c.commit()
    lid = cur.lastrowid; c.close()
    return lid if commit else r

def hp(pw, salt=None):
    salt = salt or secrets.token_hex(8)
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 150000).hex()

def init():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT);
    CREATE TABLE IF NOT EXISTS nodes(id INTEGER PRIMARY KEY, parent_id INTEGER, title TEXT, kind TEXT DEFAULT 'list',
      icon TEXT, descr TEXT, image TEXT, sort INTEGER DEFAULT 0, visible INTEGER DEFAULT 1, seo_title TEXT, seo_desc TEXT);
    CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY, node_id INTEGER, type TEXT DEFAULT 'مقال', title TEXT, subtitle TEXT,
      summary TEXT, body TEXT, author TEXT, image TEXT, link TEXT, deadline TEXT, status TEXT DEFAULT 'draft',
      pub_at TEXT, updated_at TEXT, featured INTEGER DEFAULT 0, seo_title TEXT, seo_desc TEXT);
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT UNIQUE, pw TEXT, role TEXT DEFAULT 'admin');
    CREATE TABLE IF NOT EXISTS forms(id INTEGER PRIMARY KEY, kind TEXT, name TEXT, email TEXT, subject TEXT, message TEXT, status TEXT DEFAULT 'new', created TEXT);
    """)
    try: c.execute("ALTER TABLE items ADD COLUMN meta TEXT DEFAULT '{}'")
    except sqlite3.OperationalError: pass
    if not c.execute("SELECT 1 FROM settings").fetchone():
        d = dict(site_name="شبكة الصحفيين المستقلين في اليمن - ناقد", site_desc="منصة للصحافة المستقلة والحماية المهنية والفرص والموارد",
                 primary="#0b2a5b", secondary="#c9a227", bg="#f5f7fb", text="#1b2433", font="Tahoma, 'Segoe UI', sans-serif",
                 logo="", footer="جميع الحقوق محفوظة © شبكة الصحفيين المستقلين في اليمن", contact_email="",
                 robots="User-agent: *\nDisallow: /admin\nDisallow: /search\nAllow: /", base_url="", donate_url="/contact", footer_links=FL)
        c.executemany("INSERT INTO settings VALUES(?,?)", d.items())
        L = lambda *x: {i: {} for i in x}
        T = {"الرئيسية": ("home", {}),
         "الصحافة": ("list", {"التحقيقات الاستقصائية": L("التحقيقات المحلية", "التحقيقات الإقليمية", "التحقيقات الدولية", "التحقيقات المنشورة بالشراكة"), "التقارير والقصص": {}, "قصص البيانات": {}, "التحقيقات المشتركة": {}, "الصحافة متعددة الوسائط": {}}),
         "الفرص": ("list", {"المنح وتمويل المشاريع": L("منح الصحافة", "منح التحقيقات", "منح المشاريع الإعلامية", "منح المؤسسات", "منح الأفراد"), "الزمالات": {}, "الوظائف": L("وظائف الصحفيين", "وظائف المؤسسات الإعلامية", "وظائف العمل عن بعد", "فرص التعاقد"), "التدريبات والدورات": L("تدريب حضوري", "تدريب عن بعد", "دورات", "ورش عمل", "برامج تدريبية طويلة")}),
         "الموارد": ("list", {"الصحافة والتحقيق": L("أساسيات الصحافة", "الصحافة المستقلة", "الصحافة الاستقصائية", "صحافة الحلول", "حرية الصحافة"), "الصحافة الرقمية والإعلام الجديد": L("الصحافة الرقمية", "الصحافة متعددة الوسائط", "صحافة الموبايل", "الإعلام الاجتماعي", "الابتكارات الإعلامية"), "الذكاء الاصطناعي للصحفيين": L("أدوات الذكاء الاصطناعي", "البحث والتحليل", "التحقق", "الإنتاج الصحفي", "أخلاقيات استخدام الذكاء الاصطناعي"), "البيانات والتحقق ومكافحة التضليل": L("صحافة البيانات", "التحقق من المعلومات", "التحقق من الصور والفيديو", "مكافحة التضليل", "المعلومات المضللة والخاطئة"), "السلامة والحماية": L("السلامة الرقمية", "السلامة الجسدية", "السلامة الميدانية", "حماية المصادر", "أمن الاتصالات والبيانات")}),
         "الحماية والشبكة": ("list", {"السلامة المهنية": L("تقييم المخاطر", "خطط السلامة", "العمل في مناطق النزاع", "السلامة أثناء التغطية", "إدارة المخاطر المهنية"), "السلامة الرقمية والميدانية": L("حماية الحسابات", "حماية الأجهزة", "الاتصالات الآمنة", "حماية المصادر", "إجراءات العمل الميداني"), "الدعم القانوني": L("الحقوق القانونية للصحفيين", "الوصول إلى المعلومات", "التعامل مع الاستدعاءات", "الحماية القانونية", "الأدلة القانونية"), "انتهاكات الصحفيين": L("رصد الانتهاكات", "قاعدة بيانات الانتهاكات", "التقارير", "الحالات الموثقة", "الإحصاءات"), "بيانات ومواقف الشبكة": L("البيانات الصحفية", "المواقف", "المناشدات", "بيانات التضامن", "الأخبار المؤسسية"), "من نحن": L("من نحن", "الرؤية", "الرسالة", "الأهداف", "المبادئ والقيم", "العضوية", "الهيكل التنظيمي", "الشركاء", "فريق الشبكة", "تواصل معنا")}),
         "البحث": ("search", {})}
        def add(pid, d):
            for j, (t, ch) in enumerate(d.items()):
                add(c.execute("INSERT INTO nodes(parent_id,title,sort) VALUES(?,?,?)", (pid, t, j)).lastrowid, ch)
        for i, (t, (k, ch)) in enumerate(T.items()):
            add(c.execute("INSERT INTO nodes(title,kind,sort) VALUES(?,?,?)", (t, k, i)).lastrowid, ch)
        gen = not os.environ.get("YJN_ADMIN_PASSWORD"); pw = os.environ.get("YJN_ADMIN_PASSWORD") or secrets.token_urlsafe(9)
        c.execute("INSERT INTO users(name,pw) VALUES('admin',?)", (hp(pw),))
        print(f"\n>>> حساب المدير: admin  كلمة المرور: {pw if gen else '(من YJN_ADMIN_PASSWORD)'}  (غيّرها بعد الدخول)\n", flush=True)
    c.commit(); c.close()

def S(): return {r["k"]: r["v"] for r in q("SELECT * FROM settings")}
META = {"entity": "الجهة", "scope": "النطاق الجغرافي / الدولة", "eligibility": "الأهلية", "funding": "قيمة التمويل", "lang": "اللغة", "region": "المحافظة / المنطقة", "sources": "مصادر الخبر"}
FL = "الشبكة|من نحن|/search\nالشبكة|انضم إلينا|/join\nالشبكة|اتصل بنا|/contact\nالمحتوى|البحث|/search\nالمحتوى|RSS|/rss.xml\nالدعم|تبرع لدعم الصحافة المستقلة|/contact\nالدعم|النشرة البريدية|/subscribe\nقانوني|خريطة الموقع|/sitemap.xml"
PUB = "status IN ('published','scheduled') AND pub_at<=?"

def desc_ids(nid):
    ids, st = [nid], [nid]
    while st:
        for r in q("SELECT id FROM nodes WHERE parent_id=?", (st.pop(),)): ids.append(r["id"]); st.append(r["id"])
    return ids

def layout(title, body, desc="", head="", s=None):
    s = s or S()
    tabs = "".join(f'<a href="{"/" if n["kind"]=="home" else "/search" if n["kind"]=="search" else "/n/%d" % n["id"]}">{esc(n["icon"] or "")} {esc(n["title"])}</a>'
                   for n in q("SELECT * FROM nodes WHERE parent_id IS NULL AND visible=1 ORDER BY sort,id"))
    ff = ("'NaqidFont'," if s.get("font_url") else "") + s["font"]
    fontface = f"@font-face{{font-family:'NaqidFont';src:url('{esc(s['font_url'])}')}}" if s.get("font_url") else ""
    org = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": [{"@type": "Organization", "name": s["site_name"], "alternateName": s.get("site_name_en", ""), "url": s["base_url"]}, {"@type": "WebSite", "name": s["site_name"], "url": s["base_url"], "inLanguage": "ar"}]}, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    cols = {}
    for ln in s.get("footer_links", "").splitlines():
        p_ = ln.split("|")
        if len(p_) == 3: cols.setdefault(p_[0], []).append(f'<a href="{esc(p_[2])}" style="color:#fff">{esc(p_[1])}</a>')
    fcols = '<div style="display:flex;gap:30px;justify-content:center;flex-wrap:wrap;text-align:right">' + "".join(f"<div><b style='color:var(--s)'>{esc(k)}</b><br>" + "<br>".join(v) + "</div>" for k, v in cols.items()) + "</div><hr>"
    logo = f'<img src="{esc(s["logo"])}" height="40" alt="">' if s["logo"] else ""
    return f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — {esc(s['site_name'])}</title><meta name="description" content="{esc(desc or s['site_desc'])}">
<link rel="alternate" type="application/rss+xml" href="/rss.xml">{head}{org}
<style>{fontface}:root{{--p:{esc(s['primary'])};--s:{esc(s['secondary'])};--bg:{esc(s['bg'])};--t:{esc(s['text'])}}}
*{{box-sizing:border-box}}body{{margin:0;font-family:{esc(ff)};background:var(--bg);color:var(--t);line-height:1.9}}
a{{color:var(--p)}}header{{background:var(--p);color:#fff}}header .in{{max-width:1100px;margin:auto;padding:12px 16px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}}
header b{{font-size:1.2rem}}nav{{display:flex;gap:4px;flex-wrap:wrap}}nav a{{color:#fff;text-decoration:none;padding:6px 12px;border-radius:6px}}nav a:hover{{background:rgba(255,255,255,.15);border-bottom:2px solid var(--s)}}
main{{max-width:1100px;margin:20px auto;padding:0 16px}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}}
.card{{background:#fff;border-radius:10px;padding:14px;box-shadow:0 1px 4px #0002;border-top:3px solid var(--s)}}.card img{{width:100%;height:150px;object-fit:cover;border-radius:6px}}
.btn,button{{background:var(--p);color:#fff;border:0;padding:8px 16px;border-radius:6px;cursor:pointer;text-decoration:none;display:inline-block;font:inherit}}
input,select,textarea{{width:100%;padding:8px;border:1px solid #bbc;border-radius:6px;font:inherit;margin:4px 0 10px}}label{{font-weight:bold}}
h1,h2{{color:var(--p)}}footer{{background:var(--p);color:#fff;text-align:center;padding:18px;margin-top:40px}}.meta{{color:#667;font-size:.9rem}}
table{{width:100%;border-collapse:collapse;background:#fff}}td,th{{border:1px solid #dde;padding:6px;text-align:right}}.art{{background:#fff;padding:24px;border-radius:10px}}.art img{{max-width:100%}}
@media print{{header,footer,.noprint{{display:none}}body{{background:#fff}}.art{{box-shadow:none;padding:0}}}}</style></head>
<body><header><div class="in">{logo}<div><b>{esc(s['site_name'])}</b><br><small style='opacity:.8'>{esc(s.get('site_name_en',''))}</small></div><nav>{tabs}</nav></div></header><main>{body}</main><footer>{fcols}<div>{esc(s['footer'])}</div></footer></body></html>"""

def card(i):
    img = f'<img src="{esc(i["image"])}" alt="{esc(i["title"])}">' if i["image"] else ""
    dl = f'<div class="meta">آخر موعد: {esc(i["deadline"])}</div>' if i["deadline"] else ""
    return f'<div class="card">{img}<div class="meta">{esc(i["type"])} · {esc((i["pub_at"] or "")[:10])}</div><h3><a href="/a/{i["id"]}">{esc(i["title"])}</a></h3><p>{esc(i["summary"])}</p>{dl}<div class="meta">{esc(i["author"])}</div><a href="/a/{i["id"]}">قراءة المادة ←</a></div>'

def items_in(ids, limit=30, extra=""):
    ph = ",".join("?" * len(ids))
    return q(f"SELECT * FROM items WHERE node_id IN ({ph}) AND {PUB} {extra} ORDER BY pub_at DESC LIMIT {int(limit)}", (*ids, now()))

def crumbs(nid):
    out = []
    while nid:
        n = q("SELECT * FROM nodes WHERE id=?", (nid,), one=True)
        if not n: break
        out.append(f'<a href="/n/{n["id"]}">{esc(n["title"])}</a>'); nid = n["parent_id"]
    return " ‹ ".join(reversed(out))

def rss(title, link, rows, s):
    base = s["base_url"].rstrip("/")
    it = "".join(f"<item><title>{esc(r['title'])}</title><link>{base}/a/{r['id']}</link><guid>{base}/a/{r['id']}</guid><description>{esc(r['summary'])}</description><pubDate>{format_datetime(datetime.strptime(r['pub_at'],'%Y-%m-%d %H:%M'))}</pubDate></item>" for r in rows)
    return f'<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>{esc(title)}</title><link>{base}/</link><description>{esc(s["site_desc"])}</description><language>ar</language>{it}</channel></rss>'

class H(BaseHTTPRequestHandler):
    def out(self, body, ct="text/html; charset=utf-8", code=200, hdr=()):
        b = body if isinstance(body, bytes) else body.encode(); self.send_response(code); self.send_header("Content-Type", ct)
        for h in hdr: self.send_header(*h)
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def go(self, to, hdr=()): self.out("", code=303, hdr=[("Location", to), *hdr])
    def user(self):
        ck = self.headers.get("Cookie", ""); m = re.search(r"sid=([\w-]+)", ck)
        return SESS.get(m.group(1)) if m else None
    def do_HEAD(self):
        self.send_response(200); self.send_header("Content-Length", "0"); self.end_headers()
    def log_message(self, *a): pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); raw = self.rfile.read(n); ct = self.headers.get("Content-Type", ""); self.files = []
        f = extra.parse_multipart(self, raw, ct) if ct.startswith("multipart/") else {k: v[0] for k, v in parse_qs(raw.decode(), keep_blank_values=True).items()}
        p = urlparse(self.path).path
        if extra.post(self, p, f): return
        if p == "/admin/login":
            u = q("SELECT * FROM users WHERE name=?", (f.get("name", ""),), one=True)
            if u and hmac.compare_digest(hp(f.get("pw", ""), u["pw"].split("$")[0]), u["pw"]):
                t = secrets.token_hex(16); SESS[t] = u["id"]
                return self.go("/admin", [("Set-Cookie", f"sid={t}; HttpOnly; SameSite=Strict; Path=/" + ("; Secure" if S()["base_url"].startswith("https") else ""))])
            return self.out(layout("دخول", "<p>بيانات غير صحيحة</p><a href='/admin'>رجوع</a>", plain=True), code=401)
        if p in ("/join", "/contact"):
            if f.get("website"): return self.go("/")  # honeypot ضد الرسائل الآلية
            q("INSERT INTO forms(kind,name,email,subject,message,created) VALUES(?,?,?,?,?,?)", (p[1:], f.get("name"), f.get("email"), f.get("subject"), f.get("message"), now()), commit=True)
            return self.out(layout("تم", "<div class='art'><h2>شكراً لك، تم استلام رسالتك.</h2></div>"))
        if not self.user(): return self.go("/admin")
        if p == "/admin/node":
            v = (f.get("parent_id") or None, f["title"], f["kind"], f["icon"], f["descr"], f["image"], int(f.get("sort") or 0), int(f.get("visible") == "1"), f["seo_title"], f["seo_desc"])
            if f.get("id"): q("UPDATE nodes SET parent_id=?,title=?,kind=?,icon=?,descr=?,image=?,sort=?,visible=?,seo_title=?,seo_desc=? WHERE id=?", (*v, f["id"]), commit=True)
            else: q("INSERT INTO nodes(parent_id,title,kind,icon,descr,image,sort,visible,seo_title,seo_desc) VALUES(?,?,?,?,?,?,?,?,?,?)", v, commit=True)
            return self.go("/admin/nodes")
        if p == "/admin/node/del":
            if not q("SELECT 1 FROM nodes WHERE parent_id=?", (f["id"],), one=True):
                q("UPDATE items SET node_id=NULL WHERE node_id=?", (f["id"],), commit=True); q("DELETE FROM nodes WHERE id=?", (f["id"],), commit=True)
            return self.go("/admin/nodes")
        if p == "/admin/item":
            pub = (f.get("pub_at") or now()).replace("T", " ")[:16]
            v = (f.get("node_id") or None, f["type"], f["title"], f["subtitle"], f["summary"], f["body"], f["author"], f["image"], f["link"], f["deadline"], f["status"], pub, now(), int(f.get("featured") == "1"), f["seo_title"], f["seo_desc"], json.dumps({k: f.get(k, "") for k in META}, ensure_ascii=False))
            c = "node_id=?,type=?,title=?,subtitle=?,summary=?,body=?,author=?,image=?,link=?,deadline=?,status=?,pub_at=?,updated_at=?,featured=?,seo_title=?,seo_desc=?,meta=?"
            if f.get("id"): q(f"UPDATE items SET {c} WHERE id=?", (*v, f["id"]), commit=True)
            else: q("INSERT INTO items(node_id,type,title,subtitle,summary,body,author,image,link,deadline,status,pub_at,updated_at,featured,seo_title,seo_desc,meta) VALUES(" + ",".join("?" * 17) + ")", v, commit=True)
            return self.go("/admin/items")
        if p == "/admin/item/del": q("DELETE FROM items WHERE id=?", (f["id"],), commit=True); return self.go("/admin/items")
        if p == "/admin/settings":
            for k in S():
                if k in f: q("UPDATE settings SET v=? WHERE k=?", (f[k], k), commit=True)
            return self.go("/admin/settings")
        if p == "/admin/form/status": q("UPDATE forms SET status=? WHERE id=?", (f["status"], f["id"]), commit=True); return self.go("/admin/forms")
        self.out("404", code=404)

    def do_GET(self):
        u = urlparse(self.path); p = u.path; a = {k: v[0] for k, v in parse_qs(u.query).items()}; s = S()
        if extra.get(self, p, a, s): return
        if p == "/": return self.home(s)
        if p.startswith("/n/"): return self.node(int(p[3:]), s)
        if p.startswith("/a/"): return self.article(int(p[3:]), s)
        if p == "/search": return self.search(a, s)
        if p in ("/join", "/contact"):
            ex = "<label>نوع العضوية / الموضوع</label><input name='subject'>"
            return self.out(layout("انضم" if p == "/join" else "تواصل", f"<div class='art'><h1>{'طلب العضوية' if p=='/join' else 'تواصل معنا'}</h1><form method='post'><label>الاسم</label><input name='name' required><label>البريد</label><input type='email' name='email' required>{ex}<label>الرسالة / نبذة</label><textarea name='message' rows='6' required></textarea><input name='website' style='display:none' tabindex='-1' autocomplete='off'><button>إرسال</button></form></div>", s=s))
        if p == "/rss.xml" or re.match(r"/rss/\d+\.xml", p):
            ids = desc_ids(int(re.findall(r"\d+", p)[0])) if p != "/rss.xml" else [r["id"] for r in q("SELECT id FROM nodes")]
            return self.out(rss(s["site_name"], "/", items_in(ids, 30), s), "application/rss+xml; charset=utf-8")
        if p == "/sitemap.xml":
            b = s["base_url"].rstrip("/")
            urls = [f"{b}/"] + [f"{b}/n/{r['id']}" for r in q("SELECT id FROM nodes WHERE visible=1")] + [f"{b}/a/{r['id']}" for r in q(f"SELECT id FROM items WHERE {PUB}", (now(),))]
            return self.out('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{esc(x)}</loc></url>" for x in urls) + "</urlset>", "application/xml")
        if p == "/robots.txt": return self.out(s["robots"] + f"\nSitemap: {s['base_url'].rstrip('/')}/sitemap.xml\n", "text/plain; charset=utf-8")
        if p.startswith("/admin"): return self.admin(p, a, s)
        extra.nf(self, s)

    def home(self, s):
        feat = items_in([r["id"] for r in q("SELECT id FROM nodes")], 6, "AND featured=1")
        out = f"<div class='art'><h1>{esc(s['site_name'])}</h1><p>{esc(s['site_desc'])}</p><a class='btn' href='/join'>انضم إلى الشبكة</a> <a class='btn' href='/contact'>تواصل معنا</a></div>"
        cnt = lambda t: q("SELECT COUNT(*) c FROM items WHERE type=? AND " + PUB, (t, now()), one=True)["c"]
        out += "<div class='grid'>" + "".join(f"<div class='card'><h2>{cnt(t)}</h2>{l}</div>" for t, l in [("تحقيق", "تحقيقات"), ("قصة", "قصص"), ("فرصة", "فرص"), ("دليل", "أدلة وموارد")]) + "</div><br>"
        out += f"<div class='grid'><div class='card' style='border-top-color:green'><h3>انضم إلى الشبكة</h3><p>لماذا تنضم؟ من يمكنه الانضمام؟ أنواع ومزايا العضوية.</p><a class='btn' style='background:green' href='/join'>انضم إلى شبكة الصحفيين المستقلين</a></div><div class='card'><h3>تواصل معنا</h3><p>الشراكات والتعاون الإعلامي والاستفسارات المهنية.</p><a class='btn' href='/contact'>تواصل معنا</a></div><div class='card' style='border-top-color:#b22'><h3>ادعم الصحافة المستقلة في اليمن</h3><p>ساهم في تمكين الصحفيين المستقلين من الوصول إلى المعرفة والفرص والحماية المهنية.</p><a class='btn' style='background:#b22' href='{esc(s.get('donate_url', '/contact'))}'>تبرع لدعم الصحافة المستقلة</a></div></div>"
        if feat: out += "<h2>مواد مميزة</h2><div class='grid'>" + "".join(map(card, feat)) + "</div>"
        hs = [l.split("|") for l in s.get("home_sections", "").splitlines() if l.count("|") == 2 and l.split("|")[0].strip().isdigit()]
        secs = [(q("SELECT * FROM nodes WHERE id=?", (int(x[0]),), one=True), int(x[1] or 3), x[2]) for x in hs] if hs else [(t, 3, t["title"]) for t in q("SELECT * FROM nodes WHERE parent_id IS NULL AND kind='list' AND visible=1 ORDER BY sort")]
        for t, lim, ttl in secs:
            if not t: continue
            r = items_in(desc_ids(t["id"]), lim)
            if r: out += f"<h2><a href='/n/{t['id']}'>{esc(ttl)}</a></h2><div class='grid'>" + "".join(map(card, r)) + "</div>"
        self.out(layout("الرئيسية", out, s=s))

    def node(self, nid, s):
        n = q("SELECT * FROM nodes WHERE id=? AND visible=1", (nid,), one=True)
        if not n: return extra.nf(self, s)
        ch = q("SELECT * FROM nodes WHERE parent_id=? AND visible=1 ORDER BY sort,id", (nid,))
        o = f"<div class='meta'>{crumbs(nid)}</div><h1>{esc(n['title'])}</h1><p>{esc(n['descr'])}</p>"
        if ch: o += "<div class='grid'>" + "".join(f"<div class='card'><h3><a href='/n/{c['id']}'>{esc(c['icon'] or '')} {esc(c['title'])}</a></h3><p>{esc(c['descr'])}</p></div>" for c in ch) + "</div>"
        its = items_in(desc_ids(nid), 60)
        if its: o += "<h2>المواد</h2><div class='grid'>" + "".join(map(card, its)) + "</div>"
        o += f"<p><a href='/rss/{nid}.xml'>RSS لهذه النافذة</a></p>"
        self.out(layout(n["seo_title"] or n["title"], o, n["seo_desc"] or n["descr"], s=s))

    def article(self, iid, s):
        i = q(f"SELECT * FROM items WHERE id=? AND {PUB}", (iid, now()), one=True)
        if not i: return extra.nf(self, s)
        b = s["base_url"].rstrip("/"); url = f"{b}/a/{iid}"
        ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": i["title"], "author": {"@type": "Person", "name": i["author"] or ""},
              "datePublished": i["pub_at"], "dateModified": i["updated_at"], "publisher": {"@type": "Organization", "name": s["site_name"]}}
        if i["image"]: ld["image"] = i["image"]
        if i["type"] == "دورة": ld = {"@context": "https://schema.org", "@type": "Course", "name": i["title"], "description": i["summary"] or i["title"], "provider": {"@type": "Organization", "name": s["site_name"]}}
        head = f'<meta property="og:title" content="{esc(i["title"])}"><meta property="og:description" content="{esc(i["summary"])}"><meta property="og:image" content="{esc(i["image"])}"><meta property="og:type" content="article"><link rel="canonical" href="{esc(url)}"><script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")}</script>'
        sh = lambda n, u: f'<a class="btn" target="_blank" rel="noopener" href="{u}">{n}</a>'
        eu = esc(url)
        share = " ".join([sh("Facebook", f"https://www.facebook.com/sharer/sharer.php?u={eu}"), sh("X", f"https://twitter.com/intent/tweet?url={eu}"), sh("WhatsApp", f"https://wa.me/?text={eu}"), sh("Telegram", f"https://t.me/share/url?url={eu}")])
        rel = items_in([i["node_id"]] if i["node_id"] else [0], 4, f"AND id!={iid}")
        o = f"<div class='art'><div class='meta'>{crumbs(i['node_id'])}</div><h1>{esc(i['title'])}</h1><h3>{esc(i['subtitle'])}</h3><div class='meta'>{esc(i['author'])} · نُشر {esc(i['pub_at'])} · حُدّث {esc(i['updated_at'])}</div>"
        if i["image"]: o += f"<img src='{esc(i['image'])}' alt=''>"
        if i["deadline"]: o += f"<p><b>آخر موعد:</b> {esc(i['deadline'])}</p>"
        m = json.loads(i["meta"] or "{}")
        o += "".join(f"<p><b>{v}:</b> {esc(m[k])}</p>" for k, v in META.items() if m.get(k))
        o += f"<div id='body'>{i['body']}</div>"
        if i["link"]: o += f"<p><a class='btn' href='{esc(i['link'])}' rel='noopener'>الرابط / التقديم</a></p>"
        o += f"<div class='noprint'><button onclick='window.print()'>طباعة / حفظ PDF</button> <button onclick=\"b=document.getElementById('body').style;b.fontSize=(parseFloat(b.fontSize||16)+2)+'px'\">A+</button> {share} <button onclick=\"navigator.clipboard.writeText(location.href)\">نسخ الرابط</button></div></div>"
        if rel: o += "<h2>مواد مرتبطة</h2><div class='grid'>" + "".join(map(card, rel)) + "</div>"
        self.out(layout(i["seo_title"] or i["title"], o, i["seo_desc"] or i["summary"], head, s))

    def search(self, a, s):
        t, ty, nd, au, df = (a.get(k, "").strip() for k in ("q", "type", "node", "author", "from"))
        tys = ["مقال", "تقرير", "تحقيق", "قصة", "دليل", "ملف", "فرصة", "دورة", "خبر", "بيان", "فيديو"]
        no = "<option value=''>كل النوافذ</option>" + "".join(f"<option value='{n['id']}' {'selected' if nd==str(n['id']) else ''}>{esc(n['title'])}</option>" for n in q("SELECT * FROM nodes WHERE visible=1 ORDER BY parent_id,sort"))
        to = "<option value=''>كل الأنواع</option>" + "".join(f"<option {'selected' if ty==x else ''}>{x}</option>" for x in tys)
        o = f"<h1>البحث</h1><form><input name='q' value='{esc(t)}' placeholder='ابحث في الموقع'><select name='type'>{to}</select><select name='node'>{no}</select><input name='author' value='{esc(au)}' placeholder='الكاتب'><input name='from' value='{esc(df)}' placeholder='من تاريخ YYYY-MM-DD'><button>بحث</button></form>"
        if t or ty or nd or au or df:
            w, ar = [PUB], [now()]
            if t: w.append("(title LIKE ? OR summary LIKE ? OR body LIKE ? OR author LIKE ? OR meta LIKE ?)"); ar += [f"%{t}%"] * 5
            if ty: w.append("type=?"); ar.append(ty)
            if nd and nd.isdigit(): ids = desc_ids(int(nd)); w.append("node_id IN (%s)" % ",".join("?" * len(ids))); ar += ids
            if au: w.append("author LIKE ?"); ar.append(f"%{au}%")
            if df: w.append("pub_at>=?"); ar.append(df)
            r = q("SELECT * FROM items WHERE " + " AND ".join(w) + " ORDER BY pub_at DESC LIMIT 50", tuple(ar))
            o += f"<p>{len(r)} نتيجة</p><div class='grid'>" + "".join(map(card, r)) + "</div>"
        self.out(layout("البحث", o, s=s))

    # ---------------- لوحة التحكم ----------------
    def admin(self, p, a, s):
        if not self.user():
            return self.out(layout("دخول", "<div class='art'><h1>دخول الإدارة</h1><form method='post' action='/admin/login'><label>المستخدم</label><input name='name'><label>كلمة المرور</label><input type='password' name='pw'><button>دخول</button></form></div>", s=s, plain=True), hdr=[("X-Robots-Tag", "noindex")])
        nav = " | ".join(f"<a href='{h}'>{t}</a>" for h, t in [("/admin", "المؤشرات"), ("/admin/nodes", "التبويبات والنوافذ"), ("/admin/items", "المواد"), ("/admin/forms", "الرسائل والعضوية"), ("/admin/settings", "الإعدادات والتصميم"), ("/admin/media", "الوسائط"), ("/admin/feeds", "RSS"), ("/admin/seo", "SEO"), ("/admin/subs", "النشرة"), ("/admin/users", "المستخدمون"), ("/admin/roles", "الأدوار"), ("/admin/activity", "السجل"), ("/admin/backup", "نسخ احتياطي")])
        def kind_opts(sel): return "".join(f"<option value='{k}' {'selected' if k==sel else ''}>{l}</option>" for k, l in [("list", "قائمة مواد"), ("home", "رئيسية"), ("search", "بحث"), ("articles", "مقالات"), ("opps", "فرص"), ("resources", "موارد"), ("files", "ملفات"), ("video", "فيديو"), ("data", "بيانات"), ("page", "صفحة تعريفية"), ("custom", "مخصصة")])
        def node_opts(sel, none=True): return ("<option value=''>— بلا (مستوى أعلى) —</option>" if none else "") + "".join(f"<option value='{n['id']}' {'selected' if str(sel)==str(n['id']) else ''}>{esc(n['title'])}</option>" for n in q("SELECT * FROM nodes ORDER BY parent_id,sort"))
        body = ""
        if p == "/admin":
            c = lambda t: q(f"SELECT COUNT(*) c FROM {t}", one=True)["c"]
            body += f"<h1>لوحة المؤشرات</h1><div class='grid'>" + "".join(f"<div class='card'><h2>{v}</h2>{k}</div>" for k, v in [("نوافذ", c("nodes")), ("مواد", c("items")), ("رسائل وطلبات", c("forms")), ("مسودات", q("SELECT COUNT(*) c FROM items WHERE status='draft'", one=True)["c"]), ("بلا وصف SEO", q("SELECT COUNT(*) c FROM items WHERE seo_desc='' OR seo_desc IS NULL", one=True)["c"]), ("بلا صورة", q("SELECT COUNT(*) c FROM items WHERE image='' OR image IS NULL", one=True)["c"])]) + "</div><p><a href='/rss.xml'>RSS</a> · <a href='/sitemap.xml'>Sitemap</a> · <a href='/robots.txt'>robots.txt</a></p>"
        elif p == "/admin/nodes":
            e = q("SELECT * FROM nodes WHERE id=?", (a.get("edit"),), one=True) if a.get("edit") else None
            g = lambda k: esc(e[k]) if e and e[k] is not None else ""
            body += f"<h1>التبويبات والنوافذ (متعددة المستويات)</h1><table><tr><th>العنوان</th><th>الأب</th><th>النوع</th><th>ترتيب</th><th>ظاهر</th><th></th></tr>"
            for n in q("SELECT n.*, p.title pt FROM nodes n LEFT JOIN nodes p ON p.id=n.parent_id ORDER BY COALESCE(n.parent_id,0),n.sort"):
                body += f"<tr><td>{esc(n['title'])}</td><td>{esc(n['pt'] or '—')}</td><td>{esc(n['kind'])}</td><td>{n['sort']}</td><td>{'✓' if n['visible'] else '✗'}</td><td><a href='?edit={n['id']}'>تعديل</a> <form method='post' action='/admin/node/del' style='display:inline'><input type='hidden' name='id' value='{n['id']}'><button>حذف</button></form></td></tr>"
            body += f"</table><h2>{'تعديل' if e else 'إضافة'} نافذة</h2><form method='post' action='/admin/node'><input type='hidden' name='id' value='{g('id')}'><label>الأب</label><select name='parent_id'>{node_opts(e['parent_id'] if e else '')}</select><label>العنوان</label><input name='title' value='{g('title')}' required><label>النوع</label><select name='kind'>{kind_opts(e['kind'] if e else 'list')}</select><label>أيقونة (إيموجي)</label><input name='icon' value='{g('icon')}'><label>الوصف</label><textarea name='descr'>{g('descr')}</textarea><label>صورة (رابط)</label><input name='image' value='{g('image')}'><label>الترتيب</label><input name='sort' value='{g('sort') or 0}'><label><input type='checkbox' name='visible' value='1' style='width:auto' {'checked' if not e or e['visible'] else ''}> ظاهرة</label><label>عنوان SEO</label><input name='seo_title' value='{g('seo_title')}'><label>وصف SEO</label><input name='seo_desc' value='{g('seo_desc')}'><button>حفظ</button></form>"
        elif p == "/admin/items":
            e = q("SELECT * FROM items WHERE id=?", (a.get("edit"),), one=True) if a.get("edit") else None
            g = lambda k: esc(e[k]) if e and e[k] is not None else ""
            body += "<h1>المواد</h1><table><tr><th>العنوان</th><th>النوع</th><th>الحالة</th><th>النشر</th><th></th></tr>"
            for i in q("SELECT * FROM items ORDER BY id DESC LIMIT 100"):
                body += f"<tr><td><a href='/a/{i['id']}'>{esc(i['title'])}</a></td><td>{esc(i['type'])}</td><td>{esc(i['status'])}</td><td>{esc(i['pub_at'])}</td><td><a href='?edit={i['id']}'>تعديل</a> <form method='post' action='/admin/item/del' style='display:inline'><input type='hidden' name='id' value='{i['id']}'><button>حذف</button></form></td></tr>"
            mm = json.loads(e["meta"] or "{}") if e else {}
            MD = [dict(r) for r in q("SELECT * FROM media ORDER BY id DESC")]
            mf = "".join(f"<label>{v}</label>" + (f"<textarea name='{k}' rows='4' placeholder='العنوان|الرابط (سطر لكل مصدر؛ ملف أو رابط)'>{esc(mm.get(k, ''))}</textarea>{extra.srcpick(MD)}" if k == "sources" else f"<input name='{k}' value='{esc(mm.get(k, ''))}'>") for k, v in META.items())
            ed = extra.editor(e["body"] if e and e["body"] else "", MD)
            so = lambda lst, sel: "".join(f"<option {'selected' if x==sel else ''}>{x}</option>" for x in lst)
            st = [("draft", "مسودة"), ("review", "قيد المراجعة"), ("ready", "جاهز"), ("published", "منشور"), ("scheduled", "مجدول"), ("archived", "مؤرشف")]
            body += f"</table><h2>{'تعديل' if e else 'إضافة'} مادة</h2><form method='post' action='/admin/item'><input type='hidden' name='id' value='{g('id')}'><label>النافذة</label><select name='node_id'>{node_opts(e['node_id'] if e else '', False)}</select><label>النوع</label><select name='type'>{so(['مقال','تقرير','تحقيق','قصة','دليل','ملف','فرصة','دورة','خبر','بيان','فيديو','صفحة ثابتة','مادة متعددة الوسائط'], e['type'] if e else '')}</select><label>العنوان</label><input name='title' value='{g('title')}' required><label>العنوان الفرعي</label><input name='subtitle' value='{g('subtitle')}'><label>الملخص</label><textarea name='summary'>{g('summary')}</textarea>{ed}{mf}<label>الكاتب</label><input name='author' value='{g('author')}'><label>الصورة الرئيسية (رابط)</label><input name='image' value='{g('image')}'><label>رابط (تقديم/مصدر)</label><input name='link' value='{g('link')}'><label>الموعد النهائي (للفرص)</label><input name='deadline' value='{g('deadline')}'><label>الحالة</label><select name='status'>{''.join(f'<option value={k} {chr(115)+chr(101)+chr(108)+chr(101)+chr(99)+chr(116)+chr(101)+chr(100) if e and e[chr(115)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115)]==k else chr(32)}>{l}</option>' for k,l in st)}</select><label>تاريخ النشر (YYYY-MM-DD HH:MM)</label><input name='pub_at' value='{g('pub_at') or now()}'><label><input type='checkbox' name='featured' value='1' style='width:auto' {'checked' if e and e['featured'] else ''}> مميزة</label><label>عنوان SEO</label><input name='seo_title' value='{g('seo_title')}'><label>وصف SEO</label><input name='seo_desc' value='{g('seo_desc')}'><button>حفظ</button></form>"
        elif p == "/admin/forms":
            body += "<h1>الرسائل وطلبات العضوية</h1><table><tr><th>النوع</th><th>الاسم</th><th>البريد</th><th>الموضوع</th><th>الرسالة</th><th>الحالة</th></tr>"
            for f in q("SELECT * FROM forms ORDER BY id DESC LIMIT 200"):
                body += f"<tr><td>{esc(f['kind'])}</td><td>{esc(f['name'])}</td><td>{esc(f['email'])}</td><td>{esc(f['subject'])}</td><td>{esc(f['message'])}</td><td><form method='post' action='/admin/form/status'><input type='hidden' name='id' value='{f['id']}'><select name='status'>" + "".join(f"<option {'selected' if f['status']==x else ''}>{x}</option>" for x in ["new", "accepted", "rejected", "need_info", "archived"]) + "</select><button>حفظ</button></form></td></tr>"
            body += "</table>"
        elif p == "/admin/settings":
            body += "<h1>الإعدادات والتصميم والـ SEO</h1><form method='post'>" + "".join(f"<label>{esc(k)}</label>" + (f"<textarea name='{k}' rows='4'>{esc(v)}</textarea>" if k in ("robots", "footer_links", "home_sections") else f"<input name='{k}' value='{esc(v)}'>") for k, v in s.items()) + "<button>حفظ</button></form>"
        return self.out(layout("الإدارة", body, s=s, plain=True), hdr=[("X-Robots-Tag", "noindex")])

if __name__ == "__main__":
    init(); extra.A = sys.modules[__name__]; theme.A = extra.A; extra.init(); theme.install(); extra.start(); print(f"http://localhost:{PORT}"); ThreadingHTTPServer(("", PORT), H).serve_forever()
