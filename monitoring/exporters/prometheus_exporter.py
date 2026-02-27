"""
prometheus_exporter.py
======================
Serviço que expõe métricas de monitoramento do modelo na porta 8007.
O Prometheus faz scrape periodicamente deste endpoint.

Métricas expostas:
  - feature_drift_score{feature, modelo, versao}  → drift score por feature
  - dataset_drift_detected{modelo, versao}         → 1.0 se dataset driftou
  - share_drifted_columns{modelo, versao}          → proporção de features driftadas
  - last_drift_run_timestamp                       → unix timestamp da última execução

Uso:
    python monitoring/exporters/prometheus_exporter.py
"""

import logging
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, ROOT)

import pymysql
from prometheus_client import Gauge, start_http_server

from monitoring.db.mysql import MYSQL_CONFIG

# ─── Configurações ────────────────────────────────────────────────────────────
PORT           = int(os.getenv("EXPORTER_PORT", 8007))
POLL_INTERVAL  = int(os.getenv("EXPORTER_POLL_SECONDS", 60))   # segundos entre coletas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EXPORTER] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

# ─── Definição das métricas Prometheus ───────────────────────────────────────
feature_drift_gauge = Gauge(
    "feature_drift_score",
    "Drift score por feature (Evidently KS / PSI)",
    ["feature", "modelo", "versao"],
)

dataset_drift_gauge = Gauge(
    "dataset_drift_detected",
    "1.0 se o dataset inteiro driftou, 0.0 caso contrário",
    ["modelo", "versao"],
)

share_drifted_gauge = Gauge(
    "share_drifted_columns",
    "Proporção de features com drift detectado",
    ["modelo", "versao"],
)

last_run_gauge = Gauge(
    "last_drift_run_timestamp",
    "Unix timestamp da última vez que o job de drift foi executado",
)


# ─── Lógica de coleta ─────────────────────────────────────────────────────────
def _get_connection():
    return pymysql.connect(cursorclass=pymysql.cursors.DictCursor, **MYSQL_CONFIG)


def collect_and_expose() -> None:
    """
    Lê as métricas mais recentes de `metrics_monitoramento` e atualiza
    os gauges do Prometheus.
    """
    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                # ── Feature drift (última leitura por feature/modelo/versão) ──
                cur.execute(
                    """
                    SELECT feature_name, metric_name, metric_value, modelo, versao_modelo, MAX(created_at) AS ts
                    FROM metrics_monitoramento
                    WHERE metric_name IN ('data_drift', 'dataset_drift_detected', 'share_drifted_columns')
                    GROUP BY feature_name, metric_name, modelo, versao_modelo
                    ORDER BY ts DESC
                    LIMIT 500
                    """
                )
                rows = cur.fetchall()

        last_ts = None

        for row in rows:
            modelo  = row["modelo"] or "unknown"
            versao  = row["versao_modelo"] or "unknown"
            val     = float(row["metric_value"])
            ts      = row["ts"]

            if last_ts is None or (ts and ts > last_ts):
                last_ts = ts

            if row["metric_name"] == "data_drift":
                feature_drift_gauge.labels(
                    feature=row["feature_name"],
                    modelo=modelo,
                    versao=versao,
                ).set(val)

            elif row["metric_name"] == "dataset_drift_detected":
                dataset_drift_gauge.labels(modelo=modelo, versao=versao).set(val)

            elif row["metric_name"] == "share_drifted_columns":
                share_drifted_gauge.labels(modelo=modelo, versao=versao).set(val)

        if last_ts is not None:
            last_run_gauge.set(last_ts.timestamp() if hasattr(last_ts, "timestamp") else float(last_ts))

        log.info("Métricas coletadas: %d registros.", len(rows))

    except Exception as exc:
        log.error("Erro ao coletar métricas do MySQL: %s", exc)


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info("Iniciando Prometheus Exporter na porta %d ...", PORT)
    start_http_server(PORT)
    log.info("Endpoint disponível em http://0.0.0.0:%d/metrics", PORT)

    while True:
        collect_and_expose()
        time.sleep(POLL_INTERVAL)
