import os

import pymysql


def get_connection():
    return pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="airflow",
        database="imoveis",
        charset='utf8mb4',
        cursorclass=pymysql.cursors.Cursor
    )

def salvar_predicao(dados, preco, modelo, versao):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO predicoes (
        area_m2, bairro, banheiros, quartos, vagas_garagem,
        score_escola_privada, score_escola_publica, score_farmacia,
        score_hospitais, score_mercado, score_parque, score_seguranca,
        preco_predito, modelo, versao_modelo, cidade
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        dados["area_m2"],
        dados["bairro"],
        dados["banheiros"],
        dados["quartos"],
        dados["vagas_garagem"],
        dados["score_escola_privada"],
        dados["score_escola_publica"],
        dados["score_farmacia"],
        dados["score_hospitais"],
        dados["score_mercado"],
        dados["score_parque"],
        dados["score_seguranca"],
        preco,
        modelo,
        versao,
        dados["cidade"]
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()