"""Built-in tools - Ferramentas de exemplo registradas automaticamente.

Exemplos de uso dos decorators e patterns.
"""

from typing import Annotated
from pydantic import Field

from tools.registry import tool


@tool(
    id="fetch_weather",
    name="Weather Fetcher",
    description="Obtém dados meteorológicos de uma cidade",
    category="weather",
    version="1.0.0",
    tags=["weather", "api", "external"],
)
def fetch_weather(
    city: Annotated[str, Field(description="Nome da cidade")],
) -> dict:
    """Busca informações de clima para uma cidade.

    Args:
        city: Nome da cidade

    Returns:
        Dict com dados meteorológicos
    """
    # Simulação (em produção: API real)
    return {
        "city": city,
        "temperature": 22,
        "condition": "sunny",
        "humidity": 65,
    }


@tool(
    id="summarize_guidelines",
    name="Guideline Summarizer",
    description="Resume guidelines operacionais",
    category="documentation",
    version="1.0.0",
    tags=["docs", "guidelines", "internal"],
)
def summarize_guidelines(
    topic: Annotated[str, Field(description="Tópico das guidelines")],
) -> str:
    """Resume guidelines de um tópico específico.

    Args:
        topic: Tópico das guidelines

    Returns:
        Resumo em texto
    """
    # Simulação
    return f"Guidelines para '{topic}': Seguir processo padrão, documentar decisões."


@tool(
    id="compute_costs",
    name="Cost Calculator",
    description="Calcula custos operacionais",
    category="finance",
    version="1.0.0",
    tags=["finance", "calculator", "ops"],
)
def compute_costs(
    hours: Annotated[float, Field(description="Horas de trabalho")],
    rate: Annotated[float, Field(description="Taxa horária")] = 50.0,
) -> dict:
    """Calcula custos baseado em horas e taxa.

    Args:
        hours: Horas trabalhadas
        rate: Taxa por hora (default: 50.0)

    Returns:
        Dict com breakdown de custos
    """
    total = hours * rate
    return {
        "hours": hours,
        "rate": rate,
        "total": total,
        "currency": "USD",
    }
