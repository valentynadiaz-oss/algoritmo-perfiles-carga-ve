"""Simulación de viajes y carga de VE por zona (Mejia et al., 2025; Mejía Alzate, 2021).

Cada vehículo recorre sus viajes del año. Si al llegar la batería queda bajo el umbral, carga:
  1. batería agotada o próximo viaje en menos de 1 h -> rápida
  2. llegó a casa y tiene garaje                      -> lenta (casa)
  3. otro caso                                        -> semirrápida (pública)

Entrada: 3_carga/insumos_algoritmo.xlsx     Salida: 5_resultados/
"""
import csv
import math
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import INSUMOS, RESULTADOS  # noqa: E402

TIPOS = ["rapida", "semirrapida", "lenta"]
HORAS = 8760


class Registro:
    """Guarda todo lo de cada vehículo mientras se simula (por viaje, por carga, por hora y por día)."""

    def __init__(self, carpeta, zonas):
        carpeta.mkdir(parents=True, exist_ok=True)
        self.archivos = []
        self.viajes = self._abrir(carpeta / "viajes_por_carro.csv", [
            "vehiculo", "zona_vive", "dia", "viaje_del_dia", "hora_salida", "hora_llegada", "km",
            "kwh_gastados", "bateria_antes_%", "bateria_al_llegar_%", "zona_destino",
            "termina_en_casa", "tipo_carga", "kwh_cargados", "bateria_despues_de_cargar_%"])
        self.cargas = self._abrir(carpeta / "cargas.csv", [
            "vehiculo", "zona_vive", "zona_carga", "tipo", "hora_del_anio", "dia", "duracion_h",
            "kwh", "potencia_kw", "bateria_kwh", "bateria_al_llegar_%"])
        self.horas = self._abrir(carpeta / "cargas_por_hora.csv", [
            "vehiculo", "zona_vive", "zona_carga", "tipo", "hora_del_anio", "dia", "hora", "kwh"])
        cols = ["vehiculo", "zona_vive", "bateria_kwh", "garaje", "dia", "viajes", "km",
                "kwh_gastados", *[f"kwh_cargados_{t}" for t in TIPOS], "kwh_cargados_total",
                "numero_de_cargas", "bateria_inicio_dia_%", "bateria_fin_dia_%", "zonas_visitadas"]
        self.diario = {z: self._abrir(carpeta / f"diario_{z.replace(' ', '_')}.csv", cols) for z in zonas}

    def _abrir(self, ruta, encabezado):
        f = open(ruta, "w", newline="", encoding="utf-8-sig")
        self.archivos.append(f)
        w = csv.writer(f)
        w.writerow(encabezado)
        return w

    def cerrar(self):
        for f in self.archivos:
            f.close()


def leer_insumos():
    tabla = pd.read_excel(INSUMOS, sheet_name="parametros").set_index("parametro")["valor"]
    P = {n: float(str(v).replace(",", ".")) for n, v in tabla.items() if n != "baterias_kwh"}
    P["baterias_kwh"] = [float(x.replace(",", ".")) for x in str(tabla["baterias_kwh"]).split(";")]
    for hoja in ("ve_por_zona", "hora_salida", "duracion_viaje"):
        P[hoja] = pd.read_excel(INSUMOS, sheet_name=hoja)
    P["matriz_od"] = pd.read_excel(INSUMOS, sheet_name="matriz_od", index_col=0)
    return P


def crear_flota(P, azar):
    flota = []
    for r in P["ve_por_zona"].itertuples():
        n = max(1, round(r.vehiculos * P["escala"]))
        for k in range(n):
            flota.append({"vehiculo": f"{r.zona}_{k + 1}", "zona": r.zona, "peso": r.vehiculos / n,
                          "bateria_kwh": azar.choice(P["baterias_kwh"]),
                          "carga_inicial": azar.uniform(P["soc_inicial_min"], P["soc_inicial_max"]),
                          "garaje": azar.random() < r.fraccion_garaje})   # % apartamentos de la zona
    return flota


