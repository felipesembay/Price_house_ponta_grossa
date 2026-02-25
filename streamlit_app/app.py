"""
App Streamlit com Pipeline Completo de Feature Engineering

Este app segue a mesma lógica dos notebooks Coleta_e_tratamento.ipynb e EDA.ipynb:
1. Usuário insere endereço do imóvel
2. Geocoding do endereço → lat/lon
3. Cálculo de distâncias e contagens de POIs (escolas, hospitais, mercados, etc.)
4. Geração de scores de proximidade
5. Predição via API
6. Salvamento no banco de dados
"""

import os
import time

import numpy as np
import pandas as pd
import streamlit as st
from db import salvar_predicao
from geopy.geocoders import Nominatim
from shapely import wkt
from sklearn.neighbors import BallTree

from api import prever_preco

# ============================================================
# Configuração
# ============================================================

st.set_page_config(page_title="Previsão de Imóveis - Pipeline Completo", layout="wide")

# Caminhos dos POIs
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pre")

# Cache para não recarregar a cada interação
@st.cache_data
def carregar_pois():
    """Carrega todos os datasets de POIs"""
    
    escolas = pd.read_csv(os.path.join(DATA_DIR, "escolas.csv"))
    hospitais = pd.read_csv(os.path.join(DATA_DIR, "hospitais.csv"))
    parques = pd.read_csv(os.path.join(DATA_DIR, "parques.csv"))
    farmacia = pd.read_csv(os.path.join(DATA_DIR, "farmacia.csv"))
    mercado = pd.read_csv(os.path.join(DATA_DIR, "mercados.csv"))
    policia = pd.read_csv(os.path.join(DATA_DIR, "policia.csv"))
    
    # Separar escolas por tipo
    escolas_publicas = escolas[escolas["tipo_escola"] == "publica"].copy()
    escolas_privadas = escolas[escolas["tipo_escola"] == "privada"].copy()
    
    return {
        "escolas_publicas": escolas_publicas,
        "escolas_privadas": escolas_privadas,
        "hospitais": hospitais,
        "parques": parques,
        "farmacia": farmacia,
        "mercado": mercado,
        "policia": policia
    }

# ============================================================
# Funções de Feature Engineering (mesmas do EDA.ipynb)
# ============================================================

def extract_lat_lon_from_geometry(df, geometry_col="geometry"):
    """
    Extrai lat/lon de geometrias POINT ou POLYGON usando centróide
    Mesma função do EDA.ipynb
    """
    def get_lat_lon(geom_wkt):
        try:
            geom = wkt.loads(geom_wkt)
            point = geom.centroid
            return pd.Series({
                "lat": point.y,
                "lon": point.x
            })
        except:
            return pd.Series({
                "lat": None,
                "lon": None
            })

    coords = df[geometry_col].apply(get_lat_lon)
    df = pd.concat([df, coords], axis=1)
    return df


