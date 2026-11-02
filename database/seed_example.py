import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.config import get_connection, init_db

DB_PATH = Path(__file__).with_name("almacen_example.db")

EXAMPLE_DATA: dict[str, list[dict[str, object]]] = {
    "sucursal": [
        {
            "division": "Sucursal de ejemplo",
            "direccion": "Calle de prueba 123",
            "extension": None,
            "numero": 123,
            "codigo_postal": 22800,
            "estado": "Baja California",
            "municipio": "Ensenada",
            "telefono": "646-000-0000",
            "correo": "sucursal@example.invalid",
        }
    ],
    "departamento": [
        {
            "id_sucursal": 1,
            "nombre": "Departamento de ejemplo",
            "telefono": None,
            "correo": "departamento@example.invalid",
        }
    ],
    "empleado": [
        {
            "id_departamento": 1,
            "cargo": "Responsable de ejemplo",
            "titulo_academico": None,
            "rpe": "DEMO001",
            "nombres": "Alex",
            "apellido_paterno": "Ejemplo",
            "apellido_materno": None,
            "telefono": "646-000-0001",
            "correo": "empleado@example.invalid",
        }
    ],
    "usuario": [{"id_empleado": 1, "activo": True}],
    "almacen": [{"id_sucursal": 1, "tipo": "A"}],
    "articulos": [
        {"nombre": "Casco de ejemplo"},
        {"nombre": "Guantes de ejemplo"},
    ],
    "detalles_articulos": [
        {
            "id_articulo": 1,
            "material": "Plástico",
            "descripcion": "Casco de protección ficticio",
        },
        {
            "id_articulo": 2,
            "material": "Textil",
            "descripcion": "Guantes de trabajo ficticios",
        },
    ],
    "medida": [{"tipo": "UNITALLA"}, {"tipo": "M"}],
    "color": [{"tipo": "AMARILLO"}, {"tipo": "AZUL"}],
    "clase": [{"tipo": "SIN CLASE"}],
    "marca": [{"tipo": "SIN MARCA"}],
    "catalogo": [
        {
            "id_detalle": 1,
            "id_medida": 1,
            "id_color": 1,
            "id_clase": 1,
            "id_marca": 1,
        },
        {
            "id_detalle": 2,
            "id_medida": 2,
            "id_color": 2,
            "id_clase": 1,
            "id_marca": 1,
        },
    ],
    "inventario": [
        {"id_catalogo": 1, "id_almacen": 1, "cantidad_unidades": 10},
        {"id_catalogo": 2, "id_almacen": 1, "cantidad_unidades": 25},
    ],
    "entradas": [
        {
            "id_inventario": 1,
            "cantidad_unidades": 5,
            "id_usuario": 1,
            "descripcion": "Entrada de ejemplo",
        }
    ],
    "salidas": [
        {
            "id_inventario": 1,
            "cantidad_unidades": 2,
            "id_empleado": 1,
            "id_usuario": 1,
            "descripcion": "Salida de ejemplo",
        }
    ],
}


def load_example_data(db_path: Path = DB_PATH) -> int:
    init_db(str(db_path))

    with get_connection(str(db_path)) as connection:
        for table in EXAMPLE_DATA:
            row_count = connection.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
            if row_count:
                raise RuntimeError(
                    f"La base de ejemplo ya contiene datos en '{table}'; "
                    "se cancela la carga para evitar duplicados."
                )

        inserted = 0
        for table, rows in EXAMPLE_DATA.items():
            columns = tuple(rows[0])
            column_names = ", ".join(f'"{column}"' for column in columns)
            placeholders = ", ".join("?" for _ in columns)
            sql = f'INSERT INTO "{table}" ({column_names}) VALUES ({placeholders})'
            values = [tuple(row[column] for column in columns) for row in rows]
            connection.executemany(sql, values)
            inserted += len(values)

    return inserted


if __name__ == "__main__":
    print(f" {load_example_data()} rows inserted.")
