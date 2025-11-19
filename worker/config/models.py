"""Model configuration models."""

from typing import Any, Literal
from pydantic import BaseModel, Field


class ModelProfile(BaseModel):
    """Profile de modelo reutilizável."""
    
    id: str = Field(..., description="Profile identifier")
    client_type: Literal["openai", "azure"] = Field(..., description="Client provider")
    model: str = Field(..., description="Model identifier or env var")
    default_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Default client parameters"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """Model configuration section."""
    
    profiles: dict[str, ModelProfile] = Field(default_factory=dict)
    default_profile: str | None = None