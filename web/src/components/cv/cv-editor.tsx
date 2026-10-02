"use client";

import { Loader2, Save } from "lucide-react";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { command, request, requestPdf } from "@/lib/api";
import { cvResponseSchema, type Cv } from "@/lib/schemas";
import {
  Button,
  Card,
  Field,
  Input,
  Notice,
  PageHeader,
  Textarea,
} from "../ui";
import {
  ContactSection,
  EducationSection,
  ExperienceSection,
  ProjectsSection,
  SkillsSection,
} from "./sections";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card className="space-y-4">
      <h2 className="text-base font-semibold">{title}</h2>
      {children}
    </Card>
  );
}

export function CvEditor() {
  const [cv, setCv] = useState<Cv | null>(null);
  const [sample, setSample] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState<"save" | "pdf" | null>(null);
  const [pdf, setPdf] = useState<string | null>(null);
  const pdfUrl = useRef<string | null>(null);

  useEffect(() => {
    request(cvResponseSchema, "/cv")
      .then((r) => {
        setCv(r.cv);
        setSample(r.ejemplo);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(
    () => () => void (pdfUrl.current && URL.revokeObjectURL(pdfUrl.current)),
    [],
  );

  const edit = useCallback((patch: Partial<Cv>) => {
    setCv((current) => (current ? { ...current, ...patch } : current));
    setSaved(false);
  }, []);

  const preview = async (current: Cv) => {
    setBusy("pdf");
    setError(null);
    try {
      const url = URL.createObjectURL(await requestPdf("/cv/pdf", current));
      if (pdfUrl.current) URL.revokeObjectURL(pdfUrl.current);
      pdfUrl.current = url;
      setPdf(url);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "No se pudo generar la vista previa.",
      );
    } finally {
      setBusy(null);
    }
  };

  const save = async (current: Cv) => {
    setBusy("save");
    setError(null);
    try {
      await command("/cv", "PUT", current);
      setSaved(true);
      setSample(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo guardar.");
    } finally {
      setBusy(null);
    }
  };

  if (!cv)
    return (
      <p className="text-sm text-muted-foreground">{error ?? "Cargando…"}</p>
    );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Hoja de vida"
        description="Edita tus datos una sola vez. De aquí salen el PDF, las versiones adaptadas a cada oferta y las cartas."
        actions={
          <>
            <Button
              variant="outline"
              onClick={() => preview(cv)}
              disabled={busy !== null}
            >
              {busy === "pdf" && <Loader2 className="size-4 animate-spin" />}
              Vista previa
            </Button>
            <Button onClick={() => save(cv)} disabled={busy !== null}>
              {busy === "save" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Save className="size-4" />
              )}
              Guardar
            </Button>
          </>
        }
      />
      {sample && (
        <Notice>
          Estás viendo datos de ejemplo. Edítalos y guarda para crear tu hoja de
          vida.
        </Notice>
      )}
      {error && <Notice tone="error">{error}</Notice>}
      {saved && <Notice>Guardado.</Notice>}

      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="space-y-6">
          <Section title="Datos principales">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Nombre completo">
                <Input
                  value={cv.nombre}
                  onChange={(e) => edit({ nombre: e.target.value })}
                />
              </Field>
              <Field label="Titular" hint="Una línea: tu puesto o especialidad">
                <Input
                  value={cv.titular}
                  onChange={(e) => edit({ titular: e.target.value })}
                />
              </Field>
            </div>
            <Field label="Resumen">
              <Textarea
                rows={4}
                value={cv.resumen}
                onChange={(e) => edit({ resumen: e.target.value })}
              />
            </Field>
          </Section>
          <Section title="Contacto">
            <ContactSection
              value={cv.contacto}
              onChange={(contacto) => edit({ contacto })}
            />
          </Section>
          <Section title="Experiencia">
            <ExperienceSection
              value={cv.experiencia}
              onChange={(experiencia) => edit({ experiencia })}
            />
          </Section>
          <Section title="Proyectos">
            <ProjectsSection
              value={cv.proyectos}
              onChange={(proyectos) => edit({ proyectos })}
            />
          </Section>
          <Section title="Educación">
            <EducationSection
              value={cv.educacion}
              onChange={(educacion) => edit({ educacion })}
            />
          </Section>
          <Section title="Habilidades">
            <SkillsSection
              value={cv.habilidades}
              onChange={(habilidades) => edit({ habilidades })}
            />
          </Section>
        </div>

        <div className="xl:sticky xl:top-6">
          <Card className="p-2">
            {pdf ? (
              <iframe
                title="Vista previa del PDF"
                src={pdf}
                className="h-[80vh] w-full rounded-lg"
              />
            ) : (
              <p className="p-10 text-center text-sm text-muted-foreground">
                Pulsa «Vista previa» para ver tu hoja de vida como PDF. La
                primera vez tarda unos segundos.
              </p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
