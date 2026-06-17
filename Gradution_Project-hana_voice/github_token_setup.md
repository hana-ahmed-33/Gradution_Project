# إعداد Personal Access Token للرفع على GitHub

## الخطوات:

### 1. إنشاء Personal Access Token:
1. اذهبي إلى: https://github.com/settings/tokens
2. اضغطي "Generate new token" > "Generate new token (classic)"
3. اختاري Expiration: 90 days أو No expiration
4. اختاري Scopes:
   - ✅ repo (full control of private repositories)
   - ✅ workflow (update GitHub Action workflows)
5. اضغطي "Generate token"
6. انسخي الـ token (مهم جداً - مش هيظهر تاني!)

### 2. استخدام الـ Token:
بعد ما تعملي الـ token، استخدمي الكوماند ده:

```bash
git push origin hana_voice
```

لما يطلب منك:
- Username: hana-ahmed-33
- Password: [الصقي الـ token هنا]

### 3. أو استخدمي الكوماند ده مباشرة:
```bash
git remote set-url origin https://YOUR_TOKEN@github.com/hana-ahmed-33/Gradution_Project.git
git push origin hana_voice
```

استبدلي YOUR_TOKEN بالـ token اللي عملتيه.

## بديل سريع:
استخدمي GitHub Desktop - أسهل وأسرع!