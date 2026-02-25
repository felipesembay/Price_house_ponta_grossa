import pymysql
from config import DB_CONFIG


def get_connection():
    """Cria conexão com MySQL usando configuração centralizada"""
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=pymysql.cursors.Cursor
    )


def salvar_predicao(dados, preco_predito, modelo, versao):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO predicoes (
        area_m2, endereco, banheiros, quartos, vagas_garagem,
        tipo_imovel_cat, is_sobrado,
        score_escola_privada, score_escola_publica, score_farmacia,
        score_hospitais, score_mercado, score_parque, score_seguranca,
        preco_anuncio, preco_predito, modelo, versao_modelo
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        dados["area_m2"],
        dados.get("endereco", "N/A"),
        dados["banheiros"],
        dados["quartos"],
        dados["vagas_garagem"],
        dados.get("tipo_imovel_cat", "casa"),
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
        modelo,
        versao
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()