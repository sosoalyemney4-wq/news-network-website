# -*- coding: utf-8 -*-
# إضافات ناقد: الصلاحيات، المستخدمون، الوسائط، استيراد RSS، النشرة، SEO، النسخ الاحتياطي، المحرر
import theme, admin, os, re, json, secrets, hmac, hashlib, time, threading, smtplib, sqlite3, tempfile, urllib.request
from email import message_from_bytes
from email.mime.text import MIMEText
import xml.etree.ElementTree as ET
from datetime import datetime

A = None  # وحدة التطبيق (تُحقن من app.py)
E = lambda s: A.esc(s)
PERMS = {"nodes": "التبويبات والنوافذ", "items": "المواد", "forms": "العضوية والرسائل", "media": "الوسائط", "seo": "SEO والروابط",
         "rss": "RSS", "outreach": "النشرة والانتشار", "settings": "الإعدادات والنسخ الاحتياطي", "users": "المستخدمون والصلاحيات"}
ROLES = {"مدير الموقع": "all", "مدير المحتوى": "items,nodes,media", "محرر": "items,media", "مدقق": "items", "مدير فرص": "items,media",
         "مدير الموارد": "items,media", "مسؤول عضوية": "forms", "مسؤول تقني": "seo,rss,settings", "مستخدم محدود": ""}
PP = [("/admin/node", "nodes"), ("/admin/item", "items"), ("/admin/form", "forms"), ("/admin/media", "media"), ("/admin/seo", "seo"),
      ("/admin/redirect", "seo"), ("/admin/log404", "seo"), ("/admin/feed", "rss"), ("/admin/sub", "outreach"), ("/admin/news", "outreach"), ("/admin/settings", "settings"),
      ("/admin/backup", "settings"), ("/admin/restore", "settings"), ("/admin/user", "users"), ("/admin/role", "users"), ("/admin/activity", "users")]
NAV = [("/admin", "المؤشرات", None), ("/admin/nodes", "التبويبات والنوافذ", "nodes"), ("/admin/items", "المواد", "items"), ("/admin/media", "الوسائط", "media"),
       ("/admin/forms", "العضوية والرسائل", "forms"), ("/admin/feeds", "استيراد RSS", "rss"), ("/admin/seo", "SEO والزحف", "seo"), ("/admin/subs", "النشرة", "outreach"),
       ("/admin/users", "المستخدمون", "users"), ("/admin/roles", "الأدوار", "users"), ("/admin/activity", "السجل", "users"), ("/admin/settings", "الإعدادات والتصميم", "settings"), ("/admin/backup", "النسخ الاحتياطي", "settings")]
CT = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp", ".pdf": "application/pdf", ".mp4": "video/mp4",
      ".webm": "video/webm", ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf", ".otf": "font/otf", ".txt": "text/plain", ".csv": "text/csv",
      ".docx": "application/octet-stream", ".xlsx": "application/octet-stream"}
UP = os.environ.get("YJN_UPLOADS", "uploads")

def init():
    admin.A = A
    c = A.db()
    c.executescript("""CREATE TABLE IF NOT EXISTS redirects(id INTEGER PRIMARY KEY,src TEXT UNIQUE,dst TEXT,code INTEGER DEFAULT 301);
CREATE TABLE IF NOT EXISTS log404(path TEXT PRIMARY KEY,hits INTEGER DEFAULT 0,last TEXT);
CREATE TABLE IF NOT EXISTS media(id INTEGER PRIMARY KEY,filename TEXT,orig TEXT,alt TEXT,size INTEGER,created TEXT);
CREATE TABLE IF NOT EXISTS subs(email TEXT PRIMARY KEY,status TEXT DEFAULT 'active',created TEXT);
CREATE TABLE IF NOT EXISTS feeds(id INTEGER PRIMARY KEY,name TEXT,url TEXT,node_id INTEGER,keywords TEXT,active INTEGER DEFAULT 1,every INTEGER DEFAULT 60,last TEXT,error TEXT);
CREATE TABLE IF NOT EXISTS feed_items(id INTEGER PRIMARY KEY,feed_id INTEGER,title TEXT,link TEXT UNIQUE,summary TEXT,published TEXT,status TEXT DEFAULT 'new');
CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY,user TEXT,action TEXT,created TEXT);
CREATE TABLE IF NOT EXISTS roles(name TEXT PRIMARY KEY,perms TEXT);""")
    if not c.execute("SELECT 1 FROM roles").fetchone(): c.executemany("INSERT INTO roles VALUES(?,?)", ROLES.items())
    c.execute("UPDATE users SET role='مدير الموقع' WHERE role='admin'")
    c.execute("UPDATE settings SET v='شبكة الصحفيين المستقلين في اليمن - ناقد' WHERE k='site_name' AND v='شبكة الصحفيين المستقلين في اليمن'")
    for k, v in dict(site_name_en="Freelance Journalists Network in Yemen-NAQID", font_url="", home_sections="", smtp_host="", smtp_port="587", smtp_user="", smtp_pass="",
                     smtp_from="", newsletter_count="8", secret=secrets.token_hex(16)).items():
        c.execute("INSERT OR IGNORE INTO settings VALUES(?,?)", (k, v))
    bu = os.environ.get("YJN_BASE_URL") or os.environ.get("RENDER_EXTERNAL_URL") or ""
    if bu: c.execute("UPDATE settings SET v=? WHERE k='base_url' AND v=''", (bu,))
    c.commit(); c.close(); os.makedirs(UP, exist_ok=True)

