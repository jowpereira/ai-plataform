"""
Ferramentas mock para demonstração de seguros (Mapfre).

Simula consultas a sistemas internos da seguradora para 
demonstração aos executivos.

Utiliza @ai_function do Microsoft Agent Framework.
"""

from __future__ import annotations

from random import choice, randint, uniform
from typing import Annotated
from datetime import datetime, timedelta

from pydantic import Field
from agent_framework import ai_function


# =============================================================================
# FERRAMENTAS DE CONSULTA - TABELAS E BASES
# =============================================================================

@ai_function(
    name="consultar_tabela_fipe",
    description="Consulta valor de veículo na Tabela FIPE"
)
def consultar_tabela_fipe(
    marca: Annotated[str, Field(description="Marca do veículo (ex: Honda, Toyota, VW)")],
    modelo: Annotated[str, Field(description="Modelo do veículo (ex: Civic, Corolla, Golf)")],
    ano: Annotated[int, Field(description="Ano de fabricação do veículo", ge=2000, le=2025)],
) -> str:
    """Retorna valor FIPE simulado para um veículo."""
    # Tabela base simulada por marca
    base_values = {
        "honda": 95000, "toyota": 98000, "vw": 75000, "volkswagen": 75000,
        "fiat": 65000, "chevrolet": 70000, "gm": 70000, "hyundai": 80000,
        "jeep": 120000, "ford": 85000, "nissan": 88000, "renault": 72000,
        "bmw": 250000, "mercedes": 280000, "audi": 220000, "porsche": 450000,
    }
    
    base = base_values.get(marca.lower(), 80000)
    
    # Ajuste por ano (depreciação ~8% ao ano)
    anos_uso = 2024 - ano
    depreciacao = 0.92 ** anos_uso
    valor = int(base * depreciacao)
    
    # Ajuste por modelo premium
    modelos_premium = ["civic", "corolla", "cruze", "jetta", "golf", "compass", "renegade"]
    if any(m in modelo.lower() for m in modelos_premium):
        valor = int(valor * 1.15)
    
    return (
        f"📊 CONSULTA TABELA FIPE\n"
        f"Veículo: {marca.upper()} {modelo.upper()} {ano}\n"
        f"Referência: Dezembro/2024\n"
        f"Valor FIPE: R$ {valor:,.2f}\n"
        f"Código FIPE: {randint(100000, 999999)}-{randint(1,9)}"
    )


@ai_function(
    name="consultar_perfil_cliente",
    description="Consulta perfil e histórico do cliente na base Mapfre"
)
def consultar_perfil_cliente(
    documento: Annotated[str, Field(description="CPF ou CNPJ do cliente")],
) -> str:
    """Retorna perfil simulado de um cliente."""
    # Gerar dados determinísticos baseados no documento
    seed = sum(ord(c) for c in documento if c.isdigit())
    
    categorias = ["Premium", "Gold", "Standard", "Atenção"]
    categoria = categorias[seed % 4]
    
    anos_cliente = (seed % 10) + 1
    qtd_apolices = (seed % 4) + 1
    sinistros_total = seed % 3
    bonus = min(10, anos_cliente) if sinistros_total == 0 else max(0, 5 - sinistros_total)
    
    produtos = ["Auto", "Residencial", "Vida", "Empresarial"]
    produtos_contratados = produtos[:qtd_apolices]
    
    return (
        f"📋 PERFIL DO CLIENTE MAPFRE\n"
        f"{'='*40}\n"
        f"Documento: {documento}\n"
        f"Categoria: {categoria}\n"
        f"Cliente desde: {2024 - anos_cliente}\n"
        f"Tempo de relacionamento: {anos_cliente} anos\n\n"
        f"📊 HISTÓRICO\n"
        f"Apólices ativas: {qtd_apolices}\n"
        f"Produtos: {', '.join(produtos_contratados)}\n"
        f"Sinistros (últimos 5 anos): {sinistros_total}\n"
        f"Classe de Bônus: {bonus}\n"
        f"Desconto por bônus: {bonus * 3.5:.1f}%\n\n"
        f"💳 PAGAMENTO\n"
        f"Pontualidade: {95 + (seed % 5)}%\n"
        f"Forma preferida: {'Débito automático' if seed % 2 == 0 else 'Boleto'}\n"
        f"Inadimplência: {'Nenhuma' if seed % 3 != 0 else '1 ocorrência (regularizada)'}"
    )


