"""Tipo de vivienda por municipio (DANE, CNPV 2018) para el Valle de Aburrá y Pereira.
Usa el JSON del visor del censo y la DIVIPOLA de datos.gov.co."""
import json
import urllib.request
from pathlib import Path

import pandas as pd

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import CRUDOS_DANE as FUENTES, TIPO_VIVIENDA_XLSX as SALIDA  # noqa: E402
URL_DANE = "https://sitios.dane.gov.co/cnpv/app/data/json/cv/viviendas/"
URL_DIVIPOLA = "https://www.datos.gov.co/resource/gdxc-w37w.json?$limit=5000"

# Los 10 municipios del Área Metropolitana del Valle de Aburrá, ámbito de la EOD 2025.
VALLE_DE_ABURRA = ["05001", "05079", "05088", "05129", "05212",
                   "05266", "05308", "05360", "05380", "05631"]
OTROS = {"0": "TOTAL NACIONAL", "05": "ANTIOQUIA (departamento)",
         "66": "RISARALDA (departamento)", "66001": None}       # None: nombre del DIVIPOLA
COLUMNAS = {"Casa": "casa_%", "Apartamento": "apartamento_%", "Tipo cuarto": "tipo_cuarto_%",
            "Vivienda tradicional indígena": "tradicional_indigena_%",
            "Vivienda tradicional étnica (afrocolombiana, isleña, Rrom)": "tradicional_etnica_%",
            "Otro (contenedor, carpa, embarcación, vagón, cueva, refugio natural, etc.)": "otro_%"}


def descargar(url, archivo):
    FUENTES.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        (FUENTES / archivo).write_bytes(r.read())
    return json.loads((FUENTES / archivo).read_text(encoding="utf-8-sig"))


def codigo(x):
    """El JSON del DANE trae 5001 o "05"; se normaliza a 5 dígitos (municipio) o 2 (depto)."""
    s = str(x).strip()
    if s == "0":
        return "0"
    return s.zfill(5) if len(s) > 2 else s.zfill(2)


def main():
    tipo = descargar(URL_DANE + "tipo_vivienda.json", "tipo_vivienda.json")
    ocup = descargar(URL_DANE + "total_viviendas_ocup.json", "total_viviendas_ocup.json")
    divi = descargar(URL_DIVIPOLA, "divipola_municipios.json")

    tipo = {codigo(r["divipola"]): r for r in tipo}
    ocup = {codigo(r["divipola"]): r["valor"] for r in ocup}
    nombres = {r["cod_mpio"]: (r["nom_mpio"], r["dpto"]) for r in divi}

    filas = []
    for cod in VALLE_DE_ABURRA + list(OTROS):
        r = tipo[cod]
        nombre, dpto = nombres.get(cod, (OTROS.get(cod), ""))
        fila = {"divipola": cod, "municipio": nombre, "departamento": dpto,
                "grupo": "Valle de Aburrá" if cod in VALLE_DE_ABURRA else "Referencia",
                "viviendas_ocupadas": ocup.get(cod)}
        fila.update({nuevo: r[viejo] for viejo, nuevo in COLUMNAS.items()})
        filas.append(fila)
    df = pd.DataFrame(filas)

    # Promedio del Valle de Aburrá ponderado por viviendas ocupadas.
    va = df[df.grupo == "Valle de Aburrá"]
    w = va["viviendas_ocupadas"]
    prom = {"divipola": "-", "municipio": "VALLE DE ABURRÁ (10 municipios, ponderado)",
            "departamento": "ANTIOQUIA", "grupo": "Valle de Aburrá",
            "viviendas_ocupadas": int(w.sum())}
    prom.update({c: round((va[c] * w).sum() / w.sum(), 2) for c in COLUMNAS.values()})
    df = pd.concat([df.iloc[:len(va)], pd.DataFrame([prom]), df.iloc[len(va):]], ignore_index=True)

    fuente = pd.DataFrame({"FUENTE Y MÉTODO": [
        "Tipo de vivienda: DANE, Censo Nacional de Población y Vivienda (CNPV) 2018.",
        "Visor: https://sitios.dane.gov.co/cnpv/#!/tipo_viviendad",
        "Archivo de datos del visor (todos los municipios): " + URL_DANE + "tipo_vivienda.json",
        "Viviendas ocupadas (para ponderar): " + URL_DANE + "total_viviendas_ocup.json",
        "Nombres de municipios: DIVIPOLA, datos.gov.co, conjunto gdxc-w37w (" + URL_DIVIPOLA + ")",
        "",
        "Los porcentajes son los mismos que muestra el visor al elegir cada municipio.",
        "El promedio del Valle de Aburrá pondera cada municipio por sus viviendas ocupadas con",
        "personas presentes (el visor no publica el total de viviendas por tipo).",
        "Valle de Aburrá = los 10 municipios del Área Metropolitana: Medellín, Barbosa, Bello,",
        "Caldas, Copacabana, Envigado, Girardota, Itagüí, La Estrella y Sabaneta.",
        "El visor llega hasta municipio: no trae comunas.",
    ]})
    with pd.ExcelWriter(SALIDA, engine="openpyxl") as wr:
        df.to_excel(wr, sheet_name="tipo_vivienda", index=False)
        fuente.to_excel(wr, sheet_name="fuente", index=False)
        ws = wr.sheets["tipo_vivienda"]
        for col, ancho in zip("ABCDEFGHIJK", [9, 44, 14, 16, 18, 9, 14, 13, 20, 19, 9]):
            ws.column_dimensions[col].width = ancho
        wr.sheets["fuente"].column_dimensions["A"].width = 120
    print(df[["divipola", "municipio", "viviendas_ocupadas", "casa_%", "apartamento_%"]]
          .to_string(index=False))
    print("\nok", SALIDA)


if __name__ == "__main__":
    main()