def perms_of(h):
    uid = h.user()
    u = A.q("SELECT * FROM users WHERE id=?", (uid,), one=True) if uid else None
    if not u: return None, None
    r = A.q("SELECT perms FROM roles WHERE name=?", (u["role"],), one=True)
    ps = (r["perms"] if r else "").split(",")
    return (set(PERMS) if "all" in ps else {x for x in ps if x}), u

def send(h, title, body, code=200):
    ps, _ = perms_of(h)
    nav = " | ".join(f"<a href='{u}'>{l}</a>" for u, l, pm in NAV if pm is None or pm in ps)
    h.out(A.layout(title, body, s=A.S(), plain=True), code=code, hdr=[("X-Robots-Tag", "noindex")])

def nf(h, s):
    p = h.path.split("?")[0][:200]; A.q("INSERT INTO log404(path,hits,last) VALUES(?,1,?) ON CONFLICT(path) DO UPDATE SET hits=hits+1,last=?", (p, A.now(), A.now()), commit=True)
    h.out(A.layout("غير موجود", "<h1>404 — الصفحة غير موجودة</h1>", s=s), code=404)

def srcpick(media):
    o = "".join(f"<option value=\"{A.esc(m['orig'])}|/uploads/{m['filename']}\">{A.esc(m['orig'])}</option>" for m in media)
    return ("<select onchange=\"var t=document.querySelector('[name=sources]');if(this.value){t.value+=(t.value?String.fromCharCode(10):'')+this.value;this.selectedIndex=0}\">"
            "<option value=''>+ إضافة ملف من مكتبة الوسائط إلى المصادر</option>" + o + "</select>")

def editor(body, media=()):
    md = json.dumps([{"u": "/uploads/" + m["filename"], "n": m["orig"], "a": m["alt"] or "", "i": m["filename"].lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))} for m in media], ensure_ascii=False).replace("</", "<\\/")
    return """<label>نص المقالة (يدعم الطويل جداً)</label><div class='noprint'><button type='button' onclick="c('bold')">B</button> <button type='button' onclick="c('italic')">I</button>
<button type='button' onclick="c('formatBlock','h2')">عنوان</button> <button type='button' onclick="c('formatBlock','h3')">عنوان فرعي</button> <button type='button' onclick="c('formatBlock','p')">فقرة</button>
<button type='button' onclick="c('insertUnorderedList')">قائمة</button> <button type='button' onclick="c('formatBlock','blockquote')">اقتباس</button>
<button type='button' onclick="var u=prompt('الرابط');if(u)c('createLink',u)">رابط</button> <button type='button' onclick="var u=prompt('رابط صورة');if(u)c('insertImage',u)">صورة برابط</button>
<button type='button' onclick="var u=prompt('رابط الفيديو');if(u)ins('<p><video controls src=&quot;'+u+'&quot;></video></p>')">فيديو</button> <button type='button' onclick="tg()">HTML</button>
<button type='button' onclick="mp()">🖼 إدراج من مكتبة الوسائط</button>
<span class='ui'> المكان: <select id='ipos' style='width:auto;display:inline'><option value='c'>عند المؤشر</option><option value='t'>أعلى المقالة</option><option value='b'>نهاية المقالة</option></select>
 الحجم: <select id='isz' style='width:auto;display:inline'><option value=''>كاملة العرض</option><option value='mid'>متوسطة</option><option value='sm'>صغيرة</option><option value='start'>يمين النص</option><option value='end'>يسار النص</option></select></span></div>
<div id='mpn' style='display:none;background:var(--soft);padding:10px;border-radius:10px;margin:8px 0;max-height:240px;overflow:auto'></div>
<div id='ed' contenteditable='true' style='min-height:420px;background:var(--card);border:1px solid var(--line);padding:14px;border-radius:8px;line-height:2'>@@</div>
<textarea name='body' rows='18' hidden></textarea><script>var MD=@MD@,ed=document.getElementById('ed'),sr=null;
function q(s){return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;')}
function sv(){var s=getSelection();if(s.rangeCount&&ed.contains(s.anchorNode))sr=s.getRangeAt(0).cloneRange()}
['keyup','mouseup','blur'].forEach(function(e){ed.addEventListener(e,sv)});
function c(a,v){ed.focus();if(sr){var s=getSelection();s.removeAllRanges();s.addRange(sr)}document.execCommand(a,false,v||null)}
function ins(h){var p=document.getElementById('ipos').value;if(p=='t')ed.insertAdjacentHTML('afterbegin',h);else if(p=='b')ed.insertAdjacentHTML('beforeend',h);else{ed.focus();if(sr){var s=getSelection();s.removeAllRanges();s.addRange(sr)}document.execCommand('insertHTML',false,h)}}
function pick(i){var m=MD[i],z=document.getElementById('isz').value;ins(m.i?'<figure class="'+z+'"><img src="'+q(m.u)+'" alt="'+q(m.a)+'"><figcaption>'+q(m.a||'تعليق الصورة')+'</figcaption></figure><p><br></p>':'<p><a class="filecard" href="'+q(m.u)+'" target="_blank">'+q(m.n)+'</a></p>')}
function mp(){var d=document.getElementById('mpn');if(d.style.display=='none'){d.innerHTML=MD.length?MD.map(function(m,i){return '<button type="button" onclick="pick('+i+')" style="margin:3px">'+(m.i?'<img src="'+q(m.u)+'" style="height:46px;vertical-align:middle;border-radius:4px"> ':'📎 ')+q(m.n)+'</button>'}).join(''):'لا توجد ملفات. ارفع من صفحة الوسائط أولاً.';d.style.display='block'}else d.style.display='none'}
function tg(){var t=document.getElementsByName('body')[0];if(t.hidden){t.value=ed.innerHTML;t.hidden=false;ed.style.display='none'}else{ed.innerHTML=t.value;t.hidden=true;ed.style.display=''}}
document.querySelector("form[action='/admin/item']").onsubmit=function(){var t=document.getElementsByName('body')[0];if(t.hidden)t.value=ed.innerHTML}</script>""".replace("@MD@", md).replace("@@", body)

