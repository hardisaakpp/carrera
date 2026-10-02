"""Seguimiento de postulaciones. Estados: borrador -> confirmada -> enviada | descartada.

Nada pasa a `enviada` sin que la persona lo marque: la herramienta no envía por sí sola.
"""

from __future__ import annotations

import sqlite3
import time

ESTADOS = ("borrador", "confirmada", "enviada", "descartada")
TRANSICIONES = {
    "borrador": {"confirmada", "descartada"},
    "confirmada": {"enviada", "descartada"},
    "enviada": set(),
    "descartada": set(),
}


class TransicionInvalida(ValueError):
    pass


class Registro:
    def __init__(self, db: sqlite3.Connection) -> None:
        self.db = db
        db.execute("""CREATE TABLE IF NOT EXISTS postulaciones (
            clave TEXT PRIMARY KEY, estado TEXT NOT NULL, carpeta TEXT NOT NULL,
            titulo TEXT NOT NULL, empresa TEXT NOT NULL, url TEXT NOT NULL, actualizada REAL NOT NULL)""")

    def crear(self, clave: str, carpeta: str, titulo: str, empresa: str, url: str) -> None:
        self.db.execute("INSERT OR IGNORE INTO postulaciones VALUES (?,?,?,?,?,?,?)",
                        (clave, "borrador", carpeta, titulo, empresa, url, time.time()))
        self.db.commit()

    def estado(self, clave: str) -> str | None:
        fila = self.db.execute("SELECT estado FROM postulaciones WHERE clave=?", (clave,)).fetchone()
        return fila[0] if fila else None

    def mover(self, clave: str, nuevo: str) -> None:
        actual = self.estado(clave)
        if actual is None:
            raise KeyError(clave)
        if nuevo not in TRANSICIONES[actual]:
            raise TransicionInvalida(f"{actual} -> {nuevo} no está permitido")
        self.db.execute("UPDATE postulaciones SET estado=?, actualizada=? WHERE clave=?",
                        (nuevo, time.time(), clave))
        self.db.commit()

    def listar(self) -> list[tuple[str, str, str, str, str]]:
        return self.db.execute(
            "SELECT clave, estado, titulo, empresa, url FROM postulaciones ORDER BY actualizada DESC"
        ).fetchall()
