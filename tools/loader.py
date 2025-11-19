"""Tools Loader - Auto-discovery e carregamento de ferramentas.

Carrega automaticamente ferramentas de:
- Módulo builtins
- Diretórios de plugins
- Import paths customizados
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Any

from tools.registry import ToolRegistry


class ToolLoader:
    """Carregador automático de ferramentas."""

    @staticmethod
    def load_builtins() -> int:
        """Carrega ferramentas built-in.

        Returns:
            Quantidade de tools carregadas
        """
        try:
            import tools.builtins  # noqa: F401
            return len(ToolRegistry.list_tools(enabled_only=False))
        except ImportError:
            return 0

    @staticmethod
    def load_from_module(module_path: str) -> int:
        """Carrega ferramentas de um módulo Python.

        Args:
            module_path: Path do módulo (e.g., "myapp.tools")

        Returns:
            Quantidade de tools carregadas
        """
        before = len(ToolRegistry.list_tools(enabled_only=False))

        try:
            importlib.import_module(module_path)
        except ImportError as e:
            raise ImportError(f"Falha ao carregar módulo {module_path}: {e}")

        after = len(ToolRegistry.list_tools(enabled_only=False))
        return after - before

    @staticmethod
    def load_from_directory(directory: Path | str, package: str = "") -> int:
        """Carrega ferramentas de um diretório recursivamente.

        Args:
            directory: Path do diretório
            package: Nome do pacote base

        Returns:
            Quantidade de tools carregadas
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise ValueError(f"Diretório não encontrado: {directory}")

        before = len(ToolRegistry.list_tools(enabled_only=False))

        for importer, module_name, is_pkg in pkgutil.walk_packages(
            [str(directory)],
            prefix=f"{package}." if package else "",
        ):
            try:
                importlib.import_module(module_name)
            except Exception:
                continue  # Skip módulos com erro

        after = len(ToolRegistry.list_tools(enabled_only=False))
        return after - before

    @staticmethod
    def load_from_import_path(import_path: str) -> str:
        """Carrega ferramenta individual de import path.

        Args:
            import_path: Path completo (e.g., "mytools:fetch_data")

        Returns:
            ID da tool registrada

        Raises:
            ValueError: se formato inválido
            ImportError: se módulo não existe
            AttributeError: se função não existe
        """
        if ":" not in import_path:
            raise ValueError(f"Import path deve ter formato 'module:function', recebeu: {import_path}")

        module_path, func_name = import_path.rsplit(":", 1)
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)

        # Se já foi decorada com @tool, retorna ID existente
        # Senão, registra com ID = func_name
        try:
            return ToolRegistry.get_metadata(func_name).id
        except KeyError:
            ToolRegistry.register(func, id=func_name)
            return func_name


# Auto-load builtins na importação
ToolLoader.load_builtins()