def parse_multipart(h, raw, ct):
    msg = message_from_bytes(b"Content-Type: " + ct.encode() + b"\r\n\r\n" + raw); f = {}
    for part in msg.get_payload():
        nm = part.get_param("name", header="content-disposition"); fn = part.get_filename(); d = part.get_payload(decode=True) or b""
        if fn: h.files.append((nm, fn, d))
        elif nm: f[nm] = d.decode("utf-8", "replace")
    return f

# ---------- RSS استيراد ----------
def strip(t): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or "")).strip()[:500]
def fetch(fid):
    fd = A.q("SELECT * FROM feeds WHERE id=?", (fid,), one=True); err = ""
    try:
        if not fd["url"].startswith(("http://", "https://")): raise ValueError("رابط غير صالح")
        data = urllib.request.urlopen(urllib.request.Request(fd["url"], headers={"User-Agent": "NAQID-Reader"}), timeout=15).read(2_000_000)
        if b"<!ENTITY" in data: raise ValueError("ملف XML مرفوض")
        root = ET.fromstring(data); at = "{http://www.w3.org/2005/Atom}"
        for e in root.findall(".//item") + root.findall(f".//{at}entry"):
            t = e.findtext("title") or e.findtext(at + "title") or ""
            l = e.findtext("link") or (e.find(at + "link").get("href") if e.find(at + "link") is not None else "")
            sm = strip(e.findtext("description") or e.findtext(at + "summary") or ""); pub = e.findtext("pubDate") or e.findtext(at + "updated") or ""
            kw = [k.strip() for k in (fd["keywords"] or "").split(",") if k.strip()]
            if l and t and (not kw or any(k in t + sm for k in kw)):
                A.q("INSERT OR IGNORE INTO feed_items(feed_id,title,link,summary,published) VALUES(?,?,?,?,?)", (fid, t.strip(), l.strip(), sm, pub), commit=True)
    except Exception as x: err = str(x)[:200]
    A.q("UPDATE feeds SET last=?,error=? WHERE id=?", (A.now(), err, fid), commit=True)

def start():
    def loop():
        while True:
            time.sleep(60)
            try:
                for f in A.q("SELECT * FROM feeds WHERE active=1"):
                    if not f["last"] or (datetime.now() - datetime.strptime(f["last"], "%Y-%m-%d %H:%M")).total_seconds() >= f["every"] * 60: fetch(f["id"])
            except Exception: pass
    threading.Thread(target=loop, daemon=True).start()

