# app.py – Tessena • Buscador IA de Medicamentos (OpenRouter · Diseño mejorado)
# -----------------------------------------------------------------
# Requisitos:
#   pip install streamlit openai pillow requests
# Variables de entorno necesarias:
#   OPENROUTER_API_KEY = "sk-..."
# -----------------------------------------------------------------

import os, json, requests
from io import BytesIO
from PIL import Image
import streamlit as st
from openai import OpenAI

# ---------- Configuración general ----------
st.set_page_config(
    page_title="Tessena • Buscador IA de Medicamentos",
    page_icon="💊",
    layout="wide",
)

# ---------- Estilos globales ----------
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg,#e5f1ff 0%,#ffffff 100%);
    }
    .tessena-card {
        background: #ffffff;
        border: 1px solid #e1e8ff;
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        margin-top: 8px;
    }
    .stButton>button {
        background-color:#1976D2;
        color:#fff;
        border:none;
        border-radius:8px;
        padding:0.6rem 1.2rem;
        font-weight:600;
        transition:background 0.2s ease;
    }
    .stButton>button:hover {
        background-color:#125ca1;
        color:#fff;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------- Recursos ----------
HERO_IMG_URL = "https://raw.githubusercontent.com/tu-usuario/tessena-assets/main/hero-laptop-stethoscope.png"

# ---------- Cliente OpenRouter ----------
api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY", "")
if not api_key:
    st.error("⚠️ Debes configurar OPENROUTER_API_KEY en tu entorno o en st.secrets.")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://tessena.streamlit.app/",
        "X-Title": "TessenaMedicamentos",
    },
)

# ---------- Schema JSON ----------
DRUG_CARD_SCHEMA = {
    "name": "drug_card",
    "description": "Ficha resumida de un medicamento",
    "parameters": {
        "type": "object",
        "properties": {
            "brand_name": {"type": "string"},
            "generic_name": {"type": "string"},
            "composition": {"type": "string"},
            "therapeutic_indications": {"type": "string"},
            "contraindications": {"type": "string"},
            "adverse_reactions": {"type": "string"},
            "dose_and_route": {"type": "string"},
            "presentations": {"type": "string"},
            "lab": {"type": "string"},
        },
        "required": ["brand_name", "generic_name"],
    },
}

DISCLAIMER = "🔔 **Información educativa:** Los datos mostrados no sustituyen la consulta con un profesional de la salud."

# ---------- Auxiliares ----------

def load_image(url: str):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return Image.open(BytesIO(res.content))
    except Exception:
        return None


def fetch_card(question: str) -> dict:
    system = (
        "Eres un asistente farmacéutico. Responde sólo con datos que conozcas con certeza. Si desconoces un punto, escribe 'ND'. "
        "No prescribas dosis personalizadas. Al final añade la frase 'Información educativa, no sustituye la consulta médica'."
    )

    resp = client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
        tools=[{"type": "function", "function": DRUG_CARD_SCHEMA}],
        tool_choice={"type": "function", "function": {"name": "drug_card"}},
    )

    try:
        args = resp.choices[0].message.tool_calls[0].function.arguments
        return json.loads(args)
    except Exception:
        return {}


def draw_section(title: str, text: str):
    if text and text.strip().upper() != "ND":
        st.markdown(f"**{title}:**  ")
        st.markdown(text)


# ---------- UI ----------

def main():
    col_hero, col_img = st.columns([3, 2])
    with col_hero:
        st.markdown("## Tessena 💊")
        st.markdown("### Encuentra información confiable de medicamentos al instante")
        st.write("Ingresa el nombre comercial o genérico y obtén un resumen estructurado en segundos.")
    with col_img:
        hero = load_image(HERO_IMG_URL)
        if hero:
            st.image(hero, use_column_width=True)

    st.markdown("---")

    query = st.text_input("Nombre del medicamento", placeholder="Ej. Tempra 500 mg o Paracetamol")
    if st.button("🔍 Buscar") and query.strip():
        with st.spinner("Consultando Tessena IA…"):
            card = fetch_card(query.strip())

        if card:
            st.markdown('<div class="tessena-card">', unsafe_allow_html=True)
            st.markdown(f"### {card.get('brand_name','Medicamento')} ({card.get('generic_name','')})")
            draw_section("Composición", card.get("composition"))
            draw_section("Indicaciones terapéuticas", card.get("therapeutic_indications"))
            draw_section("Contraindicaciones", card.get("contraindications"))
            draw_section("Reacciones adversas", card.get("adverse_reactions"))
            draw_section("Dosis y vía de administración", card.get("dose_and_route"))
            draw_section("Presentaciones", card.get("presentations"))
            draw_section("Laboratorio", card.get("lab"))
            st.markdown(DISCLAIMER)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("No se encontró información fiable para esa consulta.")

    st.markdown("---")
    st.caption("© 2025 Tessena – Proyecto de inteligencia farmacéutica | Made with Streamlit & OpenRouter")


if __name__ == "__main__":
    main()
