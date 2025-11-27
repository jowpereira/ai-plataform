"""
Construção de mensagens estruturadas.

Fornece uma API fluente para construir sequências de mensagens
compatíveis com o agent_framework.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class MessageRole(str, Enum):
    """Papéis de mensagem suportados."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"  # Legacy, mapeado para tool


@dataclass
class Message:
    """
    Representação interna de uma mensagem.
    
    Attributes:
        role: Papel do remetente (system, user, assistant, tool)
        content: Conteúdo textual da mensagem
        name: Nome opcional do remetente
        metadata: Dados adicionais (tool_call_id, function_name, etc.)
    """
    role: MessageRole
    content: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário compatível com APIs."""
        result = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.name:
            result["name"] = self.name
        # Incluir metadados específicos
        if "tool_call_id" in self.metadata:
            result["tool_call_id"] = self.metadata["tool_call_id"]
        return result


class MessageBuilder:
    """
    Builder fluente para construção de mensagens.
    
    Permite criar sequências de mensagens de forma legível:
    
    ```python
    messages = (
        MessageBuilder()
        .system("Você é um assistente útil")
        .user("Olá!")
        .assistant("Olá! Como posso ajudar?")
        .user("Qual a capital do Brasil?")
        .build()
    )
    ```
    """
    
    def __init__(self):
        self._messages: List[Message] = []
    
    def add(
        self,
        role: MessageRole,
        content: str,
        name: Optional[str] = None,
        **metadata: Any
    ) -> "MessageBuilder":
        """
        Adiciona uma mensagem genérica.
        
        Args:
            role: Papel da mensagem
            content: Conteúdo
            name: Nome opcional
            **metadata: Metadados adicionais
            
        Returns:
            Self para encadeamento
        """
        self._messages.append(Message(
            role=role,
            content=content,
            name=name,
            metadata=metadata
        ))
        return self
    
    def system(self, content: str, name: Optional[str] = None) -> "MessageBuilder":
        """Adiciona mensagem de sistema."""
        return self.add(MessageRole.SYSTEM, content, name)
    
    def user(self, content: str, name: Optional[str] = None) -> "MessageBuilder":
        """Adiciona mensagem do usuário."""
        return self.add(MessageRole.USER, content, name)
    
    def assistant(self, content: str, name: Optional[str] = None) -> "MessageBuilder":
        """Adiciona mensagem do assistente."""
        return self.add(MessageRole.ASSISTANT, content, name)
    
    def tool(
        self,
        content: str,
        tool_call_id: str,
        name: Optional[str] = None
    ) -> "MessageBuilder":
        """
        Adiciona resultado de chamada de ferramenta.
        
        Args:
            content: Resultado da ferramenta
            tool_call_id: ID da chamada de ferramenta
            name: Nome da ferramenta
        """
        return self.add(
            MessageRole.TOOL,
            content,
            name,
            tool_call_id=tool_call_id
        )
    
    def from_template(
        self,
        role: MessageRole,
        template: "PromptTemplate",
        **kwargs: Any
    ) -> "MessageBuilder":
        """
        Adiciona mensagem renderizada a partir de um template.
        
        Args:
            role: Papel da mensagem
            template: PromptTemplate a renderizar
            **kwargs: Variáveis para o template
        """
        from src.worker.prompts.models import PromptTemplate
        
        content = template.format(**kwargs)
        return self.add(role, content)
    
    def extend(self, messages: List[Message]) -> "MessageBuilder":
        """Adiciona múltiplas mensagens de uma vez."""
        self._messages.extend(messages)
        return self
    
    def clear(self) -> "MessageBuilder":
        """Limpa todas as mensagens."""
        self._messages.clear()
        return self
    
    def build(self) -> List[Message]:
        """
        Constrói e retorna a lista de mensagens.
        
        Returns:
            Lista de Message
        """
        return list(self._messages)
    
    def build_dicts(self) -> List[Dict[str, Any]]:
        """
        Constrói e retorna como lista de dicionários.
        
        Útil para enviar diretamente a APIs.
        
        Returns:
            Lista de dicts compatíveis com OpenAI/Azure
        """
        return [msg.to_dict() for msg in self._messages]
    
    def to_framework_messages(self) -> List[Any]:
        """
        Converte para mensagens do agent_framework.
        
        Returns:
            Lista de ChatMessage do framework
        """
        from agent_framework import ChatMessage, SystemMessage, UserMessage, AssistantMessage
        
        result = []
        for msg in self._messages:
            if msg.role == MessageRole.SYSTEM:
                result.append(SystemMessage(content=msg.content))
            elif msg.role == MessageRole.USER:
                result.append(UserMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                result.append(AssistantMessage(content=msg.content))
            else:
                # Fallback para ChatMessage genérico
                result.append(ChatMessage(role=msg.role.value, content=msg.content))
        
        return result
    
    @property
    def count(self) -> int:
        """Número de mensagens atuais."""
        return len(self._messages)
    
    @property
    def last(self) -> Optional[Message]:
        """Última mensagem adicionada."""
        return self._messages[-1] if self._messages else None
