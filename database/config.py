"""
database/config.py
------------------
SQLite configuration and schema for the CFE CRUD (almacén) system.

Usage (from the project root):
    python -m database.config          # creates almacen.db with all tables

    from database.config import get_connection
    with get_connection() as conn:
        conn.execute("SELECT * FROM articulos")
"""

import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# --------------------------------------------------------------------------
# Schema
# Table/column names are ASCII (no accents) to avoid quoting issues.
# Order matters: parent tables are created before the tables that reference them.
# --------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS sucursal (
    id_sucursal   INTEGER PRIMARY KEY AUTOINCREMENT,
    division      VARCHAR(50) NOT NULL,
    direccion     VARCHAR(50) NOT NULL,
    extension     INTEGER,
    numero        INTEGER,
    codigo_postal INTEGER     NOT NULL,
    estado        VARCHAR(50) NOT NULL,
    municipio     VARCHAR(50) NOT NULL,
    telefono      VARCHAR(50),
    correo        VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS departamento (
    id_departamento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_sucursal     INTEGER     NOT NULL,
    nombre          VARCHAR(50) NOT NULL,
    telefono        VARCHAR(50),
    correo          VARCHAR(50),
    FOREIGN KEY (id_sucursal) REFERENCES sucursal (id_sucursal)
);


CREATE TABLE IF NOT EXISTS empleado (
    id_empleado      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_departamento  INTEGER     NOT NULL,
    cargo            VARCHAR(50),
    titulo_academico VARCHAR(30),
    rpe              VARCHAR(20) NOT NULL,
    nombres          VARCHAR(80) NOT NULL,
    apellido_paterno VARCHAR(80),
    apellido_materno VARCHAR(80),
    telefono         VARCHAR(50),
    correo           VARCHAR(50),
    FOREIGN KEY (id_departamento) REFERENCES departamento (id_departamento)
);

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_empleado INTEGER NOT NULL,
    activo      BOOLEAN NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    login       DATETIME,   -- NULL until the first session
    log_out     DATETIME,   -- NULL while the session is open
    FOREIGN KEY (id_empleado) REFERENCES empleado (id_empleado)
);

CREATE TABLE IF NOT EXISTS almacen (
    id_almacen  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_sucursal INTEGER     NOT NULL,
    tipo        VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_sucursal) REFERENCES sucursal (id_sucursal)
);

CREATE TABLE IF NOT EXISTS articulos (
    id_articulo INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS detalles_articulos (
    id_detalle        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_articulo       INTEGER     NOT NULL,
    material          VARCHAR(50) ,
    descripcion       TEXT,
    FOREIGN KEY (id_articulo) REFERENCES articulos (id_articulo)
);
CREATE TABLE IF NOT EXISTS medida (
    id_medida INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo      VARCHAR(30)
);
CREATE TABLE IF NOT EXISTS color (
    id_color INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo     VARCHAR(30)
);
CREATE TABLE IF NOT EXISTS clase (
    id_clase INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo     VARCHAR(30)
);
CREATE TABLE IF NOT EXISTS marca (
    id_marca INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo     VARCHAR(30)
);
CREATE TABLE IF NOT EXISTS catalogo (
    id_catalogo INTEGER PRIMARY KEY AUTOINCREMENT,
    id_detalle  INTEGER     NOT NULL,
    id_medida   INTEGER     NOT NULL,
    id_color    INTEGER     NOT NULL,
    id_clase    INTEGER     NOT NULL,
    id_marca    INTEGER     NOT NULL,
    FOREIGN KEY (id_detalle) REFERENCES detalles_articulos (id_detalle),
    FOREIGN KEY (id_medida) REFERENCES medida(id_medida),
    FOREIGN KEY (id_color) REFERENCES color (id_color),
    FOREIGN KEY (id_clase) REFERENCES clase (id_clase),
    FOREIGN KEY (id_marca) REFERENCES marca (id_marca)
);

CREATE TABLE IF NOT EXISTS inventario (
    id_inventario INTEGER PRIMARY KEY AUTOINCREMENT,
    id_catalogo   INTEGER NOT NULL,
    id_almacen    INTEGER NOT NULL,
    cantidad_unidades INTEGER NOT NULL CHECK (cantidad_unidades >= 0),
    fecha         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_catalogo) REFERENCES catalogo (id_catalogo),
    FOREIGN KEY (id_almacen)  REFERENCES almacen (id_almacen)
);

