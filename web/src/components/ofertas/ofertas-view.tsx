"use client";

import { ExternalLink, Loader2, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { command, request } from "@/lib/api";
import { ETIQUETA_ESTADO, TONO_ESTADO } from "@/lib/estado";
import {
  preferenciasSchema,
  rankingSchema,
  resultadoCapturaSchema,
  type Preferencias,
  type Ranking,
} from "@/lib/schemas";
import { Badge, Button, Card, Notice, PageHeader } from "../ui";
import { PreferenciasPanel } from "./preferencias-panel";

const FUENTE: Record<string, string> = {
  remotive: "Remotive",
  remoteok: "Remote OK",
  weworkremotely: "We Work Remotely",
};

function Puntaje({ valor }: { valor: number }) {
  return (
    <div
      className="w-24 shrink-0"
      title={`Afinidad con tu hoja de vida: ${valor} de 100`}
    >
      <div className="text-lg font-semibold tabular-nums">
        {Math.round(valor)}
      </div>
      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${Math.min(100, valor)}%` }}
        />
      </div>
    </div>
  );
}

export function OfertasView() {
  const router = useRouter();
  const [ranking, setRanking] = useState<Ranking | null>(null);
  const [prefs, setPrefs] = useState<Preferencias | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState<"load" | "refresh" | string | null>("load");

  const load = useCallback(async () => {
    setBusy("load");
    try {
      setRanking(await request(rankingSchema, "/ofertas"));
      setError(null);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "No se pudieron cargar las ofertas.",
      );
    } finally {
      setBusy(null);
    }
  }, []);

  useEffect(() => {
    // First load: `busy` already starts as "load", so nothing is set synchronously here.
    request(rankingSchema, "/ofertas")
      .then(setRanking)
      .catch((e: Error) => setError(e.message))
      .finally(() => setBusy(null));
    request(preferenciasSchema, "/preferencias")
      .then(setPrefs)
      .catch(() => undefined);
  }, []);

  // Offers whose affinity is still being computed in the background: ask again until none is left.
  const pendientes = ranking?.pendientes ?? 0;
  useEffect(() => {
    if (pendientes === 0) return;
    const timer = setTimeout(
      () =>
        request(rankingSchema, "/ofertas")
          .then(setRanking)
          .catch(() => undefined),
      4000,
    );
    return () => clearTimeout(timer);
  }, [pendientes, ranking]);

  const refresh = async () => {
    setBusy("refresh");
    setInfo(null);
    try {
      const result = await request(
        resultadoCapturaSchema,
        "/ofertas/actualizar",
        "POST",
      );
      setInfo(
        Object.entries(result)
          .map(([fuente, estado]) => `${FUENTE[fuente] ?? fuente}: ${estado}`)
          .join(" · "),
      );
      await load();
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "No se pudieron actualizar las ofertas.",
      );
      setBusy(null);
    }
  };

  const prepare = async (clave: string) => {
    setBusy(clave);
    try {
      await command(`/postulaciones/${clave}`);
      router.push(`/postulaciones/${clave}`);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "No se pudo preparar la postulación.",
      );
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Ofertas"
        description="Ordenadas por cercanía a tu hoja de vida. Cada oferta enlaza a su fuente original: allí aplicas tú."
        actions={
          <Button variant="outline" onClick={refresh} disabled={busy !== null}>
            {busy === "refresh" ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RefreshCw className="size-4" />
            )}
            Buscar ofertas nuevas
          </Button>
        }
      />
      {error && <Notice tone="error">{error}</Notice>}
      {info && (
        <Notice>
          {info}. Cada fuente se consulta como máximo una vez cada 6 horas.
        </Notice>
      )}

      {prefs && <PreferenciasPanel inicial={prefs} onSaved={load} />}

      {busy === "load" && !ranking && (
        <p className="text-sm text-muted-foreground">
          Calculando afinidad… la primera vez tarda unos segundos.
        </p>
      )}
      {ranking && (
        <>
          {pendientes > 0 && (
            <Notice>
              Calculando la afinidad de {pendientes} ofertas nuevas. Ya puedes
              ver el resto; esta lista se actualiza sola.
            </Notice>
          )}
          <p className="text-sm text-muted-foreground">
            {ranking.ofertas.length} mostradas de {ranking.total};{" "}
            {ranking.descartadas} descartadas por tus reglas.
          </p>
          {ranking.ofertas.length === 0 && (
            <Card>
              <p className="text-sm text-muted-foreground">
                Aún no hay ofertas. Pulsa «Buscar ofertas nuevas».
              </p>
            </Card>
          )}
          <ul className="space-y-3">
            {ranking.ofertas.map((o) => (
              <li key={o.clave}>
                <Card className="flex flex-wrap items-center gap-4">
                  <Puntaje valor={o.puntaje} />
                  <div className="min-w-0 flex-1 space-y-1.5">
                    <h3 className="font-medium">{o.titulo}</h3>
                    <p className="line-clamp-1 text-sm text-muted-foreground" title={o.ubicacion}>
                      {o.empresa}
                      {o.ubicacion && ` · ${o.ubicacion}`} ·{" "}
                      {FUENTE[o.fuente] ?? o.fuente}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {o.coinciden.length === 0 && (
                        <span className="text-xs text-muted-foreground">
                          Sin tecnologías en común
                        </span>
                      )}
                      {o.coinciden.map((t) => (
                        <Badge key={t} tone="good">
                          {t}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <a
                      href={o.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted"
                    >
                      Ver oferta <ExternalLink className="size-3.5" />
                    </a>
                    {o.estado ? (
                      <Link href={`/postulaciones/${o.clave}`}>
                        <Badge tone={TONO_ESTADO[o.estado]}>
                          {ETIQUETA_ESTADO[o.estado]}
                        </Badge>
                      </Link>
                    ) : (
                      <Button
                        onClick={() => prepare(o.clave)}
                        disabled={busy !== null}
                      >
                        {busy === o.clave && (
                          <Loader2 className="size-4 animate-spin" />
                        )}
                        Preparar postulación
                      </Button>
                    )}
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
