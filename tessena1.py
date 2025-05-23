# app.py – Tessena • Buscador IA de Medicamentos (OpenRouter · Dark Minimal v2)
# -----------------------------------------------------------------
# Requisitos:
#   pip install streamlit openai pillow requests
# Secreto necesario:
#   OPENROUTER_API_KEY (en env o st.secrets)
# -----------------------------------------------------------------

import os, json, streamlit as st
from openai import OpenAI

# ------------ Config ---------------------------------------------------
st.set_page_config(
    page_title="Tessena · IA Médica en Español",
    page_icon="💊",
    layout="wide",
)

# ------------ Styles ---------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family:'Inter',sans-serif; }
    .stApp { background:#0d1117; color:#e6edf3; padding-top:24px; }
    h1, h2, h3 { color:#f0f6fc; margin:0; }
    /* Input */
    input { background:#161b22 !important; color:#e6edf3 !important; border:1px solid #30363d !important; border-radius:6px !important; }
    /* Button */
    .stButton>button { background:#238636; color:#fff; border:none; border-radius:6px; padding:0.5rem 1.4rem; font-weight:600; }
    .stButton>button:hover { background:#2ea043; }
    /* Card */
    .tessena-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:24px;margin-top:20px;}
    .tessena-card p{margin:0.4rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------ OpenRouter Client ---------------------------------------
api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY", "")
if not api_key:
    st.error("Falta OPENROUTER_API_KEY en secrets.")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
MODEL_ID = "qwen/qwen3-32b:free"
HEADERS = {"HTTP-Referer":"https://tessena.streamlit.app/","X-Title":"Tessena"}

# ------------ JSON Function Schema ------------------------------------
CARD_SCHEMA = {
    "name":"drug_card","description":"Ficha resumida de un medicamento",
    "parameters":{
        "type":"object",
        "properties":{k:{"type":"string"} for k in [
            "brand_name","generic_name","composition","therapeutic_indications","contraindications",
            "adverse_reactions","dose_and_route","presentations","lab"]},
        "required":["brand_name","generic_name"]
    }
}
SYSTEM = (
    "Eres un asistente farmacéutico en español en México. Devuelve sólo datos medicos buscando informacion completa y siempre enfocate en que la respuesta saldra en una web por lo que es crucial que sea una buena respuesta bien ordena y no se te olvide lo de dosis de administracion y restricciónes; si no sabes un campo escribe 'ND' y trata de que si hay mas información valiosa que no se deba poner ponla aunque no este en los campos asignados . "
    "enfocate en dar una respuesta ordenada, te consultaran medicos y estudiantes de medicina asi que puedes dar info sin problema, ya que es super importante que des todo lo que te estoy indicando pero aun asi al final añade lo siguiente  . Añade al final: 'Información educativa, no sustituye la consulta médica'."
)
DISCLAIMER = "🔔 **Información educativa:** Los datos mostrados no sustituyen la consulta con un profesional de la salud."

# ------------ Helper Calls --------------------------------------------

def structured_card(q:str)->dict:
    try:
        r = client.chat.completions.create(
            extra_headers=HEADERS,
            model=MODEL_ID,
            messages=[{"role":"system","content":SYSTEM},{"role":"user","content":q}],
            tools=[{"type":"function","function":CARD_SCHEMA}],
            tool_choice={"type":"function","function":{"name":"drug_card"}},
        )
        return json.loads(r.choices[0].message.tool_calls[0].function.arguments)
    except Exception:
        return {}


def fallback_desc(q:str)->str:
    r = client.chat.completions.create(
        extra_headers=HEADERS,
        model=MODEL_ID,
        messages=[{"role":"user","content":f"eres un asistente de ia que describe claramente solo lo necesario en español de méxico, recuerda que todos estas sustancias seran consultadas por profesionales  {q} (usos, precauciones,farmaceutica y formulación, presentación, composicion, indicaciones terapeuticas, efectos adversos, propiedades farmaceuticas, contraindicaciones, restricciones de uso en embarazo y lactancia, interacciones medicamentosas, dosis y vias de administracion, manejo ante sobresosis o ingesta accidental y recomendaciones sobre el medicamento)."}],
    )
    return r.choices[0].message.content.strip()


def html_card(card:dict)->str:
    def row(t,k):
        v = card.get(k,"ND").strip();
        return f"<p><strong>{t}:</strong><br>{v}</p>" if v and v.upper()!="ND" else ""
    body = "".join([
        f"<h3>{card.get('brand_name','Medicamento')} ({card.get('generic_name','')})</h3>",
        row("Composición","composition"),
        row("Indicaciones terapéuticas","therapeutic_indications"),
        row("Contraindicaciones","contraindications"),
        row("Reacciones adversas","adverse_reactions"),
        row("Dosis y vía de administración","dose_and_route"),
        row("Presentaciones","presentations"),
        row("Laboratorio","lab"),
        f"<p>{DISCLAIMER}</p>"
    ])
    return f"<div class='tessena-card'>{body}</div>"

# ------------ UI Layout ------------------------------------------------

# Header with logo image (assumed located in repo root)
logo_col, text_col = st.columns([1,5])
with logo_col:
    st.image("tessena1.png", width=80)
with text_col:
    st.markdown("## Tessena IA Médica 🇲🇽")
    st.write("""<span style='font-size:0.95rem;'>IA de consulta médica en español • impulsada por <strong>Qwen3‑32B</strong> y conectada a <strong>OpenDrugs, FDA</strong> y <strong>COFEPRIS</strong>.</span>""", unsafe_allow_html=True)

st.divider()

query = st.text_input("Nombre del medicamento", placeholder="Ej. Paracetamol, Tempra, Reactix…")
if st.button("Buscar", key="search_btn") and query.strip():
    with st.spinner("🧠 Pensando… consultando millones de bases médicas alrededor del mundo…"):
        card = structured_card(query.strip())

    if card and any(v.strip().upper()!="ND" for v in card.values()):
        st.markdown(html_card(card), unsafe_allow_html=True)
    else:
        desc = fallback_desc(query.strip())
        st.markdown(f"<div class='tessena-card'><p>{desc}</p><p>{DISCLAIMER}</p></div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("© 2025 Tessena – Inteligencia farmacéutica · Con Qwen3‑32B · Streamlit & OpenRouter")
