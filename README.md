# Perfiles de carga de vehículos eléctricos por zona

Implementación sencilla del algoritmo de simulación de viajes y decisión de carga de Mejía
Alzate (2021) y Mejia et al. (2025). Se aplica a un caso de estudio en el Valle de Aburrá,
porque es donde hay una encuesta origen-destino pública y reciente (EOD 2025). Los vehículos
son los 3.001 proyectados para Pereira en 2030 (Objetivo 2).

El caso es ficticio: sirve para estudiar el algoritmo, no para ubicar cargadores reales.

## Estructura

| Carpeta | Contenido |
|---|---|
| `1_extraccion/` | Descarga de datos; copias en `datos_crudos/` |
| `2_transformacion/` | Zonas, matriz origen-destino e insumos |
| `3_carga/` | `insumos_algoritmo.xlsx`, lo único que lee el modelo |
| `4_modelo/` | `algoritmo.py` y `analisis_gasto_diario.py` |
| `5_resultados/` | Tablas de salida y registro por vehículo (`por_carro/`) |
| `6_graficas/` | Mapas y gráficas |
| `7_documentacion/` | Documento Word |

Para correr: doble clic en `CORRER_ALGORITMO.bat` (unos 35 min con los 3.001 vehículos).

Para rehacer las zonas, en `2_transformacion/`: `crear_zonas_por_estrato.py`,
`crear_matriz_od_zonas.py`, `actualizar_insumos_zonas.py` y las dos gráficas.

## Datos

| Dato | Fuente |
|---|---|
| Hora de salida, duración de viajes, viajes por persona (2,34) | EOD 2025, tablero (Área Metropolitana del Valle de Aburrá, 2025) |
| Matriz origen-destino entre 67 macrozonas | EOD 2025, API del tablero, indicador 15 |
| Población por estrato de cada macrozona | EOD 2025, API del tablero, indicador 46 |
| Tipo de vivienda por municipio | CNPV 2018 (DANE, 2018) |
| Códigos de municipio | DIVIPOLA (DANE, s. f.) |
| Predios por estrato y comuna de Pereira | Secretaría de Planeación de Pereira (2011) |
| VE 2030 por comuna | Objetivo 2 |
| Consumo: 0,135 kWh/km | Enel (s. f.) |
| Velocidad urbana: 22,5 km/h | Punto medio de 20–25 km/h, EOD 2017 (El Colombiano, s. f.) |
| Batería 24/35/50 kWh, carga inicial 50–100 %, umbral 30 %, carga hasta 90 %, rápida de 10 a 60 min | Mejía Alzate (2021) |
| Potencias: rápida 22 kW, semirrápida 7,4 kW, lenta 3,7 kW | Puntos de carga existentes en Pereira (sección 2.5) |
| VE matriculados por municipio (solo referencia) | RUNT 2.0 (Ministerio de Transporte, 2026) |

## Zonas

Las 66 macrozonas de la EOD 2025 se agrupan por la **moda del estrato** (el estrato con más
población). Salen cinco modas: 1, 2, 3, 5 y 6; ninguna macrozona tiene moda 4. Cada moda es una
zona.

Cada comuna de Pereira va a la zona con su misma moda (estrato con más predios). Boston tiene
moda 4 y se asigna por su segundo estrato (3).

| Zona | Moda | Macrozonas | VE | Comunas de Pereira |
|---|---|---|---|---|
| 1 | 1 | 5 | 300 | Ferrocarril, Oriente, Villa Santana |
| 2 | 2 | 39 | 863 | Consota, Del Café, El Oso, Perla del Otún, San Joaquín, San Nicolás |
| 3 | 3 | 15 | 943 | Boston, Cuba, El Poblado, Río Otún, Villavicencio |
| 4 | 5 | 4 | 601 | Centro, El Rocío, Olímpica |
| 5 | 6 | 3 | 294 | El Jardín, Universidad |

Como las zonas son grupos de macrozonas de la encuesta, la matriz origen-destino de las zonas
es la suma exacta de la de sus macrozonas.

Garaje: se supone que un vehículo con vivienda tipo apartamento tiene parqueadero para cargar.
La probabilidad es el porcentaje de apartamentos de la zona.

Mapas: `6_graficas/mapa_zonas_ficticias.png`, `mapa_carros_por_zona.png` y
`esquema_extrapolacion_pereira_valle.png`.

## Algoritmo

1. Cada vehículo recibe una zona, una batería, una carga inicial y garaje o no.
2. Cada día hace 2 o 3 viajes (promedio 2,34). La hora y la duración se sortean de la EOD; el
   destino, con la matriz origen-destino de la zona donde está. El último viaje vuelve a casa.
   Distancia = duración × velocidad.
3. Cada viaje descuenta consumo × km. Si al llegar la batería queda bajo 30 %, carga:
   - batería agotada o próximo viaje en menos de 1 h: rápida;
   - llegó a casa y tiene garaje: lenta;
   - otro caso: semirrápida.
4. La batería pasa de un día al siguiente.

Diferencias con las fuentes originales: los viajes se sortean de los resúmenes de la EOD (Mejía
usa viajes reales de cada vehículo), la batería se revisa al llegar y no durante el viaje, y no
se usa k-means.

## Resultados

