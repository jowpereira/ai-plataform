"""
Implementação base para LLM Providers.

Fornece funcionalidade comum que pode ser reutilizada
por providers específicos.
"""

import os
from typing import Any, Dict, List, Optional

from src.worker.interfaces import LLMProvider, ProviderType


class BaseLLMProvider(LLMProvider):
    """
    Classe base para providers de LLM.
    
    Fornece implementações padrão para métodos comuns
    e utilitários para configuração de ambiente.
    """
    
    def __init__(self):
        self._env_backup: Dict[str, Optional[str]] = {}
    
    @property
    def supported_models(self) -> List[str]:
        """Por padrão, aceita qualquer modelo."""
        return []
    
    def _apply_env_vars(self, env_vars: Optional[Dict[str, str]]) -> None:
        """
        Aplica variáveis de ambiente temporárias.
        
        Guarda os valores originais para restauração posterior.
        
        Args:
            env_vars: Mapeamento de variáveis a aplicar
        """
        if not env_vars:
            return
            
        for key, value in env_vars.items():
            # Backup do valor original
            self._env_backup[key] = os.environ.get(key)
            # Aplicar novo valor
            os.environ[key] = value
    
    def _restore_env_vars(self) -> None:
        """Restaura variáveis de ambiente aos valores originais."""
        for key, original_value in self._env_backup.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value
        self._env_backup.clear()
    
    def validate_required_env(self, required_vars: List[str]) -> List[str]:
        """
        Valida se as variáveis de ambiente necessárias estão definidas.
        
        Args:
            required_vars: Lista de nomes de variáveis obrigatórias
            
        Returns:
            Lista de variáveis faltantes (vazia se todas presentes)
        """
        missing = []
        for var in required_vars:
            if not os.environ.get(var):
                missing.append(var)
        return missing
    
    def health_check(self) -> bool:
        """
        Verifica se o provider está configurado corretamente.
        
        Override em implementações específicas para fazer
        verificações mais elaboradas (ex: testar conexão).
        """
        return True
