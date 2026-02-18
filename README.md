# Projeto de Machine Learning: Previsão de Preços de Imóveis em Ponta Grossa

Um projeto end-to-end de machine learning que utiliza regressão para prever o preço de imóveis em Ponta Grossa, PR, com dados coletados via web scraping do ZapImóveis.

## 📋 Estrutura do Projeto

```
Casas Ponta Grossa/
├── src/                          # Código-fonte principal
│   ├── scraper.py               # Web scraping do ZapImóveis
│   ├── preprocessing.py          # Limpeza e preparação de dados
│   └── modelo.py                # Treino e avaliação de modelos
├── data/
│   ├── raw/                     # Dados brutos (não rastreados)
│   └── processed/               # Dados processados (não rastreados)
├── models/                       # Modelos treinados (não rastreados)
├── notebooks/                    # Jupyter notebooks para exploração
├── requirements.txt             # Dependências do projeto
├── .gitignore                   # Arquivos ignorados pelo Git
└── README.md                    # Este arquivo
```

## 🛠️ Dependências

- **requests**: Para requisições HTTP
- **beautifulsoup4**: Para parsing de HTML
- **pandas**: Manipulação de dados
- **numpy**: Operações numéricas
- **scikit-learn**: Machine learning
- **matplotlib/seaborn**: Visualização

## 🚀 Como Usar

### 1. Configurar Ambiente

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Fazer Web Scraping

```bash
python src/scraper.py
```

Isso irá:
- Fazer scraping de múltiplas páginas do ZapImóveis
- Extrair dados como preço, localização, quartos, banheiros e área
- Salvar dados brutos em `data/raw/imoveis_guarapuava.csv`

### 3. Pré-processar Dados

```bash
python src/preprocessing.py
```

Operações realizadas:
- Limpeza de valores monetários
- Tratamento de valores faltantes
- Remoção de outliers
- Feature engineering (preço por m², etc.)
- Normalização

Saída: `data/processed/imoveis_guarapuava_processados.csv`

### 4. Treinar Modelos

```bash
python src/modelo.py
```

Modelos treinados:
- Regressão Linear
- Ridge (L2 Regularization)
- Lasso (L1 Regularization)
- Random Forest
- Gradient Boosting

Saída:
- Melhor modelo salvo em `models/`
- Comparativo de métricas em `results/comparativo_modelos.csv`

## 📊 Métricas de Avaliação

Os modelos são avaliados usando:
- **RMSE** (Root Mean Squared Error): Erro médio em reais
- **MAE** (Mean Absolute Error): Erro absoluto médio
- **R² Score**: Proporção da variância explicada (0-1)

## 🔍 Features Utilizadas

| Feature | Descrição |
|---------|-----------|
| `area_m2` | Área do imóvel em metros quadrados |
| `quartos` | Número de quartos |
| `banheiros` | Número de banheiros |
| `preco_por_m2` | Preço por metro quadrado (engenharia) |
| `banheiro_por_quarto` | Razão banheiros/quartos (engenharia) |
| `tamanho_imovel` | Classificação de tamanho (engenharia) |

## 📈 Pipeline Completo

```
Web Scraping → Limpeza → Exploração → Pré-processamento → 
Feature Engineering → Treinamento → Avaliação → Deployment
```

## 🎯 Próximos Passos

1. **Exploração de Dados**: Criar notebooks Jupyter para análise exploratória
2. **Ajuste de Hiperparâmetros**: Otimização usando GridSearchCV
3. **Validação Cruzada**: Implementar k-fold cross-validation
4. **API**: Criar API REST para fazer predições
5. **Monitoramento**: Acompanhar performance do modelo em produção

## ⚠️ Importante

- Respeite o `robots.txt` e os termos de serviço do ZapImóveis
- Use delays adequados entre requisições (padrão: 2 segundos)
- Os dados brutos e modelos não são rastreados no Git (veja `.gitignore`)

## 📝 Licença

Este projeto é fornecido como exemplo educacional.

## 👤 Autor

Felipe - Portfolio de Machine Learning

---

**Última atualização**: 6 de fevereiro de 2026
