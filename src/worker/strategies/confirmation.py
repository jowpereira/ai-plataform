from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import asyncio
import os
import json

class ConfirmationStrategy(ABC):
    """
    Estratégia para lidar com confirmações e inputs humanos.
    Permite desacoplar a lógica de interação (CLI vs API vs Web).
    """
    
    @abstractmethod
    async def request_approval(self, step_id: str, prompt: str, instructions: str = "") -> Any:
        """
        Solicita aprovação ou input do usuário.
        
        Args:
            step_id: ID do passo atual
            prompt: Texto ou objeto a ser apresentado
            instructions: Instruções adicionais
            
        Returns:
            Input do usuário (texto, booleano ou objeto estruturado)
        """
        pass

class CLIConfirmationStrategy(ConfirmationStrategy):
    """Estratégia para interação via linha de comando (Terminal)."""
    
    async def request_approval(self, step_id: str, prompt: str, instructions: str = "") -> str:
        print(f"\n👤 [Entrada Humana Necessária] Passo: {step_id}")
        print(f"❓ Prompt: {prompt}")
        if instructions:
            print(f"ℹ️ Instruções: {instructions}")
        
        # Usa asyncio.to_thread para não bloquear o loop de eventos
        return await asyncio.to_thread(input, ">> ")

class StructuredConfirmationStrategy(ConfirmationStrategy):
    """
    Estratégia para interação estruturada (API/DevUI).
    Retorna um objeto especial que sinaliza a necessidade de input.
    """
    
    async def request_approval(self, step_id: str, prompt: str, instructions: str = "") -> Dict[str, Any]:
        # Retorna um objeto estruturado que pode ser interceptado pelo frontend
        return {
            "type": "human_approval_request",
            "step_id": step_id,
            "prompt": prompt,
            "instructions": instructions,
            "status": "waiting"
        }

class AutoApprovalStrategy(ConfirmationStrategy):
    """Estratégia para testes automatizados (aprova tudo)."""
    
    def __init__(self, default_response: str = "yes"):
        self.default_response = default_response
        
    async def request_approval(self, step_id: str, prompt: str, instructions: str = "") -> str:
        return self.default_response
