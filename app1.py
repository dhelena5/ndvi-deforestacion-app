import ee
import streamlit as st
import geemap.foliumap as geemap
import folium
import json

# Autenticación con cuenta de servicio
service_account = 'streamlit-app@streamlit-ee-app.iam.gserviceaccount.com'
key_file = 'ee-key.json'

credentials = ee.ServiceAccountCredentials(service_account, key_file)
ee.Initialize(credentials)


st.title("🌳 Monitoreo de Deforestación con NDVI (Landsat 8)")
st.markdown("Comparación de NDVI entre dos años para detectar pérdida o ganancia de vegetación.")

# Región de interés (norte de Colombia)
roi = ee.Geometry.Rectangle([-74.7, 9.2, -74.3, 9.6])

# Función para obtener NDVI
def get_ndvi(year):
    start = ee.Date.fromYMD(year, 1, 1)
    end = ee.Date.fromYMD(year, 12, 31)
    image = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
             .filterDate(start, end)
             .filterBounds(roi)
             .filter(ee.Filter.lt('CLOUD_COVER', 20))
             .median())
    return image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI').clip(roi)

# UI: selección de años
col1, col2 = st.columns(2)
with col1:
    year1 = st.selectbox("📆 Año base", [2015, 2016, 2017, 2018, 2019, 2020], index=0)
with col2:
    year2 = st.selectbox("📆 Año actual", [2021, 2022, 2023], index=2)

# Calcular imágenes
ndvi1 = get_ndvi(year1)
ndvi2 = get_ndvi(year2)
ndvi_diff = ndvi2.subtract(ndvi1).rename("NDVI_Change")

# Parámetros visuales
ndvi_vis = {"min": 0, "max": 1, "palette": ['brown', 'yellow', 'green']}
diff_vis = {"min": -0.5, "max": 0.5, "palette": ['red', 'white', 'green']}

# Crear mapa
Map = geemap.Map(center=[9.4, -74.5], zoom=9)
Map.addLayer(ndvi1, ndvi_vis, f"NDVI {year1}")
Map.addLayer(ndvi2, ndvi_vis, f"NDVI {year2}")
Map.addLayer(ndvi_diff, diff_vis, f"Cambio NDVI {year1}→{year2}")
Map.addLayer(roi, {}, "Región")

# Determinar qué leyenda mostrar
if year1 != year2:
    # Si están comparando dos años distintos, mostrar leyenda de cambio
    legend_html = """
    <div style="
        position: fixed;
        bottom: 40px;
        left: 40px;
        background: rgba(255,255,255,0.8);
        padding: 8px;
        border: 1px solid gray;
        border-radius: 8px;
        font-size: 14px;
        z-index:9999;
    ">
    <b>Cambio NDVI</b><br>
    <div style="display: flex; align-items: center;">
      <div style="background:red;width:20px;height:20px;border:1px solid #555;"></div>
      <div style="margin-left:6px;">Perdida</div>
    </div>
    <div style="display: flex; align-items: center;">
      <div style="background:white;width:20px;height:20px;border:1px solid #555;"></div>
      <div style="margin-left:6px;">Sin cambio</div>
    </div>
    <div style="display: flex; align-items: center;">
      <div style="background:green;width:20px;height:20px;border:1px solid #555;"></div>
      <div style="margin-left:6px;">Ganancia</div>
    </div>
    </div>
    """
else:
    # Si el mismo año, mostrar leyenda NDVI simple
    legend_html = """
    <div style="
        position: fixed;
        bottom: 40px;
        left: 40px;
        background: rgba(255,255,255,0.8);
        padding: 8px;
        border: 1px solid gray;
        border-radius: 8px;
        font-size: 14px;
        z-index:9999;
    ">
    <b>NDVI</b><br>
    <div style="display: flex; align-items: center;">
      <div style="background:brown;width:20px;height:20px;border:1px solid #555;"></div>
      <div style="margin-left:6px;">Bajo</div>
    </div>
    <div style="display: flex; align-items: center;">
      <div style="background:yellow;width:20px;height:20px;border:1px solid #555;"></div>
      <div style="margin-left:6px;">Medio</div>
    </div>
    <div style="display: flex; align-items: center;">
      <div style="background:green;width:20px;height:20px;border:1px solid #555;"></div>
      <div style="margin-left:6px;">Alto</div>
    </div>
    </div>
    """

# Añadir leyenda dinámica
Map.get_root().html.add_child(folium.Element(legend_html))

# Mostrar mapa en Streamlit
with st.expander("🗺️ Ver Mapa Interactivo"):
    Map.to_streamlit(height=600)

# Exportar imagen a Google Drive
if st.button("📤 Exportar cambio NDVI a Drive"):
    task = ee.batch.Export.image.toDrive(
        image=ndvi_diff,
        description=f'NDVI_Diff_{year1}_to_{year2}',
        folder='EarthEngineExports',
        fileNamePrefix=f'NDVI_Diff_{year1}_to_{year2}',
        region=roi,
        scale=30,
        maxPixels=1e13
    )
    task.start()
    st.success(f"✅ Exportación iniciada a Google Drive (EarthEngineExports).")
