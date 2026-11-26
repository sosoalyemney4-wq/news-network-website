# -*- coding: utf-8 -*-
# لوحة التحكم الاحترافية: قالب بشريط جانبي، مؤشرات، مواد، محرر بنشر وحفظ، شجرة نوافذ، وسائط، إعدادات
import os, json, secrets, threading
A = None
TL = threading.local()
E = lambda s: A.esc(s)
ST = {"draft": ("مسودة", "gray"), "review": ("قيد المراجعة", "amber"), "ready": ("جاهز", "blue"), "published": ("منشور", "green"), "scheduled": ("مجدول", "purple"), "archived": ("مؤرشف", "gray")}
ICONS = dict(dash='<path d="M3 13h8V3H3zM13 21h8V11h-8zM3 21h8v-6H3zM13 3v6h8V3z"/>', doc='<path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6M9 13h6M9 17h6"/>',
 tree='<path d="M12 3v6M5 21v-6a3 3 0 0 1 3-3h8a3 3 0 0 1 3 3v6M12 9v3"/><circle cx="12" cy="3" r="1"/><circle cx="5" cy="21" r="1"/><circle cx="19" cy="21" r="1"/>',
 img='<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>', inbox='<path d="M3 13l3-8h12l3 8v6H3zM3 13h5l1 3h6l1-3h5"/>',
 rss='<path d="M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1"/>', seo='<circle cx="11" cy="11" r="7"/><path d="M21 21l-5-5"/>',
 mail='<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>', users='<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0M16 4a3 3 0 0 1 0 6M21 20a6 6 0 0 0-4-5.6"/>',
 shield='<path d="M12 3l8 3v6c0 5-3.500 8-8 9-4.500-1-8-4-8-9V6z"/>', clock='<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 gear='<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2"/>', db='<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.700 3.600 3 8 3s8-1.300 8-3V6M4 12c0 1.700 3.600 3 8 3s8-1.300 8-3"/>')
ic = lambda k: f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[k]}</svg>'
GROUPS = [("", [("/admin", "لوحة المؤشرات", "dash", None)]),
 ("المحتوى", [("/admin/items", "المواد والمقالات", "doc", "items"), ("/admin/nodes", "التبويبات والنوافذ", "tree", "nodes"), ("/admin/media", "مكتبة الوسائط", "img", "media")]),
 ("التفاعل", [("/admin/forms", "العضوية والرسائل", "inbox", "forms"), ("/admin/feeds", "استيراد RSS", "rss", "rss"), ("/admin/subs", "النشرة البريدية", "mail", "outreach")]),
 ("النظام", [("/admin/seo", "SEO والزحف", "seo", "seo"), ("/admin/users", "المستخدمون", "users", "users"), ("/admin/roles", "الأدوار والصلاحيات", "shield", "users"),
             ("/admin/activity", "سجل النشاط", "clock", "users"), ("/admin/settings", "الإعدادات والتصميم", "gear", "settings"), ("/admin/backup", "النسخ الاحتياطي", "db", "settings")])]
badge = lambda k: f'<span class="bd {ST.get(k, ("", "gray"))[1]}">{ST.get(k, (k, ""))[0]}</span>'

def shell(title, body):
    ps = getattr(TL, "ps", None); path = getattr(TL, "path", ""); act = getattr(TL, "act", ""); u = getattr(TL, "u", None); s = A.S()
    head = (f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>{E(title)} — لوحة التحكم</title>'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@500;700&family=Noto+Naskh+Arabic:wght@400;600&display=swap"><link rel="stylesheet" href="/static/admin.css"><script src="/static/admin.js" defer></script></head>')
    if ps is None: return head + f'<body class="login"><div class="lg"><h2>{E(s["site_name"])}</h2>{body}</div></body></html>'
    nf = A.q("SELECT COUNT(*) c FROM forms WHERE status='new'", one=True)["c"]; nav = ""
    for g, its in GROUPS:
        r = "".join(f'<a href="{h}" class="{"on" if (path == h or (h != "/admin" and path.startswith(h))) else ""}">{ic(i)}<span>{l}</span>{f"<em>{nf}</em>" if h == "/admin/forms" and nf else ""}</a>' for h, l, i, pm in its if pm is None or pm in ps)
        if r: nav += (f"<div class='g'>{g}</div>" if g else "") + r
    return (head + f'<body><aside class="sb"><div class="lo"><b>{E(s["site_name"])}</b><small>لوحة التحكم</small></div><nav>{nav}</nav><div class="sf"><a href="/" target="_blank">عرض الموقع ↗</a><a href="/admin/logout">تسجيل الخروج</a></div></aside>'
            f'<div class="mn"><header class="tb"><button id="sbt" type="button" aria-label="القائمة">☰</button><h1>{E(title)}</h1><div class="ac">{act}</div><span class="us">{E(u["name"] if u else "")}</span></header><div class="ct">{body}</div></div><div id="ts"></div></body></html>')

def page(h, title, body, actions="", code=200):
    TL.act = actions; h.out(A.layout(title, body, s=A.S(), plain=True), code=code, hdr=[("X-Robots-Tag", "noindex")])

def tree_rows(parent=None, d=0):
    for n in A.q("SELECT * FROM nodes WHERE parent_id IS ? ORDER BY sort,id", (parent,)):
        yield n, d; yield from tree_rows(n["id"], d + 1)

