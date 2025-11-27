"""
Sistema de Eventos para Observabilidade.

Implementa o EventBus para hooks e logging estruturado.
Permite que componentes externos se inscrevam para receber
notificações sobre eventos do worker.

Uso:
    ```python
    from src.worker.events import SimpleEventBus, WorkerEventType
    
    bus = SimpleEventBus()
    
    # Inscrever para eventos
    def on_llm_request(event):
        print(f"LLM Request: {event.data}")
    
    bus.subscribe(WorkerEventType.LLM_REQUEST_START, on_llm_request)
    
    # Emitir eventos
    bus.emit_simple(WorkerEventType.LLM_REQUEST_START, {"model": "gpt-4o"})
    ```
"""

import logging
import uuid
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
import time

from src.worker.interfaces import EventBus, WorkerEvent, WorkerEventType, EventHandler


# Configurar logger
logger = logging.getLogger("worker.events")


class SimpleEventBus(EventBus):
    """
    Implementação simples e síncrona do EventBus.
    
    Características:
    - Síncrono (handlers executados na mesma thread)
    - Suporta múltiplos handlers por tipo de evento
    - Suporta handler "wildcard" que recebe todos os eventos
    - Thread-safe para registro/cancelamento (não para emissão)
    """
    
    WILDCARD = "*"
    
    def __init__(self):
        self._handlers: Dict[str, Dict[str, EventHandler]] = defaultdict(dict)
        self._enabled = True
    
    def subscribe(
        self,
        event_type: Union[WorkerEventType, List[WorkerEventType], str],
        handler: EventHandler
    ) -> str:
        """
        Inscreve um handler para eventos.
        
        Args:
            event_type: Tipo(s) de evento ou "*" para todos
            handler: Função callback
            
        Returns:
            ID da inscrição
        """
        subscription_id = str(uuid.uuid4())[:8]
        
        # Normalizar para lista
        if isinstance(event_type, str):
            types = [event_type]
        elif isinstance(event_type, WorkerEventType):
            types = [event_type.value]
        else:
            types = [t.value for t in event_type]
        
        for t in types:
            self._handlers[t][subscription_id] = handler
        
        logger.debug(f"Subscribed {subscription_id} to {types}")
        return subscription_id
    
    def subscribe_all(self, handler: EventHandler) -> str:
        """
        Inscreve um handler para TODOS os eventos.
        
        Args:
            handler: Função callback
            
        Returns:
            ID da inscrição
        """
        return self.subscribe(self.WILDCARD, handler)
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Cancela uma inscrição.
        
        Args:
            subscription_id: ID retornado por subscribe
            
        Returns:
            True se encontrado e removido
        """
        found = False
        for event_type in list(self._handlers.keys()):
            if subscription_id in self._handlers[event_type]:
                del self._handlers[event_type][subscription_id]
                found = True
        
        if found:
            logger.debug(f"Unsubscribed {subscription_id}")
        return found
    
    def emit(self, event: WorkerEvent) -> None:
        """
        Emite um evento para todos os handlers inscritos.
        
        Args:
            event: Evento a emitir
        """
        if not self._enabled:
            return
        
        event_type = event.type.value
        
        # Coletar handlers específicos + wildcards
        handlers_to_call = []
        
        if event_type in self._handlers:
            handlers_to_call.extend(self._handlers[event_type].values())
        
        if self.WILDCARD in self._handlers:
            handlers_to_call.extend(self._handlers[self.WILDCARD].values())
        
        # Executar handlers
        for handler in handlers_to_call:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    def emit_simple(
        self,
        event_type: WorkerEventType,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkerEvent:
        """
        Helper para emitir eventos simples.
        
        Args:
            event_type: Tipo do evento
            data: Dados do evento
            metadata: Metadados adicionais
            
        Returns:
            Evento emitido
        """
        event = WorkerEvent(
            type=event_type,
            timestamp=time.time(),
            data=data or {},
            metadata=metadata or {}
        )
        self.emit(event)
        return event
    
    def enable(self) -> None:
        """Habilita emissão de eventos."""
        self._enabled = True
    
    def disable(self) -> None:
        """Desabilita emissão de eventos (útil para testes)."""
        self._enabled = False
    
    def clear(self) -> None:
        """Remove todas as inscrições."""
        self._handlers.clear()
    
    @property
    def handler_count(self) -> int:
        """Número total de handlers registrados."""
        return sum(len(h) for h in self._handlers.values())


# =============================================================================
# Handlers Pré-definidos
# =============================================================================

def create_logging_handler(
    level: int = logging.INFO,
    logger_name: str = "worker.events"
) -> EventHandler:
    """
    Cria um handler que loga eventos.
    
    Args:
        level: Nível de log
        logger_name: Nome do logger
        
    Returns:
        Handler configurado
    """
    event_logger = logging.getLogger(logger_name)
    
    def handler(event: WorkerEvent) -> None:
        event_logger.log(
            level,
            f"[{event.type.value}] {event.data}"
        )
    
    return handler


def create_json_handler(
    output_func: Callable[[str], None]
) -> EventHandler:
    """
    Cria um handler que serializa eventos para JSON.
    
    Args:
        output_func: Função que recebe a string JSON
        
    Returns:
        Handler configurado
    """
    import json
    
    def handler(event: WorkerEvent) -> None:
        json_str = json.dumps({
            "type": event.type.value,
            "timestamp": event.timestamp,
            "data": event.data,
            "metadata": event.metadata
        })
        output_func(json_str)
    
    return handler


def create_metrics_handler(
    metrics_dict: Dict[str, int]
) -> EventHandler:
    """
    Cria um handler que conta eventos por tipo.
    
    Args:
        metrics_dict: Dicionário para acumular contagens
        
    Returns:
        Handler configurado
    """
    def handler(event: WorkerEvent) -> None:
        key = event.type.value
        metrics_dict[key] = metrics_dict.get(key, 0) + 1
    
    return handler


# =============================================================================
# Instância Global (Singleton Opcional)
# =============================================================================

_global_bus: Optional[SimpleEventBus] = None


def get_event_bus() -> SimpleEventBus:
    """
    Obtém a instância global do EventBus.
    
    Returns:
        SimpleEventBus singleton
    """
    global _global_bus
    if _global_bus is None:
        _global_bus = SimpleEventBus()
    return _global_bus


def reset_event_bus() -> None:
    """Reseta o EventBus global (útil para testes)."""
    global _global_bus
    if _global_bus:
        _global_bus.clear()
    _global_bus = None
