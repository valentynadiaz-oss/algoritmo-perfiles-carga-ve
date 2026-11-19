"""Descarga de la API del tablero EOD 2025: indicadores, matriz origen-destino (15),
estrato por macrozona (46) y mapa de macrozonas."""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import CRUDOS_EOD_API  # noqa: E402

BASE = "https://eod2025.metropol.gov.co"
INDICADORES = [*range(1, 30), *range(31, 40), *range(42, 47)]


def bajar(url, archivo=None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    datos = urllib.request.urlopen(req, timeout=120).read()
    if archivo:
        (CRUDOS_EOD_API / archivo).write_bytes(datos)
    return json.loads(datos)


def main():
    CRUDOS_EOD_API.mkdir(parents=True, exist_ok=True)
    for m in ("municipios", "temas", "indicadores"):
        bajar(f"{BASE}/api/api/metadata/{m}", f"meta_{m}.json")
    for i in INDICADORES:
        bajar(f"{BASE}/api/api/indicadores/{i}/agregado", f"ind_{i}.json")
    bajar(f"{BASE}/macrozonas_actualizado.geo.json", "macrozonas_actualizado.geo.json")

    codigos = json.loads((CRUDOS_EOD_API / "macrozonas_codigos.json").read_text(encoding="utf-8"))
    estrato = {}
    for cod, v in codigos.items():
        if cod == "67":                     # «Sin especificar»
            continue
        q = urllib.parse.urlencode({"municipio": v["municipio"], "macrozona": cod})
        d = bajar(f"{BASE}/api/api/indicadores/46/agregado?{q}")
        estrato[cod] = {"municipio": v["municipio"], "macrozona": v["macrozona"],
                        "grupos": d.get("grupos")}
    (CRUDOS_EOD_API / "ind_46_estrato_por_macrozona.json").write_text(
        json.dumps(estrato, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ok:", CRUDOS_EOD_API)


if __name__ == "__main__":
    main()
