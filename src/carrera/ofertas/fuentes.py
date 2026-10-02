"""Fuentes con feed/API pública y términos que permiten consumirlas.

Condiciones comunes: enlazar a la URL original y citar la fuente, y no
consultar con frecuencia (el almacén limita el intervalo).
"""

from __future__ import annotations

import json
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from .modelo import Oferta
from .texto import a_texto

Http = Callable[[str], bytes]
USER_AGENT = "carrera/0.1 (uso personal)"
MAX_BYTES = 8_000_000


def http_get(url: str) -> bytes:
    if not url.startswith("https://"):
        raise ValueError("solo https")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 (https verificado arriba)
        datos = r.read(MAX_BYTES + 1)
    if len(datos) > MAX_BYTES:
        raise ValueError("respuesta demasiado grande")
    return datos


def _fecha_iso(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return None


def remotive(http: Http = http_get, categoria: str = "software-dev") -> list[Oferta]:
    crudo = json.loads(http(f"https://remotive.com/api/remote-jobs?category={categoria}"))
    return [
        Oferta(
            fuente="remotive", id_fuente=str(j["id"]), url=j["url"], titulo=j["title"],
            empresa=j["company_name"], ubicacion=j.get("candidate_required_location") or "",
            etiquetas=list(j.get("tags") or []), descripcion=a_texto(j.get("description", "")),
            publicada=_fecha_iso(j.get("publication_date")),
        )
        for j in crudo.get("jobs", [])
    ]


def remoteok(http: Http = http_get) -> list[Oferta]:
    crudo = json.loads(http("https://remoteok.com/api"))
    ofertas = []
    for j in crudo:
        if "position" not in j:  # el primer elemento es el aviso legal
            continue
        ofertas.append(Oferta(
            fuente="remoteok", id_fuente=str(j["id"]), url=j["url"], titulo=j["position"],
            empresa=j.get("company", ""), ubicacion=j.get("location") or "",
            etiquetas=list(j.get("tags") or []), descripcion=a_texto(j.get("description", "")),
            publicada=_fecha_iso(j.get("date")),
        ))
    return ofertas


def weworkremotely(http: Http = http_get,
                   categoria: str = "remote-back-end-programming-jobs") -> list[Oferta]:
    raiz = ET.fromstring(http(f"https://weworkremotely.com/categories/{categoria}.rss"))  # noqa: S314
    ofertas = []
    for it in raiz.iter("item"):
        titulo = (it.findtext("title") or "").strip()
        empresa, _, puesto = titulo.partition(": ")
        if not puesto:
            empresa, puesto = "", titulo
        fecha = it.findtext("pubDate")
        ofertas.append(Oferta(
            fuente="weworkremotely", id_fuente=(it.findtext("guid") or it.findtext("link") or ""),
            url=(it.findtext("link") or "").strip(), titulo=puesto, empresa=empresa,
            ubicacion=(it.findtext("region") or "").strip(),
            descripcion=a_texto(it.findtext("description") or ""),
            publicada=parsedate_to_datetime(fecha).astimezone(timezone.utc) if fecha else None,
        ))
    return ofertas


FUENTES: dict[str, Callable[..., list[Oferta]]] = {
    "remotive": remotive,
    "remoteok": remoteok,
    "weworkremotely": weworkremotely,
}
