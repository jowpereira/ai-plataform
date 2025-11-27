"""
Strategy para workflows Magentic One.

Implementa orquestração avançada com:
- Planejamento dinâmico via LLM
- Task Ledger para tracking de fatos
- Replanning adaptativo
- Revisão humana opcional do plano
"""

from typing import Any, List, Optional

from agent_framework import ChatAgent
from agent_framework._workflows import MagenticBuilder

from src.worker.strategies.base import BaseWorkflowStrategy


class MagenticStrategy(BaseWorkflowStrategy):
    """
    Strategy para construção de workflows Magentic One.
    
    Magentic One é um orquestrador AI-driven que:
    1. Analisa a tarefa e extrai fatos relevantes
    2. Cria um plano de execução dinâmico
    3. Seleciona agentes baseado no progresso
    4. Replana quando encontra obstáculos
    5. Permite revisão humana do plano (opcional)
    
    Ideal para:
    - Tarefas complexas que requerem múltiplos especialistas
    - Cenários onde o caminho não é determinístico
    - Workflows que precisam adaptar-se a resultados intermediários
    
    Exemplo de Config:
        ```yaml
        workflow:
          type: magentic
          manager_model: gpt-4o
          max_rounds: 20
          max_stall_count: 3
          enable_plan_review: false
          manager_instructions: "Você é um coordenador de equipe..."
          steps:
            - id: researcher
              type: agent
              agent: research_agent
            - id: writer
              type: agent
              agent: writing_agent
            - id: reviewer
              type: agent
              agent: review_agent
        ```
    
    Diferença do GroupChat:
    - GroupChat: Manager seleciona próximo falante, conversa livre
    - Magentic: Manager planeja execução, tracking de progresso, replanning
    """
    
    @property
    def workflow_type(self) -> str:
        return "magentic"
    
    def build(
        self,
        agents: List[Any],
        config: Any,
        agent_factory: Any
    ) -> Any:
        """
        Constrói workflow Magentic One.
        
        Args:
            agents: Lista de agentes participantes
            config: WorkflowConfig com configurações do manager
            agent_factory: Factory para criar clientes LLM
            
        Returns:
            Workflow Magentic construído
        """
        if not agents:
            raise ValueError("Magentic requer pelo menos um agente participante")
        
        self._log(f"Construindo Magentic com {len(agents)} participantes")
        
        builder = MagenticBuilder()
        
        # 1. Registrar participantes como kwargs nomeados
        # O MagenticBuilder espera participants como keyword args
        participants_dict = {}
        for agent in agents:
            # Usar o name ou id do agente como chave
            agent_name = getattr(agent, 'name', None) or getattr(agent, 'id', f'agent_{len(participants_dict)}')
            participants_dict[agent_name] = agent
        
        builder.participants(**participants_dict)
        self._log(f"Participantes registrados: {list(participants_dict.keys())}")
        
        # 2. Configurar Manager
        manager_model_id = getattr(config, 'manager_model', None)
        if not manager_model_id:
            # Fallback: usar modelo do primeiro agente
            if hasattr(agent_factory, 'config') and agent_factory.config.agents:
                manager_model_id = agent_factory.config.agents[0].model
                self._log(f"Usando modelo fallback: {manager_model_id}", "warning")
        
        if not manager_model_id:
            raise ValueError("Magentic requer 'manager_model' definido")
        
        try:
            # Criar cliente LLM para o manager
            chat_client = agent_factory.create_client(manager_model_id)
            
            # Parâmetros do manager
            max_round_count = getattr(config, 'max_rounds', 20)
            max_stall_count = getattr(config, 'max_stall_count', 3)
            instructions = getattr(config, 'manager_instructions', None)
            
            # Usar with_standard_manager
            builder.with_standard_manager(
                chat_client=chat_client,
                instructions=instructions,
                max_round_count=max_round_count,
                max_stall_count=max_stall_count,
            )
            
            self._log(f"Manager configurado: model={manager_model_id}, max_rounds={max_round_count}")
            
        except Exception as e:
            self._log(f"Falha ao configurar manager: {e}", "error")
            raise
        
        # 3. Revisão de Plano (opcional)
        enable_plan_review = getattr(config, 'enable_plan_review', False)
        if enable_plan_review:
            builder.with_plan_review(enable=True)
            self._log("Revisão de plano habilitada")
        
        # 4. Checkpointing (se configurado)
        checkpoint_storage = getattr(config, 'checkpoint_storage', None)
        if checkpoint_storage:
            builder.with_checkpointing(checkpoint_storage)
            self._log("Checkpointing habilitado")
        
        # 5. Construir
        workflow = builder.build()
        
        self._log("Magentic workflow construído com sucesso")
        return workflow
    
    def validate(self, config: Any) -> List[str]:
        """Validação específica para Magentic."""
        errors = super().validate(config)
        
        # Manager model é obrigatório
        if not getattr(config, 'manager_model', None):
            errors.append("Magentic requer 'manager_model' definido")
        
        # Verificar se há participantes suficientes
        if hasattr(config, 'steps') and len(config.steps) < 2:
            errors.append(
                "Magentic é mais efetivo com 2+ participantes. "
                "Para agente único, considere usar 'sequential'"
            )
        
        # Avisar sobre max_rounds baixo
        max_rounds = getattr(config, 'max_rounds', 20)
        if max_rounds < 5:
            errors.append(
                f"max_rounds={max_rounds} pode ser insuficiente "
                "para tarefas complexas. Considere aumentar para 10+"
            )
        
        return errors
