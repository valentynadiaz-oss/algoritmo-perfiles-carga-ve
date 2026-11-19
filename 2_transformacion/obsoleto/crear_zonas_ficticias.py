"""Divide el Valle de Aburrá en 5 ZONAS FICTICIAS («comunas inventadas») para el modelo de
estudio, les asigna el tipo de vivienda del DANE y les reparte los VE de Pereira al azar.

ES UN CASO FICTICIO, de estudio: las zonas no existen. Se hace así porque la encuesta de
viajes (EOD 2025) es del Valle de Aburrá, y el DANE solo publica tipo de vivienda por
municipio.

CÓMO SE HACE
  1. Límites de los 10 municipios del Valle de Aburrá: OpenStreetMap (Nominatim, vía osmnx).
  2. Se lanzan 5.000 puntos al azar dentro del Valle y se agrupan en 5 grupos (k-means);
     cada zona es el área más cercana al centro de su grupo (polígonos de Voronoi). Así las
     zonas son al azar pero de tamaño parecido.
  3. Tipo de vivienda de cada zona: la mezcla de los municipios que cubre, según el DANE
     (CNPV 2018). Se supone que las viviendas de cada municipio están repartidas parejo en su
     área: viviendas de la zona = viviendas del municipio × fracción de su área en la zona.
  4. VE: las 19 comunas de Pereira (3.001 VE del Objetivo 2) se reparten al azar entre las
     5 zonas (cada zona recibe al menos una comuna) y se suman sus VE.

Salidas (en esta carpeta): zonas_ficticias.xlsx, zonas_ficticias.geojson y
mapa_zonas_ficticias.png. Uso: python crear_zonas_ficticias.py
"""
import random
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from shapely.geometry import MultiPoint, Point  # noqa: E402
from shapely.ops import voronoi_diagram  # noqa: E402

AQUI = Path(__file__).resolve().parent
FUENTES = AQUI / "fuentes"
SEMILLA = 7
N_ZONAS = 5
CRS_METROS = 3116                       # MAGNA-SIRGAS / Colombia Bogotá, en metros
MUNICIPIOS = {"Medellín": "05001", "Barbosa": "05079", "Bello": "05088", "Caldas": "05129",
              "Copacabana": "05212", "Envigado": "05266", "Girardota": "05308",
              "Itagüí": "05360", "La Estrella": "05380", "Sabaneta": "05631"}
COLORES = ["#FFF3A3", "#A9D8F5", "#E8505B", "#B5E5B0", "#FFC48C", "#C9B6F2", "#F7B6D2"]
NOMBRES_COLOR = ["amarillo claro", "azul claro", "rojo", "verde claro", "naranja claro",
                 "lila", "rosado"]


def limites_municipios():
    ruta = FUENTES / "limites_valle_aburra_osm.gpkg"
    if not ruta.exists():
        import osmnx as ox
        g = ox.geocode_to_gdf([f"{m}, Antioquia, Colombia" for m in MUNICIPIOS])
        g["municipio"] = list(MUNICIPIOS)
        g[["municipio", "display_name", "geometry"]].to_file(ruta)
    g = gpd.read_file(ruta)
    g["divipola"] = g["municipio"].map(MUNICIPIOS)
    return g.to_crs(CRS_METROS)


def crear_zonas(mun):
    valle = mun.union_all()
    rng = np.random.default_rng(SEMILLA)
    xmin, ymin, xmax, ymax = valle.bounds
    puntos = []
    while len(puntos) < 5000:                                  # puntos al azar en el Valle
        x, y = rng.uniform(xmin, xmax), rng.uniform(ymin, ymax)
        if valle.contains(Point(x, y)):
            puntos.append((x, y))
    puntos = np.array(puntos)
    centros = puntos[rng.choice(len(puntos), N_ZONAS, replace=False)]
    for _ in range(50):                                        # k-means
        grupo = ((puntos[:, None] - centros[None]) ** 2).sum(-1).argmin(1)
        centros = np.array([puntos[grupo == k].mean(0) for k in range(N_ZONAS)])
    celdas = voronoi_diagram(MultiPoint([Point(c) for c in centros]), envelope=valle.envelope)
    zonas = []
    for celda in celdas.geoms:
        k = next(i for i, c in enumerate(centros) if celda.contains(Point(c)))
        zonas.append((k, celda.intersection(valle)))
    # Numerar de norte a sur: zona 1 la más al norte.
    zonas.sort(key=lambda z: -z[1].centroid.y)
    return gpd.GeoDataFrame({"zona": [f"Zona {i + 1}" for i in range(N_ZONAS)]},
                            geometry=[z[1] for z in zonas], crs=CRS_METROS)


