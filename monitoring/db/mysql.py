import os
from datetime import datetime, timedelta

import pandas as pd
import pymysql

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "airflow"),
    "database": os.getenv("MYSQL_DATABASE", "imoveis"),
    "port": int(os.getenv("MYSQL_PORT", 3306))
}


def get_connection():
    return pymysql.connect(
        cursorclass=pymysql.cursors.DictCursor,
        **MYSQL_CONFIG
    )


def load_baseline_data(baseline_days: int) -> pd.DataFrame:
    query = f"""
        SELECT *
        FROM predicoes
        WHERE created_at < NOW() - INTERVAL {baseline_days} DAY
    """
    with get_connection() as conn:
        return pd.read_sql(query, conn)


def load_current_data(current_days: int) -> pd.DataFrame:
    query = f"""
        SELECT *
        FROM predicoes
        WHERE created_at >= NOW() - INTERVAL {current_days} DAY
    """
    with get_connection() as conn:
        return pd.read_sql(query, conn)


def save_metric(
    metric_name: str,
    metric_value: float,
    feature_name: str,
    metric_type: str,
    modelo: str,
    versao_modelo: str
):
    query = """
        INSERT INTO metrics_monitoramento (
            metric_name,
            metric_value,
            feature_name,
            metric_type,
            modelo,
            versao_modelo
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    metric_name,
                    metric_value,
                    feature_name,
                    metric_type,
                    modelo,
                    versao_modelo
                )
            )
        conn.commit()


def save_distribution_stats(
    feature_name: str,
    dataset_type: str,  # 'baseline' ou 'production'
    stats: dict,
    modelo: str,
    versao_modelo: str
):
    """
    Salva estatísticas descritivas de uma feature.
    
    Args:
        feature_name: nome da feature
        dataset_type: 'baseline' ou 'production'
        stats: dict com keys: mean, std, min, max, p25, p50, p75, count
        modelo: nome do modelo
        versao_modelo: versão do modelo
    """
    query = """
        INSERT INTO distribution_stats (
            feature_name,
            dataset_type,
            mean_value,
            std_value,
            min_value,
            max_value,
            p25_value,
            p50_value,
            p75_value,
            sample_count,
            modelo,
            versao_modelo
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    feature_name,
                    dataset_type,
                    stats.get('mean'),
                    stats.get('std'),
                    stats.get('min'),
                    stats.get('max'),
                    stats.get('p25'),
                    stats.get('p50'),
                    stats.get('p75'),
                    stats.get('count'),
                    modelo,
                    versao_modelo
                )
            )
        conn.commit()
        conn.commit()