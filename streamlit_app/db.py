import pymysql
from config import DB_CONFIG


def get_connection():
    """Cria conexão com MySQL usando configuração centralizada"""
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=pymysql.cursors.Cursor
    )


# def salvar_predicao(dados, preco_predito, modelo, versao, erro_abs=None, erro_pct=None):
#     conn = get_connection()
#     cursor = conn.cursor()

#     query = """
#     INSERT INTO predicoes (
#         area_m2, endereco, banheiros, quartos, vagas_garagem,
#         tipo_imovel_cat, is_sobrado,
#         score_escola_privada, score_escola_publica, score_farmacia,
#         score_hospitais, score_mercado, score_parque, score_seguranca,
#         preco_anuncio, preco_predito, erro_absoluto, erro_percentual,
#         modelo, versao_modelo
#     ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """

#     values = (
#         dados["area_m2"],
#         dados.get("endereco", "N/A"),
#         dados["banheiros"],
#         dados["quartos"],
#         dados["vagas_garagem"],
#         dados.get("tipo_imovel_cat", "casa"),
#         dados.get("is_sobrado", 0),
#         dados["score_escola_privada"],
#         dados["score_escola_publica"],
#         dados["score_farmacia"],
#         dados["score_hospitais"],
#         dados["score_mercado"],
#         dados["score_parque"],
#         dados["score_seguranca"],
#         dados.get("preco_anuncio"),
#         preco_predito,
#         erro_abs,
#         erro_pct,
#         modelo,
#         versao
#     )

#     cursor.execute(query, values)
#     conn.commit()

#     cursor.close()
#     conn.close()


def salvar_predicao(dados, preco_predito, modelo, versao, erro_abs=None, erro_pct=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO predicoes (
    area_m2,
    endereco,
    banheiros,
    quartos,
    vagas_garagem,
    tipo_imovel_cat,
    is_sobrado,
    score_escola_privada,
    score_escola_publica,
    score_farmacia,
    score_hospitais,
    score_mercado,
    score_parque,
    score_seguranca,
    preco_anuncio,
    preco_predito,
    erro_absoluto,
    erro_percentual,
    modelo,
    versao_modelo
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

    values = (
    dados["area_m2"],
    dados.get("endereco"),
    dados["banheiros"],
    dados["quartos"],
    dados["vagas_garagem"],
    dados["tipo_imovel_cat"],
    dados.get("is_sobrado", 0),
    dados["score_escola_privada"],
    dados["score_escola_publica"],
    dados["score_farmacia"],
    dados["score_hospitais"],
    dados["score_mercado"],
    dados["score_parque"],
    dados["score_seguranca"],
    dados.get("preco_anuncio"),
    preco_predito,
    erro_abs,
    erro_pct,
    modelo,
    versao
)

    cursor.execute(query, values)
    conn.commit()

    predicao_id = cursor.lastrowid  # 👈 ponto chave

    cursor.close()
    conn.close()

    return predicao_id


def salvar_features_monitoramento(predicao_id, area_m2, scores):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO features_monitoramento (
        predicao_id,
        area_m2,
        score_escola_privada,
        score_escola_publica,
        score_farmacia,
        score_hospitais,
        score_mercado,
        score_parque,
        score_seguranca
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        predicao_id,
        area_m2,
        scores["score_escola_privada"],
        scores["score_escola_publica"],
        scores["score_farmacia"],
        scores["score_hospitais"],
        scores["score_mercado"],
        scores["score_parque"],
        scores["score_seguranca"]
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()