import { DetallePostulacion } from "@/components/postulaciones/detalle";

export default async function PostulacionPage({
  params,
}: PageProps<"/postulaciones/[clave]">) {
  const { clave } = await params;
  return <DetallePostulacion clave={clave} />;
}
