
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats

# --------------------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------------------

st.set_page_config(
    page_title="Dashboard de actividad sísmica",
    page_icon="🌎",
    layout="wide"
)

st.title("🌎 Dashboard interactivo de actividad sísmica")
st.markdown(
    """
    **Análisis de terremotos registrados entre 1965 y 2016.**

    Este dashboard permite explorar los registros sísmicos,
    analizar la magnitud y profundidad de los eventos e
    identificar tendencias a través del tiempo.
    """
)

# --------------------------------------------------
# CARGA DE DATOS
# --------------------------------------------------

archivo = Path(__file__).parent / "Significant Earthquakes 1965–2016.csv"

@st.cache_data
def cargar_datos(ruta):
    datos = pd.read_csv(ruta)

        # Validar las columnas necesarias
    columnas_requeridas = [
        "Magnitude",
        "Depth",
        "Date",
        "Type"
    ]

    columnas_faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in datos.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas necesarias en el CSV: "
            + ", ".join(columnas_faltantes)
        )

    datos["Magnitude"] = pd.to_numeric(
        datos["Magnitude"], errors="coerce"
    )

    datos["Depth"] = pd.to_numeric(
        datos["Depth"], errors="coerce"
    )

    datos["Date"] = pd.to_datetime(
        datos["Date"], errors="coerce"
    )

    datos["Year"] = datos["Date"].dt.year
    
        # Validar que existan fechas válidas
    if datos["Date"].notna().sum() == 0:
        raise ValueError(
            "No existen fechas válidas en la columna Date."
        )

        # Validar que existan magnitudes numéricas válidas
    if datos["Magnitude"].notna().sum() == 0:
        raise ValueError(
            "No existen valores numéricos válidos en la columna Magnitude."
        )
        # Validar que existan profundidades numéricas válidas
    if datos["Depth"].notna().sum() == 0:
        raise ValueError(
            "No existen valores numéricos válidos en la columna Depth."
        )

    return datos

try:
    df = cargar_datos(archivo)
except FileNotFoundError:
    st.error(
        "No se encontró el archivo CSV. "
        "Verifica que esté en la misma carpeta que app.py."
    )
    st.stop()
except Exception as error:
    st.error(f"No fue posible cargar los datos: {error}")
    st.stop()

# --------------------------------------------------
# FILTROS LATERALES
# --------------------------------------------------

st.sidebar.header("Filtros del dashboard")

tipos = sorted(df["Type"].dropna().unique().tolist())

tipos_seleccionados = st.sidebar.multiselect(
    "Selecciona el tipo de evento:",
    options=tipos,
    default=tipos
)

magnitud_minima = float(df["Magnitude"].min())
magnitud_maxima = float(df["Magnitude"].max())

rango_magnitud = st.sidebar.slider(
    "Rango de magnitud:",
    min_value=magnitud_minima,
    max_value=magnitud_maxima,
    value=(magnitud_minima, magnitud_maxima),
    step=0.1
)

# --------------------------------------------------
# APLICACIÓN DE FILTROS
# --------------------------------------------------

filtrado = df[
    (df["Type"].isin(tipos_seleccionados))
    & (df["Magnitude"] >= rango_magnitud[0])
    & (df["Magnitude"] <= rango_magnitud[1])
].copy()

if filtrado.empty:
    st.warning("No hay registros para los filtros seleccionados.")
    st.stop()

# --------------------------------------------------
# INDICADORES PRINCIPALES
# --------------------------------------------------

st.header("Indicadores generales")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Registros encontrados",
    f"{len(filtrado):,}"
)

col2.metric(
    "Magnitud promedio",
    f"{filtrado['Magnitude'].mean():.2f}"
)

col3.metric(
    "Desviación estándar",
    f"{filtrado['Magnitude'].std():.2f}"
)

col4.metric(
    "Profundidad promedio",
    f"{filtrado['Depth'].mean():.2f} km"
)

st.divider()

# --------------------------------------------------
# TABLA DE DATOS
# --------------------------------------------------

st.header("Datos filtrados")

st.dataframe(
    filtrado,
    use_container_width=True
)

# --------------------------------------------------
# VISUALIZACIÓN 1: TIPO DE EVENTO
# --------------------------------------------------

st.header("1. Distribución de eventos por tipo")

conteo_tipos = (
    filtrado["Type"]
    .value_counts()
    .rename_axis("Tipo de evento")
    .reset_index(name="Cantidad")
)

