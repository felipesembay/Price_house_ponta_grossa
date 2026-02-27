CREATE DATABASE IF NOT EXISTS imoveis;
USE imoveis;

CREATE TABLE predicoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    area_m2 FLOAT,
    endereco VARCHAR(255),
    banheiros INT,
    quartos INT,
    vagas_garagem INT,
    
    tipo_imovel_cat VARCHAR(50),
    is_sobrado INT DEFAULT 0,

    score_escola_privada FLOAT,
    score_escola_publica FLOAT,
    score_farmacia FLOAT,
    score_hospitais FLOAT,
    score_mercado FLOAT,
    score_parque FLOAT,
    score_seguranca FLOAT,

    preco_anuncio FLOAT,
    preco_predito FLOAT,

    erro_absoluto FLOAT,
    erro_percentual FLOAT,

    modelo VARCHAR(100),
    versao_modelo VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Script de migração para adicionar novas colunas em tabela existente
-- USE imoveis;
-- ALTER TABLE predicoes ADD COLUMN tipo_imovel_cat VARCHAR(50) AFTER vagas_garagem;
-- ALTER TABLE predicoes ADD COLUMN is_sobrado INT DEFAULT 0 AFTER tipo_imovel_cat;


CREATE TABLE pois (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    nome VARCHAR(255),
    tipo_poi ENUM(
        'mercado',
        'farmacia',
        'escola',
        'hospital',
        'parque',
        'policia'
    ) NOT NULL,

    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(10,7) NOT NULL,

    cidade VARCHAR(120) NOT NULL,
    estado CHAR(2),

    fonte VARCHAR(100), -- ex: 'csv', 'osm', 'google'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_poi_cidade (cidade),
    INDEX idx_poi_tipo (tipo_poi),
    INDEX idx_poi_lat_lon (latitude, longitude)
);

ALTER TABLE predicoes
ADD COLUMN erro_absoluto FLOAT,
ADD COLUMN erro_percentual FLOAT;

--Query para Drifit de Baseline
CREATE TABLE features_monitoramento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    predicao_id INT,

    area_m2 FLOAT,
    score_escola_privada FLOAT,
    score_escola_publica FLOAT,
    score_farmacia FLOAT,
    score_hospitais FLOAT,
    score_mercado FLOAT,
    score_parque FLOAT,
    score_seguranca FLOAT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (predicao_id) REFERENCES predicoes(id)
);

CREATE TABLE metrics_monitoramento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value FLOAT,
    feature_name VARCHAR(100),
    metric_type VARCHAR(50), -- drift, performance
    modelo VARCHAR(100),
    versao_modelo VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


--Criando a Query de Baseline para calcular os erros
SELECT
    COUNT(*) AS total_predicoes,
    AVG(erro_absoluto) AS mae,
    AVG(erro_percentual) AS mape,
    STDDEV(erro_percentual) AS std_mape
FROM predicoes
WHERE erro_percentual IS NOT NULL;

-- Analise por faixa de preço
SELECT
    CASE
        WHEN preco_anuncio < 200000 THEN 'Até 200k'
        WHEN preco_anuncio BETWEEN 200000 AND 400000 THEN '200k–400k'
        WHEN preco_anuncio BETWEEN 400000 AND 700000 THEN '400k–700k'
        ELSE '700k+'
    END AS faixa_preco,
    COUNT(*) AS total,
    AVG(erro_percentual) AS mape
FROM predicoes
WHERE erro_percentual IS NOT NULL
GROUP BY faixa_preco;

-- Monitoramento temporal (model degradation)
SELECT
    DATE(created_at) AS dia,
    AVG(erro_percentual) AS mape_dia
FROM predicoes
WHERE erro_percentual IS NOT NULL
GROUP BY dia
ORDER BY dia;



