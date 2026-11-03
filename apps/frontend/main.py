import streamlit as st
import requests
import time
import csv
import io
import random
from fpdf import FPDF

# ==========================================
# CONFIGURACIÓN Y ESTADO DE LA SESIÓN
# ==========================================
API_BASE = "http://localhost:8000/api"
TIMEOUT_SECONDS = 5 * 60  # 5 minutos de inactividad global

st.set_page_config(page_title="Almacén CFE", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Inicializar variables de sesión
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "last_activity" not in st.session_state:
    st.session_state.last_activity = time.time()

# Verificación de Timeout Global
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > TIMEOUT_SECONDS:
        st.session_state.logged_in = False
        st.warning("Su sesión expiró por inactividad. Inicie sesión de nuevo.")
        st.rerun()
    else:
        st.session_state.last_activity = time.time()


# ==========================================
# FUNCIONES DE DATOS Y CONEXIÓN
# ==========================================
def get_articulos():
    try:
        return [
            {"id_articulo": 1, "nombre": "Cable de cobre 12 AWG", "codigo_barras": "7501001"},
            {"id_articulo": 2, "nombre": "Transformador 25 kVA", "codigo_barras": "7501002"},
            {"id_articulo": 3, "nombre": "Poste de concreto 12 m", "codigo_barras": "7501003"},
            {"id_articulo": 4, "nombre": "Desarmador Phillips", "codigo_barras": "7501004"}
        ]
    except Exception as e:
        return []


def api_post(endpoint, payload):
    return True, "Operación registrada correctamente."


def generar_csv(tipo_reporte):
    output = io.StringIO()
    writer = csv.writer(output)

    if tipo_reporte == "Existencias actuales":
        writer.writerow(['ID Articulo', 'Nombre', 'Codigo de Barras', 'Existencia (Unidades)'])
        for a in get_articulos():
            writer.writerow([a['id_articulo'], a['nombre'], a['codigo_barras'], random.randint(10, 150)])
    else:
        writer.writerow(['Fecha', 'Movimiento', 'Articulo', 'Cantidad', 'RPE / Usuario'])
        writer.writerow(['2026-10-25', 'Entrada', 'Transformador 25 kVA', 5, 'Admin'])
        writer.writerow(['2026-10-26', 'Salida', 'Desarmador Phillips', 1, '94182'])
    return output.getvalue()


def generar_pdf(tipo_reporte):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=f"Almacen CFE - {tipo_reporte}", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 10)

    if tipo_reporte == "Existencias actuales":
        encabezados = ['ID', 'Nombre del Articulo', 'Cod. Barras', 'Unidades']
        anchos = [15, 110, 35, 30]

        for i in range(len(encabezados)):
            pdf.cell(anchos[i], 10, encabezados[i], border=1, align='C')
        pdf.ln()

        pdf.set_font("Arial", '', 10)
        for a in get_articulos():
            pdf.cell(anchos[0], 10, str(a['id_articulo']), border=1, align='C')
            pdf.cell(anchos[1], 10, str(a['nombre']), border=1)
            pdf.cell(anchos[2], 10, str(a['codigo_barras']), border=1, align='C')
            pdf.cell(anchos[3], 10, str(random.randint(10, 150)), border=1, align='C')
            pdf.ln()

    else:
        encabezados = ['Fecha', 'Movimiento', 'Articulo', 'Cant.', 'RPE / Usr']
        anchos = [25, 25, 90, 15, 35]

        for i in range(len(encabezados)):
            pdf.cell(anchos[i], 10, encabezados[i], border=1, align='C')
        pdf.ln()

        pdf.set_font("Arial", '', 10)
        movimientos = [
            ['2026-10-25', 'Entrada', 'Transformador 25 kVA', '5', 'Admin'],
            ['2026-10-26', 'Salida', 'Desarmador Phillips', '1', '94182']
        ]
        for m in movimientos:
            for i in range(len(m)):
                align = 'L' if i == 2 else 'C'
                pdf.cell(anchos[i], 10, m[i], border=1, align=align)
            pdf.ln()

    return pdf.output(dest='S').encode('latin-1')


# ==========================================
# POP-UP DE DESCARGA DIRECTA
# ==========================================
@st.dialog("📄 Reporte Generado")
def modal_descarga_reporte(csv_data, pdf_data, base_filename):
    st.success("¡El reporte se ha procesado exitosamente!")

    st.download_button(
        label="⬇️ Descargar en formato CSV",
        data=csv_data,
        file_name=f"{base_filename}.csv",
        mime="text/csv",
        use_container_width=True,
        type="primary"
    )

    st.download_button(
        label="⬇️ Descargar en formato PDF",
        data=pdf_data,
        file_name=f"{base_filename}.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="secondary"
    )

    st.divider()
    if st.button("Cerrar ventana", use_container_width=True):
        st.rerun()


