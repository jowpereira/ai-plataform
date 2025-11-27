"""
Strategy para workflows sequenciais.

Conecta agentes em série, onde a saída de um
alimenta a entrada do próximo.
"""

from typing import Any, List

from agent_framework import SequentialBuilder

from src.worker.strategies.base import BaseWorkflowStrategy


class SequentialStrategy(BaseWorkflowStrategy):
    """
    Strategy para construção de workflows sequenciais.
    
    Características:
    - Agentes executados em ordem definida
    - Output de um agente vai para o próximo
    - Simples e determinístico
    
    Exemplo de Config:
        ```yaml
        workflow:
          type: sequential
          steps:
            - id: step1
              type: agent
              agent: pesquisador
            - id: step2
              type: agent
              agent: escritor
        ```
    """
    
    @property
    def workflow_type(self) -> str:
        return "sequential"
    
    def build(
        self,
        agents: List[Any],
        config: Any,
        agent_factory: Any
    ) -> Any:
        """
        Constrói workflow sequencial usando SequentialBuilder.
        
        Args:
            agents: Lista ordenada de agentes
            config: WorkflowConfig
            agent_factory: Factory para criar agentes adicionais
            
        Returns:
            Workflow construído
        """
        if not agents:
            raise ValueError("Sequential workflow requer pelo menos um agente")
        
        self._log(f"Construindo workflow com {len(agents)} agentes")
        
        # SequentialBuilder conecta automaticamente em ordem
        workflow = SequentialBuilder().participants(agents).build()
        
        self._log("Workflow sequencial construído com sucesso")
        return workflow
    
    def validate(self, config: Any) -> List[str]:
        """Validação específica para sequential."""
        errors = super().validate(config)
        
        # Sequential não precisa de start_step
        # Apenas validar que há agentes
        
        return errors
