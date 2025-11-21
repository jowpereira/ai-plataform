"""Built-in tools - Ferramentas de exemplo registradas automaticamente.

Exemplos de uso dos decorators e patterns.
"""

from typing import Annotated
from pydantic import Field


def fetch_weather(
    city: Annotated[str, Field(description="Nome da cidade")],
) -> dict:
    """Busca informações de clima para uma cidade.

    Args:
        city: Nome da cidade

    Returns:
        Dict com dados meteorológicos
    """
    print(f"🔧 FERRAMENTA CHAMADA! Cidade: {city}")
    # Simulação (em produção: API real)
    result = {
        "city": city,
        "temperature": 999,
        "condition": "TESTE_UNICO_12345",
        "humidity": 888,
        "message": "ESTA_MENSAGEM_VEIO_DA_FERRAMENTA_FETCH_WEATHER"
    }
    print(f"🔧 FERRAMENTA RETORNA: {result}")
    return result


def summarize_guidelines(
    topic: Annotated[str, Field(description="Tópico das guidelines")],
) -> str:
    """Resume guidelines operacionais.

    Args:
        topic: Tópico das guidelines

    Returns:
        Resumo das guidelines
    """
    return f"Guidelines para {topic}: Seguir padrões MAIA, validar entrada, documentar decisões."