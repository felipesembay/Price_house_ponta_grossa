"""
App Streamlit com Pipeline Completo de Feature Engineering (versão produto)
Pipeline: Endereço → Google Geocoding → POIs OSMnx → Scores → Predição
"""

import os

import folium
import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd
import requests
import streamlit as st
from db import salvar_features_monitoramento, salvar_predicao
from dotenv import load_dotenv
from shapely.geometry import Point
from sklearn.neighbors import BallTree

from api import prever_preco

# ==========================================
# Configurações globais
# ==========================================
st.set_page_config(
    page_title="🏠 Precificação Imobiliária",
    layout="wide",
    initial_sidebar_state="collapsed"
)

ox.settings.use_cache = True  # Cache para melhor performance
ox.settings.log_console = False

load_dotenv()
GOOGLE_API_KEY = os.getenv("GEOCODING_MAPS")
if not GOOGLE_API_KEY:
    st.error("❌ Chave GEOCODING_MAPS não encontrada no .env")
    st.stop()

# ==========================================
# Google Geocoding
# ==========================================
@st.cache_data
def geocode_google(endereco: str):
    """Geocoding com Google Maps API"""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": endereco,
        "key": GOOGLE_API_KEY,
        "region": "br",
        "language": "pt-BR"
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        if data.get("status") != "OK":
            return None
            
        result = data["results"][0]
        location = result["geometry"]["location"]
        
        return {
            "lat": location["lat"],
            "lng": location["lng"],
            "endereco_formatado": result["formatted_address"]
        }
    except Exception as e:
        st.error(f"Erro no geocoding: {e}")
        return None

# ==========================================
# POIs via OSMnx (otimizado)
# ==========================================
def carregar_pois_por_ponto(lat, lng, raio=3000):
    configs = {
        "hospitais": {"amenity": "hospital"},
        "mercados": {"shop": ["supermarket", "convenience"]},
        "farmacias": {"amenity": "pharmacy"},
        "escolas": {"amenity": ["school", "college", "university"]},
        "parques": {"leisure": ["park", "garden"], "landuse": "recreation_ground"},
        "policia": {"amenity": ["police", "fire_station", "courthouse"]}
    }

    pois_data = {}

    for nome, tags in configs.items():
        try:
            gdf = ox.features_from_point((lat, lng), tags, dist=raio)

            if gdf.empty:
                pois_data[nome] = {"coords": np.empty((0, 2)), "count": 0}
                continue

            gdf["geometry"] = gdf.geometry.apply(
                lambda g: g.centroid if g.geom_type != "Point" else g
            )

            coords = np.radians(
                np.column_stack([
                    gdf.geometry.y.values,
                    gdf.geometry.x.values
                ])
            )

            pois_data[nome] = {
                "coords": coords,
                "count": coords.shape[0]
            }

        except Exception as e:
            pois_data[nome] = {"coords": np.empty((0, 2)), "count": 0}

    return pois_data

def calcular_features_poi(lat, lng, pois_data):
    """Calcula distâncias e contagens usando BallTree"""
    imovel_coords = np.radians([[lat, lng]])
    features = {}
    
    raios = {
        "hospitais": 1000,
        "mercados": 500,
        "farmacias": 300,
        "escolas": 500,
        "parques": 1000,
        "policia": 500
    }
    
    for nome, data in pois_data.items():
        if len(data["coords"]) == 0:
            features[f"dist_{nome}_mais_proximo"] = np.inf
            features[f"qtd_{nome}_{raios[nome]}m"] = 0
            continue
        
        tree = BallTree(data["coords"], metric="haversine")
        
        # Distância mínima
        dist, _ = tree.query(imovel_coords, k=1)
        features[f"dist_{nome}_mais_proximo"] = dist[0, 0] * 6371000  # metros
        
        # Contagem no raio
        count = tree.query_radius(
            imovel_coords,
            r=raios[nome] / 6371000,
            count_only=True
        )[0]
        features[f"qtd_{nome}_{raios[nome]}m"] = int(count)
    
    return features

# ==========================================
# Scores (compatível com API original)
# ==========================================
def calcular_scores(features):
    """Calcula scores mantendo compatibilidade com API"""
    scores = {}
    
    # Hospitais
    scores['score_hospitais'] = (
        0.8 * np.exp(-features['dist_hospitais_mais_proximo'] / 1200) +
        0.4 * features['qtd_hospitais_1000m']
    )
    
    # Mercados
    scores['score_mercado'] = (
        1.0 * np.exp(-features['dist_mercados_mais_proximo'] / 400) +
        0.4 * features['qtd_mercados_500m']
    )
    
    # Farmacias
    scores['score_farmacia'] = (
        0.6 * np.exp(-features['dist_farmacias_mais_proximo'] / 300) +
        0.2 * features['qtd_farmacias_300m']
    )
    
    # Escolas (combinadas)
    scores['score_escola_privada'] = (
        1.2 * np.exp(-features['dist_escolas_mais_proximo'] / 600) +
        0.6 * features['qtd_escolas_500m']
    )
    scores['score_escola_publica'] = (
        0.6 * np.exp(-features['dist_escolas_mais_proximo'] / 600) +
        0.2 * features['qtd_escolas_500m']
    )
    
    # Parques
    scores['score_parque'] = (
        1.2 * np.exp(-features['dist_parques_mais_proximo'] / 1200) +
        0.8 * features['qtd_parques_1000m']
    )
    
    # Segurança
    scores['score_seguranca'] = (
        1.0 * np.exp(-features['dist_policia_mais_proximo'] / 1500) +
        0.3 * features['qtd_policia_500m']
    )
    
    return {k: round(v, 2) for k, v in scores.items()}

