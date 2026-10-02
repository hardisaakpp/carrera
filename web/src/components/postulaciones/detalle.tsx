"use client";

import { ExternalLink, Loader2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { command, request, requestPdf } from "@/lib/api";
import { ETIQUETA_ESTADO, SIGUIENTES, TONO_ESTADO } from "@/lib/estado";
import { postulacionesSchema, postulacionSchema } from "@/lib/schemas";
import { Badge, Button, Card, Notice, PageHeader, Textarea } from "../ui";

type Ficha = {
  clave: string;
  carta: string;
  estado: keyof typeof ETIQUETA_ESTADO;
  titulo: string;
  empresa: string;
  url: string;
};

async function traer(clave: string): Promise<Ficha> {
  const [detalle, todas] = await Promise.all([
    request(postulacionSchema, `/postulaciones/${clave}`),
    request(postulacionesSchema, "/postulaciones"),
  ]);
  const resumen = todas.find((p) => p.clave === clave);
  if (!resumen) throw new Error("No se encontró la postulación.");
  return {
    ...detalle,
    titulo: resumen.titulo,
    empresa: resumen.empresa,
    url: resumen.url,
  };
}

export function DetallePostulacion({ clave }: { clave: string }) {
  const [ficha, setFicha] = useState<Ficha | null>(null);
  const [carta, setCarta] = useState("");
  const [pdf, setPdf] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const pdfUrl = useRef<string | null>(null);

  const aplicar = (f: Ficha) => {
    setFicha(f);
    setCarta(f.carta);
  };
  const cargar = async () => aplicar(await traer(clave));

  useEffect(() => {
    let vigente = true;
    traer(clave)
      .then((f) => vigente && aplicar(f))
      .catch((e: Error) => vigente && setError(e.message));
    return () => {
      vigente = false;
      if (pdfUrl.current) URL.revokeObjectURL(pdfUrl.current);
    };
  }, [clave]);

  const run = async (
    key: string,
    action: () => Promise<void>,
    message?: string,
  ) => {
    setBusy(key);
    setError(null);
    setAviso(null);
    try {
      await action();
      if (message) setAviso(message);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Algo falló.");
    } finally {
      setBusy(null);
    }
  };

  const verPdf = () =>
    run("pdf", async () => {
      const url = URL.createObjectURL(
        await requestPdf(`/postulaciones/${clave}/cv.pdf`),
      );
      if (pdfUrl.current) URL.revokeObjectURL(pdfUrl.current);
      pdfUrl.current = url;
      setPdf(url);
    });

  if (!ficha)
    return (
      <p className="text-sm text-muted-foreground">{error ?? "Cargando…"}</p>
    );
  const cambiada = carta !== ficha.carta;

  return (
    <div className="space-y-6">
      <Link
        href="/postulaciones"
        className="text-sm text-muted-foreground hover:underline"
      >
        ← Postulaciones
      </Link>
      <PageHeader
        title={ficha.titulo}
        description={ficha.empresa}
        actions={
          <Badge tone={TONO_ESTADO[ficha.estado]}>
            {ETIQUETA_ESTADO[ficha.estado]}
          </Badge>
        }
      />
      {error && <Notice tone="error">{error}</Notice>}
      {aviso && <Notice>{aviso}</Notice>}

      <Notice>
        carrera no envía nada. Revisa tu hoja de vida y la carta, aplica en la
        página de la oferta y después márcala aquí.
      </Notice>

      <div className="grid items-start gap-6 xl:grid-cols-2">
        <div className="space-y-6">
          <Card className="space-y-3">
            <h2 className="text-base font-semibold">Carta de presentación</h2>
            <p className="text-xs text-muted-foreground">
              Sale de una plantilla con datos de tu hoja de vida; solo menciona
              tecnologías que tú declaraste. Puedes retocarla.
            </p>
            <Textarea
              rows={14}
              value={carta}
              onChange={(e) => setCarta(e.target.value)}
            />
            <Button
              variant="outline"
              disabled={!cambiada || busy !== null}
              onClick={() =>
                run(
                  "carta",
                  async () => {
                    await command(`/postulaciones/${clave}/carta`, "PUT", {
                      carta,
                    });
                    setFicha({ ...ficha, carta });
                  },
                  "Carta guardada.",
                )
              }
            >
              {busy === "carta" && <Loader2 className="size-4 animate-spin" />}
              Guardar carta
            </Button>
          </Card>

          <Card className="space-y-3">
            <h2 className="text-base font-semibold">Siguiente paso</h2>
            <a
              href={ficha.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-primary underline"
            >
              Abrir la oferta para aplicar <ExternalLink className="size-3.5" />
            </a>
            <div className="flex flex-wrap gap-2">
              {SIGUIENTES[ficha.estado].map(({ accion, texto }) => (
                <Button
                  key={accion}
                  variant={accion === "descartar" ? "danger" : "primary"}
                  disabled={busy !== null}
                  onClick={() =>
                    run(accion, async () => {
                      await command(`/postulaciones/${clave}/${accion}`);
                      await cargar();
                    })
                  }
                >
                  {busy === accion && (
                    <Loader2 className="size-4 animate-spin" />
                  )}
                  {texto}
                </Button>
              ))}
              {SIGUIENTES[ficha.estado].length === 0 && (
                <p className="text-sm text-muted-foreground">
                  Este estado es definitivo.
                </p>
              )}
            </div>
          </Card>
        </div>

        <Card className="space-y-3 p-3">
          <div className="flex items-center justify-between gap-3 px-2 pt-1">
            <h2 className="text-base font-semibold">
              Hoja de vida para esta oferta
            </h2>
            <Button variant="outline" onClick={verPdf} disabled={busy !== null}>
              {busy === "pdf" && <Loader2 className="size-4 animate-spin" />}
              {pdf ? "Actualizar" : "Ver PDF"}
            </Button>
          </div>
          {pdf ? (
            <iframe
              title="Hoja de vida adaptada"
              src={pdf}
              className="h-[75vh] w-full rounded-lg"
            />
          ) : (
            <p className="p-10 text-center text-sm text-muted-foreground">
              Es la misma hoja de vida, mostrando primero lo más relevante para
              esta oferta.
            </p>
          )}
        </Card>
      </div>
    </div>
  );
}
