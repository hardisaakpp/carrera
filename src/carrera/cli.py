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


def main(argv: list[str] | None = None) -> int:
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