def viajes_de_un_dia(ve, P, azar):
    """[salida, duración h, km, termina en casa, zona destino] de cada viaje del día."""
    m = P["viajes_por_dia"]
    n = math.floor(m) + (azar.random() < m - math.floor(m))
    h, d, od = P["hora_salida"], P["duracion_viaje"], P["matriz_od"]
    salidas = sorted(x + azar.random() for x in azar.choices(list(h["hora"]), weights=list(h["viajes"]), k=n))
    rangos = list(zip(d["desde_min"], d["hasta_min"]))
    viajes, libre, aqui = [], 0.0, ve["zona"]
    for salida in salidas:
        a, b = azar.choices(rangos, weights=list(d["porcentaje"]))[0]
        dur = azar.uniform(a, b) / 60
        inicio = max(salida, libre)
        if inicio + dur > 24:
            break
        destino = azar.choices(list(od.columns), weights=list(od.loc[aqui]))[0]
        viajes.append([inicio, dur, dur * P["velocidad_kmh"], False, destino])
        libre, aqui = inicio + dur, destino
    if viajes:
        viajes[-1][3:] = [True, ve["zona"]]          # el último vuelve a casa
    return viajes


def generar_viajes(flota, P, azar):
    return {ve["vehiculo"]: [[dia * 24 + v[0], *v[1:]] for dia in range(365)
                             for v in viajes_de_un_dia(ve, P, azar)] for ve in flota}


