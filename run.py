from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv

# Configurar encoding UTF-8 para Windows
if sys.platform == "win32":
    # Forçar UTF-8 no console do Windows
    os.system("chcp 65001 > nul 2>&1")
    
    # Configurar variáveis de ambiente para UTF-8
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    # Reconfigure stdout/stderr para UTF-8 se possível
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Adiciona a raiz do projeto ao sys.path para permitir imports de src
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.worker.config import ConfigLoader, StandaloneAgentConfig, WorkerConfig, RagConfig, RagEmbeddingConfig
from src.worker.engine import WorkflowEngine
from src.worker.runner import AgentRunner
from src.worker.rag.knowledge.service import KnowledgeBaseService

from src.worker.rag import register_vector_store

app = typer.Typer(add_completion=False, help="Executor genérico para workers do Microsoft Agent Framework.")
rag_app = typer.Typer(help="Gerenciamento de RAG (Knowledge Base)")
app.add_typer(rag_app, name="rag")


def get_rag_service() -> KnowledgeBaseService:
    """Inicializa o serviço de Knowledge Base para CLI."""
    load_dotenv()
    
    # Configuração padrão para CLI
    def config_getter() -> RagConfig:
        return RagConfig(
            enabled=True,
            provider="memory",
            embedding=RagEmbeddingConfig(
                model="text-embedding-ada-002",
                dimensions=1536,
                normalize=True
            )
        )
    
    root_dir = PROJECT_ROOT / ".maia" / "knowledge"
    return KnowledgeBaseService(
        root_dir=root_dir,
        rag_config_getter=config_getter
    )


async def setup_rag_for_execution():
    """Prepara o ambiente RAG para execução de agentes."""
    try:
        service = get_rag_service()
        # Carregar dados persistidos para a memória
        await service.rebuild_vector_index(force_reembed=False)
        # Registrar store para ser usado pelo RagRuntime
        register_vector_store(service.get_vector_store())
        # Contar documentos de todas as coleções
        state = service.get_state_snapshot()
        total_docs = len(state.documents)
        total_chunks = sum(c.chunk_count for c in state.collections.values())
        print(f"📚 RAG inicializado com {total_docs} documentos ({total_chunks} chunks)")
    except Exception as e:
        print(f"⚠️ Falha ao inicializar RAG: {e}")


@rag_app.command("init")
def rag_init(
    name: str = typer.Option(..., "--name", "-n", help="Nome da coleção"),
    description: str = typer.Option("", "--desc", "-d", help="Descrição da coleção"),
):
    """Cria uma nova coleção na Knowledge Base."""
    service = get_rag_service()
    try:
        collection = service.create_collection(name=name, description=description)
        print(f"✅ Coleção '{name}' criada com sucesso!")
        print(f"   ID: {collection.id}")
        print(f"   Namespace: {collection.namespace}")
    except Exception as e:
        print(f"❌ Erro ao criar coleção: {e}")


@rag_app.command("list")
def rag_list():
    """Lista todas as coleções existentes."""
    service = get_rag_service()
    collections = service.list_collections()
    print(f"📚 Encontradas {len(collections)} coleções:")
    for col in collections:
        print(f"   - {col.name} (ID: {col.id})")
        print(f"     Docs: {col.document_count} | Chunks: {col.chunk_count}")


@rag_app.command("ingest")
def rag_ingest(
    collection_name: str = typer.Option(..., "--collection", "-c", help="Nome da coleção destino"),
    file_path: str = typer.Option(..., "--file", "-f", help="Caminho do arquivo para ingestão"),
):
    """Ingere um arquivo em uma coleção."""
    service = get_rag_service()
    
    # Encontrar ID da coleção pelo nome
    collections = service.list_collections()
    target_col = next((c for c in collections if c.name == collection_name), None)
    
    if not target_col:
        print(f"❌ Coleção '{collection_name}' não encontrada.")
        return

    path = Path(file_path)
    if not path.exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        return

    print(f"📤 Ingerindo '{path.name}' em '{collection_name}'...")
    
    async def _ingest():
        with open(path, "rb") as f:
            content = f.read()
        
        try:
            result = await service.ingest_file(
                collection_id=target_col.id,
                filename=path.name,
                content_type="text/plain", # Simplificação para CLI
                raw_bytes=content
            )
            print(f"✅ Ingestão concluída!")
            print(f"   Documento ID: {result.document.id}")
            print(f"   Chunks gerados: {result.document.chunk_count}")
        except Exception as e:
            print(f"❌ Erro na ingestão: {e}")

    asyncio.run(_ingest())


