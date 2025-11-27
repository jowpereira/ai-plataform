"""
Strategy para workflows de Router.

Implementa roteamento condicional onde um agente
decide para qual especialista encaminhar.

Padrão Microsoft Agent Framework:
    - Usa WorkflowBuilder com add_switch_case_edge_group
    - Executor terminal com @executor decorator
    - Condições via Case/Default

Referência: O framework não tem RouterBuilder dedicado,
então usamos WorkflowBuilder diretamente seguindo o padrão.
"""

from typing import Any, Dict, List

from agent_framework import WorkflowBuilder, Case, Default

from src.worker.strategies.base import BaseWorkflowStrategy
from src.worker.strategies.executors import yield_agent_response


class RouterStrategy(BaseWorkflowStrategy):
    """
    Strategy para construção de workflows de Router.
    
    Características:
    - Agente roteador analisa input e decide destino
    - Output do roteador deve ser o ID do step de destino
    - Suporta múltiplos destinos com case/default
    - Usa @executor funcional (padrão do framework)
    
    Exemplo de Config:
        ```yaml
        workflow:
          type: router
          start_step: classifier
          steps:
            - id: classifier
              type: agent
              agent: classifier_agent
              input_template: "Classifique: {input}. Responda apenas: tech, sales ou support"
            - id: tech
              type: agent
              agent: tech_support
            - id: sales
              type: agent
              agent: sales_team
            - id: support
              type: agent
              agent: general_support
        ```
    """
    
    @property
    def workflow_type(self) -> str:
        return "router"
    
    def build(
        self,
        agents: List[Any],
        config: Any,
        agent_factory: Any
    ) -> Any:
        """
        Constrói workflow de Router usando WorkflowBuilder com switch-case.
        
        Args:
            agents: Lista de agentes (primeiro é o roteador)
            config: WorkflowConfig com start_step
            agent_factory: Factory para criar agentes
            
        Returns:
            Workflow construído
        """
        if not agents:
            raise ValueError("Router workflow requer pelo menos um agente")
        
        steps = getattr(config, 'steps', [])
        start_step_id = getattr(config, 'start_step', None)
        
        if not start_step_id:
            raise ValueError("Router workflow requer 'start_step' definido")
        
        self._log(f"Construindo Router com {len(agents)} agentes")
        
        # 1. Criar mapa step_id -> agente
        step_agents: Dict[str, Any] = {}
        for i, step in enumerate(steps):
            if i < len(agents):
                step_agents[step.id] = agents[i]
        
        # 2. Identificar roteador e destinos
        if start_step_id not in step_agents:
            raise ValueError(f"start_step '{start_step_id}' não encontrado nos steps")
        
        start_agent = step_agents[start_step_id]
        target_steps = [s for s in steps if s.id != start_step_id]
        
        if not target_steps:
            raise ValueError("Router deve ter pelo menos um step de destino")
        
        self._log(f"Roteador: {start_step_id}, Destinos: {[s.id for s in target_steps]}")
        
        # 3. Construir workflow com WorkflowBuilder
        builder = WorkflowBuilder()
        
        # Adicionar agentes
        for agent in step_agents.values():
            builder.add_agent(agent)
        
        # Definir start como o agente roteador
        builder.set_start_executor(start_agent)
        
        # 4. Criar condições de roteamento
        cases = []
        
        # Função factory para criar condições (closure correta)
        def make_condition(target_id: str):
            def condition(output: Any) -> bool:
                val = self._extract_message_content(output)
                # Comparação case-insensitive
                return val.strip().lower() == target_id.lower()
            return condition
        
        # Último step é Default, outros são Cases
        default_step = target_steps[-1]
        other_steps = target_steps[:-1]
        
        for step in other_steps:
            cases.append(Case(
                condition=make_condition(step.id),
                target=step_agents[step.id]
            ))
            self._log(f"  Case: output == '{step.id}' -> {step.id}")
        
        # Default case
        cases.append(Default(target=step_agents[default_step.id]))
        self._log(f"  Default -> {default_step.id}")
        
        # 5. Adicionar arestas switch-case
        builder.add_switch_case_edge_group(start_agent, cases)
        
        # 6. Adicionar edges dos destinos para executor terminal
        # Usa o @executor funcional (padrão do framework)
        for step in target_steps:
            agent = step_agents[step.id]
            builder.add_edge(agent, yield_agent_response)
            self._log(f"  Edge: {step.id} -> workflow_output")
        
        # 7. Construir
        workflow = builder.build()
        
        self._log("Router workflow construído com sucesso")
        return workflow

    
    def validate(self, config: Any) -> List[str]:
        """Validação específica para Router."""
        errors = super().validate(config)
        
        # Verificar start_step
        if not getattr(config, 'start_step', None):
            errors.append("Router workflow requer 'start_step' definido")
        
        # Verificar se há destinos
        steps = getattr(config, 'steps', [])
        start_step = getattr(config, 'start_step', None)
        
        target_count = sum(1 for s in steps if s.id != start_step)
        if target_count < 1:
            errors.append("Router workflow deve ter pelo menos um step de destino")
        
        return errors
