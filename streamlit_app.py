import streamlit as st
import pandas as pd
from snowflake.snowpark.functions import col

# Configuración inicial
st.set_page_config(page_title="Glosario Dinámico", layout="wide")
st.title("📘 Glosario Dinámico")

# Conexión a Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Función para cargar glosario
@st.cache_data(ttl=60)
def load_glosario():
    df = session.table("glosario").select(col("termino"), col("definicion"))
    return df.to_pandas()

# Función para insertar término
def insert_term(term, definition):
    session.sql(f"""
        INSERT INTO glosario (termino, definicion) 
        VALUES (%s, %s)
    """, params=[term, definition]).collect()

# Función para eliminar términos
def delete_terms(terminos):
    for term in terminos:
        session.sql(f"DELETE FROM glosario WHERE termino = :1", params=[term]).collect()

# Función para resetear inputs
def reset_inputs(keys: list[str]):
    for key in keys:
        if key in st.session_state:
            st.session_state[key] = ""

# Tabs de navegación
tab1, tab2 = st.tabs(["📚 Ver glosario", "➕/🗑 Añadir/Eliminar término"])

# === TAB 1: Visualización del glosario ===
with tab1:
    search = st.text_input("🔍 Buscar término:")

    data = load_glosario()
    if search.strip():
        filtered = data[data["TERMINO"].str.contains(search, case=False, na=False)]
    else:
        filtered = data

    if filtered.empty:
        st.warning("No se encontraron resultados para esa búsqueda.")
    else:
        col1, col2, col3 = st.columns(3)
        for i, row in filtered.iterrows():
            target_col = [col1, col2, col3][i % 3]
            with target_col:
                st.markdown(
                    f"""
                    <div style='border:1px solid #ddd; border-radius:10px; padding:15px; margin:10px; background-color:#f9f9f9;'>
                        <h4>{row['TERMINO']}</h4>
                        <p>{row['DEFINICION'][:120]}...</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# === TAB 2: Añadir o eliminar términos ===
with tab2:
    st.subheader("🛠 Añadir o eliminar término del glosario")
    modo = st.radio("Selecciona una acción:", ["➕ Añadir", "🗑 Eliminar"], horizontal=True)

    if modo == "➕ Añadir":
        with st.form("form_add_term"):
            nuevo_termino = st.text_input("Término", key="nuevo_termino_input")
            nueva_definicion = st.text_area("Definición", key="nueva_definicion_input")
            guardar = st.form_submit_button("💾 Guardar término")

            if guardar:
                if nuevo_termino.strip() and nueva_definicion.strip():
                    insert_term(nuevo_termino.strip(), nueva_definicion.strip())
                    st.success(f"✅ '{nuevo_termino}' fue añadido correctamente.")
                    load_glosario.clear()
                    reset_inputs(["nuevo_termino_input", "nueva_definicion_input"])
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



