from typing import Any, Callable, Awaitable
from inspect import isasyncgen, isgenerator
from agent_framework import AgentMiddleware, AgentRunContext, ChatMessage

class EventMiddleware(AgentMiddleware):
    """
    Middleware para emitir eventos de execução do agente.
    
    NOTA: Eventos de agente agora são controlados pelo WorkflowEngine
    para capturar conteúdo completo do WorkflowOutputEvent.
    Este middleware foi desabilitado para evitar duplicação.
    """
    
    def __init__(self, agent_name: str, emit_events: bool = False):
        self.agent_name = agent_name
        self.emit_events = emit_events  # Desabilitado por padrão
        
    async def process(self, context: AgentRunContext, next: Callable[[AgentRunContext], Awaitable[None]]) -> None:
        # Eventos agora são controlados pelo engine via run_stream()
        # Este middleware apenas executa o próximo handler
        await next(context)
    
    def _extract_content(self, result: Any) -> str:
        """
        Extrai conteúdo de diferentes tipos de resultado.
        
        Trata corretamente:
        - Strings
        - Objetos com atributos text/content
        - Listas de mensagens
        - AsyncGenerators/Generators (retorna placeholder)
        """
        if result is None:
            return "Completed"
        
        # Verificar se é um generator/async generator (stream)
        # Não consumimos streams aqui - apenas indicamos que é streaming
        if isasyncgen(result) or isgenerator(result):
            return "[Streaming response...]"
        
        # String direta
        if isinstance(result, str):
            return result
        
        # Objeto com text/content
        if hasattr(result, "text") and result.text:
            return str(result.text)
        if hasattr(result, "content") and result.content:
            return str(result.content)
        
        # Lista de mensagens
        if isinstance(result, list) and result:
            last_msg = result[-1]
            if hasattr(last_msg, "text") and last_msg.text:
                return str(last_msg.text)
            if hasattr(last_msg, "content") and last_msg.content:
                return str(last_msg.content)
            return str(last_msg)
        
        # Fallback
        result_str = str(result)
        
        # Detectar representação de async_generator
        if "async_generator" in result_str or "generator object" in result_str:
            return "[Streaming response...]"
        
        return result_str


class EnhancedTemplateMiddleware(AgentMiddleware):
    def __init__(self, template: str):
        self.template = template

    async def process(self, context: AgentRunContext, next: Callable[[AgentRunContext], Awaitable[None]]) -> None:
        messages = context.messages
        last_content = ""
        
        # Extrair conteúdo da última mensagem
        if isinstance(messages, list) and messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "text"):
                last_content = str(last_msg.text)
            elif isinstance(last_msg, dict) and "content" in last_msg:
                last_content = str(last_msg["content"])
            else:
                last_content = str(last_msg)
        elif isinstance(messages, str):
            last_content = messages
            
        # Aplicar template PRESERVANDO o input original
        if "{{user_input}}" in self.template:
            new_content = self.template.replace("{{user_input}}", last_content)
        elif "{{previous_output}}" in self.template:
            new_content = self.template.replace("{{previous_output}}", last_content)
        else:
            # Se não tem placeholders, adiciona o template como contexto
            new_content = f"{self.template}\n\nInput do usuário: {last_content}"
        
        # Atualizar mensagem preservando role
        if isinstance(messages, list) and messages:
            last_msg = messages[-1]
            if isinstance(last_msg, ChatMessage):
                new_msg = ChatMessage(role=last_msg.role, text=new_content)
                messages[-1] = new_msg
            elif isinstance(last_msg, dict):
                last_msg["content"] = new_content
            else:
                messages[-1] = new_content

        await next(context)
