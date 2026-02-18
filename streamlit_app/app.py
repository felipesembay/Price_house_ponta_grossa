import streamlit as st
from db import salvar_predicao

from api import prever_preco

st.set_page_config(page_title="Previsão de Imóveis", layout="centered")

st.title("🏡 Previsão de Preço de Imóveis")

with st.form("form_imovel"):
    cidade = st.text_input("Cidade", value="Ponta Grossa")
    bairro = st.text_input("Bairro")

    area = st.number_input("Área (m²)", min_value=10)
    quartos = st.number_input("Quartos", min_value=0)
    banheiros = st.number_input("Banheiros", min_value=0)
    vagas = st.number_input("Vagas de garagem", min_value=0)

    st.subheader("📍 Infraestrutura do entorno")

    score_escola_privada = st.slider("Escolas privadas", 0.0, 10.0, 1.0)
    score_escola_publica = st.slider("Escolas públicas", 0.0, 10.0, 1.0)
    score_farmacia = st.slider("Farmácias", 0.0, 10.0, 1.0)
    score_hospitais = st.slider("Hospitais", 0.0, 10.0, 1.0)
    score_mercado = st.slider("Mercados", 0.0, 10.0, 1.0)
    score_parque = st.slider("Parques", 0.0, 10.0, 1.0)
    score_seguranca = st.slider("Segurança", 0.0, 10.0, 1.0)

    submit = st.form_submit_button("🔮 Prever Preço")

if submit:
    payload = {
        "cidade": cidade,
        "bairro": bairro,
        "area_m2": area,
        "banheiros": banheiros,
        "quartos": quartos,
        "vagas_garagem": vagas,
        "score_escola_privada": score_escola_privada,
        "score_escola_publica": score_escola_publica,
        "score_farmacia": score_farmacia,
        "score_hospitais": score_hospitais,
        "score_mercado": score_mercado,
        "score_parque": score_parque,
        "score_seguranca": score_seguranca
    }

    with st.spinner("Calculando preço..."):
        resultado = prever_preco(payload)

    preco = resultado["preco_estimado"]

    st.success(f"💰 Preço estimado: R$ {preco:,.2f}")

    salvar_predicao(
        payload,
        preco,
        resultado.get("model_name"),
        resultado.get("version")
    )

    st.caption("Predição salva no banco de dados.")
