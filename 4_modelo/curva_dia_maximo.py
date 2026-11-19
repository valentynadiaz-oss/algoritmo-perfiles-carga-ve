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

    with pd.ExcelWriter(RESULTADOS / "curva_dia_maximo_por_zona.xlsx") as w:
        pico.to_excel(w, sheet_name="pico_por_zona")
        total.round(1).to_excel(w, sheet_name="zona_x_hora")
        curva.round(1).to_excel(w, sheet_name="zona_tipo_x_hora")
        por_dia.groupby("vehiculo").max().rename("kwh_dia_max").to_frame().join(dia_max).to_excel(
            w, sheet_name="dia_max_por_vehiculo")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for z, color in zip(total.index, ["#E0B000", "#3A9AD9", "#E8505B", "#4CAF50", "#FF8C00"]):
        ax.plot(range(24), total.loc[z], marker="o", ms=4, lw=2.2, color=color,
                label=f"{z} (pico {total.loc[z].max():,.0f} kW)")
    ax.set(xticks=range(24), xlabel="Hora del día", ylabel="kW",
           title="Demanda por zona y hora con el día de mayor carga de cada vehículo")
    ax.grid(alpha=.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(GRAFICAS / "curva_dia_maximo_por_zona.png", dpi=170, bbox_inches="tight")
    print(pico.to_string())
    print(total.round(0).astype(int).to_string())


if __name__ == "__main__":
    main()
