import os
import importlib
import inspect
from typing import List, Dict, Any
from pydantic import BaseModel

class ToolInfo(BaseModel):
    id: str
    name: str
    description: str
    path: str
    parameters: Dict[str, Any]

def discover_tools(tools_dir: str = "tools") -> List[ToolInfo]:
    """Descobre ferramentas (funções) no diretório especificado."""
    tools = []
    if not os.path.exists(tools_dir):
        return []

    # Normalizar caminho para importação
    # Assumindo que tools_dir é relativo à raiz do projeto e é um pacote python
    package_name = tools_dir.replace("/", ".").replace("\\", ".")

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            module_path = f"{package_name}.{module_name}"
            try:
                module = importlib.import_module(module_path)
                
                # Se o módulo define __all__, usar apenas essas funções
                if hasattr(module, "__all__"):
                    functions_to_inspect = [(name, getattr(module, name)) for name in module.__all__]
                else:
                    functions_to_inspect = inspect.getmembers(module, inspect.isfunction)

                for name, obj in functions_to_inspect:
                    # Filtrar apenas funções definidas no módulo (evitar imports)
                    if inspect.isfunction(obj) and obj.__module__ == module_path:
                        
                        # Extrair docstring
                        doc = inspect.getdoc(obj) or ""
                        
                        # Extrair parâmetros
                        sig = inspect.signature(obj)
                        params = {}
                        for param_name, param in sig.parameters.items():
                            param_type = str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any"
                            params[param_name] = param_type

                        tools.append(ToolInfo(
                            id=name,
                            name=name,
                            description=doc,
                            path=f"{module_path}:{name}",
                            parameters=params
                        ))
            except Exception as e:
                print(f"Erro ao carregar módulo {module_path}: {e}")
    return tools
