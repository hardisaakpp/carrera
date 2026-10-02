"use client";

import { useState } from "react";
import { command } from "@/lib/api";
import type { Preferencias } from "@/lib/schemas";
import { Button, Card, Notice } from "../ui";
import { ListInput } from "../cv/inputs";

export function PreferenciasPanel({
  inicial,
  onSaved,
}: {
  inicial: Preferencias;
  onSaved: () => void;
}) {
  const [prefs, setPrefs] = useState(inicial);
  const [state, setState] = useState<"idle" | "saving" | "saved" | string>(
    "idle",
  );

  const save = async () => {
    setState("saving");
    try {
      await command("/preferencias", "PUT", prefs);
      setState("saved");
      onSaved();
    } catch (e) {
      setState(e instanceof Error ? e.message : "No se pudo guardar.");
    }
  };

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-base font-semibold">
          Reglas que descartan una oferta
        </h2>
        <p className="text-sm text-muted-foreground">
          Lo que cumpla alguna de estas reglas no aparece en la lista.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <ListInput
          label="Títulos a excluir"
          hint="Por ejemplo: sales, recruiter"
          value={prefs.excluir_titulos}
          onChange={(excluir_titulos) =>
            setPrefs({ ...prefs, excluir_titulos })
          }
        />
        <ListInput
          label="Textos a excluir"
          hint="Por ejemplo: security clearance"
          value={prefs.excluir_texto}
          onChange={(excluir_texto) => setPrefs({ ...prefs, excluir_texto })}
        />
        <ListInput
          label="Ubicaciones aceptadas"
          hint="Vacío = cualquiera. Por ejemplo: worldwide, latam"
          value={prefs.ubicaciones}
          onChange={(ubicaciones) => setPrefs({ ...prefs, ubicaciones })}
        />
        <ListInput
          label="Tecnologías obligatorias"
          hint="La oferta debe mencionarlas todas"
          value={prefs.obligatorias}
          onChange={(obligatorias) => setPrefs({ ...prefs, obligatorias })}
        />
      </div>
      {state !== "idle" && state !== "saving" && state !== "saved" && (
        <Notice tone="error">{state}</Notice>
      )}
      {state === "saved" && <Notice>Reglas guardadas.</Notice>}
      <Button onClick={save} disabled={state === "saving"}>
        Guardar reglas
      </Button>
    </Card>
  );
}
