-- ─────────────────────────────────────────────────────────────────────────────
-- Schema MySQL — Monitoramento do Modelo de Precificação de Imóveis
-- Executado automaticamente na criação do container MySQL.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS imoveis;
USE imoveis;

-- ── Predições (histórico de inferências em produção) ─────────────────────────
CREATE TABLE IF NOT EXISTS predicoes (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    area_m2             FLOAT,
    endereco            VARCHAR(255),
    banheiros           INT,
    quartos             INT,
    vagas_garagem       INT,
    tipo_imovel_cat     VARCHAR(50),
    is_sobrado          INT DEFAULT 0,

    score_escola_privada FLOAT,
    score_escola_publica FLOAT,
    score_farmacia       FLOAT,
    score_hospitais      FLOAT,
    score_mercado        FLOAT,
    score_parque         FLOAT,
    score_seguranca      FLOAT,

    preco_anuncio        FLOAT,
    preco_predito        FLOAT,

    erro_absoluto        FLOAT,
    erro_percentual      FLOAT,

    modelo               VARCHAR(100),
    versao_modelo        VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_predicoes_created_at (created_at),
    INDEX idx_predicoes_modelo (modelo)
);

-- ── Features de monitoramento (ligadas a cada predição) ──────────────────────
CREATE TABLE IF NOT EXISTS features_monitoramento (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    predicao_id          INT,

    area_m2              FLOAT,
    score_escola_privada FLOAT,
    score_escola_publica FLOAT,
    score_farmacia       FLOAT,
    score_hospitais      FLOAT,
    score_mercado        FLOAT,
    score_parque         FLOAT,
    score_seguranca      FLOAT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (predicao_id) REFERENCES predicoes(id),
    INDEX idx_fm_predicao (predicao_id),
    INDEX idx_fm_created (created_at)
);

-- ── Métricas de monitoramento (resultados Evidently / Prometheus) ────────────
CREATE TABLE IF NOT EXISTS metrics_monitoramento (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    metric_name    VARCHAR(100)  NOT NULL,   -- ex: data_drift, dataset_drift_detected
    metric_value   FLOAT         NOT NULL,
    feature_name   VARCHAR(100),             -- ex: area_m2, score_mercado, dataset
    metric_type    VARCHAR(50),              -- ex: drift, performance
    modelo         VARCHAR(100),
    versao_modelo  VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_mm_metric   (metric_name),
    INDEX idx_mm_feature  (feature_name),
    INDEX idx_mm_created  (created_at),
    INDEX idx_mm_modelo   (modelo, versao_modelo)
);

-- ── POIs (pontos de interesse) ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pois (
    id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    nome      VARCHAR(255),
    tipo_poi  ENUM(
                  'mercado', 'farmacia', 'escola',
                  'hospital', 'parque', 'policia'
              ) NOT NULL,
    latitude  DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    cidade    VARCHAR(120)   NOT NULL,
    estado    CHAR(2),
    fonte     VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_poi_cidade    (cidade),
    INDEX idx_poi_tipo      (tipo_poi),
    INDEX idx_poi_lat_lon   (latitude, longitude)
);
