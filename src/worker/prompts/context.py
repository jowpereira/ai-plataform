"""
Contexto conversacional para gerenciamento de histórico.

Gerencia o estado da conversa, incluindo:
- Histórico de mensagens
- Variáveis dinâmicas
- Memória de curto prazo
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.worker.prompts.messages import Message, MessageRole


@dataclass
class ConversationTurn:
    """
    Representa um turno de conversa (pergunta + resposta).
    
    Attributes:
        user_message: Mensagem do usuário
        assistant_message: Resposta do assistente
        timestamp: Momento do turno
        metadata: Dados adicionais (tool calls, etc.)
    """
    user_message: str
    assistant_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationalContext:
    """
    Gerenciador de contexto conversacional.
    
    Mantém histórico de mensagens, variáveis de sessão e
    fornece métodos para manipulação do contexto.
    
    Exemplo:
        ```python
        ctx = ConversationalContext(max_history=10)
        
        # Adicionar variáveis
        ctx.set_variable("user_name", "João")
        ctx.set_variable("preference", "formal")
        
        # Adicionar mensagem
        ctx.add_user_message("Olá!")
        ctx.add_assistant_message("Olá {user_name}!")
        
        # Obter histórico formatado
        history = ctx.get_formatted_history()
        
        # Renderizar template com contexto
        rendered = ctx.render_with_context("Olá {user_name}, como vai?")
        ```
    """
    
    def __init__(
        self,
        max_history: int = 50,
        max_tokens_estimate: int = 4000,
        session_id: Optional[str] = None
    ):
        """
        Inicializa o contexto.
        
        Args:
            max_history: Número máximo de mensagens a manter
            max_tokens_estimate: Limite estimado de tokens para histórico
            session_id: ID opcional da sessão
        """
        self.max_history = max_history
        self.max_tokens_estimate = max_tokens_estimate
        self.session_id = session_id or self._generate_session_id()
        
        self._messages: List[Message] = []
        self._variables: Dict[str, Any] = {}
        self._turns: List[ConversationTurn] = []
        self._system_message: Optional[str] = None
        self._created_at = datetime.now()
    
    def _generate_session_id(self) -> str:
        """Gera um ID de sessão único."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    # =========================================================================
    # Gerenciamento de Variáveis
    # =========================================================================
    
    def set_variable(self, name: str, value: Any) -> None:
        """Define uma variável de contexto."""
        self._variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Obtém uma variável de contexto."""
        return self._variables.get(name, default)
    
    def update_variables(self, variables: Dict[str, Any]) -> None:
        """Atualiza múltiplas variáveis de uma vez."""
        self._variables.update(variables)
    
    def clear_variables(self) -> None:
        """Limpa todas as variáveis."""
        self._variables.clear()
    
    @property
    def variables(self) -> Dict[str, Any]:
        """Retorna cópia das variáveis."""
        return dict(self._variables)
    
    # =========================================================================
    # Gerenciamento de Mensagens
    # =========================================================================
    
    def set_system_message(self, content: str) -> None:
        """Define a mensagem de sistema."""
        self._system_message = content
    
    def add_message(self, message: Message) -> None:
        """Adiciona uma mensagem ao histórico."""
        self._messages.append(message)
        self._trim_history()
    
    def add_user_message(self, content: str, name: Optional[str] = None) -> None:
        """Adiciona mensagem do usuário."""
        self.add_message(Message(
            role=MessageRole.USER,
            content=content,
            name=name
        ))
        # Iniciar novo turno
        self._turns.append(ConversationTurn(user_message=content))
    
    def add_assistant_message(self, content: str, name: Optional[str] = None) -> None:
        """Adiciona mensagem do assistente."""
        self.add_message(Message(
            role=MessageRole.ASSISTANT,
            content=content,
            name=name
        ))
        # Completar turno atual
        if self._turns and self._turns[-1].assistant_message is None:
            self._turns[-1].assistant_message = content
    
    def add_tool_result(
        self,
        content: str,
        tool_call_id: str,
        tool_name: Optional[str] = None
    ) -> None:
        """Adiciona resultado de chamada de ferramenta."""
        self.add_message(Message(
            role=MessageRole.TOOL,
            content=content,
            name=tool_name,
            metadata={"tool_call_id": tool_call_id}
        ))
    
    def _trim_history(self) -> None:
        """Remove mensagens antigas se exceder o limite."""
        if len(self._messages) > self.max_history:
            # Manter as mensagens mais recentes
            excess = len(self._messages) - self.max_history
            self._messages = self._messages[excess:]
    
    # =========================================================================
    # Acesso ao Histórico
    # =========================================================================
    
    def get_messages(self, include_system: bool = True) -> List[Message]:
        """
        Retorna o histórico de mensagens.
        
        Args:
            include_system: Se deve incluir mensagem de sistema
            
        Returns:
            Lista de mensagens
        """
        result = []
        
        if include_system and self._system_message:
            result.append(Message(
                role=MessageRole.SYSTEM,
                content=self._system_message
            ))
        
        result.extend(self._messages)
        return result
    
    def get_formatted_history(
        self,
        format_template: str = "{role}: {content}",
        separator: str = "\n"
    ) -> str:
        """
        Retorna histórico formatado como string.
        
        Args:
            format_template: Template para cada mensagem
            separator: Separador entre mensagens
            
        Returns:
            String formatada
        """
        lines = []
        for msg in self._messages:
            lines.append(format_template.format(
                role=msg.role.value,
                content=msg.content,
                name=msg.name or ""
            ))
        return separator.join(lines)
    
    def get_last_n_messages(self, n: int) -> List[Message]:
        """Retorna as últimas N mensagens."""
        return self._messages[-n:] if n > 0 else []
    
    def get_turns(self) -> List[ConversationTurn]:
        """Retorna os turnos de conversa."""
        return list(self._turns)
    
    # =========================================================================
    # Renderização com Contexto
    # =========================================================================
    
    def render_with_context(self, template: str) -> str:
        """
        Renderiza um template usando as variáveis do contexto.
        
        Args:
            template: String com placeholders {var}
            
        Returns:
            String renderizada
        """
        try:
            return template.format(**self._variables)
        except KeyError as e:
            # Retornar template original se variável não encontrada
            return template
    
    def get_context_for_prompt(self) -> Dict[str, Any]:
        """
        Retorna dicionário com todo o contexto para uso em prompts.
        
        Inclui variáveis, metadados de sessão e resumo do histórico.
        """
        return {
            **self._variables,
            "session_id": self.session_id,
            "message_count": len(self._messages),
            "turn_count": len(self._turns),
            "last_user_message": self._get_last_user_message(),
            "last_assistant_message": self._get_last_assistant_message(),
        }
    
    def _get_last_user_message(self) -> Optional[str]:
        """Obtém a última mensagem do usuário."""
        for msg in reversed(self._messages):
            if msg.role == MessageRole.USER:
                return msg.content
        return None
    
    def _get_last_assistant_message(self) -> Optional[str]:
        """Obtém a última mensagem do assistente."""
        for msg in reversed(self._messages):
            if msg.role == MessageRole.ASSISTANT:
                return msg.content
        return None
    
    # =========================================================================
    # Serialização
    # =========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa o contexto para dicionário."""
        return {
            "session_id": self.session_id,
            "created_at": self._created_at.isoformat(),
            "variables": self._variables,
            "system_message": self._system_message,
            "messages": [msg.to_dict() for msg in self._messages],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationalContext":
        """Reconstrói contexto a partir de dicionário."""
        ctx = cls(session_id=data.get("session_id"))
        ctx._variables = data.get("variables", {})
        ctx._system_message = data.get("system_message")
        
        for msg_data in data.get("messages", []):
            ctx.add_message(Message(
                role=MessageRole(msg_data["role"]),
                content=msg_data["content"],
                name=msg_data.get("name")
            ))
        
        return ctx
    
    # =========================================================================
    # Utilitários
    # =========================================================================
    
    def clear(self) -> None:
        """Limpa todo o contexto (mensagens e variáveis)."""
        self._messages.clear()
        self._variables.clear()
        self._turns.clear()
        self._system_message = None
    
    def clear_history(self) -> None:
        """Limpa apenas o histórico de mensagens."""
        self._messages.clear()
        self._turns.clear()
    
    @property
    def is_empty(self) -> bool:
        """Verifica se o contexto está vazio."""
        return len(self._messages) == 0
    
    def __len__(self) -> int:
        """Número de mensagens no histórico."""
        return len(self._messages)
