# carrera

Hoja de vida como **datos** (YAML validado) → **LaTeX** → **PDF**, y base para un
agente que busca, clasifica y prepara postulaciones a empleos.

## Estado

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Esquema del CV, plantilla LaTeX, compilación a PDF en Docker | hecha |
| 2 | Captura de ofertas (Remotive, RemoteOK, We Work Remotely), texto plano, deduplicación, intervalo de 6 h | hecha |
| 3 | Ranking: reglas duras + embeddings bge-m3 + tecnologías en común, con explicación por oferta | hecha (falta evaluar con tus etiquetas) |
| 4 | CV adaptado por oferta: el modelo solo elige y ordena, una compuerta verifica contra el YAML | hecha |
| 5 | Postulación asistida: borrador (CV + carta), seguimiento por estados, nunca envía | hecha |
| 6 | Interfaz web: editor de hoja de vida con PDF, ofertas ordenadas, postulaciones | hecha |

## Interfaz web

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'   # una vez
(cd web && npm install)                                        # una vez
./dev.sh                                                       # API en :8920 y web en http://localhost:3010
```

- **Hoja de vida:** formulario por secciones con vista previa en PDF. Guarda en `data/cv.local.yaml`.
- **Ofertas:** lista ordenada por afinidad, con las tecnologías en común y el enlace a la fuente. Aquí defines las
  reglas que descartan ofertas y pulsas «Preparar postulación». La primera vez calcula la afinidad en segundo plano
  (unos minutos para ~120 ofertas); la pantalla se actualiza sola.
- **Postulaciones:** carta editable, PDF adaptado y los estados. Nada se envía desde aquí.
- La API escucha solo en `127.0.0.1` y no tiene cuentas: es una herramienta personal. La web habla únicamente con
  su propio servidor, que reenvía `/api` a la API.

## Uso por línea de comandos

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

## Ofertas (fase 2)

```bash
.venv/bin/carrera ofertas            # consulta las fuentes (máx. 1 vez cada 6 h por fuente)
.venv/bin/carrera ofertas --forzar
```

- Solo feeds/APIs públicos, por https y con tope de tamaño. Cada oferta conserva su URL
  original: las tres fuentes exigen enlazar de vuelta y citarlas como origen. Mostrar
  la fuente en cualquier interfaz es obligatorio.
- El HTML de cada oferta se convierte a texto plano (sin scripts ni marcado).
- La misma vacante en varias fuentes colapsa por empresa + título normalizados.
- Un fallo de una fuente no detiene a las demás. Se guardan en `data/ofertas.db` (SQLite, no versionada).
- LinkedIn e Indeed no tienen acceso permitido: quedarían como entrada manual (pegar el texto).
- RemoteOK no filtra por categoría, así que entran ofertas ajenas al perfil; las filtra el ranking (fase 3).

## Ranking (fase 3)

```bash
.venv/bin/carrera ranking data/ejemplo.yaml --prefs data/preferencias.ejemplo.yaml --top 10
.venv/bin/python eval/run.py          # precisión contra ofertas etiquetadas
```

- **Reglas duras** (`Preferencias`): títulos/textos excluidos, ubicaciones, tecnologías obligatorias.
  Una oferta descartada conserva el motivo.
- **Puntaje 0-100** = 60 % afinidad semántica (coseno CV↔oferta, bge-m3) + 40 % tecnologías
  del CV mencionadas en la oferta. La explicación (qué coincide) sale de datos, no de un modelo.
- Los vectores se guardan en caché (SQLite) por hash del texto.
- Los embeddings corren en **CPU** (`num_gpu: 0`): con la GPU, bge-m3 devolvió NaN (HTTP 500)
  para textos cortos como "Senior Java Developer…". Aplica a cualquier proyecto que use
  bge-m3 con este Ollama.

**Medición.** En `eval/etiquetadas.yaml` (24 ofertas sintéticas escritas por mí) acierta
precision@10 = 10/10, pero el margen es mínimo (peor relevante 58.7, mejor irrelevante 58.6)
y el conjunto es optimista: no sustituye a ofertas reales etiquetadas por ti.

**Limitación conocida.** Ofertas con una lista genérica de tecnologías (p. ej. "Senior Data Scientist"
de Lemon.io, que enumera .NET, Next.js, etc.) puntúan alto por coincidencias que no describen el puesto.
Solución prevista: ponderar más título y etiquetas que el cuerpo, y calibrar con etiquetas reales.

## CV por oferta (fase 4)

```bash
.venv/bin/carrera adaptar data/ejemplo.yaml --oferta <id>   # id que imprime `ranking`
```

El modelo (qwen3:8b, salida JSON con esquema) **no escribe texto**: devuelve qué logros y
proyectos mostrar y qué tecnologías destacar. `aplicar` descarta índices o nombres que no
existan y `verificar.problemas` compara el resultado contra el YAML (cargos, fechas, logros,
tecnologías, educación, resumen). Si el modelo falla o algo no cuadra, se usa el original.
Tests: modelo mentiroso, modelo caído y oferta con instrucciones.

## Postulación asistida (fase 5)

```bash
carrera postular crear     --oferta <id> --cv data/cv.local.yaml   # carpeta con cv.pdf, carta.txt, oferta.txt
carrera postular confirmar --oferta <id>
carrera postular enviada   --oferta <id>    # lo marcas tú después de aplicar en la web de la oferta
carrera postular listar
```

- La **carta es determinista** (plantilla + datos verificados): solo nombra tecnologías que están en
  tu CV y en la oferta, así que una oferta no puede hacerla afirmar nada falso.
- Estados `borrador → confirmada → enviada | descartada`; saltarse la confirmación no se permite.
- **La herramienta no envía nada.** Aplicas tú en la URL de la oferta; así no arriesgas tu cuenta
  en las plataformas ni envías algo sin revisar.
- Tu CV real va en `data/cv.local.yaml` (ignorado por git).
