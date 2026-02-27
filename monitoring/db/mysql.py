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