"""Mide el ranking contra ofertas etiquetadas (relevante sí/no). Usa el embedder real.

    .venv/bin/python eval/run.py [eval/etiquetadas.yaml] [data/ejemplo.yaml]
"""
import sys
from pathlib import Path

import yaml

from carrera.modelo import Cv
from carrera.ofertas.modelo import Oferta
from carrera.ranking.embeddings import ollama
from carrera.ranking.preferencias import Preferencias
from carrera.ranking.ranking import ordenar

etiquetadas = Path(sys.argv[1] if len(sys.argv) > 1 else "eval/etiquetadas.yaml")
cv = Cv.model_validate(yaml.safe_load(Path(sys.argv[2] if len(sys.argv) > 2 else "data/ejemplo.yaml").read_text("utf-8")))
filas = yaml.safe_load(etiquetadas.read_text("utf-8"))
ofertas = [Oferta(fuente="eval", id_fuente=str(i), url="https://example.com", titulo=f["titulo"],
                  empresa="X", etiquetas=f["etiquetas"], descripcion=f["descripcion"])
           for i, f in enumerate(filas)]
relevantes = {o.id_fuente for o, f in zip(ofertas, filas) if f["relevante"]}
r = ordenar(cv, ofertas, Preferencias(), ollama)
n = len(relevantes)
for k in (3, 5, n):
    aciertos = sum(x.oferta.id_fuente in relevantes for x in r[:k])
    print(f"precision@{k}: {aciertos}/{k}")
mejor_irrelevante = max(x.puntaje for x in r if x.oferta.id_fuente not in relevantes)
peor_relevante = min(x.puntaje for x in r if x.oferta.id_fuente in relevantes)
print(f"peor relevante {peor_relevante} | mejor irrelevante {mejor_irrelevante}")
for x in r:
    marca = "OK " if x.oferta.id_fuente in relevantes else "   "
    print(f"{marca}{x.puntaje:5.1f}  cos={x.similitud:.2f}  {x.oferta.titulo}")
