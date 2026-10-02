"use client";

import { Briefcase, FileText, Send } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cx } from "./ui";

const LINKS = [
  { href: "/cv", label: "Hoja de vida", icon: FileText },
  { href: "/ofertas", label: "Ofertas", icon: Briefcase },
  { href: "/postulaciones", label: "Postulaciones", icon: Send },
];

export function Nav() {
  const path = usePathname();
  return (
    <aside className="flex shrink-0 flex-col gap-6 bg-sidebar p-4 text-sidebar-foreground md:w-60">
      <div className="px-2 text-lg font-semibold tracking-tight">carrera</div>
      <nav className="flex gap-1 md:flex-col" aria-label="Principal">
        {LINKS.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            aria-current={path.startsWith(href) ? "page" : undefined}
            className={cx(
              "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/10",
              path.startsWith(href) && "bg-white/15 font-medium",
            )}
          >
            <Icon className="size-4" />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
