"""
Camada de Mensagens e Prompts (PromptEngine).

Este módulo fornece uma abstração robusta para gerenciamento de prompts,
similar ao LangChain, incluindo:

- PromptTemplate: Templates com variáveis dinâmicas
- MessageBuilder: Construção de mensagens estruturadas
- ConversationalContext: Gerenciamento de histórico
- PromptEngine: Orquestração de renderização

Uso:
    ```python
    from src.worker.prompts import PromptTemplate, MessageBuilder, PromptEngine
    
    # Template simples
    template = PromptTemplate(
        template="Analise o seguinte texto: {texto}",
        input_variables=["texto"]
    )
    rendered = template.format(texto="Olá mundo")
    
    # MessageBuilder
    messages = MessageBuilder()
        .system("Você é um assistente útil")
        .user("Olá!")
        .build()
    
    # PromptEngine com contexto
    engine = PromptEngine()
    engine.add_template("analise", template)
    result = engine.render("analise", texto="Conteúdo...")
    ```
"""

from src.worker.prompts.models import (
    PromptTemplate,
    PromptVariable,
    PromptChain,
    PromptConfig,
)
from src.worker.prompts.messages import MessageBuilder, MessageRole
from src.worker.prompts.context import ConversationalContext
from src.worker.prompts.engine import PromptEngine

__all__ = [
    # Models
    "PromptTemplate",
    "PromptVariable",
    "PromptChain",
    "PromptConfig",
    # Messages
    "MessageBuilder",
    "MessageRole",
    # Context
    "ConversationalContext",
    # Engine
    "PromptEngine",
]
