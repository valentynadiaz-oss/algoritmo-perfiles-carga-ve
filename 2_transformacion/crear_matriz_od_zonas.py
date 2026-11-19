"""Matriz origen-destino de las zonas: suma de los viajes entre sus macrozonas (EOD 2025, indicador 15)."""
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import CRUDOS_EOD_API as API, MATRIZ_OD_XLSX, ZONAS_GEOJSON, ZONAS_XLSX  # noqa: E402

# Código de cada macrozona en la API -> (municipio, macrozona). Copiado del tablero.
MACROZONAS = json.loads((API / "macrozonas_codigos.json").read_text(encoding="utf-8"))


def main():
    od = pd.DataFrame(json.loads((API / "ind_15.json").read_text(encoding="utf-8"))["matriz"])
    od["origen"] = od["agrupa_mz_origen"].astype(int)
    od["destino"] = od["agrupa_mz_destino"].astype(int)

    geo = gpd.read_file(API / "macrozonas_actualizado.geo.json")
    geo["clave"] = geo["municipio"].str.strip() + " - " + geo["macrozona"].str.strip()
    # El mapa usa nombres cortos para dos corregimientos de Medellín.
    geo["clave"] = geo["clave"].replace({
        "Medellín - Corregimiento San Antonio": "Medellín - Corregimiento San Antonio de Prado",
        "Medellín - Corregimiento San Sebastián": "Medellín - Corregimiento San Sebastián de Palmitas"})
    zonas = gpd.read_file(ZONAS_GEOJSON)[["zona", "geometry"]]
    centros = geo.to_crs(3116).copy()
    centros["geometry"] = centros.representative_point()
    centros = gpd.sjoin(centros, zonas.to_crs(3116), how="left", predicate="within")
    zona_de = dict(zip(centros["clave"], centros["zona"]))

    filas = []
    for cod, v in MACROZONAS.items():
        clave = f"{v['municipio']} - {v['macrozona']}"
        filas.append({"codigo": int(cod), "municipio": v["municipio"], "macrozona": v["macrozona"],
                      "tipo": v["tipo"], "zona": zona_de.get(clave)})
    mz = pd.DataFrame(filas)
    sin_zona = mz[mz.zona.isna() & (mz.codigo != 67)]
    if len(sin_zona):
        print("Macrozonas sin zona (revisar nombres):", sin_zona[["municipio", "macrozona"]].values)

    # Si las zonas se armaron por estrato, cada macrozona ya trae su zona: se usa esa.
    hojas = pd.ExcelFile(ZONAS_XLSX).sheet_names
    if "macrozonas" in hojas:
        directa = pd.read_excel(ZONAS_XLSX, sheet_name="macrozonas")
        mz["zona"] = mz["codigo"].map(dict(zip(directa.codigo, directa.zona)))
    z = dict(zip(mz.codigo, mz.zona))
    od["zona_origen"] = od["origen"].map(z)
    od["zona_destino"] = od["destino"].map(z)
    od = od.dropna(subset=["zona_origen", "zona_destino"])
    matriz = od.pivot_table(index="zona_origen", columns="zona_destino", values="valor",
                            aggfunc="sum").round(0)
    pct = (matriz.div(matriz.sum(axis=1), axis=0) * 100).round(2)

    mz["viajes_que_salen"] = mz.codigo.map(
        pd.DataFrame(json.loads((API / "ind_15.json").read_text(encoding="utf-8"))["matriz"])
        .assign(o=lambda d: d.agrupa_mz_origen.astype(int)).groupby("o")["valor"].sum()).round(0)
    leeme = pd.DataFrame({"LEEME": [
        "MATRIZ ORIGEN-DESTINO DE LAS 7 ZONAS FICTICIAS (EOD 2025, Valle de Aburrá)",
        "Fuente: API del tablero oficial, indicador 15 (matriz entre 67 macrozonas, viajes en un",
        "día hábil, todos los modos): https://eod2025.metropol.gov.co/api/api/indicadores/15/agregado",
        "Cada macrozona se asigna a la zona donde cae su punto central (mapa oficial de",
        "macrozonas del tablero). Se descarta la macrozona 67, «Sin especificar».",
        "",
        "viajes: filas = zona de origen, columnas = zona de destino.",
        "porcentaje_por_fila: de los viajes que salen de una zona, qué % va a cada zona.",
        "macrozonas: a qué zona quedó asignada cada macrozona.",
    ]})
    with pd.ExcelWriter(MATRIZ_OD_XLSX, engine="openpyxl") as w:
        leeme.to_excel(w, sheet_name="LEEME", index=False)
        matriz.to_excel(w, sheet_name="viajes")
        pct.to_excel(w, sheet_name="porcentaje_por_fila")
        mz.to_excel(w, sheet_name="macrozonas", index=False)
    print(matriz.astype(int).to_string())
    print(mz.groupby("zona").size())
    return matriz


if __name__ == "__main__":
    main()
