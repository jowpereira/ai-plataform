"""Agent configuration models."""

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


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
    client_type: Literal["openai", "azure"] | None = Field(
        None,
        description="Chat client provider (optional if using model_profile)",
    )
    model: str | None = Field(None, description="Model identifier (optional if using model_profile)")
    model_profile: str | None = Field(None, description="Model profile ID from models.profiles")
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

    @model_validator(mode="after")
    def validate_model_config(self):
        """Validate model configuration."""
        has_direct = self.client_type and self.model
        has_profile = self.model_profile
        
        if not has_direct and not has_profile:
            raise ValueError("Agent must have either (client_type + model) or model_profile")
        
        if has_direct and has_profile:
            raise ValueError("Agent cannot have both direct config and model_profile")
            
        return self
