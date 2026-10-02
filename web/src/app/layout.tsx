import type { Metadata } from "next";
import { Geist } from "next/font/google";
import { Nav } from "@/components/nav";
import "./globals.css";

const geist = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "carrera",
  description:
    "Tu hoja de vida, tus ofertas y tus postulaciones en un solo lugar.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${geist.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col md:flex-row">
        <Nav />
        <main className="min-w-0 flex-1 p-6 md:p-8">{children}</main>
      </body>
    </html>
  );
}