# ---------- النشرة ----------
def utok(s, em): return hmac.new(s["secret"].encode(), em.encode(), hashlib.sha256).hexdigest()[:20]
def send_news(subject, intro):
    s = A.S(); b = s["base_url"].rstrip("/")
    rows = A.q(f"SELECT * FROM items WHERE {A.PUB} ORDER BY pub_at DESC LIMIT ?", (A.now(), int(s.get("newsletter_count") or 8)))
    lst = "".join(f"<li><a href='{b}/a/{r['id']}'>{E(r['title'])}</a><br>{E(r['summary'])}</li>" for r in rows)
    def run():
        try:
            sm = smtplib.SMTP(s["smtp_host"], int(s["smtp_port"] or 587), timeout=20); sm.starttls()
            if s["smtp_user"]: sm.login(s["smtp_user"], s["smtp_pass"])
            for r in A.q("SELECT email FROM subs WHERE status='active'"):
                m = MIMEText(f"<div dir='rtl'><p>{E(intro)}</p><ul>{lst}</ul><hr><a href='{b}/unsub?e={r['email']}&t={utok(s, r['email'])}'>إلغاء الاشتراك</a></div>", "html", "utf-8")
                m["Subject"] = subject; m["From"] = s["smtp_from"] or s["smtp_user"]; m["To"] = r["email"]; sm.send_message(m)
            sm.quit()
        except Exception as x: print("newsletter error:", x)
    threading.Thread(target=run, daemon=True).start()

# ---------- POST ----------
def post(h, p, f):
    admin.TL.ps = None
    if p == "/subscribe":
        em = f.get("email", "").strip()
        if f.get("website") or not f.get("consent") or not re.match(r"[^@\s]+@[^@\s]+\.\w+$", em): h.out(A.layout("اشتراك", "<div class='art'><h2>تعذر الاشتراك: تأكد من البريد والموافقة.</h2></div>", s=A.S()), code=400); return True
        A.q("INSERT INTO subs VALUES(?,?,?) ON CONFLICT(email) DO UPDATE SET status='active'", (em, "active", A.now()), commit=True)
        h.out(A.layout("اشتراك", "<div class='art'><h2>تم الاشتراك في النشرة. شكراً لك.</h2></div>", s=A.S())); return True
    if not p.startswith("/admin/") or p == "/admin/login": return False
    ps, u = perms_of(h)
    if not u: h.go("/admin"); return True
    pm = next((v for k, v in PP if p.startswith(k)), None)
    if pm and pm not in ps: h.out("403", code=403); return True
    A.q("INSERT INTO activity(user,action,created) VALUES(?,?,?)", (u["name"], p, A.now()), commit=True)
    if admin.post(h, p, f, ps, u): return True
    q, go = A.q, h.go
    if p == "/admin/media":
        for nm, fn, d in h.files:
            ext = os.path.splitext(fn)[1].lower()
            if ext in CT and 0 < len(d) <= 25_000_000:
                name = secrets.token_hex(6) + ext; open(os.path.join(UP, name), "wb").write(d)
                q("INSERT INTO media(filename,orig,alt,size,created) VALUES(?,?,?,?,?)", (name, fn, f.get("alt", ""), len(d), A.now()), commit=True)
        return go("/admin/media") or True
    if p == "/admin/media/del":
        m = q("SELECT * FROM media WHERE id=?", (f["id"],), one=True)
        if m:
            try: os.remove(os.path.join(UP, os.path.basename(m["filename"])))
            except OSError: pass
            q("DELETE FROM media WHERE id=?", (f["id"],), commit=True)
        return go("/admin/media") or True
    if p == "/admin/media/alt": q("UPDATE media SET alt=? WHERE id=?", (f["alt"], f["id"]), commit=True); return go("/admin/media") or True
    if p == "/admin/user":
        if f.get("id"):
            q("UPDATE users SET role=? WHERE id=?", (f["role"], f["id"]), commit=True)
            if f.get("pw"): q("UPDATE users SET pw=? WHERE id=?", (A.hp(f["pw"]), f["id"]), commit=True)
        elif f.get("name") and f.get("pw"): q("INSERT OR IGNORE INTO users(name,pw,role) VALUES(?,?,?)", (f["name"], A.hp(f["pw"]), f["role"]), commit=True)
        return go("/admin/users") or True
    if p == "/admin/user/del":
        if int(f["id"]) != u["id"]: q("DELETE FROM users WHERE id=?", (f["id"],), commit=True)
        return go("/admin/users") or True
    if p == "/admin/role":
        pr = "all" if f.get("p_all") else ",".join(k for k in PERMS if f.get("p_" + k))
        if f.get("name"): q("INSERT INTO roles VALUES(?,?) ON CONFLICT(name) DO UPDATE SET perms=?", (f["name"], pr, pr), commit=True)
        return go("/admin/roles") or True
    if p == "/admin/role/del":
        if not q("SELECT 1 FROM users WHERE role=?", (f["name"],), one=True): q("DELETE FROM roles WHERE name=?", (f["name"],), commit=True)
        return go("/admin/roles") or True
    if p == "/admin/redirect":
        if f.get("src", "").startswith("/") and f.get("dst"): q("INSERT INTO redirects(src,dst,code) VALUES(?,?,?) ON CONFLICT(src) DO UPDATE SET dst=?,code=?", (f["src"], f["dst"], f["code"], f["dst"], f["code"]), commit=True)
        return go("/admin/seo") or True
    if p == "/admin/redirect/del": q("DELETE FROM redirects WHERE id=?", (f["id"],), commit=True); return go("/admin/seo") or True
    if p == "/admin/log404/del": q("DELETE FROM log404 WHERE path=?", (f["path"],), commit=True); return go("/admin/seo") or True
    if p == "/admin/feed":
        q("INSERT INTO feeds(name,url,node_id,keywords,every) VALUES(?,?,?,?,?)", (f["name"], f["url"], f.get("node_id") or None, f.get("keywords", ""), int(f.get("every") or 60)), commit=True); return go("/admin/feeds") or True
    if p == "/admin/feed/toggle": q("UPDATE feeds SET active=1-active WHERE id=?", (f["id"],), commit=True); return go("/admin/feeds") or True
    if p == "/admin/feed/del": q("DELETE FROM feeds WHERE id=?", (f["id"],), commit=True); q("DELETE FROM feed_items WHERE feed_id=?", (f["id"],), commit=True); return go("/admin/feeds") or True
    if p == "/admin/feed/fetch": fetch(int(f["id"])); return go("/admin/feeds") or True
    if p == "/admin/feeditem":
        fi = q("SELECT fi.*, f.name fname, f.node_id FROM feed_items fi JOIN feeds f ON f.id=fi.feed_id WHERE fi.id=?", (f["id"],), one=True)
        if fi and f["act"] == "convert":  # يُنشأ مسودة بالملخص والرابط الأصلي فقط، دون إعادة نشر النص الكامل
            q("INSERT INTO items(node_id,type,title,summary,body,author,link,status,pub_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
              (fi["node_id"], "خبر", fi["title"], fi["summary"], f"<p>المصدر الأصلي: <a href='{E(fi['link'])}' rel='noopener'>{E(fi['fname'])}</a></p>", fi["fname"], fi["link"], "draft", A.now(), A.now()), commit=True)
        q("UPDATE feed_items SET status=? WHERE id=?", ("converted" if f["act"] == "convert" else "ignored", f["id"]), commit=True)
        return go("/admin/feeds") or True
    if p == "/admin/sub/del": q("DELETE FROM subs WHERE email=?", (f["email"],), commit=True); return go("/admin/subs") or True
    if p == "/admin/news":
        s = A.S()
        if not s["smtp_host"]: return send(h, "النشرة", "<p>اضبط إعدادات SMTP (smtp_host …) من الإعدادات أولاً.</p>") or True
        send_news(f["subject"], f["intro"]); return go("/admin/subs") or True
    if p == "/admin/restore":
        d = next((x[2] for x in h.files if x[0] == "db"), b"")
        if d[:16] == b"SQLite format 3\x00":
            bd = os.path.join(os.path.dirname(A.DB) or ".", "backups"); os.makedirs(bd, exist_ok=True); open(os.path.join(bd, f"before_restore_{int(time.time())}.db"), "wb").write(open(A.DB, "rb").read()); open(A.DB, "wb").write(d)
        return go("/admin/backup") or True
    return False

