from __future__ import annotations

from random import choice, randint
from typing import Annotated

from pydantic import Field


def consultar_clima(
    localizacao: Annotated[str, Field(description="Cidade ou região para consultar", examples=["São Paulo", "Rio de Janeiro"])],
    unidade: Annotated[str, Field(description="Unidade de temperatura preferida", examples=["celsius", "fahrenheit"])] = "celsius",
) -> str:
    """Retorna uma previsão do tempo simulada para exercitar a chamada de ferramentas."""
    condicoes = ["ensolarado", "nublado", "com pancadas de chuva", "com possibilidade de trovoadas"]
    temp_c = randint(12, 33)
    if unidade == "fahrenheit":
        temp_display = f"{int(temp_c * 9 / 5 + 32)}°F"
    else:
        temp_display = f"{temp_c}°C"
    return (
        f"Clima simulado para {localizacao}: {choice(condicoes)} com temperatura média de {temp_display}. "
        "Use apenas como exemplo de integração."
    )


def resumir_diretrizes(
    topico: Annotated[str, Field(description="Tema ou produto a ser resumido")],
) -> str:
    """Devolve um resumo sintético de diretrizes para simular acesso a bases internas."""
    templates = [
        f"Resumo estratégico sobre {topico}: mantenha mensagens curtas, valide fatos e cite fontes internas.",
        f"Checklist de {topico}: 1) contextualizar dado, 2) acionar especialistas, 3) registrar decisão.",
        f"Protocolos atuais para {topico}: priorize telemetria, monitore SLAs e escale desvios críticos.",
    ]
    return choice(templates)


def calcular_custos(
    carga_trabalho: Annotated[str, Field(description="Identificador da carga de trabalho")],
    horas: Annotated[int, Field(description="Horas previstas", ge=1, le=72)] = 4,
) -> str:
    """Cria uma previsão de custo simples para validar múltiplas ferramentas."""
    valor_hora = randint(18, 55)
    return (
        f"Carga simulada {carga_trabalho}: {horas}h estimadas a USD {valor_hora}/h => USD {valor_hora * horas}. "
        "Ajuste com dados reais quando integrar com ERP."
    )
