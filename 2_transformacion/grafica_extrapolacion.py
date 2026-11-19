"""Esquema: cada comuna de Pereira pasa a la zona del Valle con la misma moda de estrato."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import GRAFICAS, ZONAS_XLSX  # noqa: E402

COLORES = ["#FFF3A3", "#A9D8F5", "#E8505B", "#B5E5B0", "#FFC48C"]
NAVY = "#21213D"


def main():
    GRAFICAS.mkdir(exist_ok=True)
    zonas = pd.read_excel(ZONAS_XLSX, sheet_name="zonas")
    ve = pd.read_excel(ZONAS_XLSX, sheet_name="ve_asignados")
    color = dict(zip(zonas["zona"], COLORES))
    ve = ve.sort_values(["zona", "vehiculos"], ascending=[True, False]).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(13, 9))
    ax.set_xlim(0, 13); ax.set_ylim(-0.6, len(ve) + 0.4); ax.axis("off")
    ax.text(1.8, len(ve) + 0.1, "Comunas de Pereira\n(moda de estrato · VE 2030)", ha="center",
            fontsize=11, fontweight="bold", color=NAVY)
    ax.text(10.4, len(ve) + 0.1, "Zonas del Valle de Aburrá\n(moda de estrato de sus macrozonas, EOD 2025)",
            ha="center", fontsize=11, fontweight="bold", color=NAVY)

    y_comuna = {}
    for i, r in ve.iterrows():
        y = len(ve) - 1 - i
        y_comuna[r["comuna_pereira"]] = y
        ax.add_patch(plt.Rectangle((0.2, y - 0.38), 3.2, 0.76, color=color[r["zona"]], ec=NAVY, lw=.6))
        marca = "*" if r["moda_estrato_pereira"] != r["estrato_usado_para_asignar"] else ""
        ax.text(0.35, y, f"{r['comuna_pereira']}{marca}", va="center", fontsize=9, color=NAVY)
        ax.text(3.3, y, f"moda {r['moda_estrato_pereira']} · {r['vehiculos']:.0f} VE", va="center",
                ha="right", fontsize=8.5, color=NAVY)

    for _, z in zonas.iterrows():
        filas = ve[ve.zona == z["zona"]]
        ys = [y_comuna[c] for c in filas["comuna_pereira"]]
        yc = sum(ys) / len(ys)
        alto = max(0.9, max(ys) - min(ys) + 0.76)
        ax.add_patch(plt.Rectangle((7.8, yc - alto / 2), 5.1, alto, color=color[z["zona"]], ec=NAVY, lw=1.2))
        ax.text(10.35, yc + 0.18, f"{z['zona']} · moda estrato {z['moda_estrato']}", ha="center",
                fontsize=10.5, fontweight="bold", color=NAVY)
        ax.text(10.35, yc - 0.25, f"{z['macrozonas']} macrozonas · {z['vehiculos']:.0f} VE · "
                f"{z['apartamento_%']:.0f} % apartamentos", ha="center", fontsize=8.5, color=NAVY)
        for y in ys:
            ax.annotate("", xy=(7.8, yc), xytext=(3.4, y),
                        arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=.7, alpha=.6))

    ax.text(0.2, -0.55, "* Boston tiene moda 4; en el Valle ninguna macrozona tiene moda 4, así que va a la zona "
            "de su segundo estrato más frecuente (3).\nCada carro vive en su zona; el destino de sus viajes se "
            "sortea con la fila de esa zona en la matriz origen-destino de la EOD 2025.",
            fontsize=8.5, color="#555555", va="top")
    fig.suptitle("Cómo se llevan los vehículos de Pereira a las zonas del Valle de Aburrá: misma moda de estrato", y=0.95,
                 color=NAVY, fontsize=13)
    fig.savefig(GRAFICAS / "esquema_extrapolacion_pereira_valle.png", dpi=170, bbox_inches="tight")
    print("ok")


if __name__ == "__main__":
    main()
