"""Copia zonas y matriz origen-destino al Excel de insumos (hojas ve_por_zona y matriz_od)."""
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import INSUMOS as EXCEL, MATRIZ_OD_XLSX, ZONAS_XLSX  # noqa: E402
FUENTE = ("Zonas ficticias del Valle de Aburrá por MODA del estrato (zonas_ficticias.xlsx; EOD 2025, "
          "indicador 46). VE: comunas de Pereira (Objetivo 2, Tabla 14) asignadas a la zona con su misma "
          "moda de estrato (Planeación Pereira 2011). fraccion_garaje = % de APARTAMENTOS (DANE CNPV 2018; "
          "supuesto: el apartamento tiene parqueadero para cargar)")


def main():
    z = pd.read_excel(ZONAS_XLSX, sheet_name="zonas")
    ve = pd.DataFrame({"zona": z["zona"], "vehiculos": z["vehiculos"],
                       "fraccion_garaje": (z["apartamento_%"] / 100).round(4),
                       "moda_estrato": z["moda_estrato"],
                       "comunas_pereira_asignadas": z["comunas_pereira_asignadas"], "fuente": FUENTE})
    od = pd.read_excel(MATRIZ_OD_XLSX, sheet_name="viajes", index_col=0)
    od.index.name = "origen \\ destino"

    wb = load_workbook(EXCEL)
    for hoja in ("ve_por_zona", "matriz_od"):
        if hoja in wb.sheetnames:
            del wb[hoja]
    wb.save(EXCEL)
    with pd.ExcelWriter(EXCEL, engine="openpyxl", mode="a") as w:
        ve.to_excel(w, sheet_name="ve_por_zona", index=False)
        od.to_excel(w, sheet_name="matriz_od")
    wb = load_workbook(EXCEL)
    for hoja, anchos in (("ve_por_zona", [10, 12, 15, 14, 70, 90]), ("matriz_od", [16] * 8)):
        ws = wb[hoja]
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="21213D")
        for i, a in enumerate(anchos):
            ws.column_dimensions[chr(65 + i)].width = a
    wb.save(EXCEL)
    print(ve[["zona", "moda_estrato", "vehiculos", "fraccion_garaje"]].to_string(index=False))
    print(od)


if __name__ == "__main__":
    main()
