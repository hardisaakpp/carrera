"""API local de la interfaz web. Escucha solo en 127.0.0.1: es una herramienta personal sin cuentas."""

from __future__ import annotations

import os
import re
import tempfile
import threading
from pathlib import Path
from typing import Callable

import yaml
from fastapi import FastAPI, HTTPException, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ValidationError

from .adaptacion.adaptar import adaptar
from .cli import compilar
from .latex import renderizar
from .modelo import Cv
from .ofertas.almacen import Almacen
from .ofertas.captura import capturar
from .ofertas.fuentes import FUENTES
from .postulacion.carta import redactar
from .postulacion.registro import ESTADOS, Registro, TransicionInvalida
from .ranking.embeddings import ConCache, Embedder, ollama
from .ranking.preferencias import Preferencias
from .ranking.ranking import ordenar, texto_oferta

CLAVE = re.compile(r"^[0-9a-f]{16}$")
Compilador = Callable[[Path], Path]


class Ajustes:
    """Rutas y dependencias externas, reemplazables en las pruebas."""

    def __init__(self, datos: Path, embedder: Embedder = ollama, compilador: Compilador = compilar) -> None:
        self.datos = datos
        self.embedder = embedder
        self.compilador = compilador
        datos.mkdir(parents=True, exist_ok=True)

    @property
    def cv(self) -> Path:
        return self.datos / "cv.local.yaml"

    @property
    def preferencias(self) -> Path:
        return self.datos / "preferencias.local.yaml"

    def almacen(self) -> Almacen:
        return Almacen(self.datos / "ofertas.db")

    @property
    def postulaciones(self) -> Path:
        return self.datos / "postulaciones"


