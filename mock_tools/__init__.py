"""
Mock Tools - Ferramentas simuladas para demonstração.

Módulos disponíveis:
- basic: Ferramentas básicas genéricas (clima, custos, status)
- seguros: Ferramentas específicas para seguros (FIPE, apólice, sinistro, cotação)
"""

from mock_tools.basic import (
    consultar_clima,
    resumir_diretrizes,
    calcular_custos,
    verificar_status_sistema,
    verificar_resolucao,
)

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
    # Basic
    "consultar_clima",
    "resumir_diretrizes",
    "calcular_custos",
    "verificar_status_sistema",
    "verificar_resolucao",
    # Seguros
    "consultar_tabela_fipe",
    "consultar_perfil_cliente",
    "consultar_apolice",
    "consultar_sinistro",
    "calcular_premio_auto",
    "calcular_score_risco",
    "gerar_protocolo",
]
