# app.py – Tessena • Buscador IA de Medicamentos (OpenRouter · Pure Dark)
# -----------------------------------------------------------------
# Requisitos:
#   pip install streamlit openai pillow requests
# Secret necesario (en st.secrets o env):
#   OPENROUTER_API_KEY
# -----------------------------------------------------------------

import os, json, requests
from io import BytesIO
from PIL import Image
import streamlit as st
from openai import OpenAI, OpenAIError

# ---------- Configuración general ----------
st.set_page_config(
    page_title="Tessena • Buscador IA de Medicamentos",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- Estilos (modo oscuro minimal) ----------
DARK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family:'Inter',sans-serif; }
    .stApp { background:#0d1117; color:#e6edf3; }
    h1, h2, h3, h4, h5, h6 { color:#f0f6fc; }

    /* Inputs */
    input, textarea { background:#161b22 !important; color:#e6edf3 !important; border:1px solid #30363d !important; border-radius:6px !important; }

    /* Button */
    .stButton>button { background:#238636; color:#fff; border:none; border-radius:6px; padding:0.5rem 1.2rem; font-weight:600; }
    .stButton>button:hover { background:#2ea043; }

    /* Card */
    .tessena-card { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:20px; margin-top:12px; }
    .tessena-card p { margin-bottom:0.5rem; }

    /* Remove blank container (the previous big input) */
    div[data-testid="stPlaceholder"] { display:none; }
</style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)

# ---------- Recursos ----------
HERO_IMG_URL = "https://github.com/pato43/Tessena/blob/main/tessena1.png"

# ---------- OpenRouter client ----------
api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY", "")
if not api_key:
    st.error("⚠️ Falta OPENROUTER_API_KEY en secretos.")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
MODEL_ID = "deepseek/deepseek-chat-v3-0324"

# ---------- JSON schema ----------
DRUG_CARD_SCHEMA = {
    "name": "drug_card",
    "description": "Ficha resumida de un medicamento",
    "parameters": {
        "type": "object",
        "properties": {
            k: {"type": "string"} for k in [
                "brand_name","generic_name","composition","therapeutic_indications",
                "contraindications","adverse_reactions","dose_and_route",
                "presentations","lab"]
        },
        "required":["brand_name","generic_name"],
    },
}
DISCLAIMER = "🔔 **Información educativa:** Los datos mostrados no sustituyen la consulta con un profesional de la salud."

# ---------- helpers ----------

def load_image(url:str):
    try:
        r = requests.get(url,timeout=10); r.raise_for_status(); return Image.open(BytesIO(r.content))
    except Exception: return None

SYSTEM_PROMPT = (
    "Eres un asistente farmacéutico. Devuelve solo datos confiables. Si desconoces algo, escribe 'ND'. "
    "No prescribas dosis personalizadas. Al final añade la frase 'Información educativa, no sustituye la consulta médica'."
)


def call_structured(q:str)->dict:
    try:
        resp = client.chat.completions.create(
            extra_headers={"HTTP-Referer":"https://tessena.streamlit.app/","X-Title":"Tessena"},
            model=MODEL_ID,
            messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":q}],
            tools=[{"type":"function","function":DRUG_CARD_SCHEMA}],
            tool_choice={"type":"function","function":{"name":"drug_card"}},
        )
        return json.loads(resp.choices[0].message.tool_calls[0].function.arguments)
    except Exception: return {}


def call_free(q:str)->str:
    resp=client.chat.completions.create(
        extra_headers={"HTTP-Referer":"https://tessena.streamlit.app/","X-Title":"Tessena"},
        model=MODEL_ID,
        messages=[{"role":"user","content":f"Describe brevemente el medicamento {q} en español."}],
    )
    return resp.choices[0].message.content.strip()


def show_section(title:str,txt:str):
    if txt and txt.upper()!="ND": st.markdown(f"**{title}:**\n\n{txt}")

# ---------- UI ----------

def main():
    st.markdown("# Tessena 💊")
    st.write("Información médica confiable al alcance de tu mano. Busca un medicamento y obtén su ficha resumida.")

    query = st.text_input("Nombre del medicamento",placeholder="Ej. Paracetamol")
    if st.button("Buscar") and query.strip():
        with st.spinner("Consultando Tessena IA…"):
            card = call_structured(query.strip())

        if card and any(v.strip().upper()!="ND" for v in card.values()):
            st.markdown('<div class="tessena-card">',unsafe_allow_html=True)
            st.markdown(f"### {card.get('brand_name','Medicamento')} ({card.get('generic_name','')})")
            show_section("Composición",card.get("composition"))
            show_section("Indicaciones terapéuticas",card.get("therapeutic_indications"))
            show_section("Contraindicaciones",card.get("contraindications"))
            show_section("Reacciones adversas",card.get("adverse_reactions"))
            show_section("Dosis y vía de administración",card.get("dose_and_route"))
            show_section("Presentaciones",card.get("presentations"))
            show_section("Laboratorio",card.get("lab"))
            st.markdown(DISCLAIMER)
            st.markdown('</div>',unsafe_allow_html=True)
        else:
            st.markdown('<div class="tessena-card">',unsafe_allow_html=True)
            st.markdown(call_free(query.strip()))
            st.markdown(DISCLAIMER)
            st.markdown('</div>',unsafe_allow_html=True)

    st.markdown("---")
    st.caption("© 2025 Tessena – Proyecto de inteligencia farmacéutica · Built with Streamlit & OpenRouter")

if __name__=="__main__":
    main()