| Archivo | Contenido |
|---|---|
| `resultado_algoritmo.xlsx` | Energía por zona, curva del Valle, resumen, matriz y data frame |
| `matriz_potencia_zona_hora.csv` | kW por zona y hora (día promedio), por tipo de cargador |
| `por_carro/diario_Zona_N.csv` | Cada vehículo, cada día: viajes, km, kWh gastados y cargados, batería al inicio y al final |
| `por_carro/viajes_por_carro.csv` | Cada viaje, con la batería antes y después |
| `por_carro/cargas.csv` | Cada carga |
| `por_carro/cargas_por_hora.csv` | Cada hora en que un vehículo estuvo cargando |
| `gasto_diario/gasto_diario_por_vehiculo.xlsx` | Resumen, ajuste de distribución, por zona y por vehículo |
| `curva_dia_maximo_por_zona.xlsx` | kW por zona y hora sumando el día de mayor carga de cada vehículo |

Los archivos de `por_carro/` y `perfiles_8760_horas.csv` son grandes y no se suben a git; se
generan al correr.

**Gasto diario.** Es la energía que gasta cada vehículo en el día (km × consumo). El boxplot
usa todos los vehículo-día (3.001 × 365). La distribución que mejor ajusta es la gamma (prueba
KS). Por vehículo se toma su máximo diario, con los días atípicos incluidos porque también pueden
ocurrir; el máximo sin atípicos queda como referencia.

**Demanda con el día máximo.** De cada vehículo se toma el día en que más energía cargó y su
curva por hora, en la zona donde cargó. La suma de esas curvas da los kW por zona y hora si
todos coinciden en su peor día (`4_modelo/curva_dia_maximo.py`; gráfica
`6_graficas/curva_dia_maximo_por_zona.png`).

**Limitación.** El gasto promedio anual es casi igual en todos los vehículos (≈ 4,2 kWh/día,
31 km/día), porque todos sortean de las mismas distribuciones.

### Última corrida

3.001 vehículos, 365 días, 2.551.433 viajes.

| Zona | Energía al año (MWh) | Pico con el día máximo de cada vehículo (kW) | Hora del pico |
|---|---|---|---|
| 1 | 366 | 511 | 11:00 |
| 2 | 1.620 | 3.001 | 11:00 |
| 3 | 1.441 | 2.591 | 10:00 |
| 4 | 706 | 1.080 | 11:00 |
| 5 | 412 | 674 | 11:00 |
| **Total** | **4.545** | **7.832** | 11:00 |

Gasto diario por vehículo: mediana 3,76 kWh, Q1–Q3 de 2,37 a 5,52 kWh, máximo 21,4 kWh.
Ajuste: gamma (KS = 0,014). Suma de los máximos diarios de los 3.001 vehículos: 40.935 kWh
(30.139 kWh sin atípicos).

## Pendientes

- Fuente para los km recorridos y la velocidad (la actual es de prensa).
- Microdatos de la EOD para dar a cada vehículo su propia rutina.
- La duración de los viajes de la EOD mezcla todos los modos.
- El estrato de Pereira es de 2011.

## Referencias

Área Metropolitana del Valle de Aburrá. (2025). *Encuesta Origen-Destino 2025* [Tablero de
datos]. Recuperado el 19 de noviembre de 2026, de https://eod2025.metropol.gov.co/

Departamento Administrativo Nacional de Estadística [DANE]. (2018). *Censo Nacional de
Población y Vivienda 2018: tipo de vivienda* [Visor de datos]. Recuperado el 5 de noviembre de
2026, de https://sitios.dane.gov.co/cnpv/#!/tipo_viviendad

Departamento Administrativo Nacional de Estadística [DANE]. (s. f.). *DIVIPOLA: códigos de
municipios* [Conjunto de datos]. Datos Abiertos Colombia. Recuperado el 5 de noviembre de 2026,
de https://www.datos.gov.co/widgets/gdxc-w37w

El Colombiano. (s. f.). *Movilidad en el Valle de Aburrá: encuesta origen destino*.
Recuperado el 29 de octubre de 2026, de
https://www.elcolombiano.com/antioquia/movilidad-en-el-valle-de-aburra-encuesta-origen-destino-XJ8597154

Enel. (s. f.). *¿Cuánto consume un coche eléctrico?* Recuperado el 5 de noviembre de 2026, de
https://www.enel.com/es/learning-hub/movilidad-electrica/consumo-coche-electrico

Federación Nacional de Comerciantes [Fenalco]. (2025). *Informe vehículos eléctricos e
híbridos mayo 2025*.
https://www.fenalco.com.co/blog/gremial-4/informe-vehiculos-electricos-e-hibridos-mayo-2025-8125

Mejia, M. A., Macedo, L. H., Pinto, T., & Franco, J. F. (2025). Integrating a spatio-temporal
diffusion model with a multi-criteria decision-making approach for optimal planning of
electric vehicle charging infrastructure. *Applied Energy, 395*, 126160.
https://doi.org/10.1016/j.apenergy.2025.126160

Mejía Alzate, M. A. (2021). *Planejamento de sistemas de distribuição de energia elétrica
incluindo estações de carregamento de veículos elétricos e fontes renováveis de geração
distribuída* [Tesis doctoral, Universidade Estadual Paulista «Júlio de Mesquita Filho»].

Ministerio de Transporte. (2026). *Vehículos eléctricos e híbridos matriculados en Colombia –
RUNT 2.0* [Conjunto de datos]. Datos Abiertos Colombia. Recuperado el 19 de noviembre de 2026,
de https://www.datos.gov.co/Transporte/VEH-CULOS-EL-CTRICOS-E-H-BRIDOS-MATRICULADOS-EN-CO/ntxy-q9ix

OpenStreetMap contributors. (2026). *Límites administrativos de los municipios del Valle de
Aburrá* [Datos geográficos]. Recuperado el 5 de noviembre de 2026, de https://www.openstreetmap.org

Secretaría de Planeación de Pereira. (2011). *Informe de la estratificación socioeconómica del
municipio de Pereira, años 2008/2009/2010/2011*. Alcaldía de Pereira.
