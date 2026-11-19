"""5 zonas del Valle de Aburrá según la moda del estrato de sus macrozonas (EOD 2025).
Cada comuna de Pereira va a la zona con su misma moda; si no existe, a la de su segundo estrato."""
import json
import urllib.request
import urllib.parse
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import (CRUDOS_EOD_API as API, CRUDOS_OBJ2, GRAFICAS, TIPO_VIVIENDA_XLSX,  # noqa: E402
                   ZONAS_GEOJSON, ZONAS_XLSX)
N_ZONAS = 5
COLORES = ["#FFF3A3", "#A9D8F5", "#E8505B", "#B5E5B0", "#FFC48C"]
NOMBRES_COLOR = ["amarillo claro", "azul claro", "rojo", "verde claro", "naranja claro"]
DIVIPOLA = {"Medellín": "05001", "Barbosa": "05079", "Bello": "05088", "Caldas": "05129",
            "Copacabana": "05212", "Envigado": "05266", "Girardota": "05308",
            "Itagüí": "05360", "La Estrella": "05380", "Sabaneta": "05631"}


def estrato_macrozonas():
    est = json.loads((API / "ind_46_estrato_por_macrozona.json").read_text(encoding="utf-8"))
    filas = []
    for cod, v in est.items():
        g = {int(x["criterio"]): x["valor"] for x in v["grupos"]}
        if sum(g.values()) == 0:            # sin dato: se usa el de todo el municipio
            q = urllib.parse.urlencode({"municipio": v["municipio"]})
            req = urllib.request.Request(
                f"https://eod2025.metropol.gov.co/api/api/indicadores/46/agregado?{q}",
                headers={"User-Agent": "Mozilla/5.0"})
            d = json.loads(urllib.request.urlopen(req, timeout=60).read())
            g = {int(x["criterio"]): x["valor"] for x in d["grupos"]}
            v["nota"] = "sin dato propio: se usa el estrato de todo el municipio"
        filas.append({"codigo": int(cod), "municipio": v["municipio"], "macrozona": v["macrozona"],
                      **{f"estrato_{k}_%": round(100 * g.get(k, 0), 2) for k in range(1, 7)},
                      "nota": v.get("nota", "")})
    df = pd.DataFrame(filas)
    pct = df[[f"estrato_{k}_%" for k in range(1, 7)]]
    df["estrato_promedio"] = (pct.values * np.arange(1, 7)).sum(1) / pct.sum(1)
    df["estrato_456_%"] = df[["estrato_4_%", "estrato_5_%", "estrato_6_%"]].sum(1)
    return df


