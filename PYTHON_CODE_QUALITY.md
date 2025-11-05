# 🛡️ Python Kod Kalitesi ve Girinti Hatası Önleme Sistemi

## 🎯 Amaç

Python geliştirmede **GİRİNTİ HATASIZ** kod yazmak için profesyonel araçlar ve konfigürasyonlar.

---

## 🚀 Hızlı Başlangıç

### **1. VS Code Kullanıyorsanız (Önerilen)**

#### **Gerekli Eklentiler:**
1. VS Code'u aç
2. `Ctrl+Shift+X` → Extensions
3. Şu eklentileri yükle:
   - **Python** (ms-python.python)
   - **Pylance** (ms-python.vscode-pylance)
   - **Black Formatter** (ms-python.black-formatter)
   - **Flake8** (ms-python.flake8)
   - **isort** (ms-python.isort)
   - **Error Lens** (usernamehw.errorlens) ⭐ Hataları satırda gösterir!
   - **Indent Rainbow** (oderwat.indent-rainbow) ⭐ Girintileri renklendirir!

#### **Otomatik Kurulum:**
```bash
# Tüm önerilen eklentileri yükle
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.black-formatter
code --install-extension ms-python.flake8
code --install-extension ms-python.isort
code --install-extension usernamehw.errorlens
code --install-extension oderwat.indent-rainbow
```

#### **Ayarlar:**
`.vscode/settings.json` dosyası zaten hazır! 
- ✅ Kaydettiğinde otomatik format
- ✅ Tab boyutu: 4
- ✅ Satır uzunluğu: 120
- ✅ Import sorting otomatik
- ✅ Trailing whitespace temizleme

---

### **2. PyCharm Kullanıyorsanız**

#### **Ayarlar:**
1. `File` → `Settings` → `Editor` → `Code Style` → `Python`
2. **Tabs and Indents:**
   - Tab size: `4`
   - Indent: `4`
   - Use tab character: ✅
3. **Other:**
   - Right margin: `120`
4. **Actions on Save:**
   - `File` → `Settings` → `Tools` → `Actions on Save`
   - ✅ Reformat code
   - ✅ Optimize imports
   - ✅ Remove trailing whitespace

#### **External Tools:**
1. `File` → `Settings` → `Tools` → `External Tools`
2. **Black Formatter Ekle:**
   - Name: `Black Format`
   - Program: `/path/to/env/bin/black`
   - Arguments: `$FilePath$ --line-length 120`
   - Working directory: `$ProjectFileDir$`

---

### **3. Sublime Text / Atom / Diğer Editörler**

**EditorConfig** dosyası zaten hazır (`.editorconfig`)! 

Eklentiyi yükle:
- **Sublime:** Package Control → EditorConfig
- **Atom:** Settings → Install → editorconfig
- **Vim:** vim-plug ile editorconfig-vim

---

## 🔧 Komut Satırı Araçları

### **Tüm Dosyaları Kontrol Et**

```bash
# Syntax ve girinti kontrolü
bench --site ozerpan.com execute uretim_planlama.utils.python_syntax_checker.check_all_python_files
```

**Çıktı:**
```
🔍 PYTHON SYNTAX KONTROLÜ: uretim_planlama
══════════════════════════════════════════
📁 Toplam 145 Python dosyası taranıyor...

❌ stock_entry_events.py
   IndentationError (Satır 42): expected an indented block
      if doc.docstatus == 1:

📊 ÖZET
══════════════════════════════════════════
✅ Temiz Dosya: 144
❌ Hatalı Dosya: 1
🐛 Toplam Hata: 1
══════════════════════════════════════════
```

---

## 🎨 Görsel Araçlar

### **VS Code: Indent Rainbow**
Girintileri renklendirir:
- 1. seviye: Kırmızı
- 2. seviye: Sarı
- 3. seviye: Yeşil
- 4. seviye: Mavi

**Yanlış girinti hemen göze çarpar!** ⚡

### **VS Code: Error Lens**
Hataları satırın YANINDA gösterir:
```python
def my_function():
if True:  # ← ❌ IndentationError: expected an indented block
    pass
```

---

## ⚙️ Otomatik Format Ayarları

### **Dosya Kaydederken:**
- ✅ Black formatter çalışır
- ✅ Import'lar düzenlenir (isort)
- ✅ Trailing whitespace silinir
- ✅ Final newline eklenir

### **Format Kısayolları:**

**VS Code:**
- Format dosya: `Shift+Alt+F`
- Format seçili: `Ctrl+K Ctrl+F`

**PyCharm:**
- Format dosya: `Ctrl+Alt+L`

---

## 📋 Kod Kalitesi Kontrol Listesi

Commit öncesi:
- [ ] Syntax hatası yok
- [ ] Girinti tutarlı (hep tab VEYA hep space)
- [ ] Import'lar düzenli
- [ ] Trailing whitespace yok
- [ ] Line length < 120
- [ ] Fonksiyon/sınıf docstring'i var

---

## 🐛 Sık Karşılaşılan Girinti Hataları

### **1. Tab/Space Karışımı**
```python
# ❌ YANLIŞ
def my_func():
    if True:  # ← 4 space
	    pass  # ← 1 tab
```

**Çözüm:** Editörde "Show Whitespace" aç!

### **2. Eksik Girinti**
```python
# ❌ YANLIŞ
def my_func():
if True:  # ← Girinti yok!
    pass
```

### **3. Try-Except-Finally**
```python
# ❌ YANLIŞ
try:
    do_something()
# ← Except nerede?
```

**Çözüm:** Her try mutlaka except veya finally olmalı!

---

## 🎯 Best Practices

### **1. Tek Bir Girinti Stili Kullan**
```python
# ✅ İYİ - Sadece tab
def my_func():
	if True:
		pass

# ❌ KÖTÜ - Karışık
def my_func():
    if True:
	pass
```

### **2. Editör Ayarlarını Paylaş**
`.vscode/settings.json` ve `.editorconfig` git'e ekle:
```bash
git add .vscode/settings.json .editorconfig
git commit -m "chore: Add editor config"
```

### **3. Düzenli Kontrol**
```bash
# Her gün bir kez çalıştır
bench --site ozerpan.com execute uretim_planlama.utils.python_syntax_checker.check_all_python_files
```

---

## 🚨 Acil Durum: Tüm Dosyaları Temizle

```bash
# Tüm Python dosyalarını Black ile formatla
find apps/uretim_planlama/uretim_planlama -name "*.py" -not -path "*/migrations/*" -exec black --line-length 120 {} +

# Import'ları düzenle
find apps/uretim_planlama/uretim_planlama -name "*.py" -not -path "*/migrations/*" -exec isort --profile black {} +
```

---

## 📞 Yardım

Sorun yaşarsan:
1. Editör ayarlarını kontrol et
2. Syntax checker çalıştır
3. Error Lens eklentisini yükle

**Asla bir daha girinti hatası almayacaksın!** 🎉
