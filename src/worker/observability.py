"""Integração de observabilidade alinhada ao Microsoft Agent Framework."""

from __future__ import annotations

import atexit
import logging
import os
from dataclasses import dataclass
from typing import Optional

from opentelemetry import metrics, trace

try:  # Importação opcional para ambientes sem o pacote oficial
    from agent_framework.observability import (
        OBSERVABILITY_SETTINGS,
        setup_observability as af_setup_observability,
    )

    HAS_AGENT_FRAMEWORK_OBSERVABILITY = True
except ImportError:  # pragma: no cover - fallback apenas para dev
    HAS_AGENT_FRAMEWORK_OBSERVABILITY = False
    af_setup_observability = None  # type: ignore
    OBSERVABILITY_SETTINGS = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class ObservabilityConfig:
    """Configuração resolvida para instrumentação."""

    enable_otel: bool
    enable_sensitive_data: bool
    otlp_endpoint: Optional[str]
    applicationinsights_connection_string: Optional[str]
    vs_code_extension_port: Optional[int]


_configured = False


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: Optional[int] = None) -> Optional[int]:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Valor inválido para %s: %s", name, value)
        return default


def _build_config(
    *,
    force_enable: Optional[bool] = None,
    enable_sensitive_data: Optional[bool] = None,
    otlp_endpoint: Optional[str] = None,
    applicationinsights_connection_string: Optional[str] = None,
    vs_code_extension_port: Optional[int] = None,
) -> ObservabilityConfig:
    return ObservabilityConfig(
        enable_otel=force_enable if force_enable is not None else _env_bool("ENABLE_OTEL", False),
        enable_sensitive_data=(
            enable_sensitive_data
            if enable_sensitive_data is not None
            else _env_bool("ENABLE_SENSITIVE_DATA", False)
        ),
        otlp_endpoint=otlp_endpoint if otlp_endpoint is not None else os.getenv("OTLP_ENDPOINT"),
        applicationinsights_connection_string=(
            applicationinsights_connection_string
            if applicationinsights_connection_string is not None
            else os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        ),
        vs_code_extension_port=(
            vs_code_extension_port
            if vs_code_extension_port is not None
            else _env_int("VS_CODE_EXTENSION_PORT", 4317)
        ),
    )


def setup_observability(
    *,
    force_enable: Optional[bool] = None,
    enable_sensitive_data: Optional[bool] = None,
    otlp_endpoint: Optional[str] = None,
    applicationinsights_connection_string: Optional[str] = None,
    vs_code_extension_port: Optional[int] = None,
) -> None:
    """Inicializa a instrumentação oficial do Agent Framework se habilitada.
    
    Para enviar traces ao Azure AI Foundry, defina APPLICATIONINSIGHTS_CONNECTION_STRING
    no .env com a connection string obtida do portal Azure.
    
    Alternativamente, use OTLP_ENDPOINT para enviar a um coletor OTLP (ex: Aspire Dashboard).
    """

    global _configured

    if _configured:
        return

    config = _build_config(
        force_enable=force_enable,
        enable_sensitive_data=enable_sensitive_data,
        otlp_endpoint=otlp_endpoint,
        applicationinsights_connection_string=applicationinsights_connection_string,
        vs_code_extension_port=vs_code_extension_port,
    )

    if not config.enable_otel:
        logger.info("Observabilidade desabilitada (ENABLE_OTEL=false).")
        return

    if not HAS_AGENT_FRAMEWORK_OBSERVABILITY:
        logger.warning(
            "agent_framework.observability não disponível; habilite o pacote oficial "
            "para telemetria."
        )
        return

    if (
        OBSERVABILITY_SETTINGS is not None
        and getattr(OBSERVABILITY_SETTINGS, "_executed_setup", False)
    ):
        _configured = True
        logger.debug("Observabilidade já estava configurada pelo Agent Framework.")
        return

    try:
        af_setup_observability(  # type: ignore[call-arg]
            enable_sensitive_data=config.enable_sensitive_data,
            otlp_endpoint=config.otlp_endpoint,
            applicationinsights_connection_string=config.applicationinsights_connection_string,
            vs_code_extension_port=config.vs_code_extension_port,
        )
        _configured = True
        
        # Log do destino configurado
        if config.applicationinsights_connection_string:
            logger.info("Observabilidade configurada → Azure Application Insights (Foundry).")
        elif config.otlp_endpoint:
            logger.info("Observabilidade configurada → OTLP endpoint: %s", config.otlp_endpoint)
        else:
            logger.info("Observabilidade configurada via Agent Framework (VS Code port: %s).", config.vs_code_extension_port)
            
    except Exception as exc:  # pragma: no cover - caminho excepcional
        logger.error("Falha ao configurar observabilidade", exc_info=exc)


def shutdown_observability() -> None:
    """Tenta encerrar providers globais para garantir flush dos exporters."""

    try:
        tracer_provider = trace.get_tracer_provider()
        if hasattr(tracer_provider, "shutdown"):
            tracer_provider.shutdown()

        meter_provider = metrics.get_meter_provider()
        if hasattr(meter_provider, "shutdown"):
            meter_provider.shutdown()
    except Exception as exc:  # pragma: no cover - apenas loga erro de shutdown
        logger.warning("Erro ao finalizar observabilidade: %s", exc)


atexit.register(shutdown_observability)