@rag_app.command("search")
def rag_search(
    query: str = typer.Option(..., "--query", "-q", help="Texto da busca"),
    collection_name: str = typer.Option(None, "--collection", "-c", help="Filtrar por coleção (opcional)"),
    top_k: int = typer.Option(3, "--top", "-k", help="Número de resultados"),
):
    """Realiza busca semântica na Knowledge Base."""
    service = get_rag_service()
    
    col_id = None
    if collection_name:
        collections = service.list_collections()
        target_col = next((c for c in collections if c.name == collection_name), None)
        if target_col:
            col_id = target_col.id
        else:
            print(f"⚠️ Coleção '{collection_name}' não encontrada. Buscando em tudo.")

    async def _search():
        try:
            # Carregar índice antes de buscar
            await service.rebuild_vector_index(force_reembed=False)
            
            results = await service.search(query=query, collection_id=col_id, top_k=top_k)
            print(f"\n🔍 Resultados para: '{query}'")
            if not results:
                print("   Nenhum resultado encontrado.")
                return
                
            for i, res in enumerate(results, 1):
                print(f"\n   #{i} [Score: {res.score:.3f}]")
                print(f"   📄 Doc: {res.metadata.get('source', 'N/A')}")
                print(f"   📝 Conteúdo: {res.content[:200]}...")
        except Exception as e:
            print(f"❌ Erro na busca: {e}")

    asyncio.run(_search())


def load_all_examples_for_ui():
    """Carrega todos os exemplos da pasta 'exemplos' para o MAIA."""
    examples_dir = PROJECT_ROOT / "exemplos"
    entities = []

    if not examples_dir.exists():
        print(f"Diretório de exemplos não encontrado: {examples_dir}")
        return []

    # Carregar todos os arquivos JSON da pasta exemplos
    files_to_load = list(examples_dir.glob("*.json"))

    for file_path in files_to_load:
        print(f"Carregando exemplo: {file_path.name}")
        try:
            loader = ConfigLoader(str(file_path))
            config = loader.load()
            
            engine = WorkflowEngine(config)
            engine.build()
            
            if engine._workflow:
                entities.append(engine._workflow)
                
                # 1. Registrar instâncias do workflow (ex: step1, step2)
                # Isso permite debug de nós específicos
                workflow_agents = engine.get_agents()
                # entities.extend(workflow_agents)
                
                # 2. Registrar templates de agentes (ex: weather_agent)
                # Isso permite que o frontend recrie o workflow referenciando os templates
                template_count = 0
                if config.agents:
                    for agent_conf in config.agents:
                        try:
                            # Verificar se já não foi adicionado (evitar duplicatas se ID coincidir)
                            if not any(e.id == agent_conf.id for e in entities):
                                template_agent = engine.agent_factory.create_agent(agent_conf.id)
                                # Garantir ID original
                                template_agent.id = agent_conf.id
                                # Marcar como oculto para não poluir a UI (mas estar disponível para o engine)
                                template_agent._maia_hidden = True
                                entities.append(template_agent)
                                template_count += 1
                        except Exception as e:
                            print(f"⚠️ Aviso: Falha ao criar template '{agent_conf.id}': {e}")

                print(f"✅ Adicionado: {config.name} ({file_path.name}) + {len(workflow_agents)} nós (ocultos) + {template_count} templates (ocultos)")
            else:
                print(f"⚠️ Falha ao construir workflow para {file_path.name}")
                
        except Exception as e:
            print(f"❌ Erro ao carregar {file_path.name}: {e}")

    return entities


