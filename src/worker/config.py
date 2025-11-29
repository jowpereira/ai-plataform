import os
import re
from typing import Any, Dict, List, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class ToolConfig(BaseModel):
    id: str = Field(..., description="Identificador único da ferramenta")
    path: str = Field(..., description="Caminho de importação (module:function)")
    description: Optional[str] = Field(None, description="Descrição opcional da ferramenta")
    approval_mode: Optional[Literal["always", "never", "custom"]] = Field(
        default="never", 
        description="Modo de aprovação humana para execução da ferramenta"
    )
    hosted_config: Optional[Dict[str, Any]] = Field(
        None, 
        description="Configuração específica para ferramentas hospedadas (Hosted Tools)"
    )


class ModelConfig(BaseModel):
    type: Literal["openai", "azure-openai"] = Field(..., description="Tipo do cliente de modelo")
    deployment: Optional[str] = Field(None, description="Nome do deployment ou model ID")
    env_vars: Optional[Dict[str, str]] = Field(
        default_factory=dict, description="Mapeamento de variáveis de ambiente específicas"
    )
    
    model_config = {"extra": "allow"}


class AgentConfig(BaseModel):
    id: str = Field(..., description="Identificador único do agente")
    role: str = Field(..., description="Nome ou papel do agente")
    description: Optional[str] = Field(None, description="Descrição do agente para orquestração")
    model: str = Field(..., description="Referência a um modelo definido em resources")
    instructions: str = Field(..., description="Instruções de sistema para o agente")
    tools: List[str] = Field(default_factory=list, description="Lista de IDs de ferramentas")
    confirmation_mode: Optional[Literal["cli", "structured", "auto"]] = Field(
        default="cli", 
        description="Modo de interação humana (apenas para HumanAgent)"
    )


class WorkflowStep(BaseModel):
    id: str = Field(..., description="Identificador do passo")
    type: Literal["agent", "human"] = Field("agent", description="Tipo do passo")
    agent: Optional[str] = Field(None, description="ID do agente responsável (se type=agent)")
    input_template: Optional[str] = Field(None, description="Template Jinja2 ou string f-string like para o input (obrigatório para sequential/parallel)")
    next_step: Optional[str] = Field(None, alias="next", description="ID do próximo passo (para sequencial)")
    transitions: Optional[List[str]] = Field(None, description="Lista de IDs de passos permitidos para transição (para handoff)")


class WorkflowConfig(BaseModel):
    type: Literal["sequential", "parallel", "router", "group_chat", "handoff", "magentic"] = Field(..., description="Tipo de orquestração")
    start_step: Optional[str] = Field(None, description="ID do passo inicial (obrigatório para router/handoff)")
    steps: List[WorkflowStep] = Field(..., description="Lista de passos do workflow")
    
    # Group Chat specific fields
    manager_model: Optional[str] = Field(None, description="Modelo a ser usado pelo Manager do Group Chat/Magentic")
    manager_instructions: Optional[str] = Field(None, description="Instruções para o Manager do Group Chat/Magentic")
    max_rounds: Optional[int] = Field(10, description="Número máximo de trocas de mensagens no Group Chat")
    termination_condition: Optional[str] = Field(None, description="Condição de término (palavra-chave)")
    
    # Magentic specific fields
    max_stall_count: Optional[int] = Field(3, description="Número máximo de stalls antes de replanejamento (Magentic)")
    enable_plan_review: Optional[bool] = Field(False, description="Habilitar revisão humana do plano (Magentic)")


class ResourcesConfig(BaseModel):
    models: Dict[str, ModelConfig] = Field(..., description="Definições de modelos")
    tools: List[ToolConfig] = Field(default_factory=list, description="Definições de ferramentas")


# =============================================================================
# Configuração de Prompts (Integração com PromptEngine)
# =============================================================================

class PromptVariableConfig(BaseModel):
    """Configuração de uma variável de prompt."""
    name: str = Field(..., description="Nome da variável")
    type: str = Field(default="string", description="Tipo da variável (string, number, boolean, list, object)")
    description: Optional[str] = Field(None, description="Descrição da variável")
    default: Optional[Any] = Field(None, description="Valor padrão")
    required: bool = Field(default=True, description="Se é obrigatória")
    
    @field_validator("name")
    @classmethod
    def validate_variable_name(cls, v: str) -> str:
        """Valida que o nome é um identificador válido."""
        import re as regex
        if not regex.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError(f"Nome de variável inválido: '{v}'")
        return v


class PromptTemplateConfig(BaseModel):
    """Configuração de um template de prompt."""
    template: str = Field(..., description="Template com placeholders {var}")
    variables: List[PromptVariableConfig] = Field(default_factory=list, description="Variáveis do template")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados opcionais")


class PromptChainConfig(BaseModel):
    """Configuração de uma chain de prompts."""
    name: str = Field(..., description="Nome da chain")
    steps: List[PromptTemplateConfig] = Field(..., description="Templates em ordem de execução")


