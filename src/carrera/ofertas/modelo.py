"""Oferta normalizada. El texto es NO confiable: viene de terceros."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Oferta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fuente: str
    id_fuente: str
    url: str  # enlace de vuelta a la fuente: lo exigen sus términos
    titulo: str
    empresa: str
    ubicacion: str = ""
    etiquetas: list[str] = Field(default_factory=list)
    descripcion: str = ""  # texto plano, sin HTML
    publicada: datetime | None = None

    @property
    def clave(self) -> str:
        """Identidad entre fuentes: la misma vacante publicada en dos sitios colapsa."""
        base = "|".join(_norm(x) for x in (self.empresa, self.titulo))
        return hashlib.sha256(base.encode()).hexdigest()[:16]


def _norm(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()
