"""
Strategy para workflows de Handoff.

Implementa transições explícitas entre agentes,
onde um agente pode "passar a bola" para outro.
"""

from typing import Any, Dict, List

from agent_framework import HandoffBuilder

from src.worker.strategies.base import BaseWorkflowStrategy


class HandoffStrategy(BaseWorkflowStrategy):
    """
    Strategy para construção de workflows de Handoff.
    
    Características:
    - Transições explícitas definidas na configuração
    - Agente coordenador inicia o fluxo
    - Ferramentas de handoff registradas automaticamente
    
    Exemplo de Config:
        ```yaml
        workflow:
          type: handoff
          start_step: coordinator
          steps:
            - id: coordinator
              type: agent
              agent: coordinator_agent
              transitions: [specialist1, specialist2]
            - id: specialist1
              type: agent
              agent: tech_specialist
              transitions: [coordinator]
            - id: specialist2
              type: agent
              agent: business_specialist
              transitions: [coordinator]
        ```
    """
    
    @property
    def workflow_type(self) -> str:
        return "handoff"
    
    def build(
        self,
        agents: List[Any],
        config: Any,
        agent_factory: Any
    ) -> Any:
        """
        Constrói workflow de Handoff usando HandoffBuilder.
        
        Args:
            agents: Lista de agentes participantes
            config: WorkflowConfig com start_step e transitions nos steps
            agent_factory: Factory para criar agentes
            
        Returns:
            Workflow construído
        """
        if not agents:
            raise ValueError("Handoff workflow requer pelo menos um agente")
        
        self._log(f"Construindo Handoff com {len(agents)} agentes")
        
        builder = HandoffBuilder()
        
        # 1. Registrar participantes
        builder.participants(agents)
        
        # 2. Habilitar ferramentas automáticas de handoff
        if hasattr(builder, 'auto_register_handoff_tools'):
            builder.auto_register_handoff_tools(True)
            self._log("Ferramentas de handoff registradas automaticamente")
        
        # 3. Criar mapa de step_id -> agente
        step_agents: Dict[str, Any] = {}
        steps = getattr(config, 'steps', [])
        
        for i, step in enumerate(steps):
            if i < len(agents):
                step_agents[step.id] = agents[i]
        
        # 4. Definir coordenador (start_step)
        start_step_id = getattr(config, 'start_step', None)
        
        if start_step_id and start_step_id in step_agents:
            coordinator = step_agents[start_step_id]
            builder.set_coordinator(coordinator)
            self._log(f"Coordenador definido: {start_step_id}")
        elif agents:
            # Fallback: primeiro agente é coordenador
            builder.set_coordinator(agents[0])
            self._log("Coordenador não especificado, usando primeiro agente", "warning")
        
        # 5. Configurar transições
        transitions_configured = 0
        for step in steps:
            transitions = getattr(step, 'transitions', None)
            if transitions:
                source_agent = step_agents.get(step.id)
                targets = [step_agents[t] for t in transitions if t in step_agents]
                
                if source_agent and targets:
                    builder.add_handoff(source_agent, targets)
                    transitions_configured += 1
        
        self._log(f"Configuradas {transitions_configured} regras de transição")
        
        # 6. Construir
        workflow = builder.build()
        
        self._log("Handoff workflow construído com sucesso")
        return workflow
    
    def validate(self, config: Any) -> List[str]:
        """Validação específica para Handoff."""
        errors = super().validate(config)
        
        # Verificar start_step
        if not getattr(config, 'start_step', None):
            errors.append(
                "Handoff workflow deve ter 'start_step' definido "
                "(ID do agente coordenador)"
            )
        
        # Verificar se há transições definidas
        steps = getattr(config, 'steps', [])
        has_transitions = any(
            getattr(step, 'transitions', None) for step in steps
        )
        if not has_transitions:
            errors.append(
                "Handoff workflow deve ter pelo menos uma transição definida "
                "nos steps (campo 'transitions')"
            )
        
        return errors