@app.command()
def run(
    config_path: str = typer.Option(
        "exemplos/sequential.json",
        "--config",
        "-c",
        help="Caminho para o arquivo de configuração (workflow ou agente)",
    ),
    input_text: str = typer.Option(
        "Londres",
        "--input",
        "-i",
        help="Input inicial para o workflow ou agente",
    ),
    dev_ui: bool = typer.Option(
        False,
        "--ui",
        "--dev",
        help="Inicia o servidor MAIA com todos os exemplos (Ignora --config e --input)",
    ),
    stream: bool = typer.Option(
        True,
        "--stream/--no-stream",
        help="Usa streaming (ainvoke) ou execução direta (invoke). Streaming mostra respostas de cada agente.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Habilita logging detalhado de eventos do framework",
    ),
):
    """
    Executa o worker genérico.
    
    Modo CLI (padrão): Executa um workflow ou agente específico com input via terminal.
    Modo UI (--ui): Inicia o servidor MAIA para visualização e debug.
    
    Detecção automática:
    - Arquivos com 'workflow' e 'resources' → executados como workflow
    - Arquivos com 'model' e 'instructions' → executados como agente standalone
    """
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Configurar nível de logging
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        # Habilitar debug do worker
        logging.getLogger("worker").setLevel(logging.DEBUG)
        print("🔍 Modo DEBUG habilitado")

    if dev_ui:
        # --- MODO UI ---
        try:
            # Usando versão local do MAIA (src.maia_ui)
            from src.maia_ui import serve
            print("📦 Usando versão local do MAIA (src.maia_ui)")
        except ImportError as e:
            print(f"❌ Erro ao importar 'src.maia_ui': {e}")
            print("Verifique se a pasta 'src/maia_ui' existe e contém o arquivo '__init__.py'.")
            raise typer.Exit(code=1)

        os.environ["DEVUI_MODE"] = "true"
        print("🚀 Iniciando MAIA com exemplos locais...")
        
        examples_dir = PROJECT_ROOT / "exemplos"
        if not examples_dir.exists():
             print(f"Diretório de exemplos não encontrado: {examples_dir}")
             raise typer.Exit(code=1)

        print(f"Iniciando servidor monitorando: {examples_dir}")
            
        serve(entities_dir=str(examples_dir))
        return

    # --- MODO CLI ---
    # Resolver caminho absoluto
    abs_config_path = os.path.abspath(config_path)
    
    try:
        loader = ConfigLoader(abs_config_path)
        config_type = loader.detect_config_type()
        
        print(f"📄 Tipo detectado: {config_type}")
        
    except Exception as e:
        print(f"❌ Falha ao carregar configuração: {e}")
        raise typer.Exit(code=1)

    async def _run_workflow_async(config: WorkerConfig):
        """Executa workflow via WorkflowEngine."""
        # Configurar reporter visual
        try:
            from src.worker.events import get_event_bus
            from src.worker.reporters.console import ConsoleReporter
            
            bus = get_event_bus()
            reporter = ConsoleReporter()
            bus.subscribe_all(reporter.handle_event)
        except ImportError as e:
            print(f"⚠️ Falha ao carregar reporter visual: {e}")

        try:
            engine = WorkflowEngine(config)
            if stream:
                result = await engine.ainvoke(initial_input=input_text)
            else:
                result = await engine.invoke(initial_input=input_text)
            
        except Exception as e:
            print(f"\n❌ Erro de Execução: {e}")
            import traceback
            traceback.print_exc()
            raise typer.Exit(code=1)

    async def _run_agent_async(config: StandaloneAgentConfig):
        """Executa agente standalone via AgentRunner."""
        
        # Resolver nomes de coleções para IDs se necessário
        if config.knowledge and config.knowledge.collection_ids:
            try:
                service = get_rag_service()
                resolved_ids = []
                for col_ref in config.knowledge.collection_ids:
                    # Tentar encontrar por nome
                    collections = service.list_collections()
                    target_col = next((c for c in collections if c.name == col_ref), None)
                    
                    if target_col:
                        resolved_ids.append(target_col.id)
                    else:
                        # Assumir que já é um ID se não encontrar por nome
                        try:
                            if service.get_collection(col_ref):
                                resolved_ids.append(col_ref)
                        except ValueError:
                            print(f"⚠️ Aviso: Coleção '{col_ref}' não encontrada (ignorada)")
                
                if resolved_ids:
                    print(f"🔍 Coleções resolvidas: {config.knowledge.collection_ids} -> {resolved_ids}")
                    config.knowledge.collection_ids = resolved_ids
                else:
                    print(f"⚠️ Aviso: Nenhuma coleção válida encontrada para {config.knowledge.collection_ids}")
            except Exception as e:
                print(f"⚠️ Erro ao resolver coleções: {e}")

        # Configurar reporter visual
        try:
            from src.worker.events import get_event_bus
            from src.worker.reporters.console import ConsoleReporter
            
            bus = get_event_bus()
            reporter = ConsoleReporter()
            bus.subscribe_all(reporter.handle_event)
        except ImportError as e:
            print(f"⚠️ Falha ao carregar reporter visual: {e}")

        try:
            runner = AgentRunner(config)
            result = await runner.run(input_text)
            # Resultado já é exibido pelo ConsoleReporter via AGENT_RUN_COMPLETE
            await runner.teardown()
            
        except Exception as e:
            print(f"\n❌ Erro de Execução: {e}")
            import traceback
            traceback.print_exc()
            raise typer.Exit(code=1)

    # Executar baseado no tipo detectado
    if config_type == "agent":
        config = loader.load_agent()
        print(f"🤖 Executando agente: {config.id} ({config.role})")
        
        # Inicializar RAG se necessário
        asyncio.run(setup_rag_for_execution())
        
        asyncio.run(_run_agent_async(config))
    else:
        config = loader.load()
        print(f"⚙️ Executando workflow: {config.name}")
        
        # Inicializar RAG se necessário
        asyncio.run(setup_rag_for_execution())
        
        asyncio.run(_run_workflow_async(config))


if __name__ == "__main__":
    app()
