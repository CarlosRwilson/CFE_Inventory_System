"""Reusable CRUD operations for the inventory database."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.config import get_connection

DATABASE_PATH = ROOT / "database" / "almacen.db"


def get_article_details(barcode: str) -> dict[str, str | int | None] | None:
    """Return article variation and current stock associated with a barcode."""
    with get_connection(str(DATABASE_PATH)) as connection:
        row = connection.execute(
            """
            SELECT
                c.id_catalogo,
                c.codigo_barras,
                a.nombre,
                d.descripcion,
                d.material,
                co.tipo AS color,
                me.tipo AS medida,
                cl.tipo AS clase,
                ma.tipo AS marca,
                COALESCE(
                    (
                        SELECT i.cantidad_unidades
                        FROM inventario AS i
                        WHERE i.id_catalogo = c.id_catalogo
                            AND i.id_almacen = c.id_almacen
                    ),
                    0
                ) AS existencia
            FROM catalogo AS c
            JOIN detalles_articulos AS d ON d.id_detalle = c.id_detalle
            JOIN articulos AS a ON a.id_articulo = d.id_articulo
            JOIN color AS co ON co.id_color = c.id_color
            JOIN medida AS me ON me.id_medida = c.id_medida
            JOIN clase AS cl ON cl.id_clase = c.id_clase
            JOIN marca AS ma ON ma.id_marca = c.id_marca
            WHERE c.codigo_barras = ?
            """,
            (barcode,),
        ).fetchone()
        return dict(row) if row else None


def get_active_users() -> list[dict[str, int | str]]:
    """Return active users with the employee identity shown in the UI."""
    with get_connection(str(DATABASE_PATH)) as connection:
        rows = connection.execute(
            """
            SELECT
                u.id_usuario,
                e.rpe,
                e.nombres,
                e.apellido_paterno,
                e.apellido_materno
            FROM usuario AS u
            JOIN empleado AS e ON e.id_empleado = u.id_empleado
            WHERE u.activo = 1
            ORDER BY e.apellido_paterno, e.nombres
            """
        ).fetchall()
        return [dict(row) for row in rows]


def _validate_quantity(quantity: int) -> None:
    if quantity <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")


def register_stock_entry(
    catalog_id: int,
    quantity: int,
    user_id: int,
    description: str | None = None,
) -> None:
    """Increase stock and record the corresponding inventory entry."""
    _validate_quantity(quantity)
    with get_connection(str(DATABASE_PATH)) as connection:
        catalog = connection.execute(
            "SELECT id_almacen FROM catalogo WHERE id_catalogo = ?",
            (catalog_id,),
        ).fetchone()
        if catalog is None:
            raise ValueError("No se encontró la variación del artículo.")

        inventory = connection.execute(
            """
            SELECT id_inventario
            FROM inventario
            WHERE id_catalogo = ? AND id_almacen = ?
            """,
            (catalog_id, catalog["id_almacen"]),
        ).fetchone()

        if inventory is None:
            cursor = connection.execute(
                """
                INSERT INTO inventario
                    (id_catalogo, id_almacen, cantidad_unidades)
                VALUES (?, ?, ?)
                """,
                (catalog_id, catalog["id_almacen"], quantity),
            )
            inventory_id = cursor.lastrowid #search
        else:
            inventory_id = inventory["id_inventario"]
            connection.execute(
                """
                UPDATE inventario
                SET cantidad_unidades = cantidad_unidades + ?
                WHERE id_inventario = ?
                """,
                (quantity, inventory_id),
            )

        connection.execute(
            """
            INSERT INTO entradas
                (id_inventario, cantidad_unidades, id_usuario, descripcion)
            VALUES (?, ?, ?, ?)
            """,
            (inventory_id, quantity, user_id, description),
        )


def register_stock_exit(
    catalog_id: int,
    quantity: int,
    user_id: int,
    employee_rpe: str | None = None,
    description: str | None = None,
) -> None:
    """Decrease stock and record a delivery or inventory write-off."""
    _validate_quantity(quantity)
    with get_connection(str(DATABASE_PATH)) as connection:
        if employee_rpe:
            employee = connection.execute(
                "SELECT id_empleado FROM empleado WHERE rpe = ?",
                (employee_rpe.strip(),),
            ).fetchone()
            if employee is None:
                raise ValueError("No se encontró un empleado con ese R.P.E.")
            employee_id = employee["id_empleado"]
        else:
            user = connection.execute(
                "SELECT id_empleado FROM usuario WHERE id_usuario = ? AND activo = 1",
                (user_id,),
            ).fetchone()
            if user is None:
                raise ValueError("No se encontró un usuario activo.")
            employee_id = user["id_empleado"]

        inventory = connection.execute(
            """
            SELECT i.id_inventario, i.cantidad_unidades
            FROM inventario AS i
            JOIN catalogo AS c
                ON c.id_catalogo = i.id_catalogo
                AND c.id_almacen = i.id_almacen
            WHERE i.id_catalogo = ?
            ORDER BY i.id_inventario
            LIMIT 1
            """,
            (catalog_id,),
        ).fetchone()
        if inventory is None or inventory["cantidad_unidades"] < quantity:
            raise ValueError("No hay existencias suficientes para esta operación.")

        connection.execute(
            """
            UPDATE inventario
            SET cantidad_unidades = cantidad_unidades - ?
            WHERE id_inventario = ?
            """,
            (quantity, inventory["id_inventario"]),
        )
        connection.execute(
            """
            INSERT INTO salidas
                (
                    id_inventario,
                    cantidad_unidades,
                    id_empleado,
                    id_usuario,
                    descripcion
                )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                inventory["id_inventario"],
                quantity,
                employee_id,
                user_id,
                description,
            ),
        )


def get_stock_report() -> list[dict[str, object]]:
    """Report query placeholder; implement the inventory query here."""
    raise NotImplementedError("La consulta del reporte de existencias está pendiente.")


def get_movement_report(month: str) -> list[dict[str, object]]:
    """Report query placeholder; implement the movement query here."""
    raise NotImplementedError("La consulta del reporte de movimientos está pendiente.")