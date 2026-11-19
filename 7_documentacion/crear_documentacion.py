"""Arma Documentacion_algoritmo.docx con los insumos y resultados que haya en la carpeta.
Se puede volver a correr después de cambiar insumos: python crear_documentacion.py"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.section import WD_ORIENT, WD_SECTION  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rutas import DOCUMENTACION, GRAFICAS, INSUMOS as INS, RESULTADOS, ZONAS_XLSX  # noqa: E402

RES = RESULTADOS / "resultado_algoritmo.xlsx"
SALIDA = DOCUMENTACION / "Documentacion_algoritmo.docx"
FIGS = GRAFICAS / "documentacion"
NAVY, PURP, LILA, AZUL, FONDO = "#21213D", "#A060FF", "#C687FC", "#4657D3", "#F6EFFE"
COLOR_TIPO = {"rapida": PURP, "lenta": AZUL, "residencial": LILA}
NOMBRE_TIPO = {"rapida": "Rápida (50 kW)", "lenta": "Lenta pública", "residencial": "Residencial"}


def miles(x, dec=0):
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------------- figuras
def figura_flujo(ruta):
    fig, ax = plt.subplots(figsize=(8.2, 9.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 12.6); ax.axis("off")

    def caja(x, y, w, h, texto, color, borde=None, txt="white", tam=9.5):
        ax.add_patch(plt.Rectangle((x - w / 2, y - h / 2), w, h, facecolor=color,
                                   edgecolor=borde or color, lw=1.5, zorder=2))
        ax.text(x, y, texto, ha="center", va="center", color=txt, fontsize=tam, zorder=3,
                wrap=True)

    def flecha(x1, y1, x2, y2, etiqueta=None, lado="right"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.3), zorder=1)
        if etiqueta and y1 == y2:                       # flecha horizontal: texto encima
            ax.text((x1 + x2) / 2, y1 + 0.22, etiqueta, fontsize=8.5, color=NAVY,
                    fontweight="bold", ha="center", va="center")
        elif etiqueta:
            ax.text((x1 + x2) / 2 + (0.15 if lado == "right" else -0.15), (y1 + y2) / 2,
                    etiqueta, fontsize=8.5, color=NAVY, fontweight="bold",
                    ha="left" if lado == "right" else "right", va="center")

    caja(5, 12.0, 7.6, 0.8, "PASO 0 · Leer insumos (insumos_algoritmo.xlsx)", NAVY)
    caja(5, 10.95, 7.6, 0.8, "PASO 1 · Crear la flota: VE por zona, batería, carga inicial y garaje", NAVY)
    caja(5, 9.9, 7.6, 0.8, "PASO 2 · Sortear los viajes de cada VE, los 365 días\n"
         "(cuántos, a qué hora, cuánto duran, a qué zona van)", NAVY)
    caja(5, 8.75, 7.6, 0.8, "PASO 3 · Para cada VE, cada viaje: gastar batería = consumo × km",
         AZUL)
    caja(5, 7.55, 5.2, 0.85, "¿La batería quedó\npor debajo del 30 %?", FONDO, PURP, NAVY)
    caja(9.0, 7.55, 1.7, 0.7, "Siguiente\nviaje", "white", NAVY, NAVY, 8.5)
    caja(5, 6.2, 5.6, 0.95, "Condición 1: ¿se agotó la batería o\nel próximo viaje sale en < 1 hora?",
         FONDO, PURP, NAVY)
    caja(9.0, 6.2, 1.7, 0.85, "CARGA\nRÁPIDA\n10–60 min", PURP, tam=8.5)
    caja(5, 4.8, 5.6, 0.85, "Condición 2: ¿llegó a casa\ny la casa tiene garaje?", FONDO, PURP, NAVY)
    caja(9.0, 4.8, 1.7, 0.85, "CARGA\nRESIDENCIAL", LILA, tam=8.5)
    caja(5, 3.45, 4.0, 0.75, "Condición 3: CARGA LENTA pública", AZUL, tam=9)
    caja(5, 2.2, 7.6, 0.8, "Anotar la energía, hora por hora, en la zona donde terminó el viaje",
         NAVY)
    caja(5, 0.9, 7.6, 0.9, "PASO 4 · Sumar los 3.001 VE → kW por zona, hora y tipo\n"
         "(Excel, matriz, data frame y perfiles de 8.760 horas)", PURP)
    for y1, y2 in [(11.6, 11.35), (10.55, 10.3), (9.5, 9.15), (8.35, 7.98)]:
        flecha(5, y1, 5, y2)
    flecha(7.6, 7.55, 8.15, 7.55, "NO")
    flecha(5, 7.12, 5, 6.68, "SÍ", "right")
    flecha(7.8, 6.2, 8.15, 6.2, "SÍ")
    flecha(5, 5.72, 5, 5.23, "NO")
    flecha(7.8, 4.8, 8.15, 4.8, "SÍ")
    flecha(5, 4.37, 5, 3.83, "NO")
    flecha(5, 3.07, 5, 2.6)
    flecha(5, 1.8, 5, 1.35)
    ax.text(0.2, 6.2, "Carga hasta 90 %\no hasta que sale\nel próximo viaje\n(lenta y residencial)",
            fontsize=8, color=NAVY, va="center", style="italic")
    fig.savefig(ruta, dpi=200, bbox_inches="tight"); plt.close(fig)


def figura_ciudad(ciudad, ruta):
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for t in ["rapida", "lenta", "residencial"]:
        ax.plot(range(24), ciudad.loc[t].values, color=COLOR_TIPO[t], lw=2.4, label=NOMBRE_TIPO[t])
    ax.set_xticks(range(0, 24, 3)); ax.set_xlabel("Hora del día"); ax.set_ylabel("kW, todo el Valle")
    ax.grid(alpha=.3); ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout(); fig.savefig(ruta, dpi=200); plt.close(fig)


def figura_zonas(e, ruta):
    e = e.sort_index(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    izq = 0
    for t in ["rapida", "lenta", "residencial"]:
        ax.barh(e.index, e[t] / 1000, left=izq, color=COLOR_TIPO[t], label=NOMBRE_TIPO[t])
        izq = izq + e[t] / 1000
    ax.set_xlabel("MWh al año"); ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="lower right"); ax.grid(axis="x", alpha=.3)
    fig.tight_layout(); fig.savefig(ruta, dpi=200); plt.close(fig)


# ------------------------------------------------------------------------- Word
def sombrear(celda, color):
    tc = celda._tc.get_or_add_tcPr()
    s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto")
    s.set(qn("w:fill"), color); tc.append(s)


def tabla(doc, encabezado, filas, anchos=None, tam=8.5):
    t = doc.add_table(rows=1, cols=len(encabezado))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c, txt in zip(t.rows[0].cells, encabezado):
        c.text = ""; r = c.paragraphs[0].add_run(str(txt)); r.bold = True
        r.font.size = Pt(tam); r.font.color.rgb = RGBColor(255, 255, 255); sombrear(c, "21213D")
    for fila in filas:
        cs = t.add_row().cells
        for c, txt in zip(cs, fila):
            c.text = ""; r = c.paragraphs[0].add_run(str(txt)); r.font.size = Pt(tam)
    if anchos:
        for fila in t.rows:
            for c, a in zip(fila.cells, anchos):
                c.width = Cm(a)
    doc.add_paragraph()
    return t


def parrafo(doc, texto, negrita_inicio=None):
    p = doc.add_paragraph()
    if negrita_inicio:
        p.add_run(negrita_inicio).bold = True
    p.add_run(texto)
    return p


def vinetas(doc, items):
    for it in items:
        if isinstance(it, tuple):
            p = doc.add_paragraph(style="List Bullet"); p.add_run(it[0]).bold = True
            p.add_run(it[1])
        else:
            doc.add_paragraph(it, style="List Bullet")


def main():
    par = pd.read_excel(INS, sheet_name="parametros")
    ve = pd.read_excel(INS, sheet_name="ve_por_zona")
    hora = pd.read_excel(INS, sheet_name="hora_salida")
    dur = pd.read_excel(INS, sheet_name="duracion_viaje")
    zon = pd.read_excel(ZONAS_XLSX, sheet_name="zonas")
    ez = pd.read_excel(RES, sheet_name="energia_por_zona", index_col=0)
    valle = pd.read_excel(RES, sheet_name="valle_por_hora", index_col=0)
    flota = pd.read_csv(RESULTADOS / "vehiculos_simulados.csv")
    figura_flujo(FIGS / "fig_flujo.png")
    figura_ciudad(valle, FIGS / "fig_valle.png")
    figura_zonas(ez.drop(index="TOTAL"), FIGS / "fig_zonas.png")
    tot = ez.loc["TOTAL"]
    n_ve = ve.vehiculos.sum()
    con_garaje = (flota.peso * flota.garaje).sum() / flota.peso.sum()

    doc = Document()
    st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11)
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.2); s.top_margin = s.bottom_margin = Cm(2)

    doc.add_heading("Algoritmo de perfiles de carga de vehículos eléctricos por zona", 0)
    parrafo(doc, "Documentación de la versión sencilla del algoritmo, con sus insumos, su "
            "proceso y sus resultados, aplicada a un caso de estudio ficticio en el Valle de "
            "Aburrá. Este documento se puede editar.")
    parrafo(doc, "El algoritmo «maneja» cada carro eléctrico, viaje por viaje, durante un año "
            "entero, y anota cada vez que tiene que cargar: cuánta energía, a qué hora, en qué "
            "zona y en qué tipo de cargador. Al final entrega la potencia (kW) que pide cada "
            "zona, hora por hora, en cargadores rápidos, lentos y residenciales.", "Qué hace. ")
    parrafo(doc, "Es la Etapa 2 (simulación de viajes) de Mejia et al. (2025), Applied "
            "Energy, 395, 126160, y de la tesis doctoral de Mejía Alzate (UNESP), sección "
            "4.2.1. Esta versión conserva su lógica de decisión y quita lo que no se necesita "
            "para obtener la matriz de potencia (el agrupamiento con k-means).", "De dónde sale. ")
    parrafo(doc, "Es un modelo de estudio, no una medición. La encuesta de viajes es del Valle "
            "de Aburrá, así que el caso se arma ahí: el Valle se divide en 7 zonas inventadas, "
            "cada una con el tipo de vivienda que da el DANE para los municipios que cubre, y "
            "los 3.001 VE proyectados para las comunas de Pereira se asignan al azar a esas "
            "zonas.", "Caso de estudio ficticio. ")

    doc.add_heading("Archivos de la carpeta", 2)
    tabla(doc, ["Archivo", "Qué es"], [
        ["CORRER_ALGORITMO.bat", "Doble clic para correr el algoritmo"],
        ["algoritmo.py", "El algoritmo, en un solo archivo, comentado paso a paso"],
        ["insumos/insumos_algoritmo.xlsx", "TODOS los insumos, con su fuente. Es lo único que se edita"],
        ["insumos/zonas_ficticias.xlsx y mapa_zonas_ficticias.png", "Las 7 zonas inventadas: mapa, "
         "tipo de vivienda y VE asignados"],
        ["insumos/tipo_vivienda_DANE_CNPV2018.xlsx", "Casas y apartamentos por municipio (DANE)"],
        ["insumos/matriz_od_zonas.xlsx", "Matriz origen-destino de la EOD 2025 pasada a las 7 zonas"],
        ["insumos/mapa_carros_por_zona.png", "Qué carros le tocaron a cada zona"],
        ["insumos/crear_zonas_ficticias.py, extraer_tipo_vivienda_dane.py", "Rehacen las zonas y "
         "el dato del DANE"],
        ["insumos/fuentes/", "Copias de las fuentes originales (EOD 2025 y su API, DANE, DIVIPOLA, límites)"],
        ["resultados/", "Todo lo que entrega el algoritmo (ver sección 3)"],
        ["Documentacion_algoritmo.docx", "Este documento"],
    ], [7, 9.5])

    # ---------------------------------------------------------------- 1
    doc.add_heading("1. Inputs e insumos", 1)
    parrafo(doc, "Todos los insumos que lee el algoritmo están en un solo archivo, "
            "insumos/insumos_algoritmo.xlsx, con cinco hojas.")
    doc.add_heading("1.1 Parámetros (hoja «parametros»)", 2)
    tabla(doc, ["Parámetro", "Valor", "Unidad", "Qué es", "Fuente"],
          [[r.parametro, str(r.valor).replace(".", ",") if not isinstance(r.valor, str) else r.valor,
            r.unidad, r.descripcion, r.fuente] for r in par.itertuples()],
          [3.3, 1.7, 1.5, 4.6, 5.6], tam=7.5)
    doc.add_heading("1.2 Las 7 zonas ficticias (hoja «ve_por_zona»)", 2)
    doc.add_picture(str(GRAFICAS / "mapa_zonas_ficticias.png"), width=Cm(12.5))
    parrafo(doc, "Cómo se hicieron: se lanzaron 5.000 puntos al azar dentro de los 10 municipios "
            "del Valle de Aburrá (límites de OpenStreetMap), se agruparon en 7 con k-means y cada "
            "zona es el área más cercana al centro de su grupo (polígonos de Voronoi). Están "
            "numeradas de norte a sur.")
    tabla(doc, ["Zona", "Color", "Municipios que cubre", "% apartamentos (DANE)", "VE", "Comunas de Pereira asignadas"],
          [[r.zona, r.color, r.municipios_que_cubre, miles(r._7, 1), miles(r.vehiculos, 0),
            r.comunas_pereira_asignadas] for r in zon.itertuples()],
          [1.5, 2, 4.6, 1.8, 1.3, 5.3], tam=7.5)
    parrafo(doc, "% apartamentos: mezcla de los municipios que cubre la zona, con el tipo de "
            "vivienda del DANE (Censo 2018), suponiendo que las viviendas de cada municipio se "
            "reparten parejo en su área. Ese porcentaje es la probabilidad de que un VE de la zona "
            "tenga garaje (supuesto: el apartamento tiene parqueadero donde cargar).")
    doc.add_picture(str(GRAFICAS / "mapa_carros_por_zona.png"), width=Cm(16))
    doc.add_heading("1.3 Matriz origen-destino entre zonas (hoja «matriz_od»)", 2)
    od = pd.read_excel(INS, sheet_name="matriz_od", index_col=0)
    parrafo(doc, "Viajes en un día hábil entre zonas (filas = origen, columnas = destino). Sale "
            "de la API pública del tablero de la EOD 2025 (indicador 15: matriz entre las 67 "
            "macrozonas de la encuesta, todos los modos); cada macrozona se asignó a la zona donde "
            "cae su punto central (insumos/matriz_od_zonas.xlsx). El algoritmo sortea el destino "
            "de cada viaje con la fila de la zona donde está el carro.")
    tabla(doc, ["Origen \ destino", *[c.replace("Zona ", "Z") for c in od.columns]],
          [[i, *[miles(v) for v in r.values]] for i, r in od.iterrows()],
          [2.2] + [2] * len(od.columns), tam=7.5)
    doc.add_heading("1.4 Hora de salida de los viajes (hoja «hora_salida»)", 2)
    parrafo(doc, "Número de viajes en transporte privado que empiezan en cada hora del día, de "
            "la EOD 2025. El algoritmo usa la forma de la distribución, no el total: las horas "
            "con más viajes se sortean más veces.")
    h = hora.sort_values("viajes", ascending=False).head(4)
    parrafo(doc, "Horas con más salidas: " + "; ".join(f"{int(r.hora)}:00 ({miles(r.viajes)} viajes)"
                                                       for r in h.itertuples()) + ".")
    doc.add_heading("1.5 Duración de los viajes (hoja «duracion_viaje»)", 2)
    tabla(doc, ["Desde (min)", "Hasta (min)", "% de viajes"],
          [[int(r.desde_min), int(r.hasta_min), miles(r.porcentaje, 2)] for r in dur.itertuples()],
          [3, 3, 3])
    doc.add_heading("1.6 Supuestos (decisiones propias, no de una fuente)", 2)
    vinetas(doc, [
        ("Zonas: ", "inventadas al azar; no son comunas reales."),
        ("VE por zona: ", "las 19 comunas de Pereira (3.001 VE de 2030, Objetivo 2) se asignan al "
         "azar a las 7 zonas; cada zona recibe al menos una."),
        ("Número de viajes: ", "con un promedio de 2,34, el 66 % de los días tiene 2 viajes y el "
         "34 % tiene 3. La encuesta solo publica el promedio."),
        ("Kilómetros: ", "duración × velocidad urbana. La EOD 2025 no publica distancias."),
        ("Destino: ", "el último viaje del día vuelve a casa; los demás van a una zona sorteada "
         "con la matriz origen-destino de la encuesta (todos los modos)."),
        ("Garaje: ", "apartamento = tiene parqueadero donde cargar; casa u otro = no."),
        ("Año: ", "todos los días se tratan como el día hábil que describe la encuesta."),
        ("Duración de la encuesta: ", "mezcla todos los modos de transporte (el tablero no la "
         "separa); el rango «120 o más» se toma como 120 a 150 minutos."),
        ("Muestra: ", "se simula una fracción de los VE (escala 0,1, unos 300) y cada uno "
         "representa a unos 10. Ver la advertencia de la sección 3.4."),
    ])

    # ---------------------------------------------------------------- 2
    doc.add_heading("2. Proceso del algoritmo", 1)
    parrafo(doc, "El algoritmo tiene cinco pasos. Cada uno es una función de algoritmo.py con "
            "el mismo nombre.")
    doc.add_picture(str(FIGS / "fig_flujo.png"), width=Cm(13.5))
    tabla(doc, ["Paso", "Función", "Qué hace"], [
        ["0", "leer_insumos", "Lee las cinco hojas del Excel de insumos."],
        ["1", "crear_flota", "Crea los VE de cada zona. A cada uno le asigna al azar una batería "
         "(24, 35 o 50 kWh), una carga inicial (50 a 100 %), si tiene garaje (con la probabilidad "
         "del % de casas de su zona) y un peso: cuántos VE reales representa."],
        ["2", "generar_viajes", "Para cada VE y cada uno de los 365 días sortea: cuántos viajes hace, "
         "a qué hora sale, cuánto dura cada viaje y a qué zona va. Un viaje no empieza antes de "
         "terminar el anterior."],
        ["3", "simular", "Recorre los viajes en orden. En cada uno gasta batería (consumo × km). Al "
         "llegar, si la batería quedó por debajo del 30 %, decide el cargador con las tres "
         "condiciones y anota la energía hora por hora en la zona de destino. La batería pasa "
         "de un día al siguiente."],
        ["4", "armar_resultados / guardar", "Suma la energía de todos los VE y escribe el Excel, "
         "la matriz, el data frame y los perfiles de 8.760 horas."],
    ], [1.2, 3.6, 11.5])
    doc.add_heading("2.1 Cómo se decide el tipo de cargador", 2)
    vinetas(doc, [
        ("Condición 1, carga rápida: ", "la batería se agotó, o el próximo viaje sale en menos de "
         "1 hora (no hay tiempo de una carga lenta). Dura entre 10 y 60 minutos, al azar, o hasta "
         "llegar al 90 %."),
        ("Condición 2, carga residencial: ", "el viaje terminó en la casa y la casa tiene garaje. "
         "Carga hasta el 90 % o hasta que sale el próximo viaje."),
        ("Condición 3, carga lenta pública: ", "cualquier otro caso, incluida la casa sin garaje. "
         "Carga hasta el 90 % o hasta que sale el próximo viaje."),
    ])
    doc.add_heading("2.2 Por qué se sortea y no se usa el promedio", 2)
    parrafo(doc, "Si todos los carros usaran el promedio, saldrían a la misma hora, harían el "
            "mismo viaje y cargarían al mismo tiempo, y el pico de potencia saldría falso. Al "
            "sortear cada dato de la distribución de la encuesta, cada carro hace algo distinto "
            "cada día, pero el conjunto reproduce lo que dice la encuesta (simulación de Monte "
            "Carlo). La semilla fija el azar: con la misma semilla e insumos sale el mismo "
            "resultado.")
    doc.add_heading("2.3 Qué se quitó frente a las fuentes", 2)
    vinetas(doc, [
        "El agrupamiento con k-means de los perfiles: no hace falta para la matriz de potencia.",
        "La revisión de la batería cada 5 minutos dentro del viaje: aquí se revisa al llegar.",
        "La zona de carga al azar entre la propia y las vecinas (tesis): aquí se carga en la "
        "zona donde termina el viaje, como en el artículo.",
    ])

    # ---------------------------------------------------------------- 3
    doc.add_heading("3. Resultado", 1)
    parrafo(doc, "El resultado es por zona: las 7 zonas, cada hora del día, para cada tipo de "
            "cargador. Todo queda en la carpeta resultados/.")
    tabla(doc, ["Archivo", "Qué trae"], [
        ["resultado_algoritmo.xlsx", "Hojas: energia_por_zona, valle_por_hora, resumen_zona, "
         "matriz y dataframe"],
        ["matriz_potencia_zona_hora.csv", "LA MATRIZ: una fila por tipo de cargador y zona; una "
         "columna por hora (00h a 23h); kW del día promedio"],
        ["dataframe_resultados.csv", "EL DATA FRAME: formato largo, una fila por zona, tipo y hora "
         "(columnas zona, tipo, hora, potencia_kw)"],
        ["perfiles_8760_horas.csv", "Las 8.760 horas del año, una columna por zona|tipo"],
        ["vehiculos_simulados.csv", "Los VE simulados: zona, peso, batería, carga inicial, garaje"],
        ["viajes_simulados.csv", "Todos los viajes sorteados (hora, duración, km, destino)"],
    ], [5.5, 11])
    doc.add_heading("3.1 Por zona", 2)
    doc.add_picture(str(FIGS / "fig_zonas.png"), width=Cm(14))
    tabla(doc, ["Zona", "Rápida", "Lenta", "Residencial", "Total"],
          [[z, *[miles(r[t] / 1000, 1) for t in ["rapida", "lenta", "residencial", "total_kWh"]]]
           for z, r in ez.iterrows()], [3, 2.8, 2.8, 2.8, 2.8], tam=8.5)
    parrafo(doc, "Valores en MWh al año. La matriz por hora de cada zona está en "
            "matriz_potencia_zona_hora.csv y en la hoja «matriz» del Excel.")
    doc.add_heading("3.2 Todo el Valle", 2)
    doc.add_picture(str(FIGS / "fig_valle.png"), width=Cm(14))
    filas = []
    for t in ["rapida", "lenta", "residencial"]:
        s = valle.loc[t]
        filas.append([NOMBRE_TIPO[t], miles(tot[t] / 1000), f"{miles(s.max())} kW a las "
                      f"{int(s.values.argmax())}:00"])
    tabla(doc, ["Tipo de cargador", "MWh al año", "Hora más alta del día promedio"], filas,
          [4.5, 3, 6])
    parrafo(doc, f"En total, {miles(tot['total_kWh'] / 1000)} MWh al año, unos "
            f"{miles(tot['total_kWh'] / n_ve / 365, 1)} kWh por VE al día. El "
            f"{miles(100 * con_garaje, 1)} % de los VE simulados tiene garaje.")
    doc.add_heading("3.3 Cómo leer la matriz", 2)
    parrafo(doc, "Cada celda es la potencia promedio (kW) que pide esa zona, a esa hora, en ese "
            "tipo de cargador, en un día promedio del año. Como cada valor es la energía cargada "
            "en una hora, kW y kWh por hora son el mismo número.")
    doc.add_heading("3.4 Advertencias", 2)
    vinetas(doc, [
        ("Caso ficticio: ", "las zonas y la asignación de VE son inventadas; el resultado sirve "
         "para estudiar el algoritmo, no para ubicar cargadores reales."),
        ("Pico por zona: ", "con escala 0,1 cada VE simulado representa a unos 10, así que una "
         "sola carga rápida simulada aparece como 10 cargas al mismo tiempo. Por eso la columna "
         "potencia_pico_kW de resumen_zona exagera el pico. La matriz del día promedio no tiene "
         "ese problema. Para picos más finos, ponga escala = 1 en los insumos (tarda unas 10 "
         "veces más)."),
        ("Matriz origen-destino: ", "es de todos los modos (la API no la separa por modo) y se "
         "pasa a las zonas por el punto central de cada macrozona."),
        ("Garaje: ", "el censo dice casa o apartamento, no si hay garaje; apartamento = garaje es "
         "un supuesto de este estudio (el artículo usa lo contrario: casa = garaje)."),
    ])

    # ---------------------------------------------------------------- 3.5 todas las matrices
    resu = pd.read_excel(RES, sheet_name="resumen_zona")
    doc.add_heading("3.5 Resumen por zona y tipo de cargador", 2)
    tabla(doc, ["Zona", "Tipo", "Energía al año (kWh)", "Potencia promedio (kW)",
                "Potencia pico (kW)", "Hora más alta del día promedio"],
          [[r.zona, NOMBRE_TIPO[r.tipo], miles(r.energia_anual_kWh), miles(r.potencia_promedio_kW, 1),
            miles(r.potencia_pico_kW, 1), f"{int(r.hora_pico_dia_promedio)}:00"]
           for r in resu.sort_values(["zona", "tipo"]).itertuples()],
          [2, 3, 3, 3, 2.6, 3], tam=8)
    # Las matrices de 24 horas van en páginas horizontales para que quepan.
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = sec.page_height, sec.page_width
    sec.left_margin = sec.right_margin = Cm(1.2)
    mat = pd.read_csv(RESULTADOS / "matriz_potencia_zona_hora.csv")
    horas = [c for c in mat.columns if c.endswith("h")]
    doc.add_heading("3.6 Matrices completas: potencia por zona y hora (kW, día promedio)", 2)
    parrafo(doc, "Cada celda es la potencia promedio que pide la zona a esa hora en ese tipo de "
            "cargador, promediando los 365 días del año. Son las 7 zonas y las 24 horas. Los mismos "
            "datos están en resultados/matriz_potencia_zona_hora.csv y en la hoja «matriz» del Excel.")
    for t in ["rapida", "lenta", "residencial"]:
        doc.add_heading(f"Carga {NOMBRE_TIPO[t].lower()}", 3)
        m = mat[mat.tipo == t]
        filas = [[r["zona"].replace("Zona ", "Z"), *[miles(r[h]) for h in horas]] for _, r in m.iterrows()]
        filas.append(["Total", *[miles(m[h].sum()) for h in horas]])
        tabla(doc, ["Zona", *[h.replace("h", "") for h in horas]], filas,
              [1.2] + [1.05] * 24, tam=6.5)
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    sec.orientation = WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = sec.page_height, sec.page_width
    sec.left_margin = sec.right_margin = Cm(2.2)

    # ---------------------------------------------------------------- 4
    doc.add_heading("4. Cómo correrlo de nuevo si cambian los insumos", 1)
    vinetas(doc, [
        "Abra insumos/insumos_algoritmo.xlsx, cambie los valores (y su fuente), guarde y cierre.",
        "Cierre también resultados/resultado_algoritmo.xlsx si está abierto.",
        "Haga doble clic en CORRER_ALGORITMO.bat. Tarda unos 2 minutos con escala 0,1. Al "
        "terminar se abre la carpeta de resultados.",
        "Para otras zonas al azar: cambie SEMILLA en insumos/crear_zonas_ficticias.py, córralo y "
        "copie la hoja «zonas» a ve_por_zona.",
        "Para actualizar este Word con los resultados nuevos: python "
        "documentacion/crear_documentacion.py (con el Word cerrado).",
    ])
    doc.save(SALIDA)
    print("ok", SALIDA)


if __name__ == "__main__":
    main()