def vivienda_por_zona(zonas, mun):
    dane = pd.read_excel(AQUI / "tipo_vivienda_DANE_CNPV2018.xlsx", sheet_name="tipo_vivienda",
                         dtype={"divipola": str})
    mun = mun.merge(dane.drop(columns=["municipio", "departamento", "grupo"]), on="divipola")
    mun["area_mun"] = mun.area
    cruce = gpd.overlay(zonas, mun, how="intersection")
    cruce["fraccion_area_mun"] = cruce.area / cruce["area_mun"]
    cruce["viviendas"] = cruce["viviendas_ocupadas"] * cruce["fraccion_area_mun"]
    tipos = ["casa_%", "apartamento_%", "tipo_cuarto_%", "tradicional_indigena_%",
             "tradicional_etnica_%", "otro_%"]
    filas = []
    for z, g in cruce.groupby("zona"):
        w = g["viviendas"]
        fila = {"zona": z, "viviendas_estimadas": round(w.sum()),
                "municipios_que_cubre": ", ".join(
                    f"{m} ({100 * v / w.sum():.0f} %)" for m, v in
                    g.sort_values("viviendas", ascending=False)[["municipio", "viviendas"]].values
                    if v / w.sum() >= 0.005)}
        fila.update({t: round((g[t] * w).sum() / w.sum(), 2) for t in tipos})
        filas.append(fila)
    detalle = cruce[["zona", "municipio", "divipola", "fraccion_area_mun", "viviendas"]].copy()
    detalle["fraccion_area_mun"] = detalle["fraccion_area_mun"].round(4)
    detalle["viviendas"] = detalle["viviendas"].round()
    return pd.DataFrame(filas), detalle.sort_values(["zona", "viviendas"], ascending=[True, False])


def repartir_ve(zonas_nombres):
    ve = pd.read_csv(FUENTES / "obj2_a6_indice_demanda_comunas.csv")
    ve = ve[ve["poblacion_2019"] > 0][["comuna", "VE_2030_base"]]
    azar = random.Random(SEMILLA)
    comunas = list(ve["comuna"])
    azar.shuffle(comunas)
    destino = {c: zonas_nombres[i] for i, c in enumerate(comunas[:N_ZONAS])}   # 1 por zona
    destino.update({c: azar.choice(zonas_nombres) for c in comunas[N_ZONAS:]})
    ve["zona"] = ve["comuna"].map(destino)
    return ve.rename(columns={"comuna": "comuna_pereira", "VE_2030_base": "vehiculos"})


