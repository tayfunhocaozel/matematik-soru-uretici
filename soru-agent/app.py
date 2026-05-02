import os
import json
import subprocess
import tempfile
import re
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from supabase import create_client, Client

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Supabase setup
SUPABASE_URL = "https://mrmacnxvtqsiizyuagkp.supabase.co"
SUPABASE_KEY = "sb_publishable_ecBOs9ZNMA5VF1cEFf35Cg_XbnbX4sX"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

NOTEBOOKLM = str(Path.home() / ".notebooklm-venv/Scripts/notebooklm.exe")
SORU_YAZMA_NOTEBOOK = "85ce2d8a-264e-490b-9bde-66a1fc7217fa"

# Claude Code CLI yolu (VS Code extension)
_CLAUDE_CANDIDATES = [
    Path.home() / ".vscode/extensions/anthropic.claude-code-2.1.126-win32-x64/resources/native-binary/claude.exe",
    Path.home() / ".vscode/extensions/anthropic.claude-code-2.1.120-win32-x64/resources/native-binary/claude.exe",
    Path.home() / "AppData/Roaming/Claude/claude-code/2.1.119/claude.exe",
]
CLAUDE_EXE = next((str(p) for p in _CLAUDE_CANDIDATES if p.exists()), "claude")

# NotebookLM source IDs
SOURCES = {
    "teknik": [
        "86566c16-e745-4ddc-98eb-43a420f50f40",  # Bloom Taksonomisi 1
        "0c57eec7-8598-4a86-8031-b7bdcad7020f",  # Bloom Taksonomisi 2
    ],
    "ornek": [
        "e63bf929-64c3-40e1-8174-f4cb8591d373",  # 1_1.pdf
        "17bd0c8e-a34e-4984-be1e-372da9ba9225",  # 2.pdf
        "87624143-8b9b-4e9d-b03f-e21b9143ab4b",  # 3.pdf
        "a04410f0-5ee5-4cfa-99d4-0ed1920b077d",  # 4.pdf
        "cabe62e0-5fa5-4a33-bbd0-d973e2aaa188",  # 5.pdf
        "bc29648b-d78e-4c69-af93-9231529f743c",  # 6.pdf
        "69557a22-6725-4562-8cca-5a43ceb5970c",  # lgs_matematik.pdf
    ]
}

_claude_soru_notebook_id = None