@ai_function(
    name="consultar_apolice",
    description="Consulta detalhes de uma apólice de seguro"
)
def consultar_apolice(
    numero_apolice: Annotated[str, Field(description="Número da apólice (ex: AUTO-2024-123456)")],
) -> str:
    """Retorna detalhes simulados de uma apólice."""
    seed = sum(ord(c) for c in numero_apolice if c.isdigit())
    
    # Determinar tipo de seguro pelo prefixo ou gerar aleatório
    if "auto" in numero_apolice.lower():
        tipo = "AUTO"
        objeto = f"VW Golf 202{seed % 5} - Placa {'ABC'[seed%3]}{seed%10}{'XYZ'[seed%3]}-{seed%10000:04d}"
        capital = randint(80000, 150000)
    elif "res" in numero_apolice.lower():
        tipo = "RESIDENCIAL"
        objeto = f"Apartamento {'Morumbi' if seed%2==0 else 'Pinheiros'}, São Paulo/SP"
        capital = randint(200000, 800000)
    elif "vida" in numero_apolice.lower():
        tipo = "VIDA"
        objeto = "Titular + Cônjuge"
        capital = randint(100000, 500000)
    else:
        tipo = ["AUTO", "RESIDENCIAL", "VIDA"][seed % 3]
        objeto = f"Objeto segurado #{seed}"
        capital = randint(100000, 300000)
    
    inicio = datetime.now() - timedelta(days=randint(30, 300))
    fim = inicio + timedelta(days=365)
    premio_anual = int(capital * 0.035)
    
    return (
        f"📋 APÓLICE MAPFRE\n"
        f"{'='*40}\n"
        f"Número: {numero_apolice}\n"
        f"Tipo: {tipo}\n"
        f"Status: VIGENTE ✓\n\n"
        f"📦 OBJETO SEGURADO\n"
        f"{objeto}\n\n"
        f"📅 VIGÊNCIA\n"
        f"Início: {inicio.strftime('%d/%m/%Y')}\n"
        f"Fim: {fim.strftime('%d/%m/%Y')}\n"
        f"Dias restantes: {(fim - datetime.now()).days}\n\n"
        f"💰 VALORES\n"
        f"Capital Segurado: R$ {capital:,.2f}\n"
        f"Prêmio Anual: R$ {premio_anual:,.2f}\n"
        f"Franquia: R$ {int(capital * 0.03):,.2f}\n\n"
        f"✓ COBERTURAS CONTRATADAS\n"
        f"• Cobertura Básica\n"
        f"• {'Colisão/Incêndio/Roubo' if tipo=='AUTO' else 'Incêndio/Roubo' if tipo=='RESIDENCIAL' else 'Morte/Invalidez'}\n"
        f"• Assistência 24h\n"
        f"• Responsabilidade Civil"
    )


