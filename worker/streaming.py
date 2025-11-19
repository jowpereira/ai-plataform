"""Streaming utilities para UI e agregação de eventos.

Módulo responsável por:
- Agregar eventos de streaming em mensagens coerentes
- Fornecer interface limpa para consumo em UI
- Manter estado por executor
- Suporte a diferentes níveis de verbosidade
"""

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Literal
from collections import defaultdict

from agent_framework import (
    AgentRunUpdateEvent,
    ExecutorCompletedEvent,
    ExecutorInvokedEvent,
    WorkflowOutputEvent,
    WorkflowStartedEvent,
    WorkflowStatusEvent,
)


@dataclass
class StreamMessage:
    """Mensagem agregada para UI."""

    executor_id: str | None
    content: str
    is_complete: bool
    event_type: Literal["executor_start", "executor_update", "executor_complete", "workflow_output", "workflow_status"]
    metadata: dict[str, Any] = field(default_factory=dict)


class EventAggregator:
    """Agregador de eventos de workflow para consumo em UI.

    Características:
    - Agrega chunks por executor
    - Emite mensagens coerentes
    - Mantém histórico de executores
    - Suporte a diferentes níveis de verbosidade
    """

    def __init__(self, verbosity: Literal["minimal", "normal", "debug"] = "normal"):
        """Inicializa agregador.

        Args:
            verbosity: Nível de detalhe
                - minimal: Apenas workflow_output
                - normal: executor_start, executor_complete, workflow_output
                - debug: Todos os eventos incluindo chunks
        """
        self.verbosity = verbosity
        self._buffers: dict[str, list[str]] = defaultdict(list)
        self._current_executor: str | None = None

    def _should_emit(self, event_type: str) -> bool:
        """Verifica se deve emitir evento baseado em verbosity."""
        if self.verbosity == "minimal":
            return event_type == "workflow_output"
        elif self.verbosity == "normal":
            return event_type in ["executor_start", "executor_complete", "workflow_output"]
        else:  # debug
            return True

    async def process_stream(
        self, 
        workflow_stream: AsyncIterator[Any],
    ) -> AsyncIterator[StreamMessage]:
        """Processa stream de workflow e emite mensagens agregadas.

        Args:
            workflow_stream: AsyncIterator de eventos do workflow

        Yields:
            StreamMessage: Mensagens agregadas prontas para UI
        """
        async for event in workflow_stream:
            # WorkflowStartedEvent
            if isinstance(event, WorkflowStartedEvent):
                if self._should_emit("workflow_status"):
                    yield StreamMessage(
                        executor_id=None,
                        content="Workflow iniciado",
                        is_complete=True,
                        event_type="workflow_status",
                        metadata={"state": "started"},
                    )

            # ExecutorInvokedEvent
            elif isinstance(event, ExecutorInvokedEvent):
                self._current_executor = event.executor_id
                self._buffers[event.executor_id] = []

                if self._should_emit("executor_start"):
                    yield StreamMessage(
                        executor_id=event.executor_id,
                        content=f"Executor '{event.executor_id}' iniciado",
                        is_complete=False,
                        event_type="executor_start",
                        metadata={"executor_id": event.executor_id},
                    )

            # AgentRunUpdateEvent (chunks)
            elif isinstance(event, AgentRunUpdateEvent):
                executor_id = event.executor_id
                
                # Extrair conteúdo do evento
                # AgentRunUpdateEvent pode ter diferentes campos dependendo da versão
                content_chunk = ""
                event_str = str(event)
                
                # Parse "messages=..." do repr
                if "messages=" in event_str:
                    parts = event_str.split("messages=", 1)
                    if len(parts) > 1:
                        # Extrair até o próximo parêntese fechado
                        content_part = parts[1].rstrip(")")
                        content_chunk = content_part
                
                # Acumular chunks
                if content_chunk:
                    self._buffers[executor_id].append(content_chunk)

                # Emitir update parcial se debug
                if self._should_emit("executor_update"):
                    content = "".join(self._buffers[executor_id])
                    yield StreamMessage(
                        executor_id=executor_id,
                        content=content,
                        is_complete=False,
                        event_type="executor_update",
                        metadata={"chunk_count": len(self._buffers[executor_id])},
                    )

            # ExecutorCompletedEvent
            elif isinstance(event, ExecutorCompletedEvent):
                executor_id = event.executor_id
                
                # Flush buffer final
                if self._should_emit("executor_complete"):
                    content = "".join(self._buffers[executor_id])
                    yield StreamMessage(
                        executor_id=executor_id,
                        content=content,
                        is_complete=True,
                        event_type="executor_complete",
                        metadata={
                            "executor_id": executor_id,
                            "chunk_count": len(self._buffers[executor_id]),
                        },
                    )

                # Limpar buffer
                self._buffers[executor_id] = []

            # WorkflowOutputEvent (output final)
            elif isinstance(event, WorkflowOutputEvent):
                if self._should_emit("workflow_output"):
                    yield StreamMessage(
                        executor_id=getattr(event, "source_executor_id", None),
                        content=str(event.data),
                        is_complete=True,
                        event_type="workflow_output",
                        metadata={
                            "source_executor_id": getattr(event, "source_executor_id", None),
                        },
                    )

            # WorkflowStatusEvent
            elif isinstance(event, WorkflowStatusEvent):
                if self._should_emit("workflow_status"):
                    yield StreamMessage(
                        executor_id=None,
                        content=f"Workflow status: {event.state}",
                        is_complete=True,
                        event_type="workflow_status",
                        metadata={"state": str(event.state)},
                    )

    def clear(self):
        """Limpa buffers e estado."""
        self._buffers.clear()
        self._current_executor = None


class ConsoleStreamRenderer:
    """Renderizador de stream para console com formatação elegante."""

    def __init__(self, show_metadata: bool = False):
        """Inicializa renderer.

        Args:
            show_metadata: Se deve mostrar metadados dos eventos
        """
        self.show_metadata = show_metadata

    async def render(self, stream: AsyncIterator[StreamMessage]):
        """Renderiza stream de mensagens no console.

        Args:
            stream: AsyncIterator de StreamMessage
        """
        async for message in stream:
            await self._render_message(message)

    async def _render_message(self, msg: StreamMessage):
        """Renderiza mensagem individual."""
        # Ícones por tipo
        icons = {
            "executor_start": "🔄",
            "executor_update": "💬",
            "executor_complete": "✅",
            "workflow_output": "📦",
            "workflow_status": "ℹ️",
        }
        icon = icons.get(msg.event_type, "•")

        # Formatar executor_id
        executor = f"[{msg.executor_id}]" if msg.executor_id else ""

        # Printar mensagem
        if msg.event_type == "executor_update":
            # Update incremental (sem quebra de linha)
            print(f"\r{icon} {executor} {msg.content}", end="", flush=True)
        else:
            # Mensagem completa (com quebra de linha)
            print(f"\n{icon} {executor} {msg.content}")

        # Mostrar metadata se habilitado
        if self.show_metadata and msg.metadata:
            print(f"   └─ {msg.metadata}")
