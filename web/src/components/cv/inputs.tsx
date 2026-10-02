"use client";

import { Plus, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { Button, Field, Input, Textarea } from "../ui";

const parts = (text: string, separator: RegExp) =>
  text
    .split(separator)
    .map((p) => p.trim())
    .filter(Boolean);

/** Comma-separated values. The raw text stays local so typing a comma or space is never swallowed. */
export function ListInput({
  label,
  hint,
  value,
  onChange,
}: {
  label: string;
  hint?: string;
  value: string[];
  onChange: (value: string[]) => void;
}) {
  const [text, setText] = useState(value.join(", "));
  return (
    <Field label={label} hint={hint ?? "Separadas por comas"}>
      <Input
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          onChange(parts(e.target.value, /,/));
        }}
        onBlur={() => setText(value.join(", "))}
      />
    </Field>
  );
}

/** One item per line. */
export function LinesInput({
  label,
  hint,
  value,
  onChange,
}: {
  label: string;
  hint?: string;
  value: string[];
  onChange: (value: string[]) => void;
}) {
  const [text, setText] = useState(value.join("\n"));
  return (
    <Field label={label} hint={hint ?? "Uno por línea"}>
      <Textarea
        rows={Math.max(3, value.length + 1)}
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          onChange(parts(e.target.value, /\n/));
        }}
        onBlur={() => setText(value.join("\n"))}
      />
    </Field>
  );
}

export function Repeater<T>({
  items,
  onChange,
  blank,
  addLabel,
  itemLabel,
  render,
}: {
  items: T[];
  onChange: (items: T[]) => void;
  blank: () => T;
  addLabel: string;
  itemLabel: string;
  render: (item: T, update: (patch: Partial<T>) => void) => ReactNode;
}) {
  return (
    <div className="space-y-4">
      {items.map((item, index) => (
        // Index keys are safe here: items have no identity of their own and rows are only removed on request.
        <div
          key={index}
          className="relative space-y-3 rounded-lg border border-border bg-muted/40 p-4"
        >
          <Button
            type="button"
            variant="ghost"
            className="absolute top-2 right-2 size-8 p-0"
            aria-label={`Quitar ${itemLabel} ${index + 1}`}
            onClick={() => onChange(items.filter((_, i) => i !== index))}
          >
            <X className="size-4" />
          </Button>
          {render(item, (patch) =>
            onChange(
              items.map((it, i) => (i === index ? { ...it, ...patch } : it)),
            ),
          )}
        </div>
      ))}
      <Button
        type="button"
        variant="outline"
        onClick={() => onChange([...items, blank()])}
      >
        <Plus className="size-4" />
        {addLabel}
      </Button>
    </div>
  );
}