def save_upload(fn, d):
    X = A.extra; ext = os.path.splitext(fn)[1].lower()
    if ext not in X.CT or not (0 < len(d) <= 25_000_000): return None
    name = secrets.token_hex(6) + ext; open(os.path.join(X.UP, name), "wb").write(d)
    A.q("INSERT INTO media(filename,orig,alt,size,created) VALUES(?,?,?,?,?)", (name, fn, "", len(d), A.now()), commit=True); return "/uploads/" + name

def dashboard():
    c = lambda sql, *a: A.q(sql, a, one=True)["c"]
    cards = [("منشورة", c("SELECT COUNT(*) c FROM items WHERE status='published'"), "green", "/admin/items?st=published"), ("مسودات", c("SELECT COUNT(*) c FROM items WHERE status='draft'"), "gray", "/admin/items?st=draft"),
             ("قيد المراجعة", c("SELECT COUNT(*) c FROM items WHERE status='review'"), "amber", "/admin/items?st=review"), ("مجدولة", c("SELECT COUNT(*) c FROM items WHERE status='scheduled'"), "purple", "/admin/items?st=scheduled"),
             ("طلبات جديدة", c("SELECT COUNT(*) c FROM forms WHERE status='new'"), "blue", "/admin/forms"), ("مشتركون", c("SELECT COUNT(*) c FROM subs WHERE status='active'"), "green", "/admin/subs")]
    b = '<div class="qa"><a class="btn pri" href="/admin/items?edit=new">＋ مقالة جديدة</a><a class="btn" href="/admin/media">رفع وسائط</a><a class="btn" href="/admin/nodes">إدارة النوافذ</a><a class="btn" href="/admin/settings">الإعدادات</a></div>'
    b += '<div class="stt">' + "".join(f'<a class="sc {k}" href="{h}"><b>{v}</b><span>{t}</span></a>' for t, v, k, h in cards) + "</div>"
    rows = "".join(f'<tr><td><a href="/admin/items?edit={i["id"]}">{E(i["title"])}</a></td><td>{badge(i["status"])}</td><td>{E(i["author"])}</td><td>{E((i["pub_at"] or "")[:10])}</td></tr>' for i in A.q("SELECT * FROM items ORDER BY id DESC LIMIT 8"))
    health = [("مواد بلا وصف SEO", c("SELECT COUNT(*) c FROM items WHERE status='published' AND (seo_desc='' OR seo_desc IS NULL)"), "/admin/seo"), ("مواد بلا صورة رئيسية", c("SELECT COUNT(*) c FROM items WHERE status='published' AND (image='' OR image IS NULL)"), "/admin/seo"),
              ("مصادر RSS بها أخطاء", c("SELECT COUNT(*) c FROM feeds WHERE error!='' AND error IS NOT NULL"), "/admin/feeds"), ("مواد RSS بانتظار المراجعة", c("SELECT COUNT(*) c FROM feed_items WHERE status='new'"), "/admin/feeds")]
    b += (f'<div class="two"><div class="cd"><h3>آخر المواد</h3><div class="tw"><table><tr><th>العنوان</th><th>الحالة</th><th>الكاتب</th><th>التاريخ</th></tr>{rows or "<tr><td colspan=4>لا توجد مواد بعد</td></tr>"}</table></div></div>'
          '<div class="cd"><h3>صحة الموقع</h3>' + "".join(f'<a class="hl {"ok" if n == 0 else "wn"}" href="{h}"><span>{t}</span><b>{n}</b></a>' for t, n, h in health) + "</div></div>")
    b += '<div class="cd"><h3>آخر النشاطات</h3>' + "".join(f'<p class="ac2"><b>{E(x["user"])}</b> {E(x["action"])} <small>{x["created"]}</small></p>' for x in A.q("SELECT * FROM activity ORDER BY id DESC LIMIT 6")) + "</div>"
    return b

def items_list(a):
    st, q_, pg = a.get("st", ""), a.get("q", "").strip(), max(1, int(a.get("p") or 1)); w, ar = [], []
    if st: w.append("status=?"); ar.append(st)
    if q_: w.append("(title LIKE ? OR author LIKE ?)"); ar += [f"%{q_}%"] * 2
    W = (" WHERE " + " AND ".join(w)) if w else ""
    tot = A.q("SELECT COUNT(*) c FROM items" + W, tuple(ar), one=True)["c"]; rows = A.q("SELECT i.*,n.title nt FROM items i LEFT JOIN nodes n ON n.id=i.node_id" + W.replace("status", "i.status").replace("title", "i.title") + " ORDER BY i.id DESC LIMIT 25 OFFSET ?", (*ar, (pg - 1) * 25))
    cnt = {r["status"]: r["c"] for r in A.q("SELECT status,COUNT(*) c FROM items GROUP BY status")}
    tabs = f'<a class="{"on" if not st else ""}" href="/admin/items">الكل <i>{sum(cnt.values())}</i></a>' + "".join(f'<a class="{"on" if st == k else ""}" href="/admin/items?st={k}">{v[0]} <i>{cnt.get(k, 0)}</i></a>' for k, v in ST.items())
    b = f'<div class="tabs2">{tabs}</div><div class="cd"><form class="sr" method="get"><input name="q" value="{E(q_)}" placeholder="ابحث في العنوان أو الكاتب"><input type="hidden" name="st" value="{E(st)}"><button class="btn">بحث</button></form><div class="tw"><table><tr><th></th><th>العنوان</th><th>الكاتب</th><th>الحالة</th><th>تاريخ النشر</th><th>إجراءات</th></tr>'
    for i in rows:
        th = f'<img class="th" src="{E(i["image"])}" alt="">' if i["image"] else '<span class="th"></span>'; pub = i["status"] == "published"
        view = ('<a class="btn sm" target="_blank" href="/a/%d">عرض</a>' % i["id"]) if pub else ""
        b += (f'<tr><td>{th}</td><td><a class="tt" href="/admin/items?edit={i["id"]}">{E(i["title"])}</a><small>{E(i["type"])} · {E(i["nt"] or "بلا نافذة")}{" · ★ مميزة" if i["featured"] else ""}</small></td><td>{E(i["author"])}</td><td>{badge(i["status"])}</td><td>{E((i["pub_at"] or "")[:16])}</td>'
              f'<td class="rw"><a class="btn sm" href="/admin/items?edit={i["id"]}">تعديل</a>{view}'
              f'<form method="post" action="/admin/item/status"><input type="hidden" name="id" value="{i["id"]}"><input type="hidden" name="to" value="{"draft" if pub else "published"}"><button class="btn sm {"" if pub else "ok"}">{"إلغاء النشر" if pub else "نشر"}</button></form>'
              f'<form method="post" action="/admin/item/del" data-confirm="حذف المادة نهائياً؟"><input type="hidden" name="id" value="{i["id"]}"><button class="btn sm dg">حذف</button></form></td></tr>')
    b += "</table></div>" + ("" if rows else '<p class="em">لا توجد مواد مطابقة.</p>')
    pages = (tot + 24) // 25
    if pages > 1: b += '<div class="pgn">' + "".join(f'<a class="{"on" if n == pg else ""}" href="/admin/items?st={st}&q={E(q_)}&p={n}">{n}</a>' for n in range(1, pages + 1)) + "</div>"
    return b + "</div>"