fig_tipos = px.bar(
    conteo_tipos,
    x="Tipo de evento",
    y="Cantidad",
    color="Tipo de evento",
    title="Cantidad de registros según el tipo de evento",
    labels={
        "Tipo de evento": "Tipo de evento",
        "Cantidad": "Número de registros"
    }
)

st.plotly_chart(fig_tipos, use_container_width=True)

# --------------------------------------------------
# VISUALIZACIÓN 2: DISTRIBUCIÓN DE MAGNITUD
# --------------------------------------------------

st.header("2. Distribución de la magnitud")

fig_magnitud = px.histogram(
    filtrado,
    x="Magnitude",
    nbins=30,
    title="Frecuencia de los registros según su magnitud",
    labels={
        "Magnitude": "Magnitud",
        "count": "Número de registros"
    }
)

st.plotly_chart(fig_magnitud, use_container_width=True)

# --------------------------------------------------
# VISUALIZACIÓN 3: PROFUNDIDAD Y MAGNITUD
# --------------------------------------------------

st.header("3. Relación entre profundidad y magnitud")

datos_scatter = filtrado.dropna(
    subset=["Depth", "Magnitude"]
)

fig_relacion = px.scatter(
    datos_scatter,
    x="Depth",
    y="Magnitude",
    color="Type",
    title="Magnitud registrada según la profundidad del evento",
    labels={
        "Depth": "Profundidad (km)",
        "Magnitude": "Magnitud",
        "Type": "Tipo de evento"
    },
    opacity=0.6
)

st.plotly_chart(fig_relacion, use_container_width=True)

# --------------------------------------------------
# VISUALIZACIÓN 4: TENDENCIA ANUAL
# --------------------------------------------------

st.header("4. Evolución de los registros por año")

datos_anuales = (
    filtrado.dropna(subset=["Year"])
    .groupby("Year")
    .size()
    .reset_index(name="Cantidad de registros")
)

fig_anual = px.line(
    datos_anuales,
    x="Year",
    y="Cantidad de registros",
    markers=True,
    title="Cantidad de eventos registrados por año",
    labels={
        "Year": "Año",
        "Cantidad de registros": "Número de registros"
    }
)

st.plotly_chart(fig_anual, use_container_width=True)

# --------------------------------------------------
# VALIDACIÓN ESTADÍSTICA: PRUEBA T DE WELCH
# --------------------------------------------------

st.header("5. Validación estadística")

st.subheader(
    "Comparación de magnitud: terremotos y explosiones nucleares"
)

grupo1 = df.loc[
    df["Type"] == "Earthquake", "Magnitude"
].dropna()

grupo2 = df.loc[
    df["Type"] == "Nuclear Explosion", "Magnitude"
].dropna()

if len(grupo1) >= 2 and len(grupo2) >= 2:
    resultado = stats.ttest_ind(
        grupo1,
        grupo2,
        equal_var=False
    )
    st.write(f"Estadístico t: **{resultado.statistic:.4f}**")
    st.write(f"Valor p: **{resultado.pvalue:.4f}**")
    st.write("Nivel de significancia: **0.05**")

    if resultado.pvalue < 0.05:
        st.success(
            "Se encuentra evidencia estadística de una diferencia "
            "entre las magnitudes promedio de los dos grupos."
        )
    else:
        st.info(
            "No se encuentra evidencia estadística suficiente "
            "para afirmar que las magnitudes promedio de los dos "
            "grupos sean diferentes."
        )
else:
    st.warning(
        "Se necesitan al menos dos registros válidos de cada grupo "
        "para realizar la prueba estadística."
    )

st.caption(
    "La prueba compara los promedios de dos grupos independientes. "
    "Un resultado estadístico no demuestra por sí solo una relación causal."
)

# --------------------------------------------------
# HALLAZGOS
# --------------------------------------------------

st.header("6. Hallazgos principales")

st.markdown(
    """
    - El conjunto de datos permite identificar diferentes tipos de
      eventos sísmicos registrados entre 1965 y 2016.
    - La magnitud presenta variaciones entre los eventos analizados.
    - La profundidad y la magnitud permiten explorar el comportamiento
      de los registros, sin asumir que una variable causa la otra.
    - La cantidad de registros cambia entre años. Estas variaciones
      también pueden estar relacionadas con la cobertura y los métodos
      de registro del catálogo.
    """
)

st.info(
    "Los resultados y gráficos se actualizan automáticamente "
    "cuando se modifican los filtros."
)

st.caption("Fuente: Significant Earthquakes 1965–2016.")
