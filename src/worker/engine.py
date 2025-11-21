import json
import os
from typing import Any, Dict, Optional

from agent_framework import Workflow, WorkflowBuilder, Case, Default, ExecutorCompletedEvent, AgentRunEvent, SequentialBuilder, ConcurrentBuilder, GroupChatBuilder, HandoffBuilder, ChatAgent

from src.worker.config import WorkerConfig
from src.worker.factory import AgentFactory
from src.worker.middleware import TemplateMiddleware
from src.worker.agents import HumanAgent


class WorkflowEngine:
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.agent_factory = AgentFactory(config)
        self._workflow: Optional[Workflow] = None

    def build(self):
        """Constrói o objeto Workflow baseado na configuração usando builders nativos de alto nível."""
        steps = self.config.workflow.steps
        workflow_type = self.config.workflow.type
        
        # Mapa de step_id -> agent_instance
        step_agents = {}
        ordered_agents = []
        
        # 1. Criar todos os agentes
        for step in steps:
            agent = None
            if step.type == "agent":
                if not step.agent:
                     raise ValueError(f"Passo {step.id} do tipo 'agent' deve ter um 'agent' definido.")
                
                # Criar middleware de template se necessário
                middleware = []
                if step.input_template:
                    middleware.append(TemplateMiddleware(step.input_template))
                
                # Criar agente com middleware
                agent = self.agent_factory.create_agent(str(step.agent), middleware=middleware)
                
            elif step.type == "human":
                # Criar agente humano
                agent = HumanAgent(id=step.id, instructions=step.input_template)
            
            if agent:
                step_agents[step.id] = agent
                ordered_agents.append(agent)

        # 2. Construir workflow usando o builder apropriado
        if workflow_type == "sequential":
            # Usar SequentialBuilder para fluxos sequenciais
            # Ele conecta automaticamente os participantes em ordem
            self._workflow = SequentialBuilder().participants(ordered_agents).build()
            
        elif workflow_type == "parallel":
            # Usar ConcurrentBuilder para fluxos paralelos (fan-out/fan-in)
            # Ele cria automaticamente o dispatcher e aggregator
            self._workflow = ConcurrentBuilder().participants(ordered_agents).build()
            
        elif workflow_type == "group_chat":
            # Usar GroupChatBuilder para chat em grupo
            # Requer um manager para coordenar
            builder = GroupChatBuilder()
            builder.participants(ordered_agents)
            
            # Tentar encontrar um modelo padrão para o manager
            # Usar o modelo do primeiro agente como referência ou o primeiro disponível
            manager_model_id = None
            if self.config.agents:
                manager_model_id = self.config.agents[0].model
            
            # Criar um agente manager simples
            if manager_model_id:
                try:
                    # Usar método interno da factory para criar o client
                    # Isso é um hack, idealmente a factory deveria expor create_client
                    client = self.agent_factory._create_client(manager_model_id)
                    
                    builder.set_prompt_based_manager(
                        chat_client=client,
                        instructions="Select the next speaker based on the conversation context.",
                        display_name="GroupManager"
                    )
                except Exception as e:
                    print(f"Warning: Failed to create manager agent: {e}")
                    # Se falhar, o builder pode reclamar se não tiver manager
                    pass

            self._workflow = builder.build()

        elif workflow_type == "handoff":
            # Usar HandoffBuilder para transições explícitas
            builder = HandoffBuilder()
            builder.participants(ordered_agents)
            
            start_step_id = self.config.workflow.start_step
            if start_step_id and start_step_id in step_agents:
                builder.set_coordinator(step_agents[start_step_id])
            
            # Configurar transições baseadas no campo 'transitions' dos steps
            for step in steps:
                if step.transitions:
                    source_agent = step_agents.get(step.id)
                    targets = [step_agents[t] for t in step.transitions if t in step_agents]
                    
                    if source_agent and targets:
                        builder.add_handoff(source_agent, targets)
            
            self._workflow = builder.build()

        elif workflow_type == "router":
            # Para router, usamos o WorkflowBuilder base pois precisamos de lógica customizada de arestas
            builder = WorkflowBuilder()
            
            # Adicionar todos os agentes ao builder
            for agent in step_agents.values():
                builder.add_agent(agent)
            
            start_step_id = self.config.workflow.start_step
            if not start_step_id:
                raise ValueError("Workflow do tipo Router requer 'start_step'")
            
            start_agent = step_agents[start_step_id]
            builder.set_start_executor(start_agent)
            
            # Mapear saídas do router para os próximos agentes
            cases = []
            
            def make_condition(target_id):
                def condition(output):
                    # Extrair valor do output
                    val = output
                    
                    # Se for AgentExecutorResponse (do framework)
                    if hasattr(output, 'agent_run_response'):
                        val = output.agent_run_response
                        
                    # Se for AgentRunResponse (do agente)
                    if hasattr(val, 'value') and val.value is not None:
                        val = val.value
                    elif hasattr(val, 'messages') and val.messages:
                        # Tentar pegar o último conteúdo
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
                    
                    # Debug
                    # print(f"DEBUG: Router output: '{val}', Target: '{target_id}', Match: {str(val).strip() == target_id}")
                        
                    # Comparar com o ID do alvo (case insensitive)
                    return str(val).strip().lower() == target_id.lower()
                return condition

            # Identificar passos de destino (excluindo o start_step)
            target_steps = [s for s in steps if s.id != start_step_id]
            
            if not target_steps:
                raise ValueError("Workflow Router deve ter pelo menos um passo de destino.")
                
            # Usar o último passo como Default
            default_step = target_steps[-1]
            other_steps = target_steps[:-1]
            
            # Adicionar Cases para os outros passos
            for step in other_steps:
                cases.append(Case(condition=make_condition(step.id), target=step_agents[step.id]))
                
            # Adicionar Default para o último passo
            cases.append(Default(target=step_agents[default_step.id]))
            
            # Adicionar grupo de arestas switch-case
            builder.add_switch_case_edge_group(start_agent, cases)
            
            self._workflow = builder.build()

        # Atribuir nome ao workflow se disponível na configuração
        if self._workflow and self.config.name:
            try:
                self._workflow.name = self.config.name
            except AttributeError:
                pass
            
            # Tentar definir label também, se suportado
            # try:
            #     self._workflow.label = self.config.name
            # except AttributeError:
            #     pass

    async def run(self, initial_input: str) -> Any:
        """Executa o workflow usando o motor nativo."""
        if not self._workflow:
            self.build()
            
        if not self._workflow:
             raise RuntimeError("Failed to build workflow.")

        print(f"🚀 Iniciando execução nativa do workflow ({self.config.workflow.type})...")
        
        # Executar workflow
        # O input inicial é passado como mensagem de usuário
        # Workflow.run(message=...) retorna WorkflowRunResult
        result = await self._workflow.run(message=initial_input)
        
        # Processar resultado
        outputs = result.get_outputs()
        
        if outputs:
            # Se o output for uma lista de ChatMessage (comum em Sequential/Concurrent)
            final_output = outputs[-1]
            
            if isinstance(final_output, list):
                # Pode ser uma lista de mensagens
                # Filtrar objetos que parecem mensagens
                messages = [m for m in final_output if hasattr(m, 'content') or hasattr(m, 'text')]
                
                if messages:
                    # Retornar o conteúdo da última mensagem
                    last_msg = messages[-1]
                    if hasattr(last_msg, 'text') and getattr(last_msg, 'text', None):
                        return getattr(last_msg, 'text')
                    elif hasattr(last_msg, 'content'):
                        return str(getattr(last_msg, 'content'))
                    else:
                        return str(last_msg)
            
            # Se for um único objeto ChatMessage
            if hasattr(final_output, 'text') and getattr(final_output, 'text', None):
                return getattr(final_output, 'text')
            elif hasattr(final_output, 'content'):
                return str(getattr(final_output, 'content'))
                
            return final_output
        
        if not outputs:
            # Debug: Se não houver outputs explícitos, tentar extrair do histórico de eventos
            # Procurar por eventos de conclusão de agente
            # print("⚠️ Nenhum output explícito (yield_output) encontrado. Inspecionando eventos...")
            last_response = None
            
            # result é uma lista de eventos
            for event in result:
                # print(f"DEBUG: Event type: {type(event).__name__}")
                if isinstance(event, AgentRunEvent):
                    # print(f"DEBUG: AgentRunEvent for {event.executor_id}")
                    if hasattr(event, "data"):
                        data = event.data
                        # print(f"DEBUG: Data type: {type(data)}")
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
                elif isinstance(event, ExecutorCompletedEvent):
                    # Fallback se AgentRunEvent não tiver dados (ex: HumanAgent customizado)
                    if hasattr(event, "data") and event.data is not None:
                         # Lógica similar...
                         pass
            
            if last_response:
                return str(last_response)
                
            return "Nenhum output gerado pelo workflow."
            
        # Retornar o último output ou todos
        return outputs[-1]

        # Fallback para o runner nativo do framework se implementado
        if self._workflow:
            return await self._workflow.run(initial_input)
        else:
            raise NotImplementedError(f"Workflow type '{self.config.workflow.type}' not supported in manual mode and build failed.")
