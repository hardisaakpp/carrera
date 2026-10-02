import type { Estado } from "./schemas";

export const ETIQUETA_ESTADO: Record<Estado, string> = {
  borrador: "Borrador",
  confirmada: "Confirmada",
  enviada: "Enviada",
  descartada: "Descartada",
};

export const TONO_ESTADO: Record<Estado, "neutral" | "warn" | "good" | "bad"> =
  {
    borrador: "neutral",
    confirmada: "warn",
    enviada: "good",
    descartada: "bad",
  };

/** Same rules as the server: nothing is "sent" without being confirmed first. */
export const SIGUIENTES: Record<
  Estado,
  { accion: "confirmar" | "enviada" | "descartar"; texto: string }[]
> = {
  borrador: [
    { accion: "confirmar", texto: "Confirmar que la revisé" },
    { accion: "descartar", texto: "Descartar" },
  ],
  confirmada: [
    { accion: "enviada", texto: "Marcar como enviada" },
    { accion: "descartar", texto: "Descartar" },
  ],
  enviada: [],
  descartada: [],
};
