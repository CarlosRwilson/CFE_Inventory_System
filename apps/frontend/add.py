import csv
import io
import sqlite3
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.backend.crud import (
    get_active_users,
    get_article_details,
    get_movement_report,
    get_stock_report,
    register_stock_entry,
    register_stock_exit,
)


def _show_article(article: dict[str, str | int | None]) -> None:
    st.subheader(str(article["nombre"]))
    st.table(
        [
            {
                "Dato": label,
                "Valor": article[key] if article[key] is not None else "No especificado",
            }
            for label, key in (
                ("Código de barras", "codigo_barras"),
                ("Descripción", "descripcion"),
                ("Material", "material"),
                ("Color", "color"),
                ("Medida", "medida"),
                ("Clase", "clase"),
                ("Marca", "marca"),
                ("Existencia", "existencia"),
                ("ID de catálogo", "id_catalogo"),
            )
        ]
    )


def _report_csv(rows: list[dict[str, object]]) -> str:
    output = io.StringIO()
    if not rows:
        return output.getvalue()
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


st.set_page_config(page_title="Almacén CFE Distribución Ensenada", page_icon="⚡", layout="centered")
st.title("Gestión de artíczulos e inventario")

try:
    active_users = get_active_users()
except sqlite3.Error as error:
    st.error(f"No se pudieron cargar los usuarios: {error}")
    active_users = []

user_options = {
    f"{user['rpe']} - {user['nombres']} {user['apellido_paterno'] or ''} "
    f"{user['apellido_materno'] or ''} (ID {user['id_usuario']})": user["id_usuario"]
    for user in active_users
}
user_id = None
if user_options:
    selected_user = st.selectbox("Usuario responsable", list(user_options))
    user_id = user_options[selected_user]
else:
    st.warning("No hay usuarios activos. Las operaciones de inventario no estarán disponibles.")

tab_buscar, tab_entrega, tab_ingreso, tab_baja, tab_reportes = st.tabs(
    ["Buscar artículo", "Entrega", "Ingreso", "Baja", "Reportes"]
)

with tab_buscar:
    with st.form("buscar_articulo"):
        barcode = st.text_input("Código de barras para buscar artículo")
        search_submitted = st.form_submit_button("Buscar")

    if not st.session_state.get("_barcode_autofocus_done"):
        components.html(
            """
            <script>
            window.setTimeout(() => {
                const barcodeInput = window.parent.document.querySelector(
                    'input[aria-label="Código de barras para buscar artículo"]'
                );
                if (barcodeInput) barcodeInput.focus();
            }, 100);
            </script>
            """,
            height=0,
        )
        st.session_state["_barcode_autofocus_done"] = True

    if search_submitted:
        barcode = barcode.strip()
        if not barcode:
            st.warning("Ingresa un código de barras.")
        else:
            try:
                article = get_article_details(barcode)
            except sqlite3.Error as error:
                st.error(f"No se pudo consultar la base de datos: {error}")
            else:
                if article is None:
                    st.warning("No se encontró un artículo con ese código.")
                else:
                    _show_article(article)

with tab_entrega:
    st.info("Registra la salida de material entregado a un empleado.")
    with st.form("form_entrega"):
        delivery_barcode = st.text_input("Código de barras del artículo", key="delivery_barcode")
        delivery_quantity = st.number_input(
            "Cantidad a entregar", min_value=1, step=1, key="delivery_quantity"
        )
        recipient_rpe = st.text_input("R.P.E. del empleado que recibe")
        delivery_notes = st.text_area("Descripción / notas (opcional)")
        delivery_submitted = st.form_submit_button("Registrar entrega")

    if delivery_submitted:
        if user_id is None:
            st.error("Selecciona un usuario responsable.")
        elif not delivery_barcode.strip() or not recipient_rpe.strip():
            st.warning("Ingresa el código de barras y el R.P.E. del empleado.")
        else:
            try:
                article = get_article_details(delivery_barcode.strip())
                if article is None:
                    st.warning("No se encontró un artículo con ese código.")
                else:
                    register_stock_exit(
                        int(article["id_catalogo"]),
                        int(delivery_quantity),
                        int(user_id),
                        employee_rpe=recipient_rpe.strip(),
                        description=delivery_notes.strip() or "Entrega de material",
                    )
                    st.success(
                        f"Entrega registrada: {delivery_quantity} unidad(es) "
                        f"para {recipient_rpe.strip()}."
                    )
            except sqlite3.Error as error:
                st.error(f"No se pudo registrar la entrega: {error}")
            except ValueError as error:
                st.warning(str(error))