def cargar(perfil, reg, zona, tipo, t0, t_max, soc, ve, P):
    """Carga hasta el SOC objetivo o hasta t_max, repartiendo la energía hora por hora."""
    pot, bat = P[f"potencia_{tipo}_kw"], ve["bateria_kwh"]
    t_fin = min(t_max, t0 + (P["soc_objetivo"] - soc) * bat / pot)
    if t_fin <= t0:
        return soc
    reg.cargas.writerow([ve["vehiculo"], ve["zona"], zona, tipo, round(t0, 3), int(t0 // 24) % 365 + 1,
                         round(t_fin - t0, 4), round(pot * (t_fin - t0), 4), pot, bat, round(100 * soc, 1)])
    t = t0
    while t < t_fin - 1e-9:
        fin = min(t_fin, math.floor(t) + 1)
        e = pot * (fin - t)
        h = int(t) % HORAS
        perfil[(zona, tipo)][h] += e * ve["peso"]
        reg.horas.writerow([ve["vehiculo"], ve["zona"], zona, tipo, h, h // 24 + 1, h % 24, round(e, 4)])
        soc += e / bat
        t = fin
    return soc


def simular(flota, viajes, P, azar, reg):
    perfil = {(z, t): np.zeros(HORAS) for z in P["ve_por_zona"]["zona"] for t in TIPOS}
    for ve in flota:
        soc, bat, lista = ve["carga_inicial"], ve["bateria_kwh"], viajes[ve["vehiculo"]]
        dias = {}
        for i, (inicio, dur, km, a_casa, destino) in enumerate(lista):
            llegada, dia, gasto = inicio + dur, int(inicio // 24) + 1, P["consumo_kwh_km"] * km
            d = dias.setdefault(dia, {"viajes": 0, "km": 0, "gasto": 0, "inicio": soc, "cargas": 0,
                                      "zonas": [], **dict.fromkeys(TIPOS, 0)})
            antes = soc
            soc -= gasto / bat
            agotada = soc <= 0
            soc = al_llegar = max(soc, 0.0)
            tipo = ""
            if soc < P["umbral_carga"]:
                prox = lista[i + 1][0] if i + 1 < len(lista) else llegada + 24
                if agotada or prox - llegada <= P["horas_para_rapida"]:
                    tipo, fin = "rapida", llegada + azar.uniform(P["rapida_min_minutos"], P["rapida_max_minutos"]) / 60
                else:
                    tipo, fin = ("lenta" if a_casa and ve["garaje"] else "semirrapida"), prox
                soc = cargar(perfil, reg, destino, tipo, llegada, fin, soc, ve, P)
            cargado = (soc - al_llegar) * bat
            d["viajes"] += 1; d["km"] += km; d["gasto"] += gasto; d["fin"] = soc
            d["zonas"].append(destino)
            if tipo:
                d[tipo] += cargado; d["cargas"] += 1
            reg.viajes.writerow([ve["vehiculo"], ve["zona"], dia, d["viajes"], round(inicio % 24, 3),
                                 round(llegada % 24, 3), round(km, 2), round(gasto, 3), round(100 * antes, 1),
                                 round(100 * al_llegar, 1), destino, a_casa, tipo, round(cargado, 3),
                                 round(100 * soc, 1)])
        ultimo = ve["carga_inicial"]
        for dia in range(1, 366):
            d = dias.get(dia)
            if d:
                fila = [d["viajes"], round(d["km"], 2), round(d["gasto"], 3), *[round(d[t], 3) for t in TIPOS],
                        round(sum(d[t] for t in TIPOS), 3), d["cargas"], round(100 * d["inicio"], 1),
                        round(100 * d["fin"], 1), " > ".join(d["zonas"])]
                ultimo = d["fin"]
            else:
                fila = [0, 0, 0, 0, 0, 0, 0, 0, round(100 * ultimo, 1), round(100 * ultimo, 1), ""]
            reg.diario[ve["zona"]].writerow([ve["vehiculo"], ve["zona"], bat, int(ve["garaje"]), dia, *fila])
    return perfil


def guardar(perfil, flota):
    anual = pd.DataFrame({f"{z}|{t}": s.round(2) for (z, t), s in perfil.items()})
    anual.index.name = "hora_del_anio"
    largo = (anual.groupby(anual.index % 24).mean().stack().rename("potencia_kw").round(2)
             .rename_axis(["hora", "zona_tipo"]).reset_index())
    largo[["zona", "tipo"]] = largo.pop("zona_tipo").str.split("|", expand=True)
    largo = largo[["zona", "tipo", "hora", "potencia_kw"]]
    matriz = largo.pivot_table(index=["tipo", "zona"], columns="hora", values="potencia_kw").reindex(TIPOS, level=0)
    matriz.columns = [f"{h:02d}h" for h in matriz.columns]
    resumen = pd.DataFrame([{"zona": z, "tipo": t, "energia_anual_kWh": round(s.sum()),
                             "potencia_promedio_kW": round(s.mean(), 1), "potencia_pico_kW": round(s.max(), 1),
                             "hora_pico_dia_promedio": int(s.reshape(365, 24).mean(0).argmax())}
                            for (z, t), s in perfil.items()])
    por_zona = resumen.pivot(index="zona", columns="tipo", values="energia_anual_kWh")[TIPOS]
    por_zona["total_kWh"] = por_zona.sum(axis=1)
    por_zona.loc["TOTAL"] = por_zona.sum()
    valle = largo.groupby(["tipo", "hora"])["potencia_kw"].sum().unstack().reindex(TIPOS)
    with pd.ExcelWriter(RESULTADOS / "resultado_algoritmo.xlsx") as w:
        por_zona.to_excel(w, sheet_name="energia_por_zona")
        valle.round(1).to_excel(w, sheet_name="valle_por_hora")
        resumen.to_excel(w, sheet_name="resumen_zona", index=False)
        matriz.to_excel(w, sheet_name="matriz")
        largo.to_excel(w, sheet_name="dataframe", index=False)
    matriz.to_csv(RESULTADOS / "matriz_potencia_zona_hora.csv", encoding="utf-8-sig")
    largo.to_csv(RESULTADOS / "dataframe_resultados.csv", index=False, encoding="utf-8-sig")
    anual.to_csv(RESULTADOS / "perfiles_8760_horas.csv", encoding="utf-8-sig")
    pd.DataFrame(flota).to_csv(RESULTADOS / "vehiculos_simulados.csv", index=False, encoding="utf-8-sig")
    return por_zona


if __name__ == "__main__":
    P = leer_insumos()
    azar = random.Random(int(P["semilla"]))
    flota = crear_flota(P, azar)
    print(f"{len(flota)} vehículos; sorteando viajes...")
    viajes = generar_viajes(flota, P, azar)
    print(f"{sum(map(len, viajes.values())):,} viajes; simulando...")
    RESULTADOS.mkdir(exist_ok=True)
    reg = Registro(RESULTADOS / "por_carro", list(P["ve_por_zona"]["zona"]))
    perfil = simular(flota, viajes, P, azar, reg)
    reg.cerrar()
    print(guardar(perfil, flota).round(0).to_string())