def get_or_create_claude_soru_notebook():
    global _claude_soru_notebook_id
    if _claude_soru_notebook_id:
        return _claude_soru_notebook_id

    result = subprocess.run(
        [NOTEBOOKLM, "list", "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    try:
        data = json.loads(result.stdout)
        for nb in data.get("notebooks", []):
            if nb["title"] == "Claude_soru":
                _claude_soru_notebook_id = nb["id"]
                return _claude_soru_notebook_id
    except Exception:
        pass

    result = subprocess.run(
        [NOTEBOOKLM, "create", "Claude_soru"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    # Parse ID from output like: "Created notebook: <id>"
    match = re.search(r"([0-9a-f-]{36})", result.stdout + result.stderr)
    if match:
        _claude_soru_notebook_id = match.group(1)
    return _claude_soru_notebook_id


def nlm_ask(soru, source_ids=None):
    subprocess.run(
        [NOTEBOOKLM, "use", SORU_YAZMA_NOTEBOOK],
        capture_output=True, encoding="utf-8"
    )
    cmd = [NOTEBOOKLM, "ask", soru]
    if source_ids:
        for sid in source_ids:
            cmd += ["-s", sid]
    result = subprocess.run(
        cmd, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60
    )
    output = result.stdout
    if "Answer:" in output:
        output = output.split("Answer:", 1)[1].strip()
    return output


def generate_with_claude(prompt):
    result = subprocess.run(
        [CLAUDE_EXE, "-p", prompt],
        input="",
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120
    )
    return result.stdout.strip()


def build_pdf(soru_data, kazanimlar, zorluk, konu_adi):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    safe_konu = re.sub(r'[^\w\s-]', '', konu_adi, flags=re.UNICODE).strip().replace(' ', '_')
    filename = f"{safe_konu}_{zorluk}.pdf"
    filepath = OUTPUT_DIR / filename

    doc = SimpleDocTemplate(str(filepath), pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    normal = ParagraphStyle('normal', fontName='Helvetica', fontSize=11, leading=16)
    bold = ParagraphStyle('bold', fontName='Helvetica-Bold', fontSize=11, leading=16)
    header = ParagraphStyle('header', fontName='Helvetica-Bold', fontSize=13, leading=18, spaceAfter=6)
    small = ParagraphStyle('small', fontName='Helvetica', fontSize=9, leading=13, textColor=colors.grey)

    story = []

    story.append(Paragraph("8. Sınıf Matematik – Çoktan Seçmeli Soru", header))
    story.append(Paragraph(f"Konu: {konu_adi}  |  Zorluk: {zorluk}  |  Tarih: {datetime.now().strftime('%d.%m.%Y')}", small))
    story.append(Spacer(1, 0.4*cm))

    kazanim_kodlari = ", ".join([k["kod"] for k in kazanimlar])
    story.append(Paragraph(f"Kazanımlar: {kazanim_kodlari}", small))
    story.append(Paragraph(f"Bloom Seviyesi: {soru_data.get('bloom_seviyesi', '')}", small))
    story.append(Spacer(1, 0.6*cm))

    story.append(Paragraph(f"<b>Soru:</b> {soru_data['soru']}", normal))
    story.append(Spacer(1, 0.4*cm))

    for harf, metin in soru_data['secenekler'].items():
        story.append(Paragraph(f"<b>{harf})</b> {metin}", normal))

    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph(f"<b>Doğru Cevap:</b> {soru_data['dogru_cevap']}", bold))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"<i>Açıklama: {soru_data.get('aciklama', '')}</i>", small))

    doc.build(story)
    return filepath, filename


def save_to_notebooklm(filepath, filename):
    notebook_id = get_or_create_claude_soru_notebook()
    if not notebook_id:
        return False, "Claude_soru notebook oluşturulamadı"

    subprocess.run(
        [NOTEBOOKLM, "use", notebook_id],
        capture_output=True, encoding="utf-8"
    )
    result = subprocess.run(
        [NOTEBOOKLM, "source", "add", str(filepath)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60
    )
    success = result.returncode == 0
    return success, result.stdout + result.stderr


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/kazanimlar")
def get_kazanimlar():
    with open(BASE_DIR / "kazanimlar.json", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json
    secili_kazanimlar = data.get("kazanimlar", [])
    zorluk = data.get("zorluk", "Orta")
    konu_adi = data.get("konu_adi", "Karma")

    if not secili_kazanimlar:
        return jsonify({"error": "En az bir kazanım seçin"}), 400

    # 1. NotebookLM'den örnek sorular + teknik al
    kazanim_listesi = "\n".join([f"- {k['kod']}: {k['metin']}" for k in secili_kazanimlar])
    konular_str = ", ".join(set([k.get("konu", "") for k in secili_kazanimlar]))

    try:
        ornek_sorular = nlm_ask(
            f"Bu kazanımlarla ilgili örnek çoktan seçmeli sorular ver: {konular_str}. Kazanımlar: {', '.join([k['kod'] for k in secili_kazanimlar])}",
            source_ids=SOURCES["ornek"][:3]
        )
        yazim_teknigi = nlm_ask(
            "Bağlam temelli çoktan seçmeli matematik sorusu yazım teknikleri ve Bloom taksonomisine göre soru hazırlama kuralları nelerdir? Kısa özetle.",
            source_ids=SOURCES["teknik"]
        )
    except Exception as e:
        ornek_sorular = ""
        yazim_teknigi = ""

    # 2. Claude ile soru üret
    prompt = f"""Sen bir 8. sınıf matematik soru yazma uzmanısın.
Türkiye Milli Eğitim Bakanlığı müfredatına göre, Bloom taksonomisine uygun, bağlam temelli 1 adet çoktan seçmeli soru yaz.

SEÇİLİ KAZANIMLAR:
{kazanim_listesi}

ZORLUK DERECESİ: {zorluk}
(Kolay: tek adım, doğrudan kazanım; Orta: birleştirici, çok adım; Zor: bağlamsal, karmaşık)

ÖRNEK SORULAR (referans için):
{ornek_sorular[:1500] if ornek_sorular else "Yok"}

SORU YAZIM İLKELERİ:
{yazim_teknigi[:800] if yazim_teknigi else "Yok"}

KURALLAR:
- Tam olarak 4 şık (A, B, C, D)
- Tek ve net doğru cevap
- Seçili kazanımların HEPSİNİ kapsayan bütünleşik soru
- Günlük hayat bağlamı kullanılabilir
- Şıklar birbirine yakın değerde, ayırt edici olmalı

SADECE aşağıdaki JSON formatında yanıt ver, başka hiçbir şey yazma:
{{
  "soru": "Soru metni",
  "secenekler": {{
    "A": "Şık A",
    "B": "Şık B",
    "C": "Şık C",
    "D": "Şık D"
  }},
  "dogru_cevap": "A",
  "aciklama": "Neden bu şık doğru, kısa açıklama",
  "bloom_seviyesi": "Uygulama"
}}"""

    try:
        raw = generate_with_claude(prompt)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Claude zaman aşımı, tekrar deneyin"}), 504
    except Exception as e:
        return jsonify({"error": f"Claude çağrısı başarısız: {str(e)}"}), 500

    # 3. JSON parse
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return jsonify({"error": "Geçerli JSON bulunamadı", "raw": raw}), 500
        soru_data = json.loads(raw[start:end])
    except json.JSONDecodeError as e:
        return jsonify({"error": f"JSON parse hatası: {str(e)}", "raw": raw}), 500

    # 4. PDF oluştur
    try:
        filepath, filename = build_pdf(soru_data, secili_kazanimlar, zorluk, konu_adi)
    except Exception as e:
        return jsonify({"error": f"PDF oluşturulamadı: {str(e)}", "soru": soru_data}), 500

    # 5. NotebookLM'e kaydet
    nlm_success, nlm_msg = save_to_notebooklm(filepath, filename)

    # 6. Supabase'e kaydet
    try:
        supabase_data = {
            "soru": soru_data["soru"],
            "secenekler": soru_data["secenekler"],
            "dogru_cevap": soru_data["dogru_cevap"],
            "aciklama": soru_data.get("aciklama", ""),
            "bloom_seviyesi": soru_data.get("bloom_seviyesi", ""),
            "kazanimlar": [k["kod"] for k in secili_kazanimlar],
            "zorluk": zorluk,
            "konu_adi": konu_adi
        }
        supabase.table("sorular").insert(supabase_data).execute()
        soru_data["supabase_kaydedildi"] = True
    except Exception as e:
        soru_data["supabase_kaydedildi"] = False
        soru_data["supabase_hata"] = str(e)

    soru_data["pdf_adi"] = filename
    soru_data["notebooklm_kaydedildi"] = nlm_success
    soru_data["kazanimlar"] = [k["kod"] for k in secili_kazanimlar]
    return jsonify(soru_data)


if __name__ == "__main__":
    print("Soru Agent başlıyor → http://localhost:5000")
    app.run(debug=True, port=5000, use_reloader=False)
