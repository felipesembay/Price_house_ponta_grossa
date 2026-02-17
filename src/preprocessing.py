"""
Pré-processamento de dados para o modelo de regressão
Limpeza, transformação e feature engineering
"""

import logging
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PreprocessadorDados:
    """
    Realiza limpeza e preparação dos dados para modelagem
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df_original = df.copy()
    
    def limpar_preco(self) -> pd.DataFrame:
        """
        Limpa a coluna de preço
        Remove caracteres especiais e converte para float
        """
        try:
            # Verificar se a coluna é string ou já é numérica
            if self.df['preco'].dtype == 'object':
                self.df['preco_numerico'] = (
                    self.df['preco']
                    .str.replace('R$', '')
                    .str.replace('.', '')
                    .str.replace(',', '.')
                    .astype(float)
                )
            else:
                # Se já é numérico, usar diretamente
                self.df['preco_numerico'] = self.df['preco'].astype(float)
            logger.info("Preços convertidos com sucesso")
        except Exception as e:
            logger.error(f"Erro ao limpar preços: {e}")
        
        return self.df
    
    def remover_outliers(self, coluna: str, metodo: str = 'iqr') -> pd.DataFrame:
        """
        Remove outliers usando IQR ou desvio padrão
        """
        if metodo == 'iqr':
            Q1 = self.df[coluna].quantile(0.25)
            Q3 = self.df[coluna].quantile(0.75)
            IQR = Q3 - Q1
            
            limite_inferior = Q1 - 1.5 * IQR
            limite_superior = Q3 + 1.5 * IQR
            
            tamanho_antes = len(self.df)
            self.df = self.df[
                (self.df[coluna] >= limite_inferior) & 
                (self.df[coluna] <= limite_superior)
            ]
            
            removidos = tamanho_antes - len(self.df)
            logger.info(f"Removidos {removidos} outliers de {coluna}")
        
        return self.df
    
    def tratar_valores_faltantes(self) -> pd.DataFrame:
        """
        Trata valores faltantes nas colunas
        """
        # Para área, quartos e banheiros, preenchemos com a mediana
        colunas_numericas = ['area_m2', 'quartos', 'banheiros']
        
        for coluna in colunas_numericas:
            if coluna in self.df.columns:
                mediana = self.df[coluna].median()
                self.df[coluna].fillna(mediana, inplace=True)
                logger.info(f"Valores faltantes de {coluna} preenchidos com mediana")
        
        # Remover linhas com preço ausente
        self.df = self.df.dropna(subset=['preco_numerico'])
        logger.info(f"Linhas com preço ausente removidas")
        
        return self.df
    
    def engenharia_features(self) -> pd.DataFrame:
        """
        Cria novas features para melhorar o modelo
        """
        # Preço por metro quadrado
        self.df['preco_por_m2'] = self.df['preco_numerico'] / self.df['area_m2']
        
        # Proporção de banheiros por quarto
        self.df['banheiro_por_quarto'] = (
            self.df['banheiros'] / (self.df['quartos'] + 1)
        )
        
        # Classificação de tamanho
        def classificar_tamanho(area):
            if area < 50:
                return 'muito_pequeno'
            elif area < 100:
                return 'pequeno'
            elif area < 150:
                return 'medio'
            elif area < 250:
                return 'grande'
            else:
                return 'muito_grande'
        
        self.df['tamanho_imovel'] = self.df['area_m2'].apply(classificar_tamanho)
        
        logger.info("Features de engenharia criadas")
        return self.df
    
    def codificar_categoricas(self) -> pd.DataFrame:
        """
        Codifica variáveis categóricas
        """
        from sklearn.preprocessing import LabelEncoder
        
        colunas_categoricas = ['tamanho_imovel']
        
        for coluna in colunas_categoricas:
            if coluna in self.df.columns:
                le = LabelEncoder()
                self.df[f'{coluna}_encoded'] = le.fit_transform(
                    self.df[coluna].astype(str)
                )
        
        logger.info("Variáveis categóricas codificadas")
        return self.df
    
    def pipeline_completo(self) -> Tuple[pd.DataFrame, dict]:
        """
        Executa todo o pipeline de pré-processamento
        """
        logger.info("Iniciando pipeline de pré-processamento")
        
        # Limpeza de preço
        self.limpar_preco()
        
        # Tratamento de valores faltantes
        self.tratar_valores_faltantes()
        
        # Remoção de outliers
        self.remover_outliers('preco_numerico')
        self.remover_outliers('area_m2')
        
        # Engenharia de features
        self.engenharia_features()
        
        # Codificação de categóricas
        self.codificar_categoricas()
        
        # Estatísticas de limpeza
        stats = {
            'tamanho_original': len(self.df_original),
            'tamanho_final': len(self.df),
            'linhas_removidas': len(self.df_original) - len(self.df),
            'taxa_remocao': (len(self.df_original) - len(self.df)) / len(self.df_original) * 100
        }
        
        logger.info(f"Pipeline concluído. {stats['linhas_removidas']} linhas removidas")
        
        return self.df, stats


def main():
    """
    Função principal para teste do preprocessador
    """
    # Carregar dados
    df = pd.read_csv('data/raw/imoveis_guarapuava.csv')
    
    # Aplicar preprocessamento
    preprocessador = PreprocessadorDados(df)
    df_limpo, stats = preprocessador.pipeline_completo()
    
    # Salvar dados processados
    df_limpo.to_csv('data/processed/imoveis_guarapuava_processados.csv', index=False)
    
    print("\n" + "="*60)
    print("ESTATÍSTICAS DE PRÉ-PROCESSAMENTO")
    print("="*60)
    for chave, valor in stats.items():
        print(f"{chave}: {valor}")
    
    print("\nDados processados salvos em: data/processed/imoveis_guarapuava_processados.csv")


if __name__ == "__main__":
    main()