# ==========================================
# Interface Principal
# ==========================================
st.title("🏡 Previsão de Preço de Imóveis")
st.caption("🔮 Endereço → Google Maps → POIs Dinâmicos → Predição em tempo real")


st.subheader("📍 Endereço")
endereco = st.text_input(
        "Endereço completo",
        placeholder="Av. Presidente Getúlio Vargas, 1811, Curitiba, PR",
        help="Digite o endereço completo para melhor precisão"
    )

# Formulário
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🏠 Características")
    area_m2 = st.number_input("Área (m²)", min_value=10, value=150, step=10)
    quartos = st.number_input("Quartos", min_value=0, value=3, step=1)
    banheiros = st.number_input("Banheiros", min_value=0, value=2, step=1)
    vagas = st.number_input("Vagas de garagem", min_value=0, value=2, step=1)
    
with col2:
    is_sobrado = st.checkbox("Sobrado", value=False)
    tipo_imovel = st.selectbox("Tipo de imóvel", ["casa", "apartamento", "sala comercial"])
    preco_anuncio = st.number_input("Preço do anúncio (opcional)", min_value=0, value=0, step=100000)

if st.button("🚀 Calcular Previsão", type="primary", use_container_width=True):
    if not endereco.strip():
        st.error("❌ Por favor, insira um endereço válido")
        st.stop()
    
    # 1. GEOCODING
    with st.spinner("🌍 Geocodificando endereço..."):
        geo = geocode_google(endereco)
    
    if not geo:
        st.error("❌ Endereço não encontrado. Verifique a grafia.")
        st.stop()
    
    st.success(f"✅ {geo['endereco_formatado']}")
    
    st.map(pd.DataFrame({'lat': [geo["lat"]], 'lon': [geo["lng"]]}))
    
    # 2. POIs e FEATURES
    with st.spinner("📍 Buscando POIs próximos (raio 3km)..."):
        pois_data = carregar_pois_por_ponto(geo["lat"], geo["lng"])
        features = calcular_features_poi(geo["lat"], geo["lng"], pois_data)
    
    # 3. SCORES
    with st.spinner("🧮 Calculando scores de localização..."):
        scores = calcular_scores(features)
    
            # Mostrar features calculadas
        with st.expander("🔍 Ver Features de POI calculadas"):
            st.json(features)
        
        # ETAPA 3: Calcular scores
        with st.spinner("🧮 Calculando scores de proximidade..."):
            scores = calcular_scores(features)
        
        # Mostrar scores
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏫 Score Escolas Privadas", f"{scores['score_escola_privada']:.2f}")
            st.metric("🏫 Score Escolas Públicas", f"{scores['score_escola_publica']:.2f}")
        with col2:
            st.metric("🏥 Score Hospitais", f"{scores['score_hospitais']:.2f}")
            st.metric("🛒 Score Mercados", f"{scores['score_mercado']:.2f}")
        with col3:
            st.metric("💊 Score Farmácias", f"{scores['score_farmacia']:.2f}")
            st.metric("🌳 Score Parques", f"{scores['score_parque']:.2f}")
            st.metric("👮 Score Segurança", f"{scores['score_seguranca']:.2f}")
    
    # 4. PREPARAR PAYLOAD (compatível com API original)
    payload = {
    "area_m2": float(area_m2),
    "endereco": geo["endereco_formatado"],
    "banheiros": int(banheiros),
    "is_sobrado": int(is_sobrado),
    "quartos": int(quartos),
    "tipo_imovel_cat": tipo_imovel,
    "vagas_garagem": int(vagas),
    "preco_anuncio": float(preco_anuncio) if preco_anuncio > 0 else None,
    **scores
}
    
    # 5. PREVISÃO
    with st.expander("📤 Payload enviado à API (compare com seu curl)"):
        st.json(payload)

    with st.spinner("🤖 Fazendo predição com IA..."):
        try:
            resultado = prever_preco(payload)
            preco = resultado["preco_estimado"]
            preco_predito = preco
            preco_real = payload.get("preco_anuncio")

            erro_abs = None
            erro_pct = None

            if preco_real is not None and preco_real > 0:
                erro_abs = abs(preco_predito - preco_real)
                erro_pct = erro_abs / preco_real
            
            st.success(f"#### 💰 Preço Estimado: R$ {preco:,.2f}")
            st.caption(f"Log(preço): {resultado.get('log_preco', 0):.4f}")

            if erro_abs is not None:
                st.info(f"""
    📉 **Erro da previsão**
    - Erro absoluto: R$ {erro_abs:,.2f}
    - Erro percentual: {erro_pct * 100:.2f}%
    """)
            
            # ETAPA 6: Salvar no banco
            with st.spinner("💾 Salvando predição no banco de dados..."):
                predicao_id = salvar_predicao(
                    dados=payload,
                    preco_predito=preco,
                    modelo="RealEstatePriceModel",
                    versao="2.0.0",
                    erro_abs=erro_abs,
                    erro_pct=erro_pct
                )
                
                salvar_features_monitoramento(
                    predicao_id=predicao_id,
                    area_m2=payload["area_m2"],
                    scores=scores)
            
            st.success("✅ Predição salva no banco de dados!")
            
        except Exception as e:
            st.error(f"❌ Erro na predição: {str(e)}")
            st.exception(e)

# Rodapé
st.markdown("---")
st.caption("✅ Funciona em qualquer cidade do Brasil via Google Maps + OpenStreetMap")



