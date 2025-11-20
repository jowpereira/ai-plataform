from typing import Any, Callable, Awaitable
from agent_framework import AgentMiddleware, AgentRunContext, ChatMessage

class TemplateMiddleware(AgentMiddleware):
    def __init__(self, template: str):
        self.template = template

    async def process(self, context: AgentRunContext, next: Callable[[AgentRunContext], Awaitable[None]]) -> None:
        # Acessar as mensagens do contexto
        messages = context.messages
        last_content = ""
        
        # Extrair o conteúdo da última mensagem (input atual)
        if isinstance(messages, list) and messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "text"):
                # ChatMessage
                last_content = str(last_msg.text)
            elif isinstance(last_msg, dict) and "content" in last_msg:
                # Dict
                last_content = str(last_msg["content"])
            else:
                # String ou outro
                last_content = str(last_msg)
        elif isinstance(messages, str):
            last_content = messages
            
        # Aplicar o template
        # Substitui {{user_input}} e {{previous_output}} pelo conteúdo atual
        new_content = self.template.replace("{{user_input}}", last_content)
        new_content = new_content.replace("{{previous_output}}", last_content)
        
        # Atualizar a mensagem no contexto
        # Se for string, substituímos. Se for lista, atualizamos o último elemento.
        if isinstance(messages, str):
            # context.messages é tipado como list[ChatMessage], mas em runtime pode variar?
            # O framework garante list[ChatMessage].
            # Se for string, algo está errado, mas mantemos a lógica defensiva.
            pass 
        elif isinstance(messages, list) and messages:
            last_msg = messages[-1]
            if isinstance(last_msg, ChatMessage):
                # Criar nova mensagem com o conteúdo atualizado
                # Preservamos o role original
                new_msg = ChatMessage(role=last_msg.role, text=new_content)
                messages[-1] = new_msg
            elif isinstance(last_msg, dict):
                last_msg["content"] = new_content
            else:
                # Se era string na lista
                messages[-1] = new_content # type: ignore

        await next(context)

        await next(context)
