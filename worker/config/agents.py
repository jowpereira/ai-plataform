"""Agent configuration models."""

from typing import Any, Literal
from pydantic import BaseModel, Field


class MemoryConfig(BaseModel):
    """Agent memory configuration."""

    type: Literal["in_memory", "file", "redis"] = "in_memory"
    chat_message_store: str | None = Field(
        None,
        description="Custom ChatMessageStore import path",
    )
    max_history: int | None = None
    file_path: str | None = None
    redis_url: str | None = None


class ResponseFormatConfig(BaseModel):
    """Structured output configuration via JSON schema."""

    model_path: str = Field(..., description="Pydantic model import path")
    handle_errors: bool = True
    retry_on_validation_error: bool = True


class AgentConfig(BaseModel):
    """Individual agent configuration."""

    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent name")
    client_type: Literal["openai", "azure"] = Field(
        "openai",
        description="Chat client provider",
    )
    model: str = Field(..., description="Model identifier (e.g., 'gpt-4o-mini' ou '$OPENAI_MODEL')")
    instructions: str = Field("", description="System prompt")
    tools: list[str] = Field(
        default_factory=list,
        description="Tool IDs from resources.tools",
    )
    middleware: list[str] = Field(
        default_factory=list,
        description="Middleware IDs específicos deste agente (além do global_middleware)",
    )
    memory: MemoryConfig | None = None
    response_format: ResponseFormatConfig | None = None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais (description, temperature, max_tokens, etc.)",
    )
    enabled: bool = True
