"""
Script para unir todos os arquivos CSV de páginas individuais em um único DataFrame
"""

import pandas as pd
from pathlib import Path
import glob
import re


def unir_arquivos_por_cidade(cidade: str, estado: str, diretorio: str = ".") -> pd.DataFrame:
    """
    Une todos os arquivos CSV de uma cidade específica
    
    Args:
        cidade: Nome da cidade
        estado: Sigla do estado
        diretorio: Diretório onde estão os arquivos (padrão: diretório atual)
        
    Returns:
        DataFrame com todos os dados unidos
    """
    # Caminho base - usar diretório atual se não especificado
    base_path = Path(diretorio).resolve()
    
    # Padrão de busca: cidade_estado_paginaN.csv
    pattern = f"{cidade}_{estado}_pagina*.csv"
    arquivos = sorted(base_path.glob(pattern))
    
    if not arquivos:
        print(f"⚠️  Nenhum arquivo encontrado para {cidade}/{estado}")
        print(f"   Padrão de busca: {pattern}")
        print(f"   Diretório: {base_path}")
        return pd.DataFrame()
    
    print(f"📁 Encontrados {len(arquivos)} arquivos para {cidade.title()}/{estado.upper()}")
    print(f"   Diretório: {base_path}\n")
    
    # Ler e unir todos os arquivos
    dfs = []
    for arquivo in arquivos:
        try:
            df = pd.read_csv(arquivo)
            # Extrair número da página do nome do arquivo
            match = re.search(r'pagina(\d+)', arquivo.name)
            pagina_num = int(match.group(1)) if match else 0
            
            print(f"   ✓ {arquivo.name}: {len(df)} imóveis")
            dfs.append(df)
        except Exception as e:
            print(f"   ✗ Erro ao ler {arquivo.name}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    
    # Concatenar todos os DataFrames
    df_completo = pd.concat(dfs, ignore_index=True)
    
    # Remover duplicatas baseado no link
    if 'link' in df_completo.columns:
        antes = len(df_completo)
        df_completo = df_completo.drop_duplicates(subset=['link'], keep='first')
        depois = len(df_completo)
        
        if antes != depois:
            print(f"\n🔄 Removidas {antes - depois} duplicatas")
    
    return df_completo


def unir_todos_arquivos(diretorio: str = ".") -> pd.DataFrame:
    """
    Une TODOS os arquivos CSV do diretório, independente da cidade
    
    Args:
        diretorio: Diretório onde estão os arquivos (padrão: diretório atual)
        
    Returns:
        DataFrame com todos os dados unidos
    """
    # Caminho base - usar diretório atual se não especificado
    base_path = Path(diretorio).resolve()
    
    # Buscar todos os arquivos CSV com padrão cidade_estado_paginaN.csv
    arquivos = sorted(base_path.glob("*_pagina*.csv"))
    
    if not arquivos:
        print(f"⚠️  Nenhum arquivo encontrado em {base_path}")
        print(f"   Padrão de busca: *_pagina*.csv")
        return pd.DataFrame()
    
    print(f"📁 Encontrados {len(arquivos)} arquivos no total")
    print(f"   Diretório: {base_path}\n")
    
    # Ler e unir todos os arquivos
    dfs = []
    for arquivo in arquivos:
        try:
            df = pd.read_csv(arquivo)
            print(f"   ✓ {arquivo.name}: {len(df)} imóveis")
            dfs.append(df)
        except Exception as e:
            print(f"   ✗ Erro ao ler {arquivo.name}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    
    # Concatenar todos os DataFrames
    df_completo = pd.concat(dfs, ignore_index=True)
    
    # Remover duplicatas baseado no link
    if 'link' in df_completo.columns:
        antes = len(df_completo)
        df_completo = df_completo.drop_duplicates(subset=['link'], keep='first')
        depois = len(df_completo)
        
        if antes != depois:
            print(f"\n🔄 Removidas {antes - depois} duplicatas")
    
    return df_completo


def salvar_arquivo_unido(df: pd.DataFrame, cidade: str = None, estado: str = None):
    """
    Salva o DataFrame unido em um arquivo CSV
    
    Args:
        df: DataFrame a ser salvo
        cidade: Nome da cidade (opcional)
        estado: Sigla do estado (opcional)
    """
    if df.empty:
        print("⚠️  DataFrame vazio, nada para salvar")
        return
    
    # Salvar no diretório pai (sair de por_pagina/)
    output_dir = Path.cwd().parent
    
    # Nome do arquivo
    if cidade and estado:
        nome_arquivo = f"imoveis_{cidade}_{estado}_completo.csv"
    else:
        nome_arquivo = "imoveis_todos_completo.csv"
    
    caminho = output_dir / nome_arquivo
    
    # Salvar
    df.to_csv(caminho, index=False, encoding='utf-8')
    print(f"\n✅ Arquivo salvo: {caminho}")
    print(f"   Total de imóveis: {len(df)}")


def main():
    """
    Função principal com menu interativo
    """
    print("="*60)
    print("UNIR ARQUIVOS CSV - ZAPIMOVEIS")
    print("="*60)
    
    print("\nOpções:")
    print("1. Unir arquivos de uma cidade específica")
    print("2. Unir TODOS os arquivos")
    
    opcao = input("\nEscolha uma opção (1 ou 2): ").strip()
    
    if opcao == "1":
        cidade = input("\n📍 Digite o nome da cidade: ").strip().lower()
        estado = input("📍 Digite a sigla do estado: ").strip().lower()
        
        print(f"\n🔄 Unindo arquivos de {cidade.title()}/{estado.upper()}...")
        df = unir_arquivos_por_cidade(cidade, estado)
        
        if not df.empty:
            print("\n" + "="*60)
            print("RESUMO DOS DADOS")
            print("="*60)
            print(df.info())
            print("\nPrimeiros registros:")
            print(df.head())
            
            salvar_arquivo_unido(df, cidade, estado)
    
    elif opcao == "2":
        print("\n🔄 Unindo TODOS os arquivos...")
        df = unir_todos_arquivos()
        
        if not df.empty:
            print("\n" + "="*60)
            print("RESUMO DOS DADOS")
            print("="*60)
            print(df.info())
            print("\nPrimeiros registros:")
            print(df.head())
            
            # Mostrar estatísticas por cidade
            if 'cidade' in df.columns and 'estado' in df.columns:
                print("\n📊 Imóveis por cidade:")
                contagem = df.groupby(['cidade', 'estado']).size().reset_index(name='quantidade')
                print(contagem.to_string(index=False))
            
            salvar_arquivo_unido(df)
    
    else:
        print("❌ Opção inválida")


if __name__ == "__main__":
    main()
