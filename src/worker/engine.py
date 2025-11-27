import json
import logging
import os
import uuid
from typing import Any, Dict, Optional, List

from agent_framework import Workflow, ChatAgent, ChatMessage

from src.worker.config import WorkerConfig
from src.worker.factory import AgentFactory
from src.worker.middleware import EnhancedTemplateMiddleware
from src.worker.agents import HumanAgent
from src.worker.strategies import StrategyRegistry, get_strategy_registry
from src.worker.events import SimpleEventBus, get_event_bus, WorkerEventType
from src.worker.state import WorkflowStateManager


class WorkflowEngine:
    """
    Motor de execução de workflows.
    
    Usa StrategyRegistry para construção desacoplada de workflows
    e EventBus para observabilidade.
    """
    
    def __init__(self, config: WorkerConfig, event_bus: Optional[SimpleEventBus] = None):
        self.config = config
        self.agent_factory = AgentFactory(config)
        self._workflow: Optional[Workflow] = None
        self._event_bus = event_bus or get_event_bus()
        self._strategy_registry = get_strategy_registry()
        self.state_manager: Optional[WorkflowStateManager] = None

    @property
    def event_bus(self) -> SimpleEventBus:
        """Retorna o EventBus para inscrição de hooks externos."""
        return self._event_bus

    def _emit(self, event_type: WorkerEventType, data: Optional[Dict[str, Any]] = None) -> None:
        """Emite evento se o bus estiver configurado."""
        if self._event_bus:
            self._event_bus.emit_simple(event_type, data or {})

    def setup(self) -> None:
        """Inicializa recursos, estado e constrói o workflow."""
        self.state_manager = WorkflowStateManager(execution_id=str(uuid.uuid4()))
        self.build()
        self.state_manager.set_status("initialized")

    def teardown(self) -> None:
        """Limpa recursos após execução."""
        # Aqui poderíamos fechar conexões de banco, clientes HTTP, etc.
        pass

    def build(self):
        """Constrói o objeto Workflow baseado na configuração usando strategies."""
        self._emit(WorkerEventType.SETUP_START, {"workflow_type": self.config.workflow.type})
        
        steps = self.config.workflow.steps
        workflow_type = self.config.workflow.type
        
        # TODO: Reativar DAG quando validação estiver pronta
        if workflow_type == "dag":
            raise NotImplementedError(
                "DAG mode temporarily disabled. Use high-level builders: "
                "sequential, parallel, group_chat, handoff, router."
            )
        
        # 1. Criar todos os agentes
        step_agents = {}
        ordered_agents = []
        
        for step in steps:
            agent = None
            if step.type == "agent":
                if not step.agent:
                    raise ValueError(f"Passo {step.id} do tipo 'agent' deve ter um 'agent' definido.")
                
                # Criar middleware de template se necessário
                middleware = []
                if step.input_template:
                    middleware.append(EnhancedTemplateMiddleware(step.input_template))
                
                # Criar agente com middleware
                agent = self.agent_factory.create_agent(str(step.agent), middleware=middleware)
                
            elif step.type == "human":
                # Criar agente humano
                # Determinar modo de confirmação (pode vir de config global ou do step se suportado)
                # Por enquanto, vamos assumir CLI como padrão ou checar variável de ambiente
                mode = "cli"
                if os.getenv("DEVUI_MODE"):
                    mode = "structured"
                
                agent = HumanAgent(
                    id=step.id, 
                    instructions=step.input_template,
                    confirmation_mode=mode
                )
            
            if agent:
                step_agents[step.id] = agent
                ordered_agents.append(agent)

        # 2. Validar configuração
        errors = self._strategy_registry.validate(workflow_type, self.config.workflow)
        if errors:
            # Logar warnings mas não bloquear (algumas validações são soft)
            for error in errors:
                logging.warning(f"Validation: {error}")

        # 3. Construir workflow usando Strategy Pattern
        self._workflow = self._strategy_registry.build(
            workflow_type=workflow_type,
            agents=ordered_agents,
            config=self.config.workflow,
            agent_factory=self.agent_factory
        )

        # 4. Atribuir nome ao workflow se disponível
        if self._workflow and self.config.name:
            try:
                self._workflow.name = self.config.name
            except AttributeError:
                pass
        
        self._emit(WorkerEventType.SETUP_COMPLETE, {
            "workflow_type": workflow_type,
            "agent_count": len(ordered_agents)
        })

    async def invoke(self, initial_input: str) -> Any:
        """
        Executa o workflow de forma simples (sem streaming de eventos).
        
        Usa workflow.run() diretamente, mais eficiente para casos
        onde não é necessário capturar eventos intermediários.
        
        Args:
            initial_input: Texto de entrada para o workflow
            
        Returns:
            Resultado final do workflow
        """
        if not self._workflow:
            self.setup()
            
        if not self._workflow or not self.state_manager:
            raise RuntimeError("Failed to build workflow or initialize state.")

        self.state_manager.set_status("running")
        self._emit(WorkerEventType.WORKFLOW_START, {"input": initial_input[:100]})
        
        try:
            # Executar workflow diretamente
            result = await self._workflow.run(message=initial_input)
            
            # Processar resultado
            outputs = result.get_outputs()
            final_result = None
            
            if outputs:
                # Normalizar outputs para uma lista plana de mensagens
                all_messages = []
                for item in outputs:
                    if isinstance(item, list):
                        all_messages.extend(item)
                    else:
                        all_messages.append(item)

                # Retornar o texto da última mensagem de assistant
                if all_messages:
                    for msg in reversed(all_messages):
                        # Role pode ser enum (Role.assistant) ou string
                        role = getattr(msg, 'role', None)
                        if str(role) == 'assistant':
                            text = getattr(msg, 'text', None) or getattr(msg, 'content', None)
                            if text:
                                final_result = str(text)
                                break
            
            if final_result:
                self._emit(WorkerEventType.WORKFLOW_COMPLETE, {"result": str(final_result)})
                self.state_manager.set_status("completed")
                return str(final_result)
            
            self._emit(WorkerEventType.WORKFLOW_COMPLETE, {"result": ""})
            self.state_manager.set_status("completed")
            return "Nenhum output gerado pelo workflow."
            
        except Exception as e:
            self.state_manager.set_status("failed")
            self._emit(WorkerEventType.WORKFLOW_ERROR, {"error": str(e)})
            raise
        finally:
            self.teardown()

    async def ainvoke(self, initial_input: str) -> Any:
        """
        Executa o workflow com streaming de eventos.
        
        Usa workflow.run_stream() para capturar eventos em tempo real,
        emitindo AGENT_START para cada agente durante execução e
        AGENT_RESPONSE com conteúdo completo ao final.
        
        Args:
            initial_input: Texto de entrada para o workflow
            
        Returns:
            Resultado final do workflow
        """
        if not self._workflow:
            self.setup()
            
        if not self._workflow or not self.state_manager:
            raise RuntimeError("Failed to build workflow or initialize state.")

        self.state_manager.set_status("running")
        self._emit(WorkerEventType.WORKFLOW_START, {"input": initial_input[:100]})
        
        try:
            last_response = None
            current_agent = None
            agents_seen: set[str] = set()  # Agentes já notificados
            
            async for event in self._workflow.run_stream(message=initial_input):
                event_type = type(event).__name__
                
                # AgentRunUpdateEvent: Notifica que agente está ativo (streaming)
                if event_type == "AgentRunUpdateEvent":
                    agent_name = getattr(event, 'executor_id', 'unknown')
                    
                    # Emitir AGENT_START apenas uma vez por agente
                    if agent_name not in agents_seen and not agent_name.startswith(("to-conversation", "input-")):
                        agents_seen.add(agent_name)
                        current_agent = agent_name
                        self._emit(WorkerEventType.AGENT_START, {"agent_name": agent_name})
                
                # WorkflowOutputEvent: Mensagens completas - emitir resposta de cada agente
                elif event_type == "WorkflowOutputEvent":
                    data = getattr(event, 'data', None)
                    if data and isinstance(data, list):
                        # Emitir AGENT_RESPONSE para cada mensagem de assistant
                        for msg in data:
                            # Role pode ser enum (Role.assistant) ou string
                            role = getattr(msg, 'role', None)
                            if str(role) == 'assistant':
                                text = getattr(msg, 'text', None)
                                author = getattr(msg, 'author_name', None)
                                if text and author:
                                    last_response = text
                                    self._emit(
                                        WorkerEventType.AGENT_RESPONSE, 
                                        {"agent_name": author, "content": text}
                                    )
            
            # Retornar resultado
            if last_response:
                self._emit(WorkerEventType.WORKFLOW_COMPLETE, {"result": str(last_response)})
                self.state_manager.set_status("completed")
                return str(last_response)
            
            self._emit(WorkerEventType.WORKFLOW_COMPLETE, {"result": ""})
            self.state_manager.set_status("completed")
            return "Nenhum output gerado pelo workflow."
            
        except Exception as e:
            self.state_manager.set_status("failed")
            self._emit(WorkerEventType.WORKFLOW_ERROR, {"error": str(e)})
            raise
        finally:
            self.teardown()
    
    def _extract_event_content(self, data: Any) -> Optional[str]:
        """Extrai conteúdo textual de dados de evento."""
        if data is None:
            return None
        
        # String direta
        if isinstance(data, str):
            return data if data.strip() else None
        
        # Objeto com value
        if hasattr(data, "value") and data.value:
            return str(data.value)
        
        # Objeto com messages
        if hasattr(data, "messages") and data.messages:
            msgs = data.messages
            if isinstance(msgs, list) and msgs:
                last_msg = msgs[-1]
                if hasattr(last_msg, "text") and last_msg.text:
                    return str(last_msg.text)
                if hasattr(last_msg, "content") and last_msg.content:
                    return str(last_msg.content)
                return str(last_msg)
            elif isinstance(msgs, str):
                return msgs
        
        # Objeto com text/content direto
        if hasattr(data, "text") and data.text:
            return str(data.text)
        if hasattr(data, "content") and data.content:
            return str(data.content)
        
        # Lista de mensagens
        if isinstance(data, list) and data:
            last_item = data[-1]
            if hasattr(last_item, "text") and last_item.text:
                return str(last_item.text)
            if hasattr(last_item, "content") and last_item.content:
                return str(last_item.content)
            return str(last_item)
        
        return None
    
    def _is_stream_placeholder(self, content: str) -> bool:
        """Verifica se o conteúdo é um placeholder de streaming."""
        if not content:
            return True
        
        placeholders = [
            "[Streaming response...]",
            "async_generator object",
            "generator object",
            "<async_generator",
            "<generator",
            "Completed",
        ]
        
        return any(p in content for p in placeholders)
