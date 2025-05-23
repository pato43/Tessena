# app.py – Tessena • Buscador IA de Medicamentos (DeepSeek)
# ---------------------------------------------------
# Requisitos:
#   pip install streamlit openai pillow requests
# Variables de entorno necesarias:
#   DEEPSEEK_API_KEY = "tu‑clave"  (no compartas en código)
# ---------------------------------------------------

import os, json, requests
from io import BytesIO
from PIL import Image
import streamlit as st
from openai import OpenAI  # SDK 1.x compatible también con DeepSeek

# ---------- Configuración general ----------
st.set_page_config(
    page_title="Tessena • Buscador IA de Medicamentos",
    page_icon="💊",
    layout="centered",
)
HERO_IMG_URL = (
    "https://github.com/pato43/Tessena/blob/main/tessena1.png"
)  # cámbialo por la URL definitiva

# Crea el cliente apuntando al endpoint DeepSeek
client = OpenAI(
    api_key=os.getenv("sk-3fcdb61f94df48428f395b7953d6eed2"),
    base_url="https://api.deepseek.com",
)

# ---------- Esquema JSON que el modelo debe rellenar ----------
DRUG_CARD_SCHEMA = {
    "name": "drug_card",
    "description": "Ficha resumida, estilo prospecto, de un medicamento",
    "parameters": {
        "type": "object",
        "properties": {
            "brand_name": {"type": "string", "description": "Nombre comercial"},
            "generic_name": {"type": "string", "description": "Nombre genérico"},
            "composition": {"type": "string", "description": "Principios activos y concentraciones"},
            "therapeutic_indications": {"type": "string"},
            "contraindications": {"type": "string"},
            "adverse_reactions": {"type": "string"},
            "dose_and_route": {"type": "string"},
            "presentations": {"type": "string"},
            "lab": {"type": "string", "description": "Laboratorio o titular del registro"},
        },
        "required": ["brand_name", "generic_name"],
    },
}

DISCLAIMER = (
    "🔔 **Información educativa:** Los datos mostrados no sustituyen la consulta con un profesional de la salud."
)

# ---------- Utilidades ----------

def load_hero(url: str):
    try:
        r = requests.get(url, timeout=10)
        return Image.open(BytesIO(r.content))
    except Exception:
        return None


def call_deepseek(query: str) -> dict:
    """Llama a deepseek-chat y devuelve la ficha estructurada."""

    system_prompt = (
        "Eres un asistente farmacéutico. Contesta únicamente con información que conozcas con alta certeza. "
        "Si no hay datos fiables escribe 'ND'. No prescribas dosis personalizadas. "
        "Al final añade la frase 'Información educativa, no sustituye la consulta médica'."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    resp = client.chat.completions.create(
        model="deepseek-chat",  # o deepseek-reasoner si prefieres el modelo de razonamiento
        messages=messages,
        tools=[{"type": "function", "function": DRUG_CARD_SCHEMA}],
        tool_choice={"type": "function", "function": {"name": "drug_card"}},
        stream=False,
    )

    try:
        args_json = resp.choices[0].message.tool_calls[0].function.arguments
        return json.loads(args_json)
    except Exception:
        return {}


def section(title: str, content: str):
    """Muestra sección plegable solo si hay contenido (y no es ND)."""
    if content and content.upper() != "ND":
        with st.expander(title.capitalize()):
            st.markdown(content)


# ---------- UI ----------

def main():
    # Hero ------------------------------------------------------
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(
            """# Tessena 💊  
            ### Encuentra información confiable de medicamentos al instante""",
            unsafe_allow_html=True,
        )
        st.write(
            "Ingresa el nombre comercial o genérico y obtén un resumen estructurado en segundos."
        )
    with col2:
        img = load_hero(HERO_IMG_URL)
        if img:
            st.image(img, use_column_width=True)

    st.divider()

    # Buscador --------------------------------------------------
    query = st.text_input(
        "Nombre del medicamento", placeholder="Ej. Tempra 500 mg o Paracetamol", key="query"
    )
    col_b, col_c = st.columns([1, 5])
    with col_b:
        search_pressed = st.button("🔍 Buscar")

    if search_pressed and query.strip():
        with st.spinner("Consultando Tessena IA (DeepSeek)…"):
            card = call_deepseek(query)

        if card:
            st.success(
                f"### {card.get('brand_name', 'Medicamento')} ({card.get('generic_name', '')})"
            )
            section("Composición", card.get("composition"))
            section("Indicaciones terapéuticas", card.get("therapeutic_indications"))
            section("Contraindicaciones", card.get("contraindications"))
            section("Reacciones adversas", card.get("adverse_reactions"))
            section("Dosis y vía de administración", card.get("dose_and_route"))
            section("Presentaciones", card.get("presentations"))
            section("Laboratorio", card.get("lab"))
            st.info(DISCLAIMER)
        else:
            st.warning("No se encontró información fiable para esa consulta.")

    # Pie de página -------------------------------------------
    st.divider()
    st.caption(
        "© 2025 Tessena – Proyecto de inteligencia farmacéutica.  |  Made with Streamlit & deepseek‑chat"
    )


if __name__ == "__main__":
    main()
