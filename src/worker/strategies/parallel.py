"""
Strategy para workflows paralelos.

Executa múltiplos agentes simultaneamente e
agrega os resultados.
"""

from typing import Any, List

from agent_framework import ConcurrentBuilder

from src.worker.strategies.base import BaseWorkflowStrategy


class ParallelStrategy(BaseWorkflowStrategy):
    """
    Strategy para construção de workflows paralelos (fan-out/fan-in).
    
    Características:
    - Todos os agentes recebem o mesmo input
    - Executados concorrentemente
    - Resultados agregados ao final
    
    Exemplo de Config:
        ```yaml
        workflow:
          type: parallel
          steps:
            - id: analyst1
              type: agent
              agent: financial_analyst
            - id: analyst2
              type: agent
              agent: market_analyst
            - id: analyst3
              type: agent
              agent: risk_analyst
        ```
    """
    
    @property
    def workflow_type(self) -> str:
        return "parallel"
    
    def build(
        self,
        agents: List[Any],
        config: Any,
        agent_factory: Any
    ) -> Any:
        """
        Constrói workflow paralelo usando ConcurrentBuilder.
        
        Args:
            agents: Lista de agentes a executar em paralelo
            config: WorkflowConfig
            agent_factory: Factory para criar agentes adicionais
            
        Returns:
            Workflow construído
        """
        if not agents:
            raise ValueError("Parallel workflow requer pelo menos um agente")
        
        if len(agents) < 2:
            self._log(
                "Parallel workflow com apenas 1 agente é equivalente a sequential",
                "warning"
            )
        
        self._log(f"Construindo workflow com {len(agents)} agentes em paralelo")
        
        # ConcurrentBuilder cria dispatcher e aggregator automaticamente
        workflow = ConcurrentBuilder().participants(agents).build()
        
        self._log("Workflow paralelo construído com sucesso")
        return workflow
    
    def validate(self, config: Any) -> List[str]:
        """Validação específica para parallel."""
        errors = super().validate(config)
        
        # Idealmente, parallel deve ter 2+ agentes
        if hasattr(config, 'steps') and len(config.steps) < 2:
            errors.append("Parallel workflow deve ter pelo menos 2 agentes para ser efetivo")
        
        return errors
