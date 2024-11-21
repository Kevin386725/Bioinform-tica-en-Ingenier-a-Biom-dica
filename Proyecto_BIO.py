import streamlit as st
import pandas as pd
import altair as alt
from biopandas.pdb import PandasPdb
import plotly.express as px
import py3Dmol
import requests
import tempfile
import os

# Configuración de la página
st.set_page_config(page_title="Bioinformática en Ingeniería Biomédica", 
                   page_icon=":microscope:", layout="wide")

# Título de la app en Streamlit
st.title("Bioinformática en Ingeniería Biomédica")
st.markdown("""
Bienvenido a la aplicación de *Bioinformática* utilizando la biblioteca *Biopython*. 
Explora diferentes secciones de los archivos PDB y visualiza sus datos de manera interactiva.

Aprovecha esta herramienta para obtener información y visualizaciones sobre estructuras biomoleculares.
""")

# Barra lateral para navegación
st.sidebar.title("Navegación")

# Caja de texto para ingresar el código de la proteína (PDB ID)
pdb_code = st.sidebar.text_input("Ingresa el código de la proteína (PDB ID):", )  # Valor por defecto "1ijg"

# Función para obtener el archivo PDB desde la URL de RCSB
def obtener_pdb(pdb_code):
    url = f"https://files.rcsb.org/download/{pdb_code}.pdb"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.text
    else:
        st.sidebar.error(f" {pdb_code}")
        return None

# Intentar obtener el archivo PDB basado en el código ingresado
pdb_data = obtener_pdb(pdb_code)

# Función para guardar el archivo PDB en un archivo temporal
def guardar_pdb_temporal(pdb_data):
    # Crear un archivo temporal
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdb')
    with open(temp_file.name, 'w') as f:
        f.write(pdb_data)
    return temp_file.name

# Procesar el archivo PDB si se descargó correctamente
if pdb_data:
    # Guardar el archivo PDB en un archivo temporal
    pdb_file_path = guardar_pdb_temporal(pdb_data)
    
    # Leer el archivo PDB usando PandasPdb
    ppdb = PandasPdb().read_pdb(pdb_file_path)
    st.sidebar.success(f"Archivo PDB cargado correctamente: {pdb_code}")
else:
    ppdb = None

# Función para mostrar las secciones del archivo PDB
def datos_pdb():
    if ppdb is not None:
        # Mejoras visuales en la sección de información general
        st.markdown("---")
        st.subheader("Secciones del archivo PDB")
        st.markdown("Explora las diferentes secciones del archivo PDB:")

        for section, df in ppdb.df.items():
            st.write(f"### {section}")
            st.dataframe(df.head(), width=800)  # Estilo de tabla interactiva con un ancho adecuado

        # Información sobre los diferentes tipos de datos en el PDB
        st.markdown("#### Información sobre las dimensiones de las secciones del archivo PDB:")
        df_hetatm = ppdb.df["HETATM"].shape
        df_anistropic = ppdb.df["ANISOU"].shape
        df_others = ppdb.df["OTHERS"].shape
        st.write(f"Tamaño de HETATM: {df_hetatm}")
        st.write(f"Tamaño de ANISOU: {df_anistropic}")
        st.write(f"Tamaño de OTHERS: {df_others}")

        # Mostrar información sobre la sección "ATOM"
        st.markdown("---")
        df_atom = ppdb.df["ATOM"]
        st.subheader("Datos ATOM")
        st.write(f"Tamaño del DataFrame ATOM: {df_atom.shape}")
        st.write("Primeras filas de la sección ATOM:")
        st.dataframe(df_atom.head(), width=800)
    else:
        st.warning("")

# Función para la sección "Visualización 3D con Plotly"
def visualizacion_3d_plotly():
    if ppdb is not None:
        # Visualización 3D de las coordenadas atómicas con Plotly
        st.markdown("---")
        st.subheader("Visualización 3D de las coordenadas atómicas (Plotly)")
        df_atom = ppdb.df["ATOM"]
        fig = px.scatter_3d(df_atom, x="x_coord", y="y_coord", z="z_coord", color="element_symbol", 
                            template="plotly_dark", color_discrete_sequence=["white", "gray", "red", "yellow"])
        fig.update_coloraxes(showscale=True)
        fig.update_traces(marker=dict(size=3))
        st.plotly_chart(fig, use_container_width=True)

        # Visualización 3D de las coordenadas atómicas coloreadas por el nombre del residuo
        st.markdown("---")
        st.subheader("Visualización 3D por Nombre de Residuo (Plotly)")
        fig = px.scatter_3d(df_atom, x="x_coord", y="y_coord", z="z_coord", color="residue_name", template="plotly_dark")
        fig.update_traces(marker=dict(size=3))
        fig.update_coloraxes(showscale=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("")

# Función para la sección "Visualización 3D con Altair"
def visualizacion_3d_altair():
    if ppdb is not None:
        # Extraer las coordenadas atómicas (x, y, z) y otros datos
        df_atom = ppdb.df["ATOM"]
        df = df_atom[['x_coord', 'y_coord', 'z_coord', 'element_symbol']].copy()
        df['size'] = df['z_coord']  # Utilizamos la coordenada z como tamaño de los puntos (esto es opcional)
        df['color'] = df['z_coord']  # Utilizamos la coordenada z como color (esto es opcional)

        # Crear el gráfico de dispersión 2D con Altair
        st.markdown("---")
        st.subheader("Visualización 3D de las coordenadas atómicas (Altair)")
        c = alt.Chart(df).mark_circle().encode(
            x='x_coord',
            y='y_coord',
            size='size',
            color='color',
            tooltip=['x_coord', 'y_coord', 'z_coord', 'element_symbol']
        )
        st.altair_chart(c, use_container_width=True)
    else:
        st.warning("")

# Función para la sección "Visualización 3D de Proteína (py3Dmol)"
def visualizacion_3d_proteina():
    if ppdb is not None:
        # Crear una visualización 3D con py3Dmol
        viewer = py3Dmol.view(width=800, height=600)
        viewer.addModel(pdb_data, "pdb")  # Cargar el modelo PDB
        viewer.setStyle({'stick': {}})  # Estilo de visualización (esqueleto de varillas)
        viewer.setBackgroundColor("white")  # Fondo blanco
        viewer.zoomTo()  # Ajuste para ver toda la proteína

        # Convertir la visualización a HTML
        viewer_html = viewer._make_html()

        # Mostrar el HTML en Streamlit usando st.components.v1.html
        st.components.v1.html(viewer_html, height=600)
    else:
        st.warning("")

# Mostrar el contenido en la misma pestaña
st.markdown("---")
st.markdown("### Análisis y Visualización de la proteína")

# Llamar a las funciones para mostrar los datos y visualizaciones
datos_pdb()
visualizacion_3d_plotly()
visualizacion_3d_altair()
visualizacion_3d_proteina()

# Pie de página con información adicional
st.markdown("---")
st.markdown("""
### Información adicional:
Si tienes alguna duda sobre el uso de esta herramienta, no dudes en contactarnos. 
Este proyecto es parte de una investigación sobre Bioinformática aplicada a Ingeniería Biomédica.

#### Créditos:
* Datos obtenidos de la base de datos PDB.
* Visualización realizada con Plotly, Altair, py3Dmol y Streamlit.
""")
