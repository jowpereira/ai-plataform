from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
from collections.abc import AsyncIterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

import typer
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from agent_framework import (
    AgentRunResponse,
    ChatAgent,
    Workflow,
    WorkflowBuilder,
    WorkflowEvent,
    WorkflowOutputEvent,
)
from agent_framework.openai import OpenAIChatClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

app = typer.Typer(add_completion=False, help="Runner genérico para workers do Microsoft Agent Framework.")


class ToolConfig(BaseModel):
    name: str = Field(..., description="Identificador usado pelos agentes")
    import_path: str = Field(..., description="Caminho module:callable para importar a ferramenta")


class ClientConfig(BaseModel):
    type: Literal["openai-chat"] = "openai-chat"
    model_id: str | None = Field(default=None, description="Model ID explícito")
    model_env: str | None = Field(default="OPENAI_MODEL", description="Variável de ambiente com o model ID")

    def resolve_model(self) -> str:
        if self.model_id:
            return self.model_id
        if self.model_env:
            value = os.getenv(self.model_env)
            if value:
                return value
        raise ValueError(
            "Não foi possível determinar o model_id. Configure model_id ou a variável de ambiente informada em model_env."
        )


class AgentConfig(BaseModel):
    id: str
    name: str
    instructions: str
    description: str | None = None
    client: ClientConfig
    tools: list[str] = Field(default_factory=list)
    temperature: float | None = None
    max_tokens: int | None = None
    emit_output: bool = Field(default=False, description="Quando verdadeiro, envia o AgentRunResponse aos outputs do workflow")


class WorkflowEdgeConfig(BaseModel):
    source: str
    target: str


class WorkflowConfig(BaseModel):
    start: str
    edges: list[WorkflowEdgeConfig]


class WorkspaceConfig(BaseModel):
    name: str
    description: str | None = None
    max_iterations: int = Field(default=4, ge=1, le=25)


class WorkerConfig(BaseModel):
    workspace: WorkspaceConfig
    tools: list[ToolConfig]
    agents: list[AgentConfig]
    workflow: WorkflowConfig

    @classmethod
    def from_path(cls, path: Path) -> "WorkerConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.model_validate(data)


@dataclass
class RuntimeContext:
    config: WorkerConfig
    tools: dict[str, Callable[..., Any]]
    agents: dict[str, ChatAgent]

    def ensure_ready(self) -> None:
        missing_edges = {
            edge.source
            for edge in self.config.workflow.edges
            if edge.source not in self.agents or edge.target not in self.agents
        }
        if missing_edges:
            joined = ", ".join(sorted(missing_edges))
            raise ValueError(f"IDs de agentes inválidos no workflow: {joined}")

    def build_workflow(self) -> "Workflow":
        builder = WorkflowBuilder(
            max_iterations=self.config.workspace.max_iterations,
            name=self.config.workspace.name,
            description=self.config.workspace.description,
        )
        for agent_cfg in self.config.agents:
            builder.add_agent(
                self.agents[agent_cfg.id],
                id=agent_cfg.id,
                output_response=agent_cfg.emit_output,
            )
        builder.set_start_executor(self.config.workflow.start)
        for edge in self.config.workflow.edges:
            builder.add_edge(self.agents[edge.source], self.agents[edge.target])
        return builder.build()


def resolve_tool(import_path: str) -> Callable[..., Any]:
    if ":" not in import_path:
        raise ValueError(f"Formato inválido para import_path: {import_path}. Use modulo:callable")
    module_name, attr_path = import_path.split(":", maxsplit=1)
    module = importlib.import_module(module_name)
    target: Any = module
    for part in attr_path.split("."):
        target = getattr(target, part)
    if not callable(target):
        raise TypeError(f"Objeto importado não é chamável: {import_path}")
    return target


def build_runtime(config_path: Path) -> RuntimeContext:
    config = WorkerConfig.from_path(config_path)
    tools: dict[str, Callable[..., Any]] = {}
    for tool in config.tools:
        tools[tool.name] = resolve_tool(tool.import_path)

    agents: dict[str, ChatAgent] = {}
    for agent_cfg in config.agents:
        client = OpenAIChatClient(model_id=agent_cfg.client.resolve_model())
        agent = ChatAgent(
            chat_client=client,
            name=agent_cfg.name,
            description=agent_cfg.description,
            instructions=agent_cfg.instructions,
            temperature=agent_cfg.temperature,
            max_tokens=agent_cfg.max_tokens,
            tools=[tools[name] for name in agent_cfg.tools if name in tools],
        )
        agents[agent_cfg.id] = agent

    runtime = RuntimeContext(config=config, tools=tools, agents=agents)
    runtime.ensure_ready()
    return runtime


def extract_text(response: AgentRunResponse) -> str:
    chunks: list[str] = []
    for message in response.messages:
        for content in message.contents:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)
    return "\n".join(chunks)


async def run_workflow(runtime: RuntimeContext, message: str, stream: bool) -> list[str]:
    workflow = runtime.build_workflow()
    rendered: list[str] = []
    if stream:
        async for event in workflow.run_stream(message=message):
            if isinstance(event, WorkflowOutputEvent) and isinstance(event.data, AgentRunResponse):
                text = extract_text(event.data)
                typer.echo(typer.style("[stream] ", fg=typer.colors.CYAN) + text)
                rendered.append(text)
    else:
        result = await workflow.run(message=message)
        for event in result.get_outputs():
            if isinstance(event, AgentRunResponse):
                rendered.append(extract_text(event))
    return rendered


@app.command("run")
def run_worker(
    config: Path = typer.Option(
        Path("scripts/worker_test/config/worker.json"),
        "--config",
        "-c",
        help="Arquivo JSON com a configuração dinâmica",
    ),
    message: str = typer.Option(
        "Monte um playbook para responder incidentes em lote e entregue próximos passos.",
        "--message",
        "-m",
        help="Mensagem inicial repassada ao agente de entrada",
    ),
    stream: bool = typer.Option(False, "--stream/--no-stream", help="Mostra eventos ao vivo"),
    plan_only: bool = typer.Option(
        False,
        "--plan-only",
        help="Valida configuração e exibe os agentes/ferramentas sem chamar modelos",
    ),
) -> None:
    """Executa o worker com base em um arquivo de configuração JSON."""

    load_dotenv()
    try:
        runtime = build_runtime(config)
    except (FileNotFoundError, ValidationError, ValueError, TypeError) as exc:
        typer.echo(typer.style(f"Falha ao carregar configuração: {exc}", fg=typer.colors.RED))
        raise typer.Exit(code=1) from exc

    if plan_only:
        typer.echo(typer.style("Configuração carregada com sucesso", fg=typer.colors.GREEN))
        typer.echo("Agentes:")
        for agent in runtime.config.agents:
            typer.echo(f"- {agent.id}: {agent.name} -> ferramentas {agent.tools or ['sem ferramentas']}")
        return

    try:
        outputs = asyncio.run(run_workflow(runtime, message, stream))
    except Exception as exc:  # pragma: no cover - diagnóstico interativo
        typer.echo(typer.style(f"Execução falhou: {exc}", fg=typer.colors.RED))
        raise typer.Exit(code=2) from exc

    if not outputs:
        typer.echo(typer.style("Nenhum output gerado. Verifique se algum agente possui emit_output=true.", fg=typer.colors.YELLOW))
        raise typer.Exit(code=3)

    typer.echo(typer.style("Resposta final:", bold=True))
    typer.echo("\n---\n".join(outputs))


if __name__ == "__main__":
    app()
