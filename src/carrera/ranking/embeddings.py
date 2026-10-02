"""Embeddings con Ollama (bge-m3). Cambiar de proveedor = reemplazar este módulo."""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence

Embedder = Callable[[Sequence[str]], list[list[float]]]
MODELO = os.environ.get("CARRERA_MODELO_EMBEDDINGS", "bge-m3")
OLLAMA = os.environ.get("CARRERA_OLLAMA_URL", "http://localhost:11434")


def _con_reintentos(req: urllib.request.Request, intentos: int = 3) -> list[list[float]]:
    """Ollama devuelve 500 transitorios al intercambiar modelos en la GPU."""
    for n in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310
                return json.loads(r.read())["embeddings"]
        except urllib.error.HTTPError:
            if n == intentos - 1:
                raise
            time.sleep(2 * (n + 1))
    raise AssertionError("inalcanzable")


def ollama(textos: Sequence[str]) -> list[list[float]]:
    vectores: list[list[float]] = []
    for i in range(0, len(textos), 4):
        cuerpo = json.dumps({"model": MODELO, "input": list(textos[i:i + 4]),
                             "keep_alive": "10m",
                             # En CPU: en GPU algunos textos cortos dan NaN en bge-m3 (fp16).
                             "options": {"num_gpu": 0}}).encode()
        req = urllib.request.Request(f"{OLLAMA}/api/embed", cuerpo,
                                     {"Content-Type": "application/json"})
        vectores.extend(_con_reintentos(req))
    return vectores


def coseno(a: Sequence[float], b: Sequence[float]) -> float:
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return 0.0 if na == 0 or nb == 0 else sum(x * y for x, y in zip(a, b)) / (na * nb)


class ConCache:
    """Evita re-embeber textos iguales entre corridas (clave = hash del texto + modelo)."""

    def __init__(self, base: Embedder, db) -> None:
        self.base, self.db = base, db
        db.execute("CREATE TABLE IF NOT EXISTS vectores (h TEXT PRIMARY KEY, v TEXT NOT NULL)")

    def __call__(self, textos: Sequence[str]) -> list[list[float]]:
        claves = [hashlib.sha256(f"{MODELO}\n{t}".encode()).hexdigest() for t in textos]
        hallados = {h: json.loads(v) for h, v in self.db.execute(
            f"SELECT h,v FROM vectores WHERE h IN ({','.join('?' * len(claves))})", claves)} if claves else {}
        faltan = [(h, t) for h, t in zip(claves, textos) if h not in hallados]
        if faltan:
            for (h, _), v in zip(faltan, self.base([t for _, t in faltan])):
                hallados[h] = v
                self.db.execute("INSERT OR REPLACE INTO vectores VALUES (?,?)", (h, json.dumps(v)))
            self.db.commit()
        return [hallados[h] for h in claves]
