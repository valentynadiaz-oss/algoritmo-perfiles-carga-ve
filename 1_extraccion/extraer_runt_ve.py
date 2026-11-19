"""VE e híbridos matriculados por municipio (RUNT 2.0, datos.gov.co ntxy-q9ix). Solo referencia."""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import CRUDOS_RUNT  # noqa: E402

MUNICIPIOS = ["MEDELLIN", "BELLO", "ITAGUI", "ENVIGADO", "SABANETA", "LA ESTRELLA", "CALDAS",
              "COPACABANA", "GIRARDOTA", "BARBOSA", "PEREIRA"]


def main():
    CRUDOS_RUNT.mkdir(parents=True, exist_ok=True)
    lista = ",".join(f"'{m}'" for m in MUNICIPIOS)
    q = urllib.parse.urlencode({
        "$select": "departamento,municipio,combustible,clase,sum(cantidad) as cantidad",
        "$where": f"municipio in({lista})",
        "$group": "departamento,municipio,combustible,clase", "$limit": "50000"})
    url = f"https://www.datos.gov.co/resource/ntxy-q9ix.json?{q}"
    d = json.loads(urllib.request.urlopen(url, timeout=120).read())
    df = pd.DataFrame(d)
    df["cantidad"] = df["cantidad"].astype(int)
    df.to_csv(CRUDOS_RUNT / "ve_matriculados_por_municipio.csv", index=False, encoding="utf-8-sig")
    resumen = df.pivot_table(index="municipio", columns="combustible", values="cantidad",
                             aggfunc="sum", fill_value=0)
    print(resumen)


if __name__ == "__main__":
    main()
