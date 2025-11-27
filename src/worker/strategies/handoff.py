"""
Strategy para workflows de Handoff.

Implementa transições explícitas entre agentes,
onde um agente pode "passar a bola" para outro.

Padrão Microsoft Agent Framework:
    - Usa HandoffBuilder com participants e set_coordinator
    - Ferramentas handoff_to_X são geradas automaticamente
    - Suporta single-tier (default) e multi-tier routing
    - Condição de término personalizável

Referência: agent_framework/_workflows/_handoff.py
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
    - Ferramentas de handoff (handoff_to_X) geradas automaticamente
    - Single-tier por default: coordinator → specialist → user
    - Multi-tier opcional: specialist → specialist via add_handoff
    
    Exemplo de Config:
        ```yaml
        workflow:
          type: handoff
          start_step: coordinator
          termination_condition: "goodbye"  # Opcional
          steps:
            - id: coordinator
              type: agent
              agent: coordinator_agent
              transitions: [specialist1, specialist2]  # Multi-tier routing
            - id: specialist1
              type: agent
              agent: tech_specialist
              transitions: [coordinator]  # Opcional: permite retorno
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
        
        # 1. Criar mapa de step_id -> agente
        step_agents: Dict[str, Any] = {}
        steps = getattr(config, 'steps', [])
        
        for i, step in enumerate(steps):
            if i < len(agents):
                step_agents[step.id] = agents[i]
        
        # 2. Criar builder com participants
        # API correta: HandoffBuilder(participants=[...])
        builder = HandoffBuilder(
            name=getattr(config, 'name', 'handoff_workflow'),
            participants=agents,
        )
        
        # 3. Definir coordenador (start_step)
        start_step_id = getattr(config, 'start_step', None)
        
        if start_step_id and start_step_id in step_agents:
            # API correta: set_coordinator(agent_name ou agent)
            coordinator = step_agents[start_step_id]
            coordinator_name = getattr(coordinator, 'name', start_step_id)
            builder.set_coordinator(coordinator_name)
            self._log(f"Coordenador definido: {coordinator_name}")
        elif agents:
            # Fallback: primeiro agente é coordenador
            first_agent = agents[0]
            first_name = getattr(first_agent, 'name', 'coordinator')
            builder.set_coordinator(first_name)
            self._log(f"Coordenador não especificado, usando: {first_name}", "warning")
        
        # 4. Configurar transições multi-tier (opcional)
        # API correta: add_handoff(source, targets)
        transitions_configured = 0
        for step in steps:
            transitions = getattr(step, 'transitions', None)
            if transitions:
                source_agent = step_agents.get(step.id)
                # Converter IDs para agentes
                targets = [step_agents[t] for t in transitions if t in step_agents]
                
                if source_agent and targets:
                    try:
                        builder.add_handoff(source_agent, targets)
                        transitions_configured += 1
                        self._log(f"  Handoff: {step.id} → {transitions}")
                    except AttributeError:
                        # Se add_handoff não existir, ferramentas são auto-registradas
                        self._log(f"  Auto-handoff habilitado para {step.id}")
        
        if transitions_configured > 0:
            self._log(f"Configuradas {transitions_configured} regras de transição multi-tier")
        else:
            self._log("Usando single-tier routing (default)")
        
        # 5. Condição de término (opcional)
        term_condition = getattr(config, 'termination_condition', None)
        if term_condition:
            check_fn = self._create_termination_condition(term_condition)
            builder.with_termination_condition(check_fn)
            self._log(f"Condição de término: '{term_condition}'")
        
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
        
        return errors
