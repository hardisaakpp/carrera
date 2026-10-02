import json

from carrera.ofertas.almacen import Almacen
from carrera.ofertas.captura import capturar
from carrera.ofertas.fuentes import remoteok, remotive, weworkremotely
from carrera.ofertas.modelo import Oferta
from carrera.ofertas.texto import a_texto

REMOTIVE = json.dumps({"jobs": [{
    "id": 1, "url": "https://remotive.com/j/1", "title": "Backend Engineer",
    "company_name": "Acme", "candidate_required_location": "Worldwide", "tags": ["dotnet"],
    "description": "<p>Build <b>APIs</b></p><script>alert(1)</script>",
    "publication_date": "2026-09-30T10:00:00"}]}).encode()
REMOTEOK = json.dumps([{"legal": "x"}, {
    "id": "9", "url": "https://remoteok.com/9", "position": "backend engineer", "company": "ACME",
    "tags": ["python"], "description": "<ul><li>SQL</li></ul>", "date": "2026-09-30T18:24:42+00:00",
}]).encode()
WWR = b"""<?xml version="1.0"?><rss><channel><item>
<title>Acme: Backend Engineer</title><region>Anywhere</region>
<link>https://weworkremotely.com/x</link><guid>x1</guid>
<pubDate>Tue, 30 Sep 2026 10:00:00 +0000</pubDate>
<description>&lt;p&gt;Hola &amp;amp; adios&lt;/p&gt;</description></item></channel></rss>"""


def test_html_a_texto_quita_scripts_y_marcado():
    t = a_texto("<p>Hola <b>mundo</b></p><script>x()</script><li>uno</li>")
    assert "script" not in t and "x()" not in t and "<" not in t
    assert "Hola mundo" in t and "uno" in t


def test_normalizan_las_tres_fuentes():
    a = remotive(http=lambda u: REMOTIVE)[0]
    b = remoteok(http=lambda u: REMOTEOK)[0]
    c = weworkremotely(http=lambda u: WWR)[0]
    assert (a.empresa, c.empresa, c.titulo) == ("Acme", "Acme", "Backend Engineer")
    assert "alert" not in a.descripcion and "Build APIs" in a.descripcion
    assert b.descripcion == "SQL" and c.descripcion == "Hola & adios"


def test_misma_vacante_en_tres_fuentes_colapsa():
    ofertas = [remotive(http=lambda u: REMOTIVE)[0], remoteok(http=lambda u: REMOTEOK)[0],
               weworkremotely(http=lambda u: WWR)[0]]
    assert len({o.clave for o in ofertas}) == 1
    al = Almacen(":memory:")
    assert al.guardar(ofertas) == 1
    assert al.guardar(ofertas) == 0
    assert len(al.todas()) == 1


def test_intervalo_y_aislamiento_de_errores():
    al = Almacen(":memory:")

    def http(url):
        if "remoteok" in url:
            raise OSError("sin red")
        return REMOTIVE if "remotive" in url else WWR

    r1 = capturar(al, http=http)
    assert r1["remoteok"].startswith("error") and "1 nuevas" in r1["remotive"]
    r2 = capturar(al, http=http)
    assert r2["remotive"].startswith("omitida") and r2["remoteok"].startswith("error")
    assert "nuevas" in capturar(al, ["remotive"], http=http, forzar=True)["remotive"]


def test_rechaza_http_plano():
    import pytest
    from carrera.ofertas.fuentes import http_get
    with pytest.raises(ValueError):
        http_get("http://remotive.com/api")


def test_modelo_es_estricto():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Oferta(fuente="x", id_fuente="1", url="u", titulo="t", empresa="e", otro=1)