# ---------- GET ----------
def get(h, p, a, s):
    admin.TL.ps = None
    if p in ("/static/admin.css", "/static/admin.js"):
        h.out(admin.ACSS if p.endswith("css") else admin.AJS, "text/css; charset=utf-8" if p.endswith("css") else "application/javascript; charset=utf-8", hdr=[("Cache-Control", "public,max-age=600")]); return True
    if p in ("/static/theme.css", "/static/theme.js"):
        h.out(theme.CSS if p.endswith("css") else theme.JS, "text/css; charset=utf-8" if p.endswith("css") else "application/javascript; charset=utf-8", hdr=[("Cache-Control", "public,max-age=3600")]); return True
    r = A.q("SELECT * FROM redirects WHERE src=?", (p,), one=True)
    if r: h.out("", code=int(r["code"]), hdr=[("Location", r["dst"])]); return True
    if p.startswith("/uploads/"):
        fn = os.path.basename(p[9:]); fp = os.path.join(UP, fn); ext = os.path.splitext(fn)[1].lower()
        if ext in CT and os.path.isfile(fp): h.out(open(fp, "rb").read(), CT[ext], hdr=[("X-Content-Type-Options", "nosniff"), ("Cache-Control", "public,max-age=86400")])
        else: nf(h, s)
        return True
    if p in ("/sitemap-nodes.xml", "/sitemap-items.xml"):
        b = s["base_url"].rstrip("/")
        rows = [f"/n/{x['id']}" for x in A.q("SELECT id FROM nodes WHERE visible=1")] if "nodes" in p else [f"/a/{x['id']}" for x in A.q(f"SELECT id FROM items WHERE {A.PUB}", (A.now(),))]
        h.out('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{E(b + x)}</loc></url>" for x in rows) + "</urlset>", "application/xml"); return True
    if p == "/subscribe":
        h.out(A.layout("النشرة البريدية", "<div class='art'><h1>النشرة البريدية</h1><form method='post'><label>البريد الإلكتروني</label><input type='email' name='email' required><input name='website' style='display:none' tabindex='-1'><label><input type='checkbox' name='consent' value='1' style='width:auto' required> أوافق على استلام النشرة ويمكنني إلغاء الاشتراك في أي وقت</label><br><br><button>اشترك</button></form></div>", s=s)); return True
    if p == "/unsub":
        em = a.get("e", "")
        if hmac.compare_digest(a.get("t", ""), utok(s, em)): A.q("UPDATE subs SET status='unsubscribed' WHERE email=?", (em,), commit=True); m = "تم إلغاء اشتراكك."
        else: m = "رابط غير صالح."
        h.out(A.layout("النشرة", f"<div class='art'><h2>{m}</h2></div>", s=s)); return True
    if not p.startswith("/admin"): return False
    ps, u = perms_of(h)
    if not u: return False
    pm = next((v for k, v in PP if p.startswith(k)), None)
    if pm and pm not in ps: admin.TL.ps, admin.TL.u, admin.TL.path = ps, u, p; send(h, "ممنوع", "<h1>لا تملك الصلاحية لهذه الصفحة</h1>", 403); return True
    if admin.get(h, p, a, s, ps, u): return True
    sel = lambda opts, cur: "".join(f"<option {'selected' if o == cur else ''}>{E(o)}</option>" for o in opts)
    if p == "/admin/media":
        b = "<h1>مكتبة الوسائط</h1><form method='post' enctype='multipart/form-data'><input type='file' name='file' multiple required><label>النص البديل</label><input name='alt'><button>رفع</button></form><p>الأنواع: صور، PDF، فيديو، خطوط (woff/ttf/otf)، txt/csv/docx/xlsx حتى 25MB. انسخ الرابط واستخدمه في المواد والإعدادات (الشعار، رابط الخط font_url).</p><div class='grid'>"
        for m in A.q("SELECT * FROM media ORDER BY id DESC"):
            url = "/uploads/" + m["filename"]; im = f"<img src='{url}' alt='{E(m['alt'])}'>" if m["filename"].lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")) else f"<p>📄 {E(m['orig'])}</p>"
            used = A.q("SELECT COUNT(*) c FROM items WHERE image=? OR body LIKE ?", (url, f"%{url}%"), one=True)["c"]
            b += f"<div class='card'>{im}<input value='{url}' readonly onclick='this.select()'><form method='post' action='/admin/media/alt'><input type='hidden' name='id' value='{m['id']}'><input name='alt' value='{E(m['alt'])}' placeholder='نص بديل'><button>حفظ</button></form><div class='meta'>{m['size']//1024} KB · مستخدمة في {used}</div><form method='post' action='/admin/media/del'><input type='hidden' name='id' value='{m['id']}'><button>حذف</button></form></div>"
        return send(h, "الوسائط", b + "</div>") or True
    if p == "/admin/users":
        roles = [r["name"] for r in A.q("SELECT name FROM roles")]
        b = "<h1>المستخدمون</h1><table><tr><th>الاسم</th><th>الدور</th><th>تغيير</th></tr>"
        for x in A.q("SELECT * FROM users"):
            b += f"<tr><td>{E(x['name'])}</td><td>{E(x['role'])}</td><td><form method='post' action='/admin/user'><input type='hidden' name='id' value='{x['id']}'><select name='role'>{sel(roles, x['role'])}</select><input name='pw' placeholder='كلمة مرور جديدة (اختياري)'><button>حفظ</button></form><form method='post' action='/admin/user/del'><input type='hidden' name='id' value='{x['id']}'><button>حذف</button></form></td></tr>"
        return send(h, "المستخدمون", b + f"</table><h2>مستخدم جديد</h2><form method='post' action='/admin/user'><label>الاسم</label><input name='name' required><label>كلمة المرور</label><input name='pw' required><label>الدور</label><select name='role'>{sel(roles, '')}</select><button>إضافة</button></form>") or True
    if p == "/admin/roles":
        b = "<h1>الأدوار والصلاحيات</h1>"
        for r in A.q("SELECT * FROM roles"):
            has = set(r["perms"].split(","))
            b += f"<form method='post' action='/admin/role' class='card'><input type='hidden' name='name' value='{E(r['name'])}'><b>{E(r['name'])}</b> " + "".join(f"<label><input type='checkbox' style='width:auto' name='p_{k}' value='1' {'checked' if k in has or 'all' in has else ''}> {v}</label> " for k, v in PERMS.items()) + f"<label><input type='checkbox' style='width:auto' name='p_all' value='1' {'checked' if 'all' in has else ''}> كل الصلاحيات</label><button>حفظ</button></form><form method='post' action='/admin/role/del'><input type='hidden' name='name' value='{E(r['name'])}'><button>حذف الدور</button></form><br>"
        b += "<h2>دور جديد</h2><form method='post' action='/admin/role'><input name='name' placeholder='اسم الدور' required>" + "".join(f"<label><input type='checkbox' style='width:auto' name='p_{k}' value='1'> {v}</label> " for k, v in PERMS.items()) + "<button>إنشاء</button></form>"
        return send(h, "الأدوار", b) or True
    if p == "/admin/activity":
        return send(h, "السجل", "<h1>سجل النشاط</h1><table><tr><th>الوقت</th><th>المستخدم</th><th>العملية</th></tr>" + "".join(f"<tr><td>{x['created']}</td><td>{E(x['user'])}</td><td>{E(x['action'])}</td></tr>" for x in A.q("SELECT * FROM activity ORDER BY id DESC LIMIT 200")) + "</table>") or True
    if p == "/admin/feeds":
        nodes = "<option value=''>— النافذة —</option>" + "".join(f"<option value='{n['id']}'>{E(n['title'])}</option>" for n in A.q("SELECT * FROM nodes ORDER BY parent_id,sort"))
        b = f"<h1>مصادر RSS للرصد والمراجعة</h1><form method='post' action='/admin/feed'><label>الاسم</label><input name='name' required><label>رابط RSS</label><input name='url' required><label>النافذة الافتراضية</label><select name='node_id'>{nodes}</select><label>كلمات مفتاحية (اختياري، مفصولة بفاصلة)</label><input name='keywords'><label>التحديث كل (دقيقة)</label><input name='every' value='60'><button>إضافة</button></form><table><tr><th>المصدر</th><th>آخر تحديث</th><th>الخطأ</th><th></th></tr>"
        for f in A.q("SELECT * FROM feeds"):
            i = f["id"]; b += f"<tr><td>{E(f['name'])}<br><small>{E(f['url'])}</small></td><td>{E(f['last'])}</td><td>{E(f['error'])}</td><td>" + "".join(f"<form method='post' action='/admin/feed/{a_}' style='display:inline'><input type='hidden' name='id' value='{i}'><button>{l}</button></form>" for a_, l in [("fetch", "تحديث الآن"), ("toggle", "تفعيل ✓" if f["active"] else "تفعيل ✗"), ("del", "حذف")]) + "</td></tr>"
        b += "</table><h2>مواد بانتظار المراجعة</h2><table>"
        for x in A.q("SELECT fi.*,f.name fname FROM feed_items fi JOIN feeds f ON f.id=fi.feed_id WHERE fi.status='new' ORDER BY fi.id DESC LIMIT 100"):
            b += f"<tr><td><a href='{E(x['link'])}' rel='noopener' target='_blank'>{E(x['title'])}</a><br><small>{E(x['fname'])} · {E(x['published'])}</small><br>{E(x['summary'])}</td><td>" + "".join(f"<form method='post' action='/admin/feeditem' style='display:inline'><input type='hidden' name='id' value='{x['id']}'><input type='hidden' name='act' value='{ac}'><button>{l}</button></form>" for ac, l in [("convert", "تحويل إلى مسودة"), ("ignore", "تجاهل")]) + "</td></tr>"
        return send(h, "RSS", b + "</table><p>يُنشأ من المادة مسودة بالملخص ورابط المصدر الأصلي فقط، ولا يُنسخ النص الكامل.</p>") or True
    if p == "/admin/subs":
        subs = A.q("SELECT * FROM subs ORDER BY created DESC")
        b = "<h1>النشرة البريدية</h1><p>رابط الاشتراك العام: <a href='/subscribe'>/subscribe</a> · إعدادات SMTP في الإعدادات.</p><form method='post' action='/admin/news'><label>العنوان</label><input name='subject' required><label>مقدمة</label><textarea name='intro'></textarea><p>تُدرج آخر المواد المنشورة تلقائياً مع رابط إلغاء الاشتراك.</p><button>إرسال للمشتركين النشطين</button></form><table><tr><th>البريد</th><th>الحالة</th><th></th></tr>"
        b += "".join(f"<tr><td>{E(x['email'])}</td><td>{x['status']}</td><td><form method='post' action='/admin/sub/del'><input type='hidden' name='email' value='{E(x['email'])}'><button>حذف</button></form></td></tr>" for x in subs)
        return send(h, "النشرة", b + "</table>") or True
    if p == "/admin/seo":
        it = A.q("SELECT * FROM items")
        lst = lambda t, rows: f"<h3>{t} ({len(rows)})</h3><ul>" + "".join(f"<li><a href='/admin/items?edit={r['id']}'>{E(r['title'])}</a></li>" for r in rows[:25]) + "</ul>"
        ex = lambda t: {int(x["id"]) for x in A.q(f"SELECT id FROM {t}")}
        ai, ni = ex("items"), ex("nodes"); broken = []
        for r in it:
            for m in re.finditer(r'href=["\']/(a|n)/(\d+)', r["body"] or ""):
                if int(m.group(2)) not in (ai if m.group(1) == "a" else ni): broken.append((r, m.group(0)))
        b = "<h1>لوحة SEO والزحف</h1><p><a href='/sitemap.xml'>Sitemap</a> · <a href='/sitemap-items.xml'>مواد</a> · <a href='/sitemap-nodes.xml'>نوافذ</a> · <a href='/rss.xml'>RSS</a> · <a href='/robots.txt'>robots.txt</a> (يُعدَّل من الإعدادات)</p>"
        b += lst("بلا وصف SEO", [r for r in it if not r["seo_desc"]]) + lst("بلا عنوان SEO", [r for r in it if not r["seo_title"]]) + lst("بلا صورة رئيسية", [r for r in it if not r["image"]]) + lst("غير مرتبطة بنافذة", [r for r in it if not r["node_id"]]) + lst("صور بلا نص بديل", [r for r in it if re.search(r"<img(?![^>]*\balt=)", r["body"] or "")])
        b += f"<h3>روابط داخلية مكسورة ({len(broken)})</h3><ul>" + "".join(f"<li>{E(r['title'])}: {E(m)}</li>" for r, m in broken[:25]) + "</ul>"
        if a.get("check"):
            bad = []
            for r in it:
                for l in re.findall(r'href=["\'](https?://[^"\']+)', r["body"] or "")[:5]:
                    if len(bad) > 30: break
                    try: urllib.request.urlopen(urllib.request.Request(l, method="HEAD", headers={"User-Agent": "NAQID"}), timeout=6)
                    except Exception as x: bad.append((r["title"], l, str(x)[:40]))
            b += "<h3>روابط خارجية مكسورة</h3><ul>" + "".join(f"<li>{E(t)}: {E(l)} — {E(e)}</li>" for t, l, e in bad) + "</ul>"
        else: b += "<p><a href='?check=1'>فحص الروابط الخارجية</a></p>"
        b += "<h3>أخطاء 404</h3><table><tr><th>المسار</th><th>المرات</th><th></th></tr>" + "".join(f"<tr><td>{E(x['path'])}</td><td>{x['hits']}</td><td><form method='post' action='/admin/log404/del'><input type='hidden' name='path' value='{E(x['path'])}'><button>مسح</button></form></td></tr>" for x in A.q("SELECT * FROM log404 ORDER BY hits DESC LIMIT 50")) + "</table>"
        b += "<h3>إعادة التوجيه</h3><form method='post' action='/admin/redirect'><input name='src' placeholder='/old' required><input name='dst' placeholder='/new أو رابط كامل' required><select name='code'><option>301</option><option>302</option></select><button>حفظ</button></form><table>" + "".join(f"<tr><td>{E(x['src'])}</td><td>{E(x['dst'])}</td><td>{x['code']}</td><td><form method='post' action='/admin/redirect/del'><input type='hidden' name='id' value='{x['id']}'><button>حذف</button></form></td></tr>" for x in A.q("SELECT * FROM redirects")) + "</table>"
        return send(h, "SEO", b) or True
    if p == "/admin/backup":
        return send(h, "النسخ الاحتياطي", "<h1>النسخ الاحتياطي</h1><p><a class='btn' href='/admin/backup/download'>تنزيل نسخة من قاعدة البيانات</a></p><p>ملفات الوسائط في مجلد <code>uploads/</code> تُنسخ يدوياً مع القاعدة.</p><h2>استعادة</h2><form method='post' action='/admin/restore' enctype='multipart/form-data'><input type='file' name='db' required><button>استعادة (تُحفظ نسخة من الحالية أولاً)</button></form>") or True
    if p == "/admin/backup/download":
        t = tempfile.mktemp(); d = sqlite3.connect(t); c = A.db(); c.backup(d); d.close(); c.close(); data = open(t, "rb").read(); os.remove(t)
        h.out(data, "application/octet-stream", hdr=[("Content-Disposition", "attachment; filename=naqid-backup.db")]); return True
    return False
