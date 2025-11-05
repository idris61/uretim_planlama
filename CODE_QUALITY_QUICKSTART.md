# ⚡ Girinti Hatası Önleme - Hızlı Başlangıç

## 🎯 VS Code İçin (5 Dakika Kurulum)

### **1. Eklentileri Yükle**
```bash
code --install-extension ms-python.python
code --install-extension ms-python.black-formatter
code --install-extension usernamehw.errorlens
code --install-extension oderwat.indent-rainbow
```

### **2. Workspace'i Aç**
```bash
code apps/uretim_planlama
```

✅ `.vscode/settings.json` otomatik yüklenecek!

### **3. Artık Hazırsın!**
- Dosyayı kaydet → Otomatik format ✅
- Hataları satırda gör ✅
- Girintiler renkli ✅

---

## 🔍 Tüm Dosyaları Kontrol Et

```bash
bench --site ozerpan.com execute \
  uretim_planlama.utils.python_syntax_checker.check_all_python_files
```

**Çıktı:**
```
✅ Temiz Dosya: 87
❌ Hatalı Dosya: 3
🐛 Toplam Hata: 16
```

---

## 🎨 Görsel Araçlar

### **Error Lens**
Hataları SATIRDA gösterir:
```python
def my_func():
if True:  # ← ❌ IndentationError: expected an indented block
    pass
```

### **Indent Rainbow**
Girintileri renklendirir - yanlış girinti hemen göze çarpar!

---

## 📋 Commit Öncesi Checklist

```bash
# 1. Syntax kontrol
bench --site ozerpan.com execute uretim_planlama.utils.python_syntax_checker.check_all_python_files

# 2. Tüm dosyalar temiz ise commit
git add .
git commit -m "feat: yeni özellik"
```

---

## 🚨 Acil Düzeltme

Tüm dosyaları otomatik temizle:
```bash
find apps/uretim_planlama/uretim_planlama -name "*.py" \
  -not -path "*/migrations/*" \
  -exec python3 -m black --line-length 120 {} +
```

---

**Detaylı dokümantasyon:** `PYTHON_CODE_QUALITY.md`