def main():
    mz = estrato_macrozonas()
    od = pd.DataFrame(json.loads((API / "ind_15.json").read_text(encoding="utf-8"))["matriz"])
    salen = od.assign(o=od.agrupa_mz_origen.astype(int)).groupby("o")["valor"].sum()
    mz["viajes_que_salen"] = mz["codigo"].map(salen).fillna(0).round(0)

    # 2. Moda de cada macrozona; cada moda distinta es una zona (numeradas de menor a mayor).
    cols = [f"estrato_{k}_%" for k in range(1, 7)]
    mz["moda_estrato"] = mz[cols].values.argmax(1) + 1
    modas = sorted(mz["moda_estrato"].unique())
    zona_de_moda = {m: f"Zona {i + 1}" for i, m in enumerate(modas)}
    mz["zona"] = mz["moda_estrato"].map(zona_de_moda)
    mz = mz.sort_values(["zona", "estrato_promedio"]).reset_index(drop=True)

    # 3. Tipo de vivienda (DANE) por zona.
    dane = pd.read_excel(TIPO_VIVIENDA_XLSX, sheet_name="tipo_vivienda",
                         dtype={"divipola": str}).set_index("divipola")
    mz["divipola"] = mz["municipio"].map(DIVIPOLA)
    for c in ["casa_%", "apartamento_%"]:
        mz[c] = mz["divipola"].map(dane[c])

    filas = []
    for z, g in mz.groupby("zona"):
        w = g["viajes_que_salen"]
        fila = {"zona": z, "moda_estrato": int(g["moda_estrato"].iloc[0]),
                "macrozonas": len(g), "viajes_que_salen": int(w.sum()),
                "estrato_promedio": round((g.estrato_promedio * w).sum() / w.sum(), 2)}
        fila.update({f"estrato_{k}_%": round((g[f"estrato_{k}_%"] * w).sum() / w.sum(), 1)
                     for k in range(1, 7)})
        fila["estrato_456_%"] = round((g["estrato_456_%"] * w).sum() / w.sum(), 1)
        fila["casa_%"] = round((g["casa_%"] * w).sum() / w.sum(), 2)
        fila["apartamento_%"] = round((g["apartamento_%"] * w).sum() / w.sum(), 2)
        fila["macrozonas_que_tiene"] = ", ".join(f"{m} ({mu})" for m, mu in
                                                 g[["macrozona", "municipio"]].values)
        filas.append(fila)
    zonas = pd.DataFrame(filas)
    zonas.insert(1, "color", NOMBRES_COLOR[:len(zonas)])

    # 4. Comunas de Pereira a la zona con su misma moda de estrato.
    p = pd.read_csv(CRUDOS_OBJ2 / "obj2_a5b_estrato_comunas.csv")
    v2030 = pd.read_csv(CRUDOS_OBJ2 / "obj2_a6_indice_demanda_comunas.csv")
    p = p.merge(v2030[["comuna", "VE_2030_base", "poblacion_2019"]], on="comuna")
    p = p[p["poblacion_2019"] > 0]
    pred = [f"estrato{k}" for k in range(1, 7)]
    zona_por_moda = dict(zip(zonas["moda_estrato"], zonas["zona"]))
    asignacion = []
    for _, r in p.iterrows():
        orden = (r[pred].astype(float).values.argsort()[::-1] + 1)   # estratos del más al menos frecuente
        moda = int(orden[0])
        usada = next(int(e) for e in orden if int(e) in zona_por_moda)
        asignacion.append({"comuna_pereira": r["comuna"], "moda_estrato_pereira": moda,
                           "estrato_usado_para_asignar": usada, "zona": zona_por_moda[usada],
                           "vehiculos": r["VE_2030_base"],
                           "nota": "" if usada == moda else
                           f"no hay zona del Valle con moda {moda}; se usa el siguiente estrato más frecuente ({usada})"})
    ve = pd.DataFrame(asignacion)
    suma = ve.groupby("zona").agg(vehiculos=("vehiculos", "sum"),
                                  comunas_pereira_asignadas=("comuna_pereira", ", ".join))
    zonas = zonas.merge(suma, on="zona", how="left")
    zonas["vehiculos"] = zonas["vehiculos"].fillna(0).round(1)
    zonas["comunas_pereira_asignadas"] = zonas["comunas_pereira_asignadas"].fillna("(ninguna)")

    # Mapa: cada macrozona pintada con el color de su zona.
    geo = gpd.read_file(API / "macrozonas_actualizado.geo.json")
    geo["geometry"] = geo.geometry.make_valid()          # algunos polígonos traen errores
    geo["clave"] = geo["municipio"].str.strip() + " - " + geo["macrozona"].str.strip()
    # El mapa usa nombres cortos para dos corregimientos de Medellín.
    geo["clave"] = geo["clave"].replace({
        "Medellín - Corregimiento San Antonio": "Medellín - Corregimiento San Antonio de Prado",
        "Medellín - Corregimiento San Sebastián": "Medellín - Corregimiento San Sebastián de Palmitas"})
    mz["clave"] = mz["municipio"] + " - " + mz["macrozona"]
    geo = geo.merge(mz[["clave", "zona"]], on="clave", how="left")
    geo_z = geo.dropna(subset=["zona"]).dissolve(by="zona").reset_index()[["zona", "geometry"]]
    geo_z = geo_z.merge(zonas, on="zona")
    geo_z.to_file(ZONAS_GEOJSON, driver="GeoJSON")

    color = dict(zip(zonas["zona"], COLORES))
    g3 = geo.to_crs(3116)
    fig, ax = plt.subplots(figsize=(9, 10))
    g3.plot(ax=ax, color=[color.get(z, "#DDDDDD") for z in g3["zona"]], edgecolor="white",
            linewidth=0.4)
    g3.dissolve(by="municipio").boundary.plot(ax=ax, color="#21213D", linewidth=0.8)
    ax.axis("off")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=color[r.zona], label=f"{r.zona}: moda estrato {r.moda_estrato} "
                             f"(prom. {r.estrato_promedio:.1f}), {r.vehiculos:.0f} VE")
                       for _, r in zonas.iterrows()], loc="upper center", bbox_to_anchor=(0.5, -0.01),
              fontsize=8.5, frameon=False)
    ax.set_title("Valle de Aburrá: 5 zonas ficticias según el estrato (EOD 2025)", color="#21213D")
    ax.text(0.0, -0.17, "Cada macrozona de la encuesta se pinta con el color de su zona. Líneas oscuras: "
            "municipios.\nZona 1 = estrato más bajo; zona 5 = estrato más alto.",
            transform=ax.transAxes, fontsize=7.5, color="#555555")
    fig.savefig(GRAFICAS / "mapa_zonas_ficticias.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    leeme = pd.DataFrame({"LEEME": [
        "ZONAS FICTICIAS DEL VALLE DE ABURRÁ SEGÚN EL ESTRATO (caso de estudio)",
        "Estrato de cada macrozona: EOD 2025, indicador 46 de la API del tablero.",
        "Moda = estrato con más población (Valle) o con más predios (Pereira, 2011).",
        "Cada zona = las macrozonas con la misma moda: zona 1 moda 1, zona 2 moda 2,",
        "zona 3 moda 3, zona 4 moda 5, zona 5 moda 6 (ninguna macrozona tiene moda 4).",
        "Cada comuna de Pereira va a la zona con su misma moda; si no hay (moda 4), al",
        "siguiente estrato más frecuente de esa comuna que sí tenga zona.",
        "apartamento_% (DANE, CNPV 2018) = fracción de VE con garaje en el algoritmo.",
        "",
        "Hojas: zonas, macrozonas, ve_asignados.",
    ]})
    with pd.ExcelWriter(ZONAS_XLSX, engine="openpyxl") as wr:
        leeme.to_excel(wr, sheet_name="LEEME", index=False)
        zonas.to_excel(wr, sheet_name="zonas", index=False)
        mz.drop(columns=["clave"]).to_excel(wr, sheet_name="macrozonas", index=False)
        ve.sort_values(["zona", "comuna_pereira"]).to_excel(wr, sheet_name="ve_asignados", index=False)
    print(zonas[["zona", "moda_estrato", "macrozonas", "estrato_promedio", "apartamento_%",
                 "vehiculos"]].to_string(index=False))
    for _, r in zonas.iterrows():
        print(r["zona"], "|", r["comunas_pereira_asignadas"])


if __name__ == "__main__":
    main()
