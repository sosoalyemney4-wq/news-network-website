# موقع ناقد — دليل النشر

## الخيار الأسهل: Render.com أو Railway.app
1. ارفع مجلد المشروع (app.py, extra.py, Dockerfile) إلى مستودع GitHub.
2. أنشئ خدمة Web Service جديدة من المستودع (Docker).
3. أضف قرص تخزين دائماً (Persistent Disk) واجعل مساره: /data
   (بدونه تضيع قاعدة البيانات والملفات المرفوعة عند كل إعادة تشغيل).
4. عند أول تشغيل ستجد كلمة مرور المدير (admin) مطبوعة في سجلات الخدمة (Logs).
5. اربط نطاقك (Domain). الشهادة HTTPS تأتي تلقائياً.
6. ادخل /admin ← الإعدادات، واكتب عنوان موقعك الكامل في base_url (مثل https://naqid.org).
   ثم غيّر كلمة مرور المدير من صفحة المستخدمون.

## على خادم VPS
docker build -t naqid .
docker run -d -p 8000:8000 -v naqid_data:/data --restart=always naqid
ثم ضع Nginx أو Caddy أمامه لتفعيل HTTPS.

## بدون Docker
python3 app.py   # يعمل على المنفذ 8000

## النسخ الاحتياطي
من لوحة التحكم: النسخ الاحتياطي ← تنزيل. وانسخ مجلد uploads معه.
