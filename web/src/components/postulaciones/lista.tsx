"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { request } from "@/lib/api";
import { ETIQUETA_ESTADO, TONO_ESTADO } from "@/lib/estado";
import { postulacionesSchema } from "@/lib/schemas";
import { Badge, Card, Notice, PageHeader } from "../ui";

export function ListaPostulaciones() {
  const [items, setItems] = useState<Awaited<ReturnType<typeof load>> | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    load()
      .then(setItems)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Postulaciones"
        description="El seguimiento de lo que preparaste. carrera no envía nada: tú aplicas en la página de la oferta y aquí lo marcas."
      />
      {error && <Notice tone="error">{error}</Notice>}
      {items?.length === 0 && (
        <Card>
          <p className="text-sm text-muted-foreground">
            Todavía no preparaste ninguna. Empieza desde{" "}
            <Link className="underline" href="/ofertas">
              Ofertas
            </Link>
            .
          </p>
        </Card>
      )}
      <ul className="space-y-3">
        {items?.map((p) => (
          <li key={p.clave}>
            <Link href={`/postulaciones/${p.clave}`}>
              <Card className="flex items-center justify-between gap-4 transition-colors hover:bg-muted/50">
                <div className="min-w-0">
                  <h3 className="truncate font-medium">{p.titulo}</h3>
                  <p className="text-sm text-muted-foreground">{p.empresa}</p>
                </div>
                <Badge tone={TONO_ESTADO[p.estado]}>
                  {ETIQUETA_ESTADO[p.estado]}
                </Badge>
              </Card>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

const load = () => request(postulacionesSchema, "/postulaciones");
