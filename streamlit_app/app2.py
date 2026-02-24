# ==========================================
# Imports
# ==========================================
import os

import geopandas as gpd
import osmnx as ox
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from shapely.geometry import Point

# ==========================================
# Configurações iniciais
# ==========================================
st.set_page_config(
    page_title="Geocoding + POIs",
    layout="centered"
)

load_dotenv()

GOOGLE_API_KEY = os.getenv("GEOCODING_MAPS")

if not GOOGLE_API_KEY:
    st.error("❌ Chave GEOCODING_MAPS não encontrada no .env")
    st.stop()

# ==========================================
# Funções — Google Geocoding
# ==========================================
def geocode_google(endereco):
    url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "address": endereco,
        "key": GOOGLE_API_KEY,
        "region": "br",
        "language": "pt-BR"
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    if data["status"] != "OK":
        return None

    result = data["results"][0]

    location = result["geometry"]["location"]
    location_type = result["geometry"]["location_type"]

    return {
        "lat": location["lat"],
        "lng": location["lng"],
        "endereco_formatado": result["formatted_address"],
        "precisao": location_type
    }

# ==========================================
# Funções — Geoespaciais
# ==========================================
def ponto_imovel(lat, lng):
    return gpd.GeoDataFrame(
        [{"id": 1}],
        geometry=[Point(lng, lat)],
        crs="EPSG:4326"
    )

def projetar_metrico(gdf):
    return gdf.to_crs(epsg=3857)

def distancia_minima(ponto_gdf, pois_gdf):
    if pois_gdf.empty:
        return None

    ponto_m = projetar_metrico(ponto_gdf)
    pois_m = projetar_metrico(pois_gdf)

    distancias = pois_m.geometry.distance(ponto_m.geometry.iloc[0])
    return round(distancias.min(), 2)

def contar_pois_raio(ponto_gdf, pois_gdf, raio_m=1000):
    if pois_gdf.empty:
        return 0

    ponto_m = projetar_metrico(ponto_gdf)
    pois_m = projetar_metrico(pois_gdf)

    buffer = ponto_m.geometry.iloc[0].buffer(raio_m)
    return int(pois_m.within(buffer).sum())

# ==========================================
# Cache — POIs (OSMnx)
# ==========================================
@st.cache_data(show_spinner="🔄 Carregando POIs da cidade...")
def carregar_pois(cidade):
    hospitais = ox.features_from_place(cidade, {"amenity": "hospital"})
    mercados = ox.features_from_place(cidade, {"shop": ["supermarket", "convenience"]})
    farmacias = ox.features_from_place(cidade, {"amenity": "pharmacy"})
    parques = ox.features_from_place(
        cidade,
        {"leisure": ["park", "garden"], "landuse": "recreation_ground"}
    )
    policia = ox.features_from_place(
        cidade,
        {"amenity": ["police", "fire_station", "courthouse"]}
    )
    escolas = ox.features_from_place(
        cidade,
        {"amenity": ["school", "college", "university"]}
    )

    # Normalizar geometrias
    escolas["geometry"] = escolas.geometry.apply(
        lambda g: g.centroid if g.geom_type != "Point" else g
    )

    return hospitais, mercados, farmacias, escolas, parques, policia

# ==========================================
# Interface
# ==========================================
st.title("📍 Geocoding + POIs (Google + OSMnx)")

endereco = st.text_input(
    "Endereço completo",
    placeholder="Rua Marechal Deodoro, 217, Guarapuava, PR"
)

cidade = "Guarapuava, Paraná, Brasil"

if st.button("Buscar localização"):
    with st.spinner("🔍 Consultando Google Maps..."):
        resultado = geocode_google(endereco)

    if not resultado:
        st.error("❌ Endereço não encontrado.")
        st.stop()

    # Persistência
    st.session_state["resultado"] = resultado

# ==========================================
# Resultado persistente
# ==========================================
if "resultado" in st.session_state:
    r = st.session_state["resultado"]

    st.success("✅ Endereço localizado com sucesso!")

    st.markdown("### 📌 Endereço retornado")
    st.write(r["endereco_formatado"])

    st.markdown("### 🌐 Coordenadas")
    st.write(f"Latitude: **{r['lat']}**")
    st.write(f"Longitude: **{r['lng']}**")

    st.markdown("### 🎯 Precisão do Google")
    st.write(r["precisao"])

    # Mapa
    df_map = pd.DataFrame([{
        "lat": r["lat"],
        "lon": r["lng"]
    }])

    st.markdown("### 🗺️ Localização")
    st.map(df_map)

    # ======================================
    # POIs
    # ======================================
    hospitais, mercados, farmacias, escolas, parques, policia = carregar_pois(cidade)

    ponto = ponto_imovel(r["lat"], r["lng"])

    st.markdown("## 📏 Distância mínima aos POIs (metros)")

    st.write(f"🏥 Hospital: **{distancia_minima(ponto, hospitais)} m**")
    st.write(f"🛒 Mercado: **{distancia_minima(ponto, mercados)} m**")
    st.write(f"💊 Farmácia: **{distancia_minima(ponto, farmacias)} m**")
    st.write(f"🏫 Escola: **{distancia_minima(ponto, escolas)} m**")
    st.write(f"🌳 Parque: **{distancia_minima(ponto, parques)} m**")
    st.write(f"🚓 Segurança pública: **{distancia_minima(ponto, policia)} m**")

    st.markdown("## 📊 POIs em um raio de 1 km")

    st.write(f"🏫 Escolas: {contar_pois_raio(ponto, escolas, 500)}")
    st.write(f"🛒 Mercados: {contar_pois_raio(ponto, mercados, 500)}")
    st.write(f"💊 Farmácias: {contar_pois_raio(ponto, farmacias, 300)}")
    st.write(f"🚓 Segurança pública: {contar_pois_raio(ponto, policia, 1000)}")
    st.write(f"🏥 Hospital: {contar_pois_raio(ponto, hospitais, 1000)}")
    st.write(f"🌳 Parque: {contar_pois_raio(ponto, parques, 1000)}")