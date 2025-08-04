import streamlit as st
import pandas as pd
from datetime import datetime
from snowflake.snowpark.functions import col

# --- Cargar CSS externo ---
def load_local_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_local_css("assets/style.css")

# --- Configuración general ---
st.set_page_config(page_title="Glosario Tecnológico", layout="wide")

# --- Inicializar contador de versión para forzar recarga del caché ---
if "glosario_version" not in st.session_state:
    st.session_state.glosario_version = 0

# --- Título ---
# st.markdown("<h1 style='text-align:center;'>📖 Glosario Tecnológico</h1>", unsafe_allow_html=True)
# st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<h1 class='glossary-title'>📖 Glosario Tecnológico</h1>", unsafe_allow_html=True)

# --- Conexión a Snowflake ---
@st.cache_resource
def get_session():
    return st.connection("snowflake").session()

session = get_session()

# --- Cargar glosario desde Snowflake con control de versión ---
@st.cache_data(ttl=300)
def load_glosario(dummy=0):
    try:
        df = session.table("glosario").select(col("termino"), col("definicion"))
        return df.to_pandas()
    except Exception as e:
        load_glosario.clear()
        st.error("❌ Error al cargar datos desde Snowflake.")
        st.exception(e)
        return pd.DataFrame(columns=["termino", "definicion"])

# --- Validación de existencia de un término
def validate_term(term):
    query = f"SELECT 1 FROM GLOSARIO_DB.PUBLIC.GLOSARIO WHERE TERMINO = '{term}'"
    result = session.sql(query).collect()
    return len(result) > 0
    
# --- Insertar nuevo término (seguro con Snowpark) ---
def insert_term(term, definition):
    df = session.create_dataframe([[term, definition]], schema=["termino", "definicion"])
    df.write.mode("append").save_as_table("glosario")

# --- Eliminar múltiples términos de una vez (seguro y eficiente) ---
def delete_terms(terminos):
    if not terminos:
        return
    for term in terminos:
        session.sql("DELETE FROM glosario WHERE termino = :1", params=[term]).collect()

# --- Estado para vista de detalle ---
if "modo_detalle" not in st.session_state:
    st.session_state.modo_detalle = False

# === TABS PRINCIPALES ===
tab1, tab2, tab3 = st.tabs(["📚 Ver glosario", "➕ Añadir término", "✖️ Eliminar término"])

# === TAB 1: Ver glosario ===
with tab1:
    data = load_glosario(dummy=st.session_state.glosario_version)

    if st.session_state.modo_detalle:
        st.markdown("### 📖 Detalle del término")
        st.markdown(f"#### {st.session_state.detalle_termino}")
        st.markdown(f"<p style='text-align:justify;'>{st.session_state.detalle_definicion}</p>", unsafe_allow_html=True)

        if st.button("🔙 Volver", type="tertiary"):
            st.session_state.modo_detalle = False
            st.rerun()

    else:
        search = st.text_input(label="🔍 Buscar término:", placeholder="Ej: microprocesador, dato, hardware...")

        filtered = data[data["TERMINO"].str.contains(search, case=False, na=False)] if search.strip() else data

        if filtered.empty:
            st.warning("No se encontraron resultados para esa búsqueda.")
        else:
            col1, col2, col3 = st.columns(3)

            for idx, row in enumerate(filtered.iterrows()):
                _, row = row
                target_col = [col1, col2, col3][idx % 3]
                with target_col:
                    st.markdown(
                        f"""
                        <div class='card'>
                            <h4>{row["TERMINO"]}</h4>
                            <p>{row["DEFINICION"][:120]}...</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("Ver más", key=f"vermas_{idx}", type="tertiary"):
                        st.session_state.modo_detalle = True
                        st.session_state.detalle_termino = row["TERMINO"]
                        st.session_state.detalle_definicion = row["DEFINICION"]
                        st.rerun()

# === TAB 2: Añadir o eliminar términos ===
with tab2:
    st.subheader("📄 Añadir término al glosario")

    with st.form("form_add_term"):
        nuevo_termino = st.text_input("✏️ Nombre del nuevo término", placeholder="Ej: Inteligencia Artificial", key="nuevo_termino_input")
        nueva_definicion = st.text_area("📝 Definición", placeholder="Escribe una definición clara y breve del término...", key="nueva_definicion_input")
        guardar = st.form_submit_button("💾 Guardar término", type="secondary")

        if guardar:
            if not nuevo_termino.strip() or not nueva_definicion.strip():
                st.warning("⚠️ Por favor completa ambos campos.")
                st.stop()

            if validate_term(nuevo_termino.strip()):
                st.error("⛔ El término ya existe en el glosario.")
                st.stop()

            insert_term(nuevo_termino.strip(), nueva_definicion.strip())
            st.success(f"✅ '{nuevo_termino}' fue añadido correctamente.")
            load_glosario.clear()
            st.session_state.glosario_version += 1
            st.rerun()
                
# === TAB 3: Eliminar términos ===
with tab3:
        st.subheader("🗑️ Eliminar término del glosario")
    
        data = load_glosario(dummy=st.session_state.glosario_version)
        opciones = data["TERMINO"].tolist()
        seleccion = st.multiselect("Selecciona término(s) a eliminar:", opciones)

        if seleccion:
            confirmar = st.button("❌ Eliminar término(s) seleccionados", type="secondary")
            if confirmar:
                delete_terms(seleccion)
                st.success(f"✅ '{nuevo_termino}' eliminado correctamente.")
                load_glosario.clear()
                st.session_state.glosario_version += 1
                st.rerun()

# --- Footer ---
st.markdown("""
<hr style='margin-top: 4rem;'>
<div style='text-align:center; color:#6c757d; font-size:0.9rem;'>
    Developed by <strong>IA Visionaria 2025</strong>
</div>
""", unsafe_allow_html=True)
