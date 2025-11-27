"""
Adapters de normalização para workflows.

Segue o padrão do Microsoft Agent Framework que usa internal adapters
para normalização de tipos entre executors:
    - _InputToConversation: Normaliza input → list[ChatMessage]
    - _ResponseToConversation: Normaliza AgentExecutorResponse → list[ChatMessage]
    - _EndWithConversation: Finaliza workflow com list[ChatMessage]

Referência: agent_framework/_workflows/_sequential.py
"""

from typing import Any, List
from typing_extensions import Never

from agent_framework import (
    Executor,
    handler,
    WorkflowContext,
    ChatMessage,
    Role,
    AgentExecutorResponse,
)


class InputToConversation(Executor):
    """
    Normaliza qualquer tipo de input para list[ChatMessage].
    
    Padrão do framework: Aceita múltiplos tipos via @handler overloads.
    Cada handler processa um tipo específico de entrada.
    
    Tipos suportados:
        - str: Converte para ChatMessage(USER, text=prompt)
        - ChatMessage: Envolve em lista
        - list[ChatMessage]: Passa diretamente
        - dict: Extrai 'text' ou 'content' se disponível
    """
    
    def __init__(self, id: str = "input_normalizer"):
        super().__init__(id)
    
    @handler
    async def from_str(
        self, 
        prompt: str, 
        ctx: WorkflowContext[List[ChatMessage], Never]
    ) -> None:
        """Converte string para lista com uma mensagem USER."""
        await ctx.send_message([ChatMessage(role=Role.USER, text=prompt)])
    
    @handler
    async def from_message(
        self, 
        message: ChatMessage, 
        ctx: WorkflowContext[List[ChatMessage], Never]
    ) -> None:
        """Envolve ChatMessage único em lista."""
        await ctx.send_message([message])
    
    @handler
    async def from_messages(
        self, 
        messages: List[ChatMessage], 
        ctx: WorkflowContext[List[ChatMessage], Never]
    ) -> None:
        """Passa lista de mensagens diretamente."""
        await ctx.send_message(list(messages))
    
    @handler
    async def from_dict(
        self,
        data: dict,
        ctx: WorkflowContext[List[ChatMessage], Never]
    ) -> None:
        """Extrai texto de dicionário e converte para mensagem."""
        text = data.get('text') or data.get('content') or str(data)
        role_str = data.get('role', 'user').lower()
        role = Role.USER if role_str == 'user' else Role.ASSISTANT
        await ctx.send_message([ChatMessage(role=role, text=text)])


class ResponseToConversation(Executor):
    """
    Converte AgentExecutorResponse para list[ChatMessage].
    
    Extrai mensagens do response do agente e normaliza para formato
    de conversação padrão.
    
    Padrão do framework: Usado entre agentes em workflows sequenciais
    para manter a conversa fluindo.
    """
    
    def __init__(self, id: str = "response_normalizer"):
        super().__init__(id)
    
    @handler
    async def from_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[List[ChatMessage], Never]
    ) -> None:
        """Extrai mensagens do AgentExecutorResponse."""
        messages = []
        
        # Extrair do agent_run_response
        if hasattr(response, 'agent_run_response'):
            agent_resp = response.agent_run_response
            if hasattr(agent_resp, 'messages') and agent_resp.messages:
                messages.extend(list(agent_resp.messages))
            elif hasattr(agent_resp, 'text') and agent_resp.text:
                messages.append(ChatMessage(
                    role=Role.ASSISTANT,
                    text=agent_resp.text
                ))
        
        # Fallback: usar full_conversation
        if not messages and hasattr(response, 'full_conversation'):
            if response.full_conversation:
                messages.extend(list(response.full_conversation))
        
        # Último fallback: criar mensagem vazia
        if not messages:
            messages.append(ChatMessage(
                role=Role.ASSISTANT,
                text="(no response)"
            ))
        
        await ctx.send_message(messages)
    
    @handler
    async def from_messages(
        self,
        messages: List[ChatMessage],
        ctx: WorkflowContext[List[ChatMessage], Never]
    ) -> None:
        """Passthrough para mensagens já normalizadas."""
        await ctx.send_message(messages)


