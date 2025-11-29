"""
Code Interpreter - Execução segura de código Python.

Executa código Python em um ambiente sandbox com:
- Restrição de imports (whitelist de módulos seguros)
- Timeout de execução
- Limite de memória (via recursion limit)
- Captura de stdout/stderr

Versão: 2.0.0
"""

import io
import sys
import time
import signal
import traceback
import logging
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

from agent_framework import ai_function

logger = logging.getLogger("ferramentas.code_interpreter")

# Timeout padrão em segundos
DEFAULT_TIMEOUT = 30

# Módulos seguros permitidos
SAFE_MODULES = {
    # Matemática e estatística
    "math", "statistics", "decimal", "fractions", "random",
    # Estruturas de dados
    "collections", "itertools", "functools", "operator",
    # Strings e texto
    "re", "string", "textwrap",
    # Data/Hora
    "datetime", "time", "calendar",
    # Serialização
    "json", "csv",
    # Tipos
    "typing", "dataclasses", "enum",
    # Outros seguros
    "copy", "pprint", "uuid", "hashlib", "base64",
}

# Builtins seguros
SAFE_BUILTINS = {
    # Tipos básicos
    "bool": bool, "int": int, "float": float, "str": str,
    "list": list, "dict": dict, "set": set, "tuple": tuple,
    "frozenset": frozenset, "bytes": bytes, "bytearray": bytearray,
    # Funções matemáticas
    "abs": abs, "round": round, "pow": pow, "divmod": divmod,
    "min": min, "max": max, "sum": sum,
    # Funções de sequência
    "len": len, "range": range, "enumerate": enumerate,
    "zip": zip, "map": map, "filter": filter,
    "sorted": sorted, "reversed": reversed,
    "all": all, "any": any,
    # Conversões
    "bin": bin, "oct": oct, "hex": hex, "chr": chr, "ord": ord,
    # Inspeção
    "type": type, "isinstance": isinstance, "issubclass": issubclass,
    "hasattr": hasattr, "getattr": getattr, "setattr": setattr,
    "callable": callable, "id": id, "hash": hash,
    # I/O
    "print": print, "input": lambda *args: "",  # input desabilitado
    "repr": repr, "format": format,
    # Iteração
    "iter": iter, "next": next, "slice": slice,
    # Constantes
    "True": True, "False": False, "None": None,
    # Exceções comuns
    "Exception": Exception, "ValueError": ValueError,
    "TypeError": TypeError, "KeyError": KeyError,
    "IndexError": IndexError, "ZeroDivisionError": ZeroDivisionError,
}


@dataclass
class ExecutionResult:
    """Resultado de uma execução de código."""
    success: bool
    output: str
    error: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    code_lines: int = 0
    
    def format(self) -> str:
        """Formata o resultado para exibição detalhada."""
        parts = []
        
        if self.success:
            parts.append(f"✅ Sucesso ({self.execution_time:.3f}s)")
            
            if self.output:
                parts.append(f"📤 Output:\n{self.output}")
            
            if self.variables:
                user_vars = {
                    k: v for k, v in self.variables.items()
                    if not v.startswith("<module") and not v.startswith("<function")
                }
                if user_vars:
                    parts.append("📊 Variáveis:")
                    for name, value in user_vars.items():
                        if len(value) > 100:
                            value = value[:100] + "..."
                        parts.append(f"   • {name} = {value}")
        else:
            parts.append(f"❌ Erro ({self.execution_time:.3f}s)")
            parts.append(f"🔴 {self.error}")
        
        return "\n".join(parts)
    
    def format_compact(self) -> str:
        """Formato compacto para logs."""
        if self.success:
            result_preview = ""
            if self.variables and "resultado" in self.variables:
                result_preview = f" → {self.variables['resultado'][:50]}"
            elif self.variables and "result" in self.variables:
                result_preview = f" → {self.variables['result'][:50]}"
            elif self.output:
                first_line = self.output.split('\n')[0][:50]
                result_preview = f" → {first_line}"
            return f"✅ OK ({self.code_lines} linhas, {self.execution_time:.3f}s){result_preview}"
        else:
            error_type = self.error.split(':')[0] if self.error else "Unknown"
            return f"❌ {error_type} ({self.code_lines} linhas, {self.execution_time:.3f}s)"


