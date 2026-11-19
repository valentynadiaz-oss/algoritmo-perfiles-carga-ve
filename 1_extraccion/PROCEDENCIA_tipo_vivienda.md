# Tipo de vivienda (casa / apartamento): de dónde sale

**Para qué se busca.** En el algoritmo original (Mejia et al., 2025, sección 3.1), el porcentaje
de VE que carga en casa es el **porcentaje de casas unifamiliares** de cada región, y el que
carga en cargador público es el **porcentaje de apartamentos**. Este dato reemplaza los
escenarios de garaje (0, 50 y 100 %), que no tenían fuente.

**Resultado:** `tipo_vivienda_DANE_CNPV2018.xlsx`, en esta misma carpeta.

## Fuente

- **DANE, Censo Nacional de Población y Vivienda (CNPV) 2018**, tema «Tipo de vivienda».
  Visor: <https://sitios.dane.gov.co/cnpv/#!/tipo_viviendad>
- El visor no descarga todos los municipios a la vez: se elige uno en el botón del
  departamento o municipio. Pero el visor lee sus datos de un archivo público que trae
  **todos los municipios del país** con su código DIVIPOLA:
  <https://sitios.dane.gov.co/cnpv/app/data/json/cv/viviendas/tipo_vivienda.json>
  Los porcentajes son los mismos que muestra el visor al elegir cada municipio.
- **DIVIPOLA** (datos.gov.co, conjunto `gdxc-w37w`, <https://www.datos.gov.co/widgets/gdxc-w37w>):
  se usa para identificar los municipios por su código y ponerles nombre.
- **Viviendas ocupadas con personas presentes**, del mismo visor
  (`total_viviendas_ocup.json`): se usa solo para ponderar el promedio del Valle de Aburrá.

Las copias descargadas están en `fuentes/dane_cnpv2018/`. Para descargarlas de nuevo:
`python extraer_tipo_vivienda_dane.py`.

## Qué se buscó en el DIVIPOLA

Los 10 municipios del Área Metropolitana del Valle de Aburrá, que es el ámbito de la Encuesta
Origen-Destino 2025:

| DIVIPOLA | Municipio | Casa | Apartamento |
|---|---|---|---|
| 05001 | Medellín | 40,23 % | 57,20 % |
| 05079 | Barbosa | 66,12 % | 32,24 % |
| 05088 | Bello | 29,93 % | 68,04 % |
| 05129 | Caldas | 31,84 % | 66,60 % |
| 05212 | Copacabana | 46,46 % | 51,47 % |
| 05266 | Envigado | 31,18 % | 67,51 % |
| 05308 | Girardota | 52,17 % | 45,83 % |
| 05360 | Itagüí | 20,35 % | 77,86 % |
| 05380 | La Estrella | 41,41 % | 57,65 % |
| 05631 | Sabaneta | 18,68 % | 80,73 % |
| — | **Valle de Aburrá, ponderado** | **37,02 %** | **60,73 %** |

Como referencia: Antioquia (05) 50,93 % casas; **Pereira (66001) 72,26 % casas y 25,94 %
apartamentos**; Risaralda (66) 74,85 % casas; total nacional 61,53 % casas.

El resto hasta 100 % son «tipo cuarto», vivienda tradicional indígena o étnica y otros; están
en el Excel.

## Límites

- El visor llega hasta **municipio**, no hasta comuna. Para Pereira hay un solo valor para
  las 19 comunas.
- El censo dice si la vivienda es casa o apartamento, no si tiene garaje. Tomar casa = puede
  cargar en casa es el supuesto del artículo, y así se debe citar.
- El promedio del Valle se pondera por viviendas ocupadas, porque el visor no publica el
  total de viviendas de cada tipo.