class EndWithConversation(Executor):
    """
    Executor terminal que finaliza o workflow com list[ChatMessage].
    
    Padrão do framework: Usado como último nó em workflows que 
    retornam a conversa completa.
    
    Diferente do yield_agent_response que retorna apenas o texto,
    este preserva todo o histórico de mensagens.
    """
    
    def __init__(self, id: str = "conversation_output"):
        super().__init__(id)
    
    @handler
    async def from_messages(
        self,
        messages: List[ChatMessage],
        ctx: WorkflowContext[Never, List[ChatMessage]]
    ) -> None:
        """Emite lista de mensagens como output final."""
        await ctx.yield_output(messages)
    
    @handler
    async def from_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[Never, List[ChatMessage]]
    ) -> None:
        """Extrai e emite mensagens do AgentExecutorResponse."""
        messages = []
        
        if hasattr(response, 'full_conversation') and response.full_conversation:
            messages = list(response.full_conversation)
        elif hasattr(response, 'agent_run_response'):
            agent_resp = response.agent_run_response
            if hasattr(agent_resp, 'messages') and agent_resp.messages:
                messages = list(agent_resp.messages)
        
        await ctx.yield_output(messages)


class EndWithText(Executor):
    """
    Executor terminal que finaliza o workflow com string.
    
    Extrai o texto da última mensagem e emite como output.
    Alternativa ao @executor yield_agent_response para quando
    precisamos de classe Executor em vez de função.
    """
    
    def __init__(self, id: str = "text_output"):
        super().__init__(id)
    
    @handler
    async def from_messages(
        self,
        messages: List[ChatMessage],
        ctx: WorkflowContext[Never, str]
    ) -> None:
        """Extrai texto da última mensagem."""
        if messages:
            last = messages[-1]
            text = getattr(last, 'text', '') or str(last)
        else:
            text = ""
        await ctx.yield_output(text)
    
    @handler
    async def from_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[Never, str]
    ) -> None:
        """Extrai texto do AgentExecutorResponse."""
        text = ""
        if hasattr(response, 'agent_run_response'):
            text = response.agent_run_response.text or ""
        await ctx.yield_output(text)
    
    @handler
    async def from_str(
        self,
        text: str,
        ctx: WorkflowContext[Never, str]
    ) -> None:
        """Passthrough para strings."""
        await ctx.yield_output(text)


class RouterDispatcher(Executor):
    """
    Dispatcher para workflows de Router.
    
    Encaminha a mensagem para um executor específico baseado
    no ID do target. Usado internamente pelo RouterStrategy.
    
    Padrão do framework: Similar ao _DispatchToAllParticipants
    do ConcurrentBuilder, mas com routing condicional.
    """
    
    def __init__(self, id: str = "router_dispatcher"):
        super().__init__(id)
        self._routes: dict = {}
    
    def add_route(self, condition: str, target_id: str) -> None:
        """Registra uma rota condição → target."""
        self._routes[condition.lower()] = target_id
    
    def set_default(self, target_id: str) -> None:
        """Define rota padrão."""
        self._routes['__default__'] = target_id
    
    @handler
    async def dispatch(
        self,
        classification: str,
        ctx: WorkflowContext[str, Never]
    ) -> None:
        """Despacha para o target baseado na classificação."""
        classification_lower = classification.strip().lower()
        
        # Procurar rota exata
        target_id = self._routes.get(classification_lower)
        
        # Fallback para default
        if not target_id:
            target_id = self._routes.get('__default__')
        
        if target_id:
            await ctx.send_message(classification, target_id=target_id)
        else:
            # Sem rota encontrada, enviar para todos (broadcast)
            await ctx.send_message(classification)
