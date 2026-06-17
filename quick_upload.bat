@echo off
echo ========================================
echo    رفع فيتشرز الصوت الذكي
echo ========================================
echo.

echo الخطوة 1: تحديث معلومات المستخدم
git config user.name "hana-ahmed-33"
git config user.email "hana.ahmed33@gmail.com"

echo.
echo الخطوة 2: إضافة كل الملفات
git add .

echo.
echo الخطوة 3: عمل commit
git commit -m "feat: Enhanced Arabic Voice Recognition System

🎯 الفيتشرز الجديدة:
- نظام تصنيف ذكي يفهم السياق العربي
- تمييز الخدمات (تنظيف، إصلاح، مواصلات)
- معالجة ذكية للكلمات المتشابهة (ست = رقم 6 أو عاملة تنظيف)
- تقسيم النصوص المعقدة بذكاء
- تصنيف ثابت بالإنجليزية لمنع التكرار
- استخراج محسن للأرقام العربية (متين = 200)
- فهم السياق (صيدلية = صحة، سوبرماركت = طعام)

🔧 التحسينات التقنية:
- تحليل دلالي للمعاملات
- أنماط ذكية للتعرف على الخدمات
- معالجة محسنة للنصوص العربية المختلطة
- تصنيف تلقائي بناء على السياق والمكان"

echo.
echo الخطوة 4: محاولة الرفع
echo إذا طلب منك username/password، استخدمي:
echo Username: hana-ahmed-33
echo Password: Personal Access Token من GitHub
echo.
git push origin hana_voice

echo.
echo انتهى! إذا فشل، استخدمي GitHub Desktop أو Personal Access Token
pause