def calcular_poi_features(lat, lon, pois):
    """
    Calcula distâncias e contagens de POIs para um único imóvel
    Baseado na função add_poi_features do EDA.ipynb
    
    Retorna dict com:
    - dist_escolas_privadas_mais_proximo
    - qtd_escolas_privadas_500m
    - dist_escola_publicas_mais_proximo
    - qtd_escola_publicas_500m
    - dist_hospital_mais_proximo
    - qtd_hospital_1000m
    - dist_mercado_mais_proximo
    - qtd_mercado_500m
    - dist_farmacia_mais_proximo
    - qtd_farmacia_300m
    - dist_parque_mais_proximo
    - qtd_parque_1000m
    - dist_policia_mais_proximo
    - qtd_policia_500m
    """
    
    features = {}
    imovel_coords = np.radians([[lat, lon]])
    
    # Configurações de raios por tipo de POI (mesmas do notebook)
    configs = {
        "escolas_privadas": 500,
        "escola_publicas": 500,  # Note: usa "escola_publicas" sem 's' no final
        "hospital": 1000,
        "mercado": 500,
        "farmacia": 300,
        "parque": 1000,
        "policia": 500
    }
    
    for poi_name, radius in configs.items():
        # Ajustar nome do POI se necessário
        poi_key = poi_name
        if poi_name == "escola_publicas":
            poi_key = "escolas_publicas"
        elif poi_name == "hospital":
            poi_key = "hospitais"
        elif poi_name == "parque":
            poi_key = "parques"
        
        df_poi = pois[poi_key]
        
        # Extrair coordenadas (se ainda não tiver lat/lon)
        if "lat" not in df_poi.columns or "lon" not in df_poi.columns:
            geom_col = "geometry_std" if "geometry_std" in df_poi.columns else "geometry"
            df_poi = extract_lat_lon_from_geometry(df_poi, geom_col)
        
        # Remover POIs sem coordenadas
        df_poi = df_poi.dropna(subset=["lat", "lon"])
        
        if len(df_poi) == 0:
            features[f"dist_{poi_name}_mais_proximo"] = np.nan
            features[f"qtd_{poi_name}_{radius}m"] = 0
            continue
        
        # Converter para radianos
        poi_coords = np.radians(df_poi[["lat", "lon"]].values)
        
        # Construir BallTree
        tree = BallTree(poi_coords, metric="haversine")
        
        # Distância mínima
        dist, _ = tree.query(imovel_coords, k=1)
        features[f"dist_{poi_name}_mais_proximo"] = dist[0, 0] * 6371000  # metros
        
        # Contagem no raio
        count = tree.query_radius(
            imovel_coords,
            r=radius / 6371000,
            count_only=True
        )
        features[f"qtd_{poi_name}_{radius}m"] = int(count[0])
    
    return features


def calcular_scores(features):
    """
    Calcula os scores de proximidade baseado nas distâncias e contagens
    Mesma lógica do EDA.ipynb
    """
    
    scores = {}
    
    # Score de escolas privadas
    scores['score_escola_privada'] = (
        1.2 * np.exp(-features['dist_escolas_privadas_mais_proximo'] / 600) +
        0.6 * features['qtd_escolas_privadas_500m']
    )
    
    # Score de escolas públicas
    scores['score_escola_publica'] = (
        0.6 * np.exp(-features['dist_escola_publicas_mais_proximo'] / 600) +
        0.2 * features['qtd_escola_publicas_500m']
    )
    
    # Score de hospitais
    scores['score_hospitais'] = (
        0.8 * np.exp(-features['dist_hospital_mais_proximo'] / 1200) +
        0.4 * features['qtd_hospital_1000m']
    )
    
    # Score de mercados
    scores['score_mercado'] = (
        1.0 * np.exp(-features['dist_mercado_mais_proximo'] / 400) +
        0.4 * features['qtd_mercado_500m']
    )
    
    # Score de farmácias
    scores['score_farmacia'] = (
        0.6 * np.exp(-features['dist_farmacia_mais_proximo'] / 300) +
        0.2 * features['qtd_farmacia_300m']
    )
    
    # Score de parques
    scores['score_parque'] = (
        1.2 * np.exp(-features['dist_parque_mais_proximo'] / 1200) +
        0.8 * features['qtd_parque_1000m']
    )
    
    # Score de segurança (polícia)
    scores['score_seguranca'] = (
        1.0 * np.exp(-features['dist_policia_mais_proximo'] / 1500) +
        0.3 * features['qtd_policia_500m']
    )
    
    return scores


def geocode_endereco(endereco_completo):
    """
    Converte endereço em lat/lon usando Nominatim (mesmo do Coleta_e_tratamento)
    """
    geolocator = Nominatim(user_agent="price_house_app")
    
    try:
        time.sleep(1)  # Rate limiting
        location = geolocator.geocode(endereco_completo, timeout=10)
        
        if location:
            return location.latitude, location.longitude, "sucesso"
        else:
            return None, None, "nao_encontrado"
    except Exception as e:
        return None, None, f"erro: {str(e)}"


# ============================================================
# Interface Streamlit
# ============================================================

