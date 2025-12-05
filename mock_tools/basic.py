"""
Mock tools para testes.

Utiliza o decorator @ai_function do Microsoft Agent Framework
para registro automático de ferramentas com schema JSON.
"""

from __future__ import annotations

from random import choice, randint
from typing import Annotated

from pydantic import Field
from agent_framework import ai_function


@ai_function(name="consultar_clima", description="Consulta previsão do tempo simulada")
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
        f"A previsão do tempo para {localizacao} é {choice(condicoes)} com "
        f"temperatura de {temp_display}."
    )


@ai_function(name="resumir_diretrizes", description="Resume diretrizes internas sobre um tópico")
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


@ai_function(name="calcular_custos", description="Calcula previsão de custos para carga de trabalho")
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


@ai_function(name="verificar_status_sistema", description="Verifica status de um sistema (ONLINE/OFFLINE)")
def verificar_status_sistema(
    sistema: Annotated[str, Field(description="Nome do sistema para verificar status")]
) -> str:
    """Simula a verificação de status de um sistema (ONLINE ou OFFLINE)."""
    # Simulação determinística baseada no nome para facilitar testes
    if "prod" in sistema.lower():
        return "ONLINE"
    return "OFFLINE"


@ai_function(name="verificar_resolucao", description="Verifica se uma correção técnica foi bem-sucedida")
def verificar_resolucao(
    ticket_id: Annotated[str, Field(description="ID do ticket ou problema")]
) -> str:
    """Simula a verificação de uma correção técnica."""
    # Simulação: Tickets terminados em '99' são difíceis e falham na primeira tentativa
    if ticket_id.endswith("99"):
        return "FALHA: O sistema ainda apresenta lentidão."
    return "SUCESSO: O sistema está estável."


# Re-exportar ferramentas de seguros para compatibilidade com o path padrão
from mock_tools.seguros import (
    consultar_tabela_fipe,
    consultar_perfil_cliente,
    consultar_apolice,
    consultar_sinistro,
    calcular_premio_auto,
    calcular_score_risco,
    gerar_protocolo,
)

__all__ = [
    # Ferramentas básicas
    "consultar_clima",
    "resumir_diretrizes",
    "calcular_custos",
    "verificar_status_sistema",
    "verificar_resolucao",
    # Ferramentas de seguros (re-exportadas)
    "consultar_tabela_fipe",
    "consultar_perfil_cliente",
    "consultar_apolice",
    "consultar_sinistro",
    "calcular_premio_auto",
    "calcular_score_risco",
    "gerar_protocolo",
]