def mapa(zonas, mun, tabla, ruta):
    fig, ax = plt.subplots(figsize=(8, 10))
    zonas.plot(ax=ax, color=COLORES[:len(zonas)], edgecolor="#21213D", linewidth=1.4)
    mun.boundary.plot(ax=ax, color="#555555", linewidth=0.6, linestyle="--")
    for _, r in mun.iterrows():
        p = r.geometry.representative_point()
        ax.text(p.x, p.y, r["municipio"], fontsize=6.5, color="#444444", ha="center",
                style="italic", alpha=.6)
    for _, r in zonas.iterrows():
        p = r.geometry.representative_point()
        t = tabla.set_index("zona").loc[r["zona"]]
        ax.text(p.x, p.y + 1200, r["zona"].split()[1], fontsize=22, fontweight="bold",
                ha="center", va="center", color="#21213D")
        ax.text(p.x, p.y - 900, f"{t['casa_%']:.0f} % casas\n{t['vehiculos']:.0f} VE",
                fontsize=7.5, ha="center", va="center", color="#21213D",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=.75))
    ax.set_title("Valle de Aburrá dividido en 5 zonas ficticias (caso de estudio)",
                 fontsize=12, color="#21213D")
    ax.axis("off")
    ax.text(0.01, 0.01, "Zonas inventadas al azar (k-means + Voronoi, semilla 7). Líneas "
            "punteadas: municipios (OpenStreetMap).\nTipo de vivienda: DANE, CNPV 2018. VE: "
            "comunas de Pereira asignadas al azar.", transform=ax.transAxes, fontsize=7,
            color="#444444")
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    mun = limites_municipios()
    zonas = crear_zonas(mun)
    viv, detalle = vivienda_por_zona(zonas, mun)
    ve = repartir_ve(list(zonas["zona"]))
    suma = ve.groupby("zona").agg(vehiculos=("vehiculos", "sum"),
                                  comunas_pereira_asignadas=("comuna_pereira", ", ".join))
    tabla = (zonas.assign(area_km2=(zonas.area / 1e6).round(1),
                          color=[NOMBRES_COLOR[i] for i in range(len(zonas))])
             .drop(columns="geometry").merge(viv, on="zona").merge(suma, on="zona"))
    tabla["vehiculos"] = tabla["vehiculos"].round(1)
    tabla = tabla[["zona", "color", "area_km2", "municipios_que_cubre", "viviendas_estimadas",
                   "casa_%", "apartamento_%", "tipo_cuarto_%", "tradicional_indigena_%",
                   "tradicional_etnica_%", "otro_%", "vehiculos", "comunas_pereira_asignadas"]]
    mapa(zonas, mun.to_crs(CRS_METROS), tabla, AQUI / "mapa_zonas_ficticias.png")
    zonas.merge(tabla, on="zona").to_crs(4326).to_file(AQUI / "zonas_ficticias.geojson",
                                                         driver="GeoJSON")
    leeme = pd.DataFrame({"LEEME": [
        "ZONAS FICTICIAS DEL VALLE DE ABURRÁ (caso de estudio, no son zonas reales)",
        "",
        "zonas: una fila por zona, con su tipo de vivienda (DANE) y sus VE.",
        "composicion: qué parte de cada municipio cae en cada zona.",
        "ve_asignados: a qué zona se asignó al azar cada comuna de Pereira.",
        "",
        "Zonas: 5.000 puntos al azar dentro del Valle, agrupados en 5 con k-means; cada zona",
        "es el área más cercana a su centro (Voronoi). Semilla 7. Numeradas de norte a sur.",
        "Límites municipales: OpenStreetMap. Tipo de vivienda: DANE, CNPV 2018, por municipio.",
        "Supuesto: las viviendas de cada municipio se reparten parejo en su área.",
        "casa_% de cada zona se usa en el algoritmo como fracción de VE con garaje",
        "(Mejia et al., 2025, sección 3.1: % de casas unifamiliares de la región).",
    ]})
    with pd.ExcelWriter(AQUI / "zonas_ficticias.xlsx", engine="openpyxl") as w:
        leeme.to_excel(w, sheet_name="LEEME", index=False)
        tabla.to_excel(w, sheet_name="zonas", index=False)
        detalle.to_excel(w, sheet_name="composicion", index=False)
        ve.sort_values("zona").to_excel(w, sheet_name="ve_asignados", index=False)
    print(tabla.drop(columns=["municipios_que_cubre", "comunas_pereira_asignadas",
                              "tipo_cuarto_%", "tradicional_indigena_%", "tradicional_etnica_%",
                              "otro_%"]).to_string(index=False))
    for _, r in tabla.iterrows():
        print(r["zona"], "|", r["municipios_que_cubre"], "|", r["comunas_pereira_asignadas"])
    return tabla


if __name__ == "__main__":
    main()
