"use client";

import { useState } from "react";
import type { Cv } from "@/lib/schemas";
import { Field, Input, Textarea } from "../ui";
import { LinesInput, ListInput, Repeater } from "./inputs";

type Props<K extends keyof Cv> = {
  value: Cv[K];
  onChange: (value: Cv[K]) => void;
};

type LinkRow = { label: string; url: string };

export function ContactSection({ value, onChange }: Props<"contacto">) {
  // Rows live here because a new row has no label yet, and the stored shape (label -> url) cannot hold that.
  const [rows, setRows] = useState<LinkRow[]>(() =>
    Object.entries(value.enlaces).map(([label, url]) => ({ label, url })),
  );
  const setLinks = (next: LinkRow[]) => {
    setRows(next);
    onChange({
      ...value,
      enlaces: Object.fromEntries(
        next.filter((r) => r.label.trim()).map((r) => [r.label.trim(), r.url]),
      ),
    });
  };
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Correo">
          <Input
            type="email"
            value={value.email}
            onChange={(e) => onChange({ ...value, email: e.target.value })}
          />
        </Field>
        <Field label="Teléfono">
          <Input
            value={value.telefono ?? ""}
            onChange={(e) =>
              onChange({ ...value, telefono: e.target.value || null })
            }
          />
        </Field>
        <Field label="Ubicación">
          <Input
            value={value.ubicacion ?? ""}
            onChange={(e) =>
              onChange({ ...value, ubicacion: e.target.value || null })
            }
          />
        </Field>
      </div>
      <Repeater
        items={rows}
        onChange={setLinks}
        blank={() => ({ label: "", url: "" })}
        addLabel="Añadir enlace"
        itemLabel="enlace"
        render={(item, update) => (
          <div className="grid gap-3 sm:grid-cols-[1fr_2fr]">
            <Input
              placeholder="GitHub"
              aria-label="Etiqueta del enlace"
              value={item.label}
              onChange={(e) => update({ label: e.target.value })}
            />
            <Input
              placeholder="https://github.com/usuario"
              aria-label="Dirección del enlace"
              value={item.url}
              onChange={(e) => update({ url: e.target.value })}
            />
          </div>
        )}
      />
    </div>
  );
}

export function ExperienceSection({ value, onChange }: Props<"experiencia">) {
  return (
    <Repeater
      items={value}
      onChange={onChange}
      addLabel="Añadir experiencia"
      itemLabel="experiencia"
      blank={() => ({
        cargo: "",
        organizacion: "",
        desde: "",
        hasta: null,
        logros: [],
        tecnologias: [],
      })}
      render={(item, update) => (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Cargo">
              <Input
                value={item.cargo}
                onChange={(e) => update({ cargo: e.target.value })}
              />
            </Field>
            <Field label="Organización">
              <Input
                value={item.organizacion}
                onChange={(e) => update({ organizacion: e.target.value })}
              />
            </Field>
            <Field label="Desde" hint="Por ejemplo 2022-03">
              <Input
                value={item.desde}
                onChange={(e) => update({ desde: e.target.value })}
              />
            </Field>
            <Field label="Hasta" hint="Vacío si es tu trabajo actual">
              <Input
                value={item.hasta ?? ""}
                onChange={(e) => update({ hasta: e.target.value || null })}
              />
            </Field>
          </div>
          <LinesInput
            label="Logros"
            hint="Uno por línea, con resultados medibles si los hay"
            value={item.logros}
            onChange={(logros) => update({ logros })}
          />
          <ListInput
            label="Tecnologías"
            value={item.tecnologias}
            onChange={(tecnologias) => update({ tecnologias })}
          />
        </>
      )}
    />
  );
}

export function ProjectsSection({ value, onChange }: Props<"proyectos">) {
  return (
    <Repeater
      items={value}
      onChange={onChange}
      addLabel="Añadir proyecto"
      itemLabel="proyecto"
      blank={() => ({
        nombre: "",
        descripcion: "",
        url: null,
        tecnologias: [],
      })}
      render={(item, update) => (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Nombre">
              <Input
                value={item.nombre}
                onChange={(e) => update({ nombre: e.target.value })}
              />
            </Field>
            <Field label="Enlace">
              <Input
                value={item.url ?? ""}
                onChange={(e) => update({ url: e.target.value || null })}
              />
            </Field>
          </div>
          <Field label="Descripción">
            <Textarea
              rows={2}
              value={item.descripcion}
              onChange={(e) => update({ descripcion: e.target.value })}
            />
          </Field>
          <ListInput
            label="Tecnologías"
            value={item.tecnologias}
            onChange={(tecnologias) => update({ tecnologias })}
          />
        </>
      )}
    />
  );
}

export function EducationSection({ value, onChange }: Props<"educacion">) {
  return (
    <Repeater
      items={value}
      onChange={onChange}
      addLabel="Añadir estudio"
      itemLabel="estudio"
      blank={() => ({ titulo: "", institucion: "", desde: "", hasta: null })}
      render={(item, update) => (
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Título">
            <Input
              value={item.titulo}
              onChange={(e) => update({ titulo: e.target.value })}
            />
          </Field>
          <Field label="Institución">
            <Input
              value={item.institucion}
              onChange={(e) => update({ institucion: e.target.value })}
            />
          </Field>
          <Field label="Desde">
            <Input
              value={item.desde}
              onChange={(e) => update({ desde: e.target.value })}
            />
          </Field>
          <Field label="Hasta">
            <Input
              value={item.hasta ?? ""}
              onChange={(e) => update({ hasta: e.target.value || null })}
            />
          </Field>
        </div>
      )}
    />
  );
}

export function SkillsSection({ value, onChange }: Props<"habilidades">) {
  return (
    <Repeater
      items={value}
      onChange={onChange}
      addLabel="Añadir grupo"
      itemLabel="grupo"
      blank={() => ({ nombre: "", items: [] })}
      render={(item, update) => (
        <div className="grid gap-3 sm:grid-cols-[1fr_2fr]">
          <Field label="Grupo">
            <Input
              placeholder="Lenguajes"
              value={item.nombre}
              onChange={(e) => update({ nombre: e.target.value })}
            />
          </Field>
          <ListInput
            label="Habilidades"
            value={item.items}
            onChange={(items) => update({ items })}
          />
        </div>
      )}
    />
  );
}
