import { z } from "zod";

export const cvSchema = z.object({
  nombre: z.string(),
  titular: z.string(),
  resumen: z.string(),
  contacto: z.object({
    email: z.string(),
    telefono: z.string().nullish(),
    ubicacion: z.string().nullish(),
    enlaces: z.record(z.string(), z.string()),
  }),
  experiencia: z.array(
    z.object({
      cargo: z.string(),
      organizacion: z.string(),
      desde: z.string(),
      hasta: z.string().nullish(),
      logros: z.array(z.string()),
      tecnologias: z.array(z.string()),
    }),
  ),
  proyectos: z.array(
    z.object({
      nombre: z.string(),
      descripcion: z.string(),
      url: z.string().nullish(),
      tecnologias: z.array(z.string()),
    }),
  ),
  educacion: z.array(
    z.object({
      titulo: z.string(),
      institucion: z.string(),
      desde: z.string(),
      hasta: z.string().nullish(),
    }),
  ),
  habilidades: z.array(
    z.object({ nombre: z.string(), items: z.array(z.string()) }),
  ),
});
export type Cv = z.infer<typeof cvSchema>;

export const cvResponseSchema = z.object({
  cv: cvSchema,
  ejemplo: z.boolean(),
});

export const preferenciasSchema = z.object({
  excluir_titulos: z.array(z.string()),
  excluir_texto: z.array(z.string()),
  ubicaciones: z.array(z.string()),
  obligatorias: z.array(z.string()),
});
export type Preferencias = z.infer<typeof preferenciasSchema>;

export const ESTADOS = [
  "borrador",
  "confirmada",
  "enviada",
  "descartada",
] as const;
export type Estado = (typeof ESTADOS)[number];
const estadoSchema = z.enum(ESTADOS);

export const rankingSchema = z.object({
  total: z.number(),
  descartadas: z.number(),
  pendientes: z.number(),
  ofertas: z.array(
    z.object({
      clave: z.string(),
      titulo: z.string(),
      empresa: z.string(),
      ubicacion: z.string(),
      fuente: z.string(),
      url: z.string(),
      puntaje: z.number(),
      coinciden: z.array(z.string()),
      estado: estadoSchema.nullable(),
    }),
  ),
});
export type Ranking = z.infer<typeof rankingSchema>;

export const postulacionesSchema = z.array(
  z.object({
    clave: z.string(),
    estado: estadoSchema,
    titulo: z.string(),
    empresa: z.string(),
    url: z.string(),
  }),
);

export const postulacionSchema = z.object({
  clave: z.string(),
  carta: z.string(),
  estado: estadoSchema,
});

export const resultadoCapturaSchema = z.record(z.string(), z.string());
