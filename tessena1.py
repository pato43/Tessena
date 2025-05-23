# app.py – Tessena • Buscador IA de Medicamentos (OpenRouter · Dark Mode)
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
from openai import OpenAI, OpenAIError

# ---------- Configuración general ----------
st.set_page_config(
    page_title="Tessena • Buscador IA de Medicamentos",
    page_icon="💊",
    layout="wide",
)

# ---------- Estilos globales (modo oscuro forzado) ----------
DARK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg,#0f2027 0%, #203a43 50%, #2c5364 100%); color:#F9FAFB; }
    h1, h2, h3, h4, h5, h6, p, label { color:#F9FAFB; }
    input, textarea { color:#F9FAFB !important; }
    .tessena-card {
        background:#1F2937; border:1px solid #374151; border-radius:18px;
        padding:24px; box-shadow:0 4px 12px rgba(0,0,0,0.4); margin-top:12px;
    }
    .stButton>button {
        background-color:#00BCD4; color:#011627; border:none; border-radius:8px;
        padding:0.6rem 1.4rem; font-weight:600; transition:background 0.2s;
    }
    .stButton>button:hover { background-color:#0097A7; color:#fff; }
    .stTextInput>div>div>input { background:#111827; color:#F9FAFB;
        border:1px solid #374151; border-radius:8px; }
    .streamlit-expanderHeader { font-weight:600; }
</style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)

# ---------- Recursos ----------
HERO_IMG_URL = "https://raw.githubusercontent.com/tu-usuario/tessena-assets/main/hero-laptop-stethoscope-dark.png"

# ---------- Cliente OpenRouter ----------
api_key = (
    os.getenv("OPENROUTER_API_KEY")
    or os.getenv("OPENAI_API_KEY")  # fallback
    or st.secrets.get("OPENROUTER_API_KEY", "")
)
if not api_key:
    st.error("⚠️ Debes configurar OPENROUTER_API_KEY en tu entorno o en st.secrets.")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
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

# ---------- Utilidades ----------

def load_image(url: str):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return Image.open(BytesIO(res.content))
    except Exception:
        return None


def fetch_card(question: str) -> dict:
    """Consulta OpenRouter y devuelve la ficha estructurada o {}."""
    system_prompt = (
        "Eres un asistente farmacéutico. Responde sólo con información verificada. "
        "Si algún campo no se conoce, escribe 'ND'. No prescribas dosis personalizadas. "
        "Al final añade la frase 'Información educativa, no sustituye la consulta médica'."
    )

    try:
        resp = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://tessena.streamlit.app/",
                "X-Title": "TessenaMedicamentos",
            },
            model="deepseek/deepseek-chat-v3-0324",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            tools=[{"type": "function", "function": DRUG_CARD_SCHEMA}],
            tool_choice={"type": "function", "function": {"name": "drug_card"}},
        )
        return json.loads(resp.choices[0].message.tool_calls[0].function.arguments)
    except OpenAIError as e:
        st.error(f"Error del proveedor: {e}")
        return {}
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        return {}


def draw_section(title: str, text: str):
    if text and text.strip().upper() != "ND":
        st.markdown(f"**{title}:**")
        st.markdown(text)

# ---------- Interfaz ----------

def main():
    col_text, col_img = st.columns([3, 2])
    with col_text:
        st.markdown("## Tessena 💊")
        st.markdown("### Información médica confiable al alcance de tu mano")
        st.write("Busca cualquier medicamento y obtén su ficha resumida al instante.")
    with col_img:
        hero = load_image(HERO_IMG_URL)
        if hero:
            st.image(hero, use_column_width=True)

    st.divider()

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

    st.divider()
    st.caption("© 2025 Tessena – Proyecto de inteligencia farmacéutica | Made with Streamlit & OpenRouter")


if __name__ == "__main__":
    main()
