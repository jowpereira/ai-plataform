"""
Adapter para Ferramentas HTTP/REST.

Executa chamadas HTTP para APIs externas.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urljoin

from src.worker.tools.base import ToolAdapter
from src.worker.tools.models import (
    ToolDefinition,
    ToolResult,
    ToolExecutionContext,
    ToolType,
    RetryPolicy,
)

logger = logging.getLogger("worker.tools.http")


# Configuração padrão para HTTP
DEFAULT_HTTP_CONFIG = {
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "timeout": 30.0,
    "verify_ssl": True,
}


class HttpToolAdapter(ToolAdapter):
    """
    Adapter para execução de ferramentas via HTTP/REST.
    
    O source deve ser uma URL válida:
    - "https://api.example.com/v1/calculate"
    - "http://internal-service:8080/process"
    
    Configurações HTTP via http_config:
        {
            "method": "POST",  # GET, POST, PUT, DELETE
            "headers": {"Authorization": "Bearer {token}"},
            "timeout": 30.0,
            "verify_ssl": True,
            "auth_type": "bearer",  # bearer, basic, api_key
            "auth_header": "Authorization",
            "response_path": "data.result"  # JSONPath para extrair resultado
        }
    
    Exemplo:
        definition = ToolDefinition(
            name="fetch_data",
            description="Fetches data from an external API",
            type=ToolType.HTTP,
            source="https://api.example.com/v1/resource",
            http_config={
                "method": "GET",
                "headers": {"X-Api-Key": "{API_KEY}"}
            }
        )
    """
    
    tool_type = ToolType.HTTP
    
    def __init__(self):
        super().__init__()
        self._session = None
    
    async def _get_session(self):
        """Obtém ou cria sessão HTTP (lazy initialization)."""
        if self._session is None:
            try:
                import aiohttp
                self._session = aiohttp.ClientSession()
            except ImportError:
                logger.warning("aiohttp não instalado, usando httpx como fallback")
                try:
                    import httpx
                    self._session = httpx.AsyncClient()
                except ImportError:
                    raise ImportError(
                        "Nenhum cliente HTTP async disponível. "
                        "Instale 'aiohttp' ou 'httpx': pip install aiohttp"
                    )
        return self._session
    
    def _merge_config(self, definition: ToolDefinition) -> Dict[str, Any]:
        """Merge configuração padrão com configuração da definição."""
        config = DEFAULT_HTTP_CONFIG.copy()
        if definition.http_config:
            config.update(definition.http_config)
        return config
    
    def _resolve_headers(
        self,
        headers: Dict[str, str],
        context: Optional[ToolExecutionContext],
    ) -> Dict[str, str]:
        """Resolve placeholders nos headers."""
        resolved = {}
        for key, value in headers.items():
            if isinstance(value, str) and "{" in value:
                # Substituir placeholders
                if context:
                    if "{token}" in value and context.auth_token:
                        value = value.replace("{token}", context.auth_token)
                    for env_key, env_value in context.env_vars.items():
                        value = value.replace(f"{{{env_key}}}", env_value)
            resolved[key] = value
        return resolved
    
    def _extract_result(self, data: Any, response_path: Optional[str]) -> Any:
        """Extrai resultado usando JSONPath simples."""
        if not response_path or not isinstance(data, dict):
            return data
        
        # JSONPath simples: "data.result.value"
        parts = response_path.split(".")
        result = data
        for part in parts:
            if isinstance(result, dict):
                result = result.get(part)
            elif isinstance(result, list) and part.isdigit():
                result = result[int(part)]
            else:
                return data  # Fallback para resposta completa
        return result
    
    async def _execute_request(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        arguments: Dict[str, Any],
        timeout: float,
        verify_ssl: bool,
    ) -> Any:
        """Executa a requisição HTTP."""
        session = await self._get_session()
        
        # Preparar argumentos da requisição
        request_kwargs: Dict[str, Any] = {
            "headers": headers,
            "timeout": timeout,
        }
        
        # Para GET, argumentos vão como query params
        # Para outros métodos, vão como body JSON
        if method.upper() == "GET":
            request_kwargs["params"] = arguments
        else:
            request_kwargs["json"] = arguments
        
        # Verificar tipo de sessão e executar
        session_type = type(session).__module__
        
        if "aiohttp" in session_type:
            # aiohttp
            import aiohttp
            ssl_context = None if verify_ssl else False
            async with session.request(
                method, url, ssl=ssl_context, **request_kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()
        else:
            # httpx
            response = await session.request(method, url, **request_kwargs)
            response.raise_for_status()
            return response.json()
    
    async def execute(
        self,
        definition: ToolDefinition,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None,
    ) -> ToolResult:
        """Executa chamada HTTP."""
        start_time = time.time()
        
        try:
            config = self._merge_config(definition)
            
            # Resolver headers
            headers = self._resolve_headers(
                config.get("headers", {}),
                context
            )
            
            # Adicionar auth se presente no contexto
            if context and context.auth_token:
                auth_type = config.get("auth_type", "bearer")
                auth_header = config.get("auth_header", "Authorization")
                
                if auth_type == "bearer":
                    headers[auth_header] = f"Bearer {context.auth_token}"
                elif auth_type == "api_key":
                    headers[auth_header] = context.auth_token
            
            # Executar com retry
            policy = definition.retry_policy or RetryPolicy(
                max_attempts=3,
                retryable_errors=["TimeoutError", "ConnectionError", "HTTPError"]
            )
            
            last_error = None
            attempts = 0
            
            for attempt in range(1, policy.max_attempts + 1):
                attempts = attempt
                try:
                    data = await self._execute_request(
                        url=definition.source,
                        method=config.get("method", "POST"),
                        headers=headers,
                        arguments=arguments,
                        timeout=config.get("timeout", definition.timeout),
                        verify_ssl=config.get("verify_ssl", True),
                    )
                    
                    # Extrair resultado se configurado
                    result = self._extract_result(
                        data,
                        config.get("response_path")
                    )
                    
                    execution_time = time.time() - start_time
                    
                    logger.debug(
                        f"HTTP tool '{definition.name}' executada em {execution_time:.3f}s "
                        f"({attempts} tentativa(s))"
                    )
                    
                    return ToolResult.success_result(
                        tool_name=definition.name,
                        result=result,
                        execution_time=execution_time,
                        attempts=attempts,
                    )
                    
                except Exception as e:
                    last_error = e
                    error_type = type(e).__name__
                    
                    if attempt < policy.max_attempts and error_type in policy.retryable_errors:
                        delay = policy.calculate_delay(attempt)
                        logger.warning(
                            f"HTTP tentativa {attempt} falhou, "
                            f"retentando em {delay:.2f}s: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        break
            
            # Falhou após todas tentativas
            raise last_error or RuntimeError("HTTP request failed")
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erro ao executar HTTP tool '{definition.name}': {e}")
            
            return ToolResult.error_result(
                tool_name=definition.name,
                error=str(e),
                execution_time=execution_time,
            )
    
    def validate(self, definition: ToolDefinition) -> List[str]:
        """Valida a definição de ferramenta HTTP."""
        errors = []
        
        # Verificar URL
        source = definition.source
        if not source.startswith(("http://", "https://")):
            errors.append(
                f"Source deve ser uma URL HTTP(S), recebido: {source}"
            )
        
        # Verificar método se especificado
        if definition.http_config:
            method = definition.http_config.get("method", "POST")
            valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
            if method.upper() not in valid_methods:
                errors.append(f"Método HTTP inválido: {method}")
        
        return errors
    
    async def close(self) -> None:
        """Fecha a sessão HTTP."""
        if self._session:
            await self._session.close()
            self._session = None