@ai_function(
    name="consultar_sinistro",
    description="Consulta status de um sinistro em andamento"
)
def consultar_sinistro(
    numero_sinistro: Annotated[str, Field(description="Número do sinistro (ex: SIN-2024-123456)")],
) -> str:
    """Retorna status simulado de um sinistro."""
    seed = sum(ord(c) for c in numero_sinistro if c.isdigit())
    
    status_opcoes = [
        ("EM ANÁLISE", "Aguardando documentação complementar", 30),
        ("EM REGULAÇÃO", "Vistoria agendada para os próximos dias", 50),
        ("APROVADO", "Pagamento em processamento", 90),
        ("PENDENTE", "Faltam documentos: CNH e BO", 20),
        ("EM ANÁLISE", "Parecer técnico em elaboração", 45),
    ]
    
    status, obs, progresso = status_opcoes[seed % len(status_opcoes)]
    
    valor_pretensao = randint(5000, 80000)
    valor_aprovado = int(valor_pretensao * (0.7 + (seed % 30) / 100)) if status == "APROVADO" else 0
    
    return (
        f"📋 CONSULTA DE SINISTRO\n"
        f"{'='*40}\n"
        f"Sinistro: {numero_sinistro}\n"
        f"Status: {status}\n"
        f"Progresso: {'█' * (progresso//10)}{'░' * (10-progresso//10)} {progresso}%\n\n"
        f"📝 OBSERVAÇÃO\n"
        f"{obs}\n\n"
        f"💰 VALORES\n"
        f"Pretensão: R$ {valor_pretensao:,.2f}\n"
        f"{'Aprovado: R$ ' + f'{valor_aprovado:,.2f}' if valor_aprovado else 'Aprovado: Em análise'}\n\n"
        f"📞 PRÓXIMOS PASSOS\n"
        f"{'• Aguardar contato do regulador' if status == 'EM REGULAÇÃO' else ''}\n"
        f"{'• Enviar documentos pendentes' if status == 'PENDENTE' else ''}\n"
        f"{'• Pagamento em até 5 dias úteis' if status == 'APROVADO' else ''}\n"
        f"{'• Aguardar parecer técnico' if status == 'EM ANÁLISE' else ''}"
    )


# =============================================================================
# FERRAMENTAS DE CÁLCULO - PRECIFICAÇÃO E ANÁLISE
# =============================================================================

@ai_function(
    name="calcular_premio_auto",
    description="Calcula prêmio de seguro auto com base em parâmetros de risco"
)
def calcular_premio_auto(
    valor_veiculo: Annotated[int, Field(description="Valor do veículo em reais", ge=10000)],
    ano_veiculo: Annotated[int, Field(description="Ano do veículo", ge=2000, le=2025)],
    cep: Annotated[str, Field(description="CEP de pernoite do veículo")],
    idade_condutor: Annotated[int, Field(description="Idade do principal condutor", ge=18, le=99)],
    sexo_condutor: Annotated[str, Field(description="Sexo do condutor (M/F)")],
    possui_garagem: Annotated[bool, Field(description="Possui garagem em casa e trabalho")],
    classe_bonus: Annotated[int, Field(description="Classe de bônus (0-10)", ge=0, le=10)] = 0,
) -> str:
    """Calcula prêmio de seguro auto com todos os fatores."""
    
    # Taxa base: 3.5% do valor do veículo
    taxa_pura = valor_veiculo * 0.035
    
    # Ajuste por idade do veículo (carros novos = mais caros para segurar)
    fator_idade_veiculo = 1.0 + (2025 - ano_veiculo) * 0.02
    
    # Ajuste por idade do condutor
    if idade_condutor < 25:
        fator_idade = 1.35  # Jovem = maior risco
    elif idade_condutor < 30:
        fator_idade = 1.15
    elif idade_condutor < 60:
        fator_idade = 1.0
    else:
        fator_idade = 1.10  # Idoso = risco moderado
    
    # Ajuste por sexo (estatístico)
    fator_sexo = 1.0 if sexo_condutor.upper() == "F" else 1.08
    
    # Ajuste por região (simulado pelo CEP)
    cep_inicio = int(cep[:2]) if cep[:2].isdigit() else 1
    if cep_inicio in [1, 4, 5]:  # SP capital
        fator_regiao = 1.25
    elif cep_inicio in [20, 21, 22]:  # RJ
        fator_regiao = 1.30
    else:
        fator_regiao = 1.0
    
    # Ajuste por garagem
    fator_garagem = 0.90 if possui_garagem else 1.10
    
    # Desconto por bônus (3.5% por classe)
    desconto_bonus = classe_bonus * 0.035
    
    # Cálculo final
    premio_base = taxa_pura * fator_idade_veiculo * fator_idade * fator_sexo * fator_regiao * fator_garagem
    desconto = premio_base * desconto_bonus
    premio_final = premio_base - desconto
    
    # IOF (7.38% para auto)
    iof = premio_final * 0.0738
    premio_total = premio_final + iof
    
    # Franquia (3% do valor do veículo, mínimo R$1.500)
    franquia = max(1500, int(valor_veiculo * 0.03))
    
    return (
        f"💰 CÁLCULO DE PRÊMIO - SEGURO AUTO MAPFRE\n"
        f"{'='*50}\n\n"
        f"📊 COMPOSIÇÃO DO PRÊMIO\n"
        f"{'─'*50}\n"
        f"Taxa Pura ({valor_veiculo:,} × 3.5%): R$ {taxa_pura:,.2f}\n"
        f"Fator Idade Veículo ({ano_veiculo}): × {fator_idade_veiculo:.2f}\n"
        f"Fator Idade Condutor ({idade_condutor} anos): × {fator_idade:.2f}\n"
        f"Fator Sexo ({sexo_condutor}): × {fator_sexo:.2f}\n"
        f"Fator Região (CEP {cep}): × {fator_regiao:.2f}\n"
        f"Fator Garagem ({'Sim' if possui_garagem else 'Não'}): × {fator_garagem:.2f}\n"
        f"{'─'*50}\n"
        f"Prêmio Base: R$ {premio_base:,.2f}\n"
        f"Desconto Bônus (classe {classe_bonus}): -R$ {desconto:,.2f} ({desconto_bonus*100:.1f}%)\n"
        f"Prêmio Líquido: R$ {premio_final:,.2f}\n"
        f"IOF (7.38%): R$ {iof:,.2f}\n"
        f"{'─'*50}\n"
        f"{'█'*50}\n"
        f"PRÊMIO TOTAL ANUAL: R$ {premio_total:,.2f}\n"
        f"PRÊMIO MENSAL (12x): R$ {premio_total/12:,.2f}\n"
        f"{'█'*50}\n\n"
        f"📋 CONDIÇÕES\n"
        f"Franquia: R$ {franquia:,.2f}\n"
        f"Capital Segurado: R$ {valor_veiculo:,.2f}\n"
        f"Validade da Cotação: 7 dias"
    )


