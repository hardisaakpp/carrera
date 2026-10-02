"""SQLite local: deduplicación entre fuentes y límite de frecuencia por fuente."""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime
from pathlib import Path

from .modelo import Oferta

INTERVALO_MIN_S = 6 * 3600  # los términos de las fuentes piden pocas consultas al día

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS ofertas (
  clave TEXT PRIMARY KEY, fuente TEXT NOT NULL, id_fuente TEXT NOT NULL, url TEXT NOT NULL,
  titulo TEXT NOT NULL, empresa TEXT NOT NULL, ubicacion TEXT NOT NULL, etiquetas TEXT NOT NULL,
  descripcion TEXT NOT NULL, publicada TEXT, vista_en REAL NOT NULL, otras_fuentes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS consultas (fuente TEXT PRIMARY KEY, en REAL NOT NULL);
"""


class Almacen:
    def __init__(self, ruta: Path | str = "data/ofertas.db") -> None:
        if ruta != ":memory:":
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(ruta)
        self.db.executescript(_ESQUEMA)

    def puede_consultar(self, fuente: str, ahora: float | None = None) -> bool:
        fila = self.db.execute("SELECT en FROM consultas WHERE fuente=?", (fuente,)).fetchone()
        return fila is None or (ahora or time.time()) - fila[0] >= INTERVALO_MIN_S

    def marcar_consulta(self, fuente: str, ahora: float | None = None) -> None:
        self.db.execute("INSERT OR REPLACE INTO consultas VALUES (?,?)", (fuente, ahora or time.time()))
        self.db.commit()

    def guardar(self, ofertas: list[Oferta]) -> int:
        """Devuelve cuántas son nuevas. La misma vacante en otra fuente solo se anota."""
        nuevas = 0
        for o in ofertas:
            existente = self.db.execute(
                "SELECT fuente, otras_fuentes FROM ofertas WHERE clave=?", (o.clave,)).fetchone()
            if existente is None:
                self.db.execute(
                    "INSERT INTO ofertas VALUES (?,?,?,?,?,?,?,?,?,?,?,'')",
                    (o.clave, o.fuente, o.id_fuente, o.url, o.titulo, o.empresa, o.ubicacion,
                     ",".join(o.etiquetas), o.descripcion,
                     o.publicada.isoformat() if o.publicada else None, time.time()))
                nuevas += 1
            elif existente[0] != o.fuente:
                otras = set(filter(None, existente[1].split(","))) | {o.fuente}
                self.db.execute("UPDATE ofertas SET otras_fuentes=? WHERE clave=?",
                                (",".join(sorted(otras)), o.clave))
        self.db.commit()
        return nuevas

    def todas(self) -> list[Oferta]:
        return self._leer("")

    def buscar(self, prefijo: str) -> Oferta | None:
        """Una oferta por prefijo de clave (único) o None."""
        encontradas = self._leer("WHERE clave LIKE ? ESCAPE '\\'", (prefijo.replace("%", "").replace("_", "") + "%",))
        return encontradas[0] if len(encontradas) == 1 else None

    def _leer(self, filtro: str, params: tuple = ()) -> list[Oferta]:
        filas = self.db.execute(
            "SELECT fuente,id_fuente,url,titulo,empresa,ubicacion,etiquetas,descripcion,publicada "
            f"FROM ofertas {filtro} ORDER BY publicada DESC", params).fetchall()
        return [Oferta(fuente=f, id_fuente=i, url=u, titulo=t, empresa=e, ubicacion=ub,
                       etiquetas=[x for x in et.split(",") if x], descripcion=d,
                       publicada=datetime.fromisoformat(p) if p else None)
                for f, i, u, t, e, ub, et, d, p in filas]