CREATE TABLE IF NOT EXISTS entradas (
    id_entrada    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_inventario INTEGER  NOT NULL,
    fecha         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cantidad_unidades INTEGER NOT NULL CHECK (cantidad_unidades > 0),
    id_usuario    INTEGER  NOT NULL,
    descripcion   TEXT,
    FOREIGN KEY (id_inventario) REFERENCES inventario (id_inventario),
    FOREIGN KEY (id_usuario)  REFERENCES usuario (id_usuario)
);

CREATE TABLE IF NOT EXISTS salidas (
    id_salida     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_inventario INTEGER  NOT NULL,
    fecha         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cantidad_unidades INTEGER NOT NULL CHECK (cantidad_unidades > 0),
    id_empleado   INTEGER NOT NULL,
    id_usuario    INTEGER NOT NULL,
    descripcion   TEXT,
    FOREIGN KEY (id_inventario) REFERENCES inventario (id_inventario),
    FOREIGN KEY (id_empleado) REFERENCES empleado (id_empleado),
    FOREIGN KEY (id_usuario)  REFERENCES usuario (id_usuario)
);

-- Indexes on foreign keys (SQLite does not create them automatically)
CREATE INDEX IF NOT EXISTS idx_departamento_sucursal ON departamento (id_sucursal);
CREATE INDEX IF NOT EXISTS idx_empleado_departamento ON empleado (id_departamento);
CREATE INDEX IF NOT EXISTS idx_usuario_empleado      ON usuario (id_empleado);
CREATE INDEX IF NOT EXISTS idx_almacen_sucursal      ON almacen (id_sucursal);
CREATE INDEX IF NOT EXISTS idx_detalles_articulo     ON detalles_articulos (id_articulo);
CREATE INDEX IF NOT EXISTS idx_catalogo_detalle      ON catalogo (id_detalle);
CREATE INDEX IF NOT EXISTS idx_catalogo_color      ON catalogo (id_color);
CREATE INDEX IF NOT EXISTS idx_catalogo_medida      ON catalogo (id_medida);
CREATE INDEX IF NOT EXISTS idx_catalogo_clase      ON catalogo (id_clase);
CREATE INDEX IF NOT EXISTS idx_catalogo_marca      ON catalogo (id_marca);
CREATE INDEX IF NOT EXISTS idx_inventario_catalogo   ON inventario (id_catalogo);
CREATE INDEX IF NOT EXISTS idx_inventario_almacen    ON inventario (id_almacen);
CREATE INDEX IF NOT EXISTS idx_entradas_inventario   ON entradas (id_inventario);
CREATE INDEX IF NOT EXISTS idx_entradas_usuario      ON entradas (id_usuario);
CREATE INDEX IF NOT EXISTS idx_salidas_inventario    ON salidas (id_inventario);
CREATE INDEX IF NOT EXISTS idx_salidas_empleado      ON salidas (id_empleado);
CREATE INDEX IF NOT EXISTS idx_salidas_usuario       ON salidas (id_usuario);
"""


def connect(db: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")  # off by default in SQLite
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def get_connection(db: str) -> Iterator[sqlite3.Connection]:
    conn = connect(db)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db: str) -> None:
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db) as conn:
        conn.executescript(SCHEMA)
    print(f"Database ready at: {db}")


if __name__ == "__main__":
    init_db("almacen.db")