@ai_function(
    name="calcular_score_risco",
    description="Calcula score de risco para análise de sinistro"
)
def calcular_score_risco(
    tipo_sinistro: Annotated[str, Field(description="Tipo: COLISAO, ROUBO, INCENDIO, ALAGAMENTO, TERCEIROS")],
    horario_evento: Annotated[str, Field(description="Horário do evento (HH:MM)")],
    local_evento: Annotated[str, Field(description="Descrição do local do evento")],
    dias_para_aviso: Annotated[int, Field(description="Dias entre o evento e o aviso", ge=0)],
    valor_pretensao: Annotated[int, Field(description="Valor pretendido em reais", ge=0)],
    capital_segurado: Annotated[int, Field(description="Capital segurado em reais", ge=0)],
) -> str:
    """Calcula score de risco para análise de fraude."""
    score = 0
    fatores = []
    
    # Fator: Horário
    try:
        hora = int(horario_evento.split(":")[0])
        if 0 <= hora <= 5:
            score += 15
            fatores.append(("Horário madrugada (00h-05h)", "+15", "ALTO"))
        elif 22 <= hora <= 23:
            score += 10
            fatores.append(("Horário noturno (22h-23h)", "+10", "MÉDIO"))
        else:
            fatores.append(("Horário diurno/comercial", "+0", "BAIXO"))
    except:
        fatores.append(("Horário não identificado", "+5", "MÉDIO"))
        score += 5
    
    # Fator: Tipo de sinistro
    tipos_alto_risco = ["roubo", "incendio", "incêndio"]
    if any(t in tipo_sinistro.lower() for t in tipos_alto_risco):
        score += 20
        fatores.append((f"Tipo {tipo_sinistro} (alto risco)", "+20", "ALTO"))
    elif "colisao" in tipo_sinistro.lower() or "colisão" in tipo_sinistro.lower():
        score += 5
        fatores.append((f"Tipo {tipo_sinistro} (risco padrão)", "+5", "BAIXO"))
    else:
        fatores.append((f"Tipo {tipo_sinistro}", "+0", "BAIXO"))
    
    # Fator: Dias para aviso
    if dias_para_aviso > 7:
        score += 15
        fatores.append((f"Aviso tardio ({dias_para_aviso} dias)", "+15", "ALTO"))
    elif dias_para_aviso > 3:
        score += 5
        fatores.append((f"Aviso moderado ({dias_para_aviso} dias)", "+5", "MÉDIO"))
    else:
        fatores.append((f"Aviso imediato ({dias_para_aviso} dias)", "+0", "BAIXO"))
    
    # Fator: Proporção valor/capital
    proporcao = valor_pretensao / capital_segurado if capital_segurado > 0 else 1
    if proporcao > 0.9:
        score += 25
        fatores.append((f"Pretensão próxima ao capital ({proporcao*100:.0f}%)", "+25", "CRÍTICO"))
    elif proporcao > 0.7:
        score += 10
        fatores.append((f"Pretensão elevada ({proporcao*100:.0f}%)", "+10", "MÉDIO"))
    else:
        fatores.append((f"Pretensão proporcional ({proporcao*100:.0f}%)", "+0", "BAIXO"))
    
    # Fator: Local
    locais_risco = ["estacionamento", "via isolada", "madrugada", "deserto"]
    if any(l in local_evento.lower() for l in locais_risco):
        score += 10
        fatores.append(("Local de risco elevado", "+10", "MÉDIO"))
    else:
        fatores.append(("Local comum", "+0", "BAIXO"))
    
    # Classificação final
    if score >= 60:
        classificacao = "CRÍTICO 🔴"
        recomendacao = "INVESTIGAR - Encaminhar ao SIU"
    elif score >= 40:
        classificacao = "ALTO 🟠"
        recomendacao = "VISTORIA ESPECIAL - Regulador sênior"
    elif score >= 20:
        classificacao = "MÉDIO 🟡"
        recomendacao = "REGULAÇÃO PADRÃO"
    else:
        classificacao = "BAIXO 🟢"
        recomendacao = "APROVAÇÃO SIMPLIFICADA"
    
    fatores_str = "\n".join([f"  {f[0]}: {f[1]} ({f[2]})" for f in fatores])
    
    return (
        f"📊 SCORE DE RISCO - ANÁLISE DE SINISTRO\n"
        f"{'='*50}\n\n"
        f"🎯 SCORE FINAL: {score} pontos - {classificacao}\n\n"
        f"📋 FATORES ANALISADOS:\n"
        f"{fatores_str}\n\n"
        f"✅ RECOMENDAÇÃO: {recomendacao}\n\n"
        f"📝 DETALHES:\n"
        f"  Tipo: {tipo_sinistro}\n"
        f"  Local: {local_evento}\n"
        f"  Horário: {horario_evento}\n"
        f"  Valor Pretensão: R$ {valor_pretensao:,.2f}\n"
        f"  Capital Segurado: R$ {capital_segurado:,.2f}"
    )


