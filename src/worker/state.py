from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import copy

@dataclass
class WorkflowState:
    """Representa o estado atual da execução do workflow."""
    execution_id: str
    start_time: datetime
    current_step_id: Optional[str] = None
    global_context: Dict[str, Any] = field(default_factory=dict)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "initialized"  # initialized, running, completed, failed, paused

class WorkflowStateManager:
    """
    Gerencia o estado centralizado do workflow.
    Responsável por manter contexto global, histórico e snapshots.
    """
    
    def __init__(self, execution_id: str):
        self._state = WorkflowState(
            execution_id=execution_id,
            start_time=datetime.now()
        )
    
    @property
    def state(self) -> WorkflowState:
        return self._state
    
    @property
    def context(self) -> Dict[str, Any]:
        return self._state.global_context
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Atualiza o contexto global com novos valores."""
        self._state.global_context.update(updates)
    
    def set_step(self, step_id: str) -> None:
        """Define o passo atual."""
        self._state.current_step_id = step_id
    
    def add_history_entry(self, entry: Dict[str, Any]) -> None:
        """Adiciona uma entrada ao histórico de execução."""
        entry["timestamp"] = datetime.now().isoformat()
        self._state.execution_history.append(entry)
    
    def set_status(self, status: str) -> None:
        """Atualiza o status da execução."""
        self._state.status = status
    
    def create_snapshot(self) -> Dict[str, Any]:
        """Cria um snapshot serializável do estado atual."""
        # Deep copy para evitar modificações acidentais no snapshot
        return copy.deepcopy(self._state.__dict__)
    
    def restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restaura o estado a partir de um snapshot."""
        # TODO: Implementar validação de schema do snapshot
        self._state = WorkflowState(**snapshot)