class PromptsConfig(BaseModel):
    """
    Configuração completa de prompts para o Worker.
    
    Permite definir templates e chains no arquivo YAML/JSON.
    
    Example:
        ```yaml
        prompts:
          templates:
            saudacao:
              template: "Olá {nome}, bem-vindo!"
              variables:
                - name: nome
                  required: true
          chains:
            - name: analise_completa
              steps:
                - template: "Analise: {texto}"
                - template: "Resuma a análise anterior"
          default_variables:
            sistema: "AI Platform"
        ```
    """
    templates: Dict[str, PromptTemplateConfig] = Field(default_factory=dict, description="Templates nomeados")
    chains: List[PromptChainConfig] = Field(default_factory=list, description="Chains de prompts")
    default_variables: Dict[str, Any] = Field(default_factory=dict, description="Variáveis globais padrão")


class WorkerConfig(BaseModel):
    version: str = Field("1.0", description="Versão do schema")
    name: str = Field(..., description="Nome do worker/projeto")
    checkpoint_file: Optional[str] = Field(None, description="Caminho para arquivo de checkpoint JSON")
    resources: ResourcesConfig
    agents: List[AgentConfig]
    workflow: WorkflowConfig
    prompts: Optional[PromptsConfig] = Field(None, description="Configuração de templates de prompt")


# =============================================================================
# Configuração Standalone de Agente (para execução direta sem workflow)
# =============================================================================

class StandaloneAgentConfig(BaseModel):
    """
    Configuração para execução standalone de um agente.
    
    Diferente do WorkerConfig que requer workflow, esta configuração
    permite executar um agente diretamente via CLI ou API.
    
    Campos equivalentes ao AgentConfig com recursos inline.
    """
    id: str = Field(..., description="Identificador único do agente")
    role: str = Field(..., description="Nome ou papel do agente")
    description: Optional[str] = Field(None, description="Descrição do agente")
    model: str = Field(..., description="Model ID (ex: gpt-4o-mini)")
    instructions: str = Field(..., description="Instruções de sistema")
    tools: List[str] = Field(default_factory=list, description="Lista de IDs de ferramentas")
    confirmation_mode: Optional[Literal["cli", "structured", "auto"]] = Field(
        default="cli", 
        description="Modo de interação humana (apenas para HumanAgent)"
    )
    
    # Recursos opcionais inline (se não usar defaults)
    model_config_override: Optional[ModelConfig] = Field(
        None, 
        alias="model_config",
        description="Configuração customizada do modelo (opcional)"
    )
    tools_config: Optional[List[ToolConfig]] = Field(
        None,
        description="Configurações de ferramentas customizadas (opcional)"
    )


class ConfigLoader:
    """
    Carregador de configuração com detecção automática de tipo.
    
    Suporta:
    - WorkerConfig: Configuração completa de workflow
    - StandaloneAgentConfig: Agente individual para execução direta
    """
    
    def __init__(self, config_path: str):
        self.config_path = config_path

    def _resolve_env_vars(self, content: str) -> str:
        """Substitui padrões ${VAR_NAME} por valores de ambiente."""
        pattern = re.compile(r"\$\{([^}]+)\}")

        def replace(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))  # Retorna o original se não encontrar

        return pattern.sub(replace, content)

    def _parse_raw_data(self) -> dict:
        """Carrega e parseia o arquivo de configuração."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        resolved_content = self._resolve_env_vars(raw_content)

        try:
            return yaml.safe_load(resolved_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Erro ao processar YAML/JSON: {e}")

    def detect_config_type(self) -> Literal["workflow", "agent"]:
        """
        Detecta automaticamente o tipo de configuração.
        
        Workflow: Contém 'workflow' e 'agents' (lista) e 'resources'
        Agent: Contém 'model' e 'instructions' sem 'workflow'
        
        Returns:
            "workflow" ou "agent"
        """
        data = self._parse_raw_data()
        
        # Workflow tem campos específicos
        if "workflow" in data and "resources" in data:
            return "workflow"
        
        # Agente standalone tem model + instructions sem workflow
        if "model" in data and "instructions" in data and "workflow" not in data:
            return "agent"
        
        # Default para workflow (comportamento legacy)
        return "workflow"

    def load(self) -> WorkerConfig:
        """
        Carrega configuração de workflow (comportamento original).
        
        Returns:
            WorkerConfig validado
        """
        data = self._parse_raw_data()
        
        try:
            return WorkerConfig(**data)
        except ValidationError as e:
            raise ValueError(f"Erro de validação da configuração: {e}")

    def load_agent(self) -> StandaloneAgentConfig:
        """
        Carrega configuração de agente standalone.
        
        Returns:
            StandaloneAgentConfig validado
        """
        data = self._parse_raw_data()
        
        try:
            return StandaloneAgentConfig(**data)
        except ValidationError as e:
            raise ValueError(f"Erro de validação da configuração de agente: {e}")

    def load_auto(self) -> Union[WorkerConfig, StandaloneAgentConfig]:
        """
        Carrega configuração detectando automaticamente o tipo.
        
        Returns:
            WorkerConfig ou StandaloneAgentConfig
        """
        config_type = self.detect_config_type()
        
        if config_type == "agent":
            return self.load_agent()
        return self.load()
