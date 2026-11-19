"""Demanda por zona y hora si cada vehículo tiene su día de mayor carga al mismo tiempo.

1. Día máximo de cada vehículo: el día con más kWh cargados.
2. Curva horaria de ese día (zona donde cargó, tipo de cargador).
3. Suma de las curvas de todos los vehículos -> kW por zona y hora.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import GRAFICAS, RESULTADOS  # noqa: E402

PERFILES = {"lenta": "carga lenta (3,7 kW)", "semirrapida": "carga semirrápida (7,4 kW)",
            "rapida": "carga rápida (22 kW)"}


def graficar(tabla, titulo, archivo):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for z, color in zip(tabla.index, ["#E0B000", "#3A9AD9", "#E8505B", "#4CAF50", "#FF8C00"]):
        ax.plot(range(24), tabla.loc[z], marker="o", ms=4, lw=2.2, color=color,
                label=f"{z} (pico {tabla.loc[z].max():,.0f} kW)")
    ax.set(xticks=range(24), xlabel="Hora del día", ylabel="kW", title=titulo)
    ax.grid(alpha=.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(GRAFICAS / archivo, dpi=170, bbox_inches="tight")


def main():
    h = pd.read_csv(RESULTADOS / "por_carro" / "cargas_por_hora.csv",
                    usecols=["vehiculo", "zona_carga", "tipo", "dia", "hora", "kwh"])
    por_dia = h.groupby(["vehiculo", "dia"])["kwh"].sum()
    dia_max = por_dia.groupby("vehiculo").idxmax().map(lambda x: x[1]).rename("dia_max")
    sel = h.merge(dia_max, left_on="vehiculo", right_index=True).query("dia == dia_max")

    curva = (sel.groupby(["zona_carga", "tipo", "hora"])["kwh"].sum()
             .unstack("hora", fill_value=0).reindex(columns=range(24), fill_value=0))
    total = curva.groupby("zona_carga").sum()
    pico = pd.DataFrame({"pico_kW": total.max(axis=1), "hora_pico": total.idxmax(axis=1),
                         "energia_dia_kWh": total.sum(axis=1)}).round(1)
    pico.loc["TOTAL"] = [total.sum().max(), total.sum().idxmax(), total.values.sum().round(1)]

    graficar(total, "Demanda por zona y hora con el día de mayor carga de cada vehículo",
             "curva_dia_maximo_por_zona.png")
    picos_tipo = {}
    for t, nombre in PERFILES.items():
        tabla = curva.xs(t, level="tipo").reindex(total.index, fill_value=0)
        graficar(tabla, f"Perfil de {nombre}: demanda por zona y hora (día máximo de cada vehículo)",
                 f"curva_dia_maximo_{t}.png")
        picos_tipo[t] = tabla.max(axis=1)
        picos_tipo[f"hora_pico_{t}"] = tabla.idxmax(axis=1)
    picos_tipo = pd.DataFrame(picos_tipo).round(1)

    with pd.ExcelWriter(RESULTADOS / "curva_dia_maximo_por_zona.xlsx") as w:
        pico.to_excel(w, sheet_name="pico_por_zona")
        picos_tipo.to_excel(w, sheet_name="pico_por_perfil")
        total.round(1).to_excel(w, sheet_name="zona_x_hora")
        curva.round(1).to_excel(w, sheet_name="zona_tipo_x_hora")
        por_dia.groupby("vehiculo").max().rename("kwh_dia_max").to_frame().join(dia_max).to_excel(
            w, sheet_name="dia_max_por_vehiculo")
    print(pico.to_string())
    print(picos_tipo.to_string())


if __name__ == "__main__":
    main()
