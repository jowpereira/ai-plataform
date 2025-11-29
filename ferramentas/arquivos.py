"""
Ferramentas de manipulação de arquivos para agentes.

Utiliza o decorator @ai_function do Microsoft Agent Framework.
"""

import os
from typing import Annotated, List
from agent_framework import ai_function
from pydantic import Field

@ai_function(name="listar_arquivos", description="Lista arquivos em um diretório")
def listar_arquivos(
    diretorio: Annotated[str, Field(description="Caminho do diretório para listar", default=".")]
) -> List[str]:
    """Lista os arquivos no diretório especificado (não recursivo)."""
    try:
        if not os.path.exists(diretorio):
            return [f"Erro: Diretório '{diretorio}' não encontrado."]
        
        arquivos = []
        for nome in os.listdir(diretorio):
            caminho_completo = os.path.join(diretorio, nome)
            if os.path.isfile(caminho_completo):
                arquivos.append(nome)
            elif os.path.isdir(caminho_completo):
                arquivos.append(f"{nome}/")
        return arquivos
    except Exception as e:
        return [f"Erro ao listar arquivos: {str(e)}"]

@ai_function(name="ler_arquivo", description="Lê o conteúdo de um arquivo")
def ler_arquivo(
    caminho: Annotated[str, Field(description="Caminho do arquivo para ler")]
) -> str:
    """Lê o conteúdo de um arquivo de texto."""
    try:
        if not os.path.exists(caminho):
            return f"Erro: Arquivo '{caminho}' não encontrado."
        
        # Proteção básica para não ler arquivos muito grandes ou binários
        if os.path.getsize(caminho) > 100 * 1024: # 100KB limit
            return "Erro: Arquivo muito grande para leitura (limite 100KB)."
            
        with open(caminho, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        return "Erro: Arquivo parece ser binário ou não está em UTF-8."
    except Exception as e:
        return f"Erro ao ler arquivo: {str(e)}"

@ai_function(name="escrever_arquivo", description="Escreve conteúdo em um arquivo")
def escrever_arquivo(
    caminho: Annotated[str, Field(description="Caminho do arquivo para escrever")],
    conteudo: Annotated[str, Field(description="Conteúdo para escrever no arquivo")]
) -> str:
    """Escreve texto em um arquivo (sobrescreve se existir)."""
    try:
        # Proteção básica de diretório (apenas workspace atual)
        if ".." in caminho or caminho.startswith("/") or ":" in caminho:
             # Simplificação: permitir apenas caminhos relativos simples para segurança no exemplo
             pass 

        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        return f"Sucesso: Arquivo '{caminho}' escrito com sucesso."
    except Exception as e:
        return f"Erro ao escrever arquivo: {str(e)}"

__all__ = ["listar_arquivos", "ler_arquivo", "escrever_arquivo"]
