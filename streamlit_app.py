"""import streamlit as st
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
# Emoji separado
st.markdown("""
<div style='text-align:center; font-size: 2.5rem;'>📖</div>
""", unsafe_allow_html=True)

# Título con degradado
st.markdown("""
<div class='glossary-title'>
    Glosario Tecnológico
</div>
""", unsafe_allow_html=True)

# Línea separadora
st.markdown("<hr>", unsafe_allow_html=True)

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
""", unsafe_allow_html=True)"""

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

# --- Título completamente limpio ---
st.markdown("# 📖 Glosario Tecnológico", unsafe_allow_html=False)

# Línea separadora
st.markdown("<div style='height: 2px; background: linear-gradient(90deg, transparent, #7ED321, transparent); margin: 2rem 0;'></div>", unsafe_allow_html=True)

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

# === TABS PRINCIPALES con mejor estilo ===
tab1, tab2, tab3 = st.tabs(["📚 Ver glosario", "➕ Añadir término", "✖️ Eliminar término"])

# === TAB 1: Ver glosario ===
with tab1:
    data = load_glosario(dummy=st.session_state.glosario_version)

    if st.session_state.modo_detalle:
        # Mostrar título y definición sin emojis en HTML
        st.markdown("### 📖 Detalle del término")
        st.markdown(f"""
        <div class='card' style='margin: 2rem 0;'>
            <h2 style='color: #2D3748; margin-bottom: 1rem;'>{st.session_state.detalle_termino}</h2>
            <p style='text-align: justify; line-height: 1.6; color: #4A5568;'>{st.session_state.detalle_definicion}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔙 Volver", type="primary"):
            st.session_state.modo_detalle = False
            st.rerun()

    else:
        # Buscador mejorado
        st.markdown("### 🔍 Buscar términos")
        search = st.text_input(
            label="Buscar término:", 
            placeholder="Ej: microprocesador, dato, hardware...",
            label_visibility="collapsed"
        )

        filtered = data[data["TERMINO"].str.contains(search, case=False, na=False)] if search.strip() else data

        if filtered.empty:
            st.markdown("""
            <div class='card' style='text-align: center; padding: 3rem;'>
                <h3 style='color: #68D391;'>Sin resultados</h3>
                <p>No se encontraron resultados para esa búsqueda.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"### 📚 Términos encontrados ({len(filtered)})")
            
            col1, col2, col3 = st.columns(3)

            for idx, row in enumerate(filtered.iterrows()):
                _, row = row
                target_col = [col1, col2, col3][idx % 3]
                with target_col:
                    # Card mejorada con hover y mejor diseño
                    st.markdown(
                        f"""
                        <div class='card' style='margin-bottom: 1.5rem; min-height: 200px;'>
                            <h4 style='color: #2D3748; margin-bottom: 1rem; font-weight: 700;'>{row["TERMINO"]}</h4>
                            <p style='color: #4A5568; line-height: 1.5; margin-bottom: 1.5rem;'>{row["DEFINICION"][:120]}...</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("Ver más", key=f"vermas_{idx}", type="primary", use_container_width=True):
                        st.session_state.modo_detalle = True
                        st.session_state.detalle_termino = row["TERMINO"]
                        st.session_state.detalle_definicion = row["DEFINICION"]
                        st.rerun()

# === TAB 2: Añadir términos ===
with tab2:
    st.markdown("### ➕ Añadir nuevo término")
    
    # Formulario con mejor estilo
    st.markdown("""
    <div class='card' style='margin: 2rem 0;'>
        <h4 style='color: #2D3748; margin-bottom: 1.5rem;'>Información del término</h4>
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_add_term"):
        nuevo_termino = st.text_input(
            "✏️ Nombre del término", 
            placeholder="Ej: Inteligencia Artificial",
            key="nuevo_termino_input"
        )
        nueva_definicion = st.text_area(
            "📝 Definición", 
            placeholder="Escribe una definición clara y breve del término...",
            key="nueva_definicion_input",
            height=150
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            guardar = st.form_submit_button(
                "💾 Guardar término", 
                type="primary",
                use_container_width=True
            )

        if guardar:
            if not nuevo_termino.strip() or not nueva_definicion.strip():
                st.warning("⚠️ Por favor completa ambos campos.")
                st.stop()

            if validate_term(nuevo_termino.strip()):
                st.error("⛔ El término ya existe en el glosario.")
                st.stop()

            try:
                insert_term(nuevo_termino.strip(), nueva_definicion.strip())
                st.success(f"✅ '{nuevo_termino}' fue añadido correctamente.")
                load_glosario.clear()
                st.session_state.glosario_version += 1
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al guardar el término: {e}")
                
# === TAB 3: Eliminar términos ===
with tab3:
    st.markdown("### 🗑️ Eliminar términos")
    
    data = load_glosario(dummy=st.session_state.glosario_version)
    
    if data.empty:
        st.markdown("""
        <div class='card' style='text-align: center; padding: 3rem;'>
            <h3 style='color: #68D391;'>Glosario vacío</h3>
            <p>No hay términos en el glosario para eliminar.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='card' style='margin: 2rem 0;'>
            <h4 style='color: #2D3748; margin-bottom: 1.5rem;'>Selecciona los términos a eliminar</h4>
            <p style='color: #E53E3E; font-size: 0.9rem;'>Esta acción no se puede deshacer.</p>
        </div>
        """, unsafe_allow_html=True)
        
        opciones = data["TERMINO"].tolist()
        seleccion = st.multiselect(
            "Términos disponibles:", 
            opciones,
            placeholder="Busca y selecciona términos..."
        )

        if seleccion:
            st.markdown(f"""
            <div class='card' style='background-color: #FED7D7; border-left: 4px solid #E53E3E;'>
                <p><strong>Términos seleccionados para eliminar:</strong></p>
                <ul>
                    {''.join([f'<li>{term}</li>' for term in seleccion])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                confirmar = st.button(
                    f"❌ Eliminar {len(seleccion)} término(s)", 
                    type="primary",
                    use_container_width=True
                )
                
            if confirmar:
                try:
                    delete_terms(seleccion)
                    st.success(f"✅ {len(seleccion)} término(s) eliminado(s) correctamente.")
                    load_glosario.clear()
                    st.session_state.glosario_version += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al eliminar términos: {e}")

# --- Footer mejorado ---
st.markdown("""
<div style='margin-top: 4rem;'>
    <div style='height: 2px; background: linear-gradient(90deg, transparent, #7ED321, transparent); margin: 2rem 0;'></div>
    <div class='card' style='text-align: center; background: rgba(126, 211, 33, 0.05);'>
        <p style='margin: 0; color: #4A5568; font-size: 0.9rem;'>
            Desarrollado con amor por <strong style='color: #7ED321;'>IA Visionaria 2025</strong>
        </p>
    </div>
</div>
""", unsafe_allow_html=True)
