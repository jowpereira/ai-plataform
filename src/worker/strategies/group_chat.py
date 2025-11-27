"""
Strategy para workflows de Group Chat.

Implementa discussão em grupo onde um Manager
seleciona dinamicamente o próximo participante.

Padrão Microsoft Agent Framework:
    - Usa GroupChatBuilder.participants(**kwargs) com nomes e descriptions
    - Manager pode ser ChatAgent ou função de seleção
    - Orquestrador interno gerencia estado e turnos
    - Condição de término e max_rounds para controle de loop

Referência: agent_framework/_workflows/_group_chat.py
"""

from typing import Any, Dict, List

from agent_framework import GroupChatBuilder, ChatMessage, ChatAgent

from src.worker.strategies.base import BaseWorkflowStrategy


class GroupChatStrategy(BaseWorkflowStrategy):
    """
    Strategy para construção de workflows de Group Chat.
    
    Características:
    - Manager LLM seleciona próximo falante
    - Conversa multi-turno entre participantes
    - Condição de término configurável
    - Max rounds para evitar loops infinitos
    
    Exemplo de Config:
        ```yaml
        workflow:
          type: group_chat
          manager_model: gpt-4o
          manager_instructions: "Selecione o especialista mais adequado..."
          max_rounds: 10
          termination_condition: "TASK_COMPLETE"
          steps:
            - id: expert1
              type: agent
              agent: security_expert
            - id: expert2
              type: agent
              agent: performance_expert
        ```
    """
    
    @property
    def workflow_type(self) -> str:
        return "group_chat"
    
    def build(
        self,
        agents: List[Any],
        config: Any,
        agent_factory: Any
    ) -> Any:
        """
        Constrói workflow de Group Chat usando GroupChatBuilder.
        
        Args:
            agents: Lista de agentes participantes
            config: WorkflowConfig com manager_model, manager_instructions, etc.
            agent_factory: Factory para criar o manager
            
        Returns:
            Workflow construído
        """
        if not agents:
            raise ValueError("Group Chat requer pelo menos um agente participante")
        
        self._log(f"Construindo Group Chat com {len(agents)} participantes")
        
        builder = GroupChatBuilder()
        
        # 1. Registrar participantes como kwargs nomeados
        # Padrão do framework: participants(**{name: agent})
        # Isso permite ao manager usar os nomes exatos na seleção
        participants_dict: Dict[str, Any] = {}
        for agent in agents:
            agent_name = getattr(agent, 'name', None) or getattr(agent, 'id', f'agent_{len(participants_dict)}')
            participants_dict[agent_name] = agent
        
        builder.participants(**participants_dict)
        self._log(f"Participantes registrados: {list(participants_dict.keys())}")
        
        # 2. Configurar Manager
        manager_model_id = getattr(config, 'manager_model', None)
        
        # Fallback: usar modelo do primeiro agente se não especificado
        if not manager_model_id:
            self._log("Manager model não especificado, buscando fallback...", "warning")
            # Tentar obter do agent_factory
            if hasattr(agent_factory, 'config') and agent_factory.config.agents:
                manager_model_id = agent_factory.config.agents[0].model
        
        if manager_model_id:
            try:
                # Instruções do manager
                base_instructions = getattr(config, 'manager_instructions', None) or \
                    "Select the next speaker based on the conversation context."
                
                instructions = (
                    f"{base_instructions}\n"
                    "IMPORTANT: You must select the participant by their exact NAME "
                    "(the key in the list), not their description or role."
                )
                
                # Criar cliente para o manager
                client = agent_factory.create_client(manager_model_id)
                
                # Configurar Manager usando ChatAgent (novo padrão)
                manager_agent = ChatAgent(
                    name="GroupManager",
                    description="Orchestrator of the group chat",
                    instructions=instructions,
                    chat_client=client
                )
                
                builder.set_manager(manager_agent)
                
                self._log(f"Manager configurado com modelo: {manager_model_id}")
                
            except Exception as e:
                self._log(f"Falha ao configurar manager: {e}", "error")
                raise
        else:
            raise ValueError("Group Chat requer 'manager_model' definido")
        
        # 3. Condição de Término
        term_condition = getattr(config, 'termination_condition', None)
        if term_condition:
            check_fn = self._create_termination_condition(term_condition)
            builder.with_termination_condition(check_fn)
            self._log(f"Condição de término: '{term_condition}'")
        
        # 4. Max Rounds
        max_rounds = getattr(config, 'max_rounds', 10)
        builder.with_max_rounds(max_rounds)
        self._log(f"Max rounds: {max_rounds}")
        
        # 5. Construir
        workflow = builder.build()
        
        self._log("Group Chat construído com sucesso")
        return workflow
    
    def validate(self, config: Any) -> List[str]:
        """Validação específica para Group Chat."""
        errors = super().validate(config)
        
        # Verificar manager_model (opcional mas recomendado)
        if not getattr(config, 'manager_model', None):
            errors.append(
                "Group Chat sem 'manager_model' usará fallback, "
                "considere especificar explicitamente"
            )
        
        # Verificar se há pelo menos 2 participantes para discussão útil
        if hasattr(config, 'steps') and len(config.steps) < 2:
            errors.append("Group Chat deve ter pelo menos 2 participantes")
        
        return errors