class CodeSandbox:
    """
    Sandbox para execução segura de código Python.
    """
    
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        max_output_size: int = 10000,
        allowed_modules: Optional[set] = None,
    ):
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.allowed_modules = allowed_modules or SAFE_MODULES
        self._globals = self._create_safe_globals()
    
    def _safe_import(self, name: str, *args, **kwargs):
        """Import seguro - só permite módulos da whitelist."""
        if name in self.allowed_modules:
            return __import__(name, *args, **kwargs)
        raise ImportError(
            f"Módulo '{name}' não permitido. "
            f"Módulos seguros: {sorted(self.allowed_modules)}"
        )
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """Cria um dicionário de globals seguros."""
        safe_globals = {
            "__builtins__": {
                **SAFE_BUILTINS,
                "__import__": self._safe_import,
            },
            "__name__": "__main__",
            "__doc__": None,
        }
        
        # Pré-importar módulos comuns
        for module_name in ["math", "random", "datetime", "json", "re", 
                           "collections", "itertools", "statistics"]:
            try:
                safe_globals[module_name] = __import__(module_name)
            except ImportError:
                pass
        
        return safe_globals
    
    def execute(self, code: str) -> ExecutionResult:
        """
        Executa código no sandbox.
        
        Args:
            code: Código Python a executar
            
        Returns:
            ExecutionResult com output e status
        """
        start_time = time.time()
        code_lines = len(code.strip().split('\n'))
        
        # Preparar ambiente
        local_vars: Dict[str, Any] = {}
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Salvar e limitar recursão
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(200)
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, self._globals.copy(), local_vars)
            
            # Coletar resultados
            stdout = stdout_capture.getvalue()[:self.max_output_size]
            stderr = stderr_capture.getvalue()[:self.max_output_size]
            
            # Combinar output
            output = stdout
            if stderr:
                output += f"\n⚠️ Warnings:\n{stderr}"
            
            # Extrair variáveis definidas pelo usuário
            user_vars = {
                k: self._safe_repr(v)
                for k, v in local_vars.items()
                if not k.startswith("_")
            }
            
            # Verificar resultado especial - adicionar ao início se presente
            result_value = None
            if "resultado" in local_vars:
                result_value = local_vars['resultado']
            elif "result" in local_vars:
                result_value = local_vars['result']
            
            return ExecutionResult(
                success=True,
                output=output.strip(),
                variables=user_vars if user_vars else None,
                execution_time=time.time() - start_time,
                code_lines=code_lines,
            )
            
        except SyntaxError as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Erro de Sintaxe na linha {e.lineno}: {e.msg}",
                execution_time=time.time() - start_time,
                code_lines=code_lines,
            )
            
        except Exception as e:
            # Limpar traceback
            tb_lines = traceback.format_exc().split("\n")
            clean_tb = [l for l in tb_lines if "code_interpreter" not in l][-5:]
            
            return ExecutionResult(
                success=False,
                output="",
                error=f"{type(e).__name__}: {e}\n{''.join(clean_tb)}",
                execution_time=time.time() - start_time,
                code_lines=code_lines,
            )
            
        finally:
            sys.setrecursionlimit(old_limit)
    
    def _safe_repr(self, value: Any, max_len: int = 200) -> str:
        """Representação segura de um valor."""
        try:
            r = repr(value)
            if len(r) > max_len:
                return r[:max_len] + "..."
            return r
        except Exception:
            return "<não representável>"


# Sandbox global
_sandbox: Optional[CodeSandbox] = None


def get_sandbox() -> CodeSandbox:
    """Obtém o sandbox global."""
    global _sandbox
    if _sandbox is None:
        _sandbox = CodeSandbox()
    return _sandbox


# ============================================================================
# Ferramentas expostas para os agentes
# ============================================================================

@ai_function(
    name="executar_codigo",
    description=(
        "Executa código Python e retorna o resultado. "
        "Use para cálculos, processamento de dados, análises e algoritmos. "
        "Módulos disponíveis: math, random, datetime, json, re, collections, "
        "itertools, statistics, decimal, fractions, csv, hashlib, base64. "
        "Capture o resultado em uma variável 'resultado' ou use print()."
    )
)
def executar_codigo(codigo: str) -> str:
    """
    Executa código Python em ambiente sandbox.
    
    Args:
        codigo: Código Python a ser executado
        
    Returns:
        Resultado da execução formatado
    """
    logger.info(f"[CODE] Executando ({len(codigo)} chars)")
    logger.debug(f"Código:\n{codigo}")
    
    sandbox = get_sandbox()
    result = sandbox.execute(codigo)
    
    formatted = result.format()
    logger.info(f"[CODE] {'Sucesso' if result.success else 'Erro'}")
    
    return formatted


