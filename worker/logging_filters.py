"""Filtros de logging para suprimir warnings conhecidos do Agent Framework."""

import logging
from typing import Literal


class TerminalNodeWarningFilter(logging.Filter):
    """Suprime warning 'No outgoing edges found' para terminal nodes conhecidos.
    
    Este warning é esperado e seguro - terminal nodes não devem ter outgoing edges.
    O Framework emite o warning internamente, mas não afeta funcionamento.
    """

    def __init__(self, terminal_nodes: set[str] | None = None):
        super().__init__()
        self.terminal_nodes = terminal_nodes or set()

    def filter(self, record: logging.LogRecord) -> bool:
        """Retorna False para suprimir o log, True para permitir."""
        msg = record.getMessage()
        
        # Detectar o warning específico
        if "No outgoing edges found for executor" in msg and "dropping messages" in msg:
            # Extrair o nome do executor do warning
            # Formato: "No outgoing edges found for executor <name>; dropping messages."
            parts = msg.split("executor ")
            if len(parts) > 1:
                executor_name = parts[1].split(";")[0].strip()
                if executor_name in self.terminal_nodes:
                    return False  # Suprimir warning para terminal nodes conhecidos
        
        return True  # Permitir outros logs


def configure_workflow_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
    suppress_terminal_warnings: bool = True,
    terminal_nodes: set[str] | None = None,
) -> None:
    """Configura logging para workflows com filtros opcionais.
    
    Args:
        level: Nível de logging desejado
        suppress_terminal_warnings: Se True, suprime warnings de terminal nodes
        terminal_nodes: Set de IDs de terminal nodes para filtrar
    """
    runner_logger = logging.getLogger("agent_framework._workflows._runner")
    runner_logger.setLevel(level)
    
    if suppress_terminal_warnings and terminal_nodes:
        filter_instance = TerminalNodeWarningFilter(terminal_nodes)
        runner_logger.addFilter(filter_instance)


def reset_workflow_logging() -> None:
    """Remove todos os filtros do logger de workflows."""
    runner_logger = logging.getLogger("agent_framework._workflows._runner")
    runner_logger.filters.clear()
