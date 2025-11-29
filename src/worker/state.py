import json
import os
import copy
from typing import Any, Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class WorkflowState(BaseModel):
    """Representa o estado atual da execução do workflow."""
    execution_id: str
    start_time: datetime = Field(default_factory=datetime.now)
    current_step_id: Optional[str] = None
    global_context: Dict[str, Any] = Field(default_factory=dict)
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "initialized"  # initialized, running, completed, failed, paused

class WorkflowStateManager:
    """
    Gerencia o estado centralizado do workflow.
    Responsável por manter contexto global, histórico e snapshots.
    """
    
    def __init__(self, execution_id: str, checkpoint_file: Optional[str] = None):
        self.checkpoint_file = checkpoint_file
        
        # Tentar carregar se existir
        if self.checkpoint_file and os.path.exists(self.checkpoint_file):
            try:
                self.load_checkpoint()
            except Exception as e:
                # Se falhar, inicia novo estado mas mantém o arquivo configurado
                print(f"Erro ao carregar checkpoint: {e}")
                self._state = WorkflowState(execution_id=execution_id)
        else:
            self._state = WorkflowState(execution_id=execution_id)
    
    @property
    def state(self) -> WorkflowState:
        return self._state
    
    @property
    def context(self) -> Dict[str, Any]:
        return self._state.global_context
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Atualiza o contexto global com novos valores."""
        self._state.global_context.update(updates)
        self.save_checkpoint()
    
    def set_step(self, step_id: str) -> None:
        """Define o passo atual."""
        self._state.current_step_id = step_id
        self.save_checkpoint()
    
    def add_history_entry(self, entry: Dict[str, Any]) -> None:
        """Adiciona uma entrada ao histórico de execução."""
        entry["timestamp"] = datetime.now().isoformat()
        self._state.execution_history.append(entry)
        self.save_checkpoint()
    
    def set_status(self, status: str) -> None:
        """Atualiza o status da execução."""
        self._state.status = status
        self.save_checkpoint()
    
    def create_snapshot(self) -> Dict[str, Any]:
        """Cria um snapshot serializável do estado atual."""
        return self._state.model_dump(mode='json')
    
    def restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restaura o estado a partir de um snapshot."""
        self._state = WorkflowState(**snapshot)
        self.save_checkpoint()

    def save_checkpoint(self) -> None:
        """Salva o estado atual no arquivo de checkpoint."""
        if not self.checkpoint_file:
            return
        
        try:
            # Garantir que o diretório existe
            os.makedirs(os.path.dirname(os.path.abspath(self.checkpoint_file)), exist_ok=True)
            
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                f.write(self._state.model_dump_json(indent=2))
        except Exception as e:
            print(f"Erro ao salvar checkpoint: {e}")

    def load_checkpoint(self) -> None:
        """Carrega o estado do arquivo de checkpoint."""
        if not self.checkpoint_file or not os.path.exists(self.checkpoint_file):
            return
            
        with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self._state = WorkflowState(**data)
