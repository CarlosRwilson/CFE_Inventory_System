"""
 Data example from the inventory database

"""

data = {
    "sucursal": [
        {
            "division": "Sucursal de Ejemplo",
            "direccion": "Calle Ficticia 123",
            "extension": "",
            "numero": 123,
            "codigo_postal": 0,
            "estado": "Estado de Ejemplo",
            "municipio": "Municipio de Ejemplo",
            "telefono": "000-000-0000",
            "correo": "sucursal@example.invalid",
        }
    ],
    "departamento": [
        {
            "id_sucursal": 1,
            "nombre": "Departamento de Prueba",
            "telefono": "000-000-0000",
            "correo": "departamento@example.invalid",
        }
    ],
    "empleado": [
        {
            "id_departamento": 1,
            "cargo": "Puesto de Ejemplo",
            "titulo_academico": "Formación de Ejemplo",
            "rpe": "DEMO001",
            "nombres": "Alex",
            "apellido_paterno": "Ejemplo",
            "apellido_materno": "Prueba",
            "telefono": "000-000-0000",
            "correo": "empleado@example.invalid",
        }
    ],
    "usuario": [
        {
            "id_empleado": 1,
            "activo": True,
        }
    ],
    "almacen": [
        {
            "id_sucursal": 1,
            "tipo": "A",
        }
    ],
    "articulos": [
        {"nombre": "Casco de ejemplo"},
        {"nombre": "Guantes de ejemplo"},
        {"nombre": "Chaleco de ejemplo"},
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
        {
            "id_articulo": 3,
            "material": "Poliéster",
            "descripcion": "Chaleco de alta visibilidad ficticio",
        },
    ],
}