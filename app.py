"""
Faktura -> Excel  |  lokální Flask server
Spuštění: python app.py
Pak otevři: http://localhost:5000
"""
import os, re, json, base64
from flask import Flask, request, jsonify, render_template
import anthropic

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

FULL_PROMPT = (
    "Jsi expert na extrakci dat z faktur. Vrať POUZE čisté JSON bez textu, "
    "komentářů ani markdown.\n"
    'Formát: {"dodavatel":"","cislo":"","datum_vystaveni":"DD.MM.YYYY",'
    '"datum_splatnosti":"DD.MM.YYYY","mena":"CZK","polozky":[{"popis":"",'
    '"mnozstvi":1,"jednotka":"ks","cena_kus":0,"sleva":null,"dph_sazba":21,'
    '"celkem_bez_dph":0,"celkem_s_dph":0}]}\n'
    'Pokud faktura nemá rozepsané položky, vlož jednu položku "Celkem". POUZE JSON.'
)

COMPACT_PROMPT = (
    "Extrahuj fakturu do JSON. Zkrať popisy na max 80 znaků. Vrať POUZE JSON.\n"
    'Formát: {"dodavatel":"","cislo":"","datum_vystaveni":"DD.MM.YYYY",'
    '"datum_splatnosti":"DD.MM.YYYY","mena":"CZK","polozky":[{"popis":"",'
    '"mnozstvi":1,"jednotka":"","cena_kus":0,"sleva":null,"dph_sazba":21,'
    '"celkem_bez_dph":0,"celkem_s_dph":0}]}'
)

def parse_robust_json(raw: str) -> dict:
    s = re.sub(r'```json\s*', '', raw, flags=re.IGNORECASE)
    s = re.sub(r'```\s*', '', s).strip()
    m = re.search(r'\{[\s\S]*\}', s)
    if m:
        s = m.group(0)
    s = re.sub(r'//[^\n\r"]*', '', s)
    s = re.sub(r'/\*[\s\S]*?\*/', '', s)
    s = re.sub(r',\s*([\]}])', r'\1', s)
    return json.loads(s)

def call_claude(pdf_b64: str, filename: str, max_tokens: int, prompt: str) -> tuple[str, str]:
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=prompt,
        messages=[{
            "role": "user",
            "content": [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                {"type": "text", "text": f'Extrahuj všechny položky z faktury "{filename}". Vrať pouze JSON.'}
            ]
        }]
    )
    text = next((b.text for b in msg.content if b.type == "text"), "")
    return text, msg.stop_reason

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({"error": "Chybí soubor"}), 400

    f = request.files["file"]
    pdf_bytes = f.read()
    pdf_b64 = base64.b64encode(pdf_bytes).decode()
    filename = f.filename

    try:
        text, stop_reason = call_claude(pdf_b64, filename, 6000, FULL_PROMPT)
        if stop_reason == "max_tokens":
            app.logger.warning(f"{filename}: truncated at 6k, retrying 16k compact")
            text, _ = call_claude(pdf_b64, filename, 16000, COMPACT_PROMPT)

        result = parse_robust_json(text)
        if not isinstance(result.get("polozky"), list):
            result["polozky"] = []
        result["_file"] = filename
        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error processing {filename}: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not client.api_key:
        print("\n⚠️  Nastav API klíč: export ANTHROPIC_API_KEY=sk-ant-...\n")
    port = int(os.environ.get("PORT", 5000))
    print(f"✅  Server běží na http://localhost:{port}")
    app.run(debug=False, host="0.0.0.0", port=port)
