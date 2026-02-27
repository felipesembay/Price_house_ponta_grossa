"""
generate_baseline.py
====================
Lê o complete.csv (dados brutos com POIs), calcula os scores de localização
e salva o baseline em data/processed/baseline_monitoring.parquet.

Esse arquivo é a "referência estável" usada pelo Evidently para detectar
data drift nas predições produtivas.

Uso:
    python monitoring/jobs/generate_baseline.py
"""

import os
import sys

# Garante que o root do projeto está no PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────
# Caminhos
# ─────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CSV_PATH = os.path.join(ROOT, "data/processed/complete.csv")
OUTPUT_PATH = os.path.join(ROOT, "data/processed/baseline_monitoring.parquet")


# ─────────────────────────────────────────────
# 1. Carregar dados
# ─────────────────────────────────────────────
print("📂 Carregando complete.csv ...")
df = pd.read_csv(CSV_PATH)

if "Unnamed: 0" in df.columns:
    df = df.drop(columns=["Unnamed: 0"])

print(f"   Shape: {df.shape}")


# ─────────────────────────────────────────────
# 2. Calcular scores  (espelhando ML2.ipynb)
# ─────────────────────────────────────────────
df["score_escola_privada"] = (
    1.2 * np.exp(-df["dist_escolas_privadas_mais_proximo"] / 600)
    + 0.6 * df["qtd_escolas_privadas_500m"]
)

df["score_escola_publica"] = (
    0.6 * np.exp(-df["dist_escola_publicas_mais_proximo"] / 600)
    + 0.2 * df["qtd_escola_publicas_500m"]
)

df["score_hospitais"] = (
    0.8 * np.exp(-df["dist_hospital_mais_proximo"] / 1200)
    + 0.4 * df["qtd_hospital_1000m"]
)

df["score_mercado"] = (
    1.0 * np.exp(-df["dist_mercado_mais_proximo"] / 400)
    + 0.4 * df["qtd_mercado_500m"]
)

df["score_farmacia"] = (
    0.6 * np.exp(-df["dist_farmacia_mais_proximo"] / 300)
    + 0.2 * df["qtd_farmacia_300m"]
)

df["score_parque"] = (
    1.2 * np.exp(-df["dist_parque_mais_proximo"] / 1200)
    + 0.8 * df["qtd_parque_1000m"]
)

df["score_seguranca"] = (
    1.0 * np.exp(-df["dist_policia_mais_proximo"] / 1500)
    + 0.3 * df["qtd_policia_500m"]
)

# score_educacao composto (usado internamente no notebook, mantido aqui)
df["score_educacao"] = df["score_escola_privada"] - 0.2 * df["score_escola_publica"]


# ─────────────────────────────────────────────
# 3. Faixas de área
# ─────────────────────────────────────────────
bins = [0, 50, 80, 120, 200, 400, df["area_m2"].max()]
labels = ["Até 50", "50–80", "80–120", "120–200", "200–400", "400+"]
df["faixa_area"] = pd.cut(df["area_m2"], bins=bins, labels=labels)


# ─────────────────────────────────────────────
# 4. Classificar tipo de imóvel
# ─────────────────────────────────────────────
def classificar_tipo_imovel(tipo: str) -> str:
    if pd.isna(tipo):
        return "outros"
    tipo = str(tipo).lower()

    if "terreno" in tipo or "lote" in tipo:
        return "terreno"
    if any(x in tipo for x in ["apartamento", "cobertura", "duplex", "flat", "kitnet"]):
        return "apartamento"
    if any(x in tipo for x in ["casa", "sobrado", "vila"]):
        return "casa"
    if any(x in tipo for x in ["comercial", "loja", "box", "galpão", "deposito", "depósito", "sala", "conjunto"]):
        return "comercial"
    if "prédio" in tipo or "edificio" in tipo or "edifício" in tipo:
        return "predio"
    return "outros"


df["tipo_imovel_cat"] = df["tipo_imovel"].apply(classificar_tipo_imovel)
df["is_sobrado"] = df["tipo_imovel"].str.lower().str.contains("sobrado", na=False).astype(int)


# ─────────────────────────────────────────────
# 5. Filtrar tipos principais + criar log_preco
# ─────────────────────────────────────────────
df = df[df["tipo_imovel_cat"].isin(["casa", "apartamento", "comercial"])].copy()
df["log_preco"] = np.log(df["preco"].clip(lower=1))

print(f"   Após filtro de tipo: {df.shape}")
print(df["tipo_imovel_cat"].value_counts().to_string())


# ─────────────────────────────────────────────
# 6. Selecionar colunas do baseline
# ─────────────────────────────────────────────
BASELINE_COLS = [
    # features numéricas do modelo
    "area_m2",
    "quartos",
    "banheiros",
    "vagas_garagem",
    "is_sobrado",
    # scores
    "score_escola_privada",
    "score_escola_publica",
    "score_hospitais",
    "score_mercado",
    "score_farmacia",
    "score_parque",
    "score_seguranca",
    # categórica
    "tipo_imovel_cat",
    # target
    "log_preco",
    "preco",
]

baseline = df[BASELINE_COLS].copy()
baseline = baseline.dropna(subset=["area_m2", "preco"])

print(f"   Baseline final: {baseline.shape}")


# ─────────────────────────────────────────────
# 7. Salvar
# ─────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
baseline.to_parquet(OUTPUT_PATH, index=False)

print(f"\n✅ Baseline salvo em: {OUTPUT_PATH}")
print(baseline.describe().to_string())
