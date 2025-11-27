"""
Modelos Pydantic para a camada de Prompts.

Define estruturas validadas para templates, variáveis e chains de prompts.
"""

import re
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class VariableType(str, Enum):
    """Tipos de variáveis suportadas em templates."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LIST = "list"
    OBJECT = "object"
    ANY = "any"


class PromptVariable(BaseModel):
    """
    Definição de uma variável de template.
    
    Attributes:
        name: Nome da variável (usado no template como {name})
        type: Tipo esperado da variável
        description: Descrição para documentação
        default: Valor padrão se não fornecido
        required: Se a variável é obrigatória
    """
    name: str = Field(..., description="Nome da variável")
    type: VariableType = Field(default=VariableType.STRING, description="Tipo da variável")
    description: Optional[str] = Field(None, description="Descrição da variável")
    default: Optional[Any] = Field(None, description="Valor padrão")
    required: bool = Field(default=True, description="Se é obrigatória")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que o nome é um identificador válido."""
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError(
                f"Nome de variável inválido: '{v}'. "
                "Deve começar com letra ou underscore e conter apenas alfanuméricos."
            )
        return v


class PromptTemplate(BaseModel):
    """
    Template de prompt com suporte a variáveis dinâmicas.
    
    Suporta dois formatos de interpolação:
    - Python f-string style: {variable}
    - Jinja2 style: {{ variable }} (para templates mais complexos)
    
    Attributes:
        template: String do template com placeholders
        input_variables: Lista de variáveis esperadas
        metadata: Metadados opcionais do template
        
    Example:
        ```python
        template = PromptTemplate(
            template="Analise o texto: {texto}\\nTom: {tom}",
            input_variables=[
                PromptVariable(name="texto", required=True),
                PromptVariable(name="tom", default="neutro")
            ]
        )
        result = template.format(texto="Olá mundo")
        # -> "Analise o texto: Olá mundo\\nTom: neutro"
        ```
    """
    template: str = Field(..., description="Template com placeholders {var}")
    input_variables: List[PromptVariable] = Field(
        default_factory=list,
        description="Variáveis esperadas no template"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados opcionais"
    )
    
    @model_validator(mode="after")
    def validate_template_variables(self) -> "PromptTemplate":
        """Valida que todas as variáveis do template estão definidas."""
        # Extrair variáveis do template
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        found_vars = set(re.findall(pattern, self.template))
        
        # Variáveis definidas
        defined_vars = {v.name for v in self.input_variables}
        
        # Verificar variáveis não definidas
        undefined = found_vars - defined_vars
        if undefined:
            # Auto-criar variáveis simples para conveniência
            for var_name in undefined:
                self.input_variables.append(
                    PromptVariable(name=var_name, required=True)
                )
        
        return self
    
    def format(self, **kwargs: Any) -> str:
        """
        Renderiza o template com os valores fornecidos.
        
        Args:
            **kwargs: Valores para as variáveis
            
        Returns:
            String renderizada
            
        Raises:
            ValueError: Se variável obrigatória não fornecida
        """
        # Coletar valores com defaults
        values: Dict[str, Any] = {}
        
        for var in self.input_variables:
            if var.name in kwargs:
                values[var.name] = kwargs[var.name]
            elif var.default is not None:
                values[var.name] = var.default
            elif var.required:
                raise ValueError(
                    f"Variável obrigatória '{var.name}' não fornecida"
                )
        
        # Renderizar
        try:
            return self.template.format(**values)
        except KeyError as e:
            raise ValueError(f"Variável não encontrada no template: {e}")
    
    def get_variable_names(self) -> List[str]:
        """Retorna lista de nomes de variáveis."""
        return [v.name for v in self.input_variables]
    
    def get_required_variables(self) -> List[str]:
        """Retorna lista de variáveis obrigatórias."""
        return [v.name for v in self.input_variables if v.required]
    
    @classmethod
    def from_string(cls, template_str: str) -> "PromptTemplate":
        """
        Cria um PromptTemplate a partir de uma string simples.
        
        Extrai automaticamente as variáveis do template.
        
        Args:
            template_str: String com placeholders {var}
            
        Returns:
            PromptTemplate configurado
        """
        return cls(template=template_str, input_variables=[])


class PromptChain(BaseModel):
    """
    Cadeia de prompts para composição.
    
    Permite criar pipelines de prompts onde a saída de um
    pode alimentar a entrada do próximo.
    
    Attributes:
        steps: Lista de templates na ordem de execução
        name: Nome identificador da chain
    """
    name: str = Field(..., description="Nome da chain")
    steps: List[PromptTemplate] = Field(..., description="Templates em ordem")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_all_variables(self) -> List[str]:
        """Retorna todas as variáveis de todos os steps."""
        all_vars: List[str] = []
        for step in self.steps:
            all_vars.extend(step.get_variable_names())
        return list(set(all_vars))
    
    def get_step(self, index: int) -> Optional[PromptTemplate]:
        """Obtém um step pelo índice."""
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None


class PromptConfig(BaseModel):
    """
    Configuração de prompts para inclusão no WorkerConfig.
    
    Permite definir templates e chains no arquivo de configuração YAML/JSON.
    
    Example:
        ```yaml
        prompts:
          templates:
            analise:
              template: "Analise: {texto}"
              variables:
                - name: texto
                  required: true
          chains:
            - name: pipeline_completo
              steps:
                - template: "Passo 1: {input}"
                - template: "Passo 2: {step1_output}"
        ```
    """
    templates: Dict[str, PromptTemplate] = Field(
        default_factory=dict,
        description="Templates nomeados"
    )
    chains: List[PromptChain] = Field(
        default_factory=list,
        description="Chains de prompts"
    )
    default_variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Variáveis globais padrão"
    )
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Obtém um template pelo nome."""
        return self.templates.get(name)
    
    def get_chain(self, name: str) -> Optional[PromptChain]:
        """Obtém uma chain pelo nome."""
        for chain in self.chains:
            if chain.name == name:
                return chain
        return None
