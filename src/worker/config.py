import os
import re
from typing import Any, Dict, List, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class ToolConfig(BaseModel):
    id: str = Field(..., description="Identificador único da ferramenta")
    path: str = Field(..., description="Caminho de importação (module:function)")
    description: Optional[str] = Field(None, description="Descrição opcional da ferramenta")


class ModelConfig(BaseModel):
    type: Literal["openai", "azure-openai"] = Field(..., description="Tipo do cliente de modelo")
    deployment: Optional[str] = Field(None, description="Nome do deployment ou model ID")
    env_vars: Optional[Dict[str, str]] = Field(
        default_factory=dict, description="Mapeamento de variáveis de ambiente específicas"
    )


class AgentConfig(BaseModel):
    id: str = Field(..., description="Identificador único do agente")
    role: str = Field(..., description="Nome ou papel do agente")
    description: Optional[str] = Field(None, description="Descrição do agente para orquestração")
    model: str = Field(..., description="Referência a um modelo definido em resources")
    instructions: str = Field(..., description="Instruções de sistema para o agente")
    tools: List[str] = Field(default_factory=list, description="Lista de IDs de ferramentas")


class WorkflowStep(BaseModel):
    id: str = Field(..., description="Identificador do passo")
    type: Literal["agent", "human"] = Field("agent", description="Tipo do passo")
    agent: Optional[str] = Field(None, description="ID do agente responsável (se type=agent)")
    input_template: str = Field(..., description="Template Jinja2 ou string f-string like para o input")
    next_step: Optional[str] = Field(None, alias="next", description="ID do próximo passo (para sequencial)")
    transitions: Optional[List[str]] = Field(None, description="Lista de IDs de passos permitidos para transição (para handoff)")


class WorkflowConfig(BaseModel):
    type: Literal["sequential", "parallel", "router", "group_chat", "handoff"] = Field(..., description="Tipo de orquestração")
    start_step: Optional[str] = Field(None, description="ID do passo inicial (obrigatório para router/handoff)")
    steps: List[WorkflowStep] = Field(..., description="Lista de passos do workflow")


class ResourcesConfig(BaseModel):
    models: Dict[str, ModelConfig] = Field(..., description="Definições de modelos")
    tools: List[ToolConfig] = Field(default_factory=list, description="Definições de ferramentas")


class WorkerConfig(BaseModel):
    version: str = Field("1.0", description="Versão do schema")
    name: str = Field(..., description="Nome do worker/projeto")
    checkpoint_file: Optional[str] = Field(None, description="Caminho para arquivo de checkpoint JSON")
    resources: ResourcesConfig
    agents: List[AgentConfig]
    workflow: WorkflowConfig


class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = config_path

    def _resolve_env_vars(self, content: str) -> str:
        """Substitui padrões ${VAR_NAME} por valores de ambiente."""
        pattern = re.compile(r"\$\{([^}]+)\}")

        def replace(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))  # Retorna o original se não encontrar

        return pattern.sub(replace, content)

    def load(self) -> WorkerConfig:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        # 1. Resolver variáveis de ambiente no texto bruto
        resolved_content = self._resolve_env_vars(raw_content)

        # 2. Parsear YAML/JSON
        try:
            data = yaml.safe_load(resolved_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Erro ao processar YAML/JSON: {e}")

        # 3. Validar com Pydantic
        try:
            return WorkerConfig(**data)
        except ValidationError as e:
            raise ValueError(f"Erro de validação da configuração: {e}")