st.title("🏡 Previsão de Preço de Imóveis")
st.caption("Pipeline completo: Endereço → Geocoding → Feature Engineering → Predição")

# Carregar POIs (apenas uma vez)
with st.spinner("Carregando base de dados de POIs..."):
    pois = carregar_pois()

st.success(f"✅ POIs carregados: {sum(len(df) for df in pois.values())} registros")

# Formulário
with st.form("form_imovel"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 Localização")
        rua = st.text_input("Rua/Avenida", placeholder="Ex: Rua XV de Novembro")
        bairro = st.text_input("Bairro", placeholder="Ex: Centro")
        cidade = st.text_input("Cidade", value="Ponta Grossa")
        estado = st.text_input("Estado", value="PR")
        
    with col2:
        st.subheader("🏠 Características do Imóvel")
        area = st.number_input("Área (m²)", min_value=10, value=100, step=10)
        quartos = st.number_input("Quartos", min_value=0, value=3, step=1)
        banheiros = st.number_input("Banheiros", min_value=0, value=2, step=1)
        vagas = st.number_input("Vagas de garagem", min_value=0, value=1, step=1)
    
    submit = st.form_submit_button("🔮 Processar e Prever Preço", use_container_width=True)

# Processamento
if submit:
    if not rua or not bairro:
        st.error("❌ Por favor, preencha ao menos a Rua e o Bairro")
    else:
        # Construir endereço completo
        endereco_completo = f"{rua}, {bairro}, {cidade}, {estado}, Brasil"
        
        st.info(f"📌 Endereço: {endereco_completo}")
        
        # ETAPA 1: Geocoding
        with st.spinner("🌍 Fazendo geocoding do endereço..."):
            lat, lon, status = geocode_endereco(endereco_completo)
        
        if lat is None:
            st.error(f"❌ Não foi possível geocodificar o endereço. Status: {status}")
            st.stop()
        
        st.success(f"✅ Coordenadas: {lat:.6f}, {lon:.6f}")
        
        # Mostrar no mapa
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
        
        # ETAPA 2: Calcular features de POI
        with st.spinner("📊 Calculando distâncias e contagens de POIs..."):
            poi_features = calcular_poi_features(lat, lon, pois)
        
        # Mostrar features calculadas
        with st.expander("🔍 Ver Features de POI calculadas"):
            st.json(poi_features)
        
        # ETAPA 3: Calcular scores
        with st.spinner("🧮 Calculando scores de proximidade..."):
            scores = calcular_scores(poi_features)
        
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
        
        # ETAPA 4: Preparar payload para API
        payload = {
            "cidade": cidade,
            "bairro": bairro,
            "area_m2": float(area),
            "quartos": int(quartos),
            "banheiros": int(banheiros),
            "vagas_garagem": int(vagas),
            "score_escola_privada": float(scores['score_escola_privada']),
            "score_escola_publica": float(scores['score_escola_publica']),
            "score_hospitais": float(scores['score_hospitais']),
            "score_mercado": float(scores['score_mercado']),
            "score_farmacia": float(scores['score_farmacia']),
            "score_parque": float(scores['score_parque']),
            "score_seguranca": float(scores['score_seguranca'])
        }
        
        # ETAPA 5: Predição
        with st.spinner("🤖 Fazendo predição do preço..."):
            try:
                resultado = prever_preco(payload)
                preco = resultado["preco_estimado"]
                
                st.success(f"### 💰 Preço Estimado: R$ {preco:,.2f}")
                st.caption(f"Log(preço): {resultado.get('log_preco', 0):.4f}")
                
                # ETAPA 6: Salvar no banco
                with st.spinner("💾 Salvando predição no banco de dados..."):
                    salvar_predicao(
                        payload,
                        preco,
                        "RealEstatePriceModel",
                        "1.0.0"
                    )
                
                st.success("✅ Predição salva no banco de dados!")
                
            except Exception as e:
                st.error(f"❌ Erro na predição: {str(e)}")
                st.exception(e)