# ==========================================
# INTERFAZ DE USUARIO (VISTAS)
# ==========================================
if not st.session_state.logged_in:
    st.title("⚡ Almacén CFE")
    st.subheader("Iniciar sesión")
    with st.form("login_form"):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)

        if submit:
            if usuario and password:
                st.session_state.logged_in = True
                st.session_state.username = usuario
                st.session_state.last_activity = time.time()
                st.rerun()
            else:
                st.error("Por favor, ingrese usuario y contraseña.")
else:
    col_user, col_btn = st.columns([2, 1])
    with col_user:
        st.markdown(f"Hola, **{st.session_state.username}** 👋")
    with col_btn:
        if st.button("🚪 Salir", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()
    st.subheader("¿Qué acción desea realizar?")

    tab_entrega, tab_agregar, tab_eliminar, tab_reportes = st.tabs([
        "👷 Entrega",
        "📦 Agregar",
        "🗑️ Baja",
        "📊 Reportes"
    ])

    articulos_db = get_articulos()
    opciones_articulos = {f"{a['codigo_barras']} - {a['nombre']}": a['id_articulo'] for a in articulos_db}

    # 1. PESTAÑA DE ENTREGA
    with tab_entrega:
        st.info("Registre la salida de herramientas o materiales hacia un empleado.")
        with st.form("form_entrega"):
            seleccion = st.selectbox("Seleccione un artículo", options=list(opciones_articulos.keys()))
            cantidad = st.number_input("Cantidad (unidades)", min_value=1, step=1)
            descripcion = st.text_area("Descripción / Notas (Opcional)")
            rpe = st.text_input("R.P.E. del empleado que recibe")

            if st.form_submit_button("Registrar entrega ✅", type="primary", use_container_width=True):
                if not rpe:
                    st.warning("Debe ingresar el R.P.E. del empleado.")
                else:
                    st.success(f"Entregado: {cantidad} unidad(es) al empleado {rpe}.")

    # 2. PESTAÑA DE AGREGAR
    with tab_agregar:
        st.info("Registre la entrada de nuevo inventario al almacén.")
        with st.form("form_agregar"):
            seleccion = st.selectbox("Seleccione un artículo", options=list(opciones_articulos.keys()), key="sel_add")
            cantidad = st.number_input("Cantidad (unidades)", min_value=1, step=1, key="cant_add")
            descripcion = st.text_area("Descripción / Notas (Opcional)", key="desc_add")

            if st.form_submit_button("Agregar inventario 📥", type="primary", use_container_width=True):
                st.success("Entrada registrada con éxito.")

    # 3. PESTAÑA DE ELIMINAR
    with tab_eliminar:
        st.error("Dar de baja artículos dañados o mermados del inventario.")
        with st.form("form_eliminar"):
            seleccion = st.selectbox("Seleccione un artículo", options=list(opciones_articulos.keys()), key="sel_del")
            cantidad = st.number_input("Cantidad (unidades)", min_value=1, step=1, key="cant_del")
            motivo = st.text_area("Motivo de la baja (Obligatorio)")

            if st.form_submit_button("Eliminar artículo 🗑️", use_container_width=True):
                if not motivo:
                    st.warning("Debe ingresar un motivo.")
                else:
                    st.success("Baja registrada en el sistema.")

        # 4. PESTAÑA DE REPORTES (LIBRE)
        with tab_reportes:
            st.info("Descargue los movimientos o existencias del sistema en CSV o PDF.")

            # Al no usar 'st.form', la interfaz se actualiza al instante al cambiar de opción
            tipo_reporte = st.selectbox("Tipo de Reporte", ["Existencias actuales", "Movimientos mensuales"])

            mes = None
            if tipo_reporte == "Movimientos mensuales":
                mes = st.date_input("Seleccione un día del mes deseado")

            # Usamos st.button en lugar de st.form_submit_button
            if st.button("Generar Reporte 📊", type="primary", use_container_width=True):
                csv_data = generar_csv(tipo_reporte)
                pdf_data = generar_pdf(tipo_reporte)
                nombre_archivo = "inventario" if tipo_reporte == "Existencias actuales" else "movimientos"

                modal_descarga_reporte(csv_data, pdf_data, nombre_archivo)