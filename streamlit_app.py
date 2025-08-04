import streamlit as st
import pandas as pd
from snowflake.snowpark.functions import col

# --- Configuración general ---
st.set_page_config(page_title="Glosario Dinámico", layout="wide")

# --- Título ---
st.markdown("<h1 style='text-align:center;'>📘 Glosario Dinámico</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# --- Conexión a Snowflake ---
@st.cache_resource
def get_session():
    return st.connection("snowflake").session()

session = get_session()

# --- Cargar glosario desde Snowflake ---
@st.cache_data(ttl=60)
def load_glosario():
    df = session.table("glosario").select(col("termino"), col("definicion"))
    return df.to_pandas()

# --- Insertar nuevo término ---
def insert_term(term, definition):
    session.sql(f"""
        INSERT INTO glosario (termino, definicion)
        VALUES ('{term}', '{definition}')
    """).collect()

# --- Eliminar términos ---
def delete_terms(terminos):
    for term in terminos:
        session.sql(f"DELETE FROM glosario WHERE termino = '{term}'").collect()

# --- Estado para detalle ---
if "modo_detalle" not in st.session_state:
    st.session_state.modo_detalle = False

# --- Tabs ---
tab1, tab2 = st.tabs(["📚 Ver glosario", "➕/🗑 Añadir/Eliminar término"])

# === TAB 1: Ver glosario / Detalle ===
with tab1:
    data = load_glosario()

    if st.session_state.modo_detalle:
        st.markdown("### 📖 Detalle del término")
        st.markdown(f"#### {st.session_state.detalle_termino}")
        st.markdown(f"<p style='text-align:justify;'>{st.session_state.detalle_definicion}</p>", unsafe_allow_html=True)

        if st.button("🔙 Volver"):
            st.session_state.modo_detalle = False
            st.rerun()

    else:
        search = st.text_input("🔍 Buscar término:")

        if search.strip():
            filtered = data[data["TERMINO"].str.contains(search, case=False, na=False)]
        else:
            filtered = data

        if filtered.empty:
            st.warning("No se encontraron resultados para esa búsqueda.")
        else:
            col1, col2, col3 = st.columns(3)

            for idx, row in enumerate(filtered.iterrows()):
                i, row = row
                col = [col1, col2, col3][idx % 3]
                with col:
                    st.markdown(
                        f"""
                        <div style='border:1px solid #ddd; border-radius:10px; padding:15px; margin:10px; background-color:#f9f9f9;'>
                            <h4>{row["TERMINO"]}</h4>
                            <p>{row["DEFINICION"][:120]}...</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("Ver más", key=f"vermas_{idx}"):
                        st.session_state.modo_detalle = True
                        st.session_state.detalle_termino = row["TERMINO"]
                        st.session_state.detalle_definicion = row["DEFINICION"]
                        st.rerun()

# === TAB 2: Añadir / Eliminar ===
with tab2:
    st.subheader("🛠 Añadir o eliminar término del glosario")
    modo = st.radio("Selecciona una acción:", ["➕ Añadir", "🗑 Eliminar"], horizontal=True)

    if modo == "➕ Añadir":
        if "nuevo_termino" not in st.session_state:
            st.session_state.nuevo_termino = ""
        if "nueva_definicion" not in st.session_state:
            st.session_state.nueva_definicion = ""

        with st.form("form_add_term"):
            nuevo_termino = st.text_input("Término", value=st.session_state.nuevo_termino, key="nuevo_termino_input")
            nueva_definicion = st.text_area("Definición", value=st.session_state.nueva_definicion, key="nueva_definicion_input")
            guardar = st.form_submit_button("💾 Guardar término")
    
            if guardar:
                if nuevo_termino.strip() and nueva_definicion.strip():
                    insert_term(nuevo_termino.strip(), nueva_definicion.strip())
                    st.success(f"✅ '{nuevo_termino}' fue añadido correctamente.")
                    # Limpiar inputs
                    st.session_state.nuevo_termino = ""
                    st.session_state.nueva_definicion = ""
                    load_glosario.clear()
                    st.rerun()
                else:
                    st.error("❌ Ambos campos son obligatorios.")

    elif modo == "🗑 Eliminar":
        data = load_glosario()
        opciones = data["TERMINO"].tolist()
        seleccion = st.multiselect("Selecciona término(s) a eliminar:", opciones)

        if seleccion:
            confirmar = st.button("🗑 Eliminar término(s) seleccionados")
            if confirmar:
                delete_terms(seleccion)
                st.success("✅ Término(s) eliminado(s) correctamente.")
                load_glosario.clear()
                st.rerun()
