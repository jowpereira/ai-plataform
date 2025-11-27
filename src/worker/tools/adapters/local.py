"""
Adapter para Ferramentas Locais (Python).

Carrega e executa funções Python locais via importlib.
"""

import asyncio
import importlib
import inspect
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from src.worker.tools.base import ToolAdapter
from src.worker.tools.models import (
    ToolDefinition,
    ToolResult,
    ToolExecutionContext,
    ToolType,
    RetryPolicy,
)

logger = logging.getLogger("worker.tools.local")


class LocalToolAdapter(ToolAdapter):
    """
    Adapter para execução de funções Python locais.
    
    O source deve ser um dotted path para a função:
    - "ferramentas.basicas.calcular_soma"
    - "mock_tools.basic.search_database"
    
    Suporta funções síncronas e assíncronas.
    
    Exemplo:
        adapter = LocalToolAdapter()
        definition = ToolDefinition(
            name="calcular",
            description="Calcula valores",
            type=ToolType.LOCAL,
            source="ferramentas.basicas.calcular"
        )
        result = await adapter.execute(definition, {"x": 10, "y": 20})
    """
    
    tool_type = ToolType.LOCAL
    
    def __init__(self):
        super().__init__()
        self._function_cache: Dict[str, Callable] = {}
    
    def _load_function(self, dotted_path: str) -> Callable:
        """
        Carrega uma função via importlib.
        
        Args:
            dotted_path: Caminho no formato "module.submodule.function"
            
        Returns:
            A função carregada
            
        Raises:
            ImportError: Se o módulo não for encontrado
            AttributeError: Se a função não existir no módulo
        """
        # Verificar cache
        if dotted_path in self._function_cache:
            return self._function_cache[dotted_path]
        
        try:
            module_path, func_name = dotted_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            
            if not callable(func):
                raise ValueError(f"'{dotted_path}' não é callable")
            
            # Cachear para reutilização
            self._function_cache[dotted_path] = func
            logger.debug(f"Função carregada e cacheada: {dotted_path}")
            
            return func
            
        except (ValueError, ImportError, AttributeError) as e:
            logger.error(f"Erro ao carregar função '{dotted_path}': {e}")
            raise
    
    async def _execute_with_retry(
        self,
        func: Callable,
        arguments: Dict[str, Any],
        retry_policy: Optional[RetryPolicy],
    ) -> tuple[Any, int]:
        """
        Executa função com política de retry.
        
        Returns:
            Tupla (resultado, número_de_tentativas)
        """
        policy = retry_policy or RetryPolicy(max_attempts=1)
        last_error: Optional[Exception] = None
        
        for attempt in range(1, policy.max_attempts + 1):
            try:
                # Verificar se é async
                if asyncio.iscoroutinefunction(func):
                    result = await func(**arguments)
                else:
                    # Executar síncrono em thread pool para não bloquear
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, lambda: func(**arguments))
                
                return result, attempt
                
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                
                # Verificar se deve retentar
                if attempt < policy.max_attempts and error_type in policy.retryable_errors:
                    delay = policy.calculate_delay(attempt)
                    logger.warning(
                        f"Tentativa {attempt} falhou para função, "
                        f"retentando em {delay:.2f}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    break
        
        # Todas tentativas falharam
        raise last_error or RuntimeError("Execução falhou sem erro específico")
    
    async def execute(
        self,
        definition: ToolDefinition,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None,
    ) -> ToolResult:
        """Executa a função Python local."""
        start_time = time.time()
        
        try:
            # Carregar função
            func = self._load_function(definition.source)
            
            # Executar com retry
            result, attempts = await self._execute_with_retry(
                func, arguments, definition.retry_policy
            )
            
            execution_time = time.time() - start_time
            
            logger.debug(
                f"Ferramenta '{definition.name}' executada em {execution_time:.3f}s "
                f"({attempts} tentativa(s))"
            )
            
            return ToolResult.success_result(
                tool_name=definition.name,
                result=result,
                execution_time=execution_time,
                attempts=attempts,
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erro ao executar ferramenta '{definition.name}': {e}")
            
            return ToolResult.error_result(
                tool_name=definition.name,
                error=str(e),
                execution_time=execution_time,
            )
    
    def validate(self, definition: ToolDefinition) -> List[str]:
        """Valida a definição de ferramenta local."""
        errors = []
        
        # Verificar formato do source
        if "." not in definition.source:
            errors.append(
                f"Source deve ser um dotted path (ex: 'module.function'), "
                f"recebido: {definition.source}"
            )
        
        # Tentar carregar para validar existência
        try:
            func = self._load_function(definition.source)
            
            # Verificar parâmetros
            sig = inspect.signature(func)
            func_params = set(sig.parameters.keys())
            defined_params = {p.name for p in definition.parameters}
            
            # Parâmetros definidos que não existem na função
            extra_params = defined_params - func_params
            if extra_params:
                errors.append(
                    f"Parâmetros definidos não existem na função: {extra_params}"
                )
                
        except (ImportError, AttributeError) as e:
            errors.append(f"Não foi possível carregar a função: {e}")
        except Exception as e:
            errors.append(f"Erro ao validar função: {e}")
        
        return errors
    
    def clear_cache(self) -> None:
        """Limpa cache de funções."""
        super().clear_cache()
        self._function_cache.clear()
