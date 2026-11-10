"""
Functions that can be used in several parts of the application.
"""
from itertools import product
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def _as_list(x):
    """int -> [x]; range, list, tuple -> list(x)"""
    return [x] if isinstance(x, int) else list(x)

def variants(
        id_detalle: int | range,
        medidas: int | range,
        colores: int | range | list[int] = 13,
        clases: int | range | list[int] = 12,
        marcas: int | range | list[int] = 38,
        almacen: int | list[int] = 2,
) -> list[dict]:
    """
    
    """
    result = []
    for d in _as_list(id_detalle):
        for m, c, cl, mk, a in product(
            _as_list(medidas),
            _as_list(colores),
            _as_list(clases),
            _as_list(marcas),
            _as_list(almacen),
        ):
            result.append({
                "id_detalle": d,
                "id_medida": m,
                "id_color": c,
                "id_clase": cl,
                "id_marca": mk,
                "id_almacen": a,
            })
    return result