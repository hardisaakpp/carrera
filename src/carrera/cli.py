"""CLI: validar el YAML, generar el .tex y compilarlo a PDF en un contenedor."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from .latex import renderizar
from .modelo import Cv

IMAGEN_LATEX = "ghcr.io/xu-cheng/texlive-alpine:latest"


def cargar(ruta: Path) -> Cv:
    return Cv.model_validate(yaml.safe_load(ruta.read_text("utf-8")))


def compilar(tex: Path) -> Path:
    """Compila con latexmk dentro de Docker Engine: sin instalar TeX en el host."""
    env = {**os.environ, "DOCKER_CONTEXT": "default"}
    subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "-v", f"{tex.parent.resolve()}:/work",
         "-w", "/work", IMAGEN_LATEX, "latexmk", "-pdf", "-interaction=nonstopmode",
         "-halt-on-error", "-no-shell-escape", tex.name],
        check=True, env=env,
    )
    return tex.with_suffix(".pdf")


def ofertas(argv: list[str]) -> int:
    from .ofertas.almacen import Almacen
    from .ofertas.captura import capturar

    p = argparse.ArgumentParser(prog="carrera ofertas")
    p.add_argument("--db", default="data/ofertas.db")
    p.add_argument("--forzar", action="store_true", help="ignorar el intervalo de 6 h")
    args = p.parse_args(argv)
    almacen = Almacen(args.db)
    for fuente, estado in capturar(almacen, forzar=args.forzar).items():
        print(f"{fuente}: {estado}")
    print(f"total guardadas: {len(almacen.todas())}")
    return 0


def ranking(argv: list[str]) -> int:
    from .ofertas.almacen import Almacen
    from .ranking.embeddings import ConCache, ollama
    from .ranking.preferencias import Preferencias
    from .ranking.ranking import ordenar

    p = argparse.ArgumentParser(prog="carrera ranking")
    p.add_argument("cv", type=Path)
    p.add_argument("--prefs", type=Path, help="YAML de reglas duras")
    p.add_argument("--db", default="data/ofertas.db")
    p.add_argument("--top", type=int, default=15)
    args = p.parse_args(argv)
    pref = Preferencias.model_validate(yaml.safe_load(args.prefs.read_text("utf-8"))) if args.prefs \
        else Preferencias()
    almacen = Almacen(args.db)
    resultados = ordenar(cargar(args.cv), almacen.todas(), pref, ConCache(ollama, almacen.db))
    vivas = [r for r in resultados if r.excluida is None]
    print(f"{len(vivas)} candidatas, {len(resultados) - len(vivas)} descartadas por reglas")
    for r in vivas[: args.top]:
        o = r.oferta
        print(f"{r.puntaje:5.1f}  {o.titulo} - {o.empresa}  [{o.fuente}]\n       "
              f"coinciden: {', '.join(r.coinciden) or '-'}\n       {o.url}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["ofertas"]:
        return ofertas(argv[1:])
    if argv[:1] == ["ranking"]:
        return ranking(argv[1:])
    p = argparse.ArgumentParser(prog="carrera")
    p.add_argument("cv", type=Path, help="YAML con la hoja de vida")
    p.add_argument("--salida", type=Path, default=Path("build"))
    p.add_argument("--solo-tex", action="store_true", help="no compilar a PDF")
    args = p.parse_args(argv)
    try:
        cv = cargar(args.cv)
    except ValidationError as e:
        print(e, file=sys.stderr)
        return 2
    args.salida.mkdir(parents=True, exist_ok=True)
    tex = args.salida / "cv.tex"
    tex.write_text(renderizar(cv), "utf-8")
    if not args.solo_tex:
        print(compilar(tex))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
