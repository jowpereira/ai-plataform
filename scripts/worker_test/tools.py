from __future__ import annotations

from random import choice, randint
from typing import Annotated

from pydantic import Field


def fetch_weather(
    location: Annotated[str, Field(description="City or region to inspect", examples=["Seattle", "Sao Paulo"])],
    unit: Annotated[str, Field(description="Preferred temperature unit", examples=["celsius", "fahrenheit"])] = "celsius",
) -> str:
    """Return a playful pseudo forecast to exercise tool calling."""
    outlooks = ["ensolarado", "nublado", "com pancadas de chuva", "com possibilidade de trovoadas"]
    temps_c = randint(12, 33)
    if unit == "fahrenheit":
        temp_display = f"{int(temps_c * 9 / 5 + 32)}°F"
    else:
        temp_display = f"{temps_c}°C"
    return (
        f"Clima artificial para {location}: {choice(outlooks)} com temperatura média de {temp_display}. "
        "Use apenas como exemplo de integração com ferramentas."
    )


def summarize_guidelines(
    topic: Annotated[str, Field(description="Tema ou produto a ser resumido")],
) -> str:
    """Devolve um resumo sintético de guidelines para simular acesso a bases internas."""
    templates = [
        f"Resumo estratégico sobre {topic}: mantenha mensagens curtas, valide fatos e cite fontes internas.",
        f"Checklist de {topic}: 1) contextualizar dado, 2) acionar especialistas, 3) registrar decisão.",
        f"Protocolos atuais para {topic}: priorize telemetria, monitore SLAs e escale desvios críticos.",
    ]
    return choice(templates)


def compute_costs(
    workload: Annotated[str, Field(description="Identificador do workload")],
    hours: Annotated[int, Field(description="Horas previstas", ge=1, le=72)] = 4,
) -> str:
    """Cria uma previsão de custo simples só para validar múltiplas ferramentas."""
    hourly = randint(18, 55)
    return (
        f"Carga simulada {workload}: {hours}h estimadas a USD {hourly}/h => USD {hourly * hours}. "
        "Ajuste com dados reais quando integrar com ERP."
    )
