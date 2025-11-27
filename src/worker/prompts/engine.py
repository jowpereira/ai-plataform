"""
PromptEngine - Orquestrador de templates e mensagens.

Gerencia o ciclo de vida de prompts, incluindo:
- Registro de templates
- Renderização com contexto
- Composição de chains
- Validação
"""

from typing import Any, Dict, List, Optional, Union

from src.worker.prompts.models import PromptTemplate, PromptChain, PromptConfig
from src.worker.prompts.messages import MessageBuilder, MessageRole, Message
from src.worker.prompts.context import ConversationalContext


class PromptEngine:
    """
    Motor de renderização de prompts.
    
    Centraliza o gerenciamento de templates e fornece
    uma API unificada para renderização.
    
    Exemplo:
        ```python
        engine = PromptEngine()
        
        # Registrar templates
        engine.register_template("saudacao", PromptTemplate(
            template="Olá {nome}, bem-vindo ao {sistema}!"
        ))
        
        # Renderizar com variáveis
        result = engine.render("saudacao", nome="João", sistema="AI Platform")
        # -> "Olá João, bem-vindo ao AI Platform!"
        
        # Usar com contexto
        ctx = ConversationalContext()
        ctx.set_variable("nome", "Maria")
        result = engine.render_with_context("saudacao", ctx, sistema="AI Platform")
        # -> "Olá Maria, bem-vindo ao AI Platform!"
        ```
    """
    
    def __init__(self, config: Optional[PromptConfig] = None):
        """
        Inicializa o engine.
        
        Args:
            config: Configuração opcional com templates pré-definidos
        """
        self._templates: Dict[str, PromptTemplate] = {}
        self._chains: Dict[str, PromptChain] = {}
        self._default_variables: Dict[str, Any] = {}
        
        # Carregar configuração se fornecida
        if config:
            self._load_config(config)
    
    def _load_config(self, config: PromptConfig) -> None:
        """Carrega templates e chains de uma configuração."""
        for name, template in config.templates.items():
            self._templates[name] = template
        
        for chain in config.chains:
            self._chains[chain.name] = chain
        
        self._default_variables.update(config.default_variables)
    
    # =========================================================================
    # Registro de Templates
    # =========================================================================
    
    def register_template(
        self,
        name: str,
        template: Union[PromptTemplate, str]
    ) -> None:
        """
        Registra um template.
        
        Args:
            name: Nome identificador
            template: PromptTemplate ou string simples
        """
        if isinstance(template, str):
            template = PromptTemplate.from_string(template)
        self._templates[name] = template
    
    def register_chain(self, chain: PromptChain) -> None:
        """Registra uma chain de prompts."""
        self._chains[chain.name] = chain
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Obtém um template registrado."""
        return self._templates.get(name)
    
    def get_chain(self, name: str) -> Optional[PromptChain]:
        """Obtém uma chain registrada."""
        return self._chains.get(name)
    
    def list_templates(self) -> List[str]:
        """Lista nomes de templates registrados."""
        return list(self._templates.keys())
    
    def list_chains(self) -> List[str]:
        """Lista nomes de chains registradas."""
        return list(self._chains.keys())
    
    # =========================================================================
    # Variáveis Padrão
    # =========================================================================
    
    def set_default_variable(self, name: str, value: Any) -> None:
        """Define uma variável padrão global."""
        self._default_variables[name] = value
    
    def set_default_variables(self, variables: Dict[str, Any]) -> None:
        """Define múltiplas variáveis padrão."""
        self._default_variables.update(variables)
    
    def clear_defaults(self) -> None:
        """Limpa variáveis padrão."""
        self._default_variables.clear()
    
    # =========================================================================
    # Renderização
    # =========================================================================
    
    def render(self, template_name: str, **kwargs: Any) -> str:
        """
        Renderiza um template registrado.
        
        Args:
            template_name: Nome do template
            **kwargs: Variáveis para substituição
            
        Returns:
            String renderizada
            
        Raises:
            KeyError: Se template não encontrado
            ValueError: Se variável obrigatória faltando
        """
        template = self._templates.get(template_name)
        if not template:
            raise KeyError(f"Template '{template_name}' não encontrado")
        
        # Mesclar defaults com kwargs (kwargs tem prioridade)
        variables = {**self._default_variables, **kwargs}
        
        return template.format(**variables)
    
    def render_template(self, template: PromptTemplate, **kwargs: Any) -> str:
        """
        Renderiza um template diretamente (não precisa estar registrado).
        
        Args:
            template: PromptTemplate a renderizar
            **kwargs: Variáveis
            
        Returns:
            String renderizada
        """
        variables = {**self._default_variables, **kwargs}
        return template.format(**variables)
    
    def render_string(self, template_str: str, **kwargs: Any) -> str:
        """
        Renderiza uma string de template diretamente.
        
        Args:
            template_str: String com placeholders
            **kwargs: Variáveis
            
        Returns:
            String renderizada
        """
        template = PromptTemplate.from_string(template_str)
        return self.render_template(template, **kwargs)
    
    def render_with_context(
        self,
        template_name: str,
        context: ConversationalContext,
        **kwargs: Any
    ) -> str:
        """
        Renderiza usando variáveis do contexto conversacional.
        
        Args:
            template_name: Nome do template
            context: Contexto com variáveis
            **kwargs: Variáveis adicionais (sobrescrevem contexto)
            
        Returns:
            String renderizada
        """
        # Prioridade: kwargs > context > defaults
        variables = {
            **self._default_variables,
            **context.variables,
            **kwargs
        }
        
        template = self._templates.get(template_name)
        if not template:
            raise KeyError(f"Template '{template_name}' não encontrado")
        
        return template.format(**variables)
    
    # =========================================================================
    # Chains
    # =========================================================================
    
    def render_chain(
        self,
        chain_name: str,
        initial_variables: Optional[Dict[str, Any]] = None,
        step_callback: Optional[callable] = None
    ) -> List[str]:
        """
        Executa uma chain de prompts.
        
        Args:
            chain_name: Nome da chain
            initial_variables: Variáveis iniciais
            step_callback: Função chamada após cada step (opcional)
            
        Returns:
            Lista de resultados de cada step
        """
        chain = self._chains.get(chain_name)
        if not chain:
            raise KeyError(f"Chain '{chain_name}' não encontrada")
        
        variables = {**self._default_variables, **(initial_variables or {})}
        results = []
        
        for i, step in enumerate(chain.steps):
            result = step.format(**variables)
            results.append(result)
            
            # Disponibilizar resultado para próximo step
            variables[f"step{i}_output"] = result
            variables["last_output"] = result
            
            if step_callback:
                step_callback(i, result, variables)
        
        return results
    
    # =========================================================================
    # Construção de Mensagens
    # =========================================================================
    
    def build_messages(
        self,
        system_template: Optional[str] = None,
        user_template: Optional[str] = None,
        context: Optional[ConversationalContext] = None,
        **kwargs: Any
    ) -> MessageBuilder:
        """
        Constrói mensagens a partir de templates.
        
        Args:
            system_template: Nome do template para system message
            user_template: Nome do template para user message
            context: Contexto opcional
            **kwargs: Variáveis
            
        Returns:
            MessageBuilder configurado
        """
        builder = MessageBuilder()
        variables = {**self._default_variables, **kwargs}
        
        if context:
            variables.update(context.variables)
        
        if system_template:
            system_content = self.render(system_template, **variables)
            builder.system(system_content)
        
        # Incluir histórico do contexto se disponível
        if context:
            for msg in context.get_messages(include_system=False):
                builder.add(msg.role, msg.content, msg.name)
        
        if user_template:
            user_content = self.render(user_template, **variables)
            builder.user(user_content)
        
        return builder
    
    # =========================================================================
    # Validação
    # =========================================================================
    
    def validate_template(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> List[str]:
        """
        Valida se as variáveis fornecidas são suficientes.
        
        Args:
            template_name: Nome do template
            variables: Variáveis a validar
            
        Returns:
            Lista de erros (vazia se válido)
        """
        template = self._templates.get(template_name)
        if not template:
            return [f"Template '{template_name}' não encontrado"]
        
        errors = []
        all_vars = {**self._default_variables, **variables}
        
        for var in template.input_variables:
            if var.required and var.name not in all_vars and var.default is None:
                errors.append(f"Variável obrigatória '{var.name}' não fornecida")
        
        return errors
    
    def validate_all(self, variables: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valida todos os templates registrados.
        
        Returns:
            Dicionário de template_name -> lista de erros
        """
        results = {}
        for name in self._templates:
            errors = self.validate_template(name, variables)
            if errors:
                results[name] = errors
        return results
