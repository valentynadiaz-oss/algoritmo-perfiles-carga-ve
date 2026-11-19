@echo off
chcp 65001 > nul
title Algoritmo de perfiles de carga de VE
cd /d "%~dp0"
echo ============================================================
echo   ALGORITMO DE PERFILES DE CARGA DE VEHICULOS ELECTRICOS
echo   Insumos:    3_carga\insumos_algoritmo.xlsx
echo   Resultados: 5_resultados\    Graficas: 6_graficas\
echo   (Cierre los Excel de insumos y resultados antes de correr)
echo   Con los 3.001 carros tarda unos 35 minutos.
echo ============================================================
echo.
set "PY=%~dp0..\..\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" -X utf8 -W ignore 4_modelo\algoritmo.py
if errorlevel 1 goto error
"%PY%" -X utf8 -W ignore 4_modelo\analisis_gasto_diario.py
if errorlevel 1 goto error
"%PY%" -X utf8 -W ignore 4_modelo\curva_dia_maximo.py
if errorlevel 1 goto error
start "" "5_resultados"
goto fin
:error
echo.
echo HUBO UN ERROR. Revise el mensaje de arriba.
echo Si dice "Permission denied", cierre el Excel de resultados y vuelva a correr.
:fin
echo.
pause
