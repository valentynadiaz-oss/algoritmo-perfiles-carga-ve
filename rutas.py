"""Rutas de la carpeta, en un solo lugar. Todos los scripts las importan.

    1_extraccion/       descargar los datos crudos de sus fuentes
        datos_crudos/   copias de lo descargado (no se edita a mano)
    2_transformacion/   convertir los datos crudos en insumos del modelo
    3_carga/            insumos listos que lee el algoritmo
    4_modelo/           el algoritmo y el análisis del gasto diario
    5_resultados/       tablas que salen del algoritmo
    6_graficas/         todos los mapas y gráficas
    7_documentacion/    Word, referencias APA
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

EXTRACCION = RAIZ / "1_extraccion"
CRUDOS = EXTRACCION / "datos_crudos"
CRUDOS_EOD_API = CRUDOS / "eod2025_api"
CRUDOS_EOD_TABLERO = CRUDOS / "eod2025_tablero"
CRUDOS_DANE = CRUDOS / "dane_cnpv2018"
CRUDOS_OSM = CRUDOS / "openstreetmap"
CRUDOS_OBJ2 = CRUDOS / "objetivo2_pereira"
CRUDOS_RUNT = CRUDOS / "runt_mintransporte"

TRANSFORMACION = RAIZ / "2_transformacion"
CARGA = RAIZ / "3_carga"
INSUMOS = CARGA / "insumos_algoritmo.xlsx"
ZONAS_XLSX = CARGA / "zonas_ficticias.xlsx"
ZONAS_GEOJSON = CARGA / "zonas_ficticias.geojson"
MATRIZ_OD_XLSX = CARGA / "matriz_od_zonas.xlsx"
TIPO_VIVIENDA_XLSX = CARGA / "tipo_vivienda_DANE_CNPV2018.xlsx"

MODELO = RAIZ / "4_modelo"
RESULTADOS = RAIZ / "5_resultados"
GASTO_DIARIO = RESULTADOS / "gasto_diario"
GRAFICAS = RAIZ / "6_graficas"
DOCUMENTACION = RAIZ / "7_documentacion"

PYTHON = RAIZ.parents[1] / "venv" / "Scripts" / "python.exe"