with tab_ingreso:
    st.info("Registra la entrada de material al inventario.")
    with st.form("form_ingreso"):
        entry_barcode = st.text_input("Código de barras del artículo", key="entry_barcode")
        entry_quantity = st.number_input(
            "Cantidad ingresada", min_value=1, step=1, key="entry_quantity"
        )
        entry_notes = st.text_area("Descripción / notas (opcional)", key="entry_notes")
        entry_submitted = st.form_submit_button("Registrar ingreso")

    if entry_submitted:
        if user_id is None:
            st.error("Selecciona un usuario responsable.")
        elif not entry_barcode.strip():
            st.warning("Ingresa el código de barras.")
        else:
            try:
                article = get_article_details(entry_barcode.strip())
                if article is None:
                    st.warning("No se encontró un artículo con ese código.")
                else:
                    register_stock_entry(
                        int(article["id_catalogo"]),
                        int(entry_quantity),
                        int(user_id),
                        description=entry_notes.strip() or "Ingreso de material",
                    )
                    st.success(f"Ingreso registrado: {entry_quantity} unidad(es).")
            except sqlite3.Error as error:
                st.error(f"No se pudo registrar el ingreso: {error}")
            except ValueError as error:
                st.warning(str(error))

with tab_baja:
    st.info("Registra una baja de existencias por daño, merma u otro motivo.")
    with st.form("form_baja"):
        writeoff_barcode = st.text_input(
            "Código de barras del artículo", key="writeoff_barcode"
        )
        writeoff_quantity = st.number_input(
            "Cantidad a dar de baja", min_value=1, step=1, key="writeoff_quantity"
        )
        writeoff_reason = st.text_area("Motivo de la baja")
        writeoff_submitted = st.form_submit_button("Registrar baja")

    if writeoff_submitted:
        if user_id is None:
            st.error("Selecciona un usuario responsable.")
        elif not writeoff_barcode.strip() or not writeoff_reason.strip():
            st.warning("Ingresa el código de barras y el motivo de la baja.")
        else:
            try:
                article = get_article_details(writeoff_barcode.strip())
                if article is None:
                    st.warning("No se encontró un artículo con ese código.")
                else:
                    register_stock_exit(
                        int(article["id_catalogo"]),
                        int(writeoff_quantity),
                        int(user_id),
                        description=f"Baja: {writeoff_reason.strip()}",
                    )
                    st.success(f"Baja registrada: {writeoff_quantity} unidad(es).")
            except sqlite3.Error as error:
                st.error(f"No se pudo registrar la baja: {error}")
            except ValueError as error:
                st.warning(str(error))

with tab_reportes:
    st.info("Conexión preparada para consultar y descargar reportes.")
    report_type = st.selectbox(
        "Tipo de reporte", ["Existencias actuales", "Movimientos mensuales"]
    )
    report_month = None
    if report_type == "Movimientos mensuales":
        report_month = st.date_input("Selecciona una fecha del mes")

    if st.button("Preparar descarga", key="prepare_report"):
        st.session_state.pop("_report_rows", None)
        st.session_state.pop("_report_filename", None)
        try:
            if report_type == "Existencias actuales":
                report_rows = get_stock_report()
                filename = "existencias.csv"
            else:
                report_rows = get_movement_report(report_month.strftime("%Y-%m"))
                filename = f"movimientos_{report_month:%Y_%m}.csv"
        except NotImplementedError as error:
            st.info(str(error))
        except sqlite3.Error as error:
            st.error(f"No se pudo generar el reporte: {error}")
        else:
            st.session_state["_report_rows"] = report_rows
            st.session_state["_report_filename"] = filename

    report_rows = st.session_state.get("_report_rows")
    if report_rows:
        st.download_button(
            "Descargar reporte CSV",
            data=_report_csv(report_rows),
            file_name=st.session_state["_report_filename"],
            mime="text/csv",
        )
    elif "_report_rows" in st.session_state:
        st.info("El reporte no contiene datos para descargar.")