def crear_app(ajustes: Ajustes | None = None) -> FastAPI:
    a = ajustes or Ajustes(Path(os.environ.get("CARRERA_DATOS", "data")))
    app = FastAPI(title="carrera", docs_url=None, redoc_url=None)

    def cargar_cv() -> tuple[Cv, bool]:
        ruta, ejemplo = (a.cv, False) if a.cv.exists() else (Path(__file__).parents[2] / "data" / "ejemplo.yaml", True)
        return Cv.model_validate(yaml.safe_load(ruta.read_text("utf-8"))), ejemplo

    def cargar_preferencias() -> Preferencias:
        if not a.preferencias.exists():
            return Preferencias()
        return Preferencias.model_validate(yaml.safe_load(a.preferencias.read_text("utf-8")) or {})

    def guardar_yaml(ruta: Path, datos: BaseModel) -> None:
        ruta.write_text(yaml.safe_dump(datos.model_dump(mode="json"), allow_unicode=True, sort_keys=False), "utf-8")

    def clave_valida(clave: str) -> str:
        if not CLAVE.match(clave):
            raise HTTPException(404, "no encontrada")
        return clave

    @app.get("/api/cv")
    def leer_cv():
        cv, ejemplo = cargar_cv()
        return {"cv": cv.model_dump(mode="json"), "ejemplo": ejemplo}

    @app.put("/api/cv")
    def guardar_cv(cv: Cv):
        guardar_yaml(a.cv, cv)
        return {"ok": True}

    @app.post("/api/cv/pdf")
    async def pdf_cv(cv: Cv | None = None):
        """Compila el CV recibido (o el guardado) sin escribirlo: sirve de vista previa mientras se edita."""
        contenido = cv or cargar_cv()[0]
        with tempfile.TemporaryDirectory(dir=a.datos) as tmp:
            tex = Path(tmp) / "cv.tex"
            tex.write_text(renderizar(contenido), "utf-8")
            try:
                pdf = await run_in_threadpool(a.compilador, tex)
            except Exception as e:  # noqa: BLE001 - latexmk/docker
                raise HTTPException(422, "no se pudo compilar el CV") from e
            return Response(pdf.read_bytes(), media_type="application/pdf")

    @app.get("/api/preferencias")
    def leer_preferencias():
        return cargar_preferencias().model_dump()

    @app.put("/api/preferencias")
    def guardar_preferencias(p: Preferencias):
        guardar_yaml(a.preferencias, p)
        return {"ok": True}

    @app.post("/api/ofertas/actualizar")
    async def actualizar(forzar: bool = False):
        return await run_in_threadpool(lambda: capturar(a.almacen(), forzar=forzar))

    calculando: set[str] = set()
    cerrojo = threading.Lock()

    def precalcular(textos: list[str]) -> None:
        """Embebe en segundo plano lo que falta: la primera vez son minutos, no deben bloquear la pantalla."""
        try:
            ConCache(a.embedder, Almacen(a.datos / "ofertas.db").db)(textos)
        finally:
            with cerrojo:
                calculando.difference_update(textos)

    @app.get("/api/ofertas")
    async def ranking(limite: int = 30):
        almacen = a.almacen()
        cv, _ = cargar_cv()
        cache = ConCache(a.embedder, almacen.db)
        ofertas = almacen.todas()
        listas = [o for o in ofertas if cache.tiene(texto_oferta(o))]
        faltan = [texto_oferta(o) for o in ofertas if o not in listas]
        with cerrojo:
            nuevos = [t for t in faltan if t not in calculando]
            calculando.update(nuevos)
        if nuevos:
            threading.Thread(target=precalcular, args=(nuevos,), daemon=True).start()
        resultados = await run_in_threadpool(ordenar, cv, listas, cargar_preferencias(), cache)
        estados = {fila[0]: fila[1] for fila in Registro(almacen.db).listar()}
        vivas = [r for r in resultados if r.excluida is None]
        return {
            "total": len(ofertas), "descartadas": len(resultados) - len(vivas),
            "pendientes": len(faltan), "fuentes": list(FUENTES),
            "ofertas": [{
                "clave": r.oferta.clave, "titulo": r.oferta.titulo, "empresa": r.oferta.empresa,
                "ubicacion": r.oferta.ubicacion, "fuente": r.oferta.fuente, "url": r.oferta.url,
                "puntaje": r.puntaje, "coinciden": r.coinciden,
                "estado": estados.get(r.oferta.clave),
            } for r in vivas[:limite]],
        }

    @app.post("/api/postulaciones/{clave}")
    async def crear_postulacion(clave: str):
        almacen = a.almacen()
        oferta = almacen.buscar(clave_valida(clave))
        if oferta is None:
            raise HTTPException(404, "oferta no encontrada")
        original, _ = cargar_cv()
        adaptado = await run_in_threadpool(adaptar, original, oferta)
        carpeta = a.postulaciones / oferta.clave
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "cv.tex").write_text(renderizar(adaptado), "utf-8")
        (carpeta / "carta.txt").write_text(redactar(adaptado, oferta), "utf-8")
        Registro(almacen.db).crear(oferta.clave, str(carpeta), oferta.titulo, oferta.empresa, oferta.url)
        return {"clave": oferta.clave, "estado": "borrador"}

    @app.get("/api/postulaciones")
    def listar_postulaciones():
        registro = Registro(a.almacen().db)
        return [{"clave": c, "estado": e, "titulo": t, "empresa": m, "url": u}
                for c, e, t, m, u in registro.listar()]

    @app.get("/api/postulaciones/{clave}")
    def ver_postulacion(clave: str):
        carpeta = a.postulaciones / clave_valida(clave)
        if not (carpeta / "carta.txt").exists():
            raise HTTPException(404, "no encontrada")
        return {"clave": clave, "carta": (carpeta / "carta.txt").read_text("utf-8"),
                "estado": Registro(a.almacen().db).estado(clave)}

    @app.put("/api/postulaciones/{clave}/carta")
    def editar_carta(clave: str, cuerpo: dict):
        """La persona puede retocar la carta antes de usarla; es texto suyo, no del modelo."""
        carpeta = a.postulaciones / clave_valida(clave)
        texto = cuerpo.get("carta")
        if not (carpeta / "carta.txt").exists() or not isinstance(texto, str) or len(texto) > 8000:
            raise HTTPException(422, "carta inválida")
        (carpeta / "carta.txt").write_text(texto, "utf-8")
        return {"ok": True}

    @app.get("/api/postulaciones/{clave}/cv.pdf")
    async def pdf_postulacion(clave: str):
        carpeta = a.postulaciones / clave_valida(clave)
        tex = carpeta / "cv.tex"
        if not tex.exists():
            raise HTTPException(404, "no encontrada")
        try:
            pdf = await run_in_threadpool(a.compilador, tex)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(422, "no se pudo compilar el CV") from e
        return Response(pdf.read_bytes(), media_type="application/pdf")

    @app.post("/api/postulaciones/{clave}/{accion}")
    def mover(clave: str, accion: str):
        destino = {"confirmar": "confirmada", "enviada": "enviada", "descartar": "descartada"}.get(accion)
        if destino is None or destino not in ESTADOS:
            raise HTTPException(404, "acción desconocida")
        try:
            Registro(a.almacen().db).mover(clave_valida(clave), destino)
        except KeyError as e:
            raise HTTPException(404, "no encontrada") from e
        except TransicionInvalida as e:
            raise HTTPException(409, str(e)) from e
        return {"estado": destino}

    @app.exception_handler(ValidationError)
    async def _validacion(_, exc: ValidationError):
        return Response(exc.json(), status_code=422, media_type="application/json")

    return app


app = None  # `uvicorn carrera.api:crear_app --factory`
