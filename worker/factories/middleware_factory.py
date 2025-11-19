"""Middleware factory para instanciar middleware de recursos."""

import importlib
from typing import Any

from agent_framework import AgentMiddleware, ChatMiddleware, FunctionMiddleware

from worker.config import MiddlewareConfig


class MiddlewareFactory:
    """Factory para criar instâncias de middleware."""

    def __init__(self):
        self._cache: dict[str, Any] = {}

    def create_middleware(
        self, config: MiddlewareConfig
    ) -> FunctionMiddleware | AgentMiddleware | ChatMiddleware:
        """Cria instância de middleware a partir da config.

        Args:
            config: Configuração do middleware

        Returns:
            Instância de middleware (FunctionMiddleware, AgentMiddleware ou ChatMiddleware)

        Raises:
            ImportError: se class_path não puder ser importado
            ValueError: se tipo de middleware for inválido
        """
        if not config.enabled:
            raise ValueError(f"Middleware {config.id} está desabilitado")

        # Reuso de instâncias (se stateless)
        cache_key = f"{config.class_path}:{hash(frozenset(config.params.items()))}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Import dinâmico da classe
        module_path, class_name = config.class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        middleware_class = getattr(module, class_name)

        # Instancia middleware com params
        instance = middleware_class(**config.params)

        # Valida tipo
        if config.type == "function" and not isinstance(instance, FunctionMiddleware):
            raise ValueError(f"Middleware {config.id} não é FunctionMiddleware")
        elif config.type == "agent" and not isinstance(instance, AgentMiddleware):
            raise ValueError(f"Middleware {config.id} não é AgentMiddleware")
        elif config.type == "chat" and not isinstance(instance, ChatMiddleware):
            raise ValueError(f"Middleware {config.id} não é ChatMiddleware")

        self._cache[cache_key] = instance
        return instance

    def create_middleware_list(
        self, configs: list[MiddlewareConfig]
    ) -> list[FunctionMiddleware | AgentMiddleware | ChatMiddleware]:
        """Cria lista de middlewares a partir de configs.

        Args:
            configs: Lista de configurações de middleware

        Returns:
            Lista de instâncias de middleware
        """
        return [self.create_middleware(cfg) for cfg in configs if cfg.enabled]

    def clear_cache(self):
        """Limpa cache de instâncias."""
        self._cache.clear()