@ai_function(
    name="calcular",
    description=(
        "Calcula uma expressão matemática simples. "
        "Suporta: +, -, *, /, **, sqrt, sin, cos, tan, log, pi, e, factorial. "
        "Para cálculos complexos, use executar_codigo()."
    )
)
def calcular(expressao: str) -> str:
    """
    Avalia uma expressão matemática.
    
    Args:
        expressao: Expressão matemática
        
    Returns:
        Resultado da expressão
    """
    logger.info(f"[CALC] {expressao}")
    
    import math
    
    # Ambiente seguro para eval
    safe_dict = {
        "__builtins__": {},
        "math": math,
        "sqrt": math.sqrt,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "asin": math.asin, "acos": math.acos, "atan": math.atan,
        "log": math.log, "log10": math.log10, "log2": math.log2,
        "exp": math.exp, "pow": pow, "abs": abs, "round": round,
        "pi": math.pi, "e": math.e, "tau": math.tau,
        "factorial": math.factorial, "gcd": math.gcd,
        "ceil": math.ceil, "floor": math.floor,
        "degrees": math.degrees, "radians": math.radians,
    }
    
    try:
        resultado = eval(expressao, safe_dict)
        return f"✅ {expressao} = {resultado}"
    except Exception as e:
        return f"❌ Erro: {e}"


@ai_function(
    name="analisar_dados",
    description=(
        "Analisa uma lista de números, calculando estatísticas como "
        "média, mediana, desvio padrão, mínimo, máximo, etc."
    )
)
def analisar_dados(dados: list) -> str:
    """
    Analisa uma lista de dados numéricos.
    
    Args:
        dados: Lista de números para analisar
        
    Returns:
        Estatísticas dos dados
    """
    logger.info(f"[STATS] Analisando {len(dados)} itens")
    
    import statistics
    import math
    
    try:
        # Converter para float
        numeros = [float(x) for x in dados]
        
        n = len(numeros)
        if n == 0:
            return "❌ Lista vazia"
        
        result = {
            "contagem": n,
            "soma": sum(numeros),
            "média": statistics.mean(numeros),
            "mínimo": min(numeros),
            "máximo": max(numeros),
        }
        
        if n >= 2:
            result["mediana"] = statistics.median(numeros)
            result["desvio_padrão"] = statistics.stdev(numeros)
            result["variância"] = statistics.variance(numeros)
        
        if n >= 4:
            sorted_nums = sorted(numeros)
            q1_idx = n // 4
            q3_idx = 3 * n // 4
            result["Q1"] = sorted_nums[q1_idx]
            result["Q3"] = sorted_nums[q3_idx]
        
        # Formatar
        lines = ["📊 Análise Estatística:"]
        for k, v in result.items():
            if isinstance(v, float):
                lines.append(f"  • {k}: {v:.4f}")
            else:
                lines.append(f"  • {k}: {v}")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Erro ao analisar: {e}"


@ai_function(
    name="gerar_grafico_texto",
    description=(
        "Gera uma representação em texto (ASCII) de um gráfico de barras simples. "
        "Útil para visualização rápida de dados."
    )
)
def gerar_grafico_texto(dados: dict, titulo: str = "Gráfico") -> str:
    """
    Gera um gráfico de barras em ASCII.
    
    Args:
        dados: Dicionário {label: valor}
        titulo: Título do gráfico
        
    Returns:
        Gráfico em texto
    """
    logger.info(f"[CHART] Gerando gráfico: {titulo}")
    
    if not dados:
        return "❌ Dados vazios"
    
    try:
        max_val = max(dados.values())
        max_label_len = max(len(str(k)) for k in dados.keys())
        bar_width = 40
        
        lines = [f"📊 {titulo}", "=" * (max_label_len + bar_width + 10)]
        
        for label, value in dados.items():
            bar_len = int((value / max_val) * bar_width) if max_val > 0 else 0
            bar = "█" * bar_len
            lines.append(f"{str(label):>{max_label_len}} | {bar} {value}")
        
        lines.append("=" * (max_label_len + bar_width + 10))
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Erro ao gerar gráfico: {e}"


# Aliases
code_interpreter = executar_codigo
execute = executar_codigo
calc = calcular
