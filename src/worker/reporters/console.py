"""
Console Reporter para visualização rica de eventos.

Usa a biblioteca 'rich' se disponível, ou fallback para print formatado.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from src.worker.interfaces import WorkerEvent, WorkerEventType

logger = logging.getLogger("worker.reporters.console")

# Tentar importar rich
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.json import JSON
    from rich.theme import Theme
    from rich.status import Status
    
    HAS_RICH = True
    
    # Tema customizado
    custom_theme = Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "tool": "magenta",
        "agent": "blue",
        "workflow": "purple",
    })
    
    console = Console(theme=custom_theme)
    
except ImportError:
    HAS_RICH = False
    console = None


class ConsoleReporter:
    """
    Reporter que imprime eventos no console de forma visual.
    """
    
    def __init__(self):
        self._status: Optional[Any] = None
        self._current_step: Optional[str] = None
    
    def _is_stream_placeholder(self, content: Any) -> bool:
        """
        Detecta se o conteúdo é um placeholder de streaming ou um async_generator.
        
        Retorna True para:
        - "[Streaming response...]"
        - "<async_generator object ...>"
        - "<generator object ...>"
        """
        if not content:
            return False
        
        content_str = str(content)
        
        stream_indicators = [
            "[Streaming response...]",
            "async_generator object",
            "generator object",
            "<async_generator",
            "<generator",
        ]
        
        return any(indicator in content_str for indicator in stream_indicators)
    
    def handle_event(self, event: WorkerEvent) -> None:
        """Callback principal para eventos."""
        try:
            if HAS_RICH:
                self._handle_rich(event)
            else:
                self._handle_plain(event)
        except Exception as e:
            # Fallback seguro para não quebrar execução
            print(f"[Reporter Error] {e}")
    
    def _handle_rich(self, event: WorkerEvent) -> None:
        """Renderização rica com rich."""
        data = event.data
        timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
        
        if event.type == WorkerEventType.WORKFLOW_START:
            console.print()
            console.print(Panel(
                "[bold purple]⚡ Iniciando Workflow[/]",
                subtitle=f"[dim]{timestamp}[/]",
                border_style="purple"
            ), justify="center")
            
        elif event.type == WorkerEventType.WORKFLOW_STEP:
            step_id = data.get("step_id", "unknown")
            console.print(f"  [dim purple]├─[/] [purple]Step: {step_id}[/] [dim]({timestamp})[/]")
            
        elif event.type == WorkerEventType.AGENT_START:
            agent_name = data.get("agent_name", "unknown")
            console.print(f"  [dim blue]├─[/] [blue]🤖 {agent_name}[/] [dim]({timestamp})[/]")
            
        elif event.type == WorkerEventType.AGENT_RESPONSE:
            agent_name = data.get("agent_name", "unknown")
            content = data.get("content", "")
            
            # Detectar e tratar respostas de streaming
            if self._is_stream_placeholder(content):
                return
            
            # Tentar formatar JSON se parecer JSON
            if isinstance(content, (dict, list)):
                content_render = JSON.from_data(content)
            else:
                content_render = str(content)
            
            console.print()
            console.print(Panel(
                content_render,
                title=f"[blue]💬 {agent_name}[/]",
                subtitle=f"[dim]{timestamp}[/]",
                border_style="blue",
                expand=False,
                padding=(0, 1)
            ))
            
        elif event.type == WorkerEventType.TOOL_CALL_START:
            tool = data.get("tool", "unknown")
            args = data.get("arguments", {})
            console.print(f"  [dim magenta]├─[/] [magenta]🔧 {tool}[/] [dim]({timestamp})[/]")
            if args:
                console.print(f"  [dim]│   {json.dumps(args, ensure_ascii=False)[:80]}[/]")
            
        elif event.type == WorkerEventType.TOOL_CALL_COMPLETE:
            tool = data.get("tool", "unknown")
            result = data.get("result", "")
            result_str = str(result)[:100]
            console.print(f"  [dim green]├─[/] [green]✓ {tool}[/] [dim]→ {result_str} ({timestamp})[/]")
            
        elif event.type == WorkerEventType.TOOL_CALL_ERROR:
            tool = data.get("tool", "unknown")
            error = data.get("error", "unknown")
            console.print(f"  [dim red]├─[/] [bold red]✗ {tool}: {error}[/] [dim]({timestamp})[/]")
            
        elif event.type == WorkerEventType.WORKFLOW_COMPLETE:
            result = data.get("result", "")
            console.print()
            console.print(Panel(
                str(result),
                title="[bold green]📋 RESULTADO FINAL[/]",
                subtitle=f"[dim]Workflow concluído com sucesso • {timestamp}[/]",
                border_style="bold green",
                padding=(1, 2)
            ))
            console.print()
            
        elif event.type == WorkerEventType.WORKFLOW_ERROR:
            error = data.get("error", "unknown")
            console.print()
            console.print(Panel(
                str(error),
                title="[bold red]❌ ERRO[/]",
                subtitle="[dim]Workflow falhou[/]",
                border_style="bold red",
                padding=(1, 2)
            ))
            
        # ===== Eventos de Agente Standalone =====
        elif event.type == WorkerEventType.AGENT_RUN_START:
            agent_name = data.get("agent_name", "unknown")
            agent_role = data.get("agent_role", "")
            tools_count = data.get("tools_count", 0)
            
            info_parts = []
            if agent_role:
                info_parts.append(f"[bold]{agent_role}[/]")
            if tools_count > 0:
                info_parts.append(f"[dim]🔧 {tools_count} ferramentas[/]")
            
            header = "\n".join(info_parts) if info_parts else "[dim]Processando...[/]"
            
            console.print()
            console.print(Panel(
                header,
                title=f"[bold cyan]🤖 {agent_name}[/]",
                subtitle=f"[dim]{timestamp}[/]",
                border_style="cyan"
            ), justify="center")
            
        elif event.type == WorkerEventType.AGENT_RUN_COMPLETE:
            agent_name = data.get("agent_name", "unknown")
            result = data.get("result", "")
            
            # Exibir resultado do agente standalone
            if result and not self._is_stream_placeholder(result):
                if isinstance(result, (dict, list)):
                    content_render = JSON.from_data(result)
                else:
                    content_render = str(result)
                
                console.print()
                console.print(Panel(
                    content_render,
                    title=f"[bold green]📋 RESPOSTA[/]",
                    subtitle=f"[dim]{agent_name} concluído • {timestamp}[/]",
                    border_style="bold green",
                    expand=False,
                    padding=(1, 2)
                ))
                console.print()
            else:
                console.print(f"  [dim green]└─[/] [green]✓ {agent_name} concluído[/] [dim]({timestamp})[/]")

    def _handle_plain(self, event: WorkerEvent) -> None:
        """Renderização simples (fallback)."""
        timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{event.type.value}]"
        
        if event.type == WorkerEventType.AGENT_RESPONSE:
            agent = event.data.get("agent_name", "Agent")
            content = event.data.get("content", "")
            print(f"\n{prefix} 🤖 {agent}:")
            print(f"{content}\n")
            
        elif event.type == WorkerEventType.TOOL_CALL_START:
            tool = event.data.get("tool", "unknown")
            args = event.data.get("arguments", {})
            print(f"{prefix} 🛠️  Tool Call: {tool}({args})")
            
        elif event.type == WorkerEventType.TOOL_CALL_COMPLETE:
            tool = event.data.get("tool", "unknown")
            result = str(event.data.get("result", ""))
            print(f"{prefix} ✅ Tool Result: {result}")
            
        elif event.type == WorkerEventType.WORKFLOW_ERROR:
            print(f"{prefix} ❌ Error: {event.data.get('error')}")
            
        elif event.type == WorkerEventType.AGENT_RUN_START:
            agent = event.data.get("agent_name", "unknown")
            role = event.data.get("agent_role", "")
            print(f"\n{'='*60}")
            print(f"{prefix} 🤖 Iniciando Agente: {agent}")
            if role:
                print(f"   Role: {role}")
            print(f"{'='*60}")
            
        elif event.type == WorkerEventType.AGENT_RUN_COMPLETE:
            agent = event.data.get("agent_name", "unknown")
            result = event.data.get("result", "")
            print(f"{prefix} ✅ Agente {agent} concluído")
            if result:
                print(f"\n{'='*60}")
                print(f"📝 RESPOSTA:")
                print(f"{'='*60}")
                print(result)
                print(f"{'='*60}\n")
            
        else:
            # Log genérico para outros eventos
            # print(f"{prefix} {event.data}")
            pass
