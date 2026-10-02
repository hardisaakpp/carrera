from __future__ import annotations

from .almacen import Almacen
from .fuentes import FUENTES, Http, http_get


def capturar(almacen: Almacen, fuentes: list[str] | None = None, http: Http = http_get,
             forzar: bool = False) -> dict[str, str]:
    """Consulta cada fuente respetando su intervalo. Un fallo no detiene a las demás."""
    resultado: dict[str, str] = {}
    for nombre in fuentes or list(FUENTES):
        if nombre not in FUENTES:
            resultado[nombre] = "fuente desconocida"
            continue
        if not forzar and not almacen.puede_consultar(nombre):
            resultado[nombre] = "omitida (consultada hace menos de 6 h)"
            continue
        try:
            ofertas = FUENTES[nombre](http=http)
        except Exception as e:  # noqa: BLE001 - red/parseo de terceros
            resultado[nombre] = f"error: {type(e).__name__}"
            continue
        almacen.marcar_consulta(nombre)
        resultado[nombre] = f"{len(ofertas)} leídas, {almacen.guardar(ofertas)} nuevas"
    return resultado
