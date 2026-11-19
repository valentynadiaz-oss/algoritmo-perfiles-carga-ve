"""Mapa de las zonas con los VE asignados y sus comunas de Pereira."""
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import GRAFICAS, ZONAS_GEOJSON, ZONAS_XLSX  # noqa: E402
COLORES = ["#FFF3A3", "#A9D8F5", "#E8505B", "#B5E5B0", "#FFC48C", "#C9B6F2", "#F7B6D2"]

zonas = gpd.read_file(ZONAS_GEOJSON).to_crs(3116)
asig = pd.read_excel(ZONAS_XLSX, sheet_name="ve_asignados")

fig, (ax, axt) = plt.subplots(1, 2, figsize=(14, 9), gridspec_kw={"width_ratios": [1, 1.05]})
for i, (_, r) in enumerate(zonas.iterrows()):           # una zona puede tener varios pedazos
    gpd.GeoSeries([r.geometry], crs=zonas.crs).plot(ax=ax, color=COLORES[i], edgecolor="#21213D",
                                                    linewidth=0.6)
for _, r in zonas.iterrows():
    p = r.geometry.representative_point()
    ax.text(p.x, p.y + 1300, r["zona"].split()[1], fontsize=22, fontweight="bold",
            ha="center", va="center", color="#21213D")
    ax.text(p.x, p.y - 900, f"{r['vehiculos']:.0f} VE", fontsize=10, ha="center",
            fontweight="bold", color="#21213D",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=.8))
ax.axis("off")
ax.set_title("Carros eléctricos asignados a cada zona ficticia", fontsize=12, color="#21213D")

axt.axis("off")
y = 0.97
for i, (z, g) in enumerate(asig.groupby("zona")):
    axt.add_patch(plt.Rectangle((0, y - 0.035), 0.05, 0.04, color=COLORES[i],
                                transform=axt.transAxes, ec="#21213D"))
    axt.text(0.07, y - 0.015, f"{z}: {g['vehiculos'].sum():.0f} VE", fontsize=11,
             fontweight="bold", color="#21213D", transform=axt.transAxes, va="center")
    y -= 0.042
    for r in g.sort_values("vehiculos", ascending=False).itertuples():
        axt.text(0.09, y, f"{r.comuna_pereira}: {r.vehiculos:.0f} VE", fontsize=9,
                 color="#333333", transform=axt.transAxes, va="center")
        y -= 0.026
    y -= 0.01
axt.text(0, -0.04, "Total: 3.001 VE. Las 19 comunas de Pereira (Objetivo 2, Tabla 14) se "
         "asignaron al azar a las 5 zonas\n(semilla 7), con al menos una comuna por zona.",
         fontsize=8, color="#555555", transform=axt.transAxes)
fig.tight_layout()
fig.savefig(GRAFICAS / "mapa_carros_por_zona.png", dpi=180, bbox_inches="tight")
print("ok")