@ai_function(
    name="gerar_protocolo",
    description="Gera número de protocolo para atendimento"
)
def gerar_protocolo(
    tipo: Annotated[str, Field(description="Tipo: SINISTRO, COTACAO, OUVIDORIA, ATENDIMENTO")],
) -> str:
    """Gera um número de protocolo único."""
    prefixos = {
        "sinistro": "SIN",
        "cotacao": "COT",
        "cotação": "COT",
        "ouvidoria": "OUV",
        "atendimento": "ATD",
    }
    prefixo = prefixos.get(tipo.lower(), "GER")
    numero = randint(100000, 999999)
    data = datetime.now().strftime("%Y%m%d")
    
    protocolo = f"{prefixo}-{data}-{numero}"
    
    return (
        f"✅ PROTOCOLO GERADO\n"
        f"{'='*40}\n"
        f"Número: {protocolo}\n"
        f"Tipo: {tipo.upper()}\n"
        f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"📌 Guarde este número para acompanhamento."
    )


# =============================================================================
# EXPORTAÇÃO
# =============================================================================

__all__ = [
    "consultar_tabela_fipe",
    "consultar_perfil_cliente",
    "consultar_apolice",
    "consultar_sinistro",
    "calcular_premio_auto",
    "calcular_score_risco",
    "gerar_protocolo",
]
