# 8. Sınıf Matematik Soru Üretici – Proje Özeti

## Ne Yaptık?

NotebookLM'deki kaynaklardan beslenen ve Claude ile soru yazan bir web uygulaması geliştirdik.

---

## Mimari

```
Kullanıcı (HTML Arayüz)
    ↓
Flask Backend (app.py)
    ├── NotebookLM sorgusu → örnek sorular + yazım teknikleri
    └── Claude CLI → 4 şıklı çoktan seçmeli soru üretimi
                          ↓
                    PDF oluşturma (reportlab)
                          ↓
                    NotebookLM "Claude_soru" notebook'una kaydet
```

---

## Proje Yapısı

```
soru-agent/
├── app.py               Flask backend – tüm iş mantığı burada
├── kazanimlar.json      8. sınıf matematik konuları ve kazanımları (MEB 2018)
├── templates/
│   └── index.html       Web arayüzü
├── output/              Üretilen PDF'ler buraya kaydedilir
└── start.bat            Uygulamayı başlatan script
```

---

## Nasıl Çalışıyor?

1. Kullanıcı **kazanım seçer** (birden fazla konu karıştırılabilir)
2. **Zorluk** seçer: Kolay / Orta / Zor
3. **Soru Üret** butonuna basar
4. Backend şunları yapar:
   - NotebookLM'e örnek sorular ve yazım teknikleri için sorgu atar
   - Claude CLI'ye zengin prompt gönderir
   - Gelen JSON yanıtı parse eder
   - PDF oluşturur → `output/` klasörüne kaydeder
   - PDF'yi NotebookLM **"Claude_soru"** notebook'una yükler
5. Soru arayüzde gösterilir, kullanıcı şıklara tıklayabilir, cevabı görebilir

---

## NotebookLM Kaynakları

**"soru yazma" notebook'u** (`85ce2d8a-264e-490b-9bde-66a1fc7217fa`)

| Kaynak | Amaç | Source ID |
|--------|------|-----------|
| Bloom Taksonomisi 1 | Soru yazım tekniği | `86566c16` |
| Bloom Taksonomisi 2 (O.Birgin) | Soru yazım tekniği | `0c57eec7` |
| TYMM Soru Yazım Kılavuzu | Bağlam temelli soru yazımı | (numbered PDF) |
| 1_1.pdf – 6.pdf | Örnek sorular | `e63bf929` → `bc29648b` |
| lgs_matematik.pdf | LGS örnek soruları | `69557a22` |
| Matematik Öğretim Programı 2018 | Kazanım listesi kaynağı | `75a81a8a` |

---

## Kurulum

### Gereksinimler
- Python 3.10+
- Claude Code (VS Code extension veya desktop app)
- NotebookLM kimlik doğrulaması yapılmış olmalı

### İlk Kurulum (bir kez)

```powershell
python -m venv "$HOME\.notebooklm-venv"
& "$HOME\.notebooklm-venv\Scripts\pip.exe" install "notebooklm-py[browser]" flask reportlab
& "$HOME\.notebooklm-venv\Scripts\playwright.exe" install chromium
```

### NotebookLM Girişi (oturum sürerse)

`notebooklm_login2.ps1` dosyasını çalıştır:
```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\Tayfun Hoca\notebooklm_login2.ps1"
```

### Uygulamayı Başlat

`soru-agent/start.bat` dosyasına çift tıkla → Tarayıcıda `http://localhost:5000`

---

## Teknik Notlar

### Claude CLI Yolu
Sistem PATH'inde `claude` komutu bulunmadığından tam yol kullanılıyor:
```
C:\Users\Tayfun Hoca\.vscode\extensions\anthropic.claude-code-2.1.126-win32-x64\resources\native-binary\claude.exe
```
`app.py` içinde `CLAUDE_EXE` değişkeni bunu otomatik bulur.

### Python Ortamı
Tüm bağımlılıklar `~/.notebooklm-venv` sanal ortamında. `start.bat` bunu otomatik aktive eder.

### PDF Çıktıları
`soru-agent/output/` klasörüne `[KonuAdı]_[Zorluk].pdf` formatında kaydedilir.
Aynı dosya NotebookLM **"Claude_soru"** notebook'una da yüklenir.

---

## Yapılabilecek Geliştirmeler

- [ ] Üretilen soruları geçmiş listesinde gösterme
- [ ] Birden fazla soruyu tek PDF'de birleştirme
- [ ] Soru onaylama / reddetme akışı
- [ ] Claude API anahtarıyla bağımsız çalışma modu
- [ ] Soru bankası (SQLite) entegrasyonu
