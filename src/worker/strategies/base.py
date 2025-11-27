"""
Classe base para Workflow Strategies.

Define a interface comum e utilitários compartilhados
por todas as estratégias de construção de workflow.
"""

from abc import abstractmethod
import logging
from typing import Any, Dict, List, Optional

from src.worker.interfaces import WorkflowStrategy


class BaseWorkflowStrategy(WorkflowStrategy):
    """
    Implementação base para strategies de workflow.
    
    Fornece:
    - Validação comum
    - Utilitários para criação de agentes
    - Logging estruturado
    """
    
    def __init__(self):
        self._validation_errors: List[str] = []
    
    @property
    @abstractmethod
    def workflow_type(self) -> str:
        """Tipo de workflow que esta strategy constrói."""
        ...
    
    @abstractmethod
    def build(
        self,
        agents: List[Any],
        config: Any,
        agent_factory: Any
    ) -> Any:
        """Constrói o workflow."""
        ...
    
    def validate(self, config: Any) -> List[str]:
        """
        Valida a configuração do workflow.
        
        Override em subclasses para validações específicas.
        
        Args:
            config: WorkflowConfig a validar
            
        Returns:
            Lista de erros (vazia se válido)
        """
        errors = []
        
        # Validação básica: deve ter steps
        if not hasattr(config, 'steps') or not config.steps:
            errors.append("Workflow deve ter pelo menos um step definido")
        
        return errors
    
    def _log(self, message: str, level: str = "info") -> None:
        """
        Log estruturado para a strategy.
        
        Args:
            message: Mensagem a logar
            level: Nível (info, warning, error)
        """
        msg = f"[{self.workflow_type}] {message}"
        if level == "error":
            logging.error(msg)
        elif level == "warning":
            logging.warning(msg)
        else:
            logging.info(msg)
    
    def _create_termination_condition(self, term_condition: str):
        """
        Cria função de verificação de término.
        
        Args:
            term_condition: Palavra/frase que indica término
            
        Returns:
            Função de verificação
        """
        term_cond_lower = term_condition.lower()
        
        def check_termination(messages: List[Any]) -> bool:
            for msg in reversed(messages):
                content = getattr(msg, 'text', '') or getattr(msg, 'content', '')
                if content and term_cond_lower in str(content).lower():
                    return True
            return False
        
        return check_termination
    
    def _extract_message_content(self, output: Any) -> str:
        """
        Extrai conteúdo textual de diferentes formatos de output.
        
        Args:
            output: Output do agente (pode ser ChatMessage, list, etc.)
            
        Returns:
            String com o conteúdo
        """
        val = output
        
        # Se for lista
        if isinstance(val, list) and val:
            last = val[-1]
            val = getattr(last, 'text', '') or getattr(last, 'content', '') or str(last)
        
        # Se for AgentExecutorResponse
        if hasattr(output, 'agent_run_response'):
            val = output.agent_run_response
        
        # Se for AgentRunResponse
        if hasattr(val, 'value') and val.value is not None:
            val = val.value
        elif hasattr(val, 'messages') and val.messages:
            last_msg = val.messages[-1]
            if hasattr(last_msg, 'content'):
                val = last_msg.content
            elif hasattr(last_msg, 'text'):
                val = last_msg.text
            else:
                val = str(last_msg)
        elif hasattr(val, 'content'):
            val = val.content
        elif hasattr(val, 'text'):
            val = val.text
        
        return str(val) if val else ""
