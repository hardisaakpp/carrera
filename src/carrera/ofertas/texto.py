"""HTML de terceros -> texto plano. Nada de marcado llega más adelante."""

from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser

_BLOQUES = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "ul", "ol", "tr"}
_IGNORAR = {"script", "style", "iframe", "object"}


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self._ignorando = 0

    def handle_starttag(self, tag, attrs):
        if tag in _IGNORAR:
            self._ignorando += 1
        elif tag in _BLOQUES:
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if tag in _IGNORAR:
            self._ignorando = max(0, self._ignorando - 1)
        elif tag in _BLOQUES:
            self.partes.append("\n")

    def handle_data(self, data):
        if not self._ignorando:
            self.partes.append(data)


def a_texto(html: str, limite: int = 6000) -> str:
    p = _Extractor()
    p.feed(html or "")
    texto = unescape("".join(p.partes))
    texto = re.sub(r"[ \t\r\f\v]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n\n", texto).strip()
    return texto[:limite]
