# Copyright (c) Microsoft. All rights reserved.

"""
AgentRunner - Executor para agentes standalone (sem workflow).

Este módulo permite executar agentes individuais diretamente,
sem a necessidade de encapsulá-los em um workflow.

Reutiliza AgentFactory para criação de agentes, garantindo
consistência com o padrão existente do projeto.
"""

import logging
import os
import uuid
from typing import Any, AsyncGenerator, Optional

from agent_framework import ChatAgent

from src.worker.config import (
    StandaloneAgentConfig,
    AgentConfig,
    ModelConfig,
    ToolConfig,
    ResourcesConfig,
    WorkerConfig,
    WorkflowConfig,
    WorkflowStep,
    RagConfig,
    RagEmbeddingConfig,
)
from src.worker.factory import AgentFactory
from src.worker.events import get_event_bus, WorkerEventType
from src.worker.observability import setup_observability, shutdown_observability

logger = logging.getLogger("worker.runner")


class AgentRunner:
    """
    Executor para agentes standalone.
    
    Converte StandaloneAgentConfig para WorkerConfig e reutiliza
    AgentFactory para criação consistente de agentes.
    
    Usage:
        config = StandaloneAgentConfig(...)
        runner = AgentRunner(config)
        
        # Execução síncrona
        result = await runner.run("Olá, qual o clima em SP?")
        
        # Execução com streaming
        async for event in runner.run_stream("Olá, qual o clima em SP?"):
            print(event)
    """

    def __init__(
        self, 
        config: StandaloneAgentConfig,
        tools_base_path: str = "mock_tools.basic"
    ):
        """
        Inicializa o AgentRunner.
        
        Args:
            config: Configuração do agente standalone
            tools_base_path: Caminho base para importação de ferramentas
        """
        self.config = config
        self.tools_base_path = tools_base_path
        self._agent: Optional[ChatAgent] = None
        self._agent_factory: Optional[AgentFactory] = None
        self._setup_complete = False
        self.execution_id = str(uuid.uuid4())
        
        # Initialize observability
        setup_observability()
        
    def _build_worker_config(self) -> WorkerConfig:
        """
        Converte StandaloneAgentConfig para WorkerConfig.
        
        Cria uma configuração completa de worker com um único agente,
        permitindo reutilizar AgentFactory.
        """
        # Detectar provider automaticamente baseado em variáveis de ambiente
        if os.environ.get("AZURE_OPENAI_API_KEY"):
            provider_type = "azure-openai"
            logger.debug("Detectado: Azure OpenAI via AZURE_OPENAI_API_KEY")
        elif os.environ.get("OPENAI_API_KEY"):
            provider_type = "openai"
            logger.debug("Detectado: OpenAI via OPENAI_API_KEY")
        else:
            provider_type = "openai"
            logger.warning("Nenhum provider detectado, usando openai como default")
        
        # Usar model_config_override se fornecido, ou criar default
        if self.config.model_config_override:
            model_config = self.config.model_config_override
        else:
            model_config = ModelConfig(
                type=provider_type,
                deployment=self.config.model
            )
        
        # Construir lista de ferramentas
        tool_configs = []
        if self.config.tools_config:
            tool_configs = list(self.config.tools_config)
        else:
            # Criar ToolConfig para cada ferramenta referenciada
            for tool_id in self.config.tools:
                tool_configs.append(ToolConfig(
                    id=tool_id,
                    path=f"{self.tools_base_path}:{tool_id}",
                    description=f"Ferramenta {tool_id}"
                ))
        
        # Construir AgentConfig
        agent_config = AgentConfig(
            id=self.config.id,
            role=self.config.role,
            description=self.config.description,
            model=self.config.model,  # Referência ao modelo no resources
            instructions=self.config.instructions,
            tools=[t.id for t in tool_configs],
            confirmation_mode=self.config.confirmation_mode,
            knowledge=self.config.knowledge,
        )
        
        # Construir ResourcesConfig
        resources = ResourcesConfig(
            models={self.config.model: model_config},
            tools=tool_configs
        )
        
        # Configurar RAG se o agente solicitar knowledge
        rag_config = None
        if self.config.knowledge and self.config.knowledge.enabled:
            embedding_model = "text-embedding-ada-002"
            
            # Adicionar modelo de embedding aos recursos se não existir
            if embedding_model not in resources.models:
                # Tentar usar variáveis de ambiente para configurar o embedding
                resources.models[embedding_model] = ModelConfig(
                    type="azure-openai" if os.environ.get("AZURE_OPENAI_API_KEY") else "openai",
                    deployment=os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", embedding_model)
                )
            
            rag_config = RagConfig(
                enabled=True,
                provider="memory",
                embedding=RagEmbeddingConfig(
                    model=embedding_model,
                    dimensions=1536,
                    normalize=True
                )
            )
        
        # Workflow mínimo (necessário para WorkerConfig)
        workflow = WorkflowConfig(
            type="sequential",
            steps=[WorkflowStep(id="step1", agent=self.config.id, input_template="{input}")]
        )
        
        return WorkerConfig(
            version="1.0",
            name=f"standalone_{self.config.id}",
            resources=resources,
            agents=[agent_config],
            workflow=workflow,
            rag=rag_config
        )
        
    async def setup(self) -> None:
        """
        Configura o agente usando AgentFactory.
        
        Chamado automaticamente por run() se necessário.
        """
        if self._setup_complete:
            return
            
        logger.info(f"🔧 Configurando agente: {self.config.id}")
        
        # Converter para WorkerConfig e usar AgentFactory
        worker_config = self._build_worker_config()
        self._agent_factory = AgentFactory(worker_config)
        
        # Criar agente usando a factory (reutiliza toda a lógica existente)
        # EventMiddleware já é adicionado pela factory para observabilidade
        self._agent = self._agent_factory.create_agent(self.config.id)
        
        self._setup_complete = True
        logger.info(f"✅ Agente configurado: {self.config.id} ({len(self.config.tools)} ferramentas)")

    async def run(self, input_text: str) -> str:
        """
        Executa o agente com input e retorna resposta completa.
        
        Args:
            input_text: Texto de entrada do usuário
            
        Returns:
            Resposta do agente como string
        """
        await self.setup()
        
        if not self._agent:
            raise RuntimeError("Agente não inicializado")
        
        bus = get_event_bus()
        # Emitir evento de início de execução (header visual)
        bus.emit_simple(
            WorkerEventType.AGENT_RUN_START,
            {
                "agent_name": self.config.id,
                "agent_role": self.config.role,
                "tools_count": len(self.config.tools),
                "input": input_text
            },
            metadata={"execution_id": self.execution_id}
        )
        
        logger.info(f"🚀 Executando agente: {self.config.id}")
        logger.debug(f"📥 Input: {input_text}")
        
        try:
            response = await self._agent.run(input_text)
            
            # Extrair texto da resposta (AgentRunResponse)
            result_text = self._extract_response_text(response)
            
            # Nota: EventMiddleware já emite AGENT_RESPONSE durante execução
            bus.emit_simple(
                WorkerEventType.AGENT_RUN_COMPLETE,
                {"agent_name": self.config.id, "result": result_text},
                metadata={"execution_id": self.execution_id}
            )
            
            logger.info(f"✅ Agente concluído: {self.config.id}")
            return result_text
            
        except Exception as e:
            bus.emit_simple(
                WorkerEventType.WORKFLOW_ERROR,
                {"agent_name": self.config.id, "error": str(e)},
                metadata={"execution_id": self.execution_id}
            )
            logger.error(f"❌ Erro no agente {self.config.id}: {e}")
            raise

    def _extract_response_text(self, response: Any) -> str:
        """
        Extrai texto da resposta do agente.
        
        Suporta diferentes estruturas de resposta do Agent Framework.
        """
        # Primeiro tentar o atributo value (resposta direta)
        if hasattr(response, "value") and response.value:
            return str(response.value)
        
        # Buscar na última mensagem do assistant
        if hasattr(response, "messages") and response.messages:
            for msg in reversed(response.messages):
                if getattr(msg, "role", None) == "assistant":
                    contents = getattr(msg, "contents", [])
                    for content in contents:
                        # TextContent tem atributo 'text'
                        if hasattr(content, "text") and content.text:
                            return content.text
        
        # Fallback: converter para string
        return str(response)

    async def run_stream(self, input_text: str) -> AsyncGenerator[Any, None]:
        """
        Executa o agente com streaming de eventos.
        
        Args:
            input_text: Texto de entrada do usuário
            
        Yields:
            Eventos de resposta do agente
        """
        await self.setup()
        
        if not self._agent:
            raise RuntimeError("Agente não inicializado")
        # Emitir evento de início
        bus.emit_simple(
            WorkerEventType.AGENT_RUN_START,
            {
                "agent_name": self.config.id,
                "agent_role": self.config.role,
                "tools_count": len(self.config.tools),
                "input": input_text
            },
            metadata={"execution_id": self.execution_id}
        )
        
        logger.info(f"🚀 Executando agente (stream): {self.config.id}")
        
        try:
            if hasattr(self._agent, "run_stream"):
                async for event in self._agent.run_stream(input_text):
                    yield event
            else:
                # Fallback para run() se streaming não disponível
                result = await self._agent.run(input_text)
                yield result
        except Exception as e:
            bus.emit_simple(
                WorkerEventType.WORKFLOW_ERROR,
                {"agent_name": self.config.id, "error": str(e)},
                metadata={"execution_id": self.execution_id}
            )
            raise

    async def teardown(self) -> None:
        """Limpa recursos do agente."""
        self._agent = None
        self._agent_factory = None
        self._setup_complete = False
        logger.debug(f"Recursos liberados: {self.config.id}")
