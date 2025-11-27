import json
import logging
import os
import uuid
from typing import Any, Dict, Optional, List

from agent_framework import Workflow, ChatAgent, ChatMessage, ExecutorCompletedEvent, AgentRunEvent

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
        self._last_agent_response: Optional[str] = None  # Captura última resposta via eventos
        self._response_subscription_id: Optional[str] = None

    @property
    def event_bus(self) -> SimpleEventBus:
        """Retorna o EventBus para inscrição de hooks externos."""
        return self._event_bus
    
    def _capture_agent_response(self, event: Any) -> None:
        """Callback para capturar a última resposta de agente."""
        if hasattr(event, 'type') and event.type == WorkerEventType.AGENT_RESPONSE:
            content = event.data.get("content", "")
            if content and content != "Completed":
                self._last_agent_response = content

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

    async def run(self, initial_input: str) -> Any:
        """Executa o workflow usando o motor nativo."""
        if not self._workflow:
            self.setup()
            
        if not self._workflow or not self.state_manager:
            raise RuntimeError("Failed to build workflow or initialize state.")

        self.state_manager.set_status("running")
        self._emit(WorkerEventType.WORKFLOW_START, {"input": initial_input[:100]})
        
        # Registrar captura de respostas via EventBus
        self._last_agent_response = None
        self._response_subscription_id = self._event_bus.subscribe(
            WorkerEventType.AGENT_RESPONSE, 
            self._capture_agent_response
        )
        
        try:
            # Executar workflow
            result = await self._workflow.run(message=initial_input)
            
            # Processar resultado
            outputs = result.get_outputs()
            
            if outputs:
                # Normalizar outputs para uma lista plana de mensagens
                all_messages = []
                for item in outputs:
                    if isinstance(item, list):
                        all_messages.extend(item)
                    else:
                        all_messages.append(item)

                # Retornar o texto da última mensagem válida
                if all_messages:
                    last_msg = all_messages[-1]
                    final_result = getattr(last_msg, 'text', None) or getattr(last_msg, 'content', None) or str(last_msg)
                    self._emit(WorkerEventType.WORKFLOW_COMPLETE, {"result": str(final_result)})
                    self.state_manager.set_status("completed")
                    return final_result
            
            # Fallback 1: Usar última resposta capturada pelo EventBus
            if self._last_agent_response:
                self._emit(WorkerEventType.WORKFLOW_COMPLETE, {"result": str(self._last_agent_response)})
                self.state_manager.set_status("completed")
                return self._last_agent_response
            
            # Fallback 2: Inspecionar eventos do resultado se não houver outputs explícitos
            last_response = None
            
            for event in result:
                if isinstance(event, AgentRunEvent):
                    if hasattr(event, "data"):
                        data = event.data
                        if hasattr(data, "value") and getattr(data, "value", None):
                            last_response = getattr(data, "value")
                        elif hasattr(data, "messages") and getattr(data, "messages", None):
                            msgs = getattr(data, "messages")
                            if isinstance(msgs, list) and msgs:
                                last_msg = msgs[-1]
                                if hasattr(last_msg, "text"):
                                    last_response = getattr(last_msg, "text")
                                elif hasattr(last_msg, "content"):
                                    last_response = str(getattr(last_msg, "content"))
                                else:
                                    last_response = str(last_msg)
                            elif isinstance(msgs, str):
                                last_response = msgs
                        else:
                            last_response = str(data)
            
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
            # Limpar subscription
            if self._response_subscription_id:
                self._event_bus.unsubscribe(self._response_subscription_id)
            self.teardown()
