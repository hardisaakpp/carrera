import shutil
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from carrera.api import Ajustes, crear_app
from carrera.ofertas.almacen import Almacen
from carrera.ofertas.modelo import Oferta

EJEMPLO = Path(__file__).parent.parent / "data" / "ejemplo.yaml"


def embedder(textos):
    claves = ["backend", "api", "sales", "net"]
    return [[float(k in t.lower()) for k in claves] for t in textos]


def compilador(tex: Path) -> Path:
    pdf = tex.with_suffix(".pdf")
    pdf.write_bytes(b"%PDF-falso")
    return pdf


@pytest.fixture
def cliente(tmp_path):
    ajustes = Ajustes(tmp_path, embedder=embedder, compilador=compilador)
    almacen = ajustes.almacen()
    almacen.guardar([
        Oferta(fuente="t", id_fuente="1", url="https://x/1", titulo="Backend API engineer",
               empresa="Acme", descripcion="APIs en .NET y SQL Server"),
        Oferta(fuente="t", id_fuente="2", url="https://x/2", titulo="Sales rep", empresa="Foo",
               descripcion="ventas"),
    ])
    return TestClient(crear_app(ajustes)), ajustes, almacen


def test_cv_de_ejemplo_hasta_que_se_guarda_el_propio(cliente):
    c, ajustes, _ = cliente
    r = c.get("/api/cv").json()
    assert r["ejemplo"] is True
    cv = r["cv"]
    cv["nombre"] = "Otra Persona"
    assert c.put("/api/cv", json=cv).status_code == 200
    r = c.get("/api/cv").json()
    assert r["ejemplo"] is False and r["cv"]["nombre"] == "Otra Persona"
    assert yaml.safe_load(ajustes.cv.read_text("utf-8"))["nombre"] == "Otra Persona"


def test_rechaza_cv_invalido_o_con_campos_extra(cliente):
    c, _, _ = cliente
    cv = c.get("/api/cv").json()["cv"]
    assert c.put("/api/cv", json={**cv, "salario": 1}).status_code == 422
    assert c.put("/api/cv", json={"nombre": "x"}).status_code == 422


def test_pdf_de_vista_previa(cliente):
    c, _, _ = cliente
    r = c.post("/api/cv/pdf", json=c.get("/api/cv").json()["cv"])
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"


def esperar_ranking(c, intentos=50):
    import time
    for _ in range(intentos):
        r = c.get("/api/ofertas").json()
        if r["pendientes"] == 0:
            return r
        time.sleep(0.1)
    raise AssertionError("el cálculo en segundo plano no terminó")


def test_primera_vez_calcula_en_segundo_plano_y_luego_responde_completo(cliente):
    c, _, _ = cliente
    primera = c.get("/api/ofertas").json()
    assert primera["total"] == 2 and primera["pendientes"] in (0, 1, 2)
    final = esperar_ranking(c)
    assert len(final["ofertas"]) == 2 and final["ofertas"][0]["titulo"] == "Backend API engineer"


def test_ranking_ordena_y_aplica_preferencias(cliente):
    c, _, _ = cliente
    r = esperar_ranking(c)
    assert [o["titulo"] for o in r["ofertas"]][0] == "Backend API engineer"
    c.put("/api/preferencias", json={"excluir_titulos": ["sales"]})
    r = esperar_ranking(c)
    assert r["descartadas"] == 1 and len(r["ofertas"]) == 1


def test_flujo_de_postulacion_completo(cliente):
    c, _, almacen = cliente
    clave = esperar_ranking(c)["ofertas"][0]["clave"]
    assert c.post(f"/api/postulaciones/{clave}").json()["estado"] == "borrador"
    assert c.get(f"/api/postulaciones/{clave}").json()["carta"].startswith("Estimado equipo de Acme")
    assert c.put(f"/api/postulaciones/{clave}/carta", json={"carta": "Mi carta"}).status_code == 200
    assert c.get(f"/api/postulaciones/{clave}").json()["carta"] == "Mi carta"
    assert c.get(f"/api/postulaciones/{clave}/cv.pdf").status_code == 200

    assert c.post(f"/api/postulaciones/{clave}/enviada").status_code == 409  # no se salta la confirmación
    assert c.post(f"/api/postulaciones/{clave}/confirmar").json()["estado"] == "confirmada"
    assert c.post(f"/api/postulaciones/{clave}/enviada").json()["estado"] == "enviada"
    assert c.post(f"/api/postulaciones/{clave}/descartar").status_code == 409
    assert c.get("/api/postulaciones").json()[0]["estado"] == "enviada"
    assert esperar_ranking(c)["ofertas"][0]["estado"] == "enviada"


def test_claves_malformadas_no_tocan_el_disco(cliente):
    c, _, _ = cliente
    for malo in ["..", "%2e%2e", "a" * 16 + "/x", "ZZZZZZZZZZZZZZZZ"]:
        assert c.get(f"/api/postulaciones/{malo}/cv.pdf").status_code == 404
    assert c.put("/api/postulaciones/0123456789abcdef/carta", json={"carta": "x"}).status_code == 422
    assert c.post("/api/postulaciones/0123456789abcdef/invento").status_code == 404
    assert c.post("/api/postulaciones/0123456789abcdef").status_code == 404


def test_carta_no_puede_ser_enorme(cliente):
    c, _, _ = cliente
    clave = esperar_ranking(c)["ofertas"][0]["clave"]
    c.post(f"/api/postulaciones/{clave}")
    assert c.put(f"/api/postulaciones/{clave}/carta", json={"carta": "x" * 9000}).status_code == 422
