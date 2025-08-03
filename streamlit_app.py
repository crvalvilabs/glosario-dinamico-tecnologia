import streamlit as st

# Simulación de glosario en memoria
if "glossary" not in st.session_state:
    st.session_state.glossary = {
        "Dato": "Unidad mínima de información.",
        "Información": "Conjunto organizado de datos que tiene sentido.",
        "Hardware": "Componentes físicos de un sistema informático.",
        "Telecomunicaciones": "Transmisión de información a distancia.",
        "Arduino": "Plataforma de hardware libre con microcontrolador.",
        "Microprocesador": "Unidad central de procesamiento en un chip.",
        "Microcontrolador": "Chip con CPU, memoria y periféricos integrados."
    }

st.set_page_config(layout="wide", page_title="Glosario Streamlit")

st.markdown(
    "<style> .block-container { padding-top: 2rem; } </style>",
    unsafe_allow_html=True,
)

# Layout principal
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 📚 Términos")
    selected_term = st.radio("Selecciona un término", list(st.session_state.glossary.keys()), label_visibility="collapsed")

with col2:
    st.markdown("### 🔍 Buscar o agregar término")

    search_term = st.text_input("Buscar término...", placeholder="Ej: Arduino")
    definition_area = st.empty()

    if search_term and search_term in st.session_state.glossary:
        definition_area.info(f"**{search_term}**: {st.session_state.glossary[search_term]}")
    elif search_term:
        definition_area.warning("Término no encontrado.")

    st.markdown("---")

    with st.form("add_term_form"):
        new_term = st.text_input("Nuevo término")
        new_def = st.text_area("Definición")
        submitted = st.form_submit_button("Agregar")

        if submitted:
            if new_term and new_def:
                st.session_state.glossary[new_term] = new_def
                st.success(f"Término '{new_term}' agregado correctamente.")
            else:
                st.error("Por favor, complete ambos campos.")

    st.markdown("---")
    st.markdown(f"### 📖 Definición de: {selected_term}")
    st.info(st.session_state.glossary[selected_term])
