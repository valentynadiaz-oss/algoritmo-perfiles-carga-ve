"""Gasto diario de energía de cada vehículo (kWh/día), sin distinguir zona ni cargador.

Lee 5_resultados/por_carro/diario_*.csv (un registro por vehículo y día) y deja:
  - boxplot de todos los vehículo-día, y por zona
  - histograma con el ajuste de normal, lognormal y gamma (prueba KS)
  - por vehículo: promedio, máximo y máximo sin atípicos (bigote del boxplot)
  - por zona: suma de los máximos de sus vehículos
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import GASTO_DIARIO, GRAFICAS, RESULTADOS  # noqa: E402

FIG = GRAFICAS / "gasto_diario"
CAJA = dict(patch_artist=True, boxprops=dict(facecolor="#C687FC"), medianprops=dict(color="#21213D", lw=2),
            flierprops=dict(marker=".", markersize=2, alpha=.3))


def sin_atipicos(s):
    q1, q3 = s.quantile([.25, .75])
    return s[s <= q3 + 1.5 * (q3 - q1)].max()


def main():
    GASTO_DIARIO.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    g = pd.concat(pd.read_csv(f, usecols=["vehiculo", "zona_vive", "dia", "km", "kwh_gastados"])
                  for f in sorted((RESULTADOS / "por_carro").glob("diario_*.csv")))
    x = g["kwh_gastados"]

    fig, ax = plt.subplots(figsize=(5, 6))
    ax.boxplot(x, **CAJA)
    ax.set(xticks=[1], xticklabels=[f"{g.vehiculo.nunique():,} vehículos × 365 días\n({len(g):,} datos)"],
           ylabel="kWh gastados en el día", title="Gasto diario por vehículo")
    fig.tight_layout(); fig.savefig(FIG / "boxplot_todos.png", dpi=180)

    zonas = sorted(g.zona_vive.unique())
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot([g.loc[g.zona_vive == z, "kwh_gastados"] for z in zonas], tick_labels=zonas, **CAJA)
    ax.set(ylabel="kWh gastados en el día", title="Gasto diario por vehículo, por zona")
    fig.tight_layout(); fig.savefig(FIG / "boxplot_por_zona.png", dpi=180)

    pos = x[x > 0].sample(min(20000, (x > 0).sum()), random_state=1)
    ajustes = []
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(x, bins=120, density=True, color="#C687FC", label="vehículo-día")
    xs = pd.Series(range(1, 400)) / 400 * x.quantile(.995)
    for nombre, dist in [("gamma", stats.gamma), ("lognormal", stats.lognorm), ("normal", stats.norm)]:
        par = dist.fit(pos) if nombre == "normal" else dist.fit(pos, floc=0)
        ks = stats.kstest(pos, dist.cdf, args=par)
        ajustes.append({"distribucion": nombre, "parametros": [round(p, 4) for p in par],
                        "KS": round(ks.statistic, 4), "p_valor": ks.pvalue})
        ax.plot(xs, dist.pdf(xs, *par), lw=2, label=f"{nombre} (KS {ks.statistic:.3f})")
    ax.set(xlim=(0, x.quantile(.995)), xlabel="kWh gastados en el día", ylabel="densidad",
           title="Distribución del gasto diario")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "distribucion.png", dpi=180)

    por_carro = g.groupby(["vehiculo", "zona_vive"])["kwh_gastados"].agg(
        promedio="mean", mediana="median", maximo="max", maximo_sin_atipicos=sin_atipicos).round(3).reset_index()
    por_carro["km_promedio_dia"] = g.groupby("vehiculo")["km"].mean().round(1).values
    por_zona = por_carro.groupby("zona_vive").agg(vehiculos=("vehiculo", "count"), suma_promedios=("promedio", "sum"),
                                                  suma_maximos=("maximo", "sum"),
                                                  suma_maximos_sin_atipicos=("maximo_sin_atipicos", "sum")).round(1)
    por_zona.loc["TOTAL"] = por_zona.sum()

    with pd.ExcelWriter(GASTO_DIARIO / "gasto_diario_por_vehiculo.xlsx") as w:
        x.describe(percentiles=[.25, .5, .75, .95, .99]).round(3).to_excel(w, sheet_name="resumen")
        pd.DataFrame(ajustes).to_excel(w, sheet_name="ajuste_distribucion", index=False)
        por_zona.to_excel(w, sheet_name="por_zona")
        por_carro.to_excel(w, sheet_name="por_vehiculo", index=False)
    print(x.describe().round(3).to_string(), "\n", pd.DataFrame(ajustes).to_string(index=False), "\n", por_zona)


if __name__ == "__main__":
    main()
