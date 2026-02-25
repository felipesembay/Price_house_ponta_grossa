# 🏡 Previsão de Preços de Imóveis — Ponta Grossa (PR)

Projeto **end-to-end de Machine Learning** para previsão de preços de imóveis residenciais em Ponta Grossa (PR), utilizando dados coletados via **web scraping**, enriquecidos com **features geoespaciais** e versionados com **MLflow** para uso em produção e APIs.

O projeto cobre todo o ciclo de vida do modelo: **coleta → feature engineering → treinamento → versionamento → deploy**.

---

## 🎯 Objetivo

Construir um modelo de regressão capaz de estimar o preço de imóveis com base em:

- características estruturais do imóvel  
- contexto urbano e infraestrutura local  
- indicadores de segurança e serviços essenciais  

O foco não é apenas acurácia, mas **reprodutibilidade, rastreabilidade e prontidão para produção**.

---

## 🧱 Arquitetura do Projeto

casas-ponta-grossa/
├── src/
│ ├── ingestion.py # Web scraping e coleta de dados
│ ├── features.py # Feature engineering e enriquecimento espacial
│ ├── preprocessing.py # Pipeline de pré-processamento
│ ├── train.py # Treinamento e registro no MLflow
│ └── predict.py # Inferência
│
├── data/
│ ├── raw/ # Dados brutos (não versionados)
│ └── processed/ # Dados processados
│
├── models/ # Modelos serializados (via MLflow)
├── notebooks/ # EDA e análises exploratórias
├── mlruns/ # Experimentos MLflow
├── requirements.txt
├── .gitignore
└── README.md


---

## 🔍 Coleta e Enriquecimento de Dados

### Fonte primária
- Web scraping de anúncios imobiliários (preço, área, quartos, banheiros e localização)

### Enriquecimento geoespacial
As propriedades são enriquecidas com informações do entorno, incluindo:

- mercados  
- farmácias  
- escolas  
- hospitais  
- indicadores de segurança  

Essas informações são transformadas em **features quantitativas**, como densidade, distância e presença por raio geográfico.

---

## 🧠 Feature Engineering

Exemplos de features utilizadas:

| Feature | Descrição |
|------|----------|
| `area_m2` | Área do imóvel |
| `quartos` | Número de quartos |
| `banheiros` | Número de banheiros |
| `preco_por_m2` | Preço por metro quadrado |
| `densidade_mercados` | Mercados em raio definido |
| `dist_hospital` | Distância ao hospital mais próximo |
| `indice_seguranca` | Indicador agregado de segurança |

---

## 🤖 Modelagem

Modelos avaliados:

- Regressão Linear  
- Ridge e Lasso  
- Random Forest Regressor  
- Gradient Boosting Regressor  

Todos os experimentos são rastreados com **MLflow**, incluindo:

- parâmetros  
- métricas  
- artefatos  
- versão do pipeline completo  

O modelo final é registrado no **MLflow Model Registry**.

---

## 📊 Métricas de Avaliação

- **RMSE** — erro médio quadrático  
- **MAE** — erro absoluto médio  
- **R²** — variância explicada  

As métricas são comparadas entre modelos para seleção da melhor abordagem.

---

## 🔁 Pipeline End-to-End

Web Scraping
↓
Tratamento de Dados
↓
Feature Engineering (Geo + Estrutural)
↓
Pré-processamento
↓
Treinamento (MLflow)
↓
Registro do Modelo
↓
API / Produção


---

## 🚀 Como Executar

### 1️⃣ Criar ambiente

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Treinar e registrar o modelo

```bash
python src/train.py
```

### 3️⃣ Iniciar a API (FastAPI + Uvicorn)

```bash
uvicorn api.main:app --reload --port 8009
```

A API estará disponível em: `http://localhost:8000`  
Documentação interativa (Swagger): `http://localhost:8000/docs`

### 4️⃣ Iniciar a interface do MLflow

```bash
mlflow ui
```

A interface estará disponível em: `http://localhost:5000`

### 5️⃣ Iniciar o app Streamlit

```bash
streamlit run streamlit_app/app2.py
```

---

## 🔌 Deploy e API

* A API REST foi implementada com **FastAPI**, recebendo dados brutos do imóvel e retornando a previsão de preço com o mesmo pré-processamento utilizado no treino.

## 🛣️ Próximos Passos

* Deploy via FastAPI

* Monitoramento de performance e data drift

* Automatização com Airflow

* CI/CD para modelos

* Feature Store

## 👤 Autor

**Felipe Sembay**
**Cientista de Dados | Machine Learning | MLOps**

Última atualização: 25 de Fevereiro de 2026

