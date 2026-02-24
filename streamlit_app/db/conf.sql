CREATE DATABASE IF NOT EXISTS imoveis;
USE imoveis;


CREATE TABLE predicoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    area_m2 FLOAT,
    bairro VARCHAR(100),
    cidade VARCHAR(100),
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

    preco_predito FLOAT,
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



