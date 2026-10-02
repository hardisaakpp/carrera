# carrera

Hoja de vida como **datos** (YAML validado) → **LaTeX** → **PDF**, y base para un
agente que busca, clasifica y prepara postulaciones a empleos.

## Estado

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Esquema del CV, plantilla LaTeX, compilación a PDF en Docker | hecha |
| 2 | Captura de ofertas (fuentes con API/RSS), normalización y deduplicación | pendiente |
| 3 | Ranking: embeddings (bge-m3) + reglas duras + explicación por oferta, medido con un set etiquetado | pendiente |
| 4 | CV adaptado por oferta (el modelo reordena y resalta, **nunca inventa**) | pendiente |
| 5 | Postulación asistida: borrador listo, la persona confirma y envía | pendiente |

## Uso

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/carrera data/ejemplo.yaml          # build/cv.tex y build/cv.pdf
.venv/bin/carrera data/ejemplo.yaml --solo-tex
.venv/bin/pytest
```

La compilación corre `latexmk` en un contenedor (`ghcr.io/xu-cheng/texlive-alpine`,
Docker Engine, sin red, con tu usuario, sin `shell-escape`). No hace falta instalar TeX.

## Decisiones

- **El YAML es la fuente de verdad.** El PDF se regenera; nunca se edita a mano.
  Las versiones por oferta (fase 4) serán vistas del mismo dato, no copias.
- **Todo texto se escapa** antes de entrar a LaTeX (`latex.escapar`). El contenido
  puede venir de una oferta o de un modelo, y un `\input{}` o `\write18` no debe ejecutarse.
  Hay tests de inyección.
- **Esquema estricto** (`extra="forbid"`): un campo mal escrito falla en vez de perderse.
- **Compilar aislado**: contenedor sin red y sin shell-escape, por la misma razón.

## Reglas para las fases con IA

Aprendidas construyendo Xia (el asistente de Stockline):

1. **El modelo propone, el código valida y ejecuta.** Las ofertas son texto no confiable:
   una oferta puede decir "ignora tus instrucciones". Se tratan como datos, sin
   pasar texto libre a herramientas con efectos.
2. **Nada inventado en el CV.** Toda afirmación adaptada debe poder rastrearse a un
   campo del YAML; se verifica por código (tecnologías, fechas, cargos), no por el modelo.
3. **Nunca se envía solo.** La fase 5 deja el borrador y un botón de confirmación;
   el envío masivo automático arriesga la cuenta en las plataformas y la reputación.
4. **Medir antes de creer.** El ranking se evalúa con ofertas etiquetadas por la
   persona (precisión@k), igual que `eval/` en Xia.
5. **Respetar las fuentes.** Solo APIs/RSS/feeds permitidos; sin saltar logins ni
   términos de servicio.

## Qué se reutiliza de Xia

Bucle de herramientas con validación, embeddings bge-m3 + pgvector, Ollama local,
cuota/auditoría y el arnés de evaluación. Es un producto aparte: Xia contesta
sobre documentación; este agente actúa sobre ofertas.
