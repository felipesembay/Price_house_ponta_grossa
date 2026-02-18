CREATE DATABASE IF NOT EXISTS imoveis;
USE imoveis;


CREATE TABLE predicoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    area_m2 FLOAT,
    bairro VARCHAR(100),
    banheiros INT,
    quartos INT,
    vagas_garagem INT,

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


USE imoveis;

ALTER TABLE predicoes
ADD COLUMN cidade VARCHAR(100) NOT NULL AFTER bairro;


USE imoveis;

ALTER TABLE predicoes
MODIFY COLUMN cidade VARCHAR(100) NOT NULL
AFTER versao_modelo;