def item_form(a):
    X = A.extra; e = A.q("SELECT * FROM items WHERE id=?", (a.get("edit"),), one=True) if a.get("edit", "new") != "new" and str(a.get("edit")).isdigit() else None
    g = lambda k: E(e[k]) if e and e[k] is not None else ""; mm = json.loads(e["meta"] or "{}") if e else {}
    MD = [dict(r) for r in A.q("SELECT * FROM media ORDER BY id DESC")]
    nodes = "".join(f"<option value='{n['id']}' {'selected' if e and e['node_id'] == n['id'] else ''}>{'— ' * d}{E(n['title'])}</option>" for n, d in tree_rows())
    types = "".join(f"<option {'selected' if e and e['type'] == t else ''}>{t}</option>" for t in ["مقال", "تقرير", "تحقيق", "قصة", "دليل", "ملف", "فرصة", "دورة", "خبر", "بيان", "فيديو", "صفحة ثابتة", "مادة متعددة الوسائط"])
    imgs = "<option value=''>— اختر من المكتبة —</option>" + "".join(f"<option value='/uploads/{m['filename']}'>{E(m['orig'])}</option>" for m in MD if m["filename"].lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")))
    meta = "".join(f"<label>{v}</label>" + (f"<textarea name='{k}' rows='4' placeholder='العنوان|الرابط (سطر لكل مصدر؛ ملف أو رابط)'>{E(mm.get(k, ''))}</textarea>{X.srcpick(MD)}" if k == "sources" else f"<input name='{k}' value='{E(mm.get(k, ''))}'>") for k, v in A.META.items())
    pub = (e["pub_at"] if e and e["pub_at"] else A.now()).replace(" ", "T")
    cur = f'<div class="pv"><img id="pimg" src="{g("image")}" alt="" {"" if e and e["image"] else "hidden"}></div>'
    b = (f'<form method="post" action="/admin/item" enctype="multipart/form-data" class="ed"><input type="hidden" name="id" value="{g("id")}"><div class="mc2">'
         f'<input class="big" name="title" value="{g("title")}" placeholder="عنوان المقالة" required><input name="subtitle" value="{g("subtitle")}" placeholder="العنوان الفرعي (اختياري)"><textarea name="summary" rows="3" placeholder="ملخص قصير يظهر في البطاقات والبحث">{g("summary")}</textarea>'
         f'{X.editor(e["body"] if e and e["body"] else "", MD)}'
         f'<details class="cd" open><summary>مصادر الخبر والتفاصيل الإضافية</summary>{meta}<label>رابط التقديم / المصدر الرئيسي</label><input name="link" value="{g("link")}"><label>الموعد النهائي (للفرص)</label><input type="date" name="deadline" value="{g("deadline")}"></details>'
         f'<details class="cd"><summary>تحسين محركات البحث SEO</summary><div class="gp"><b id="gpt">{g("seo_title") or g("title")}</b><u>{E(A.S()["base_url"]) or "https://موقعك"}/a/{g("id") or "…"}</u><span id="gpd">{g("seo_desc") or g("summary")}</span></div>'
         f'<label>عنوان SEO <small data-count="#st" data-max="60"></small></label><input id="st" name="seo_title" value="{g("seo_title")}"><label>وصف SEO <small data-count="#sd" data-max="160"></small></label><textarea id="sd" name="seo_desc" rows="3">{g("seo_desc")}</textarea></details></div>'
         f'<div class="sd2"><div class="cd pub"><h3>النشر</h3><p>الحالة: {badge(e["status"]) if e else badge("draft")}</p><label>تاريخ ووقت النشر</label><input type="datetime-local" name="pub_at" value="{pub}"><label class="ck"><input type="checkbox" name="featured" value="1" {"checked" if e and e["featured"] else ""}> مميزة (تظهر في واجهة الأخبار الستة)</label>'
         f'<div class="bt2"><button class="btn pri" name="act" value="publish">{"تحديث ونشر" if e and e["status"] == "published" else "نشر الآن"}</button><button class="btn" name="act" value="draft">حفظ كمسودة</button><button class="btn" name="act" value="review">إرسال للمراجعة</button><button class="btn" name="act" value="archive">أرشفة</button></div>'
         + (f'<a class="btn" target="_blank" href="/a/{e["id"]}">معاينة / عرض المقالة ↗</a>' if e and e["status"] in ("published", "scheduled") else "") + "</div>"
         f'<div class="cd"><h3>الصورة الرئيسية</h3>{cur}<input type="file" name="imagefile" accept="image/*" data-preview="#pimg"><select name="image_pick">{imgs}</select><input name="image" value="{g("image")}" placeholder="أو رابط صورة"><label class="ck"><input type="checkbox" name="rm_image" value="1"> إزالة الصورة</label></div>'
         f'<div class="cd"><h3>التصنيف</h3><label>النافذة</label><select name="node_id"><option value="">— بلا —</option>{nodes}</select><label>نوع المادة</label><select name="type">{types}</select><label>الكاتب</label><input name="author" value="{g("author")}"></div></div></form>')
    return b, (e["title"] if e else "مقالة جديدة")

def nodes_page(a):
    e = A.q("SELECT * FROM nodes WHERE id=?", (a.get("edit"),), one=True) if a.get("edit") else None; g = lambda k: E(e[k]) if e and e[k] is not None else ""
    par = e["parent_id"] if e else (int(a["parent"]) if a.get("parent", "").isdigit() else None)
    rows = ""
    for n, d in tree_rows():
        cn = A.q("SELECT COUNT(*) c FROM items WHERE node_id=?", (n["id"],), one=True)["c"]
        rows += (f'<tr class="{"" if n["visible"] else "off"}"><td style="padding-inline-start:{8 + d * 26}px">{"└ " if d else ""}<a class="tt" href="/admin/nodes?edit={n["id"]}">{E(n["icon"] or "")} {E(n["title"])}</a><small>{n["kind"]} · {cn} مادة</small></td>'
                 f'<td class="rw"><form method="post" action="/admin/node/move"><input type="hidden" name="id" value="{n["id"]}"><button class="btn sm" name="dir" value="up" title="للأعلى">↑</button><button class="btn sm" name="dir" value="down" title="للأسفل">↓</button></form>'
                 f'<form method="post" action="/admin/node/toggle"><input type="hidden" name="id" value="{n["id"]}"><button class="btn sm">{"إخفاء" if n["visible"] else "إظهار"}</button></form><a class="btn sm" href="/admin/nodes?parent={n["id"]}">＋ فرعية</a><a class="btn sm" href="/admin/nodes?edit={n["id"]}">تعديل</a>'
                 f'<form method="post" action="/admin/node/del" data-confirm="حذف النافذة؟ (لا تُحذف إن كان لها فروع)"><input type="hidden" name="id" value="{n["id"]}"><button class="btn sm dg">حذف</button></form></td></tr>')
    po = "<option value=''>— مستوى أعلى (تبويب رئيسي) —</option>" + "".join(f"<option value='{n['id']}' {'selected' if par == n['id'] else ''}>{'— ' * d}{E(n['title'])}</option>" for n, d in tree_rows() if not (e and n["id"] == e["id"]))
    kinds = "".join(f"<option value='{k}' {'selected' if e and e['kind'] == k else ''}>{l}</option>" for k, l in [("list", "قائمة مواد"), ("home", "رئيسية"), ("search", "بحث"), ("articles", "مقالات"), ("opps", "فرص"), ("resources", "موارد"), ("files", "ملفات"), ("video", "فيديو"), ("data", "بيانات"), ("page", "صفحة تعريفية"), ("custom", "مخصصة")])
    return (f'<div class="two w"><div class="cd"><h3>هيكل الموقع</h3><div class="tw"><table>{rows}</table></div></div><form class="cd" method="post" action="/admin/node"><h3>{"تعديل نافذة" if e else "إضافة نافذة"}</h3><input type="hidden" name="id" value="{g("id")}">'
            f'<label>الأب</label><select name="parent_id">{po}</select><label>العنوان</label><input name="title" value="{g("title")}" required><label>النوع</label><select name="kind">{kinds}</select><label>أيقونة (إيموجي)</label><input name="icon" value="{g("icon")}"><label>الوصف</label><textarea name="descr" rows="3">{g("descr")}</textarea>'
            f'<label>صورة (رابط)</label><input name="image" value="{g("image")}"><label>الترتيب</label><input type="number" name="sort" value="{g("sort") or 0}"><label class="ck"><input type="checkbox" name="visible" value="1" {"checked" if not e or e["visible"] else ""}> ظاهرة في الموقع</label><label>عنوان SEO</label><input name="seo_title" value="{g("seo_title")}"><label>وصف SEO</label><input name="seo_desc" value="{g("seo_desc")}">'
            f'<div class="bt2"><button class="btn pri">حفظ</button>{"<a class=btn href=/admin/nodes>إلغاء</a>" if e or par else ""}</div></form></div>')

def media_page():
    b = '<form class="drop" method="post" action="/admin/media" enctype="multipart/form-data"><input class="autosub" type="file" name="file" multiple><b>اسحب الملفات هنا أو اضغط للاختيار</b><span>صور، PDF، فيديو، خطوط، ملفات مكتب — حتى 25MB. يبدأ الرفع تلقائياً.</span></form>'
    b += '<div class="cd"><input class="fl" data-filter=".mg" placeholder="ابحث في الوسائط"><div class="mg">'
    for m in A.q("SELECT * FROM media ORDER BY id DESC"):
        u = "/uploads/" + m["filename"]; im = f'<img src="{u}" alt="">' if m["filename"].lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")) else f'<div class="fi">{E(os.path.splitext(m["filename"])[1].upper())}</div>'
        b += (f'<div class="mi" data-t="{E(m["orig"])}">{im}<b>{E(m["orig"])}</b><small>{m["size"] // 1024} KB</small><div class="rw"><button type="button" class="btn sm" data-copy="{u}">نسخ الرابط</button>'
              f'<form method="post" action="/admin/media/del" data-confirm="حذف الملف؟"><input type="hidden" name="id" value="{m["id"]}"><button class="btn sm dg">حذف</button></form></div></div>')
    return b + "</div></div>"

def settings_page():
    s = A.S(); done = set()
    def f(k, label, kind="text", extra=""):
        done.add(k); v = E(s.get(k, ""))
        if kind == "ta": return f"<label>{label}</label><textarea name='{k}' rows='5'>{v}</textarea>"
        if kind == "color": return f"<label>{label}</label><input type='color' name='{k}' value='{v or '#000000'}' class='clr'>"
        return f"<label>{label}</label><input name='{k}' value='{v}'>{extra}"
    T = [("عام", f("site_name", "اسم الموقع") + f("site_name_en", "الاسم الإنجليزي") + f("site_desc", "وصف الموقع", "ta") + f("base_url", "عنوان الموقع الكامل (مثل https://example.com)") + f("contact_email", "البريد الرسمي") + f("footer", "نص الفوتر") + f("donate_url", "رابط زر التبرع")),
         ("المظهر", f("primary", "اللون الأساسي", "color") + f("secondary", "اللون الثانوي (الذهبي)", "color") + f("logo", "رابط الشعار", extra="<input type='file' name='logo_file' accept='image/*'><small>أو ارفع صورة جديدة ليحل محل الرابط</small>") + f("font_url", "رابط الخط", extra="<input type='file' name='font_file' accept='.woff,.woff2,.ttf,.otf'><small>ارفع ملف خط من جهازك</small>") + f("home_sections", "أقسام الرئيسية (سطر: رقم_النافذة|العدد|العنوان — اتركه فارغاً للوضع التلقائي)", "ta") + f("footer_links", "روابط الفوتر (سطر: العمود|النص|الرابط)", "ta")),
         ("SEO", f("robots", "ملف robots.txt", "ta")),
         ("البريد والنشرة", f("smtp_host", "خادم SMTP") + f("smtp_port", "المنفذ") + f("smtp_user", "المستخدم") + f("smtp_pass", "كلمة المرور") + f("smtp_from", "بريد المرسل") + f("newsletter_count", "عدد مواد النشرة"))]
    rest = "".join(f(k, k) for k in s if k not in done and k not in ("secret", "bg", "text", "font"))
    if rest: T.append(("متقدم", rest))
    nav = "".join(f'<button type="button" class="{"on" if i == 0 else ""}" data-tab="t{i}">{n}</button>' for i, (n, _) in enumerate(T))
    return f'<form class="cd" method="post" action="/admin/settings" enctype="multipart/form-data"><div class="tabs2">{nav}</div>' + "".join(f'<div class="tp" id="t{i}" {"" if i == 0 else "hidden"}>{c}</div>' for i, (_, c) in enumerate(T)) + '<div class="bt2"><button class="btn pri">حفظ الإعدادات</button></div></form>'

def forms_page():
    b = '<div class="cd"><div class="tw"><table><tr><th>النوع</th><th>الاسم</th><th>البريد</th><th>الموضوع</th><th>الرسالة</th><th>التاريخ</th><th>الحالة</th></tr>'
    for x in A.q("SELECT * FROM forms ORDER BY id DESC LIMIT 200"):
        o = "".join(f'<option value="{v}" {"selected" if x["status"] == v else ""}>{l}</option>' for v, l in [("new", "جديد"), ("accepted", "مقبول"), ("rejected", "مرفوض"), ("need_info", "يحتاج معلومات"), ("archived", "مؤرشف")])
        b += f'<tr><td>{"عضوية" if x["kind"] == "join" else "رسالة"}</td><td>{E(x["name"])}</td><td><a href="mailto:{E(x["email"])}">{E(x["email"])}</a></td><td>{E(x["subject"])}</td><td style="white-space:normal;min-width:240px">{E(x["message"])}</td><td>{E(x["created"])}</td><td><form method="post" action="/admin/form/status"><input type="hidden" name="id" value="{x["id"]}"><select name="status" data-auto>{o}</select></form></td></tr>'
    return b + "</table></div></div>"

def get(h, p, a, s, ps, u):
    TL.ps, TL.u, TL.path = ps, u, p
    X = A.extra
    if p == "/admin": return page(h, "لوحة المؤشرات", dashboard()) or True
    if p == "/admin/logout":
        for k in [k for k, v in A.SESS.items() if v == u["id"]]: A.SESS.pop(k, None)
        h.out("", code=303, hdr=[("Location", "/admin"), ("Set-Cookie", "sid=; Max-Age=0; Path=/")]); return True
    if p == "/admin/items":
        if "edit" in a:
            b, t = item_form(a); return page(h, t, b, '<a class="btn" href="/admin/items">← كل المواد</a>') or True
        return page(h, "المواد والمقالات", items_list(a), '<a class="btn pri" href="/admin/items?edit=new">＋ مقالة جديدة</a>') or True
    if p == "/admin/nodes": return page(h, "التبويبات والنوافذ", nodes_page(a)) or True
    if p == "/admin/media": return page(h, "مكتبة الوسائط", media_page()) or True
    if p == "/admin/settings": return page(h, "الإعدادات والتصميم", settings_page()) or True
    if p == "/admin/forms": return page(h, "العضوية والرسائل", forms_page()) or True
    return False

def post(h, p, f, ps, u):
    TL.ps, TL.u, TL.path = ps, u, p; q = A.q
    if p == "/admin/item":
        st = {"publish": "published", "draft": "draft", "review": "review", "archive": "archived"}.get(f.get("act"), "draft")
        n = A.now(); pub = (f.get("pub_at") or "").replace("T", " ")[:16] or n
        if st == "published" and pub > n: st = "scheduled"
        img = f.get("image_pick") or f.get("image", "").strip()
        for nm, fn, d in h.files:
            if nm == "imagefile" and d: img = save_upload(fn, d) or img
        if f.get("rm_image"): img = ""
        v = (f.get("node_id") or None, f.get("type", "مقال"), f["title"], f.get("subtitle", ""), f.get("summary", ""), f.get("body", ""), f.get("author", ""), img, f.get("link", ""), f.get("deadline", ""), st, pub, n, int(f.get("featured") == "1"), f.get("seo_title", ""), f.get("seo_desc", ""), json.dumps({k: f.get(k, "") for k in A.META}, ensure_ascii=False))
        if f.get("id"): q("UPDATE items SET node_id=?,type=?,title=?,subtitle=?,summary=?,body=?,author=?,image=?,link=?,deadline=?,status=?,pub_at=?,updated_at=?,featured=?,seo_title=?,seo_desc=?,meta=? WHERE id=?", (*v, f["id"]), commit=True); iid = f["id"]
        else: iid = q("INSERT INTO items(node_id,type,title,subtitle,summary,body,author,image,link,deadline,status,pub_at,updated_at,featured,seo_title,seo_desc,meta) VALUES(" + ",".join("?" * 17) + ")", v, commit=True)
        h.go(f"/admin/items?edit={iid}&ok={f.get('act', 'draft')}"); return True
    if p == "/admin/item/status":
        n = A.now()
        if f["to"] == "published": q("UPDATE items SET status='published', pub_at=CASE WHEN pub_at>? THEN ? ELSE pub_at END WHERE id=?", (n, n, f["id"]), commit=True)
        else: q("UPDATE items SET status=? WHERE id=?", (f["to"], f["id"]), commit=True)
        h.go("/admin/items?ok=" + ("publish" if f["to"] == "published" else "draft")); return True
    if p == "/admin/node/toggle": q("UPDATE nodes SET visible=1-visible WHERE id=?", (f["id"],), commit=True); h.go("/admin/nodes"); return True
    if p == "/admin/node/move":
        r = q("SELECT * FROM nodes WHERE id=?", (f["id"],), one=True); sib = [x for x in q("SELECT * FROM nodes WHERE parent_id IS ? ORDER BY sort,id", (r["parent_id"],))]
        ids = [x["id"] for x in sib]; i = ids.index(r["id"]); j = i - 1 if f["dir"] == "up" else i + 1
        if 0 <= j < len(ids):
            ids[i], ids[j] = ids[j], ids[i]
            for k, nid in enumerate(ids): q("UPDATE nodes SET sort=? WHERE id=?", (k, nid), commit=True)
        h.go("/admin/nodes"); return True
    if p == "/admin/settings":
        X = A.extra
        for nm, fn, d in h.files:
            if d and nm in ("logo_file", "font_file"):
                url = save_upload(fn, d)
                if url: f["logo" if nm == "logo_file" else "font_url"] = url
        cur = A.S()
        for k, v in f.items():
            if k in cur: q("UPDATE settings SET v=? WHERE k=?", (v, k), commit=True)
        h.go("/admin/settings?ok=settings"); return True
    return False

ACSS = r"""
:root{--bg:#f1f4f9;--card:#fff;--ink:#18233b;--mute:#66758f;--line:#dfe5f0;--soft:#eef2f9;--navy:#0b1d3f;--gold:#d4af37;--blue:#2a6fdb;--ok:#1d9a5b;--bad:#d13b32}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:400 .98rem/1.8 "Noto Naskh Arabic",Tahoma,sans-serif}
h1,h2,h3,b,button,label,.btn,th,nav a,.g,summary{font-family:"Noto Kufi Arabic",Tahoma,sans-serif}a{color:var(--blue)}
.sb{position:fixed;inset:0 0 0 auto;width:262px;background:linear-gradient(180deg,#0b1d3f,#081530);color:#cdd9f0;display:flex;flex-direction:column;z-index:30;transition:transform .25s}
.lo{padding:20px 20px 14px;border-bottom:1px solid #ffffff1a}.lo b{display:block;color:#fff;font-size:.95rem;line-height:1.6}.lo small{color:var(--gold);font-size:.75rem}
.sb nav{flex:1;overflow:auto;padding:10px}.g{font-size:.7rem;color:#7f93b8;padding:14px 12px 4px;letter-spacing:.5px}
.sb nav a{display:flex;align-items:center;gap:11px;color:#cdd9f0;text-decoration:none;padding:9px 12px;border-radius:9px;font-size:.88rem;margin:1px 0;transition:.15s}.sb nav a svg{width:19px;height:19px;flex:none;opacity:.85}
.sb nav a:hover{background:#ffffff12;color:#fff}.sb nav a.on{background:linear-gradient(90deg,#d4af3730,#d4af3710);color:#fff;box-shadow:inset -3px 0 var(--gold)}.sb nav em{margin-inline-start:auto;background:var(--bad);color:#fff;font-style:normal;font-size:.7rem;border-radius:99px;padding:0 8px}
.sf{padding:12px 18px;border-top:1px solid #ffffff1a;display:flex;flex-direction:column;font-size:.82rem}.sf a{color:#9fb2d6;text-decoration:none;padding:3px 0}.sf a:hover{color:#fff}
.mn{margin-inline-end:262px;min-height:100vh}.tb{position:sticky;top:0;background:#fffffff2;backdrop-filter:blur(8px);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:14px;padding:12px 26px;z-index:20}
.tb h1{font-size:1.15rem;margin:0}.ac{margin-inline-start:auto;display:flex;gap:8px}.us{background:var(--soft);padding:2px 14px;border-radius:99px;font-size:.82rem}#sbt{display:none;border:1px solid var(--line);background:#fff;border-radius:8px;width:38px;height:38px;font-size:1.1rem}
.ct{padding:24px 26px 60px;max-width:1500px}.cd{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:18px;box-shadow:0 1px 2px #0b1d3f0a}.cd h3{margin:0 0 12px;font-size:1rem}
.btn,.ct button{display:inline-flex;align-items:center;gap:6px;background:#fff;color:var(--ink);border:1px solid var(--line);border-radius:9px;padding:7px 16px;font-size:.85rem;cursor:pointer;text-decoration:none;transition:.15s}
.btn:hover,.ct button:hover{border-color:var(--blue);color:var(--blue)}.btn.pri{background:var(--navy);color:#fff;border-color:var(--navy)}.btn.pri:hover{background:#13306a;color:#fff}.btn.ok{background:var(--ok);color:#fff;border-color:var(--ok)}.btn.dg{color:var(--bad)}.btn.dg:hover{background:var(--bad);color:#fff;border-color:var(--bad)}.btn.sm{padding:3px 11px;font-size:.78rem}
input,select,textarea{width:100%;padding:9px 12px;border:1px solid var(--line);border-radius:9px;background:#fff;color:var(--ink);font:inherit;margin:3px 0 8px}input:focus,select:focus,textarea:focus{outline:2px solid #2a6fdb55;border-color:var(--blue)}input[type=checkbox]{width:auto;margin:0 0 0 8px}input[type=color]{height:44px;padding:3px;width:120px}
label{font-size:.82rem;color:var(--mute);display:block;margin-top:6px}label.ck{display:flex;align-items:center;color:var(--ink);margin:10px 0}.big{font-size:1.4rem;font-weight:700;padding:12px 16px}small{color:var(--mute)}
.qa{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}.stt{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin-bottom:18px}
.sc{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 18px;text-decoration:none;color:var(--ink);border-top:4px solid var(--mute);transition:.2s}.sc:hover{transform:translateY(-3px);box-shadow:0 10px 24px -14px #0b1d3f66}
.sc b{display:block;font-size:2rem;line-height:1.3}.sc span{color:var(--mute);font-size:.85rem}.sc.green{border-top-color:var(--ok)}.sc.amber{border-top-color:#e0a100}.sc.blue{border-top-color:var(--blue)}.sc.purple{border-top-color:#7a4cd1}
.two{display:grid;grid-template-columns:2fr 1fr;gap:18px}.two.w{grid-template-columns:1.6fr 1fr;align-items:start}.hl{display:flex;justify-content:space-between;text-decoration:none;color:var(--ink);padding:8px 12px;border-radius:9px;margin-bottom:6px;background:var(--soft)}.hl.ok b{color:var(--ok)}.hl.wn b{color:#c47f00}
.ac2{margin:0;padding:6px 0;border-bottom:1px solid var(--soft);font-size:.88rem}.tw{overflow-x:auto}table{width:100%;border-collapse:collapse}th{background:var(--soft);font-size:.78rem;color:var(--mute);text-align:right;padding:9px 12px;white-space:nowrap}td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:right;vertical-align:middle}tr:hover td{background:#f8faff}tr.off td{opacity:.5}
.tt{font-weight:700;text-decoration:none;color:var(--ink);display:block}.tt:hover{color:var(--blue)}td small{display:block}.th{width:56px;height:40px;border-radius:8px;object-fit:cover;background:var(--soft);display:block}.rw{display:flex;gap:6px;flex-wrap:wrap;white-space:nowrap}.rw form{margin:0;display:inline}
.bd{display:inline-block;padding:0 12px;border-radius:99px;font:700 .72rem "Noto Kufi Arabic",sans-serif;background:var(--soft);color:var(--mute)}.bd.green{background:#dff5ea;color:#12784a}.bd.amber{background:#fff0cf;color:#996a00}.bd.purple{background:#ece3fb;color:#5a32a3}.bd.blue{background:#e0ecff;color:#1d55b3}
.tabs2{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:14px}.tabs2 a,.tabs2 button{background:#fff;border:1px solid var(--line);border-radius:99px;padding:4px 16px;text-decoration:none;color:var(--ink);font-size:.82rem;cursor:pointer}.tabs2 .on{background:var(--navy);color:#fff;border-color:var(--navy)}.tabs2 i{font-style:normal;opacity:.7;margin-inline-start:4px}
.sr{display:flex;gap:8px;margin-bottom:12px}.sr input{margin:0}.pgn{display:flex;gap:4px;margin-top:14px}.pgn a{padding:2px 12px;border:1px solid var(--line);border-radius:8px;text-decoration:none}.pgn .on{background:var(--navy);color:#fff}.em{text-align:center;color:var(--mute);padding:24px}
.ed{display:grid;grid-template-columns:1fr 330px;gap:20px;align-items:start}.sd2{position:sticky;top:78px}.pub .bt2,.bt2{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.pub .bt2 .btn{flex:1;justify-content:center}.pub .btn.pri{flex-basis:100%;padding:10px;font-size:.95rem}
.pv img{width:100%;border-radius:10px;margin-bottom:8px;max-height:200px;object-fit:cover}details.cd summary{cursor:pointer;font-weight:700;font-size:.95rem}.gp{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:10px 0}.gp b{color:#1a0dab;display:block;font-weight:500}.gp u{color:#006621;text-decoration:none;font-size:.8rem;display:block;direction:ltr;text-align:right}.gp span{color:#4d5156;font-size:.85rem}
.drop{position:relative;display:block;border:2px dashed #b8c6e0;border-radius:16px;background:#fff;text-align:center;padding:34px 16px;margin-bottom:18px;transition:.2s}.drop.hv,.drop:hover{border-color:var(--blue);background:#f2f7ff}.drop input{position:absolute;inset:0;opacity:0;cursor:pointer;margin:0;height:100%}.drop b{display:block}.drop span{color:var(--mute);font-size:.85rem}
.mg{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:14px;margin-top:12px}.mi{border:1px solid var(--line);border-radius:12px;padding:8px;background:#fff}.mi img,.fi{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:8px;background:var(--soft);display:grid;place-items:center;font:700 1.2rem "Noto Kufi Arabic";color:var(--mute)}.mi b{display:block;font-size:.75rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:6px}
.fl{margin:0}.tp{padding-top:4px}.lg{max-width:380px;margin:12vh auto;background:#fff;border:1px solid var(--line);border-radius:16px;padding:28px;box-shadow:0 20px 50px -25px #0b1d3f66}.lg h2{margin:0 0 14px;font-size:1.1rem;text-align:center}.lg button{width:100%;background:var(--navy);color:#fff;border:0;border-radius:9px;padding:10px;font:700 .95rem "Noto Kufi Arabic";cursor:pointer}.login{background:linear-gradient(160deg,#0b1d3f,#173a7a)}
#ts{position:fixed;bottom:26px;inset-inline:0;margin:auto;width:max-content;background:var(--navy);color:#fff;padding:10px 24px;border-radius:99px;border:1px solid var(--gold);opacity:0;transform:translateY(20px);transition:.3s;z-index:99;pointer-events:none;font-family:"Noto Kufi Arabic"}#ts.on{opacity:1;transform:none}
@media (max-width:1000px){.sb{transform:translateX(100%)}.sbo .sb{transform:none}.mn{margin:0}#sbt{display:block}.ed,.two,.two.w{grid-template-columns:1fr}.sd2{position:static}.ct{padding:16px 14px 60px}.tb{padding:10px 14px}.us{display:none}}
"""

AJS = r"""
(function(){var $=function(s,r){return(r||document).querySelector(s)},$$=function(s,r){return[].slice.call((r||document).querySelectorAll(s))};
function toast(m){var t=$('#ts');t.textContent=m;t.classList.add('on');setTimeout(function(){t.classList.remove('on')},2800)}
var b=$('#sbt');if(b)b.onclick=function(){document.body.classList.toggle('sbo')};
document.addEventListener('submit',function(e){var c=e.target.dataset.confirm;if(c&&!confirm(c))e.preventDefault()});
var M={publish:'تم النشر بنجاح ✓',draft:'تم الحفظ كمسودة ✓',review:'أُرسلت للمراجعة ✓',archive:'تمت الأرشفة ✓',settings:'تم حفظ الإعدادات ✓'},k=new URLSearchParams(location.search).get('ok');if(k&&M[k])toast(M[k]);
$$('select[data-auto]').forEach(function(s){s.onchange=function(){s.form.submit()}});
$$('.autosub').forEach(function(i){i.onchange=function(){i.form.submit()});var d=i.parentNode;['dragenter','dragover'].forEach(function(e){d.addEventListener(e,function(){d.classList.add('hv')})});['dragleave','drop'].forEach(function(e){d.addEventListener(e,function(){d.classList.remove('hv')})})});
$$('[data-copy]').forEach(function(b){b.onclick=function(){var u=location.origin+b.dataset.copy;try{navigator.clipboard.writeText(u);toast('نُسخ الرابط')}catch(e){prompt('انسخ الرابط',u)}}});
$$('[data-filter]').forEach(function(i){i.oninput=function(){var q=i.value.trim();$$('.mi',$(i.dataset.filter)).forEach(function(m){m.style.display=m.dataset.t.indexOf(q)>-1?'':'none'})}});
$$('[data-tab]').forEach(function(b){b.onclick=function(){$$('[data-tab]').forEach(function(x){x.classList.toggle('on',x===b)});$$('.tp').forEach(function(p){p.hidden=p.id!==b.dataset.tab})}});
$$('[data-preview]').forEach(function(i){i.onchange=function(){var f=i.files[0],im=$(i.dataset.preview);if(f&&im){im.src=URL.createObjectURL(f);im.hidden=false}}});
$$('[data-count]').forEach(function(c){var i=$(c.dataset.count),m=+c.dataset.max,u=function(){c.textContent=i.value.length+'/'+m;c.style.color=i.value.length>m?'#d13b32':'#66758f';var g=$(i.id==='st'?'#gpt':'#gpd');if(g&&i.value)g.textContent=i.value};i.addEventListener('input',u);u()});
})();
"""
