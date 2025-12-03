# Copyright (c) Microsoft. All rights reserved.

"""FastAPI server implementation."""

import inspect
import json
import logging
import os
import secrets
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from ._deployment import DeploymentManager
from ._discovery import EntityDiscovery
from ._executor import AgentFrameworkExecutor
from ._mapper import MessageMapper
from ._openai import OpenAIExecutor
from .models import AgentFrameworkRequest, MetaResponse, OpenAIError
from .models._discovery_models import Deployment, DeploymentConfig, DiscoveryResponse, EntityInfo
from src.worker.config import RagConfig
from src.worker.rag import register_vector_store, configure_rag_runtime_from_config
from src.worker.rag.knowledge.loader import UnsupportedFileError
from src.worker.rag.knowledge.service import KnowledgeBaseService

logger = logging.getLogger(__name__)

# Diretório raiz do projeto (onde está o run.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class KnowledgeCollectionRequest(BaseModel):
    name: str
    description: str | None = None
    namespace: str | None = None
    tags: list[str] | None = None


class KnowledgeSearchRequest(BaseModel):
    query: str
    collection_id: str | None = None
    top_k: int = 5


# No AuthMiddleware class needed - we'll use the decorator pattern instead


class DevServer:
    """Development Server - OpenAI compatible API server for debugging agents."""

    def __init__(
        self,
        entities_dir: str | None = None,
        port: int = 8080,
        host: str = "127.0.0.1",
        cors_origins: list[str] | None = None,
        ui_enabled: bool = True,
        mode: str = "developer",
    ) -> None:
        """Initialize the development server.

        Args:
            entities_dir: Directory to scan for entities
            port: Port to run server on
            host: Host to bind server to
            cors_origins: List of allowed CORS origins
            ui_enabled: Whether to enable the UI
            mode: Server mode - 'developer' (full access, verbose errors) or 'user' (restricted APIs, generic errors)
        """
        self.entities_dir = entities_dir
        self.port = port
        self.host = host

        # Smart CORS defaults: permissive for localhost, restrictive for network-exposed deployments
        if cors_origins is None:
            # Localhost development: allow cross-origin for dev tools (e.g., frontend dev server)
            # Network-exposed: empty list (same-origin only, no CORS)
            cors_origins = ["*"] if host in ("127.0.0.1", "localhost") else []

        self.cors_origins = cors_origins
        self.ui_enabled = ui_enabled
        self.mode = mode
        self.executor: AgentFrameworkExecutor | None = None
        self.openai_executor: OpenAIExecutor | None = None
        self.deployment_manager = DeploymentManager()
        self._app: FastAPI | None = None
        self._pending_entities: list[Any] | None = None
        self._app_dir = PROJECT_ROOT / ".maia"
        self._app_dir.mkdir(parents=True, exist_ok=True)
        self._rag_config_path = self._app_dir / "rag_config.json"
        self._knowledge_root = self._app_dir / "knowledge"
        self._rag_config: RagConfig | None = None
        self._knowledge_base: KnowledgeBaseService | None = None

    def _is_dev_mode(self) -> bool:
        """Check if running in developer mode.

        Returns:
            True if in developer mode, False if in user mode
        """
        return self.mode == "developer"

    def _format_error(self, error: Exception, context: str = "Operation") -> str:
        """Format error message based on server mode.

        In developer mode: Returns detailed error message for debugging.
        In user mode: Returns generic message and logs details internally.

        Args:
            error: The exception that occurred
            context: Description of the operation that failed (e.g., "Request execution")

        Returns:
            Formatted error message appropriate for the current mode
        """
        if self._is_dev_mode():
            # Developer mode: Show full error details for debugging
            return f"{context} failed: {error!s}"

        # User mode: Generic message to user, detailed logging internally
        logger.error(f"{context} failed: {error}", exc_info=True)
        return f"{context} failed"

    def _enrich_workflow_dump(
        self, workflow_dump: dict[str, Any] | None, source_config: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Inject original node metadata into the workflow dump for UI consumption."""

        if not workflow_dump or not isinstance(workflow_dump, dict):
            return workflow_dump

        if not source_config or not isinstance(source_config, dict):
            return workflow_dump

        workflow_section = source_config.get("workflow")
        if not isinstance(workflow_section, dict):
            return workflow_dump

        nodes = []
        if isinstance(workflow_section.get("nodes"), list):
            nodes = workflow_section["nodes"]  # type: ignore[assignment]
        elif isinstance(workflow_section.get("steps"), list):
            nodes = workflow_section["steps"]  # type: ignore[assignment]

        executors = workflow_dump.get("executors")
        if not isinstance(executors, dict) or not nodes:
            return workflow_dump

        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_id = node.get("id")
            if not node_id or node_id not in executors:
                continue

            executor_payload = executors[node_id]
            if not isinstance(executor_payload, dict):
                continue

            node_type = node.get("type")
            if not node_type and node.get("agent"):
                node_type = "agent"

            if node_type:
                executor_payload["node_type"] = node_type

            if node.get("agent"):
                executor_payload["agent"] = node["agent"]

            if node.get("input_template"):
                executor_payload["input_template"] = node["input_template"]

            config_payload = node.get("config") or {}
            if isinstance(config_payload, dict):
                # Preserve agent reference for downstream reconstruction
                if node.get("agent") and "agent_id" not in config_payload:
                    config_payload = {**config_payload, "agent_id": node["agent"]}
                if config_payload:
                    executor_payload["config"] = config_payload

        return workflow_dump

    def _require_developer_mode(self, feature: str = "operation") -> None:
        """Check if current mode allows developer operations.

        Args:
            feature: Name of the feature being accessed (for error message)

        Raises:
            HTTPException: If in user mode
        """
        if self.mode == "user":
            logger.warning(f"Blocked {feature} access in user mode")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "message": f"Access denied: {feature} requires developer mode",
                        "type": "permission_denied",
                        "code": "developer_mode_required",
                        "current_mode": self.mode,
                    }
                },
            )

    async def _ensure_executor(self) -> AgentFrameworkExecutor:
        """Ensure executor is initialized."""
        if self.executor is None:
            logger.info("Initializing Agent Framework executor...")

            # Inicializar Knowledge Base/RAG runtime ANTES de descobrir entidades
            # Isso garante que agentes com knowledge.enabled tenham o RAG disponível
            try:
                self._get_knowledge_base()
                logger.info("🔗 RAG runtime inicializado para suportar Knowledge Base")
            except Exception as e:
                logger.warning(f"⚠️ Falha ao inicializar RAG runtime: {e}. Agentes com knowledge não funcionarão.")

            # Create components directly
            entity_discovery = EntityDiscovery(self.entities_dir)
            message_mapper = MessageMapper()
            self.executor = AgentFrameworkExecutor(entity_discovery, message_mapper)

            # Discover entities from directory
            discovered_entities = await self.executor.discover_entities()
            logger.info(f"Discovered {len(discovered_entities)} entities from directory")

            # Register any pending in-memory entities
            if self._pending_entities:
                discovery = self.executor.entity_discovery
                for entity in self._pending_entities:
                    try:
                        entity_info = await discovery.create_entity_info_from_object(entity, source="in_memory")
                        
                        # FORCE ID preservation for in-memory entities if they have a stable ID
                        # This is critical for dynamic workflows that reference agents by their config ID
                        # if hasattr(entity, "id") and entity.id:
                            # Check if ID looks like a UUID or generated ID (optional safety)
                            # But generally if the user set an ID on the object, we should respect it for in-memory registration
                            # entity_info.id = entity.id
                            
                        discovery.register_entity(entity_info.id, entity_info, entity)
                        logger.info(f"Registered in-memory entity: {entity_info.id}")
                    except Exception as e:
                        logger.error(f"Failed to register in-memory entity: {e}")
                self._pending_entities = None  # Clear after registration

            # Get the final entity count after all registration
            all_entities = self.executor.entity_discovery.list_entities()
            logger.info(f"Total entities available: {len(all_entities)}")

        return self.executor

    async def _ensure_openai_executor(self) -> OpenAIExecutor:
        """Ensure OpenAI executor is initialized.

        Returns:
            OpenAI executor instance

        Raises:
            ValueError: If OpenAI executor cannot be initialized
        """
        if self.openai_executor is None:
            # Initialize local executor first to get conversation_store
            local_executor = await self._ensure_executor()

            # Create OpenAI executor with shared conversation store
            self.openai_executor = OpenAIExecutor(local_executor.conversation_store)

            if self.openai_executor.is_configured:
                logger.info("OpenAI proxy mode available (OPENAI_API_KEY configured)")
            else:
                logger.info("OpenAI proxy mode disabled (OPENAI_API_KEY not set)")

        return self.openai_executor

    async def _cleanup_entities(self) -> None:
        """Cleanup entity resources (close clients, MCP tools, credentials, etc.)."""
        if not self.executor:
            return

        logger.info("Cleaning up entity resources...")
        entities = self.executor.entity_discovery.list_entities()
        closed_count = 0
        mcp_tools_closed = 0
        credentials_closed = 0
        hook_count = 0

        for entity_info in entities:
            entity_id = entity_info.id

            try:
                # Step 1: Execute registered cleanup hooks (NEW)
                cleanup_hooks = self.executor.entity_discovery.get_cleanup_hooks(entity_id)
                for hook in cleanup_hooks:
                    try:
                        if inspect.iscoroutinefunction(hook):
                            await hook()
                        else:
                            hook()
                        hook_count += 1
                        logger.debug(f"✓ Executed cleanup hook for: {entity_id}")
                    except Exception as e:
                        logger.warning(f"⚠ Cleanup hook failed for {entity_id}: {e}")

                # Step 2: Close chat clients and their credentials (EXISTING)
                entity_obj = self.executor.entity_discovery.get_entity_object(entity_id)

                if entity_obj and hasattr(entity_obj, "chat_client"):
                    client = entity_obj.chat_client

                    # Close the chat client itself
                    if hasattr(client, "close") and callable(client.close):
                        if inspect.iscoroutinefunction(client.close):
                            await client.close()
                        else:
                            client.close()
                        closed_count += 1
                        logger.debug(f"Closed client for entity: {entity_info.id}")

                    # Close credentials attached to chat clients (e.g., AzureCliCredential)
                    credential_attrs = ["credential", "async_credential", "_credential", "_async_credential"]
                    for attr in credential_attrs:
                        if hasattr(client, attr):
                            cred = getattr(client, attr)
                            if cred and hasattr(cred, "close") and callable(cred.close):
                                try:
                                    if inspect.iscoroutinefunction(cred.close):
                                        await cred.close()
                                    else:
                                        cred.close()
                                    credentials_closed += 1
                                    logger.debug(f"Closed credential for entity: {entity_info.id}")
                                except Exception as e:
                                    logger.warning(f"Error closing credential for {entity_info.id}: {e}")

                # Close MCP tools (framework tracks them in _local_mcp_tools)
                if entity_obj and hasattr(entity_obj, "_local_mcp_tools"):
                    for mcp_tool in entity_obj._local_mcp_tools:
                        if hasattr(mcp_tool, "close") and callable(mcp_tool.close):
                            try:
                                if inspect.iscoroutinefunction(mcp_tool.close):
                                    await mcp_tool.close()
                                else:
                                    mcp_tool.close()
                                mcp_tools_closed += 1
                                tool_name = getattr(mcp_tool, "name", "unknown")
                                logger.debug(f"Closed MCP tool '{tool_name}' for entity: {entity_info.id}")
                            except Exception as e:
                                logger.warning(f"Error closing MCP tool for {entity_info.id}: {e}")

            except Exception as e:
                logger.warning(f"Error cleaning up entity {entity_id}: {e}")

        if hook_count > 0:
            logger.info(f"✓ Executed {hook_count} cleanup hook(s)")
        if closed_count > 0:
            logger.info(f"✓ Closed {closed_count} entity client(s)")
        if credentials_closed > 0:
            logger.info(f"✓ Closed {credentials_closed} credential(s)")
        if mcp_tools_closed > 0:
            logger.info(f"✓ Closed {mcp_tools_closed} MCP tool(s)")

        # Close OpenAI executor if it exists
        if self.openai_executor:
            try:
                await self.openai_executor.close()
                logger.info("Closed OpenAI executor")
            except Exception as e:
                logger.warning(f"Error closing OpenAI executor: {e}")

    def create_app(self) -> FastAPI:
        """Create the FastAPI application."""

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            # Startup
            logger.info("Starting MAIA Server")
            
            # Inicializar Knowledge Base e RAG Runtime ANTES do executor
            # Isso garante que agentes com knowledge config possam usar o RAG
            rag_config = self._get_or_create_rag_config()
            knowledge_base = self._get_knowledge_base()
            await knowledge_base.sync_with_config(rag_config)
            
            # Agora inicializar os executores (que podem carregar agentes com knowledge)
            await self._ensure_executor()
            await self._ensure_openai_executor()  # Initialize OpenAI executor
            
            yield
            # Shutdown
            logger.info("Shutting down MAIA Server")

            # Cleanup entity resources (e.g., close credentials, clients)
            if self.executor:
                await self._cleanup_entities()

        app = FastAPI(
            title="MAIA Server",
            description="OpenAI-compatible API server for Agent Framework and other AI frameworks",
            version="1.0.0",
            lifespan=lifespan,
        )

        # Add CORS middleware
        # Note: allow_credentials cannot be True when allow_origins is ["*"]
        # For localhost dev with wildcard origins, credentials are disabled
        # For network deployments with specific origins or empty list, credentials can be enabled
        allow_credentials = self.cors_origins != ["*"]

        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.cors_origins,
            allow_credentials=allow_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add authentication middleware using decorator pattern
        # Auth is enabled by presence of DEVUI_AUTH_TOKEN
        auth_token = os.getenv("DEVUI_AUTH_TOKEN", "")
        auth_required = bool(auth_token)

        if auth_required:
            logger.info("Authentication middleware enabled")

            @app.middleware("http")
            async def auth_middleware(request: Request, call_next: Callable[[Request], Awaitable[Any]]) -> Any:
                """Validate Bearer token authentication.

                Skips authentication for health, meta, static UI endpoints, and OPTIONS requests.
                """
                # Skip auth for OPTIONS (CORS preflight) requests
                if request.method == "OPTIONS":
                    return await call_next(request)

                # Skip auth for health checks, meta endpoint, and static files
                if request.url.path in ["/health", "/meta", "/"] or request.url.path.startswith("/assets"):
                    return await call_next(request)

                # Check Authorization header
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    return JSONResponse(
                        status_code=401,
                        content={
                            "error": {
                                "message": (
                                    "Missing or invalid Authorization header. Expected: Authorization: Bearer <token>"
                                ),
                                "type": "authentication_error",
                                "code": "missing_token",
                            }
                        },
                    )

                # Extract and validate token
                token = auth_header.replace("Bearer ", "", 1).strip()
                if not secrets.compare_digest(token, auth_token):
                    return JSONResponse(
                        status_code=401,
                        content={
                            "error": {
                                "message": "Invalid authentication token",
                                "type": "authentication_error",
                                "code": "invalid_token",
                            }
                        },
                    )

                # Token valid, proceed
                return await call_next(request)

        self._register_routes(app)
        self._mount_ui(app)

        return app

    def _register_routes(self, app: FastAPI) -> None:
        """Register API routes."""

        @app.get("/health")
        async def health_check() -> dict[str, Any]:
            """Health check endpoint."""
            executor = await self._ensure_executor()
            # Use list_entities() to avoid re-discovering and re-registering entities
            entities = executor.entity_discovery.list_entities()

            return {"status": "healthy", "entities_count": len(entities), "framework": "agent_framework"}

        @app.get("/meta", response_model=MetaResponse)
        async def get_meta() -> MetaResponse:
            """Get server metadata and configuration."""
            import os

            from . import __version__

            # Ensure executors are initialized to check capabilities
            openai_executor = await self._ensure_openai_executor()

            return MetaResponse(
                ui_mode=self.mode,  # type: ignore[arg-type]
                version=__version__,
                framework="agent_framework",
                runtime="python",  # Python DevUI backend
                capabilities={
                    "tracing": os.getenv("ENABLE_OTEL") == "true",
                    "openai_proxy": openai_executor.is_configured,
                    "deployment": True,  # Deployment feature is available
                },
                auth_required=bool(os.getenv("DEVUI_AUTH_TOKEN")),
            )

        @app.get("/v1/entities", response_model=DiscoveryResponse)
        async def discover_entities() -> DiscoveryResponse:
            """List all registered entities."""
            try:
                executor = await self._ensure_executor()
                # Use list_entities() instead of discover_entities() to get already-registered entities
                entities = executor.entity_discovery.list_entities()
                
                # Filter out hidden entities (e.g. internal templates)
                visible_entities = [e for e in entities if not e.metadata.get("hidden", False)]
                
                return DiscoveryResponse(entities=visible_entities)
            except Exception as e:
                logger.error(f"Error listing entities: {e}")
                raise HTTPException(status_code=500, detail=f"Entity listing failed: {e!s}") from e

        @app.get("/v1/entities/{entity_id}/info", response_model=EntityInfo)
        async def get_entity_info(entity_id: str) -> EntityInfo:
            """Get detailed information about a specific entity (triggers lazy loading)."""
            try:
                executor = await self._ensure_executor()
                entity_info = executor.get_entity_info(entity_id)

                if not entity_info:
                    raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

                # Trigger lazy loading if entity not yet loaded
                # This will import the module and enrich metadata
                # Pass checkpoint_manager to ensure workflows get checkpoint storage injected
                entity_obj = await executor.entity_discovery.load_entity(
                    entity_id, checkpoint_manager=executor.checkpoint_manager
                )

                # Get updated entity info (may have been enriched during load)
                entity_info = executor.get_entity_info(entity_id) or entity_info

                # For workflows, populate additional detailed information
                if entity_info.type == "workflow" and entity_obj:
                    # Entity object already loaded by load_entity() above
                    # Get workflow structure
                    workflow_dump = None
                    source_config = getattr(entity_obj, "_source_config", None)

                    # Prefer the serialized workflow graph from the framework for visualization
                    if hasattr(entity_obj, "to_dict") and callable(getattr(entity_obj, "to_dict", None)):
                        try:
                            workflow_dump = entity_obj.to_dict()  # type: ignore[attr-defined]
                        except Exception:
                            workflow_dump = None
                    elif hasattr(entity_obj, "to_json") and callable(getattr(entity_obj, "to_json", None)):
                        try:
                            raw_dump = entity_obj.to_json()  # type: ignore[attr-defined]
                        except Exception:
                            workflow_dump = None
                        else:
                            if isinstance(raw_dump, (bytes, bytearray)):
                                try:
                                    raw_dump = raw_dump.decode()
                                except Exception:
                                    raw_dump = raw_dump.decode(errors="replace")
                            if isinstance(raw_dump, str):
                                try:
                                    parsed_dump = json.loads(raw_dump)
                                except Exception:
                                    workflow_dump = raw_dump
                                else:
                                    workflow_dump = parsed_dump if isinstance(parsed_dump, dict) else raw_dump
                            else:
                                workflow_dump = raw_dump
                    elif hasattr(entity_obj, "__dict__"):
                        workflow_dump = {k: v for k, v in entity_obj.__dict__.items() if not k.startswith("_")}

                    if workflow_dump and source_config:
                        workflow_dump = self._enrich_workflow_dump(workflow_dump, source_config)
                    elif workflow_dump is None and source_config:
                        workflow_dump = source_config

                    # Get input schema information
                    input_schema = {}
                    input_type_name = "Unknown"
                    start_executor_id = ""

                    try:
                        from ._utils import (
                            extract_executor_message_types,
                            generate_input_schema,
                            select_primary_input_type,
                        )

                        start_executor = entity_obj.get_start_executor()
                    except Exception as e:
                        logger.debug(f"Could not extract input info for workflow {entity_id}: {e}")
                    else:
                        if start_executor:
                            start_executor_id = getattr(start_executor, "executor_id", "") or getattr(
                                start_executor, "id", ""
                            )

                            message_types = extract_executor_message_types(start_executor)
                            input_type = select_primary_input_type(message_types)

                            if input_type:
                                input_type_name = getattr(input_type, "__name__", str(input_type))

                                # Generate schema using comprehensive schema generation
                                input_schema = generate_input_schema(input_type)

                    if not input_schema:
                        input_schema = {"type": "string"}
                        if input_type_name == "Unknown":
                            input_type_name = "string"

                    # Get executor list
                    executor_list = []
                    if hasattr(entity_obj, "executors") and entity_obj.executors:
                        executor_list = [getattr(ex, "executor_id", str(ex)) for ex in entity_obj.executors]

                    # Create copy of entity info and populate workflow-specific fields
                    # Note: DevUI provides runtime checkpoint storage for ALL workflows via conversations
                    update_payload: dict[str, Any] = {
                        "workflow_dump": workflow_dump,
                        "input_schema": input_schema,
                        "input_type_name": input_type_name,
                        "start_executor_id": start_executor_id,
                    }
                    if executor_list:
                        update_payload["executors"] = executor_list
                    return entity_info.model_copy(update=update_payload)

                # For non-workflow entities, return as-is
                return entity_info

            except HTTPException:
                raise
            except ValueError as e:
                # ValueError from load_entity indicates entity not found or invalid
                error_msg = self._format_error(e, "Entity loading")
                raise HTTPException(status_code=404, detail=error_msg) from e
            except Exception as e:
                error_msg = self._format_error(e, "Entity info retrieval")
                raise HTTPException(status_code=500, detail=error_msg) from e

        @app.post("/v1/entities/{entity_id}/reload")
        async def reload_entity(entity_id: str) -> dict[str, Any]:
            """Hot reload entity (clears cache, will reimport on next access).

            This enables hot reload during development - edit entity code, call this endpoint,
            and the next execution will use the updated code without server restart.
            """
            self._require_developer_mode("entity hot reload")
            try:
                executor = await self._ensure_executor()

                # Check if entity exists
                entity_info = executor.get_entity_info(entity_id)
                if not entity_info:
                    raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

                # Invalidate cache
                executor.entity_discovery.invalidate_entity(entity_id)

                return {
                    "success": True,
                    "message": f"Entity '{entity_id}' cache cleared. Will reload on next access.",
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error reloading entity {entity_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to reload entity: {e!s}") from e

        # ============================================================================
        # Deployment Endpoints
        # ============================================================================

        @app.post("/v1/deployments")
        async def create_deployment(config: DeploymentConfig) -> StreamingResponse:
            """Deploy entity to Azure Container Apps with streaming events.

            Returns SSE stream of deployment progress events.
            """
            self._require_developer_mode("deployment")
            try:
                executor = await self._ensure_executor()

                # Validate entity exists and supports deployment
                entity_info = executor.get_entity_info(config.entity_id)
                if not entity_info:
                    raise HTTPException(status_code=404, detail=f"Entity {config.entity_id} not found")

                if not entity_info.deployment_supported:
                    reason = entity_info.deployment_reason or "Deployment not supported for this entity"
                    raise HTTPException(status_code=400, detail=reason)

                # Get entity path from metadata
                from pathlib import Path

                entity_path_str = entity_info.metadata.get("path")
                if not entity_path_str:
                    raise HTTPException(
                        status_code=400,
                        detail="Entity path not found in metadata (in-memory entities cannot be deployed)",
                    )

                entity_path = Path(entity_path_str)

                # Stream deployment events
                async def event_generator() -> AsyncGenerator[str, None]:
                    async for event in self.deployment_manager.deploy(config, entity_path):
                        # Format as SSE
                        import json

                        yield f"data: {json.dumps(event.model_dump())}\n\n"

                return StreamingResponse(event_generator(), media_type="text/event-stream")

            except HTTPException:
                raise
            except Exception as e:
                error_msg = self._format_error(e, "Deployment creation")
                raise HTTPException(status_code=500, detail=error_msg) from e

        @app.get("/v1/deployments")
        async def list_deployments(entity_id: str | None = None) -> list[Deployment]:
            """List all deployments, optionally filtered by entity."""
            self._require_developer_mode("deployment listing")
            try:
                return await self.deployment_manager.list_deployments(entity_id)
            except Exception as e:
                error_msg = self._format_error(e, "Deployment listing")
                raise HTTPException(status_code=500, detail=error_msg) from e

        @app.get("/v1/deployments/{deployment_id}")
        async def get_deployment(deployment_id: str) -> Deployment:
            """Get deployment by ID."""
            self._require_developer_mode("deployment details")
            try:
                deployment = await self.deployment_manager.get_deployment(deployment_id)
                if not deployment:
                    raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
                return deployment
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting deployment: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get deployment: {e!s}") from e

        @app.delete("/v1/deployments/{deployment_id}")
        async def delete_deployment(deployment_id: str) -> dict[str, Any]:
            """Delete deployment from Azure Container Apps."""
            self._require_developer_mode("deployment deletion")
            try:
                await self.deployment_manager.delete_deployment(deployment_id)
                return {"success": True, "message": f"Deployment {deployment_id} deleted successfully"}
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e
            except Exception as e:
                logger.error(f"Error deleting deployment: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to delete deployment: {e!s}") from e

        # Convenience endpoint: deploy specific entity
        @app.post("/v1/entities/{entity_id}/deploy")
        async def deploy_entity(entity_id: str, config: DeploymentConfig) -> StreamingResponse:
            """Convenience endpoint to deploy entity (shortcuts to /v1/deployments)."""
            self._require_developer_mode("deployment")
            # Override entity_id from path parameter
            config.entity_id = entity_id
            return await create_deployment(config)

        # ============================================================================
        # Response/Conversation Endpoints
        # ============================================================================

        @app.post("/v1/responses")
        async def create_response(request: AgentFrameworkRequest, raw_request: Request) -> Any:
            """OpenAI Responses API endpoint - routes to local or OpenAI executor."""
            try:
                # Check if frontend requested OpenAI proxy mode
                proxy_mode = raw_request.headers.get("X-Proxy-Backend")

                if proxy_mode == "openai":
                    # Route to OpenAI executor
                    logger.info("🔀 Routing to OpenAI proxy mode")
                    openai_executor = await self._ensure_openai_executor()

                    if not openai_executor.is_configured:
                        error = OpenAIError.create(
                            "OpenAI proxy mode not configured. Set OPENAI_API_KEY environment variable."
                        )
                        return JSONResponse(status_code=503, content=error.to_dict())

                    # Execute via OpenAI with dedicated streaming method
                    if request.stream:
                        return StreamingResponse(
                            self._stream_openai_execution(openai_executor, request),
                            media_type="text/event-stream",
                            headers={
                                "Cache-Control": "no-cache",
                                "Connection": "keep-alive",
                                "Access-Control-Allow-Origin": "*",
                            },
                        )
                    return await openai_executor.execute_sync(request)

                # Route to local Agent Framework executor (original behavior)
                raw_body = await raw_request.body()
                logger.debug(f"Raw request body: {raw_body.decode()}")
                logger.debug(f"Parsed request: metadata={request.metadata}")

                # Get entity_id from metadata
                entity_id = request.get_entity_id()
                logger.debug(f"Extracted entity_id: {entity_id}")

                if not entity_id:
                    error = OpenAIError.create("Missing entity_id in metadata. Provide metadata.entity_id in request.")
                    return JSONResponse(status_code=400, content=error.to_dict())

                # Get executor and validate entity exists
                executor = await self._ensure_executor()
                try:
                    entity_info = executor.get_entity_info(entity_id)
                    logger.debug(f"Found entity: {entity_info.name} ({entity_info.type})")
                except Exception:
                    error = OpenAIError.create(f"Entity not found: {entity_id}")
                    return JSONResponse(status_code=404, content=error.to_dict())

                # Execute request
                if request.stream:
                    return StreamingResponse(
                        self._stream_execution(executor, request),
                        media_type="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                            "Access-Control-Allow-Origin": "*",
                        },
                    )
                return await executor.execute_sync(request)

            except Exception as e:
                error_msg = self._format_error(e, "Request execution")
                error = OpenAIError.create(error_msg)
                return JSONResponse(status_code=500, content=error.to_dict())

        # ========================================
        # OpenAI Conversations API (Standard)
        # ========================================

        @app.post("/v1/conversations", response_model=None)
        async def create_conversation(raw_request: Request) -> dict[str, Any] | JSONResponse:
            """Create a new conversation - routes to OpenAI or local based on mode."""
            try:
                # Parse request body
                request_data = await raw_request.json()

                # Check if frontend requested OpenAI proxy mode
                proxy_mode = raw_request.headers.get("X-Proxy-Backend")

                if proxy_mode == "openai":
                    # Create conversation in OpenAI
                    openai_executor = await self._ensure_openai_executor()
                    if not openai_executor.is_configured:
                        error = OpenAIError.create(
                            "OpenAI proxy mode not configured. Set OPENAI_API_KEY environment variable.",
                            type="configuration_error",
                            code="openai_not_configured",
                        )
                        return JSONResponse(status_code=503, content=error.to_dict())

                    # Use OpenAI client to create conversation
                    from openai import APIStatusError, AsyncOpenAI, AuthenticationError, PermissionDeniedError

                    client = AsyncOpenAI(
                        api_key=openai_executor.api_key,
                        base_url=openai_executor.base_url,
                    )

                    try:
                        metadata = request_data.get("metadata")
                        logger.debug(f"Creating OpenAI conversation with metadata: {metadata}")
                        conversation = await client.conversations.create(metadata=metadata)
                        logger.info(f"Created OpenAI conversation: {conversation.id}")
                        return conversation.model_dump()
                    except AuthenticationError as e:
                        # 401 - Invalid API key or authentication issue
                        logger.error(f"OpenAI authentication error creating conversation: {e}")
                        error_body = e.body if hasattr(e, "body") else {}
                        error_data = error_body.get("error", {}) if isinstance(error_body, dict) else {}
                        error = OpenAIError.create(
                            message=error_data.get("message", str(e)),
                            type=error_data.get("type", "authentication_error"),
                            code=error_data.get("code", "invalid_api_key"),
                        )
                        return JSONResponse(status_code=401, content=error.to_dict())
                    except PermissionDeniedError as e:
                        # 403 - Permission denied
                        logger.error(f"OpenAI permission denied creating conversation: {e}")
                        error_body = e.body if hasattr(e, "body") else {}
                        error_data = error_body.get("error", {}) if isinstance(error_body, dict) else {}
                        error = OpenAIError.create(
                            message=error_data.get("message", str(e)),
                            type=error_data.get("type", "permission_denied"),
                            code=error_data.get("code", "insufficient_permissions"),
                        )
                        return JSONResponse(status_code=403, content=error.to_dict())
                    except APIStatusError as e:
                        # Other OpenAI API errors (rate limit, etc.)
                        logger.error(f"OpenAI API error creating conversation: {e}")
                        error_body = e.body if hasattr(e, "body") else {}
                        error_data = error_body.get("error", {}) if isinstance(error_body, dict) else {}
                        error = OpenAIError.create(
                            message=error_data.get("message", str(e)),
                            type=error_data.get("type", "api_error"),
                            code=error_data.get("code", "unknown_error"),
                        )
                        return JSONResponse(
                            status_code=e.status_code if hasattr(e, "status_code") else 500, content=error.to_dict()
                        )

                # Local mode - use DevUI conversation store
                metadata = request_data.get("metadata")
                executor = await self._ensure_executor()
                conversation = executor.conversation_store.create_conversation(metadata=metadata)
                return conversation.model_dump()
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error creating conversation: {e}", exc_info=True)
                error = OpenAIError.create(f"Failed to create conversation: {e!s}")
                return JSONResponse(status_code=500, content=error.to_dict())

        @app.get("/v1/conversations")
        async def list_conversations(
            agent_id: str | None = None,
            entity_id: str | None = None,
            type: str | None = None,
        ) -> dict[str, Any]:
            """List conversations, optionally filtered by agent_id, entity_id, and/or type.

            Query Parameters:
            - agent_id: Filter by agent_id (for agent conversations)
            - entity_id: Filter by entity_id (for workflow sessions or other entities)
            - type: Filter by conversation type (e.g., "workflow_session")

            Multiple filters can be combined (AND logic).
            """
            try:
                executor = await self._ensure_executor()

                # Build filter criteria
                filters = {}
                if agent_id:
                    filters["agent_id"] = agent_id
                if entity_id:
                    filters["entity_id"] = entity_id
                if type:
                    filters["type"] = type

                # Apply filters
                conversations = executor.conversation_store.list_conversations_by_metadata(filters)

                return {
                    "object": "list",
                    "data": [conv.model_dump() for conv in conversations],
                    "has_more": False,
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error listing conversations: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to list conversations: {e!s}") from e

        @app.get("/v1/conversations/{conversation_id}")
        async def retrieve_conversation(conversation_id: str) -> dict[str, Any]:
            """Get conversation - OpenAI standard."""
            try:
                executor = await self._ensure_executor()
                conversation = executor.conversation_store.get_conversation(conversation_id)
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                return conversation.model_dump()
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting conversation {conversation_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get conversation: {e!s}") from e

        @app.post("/v1/conversations/{conversation_id}")
        async def update_conversation(conversation_id: str, request_data: dict[str, Any]) -> dict[str, Any]:
            """Update conversation metadata - OpenAI standard."""
            try:
                executor = await self._ensure_executor()
                metadata = request_data.get("metadata", {})
                conversation = executor.conversation_store.update_conversation(conversation_id, metadata=metadata)
                return conversation.model_dump()
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating conversation {conversation_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to update conversation: {e!s}") from e

        @app.delete("/v1/conversations/{conversation_id}")
        async def delete_conversation(conversation_id: str) -> dict[str, Any]:
            """Delete conversation - OpenAI standard."""
            try:
                executor = await self._ensure_executor()
                result = executor.conversation_store.delete_conversation(conversation_id)
                return result.model_dump()
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting conversation {conversation_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {e!s}") from e

        @app.post("/v1/conversations/{conversation_id}/items")
        async def create_conversation_items(conversation_id: str, request_data: dict[str, Any]) -> dict[str, Any]:
            """Add items to conversation - OpenAI standard."""
            try:
                executor = await self._ensure_executor()
                items = request_data.get("items", [])
                conv_items = await executor.conversation_store.add_items(conversation_id, items=items)
                return {"object": "list", "data": [item.model_dump() for item in conv_items]}
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error adding items to conversation {conversation_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to add items: {e!s}") from e

        @app.get("/v1/conversations/{conversation_id}/items")
        async def list_conversation_items(
            conversation_id: str, limit: int = 100, after: str | None = None, order: str = "asc"
        ) -> dict[str, Any]:
            """List conversation items - OpenAI standard."""
            try:
                executor = await self._ensure_executor()
                items, has_more = await executor.conversation_store.list_items(
                    conversation_id, limit=limit, after=after, order=order
                )
                # Handle both Pydantic models and dicts (some stores return raw dicts)
                serialized_items = []
                for item in items:
                    if hasattr(item, "model_dump"):
                        serialized_items.append(item.model_dump())
                    elif isinstance(item, dict):
                        serialized_items.append(item)
                    else:
                        logger.warning(f"Unexpected item type: {type(item)}, converting to dict")
                        serialized_items.append(dict(item))

                return {
                    "object": "list",
                    "data": serialized_items,
                    "has_more": has_more,
                }
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error listing items for conversation {conversation_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to list items: {e!s}") from e

        @app.get("/v1/conversations/{conversation_id}/items/{item_id}")
        async def retrieve_conversation_item(conversation_id: str, item_id: str) -> dict[str, Any]:
            """Get specific conversation item - OpenAI standard."""
            try:
                executor = await self._ensure_executor()
                item = executor.conversation_store.get_item(conversation_id, item_id)
                if not item:
                    raise HTTPException(status_code=404, detail="Item not found")
                result: dict[str, Any] = item.model_dump()
                return result
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting item {item_id} from conversation {conversation_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get item: {e!s}") from e

        @app.delete("/v1/conversations/{conversation_id}/items/{item_id}")
        async def delete_conversation_item(conversation_id: str, item_id: str) -> dict[str, Any]:
            """Delete conversation item - supports checkpoint deletion."""
            try:
                executor = await self._ensure_executor()

                # Check if this is a checkpoint item
                if item_id.startswith("checkpoint_"):
                    # Extract checkpoint_id from item_id (format: "checkpoint_{checkpoint_id}")
                    checkpoint_id = item_id[len("checkpoint_") :]
                    storage = executor.checkpoint_manager.get_checkpoint_storage(conversation_id)
                    deleted = await storage.delete_checkpoint(checkpoint_id)

                    if not deleted:
                        raise HTTPException(status_code=404, detail="Checkpoint not found")

                    return {
                        "id": item_id,
                        "object": "item.deleted",
                        "deleted": True,
                    }
                # For other items, delegate to conversation store (if it supports deletion)
                raise HTTPException(status_code=501, detail="Deletion of non-checkpoint items not implemented")

            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e
            except Exception as e:
                logger.error(f"Error deleting item {item_id} from conversation {conversation_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to delete item: {e!s}") from e

        # ============================================================================
        # Checkpoint Management - Now handled through conversation items API
        # Checkpoints are exposed as conversation items with type="checkpoint"
        # ============================================================================

        # ============================================================================
        # Studio / Debug Endpoints
        # ============================================================================

        @app.post("/v1/debug/save_studio_flow")
        async def save_studio_flow(config: dict[str, Any]) -> dict[str, Any]:
            """Save the studio flow configuration to a test file."""
            self._require_developer_mode("save studio flow")
            try:
                import json
                import time
                import re

                # Create output directory if it doesn't exist
                # Changed from tests/studio_output to exemplos per user request
                output_dir = PROJECT_ROOT / "exemplos"
                output_dir.mkdir(parents=True, exist_ok=True)

                # Generate filename
                name = config.get("name", "")
                if name:
                    # Sanitize name
                    safe_name = re.sub(r'[^\w\-_]', '_', name.lower())
                    filename = f"{safe_name}.json"
                else:
                    timestamp = int(time.time())
                    filename = f"flow_{timestamp}.json"
                
                file_path = output_dir / filename

                # Save to file
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)

                logger.info(f"Saved studio flow to {file_path}")

                return {
                    "success": True,
                    "message": f"Flow saved to {file_path}",
                    "path": str(file_path),
                    "filename": filename
                }

            except Exception as e:
                logger.error(f"Error saving studio flow: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to save flow: {e!s}") from e

        @app.post("/v1/agents")
        async def save_agent(agent: dict[str, Any]) -> dict[str, Any]:
            """Salvar um agente individual na pasta exemplos/agentes/."""
            self._require_developer_mode("save agent")
            try:
                import json
                import re

                output_dir = PROJECT_ROOT / "exemplos" / "agentes"
                output_dir.mkdir(parents=True, exist_ok=True)

                agent_id = agent.get("id", "")
                if agent_id:
                    safe_name = re.sub(r'[^\w\-_]', '_', agent_id.lower())
                    filename = f"{safe_name}.json"
                else:
                    import time
                    filename = f"agent_{int(time.time())}.json"
                
                file_path = output_dir / filename

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(agent, f, indent=2, ensure_ascii=False)

                logger.info(f"Saved agent to {file_path}")

                return {
                    "success": True,
                    "message": f"Agent saved to {file_path}",
                    "path": str(file_path),
                    "filename": filename,
                    "agent": agent
                }

            except Exception as e:
                logger.error(f"Error saving agent: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to save agent: {e!s}") from e

        @app.get("/v1/agents")
        async def list_agents() -> dict[str, Any]:
            """Listar todos os agentes salvos em exemplos/agentes/."""
            try:
                import json

                agents_dir = PROJECT_ROOT / "exemplos" / "agentes"
                agents = []
                
                if agents_dir.exists():
                    for file_path in agents_dir.glob("*.json"):
                        try:
                            with open(file_path, encoding="utf-8") as f:
                                agent = json.load(f)
                                agent["_file"] = file_path.name
                                agents.append(agent)
                        except Exception as e:
                            logger.warning(f"Failed to load agent {file_path}: {e}")

                return {
                    "object": "list",
                    "data": agents,
                    "count": len(agents)
                }

            except Exception as e:
                logger.error(f"Error listing agents: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to list agents: {e!s}") from e

        @app.delete("/v1/agents/{agent_id}")
        async def delete_agent(agent_id: str) -> dict[str, Any]:
            """Deletar um agente pelo ID."""
            self._require_developer_mode("delete agent")
            try:
                import re

                agents_dir = PROJECT_ROOT / "exemplos" / "agentes"
                safe_name = re.sub(r'[^\w\-_]', '_', agent_id.lower())
                file_path = agents_dir / f"{safe_name}.json"

                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted agent {file_path}")
                    return {"success": True, "message": f"Agent {agent_id} deleted"}
                else:
                    raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting agent: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to delete agent: {e!s}") from e

        @app.post("/v1/workflows")
        async def save_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
            """Salvar um workflow na pasta exemplos/workflows/."""
            self._require_developer_mode("save workflow")
            try:
                import json
                import re

                output_dir = PROJECT_ROOT / "exemplos" / "workflows"
                output_dir.mkdir(parents=True, exist_ok=True)

                name = workflow.get("name", "")
                if name:
                    safe_name = re.sub(r'[^\w\-_]', '_', name.lower())
                    filename = f"{safe_name}.json"
                else:
                    import time
                    filename = f"workflow_{int(time.time())}.json"
                
                file_path = output_dir / filename

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(workflow, f, indent=2, ensure_ascii=False)

                logger.info(f"Saved workflow to {file_path}")

                return {
                    "success": True,
                    "message": f"Workflow saved to {file_path}",
                    "path": str(file_path),
                    "filename": filename
                }

            except Exception as e:
                logger.error(f"Error saving workflow: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to save workflow: {e!s}") from e

        @app.get("/v1/workflows")
        async def list_workflows() -> dict[str, Any]:
            """Listar todos os workflows salvos em exemplos/workflows/."""
            try:
                import json

                workflows_dir = PROJECT_ROOT / "exemplos" / "workflows"
                workflows = []
                
                if workflows_dir.exists():
                    for file_path in workflows_dir.glob("*.json"):
                        try:
                            with open(file_path, encoding="utf-8") as f:
                                wf = json.load(f)
                                wf["_file"] = file_path.name
                                workflows.append(wf)
                        except Exception as e:
                            logger.warning(f"Failed to load workflow {file_path}: {e}")

                return {
                    "object": "list",
                    "data": workflows,
                    "count": len(workflows)
                }

            except Exception as e:
                logger.error(f"Error listing workflows: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to list workflows: {e!s}") from e

        @app.delete("/v1/workflows/{filename}")
        async def delete_workflow(filename: str) -> dict[str, Any]:
            """Deletar um workflow da pasta exemplos/workflows/."""
            self._require_developer_mode("delete workflow")
            try:
                workflows_dir = PROJECT_ROOT / "exemplos" / "workflows"
                file_path = workflows_dir / filename

                if not file_path.exists():
                    raise HTTPException(status_code=404, detail=f"Workflow not found: {filename}")

                # Security: ensure the file is inside workflows_dir
                if not file_path.resolve().is_relative_to(workflows_dir.resolve()):
                    raise HTTPException(status_code=400, detail="Invalid filename")

                file_path.unlink()
                logger.info(f"Deleted workflow: {file_path}")

                return {
                    "success": True,
                    "message": f"Workflow {filename} deleted",
                    "filename": filename
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting workflow: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {e!s}") from e

        @app.get("/v1/tools")
        async def list_tools() -> dict[str, Any]:
            """List available tools discovered in the workspace."""
            try:
                from src.worker.discovery import discover_tools
                
                tools = discover_tools()
                return {
                    "object": "list",
                    "data": [tool.model_dump() for tool in tools],
                    "count": len(tools)
                }
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to list tools: {e!s}") from e

        # ============================================================================
        # RAG Configuration Endpoints
        # ============================================================================

        @app.get("/v1/rag")
        async def get_rag_config() -> dict[str, Any]:
            """Get current RAG configuration."""
            config = self._get_or_create_rag_config()
            return config.model_dump()

        @app.post("/v1/rag")
        async def update_rag_config(config: dict[str, Any]) -> dict[str, Any]:
            """Update RAG configuration."""
            try:
                validated_config = RagConfig(**config)
            except ValidationError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            self._persist_rag_config(validated_config)
            knowledge_base = self._get_knowledge_base()
            await knowledge_base.sync_with_config(validated_config)

            logger.info(
                "RAG config updated: enabled=%s provider=%s",
                validated_config.enabled,
                validated_config.provider,
            )
            return validated_config.model_dump()

        # ============================================================================
        # Knowledge Base Endpoints
        # ============================================================================

        @app.get("/v1/knowledge/collections")
        async def list_collections() -> JSONResponse:
            kb = self._get_knowledge_base()
            collections = [json.loads(c.model_dump_json()) for c in kb.list_collections()]
            return JSONResponse(content={"data": collections, "count": len(collections)})

        @app.post("/v1/knowledge/collections")
        async def create_collection(payload: KnowledgeCollectionRequest) -> JSONResponse:
            try:
                kb = self._get_knowledge_base()
                collection = kb.create_collection(
                    name=payload.name,
                    description=payload.description,
                    namespace=payload.namespace,
                    tags=payload.tags,
                )
                # Usar model_dump_json() para serialização correta de datetime
                return JSONResponse(content=json.loads(collection.model_dump_json()))
            except Exception as e:
                logger.error(f"Erro ao criar coleção: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @app.delete("/v1/knowledge/collections/{collection_id}")
        async def delete_collection(collection_id: str) -> dict[str, Any]:
            kb = self._get_knowledge_base()
            try:
                await kb.delete_collection(collection_id)
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return {"success": True}

        @app.get("/v1/knowledge/collections/{collection_id}/documents")
        async def list_documents(collection_id: str) -> dict[str, Any]:
            kb = self._get_knowledge_base()
            try:
                kb.get_collection(collection_id)
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            documents = [doc.model_dump(mode="json") for doc in kb.list_documents(collection_id)]
            return {"data": documents, "count": len(documents)}

        @app.delete("/v1/knowledge/documents/{document_id}")
        async def delete_document(document_id: str) -> dict[str, Any]:
            kb = self._get_knowledge_base()
            try:
                await kb.delete_document(document_id)
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return {"success": True}

        @app.post("/v1/knowledge/collections/{collection_id}/ingest")
        async def ingest_documents(
            collection_id: str,
            files: list[UploadFile] = File(...),
            metadata: str | None = Form(None),
        ) -> dict[str, Any]:
            kb = self._get_knowledge_base()
            if not files:
                raise HTTPException(status_code=400, detail="Envie ao menos um arquivo")

            metadata_payload = self._parse_metadata_payload(metadata)
            try:
                kb.get_collection(collection_id)
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            ingested: list[dict[str, Any]] = []

            for upload in files:
                content = await upload.read()
                try:
                    result = await kb.ingest_file(
                        collection_id=collection_id,
                        filename=upload.filename or "arquivo_sem_nome",
                        content_type=upload.content_type,
                        raw_bytes=content,
                        metadata=metadata_payload,
                    )
                except UnsupportedFileError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
                ingested.append(
                    {
                        "document": result.document.model_dump(mode="json"),
                        "collection": result.collection.model_dump(mode="json"),
                    }
                )

            return {"ingested": ingested, "count": len(ingested)}

        @app.post("/v1/knowledge/search")
        async def search_knowledge(payload: KnowledgeSearchRequest) -> dict[str, Any]:
            kb = self._get_knowledge_base()
            try:
                results = await kb.search(
                    query=payload.query,
                    collection_id=payload.collection_id,
                    top_k=min(max(payload.top_k, 1), 20),
                )
            except ValueError as exc:
                message = str(exc)
                status_code = 404 if "Coleção" in message else 400
                raise HTTPException(status_code=status_code, detail=message) from exc
            return {"data": [result.model_dump(mode="json") for result in results], "count": len(results)}

        @app.post("/v1/tools/{tool_id}/invoke")
        async def invoke_tool(tool_id: str, raw_request: Request) -> dict[str, Any]:
            """Invoke a discovered tool directly (dev-only helper).

            Body: { arguments: <object|array|string> }
            """
            try:
                body = await raw_request.json()
            except Exception:
                body = {}

            args = body.get("arguments")

            candidate_modules = ["mock_tools.basic", "ferramentas.basicas"]

            target_func = None
            func_module = None
            for module_path in candidate_modules:
                try:
                    module = importlib.import_module(module_path)
                except ImportError:
                    continue

                if hasattr(module, tool_id):
                    target_func = getattr(module, tool_id)
                    func_module = module_path
                    break

            if not target_func or not callable(target_func):
                raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found in known modules")

            # Prepare invocation arguments
            try:
                if isinstance(args, str):
                    # Try parse JSON
                    import json as _json

                    try:
                        parsed = _json.loads(args)
                    except Exception:
                        parsed = args
                else:
                    parsed = args

                # Decide if parsed is list -> positional args, dict -> kwargs
                if isinstance(parsed, list):
                    result = target_func(*parsed)
                elif isinstance(parsed, dict):
                    result = target_func(**parsed)
                elif parsed is None:
                    result = target_func()
                else:
                    # single primitive argument
                    result = target_func(parsed)

                # Normalize result for JSON
                try:
                    # If result is not JSON serializable, convert to string
                    import json as _json

                    _json.dumps(result)
                    out = result
                except Exception:
                    out = str(result)

                return {"success": True, "tool": tool_id, "module": func_module, "result": out}

            except TypeError as e:
                logger.error(f"Tool invocation failed (TypeError): {e}")
                raise HTTPException(status_code=400, detail=f"Invalid arguments for tool {tool_id}: {e}") from e
            except Exception as e:
                logger.exception(f"Tool invocation error: {e}")
                raise HTTPException(status_code=500, detail=f"Tool '{tool_id}' execution failed: {e}") from e

        @app.delete("/v1/entities/{entity_id}")
        async def delete_entity(entity_id: str) -> dict[str, str]:
            """Delete an entity."""
            try:
                executor = await self._ensure_executor()
                executor.entity_discovery.delete_entity(entity_id)
                return {"status": "success", "message": f"Entity {entity_id} deleted"}
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e
            except Exception as e:
                logger.error(f"Error deleting entity {entity_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to delete entity: {e!s}") from e

    async def _stream_execution(
        self, executor: AgentFrameworkExecutor, request: AgentFrameworkRequest
    ) -> AsyncGenerator[str, None]:
        """Stream execution directly through executor."""
        try:
            # Collect events for final response.completed event
            events = []

            # Stream all events
            async for event in executor.execute_streaming(request):
                events.append(event)

                # IMPORTANT: Check model_dump_json FIRST because to_json() can have newlines (pretty-printing)
                # which breaks SSE format. model_dump_json() returns single-line JSON.
                if hasattr(event, "model_dump_json"):
                    payload = event.model_dump_json()  # type: ignore[attr-defined]
                elif hasattr(event, "to_json") and callable(getattr(event, "to_json", None)):
                    payload = event.to_json()  # type: ignore[attr-defined]
                    # Strip newlines from pretty-printed JSON for SSE compatibility
                    payload = payload.replace("\n", "").replace("\r", "")
                elif isinstance(event, dict):
                    # Handle plain dict events (e.g., error events from executor)
                    payload = json.dumps(event)
                elif hasattr(event, "to_dict") and callable(getattr(event, "to_dict", None)):
                    payload = json.dumps(event.to_dict())  # type: ignore[attr-defined]
                else:
                    payload = json.dumps(str(event))
                yield f"data: {payload}\n\n"

            # Aggregate to final response and emit response.completed event (OpenAI standard)
            from .models import ResponseCompletedEvent

            final_response = await executor.message_mapper.aggregate_to_response(events, request)
            completed_event = ResponseCompletedEvent(
                type="response.completed",
                response=final_response,
                sequence_number=len(events),
            )
            yield f"data: {completed_event.model_dump_json()}\n\n"

            # Send final done event
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Error in streaming execution: {e}")
            error_event = {"id": "error", "object": "error", "error": {"message": str(e), "type": "execution_error"}}
            yield f"data: {json.dumps(error_event)}\n\n"

    async def _stream_openai_execution(
        self, executor: OpenAIExecutor, request: AgentFrameworkRequest
    ) -> AsyncGenerator[str, None]:
        """Stream execution through OpenAI executor.

        OpenAI events are already in final format - no conversion or aggregation needed.
        Just serialize and stream them as SSE.

        Args:
            executor: OpenAI executor instance
            request: Request to execute

        Yields:
            SSE-formatted event strings
        """
        try:
            # Stream events from OpenAI - they're already ResponseStreamEvent objects
            async for event in executor.execute_streaming(request):
                # Handle error dicts from executor
                if isinstance(event, dict):
                    payload = json.dumps(event)
                    yield f"data: {payload}\n\n"
                    continue

                # OpenAI SDK events have model_dump_json() - use it for single-line JSON
                if hasattr(event, "model_dump_json"):
                    payload = event.model_dump_json()  # type: ignore[attr-defined]
                    yield f"data: {payload}\n\n"
                else:
                    # Fallback (shouldn't happen with OpenAI SDK)
                    logger.warning(f"Unexpected event type from OpenAI: {type(event)}")
                    payload = json.dumps(str(event))
                    yield f"data: {payload}\n\n"

            # OpenAI already sends response.completed event - no aggregation needed!
            # Just send [DONE] marker
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Error in OpenAI streaming execution: {e}", exc_info=True)
            # Emit proper response.failed event
            import os

            error_event = {
                "type": "response.failed",
                "response": {
                    "id": f"resp_{os.urandom(16).hex()}",
                    "status": "failed",
                    "error": {
                        "message": str(e),
                        "type": "internal_error",
                        "code": "streaming_error",
                    },
                },
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    def _mount_ui(self, app: FastAPI) -> None:
        """Mount the UI as static files."""
        from pathlib import Path

        ui_dir = Path(__file__).parent / "ui"
        if ui_dir.exists() and ui_dir.is_dir() and self.ui_enabled:
            app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")

    def register_entities(self, entities: list[Any]) -> None:
        """Register entities to be discovered when server starts.

        Args:
            entities: List of entity objects to register
        """
        if self._pending_entities is None:
            self._pending_entities = []
        self._pending_entities.extend(entities)

    def _get_or_create_rag_config(self) -> RagConfig:
        if self._rag_config is not None:
            return self._rag_config

        if self._rag_config_path.exists():
            try:
                payload = json.loads(self._rag_config_path.read_text(encoding="utf-8"))
                self._rag_config = RagConfig(**payload)
            except Exception as exc:  # pragma: no cover - fallback defensivo
                logger.warning("Falha ao carregar rag_config, usando padrão: %s", exc)
                self._rag_config = self._create_default_rag_config()
        else:
            self._rag_config = self._create_default_rag_config()
            self._persist_rag_config(self._rag_config)
        return self._rag_config

    def _create_default_rag_config(self) -> RagConfig:
        """Cria configuração RAG padrão usando variáveis de ambiente."""
        import os
        from src.worker.config import RagEmbeddingConfig
        
        # Detecta modelo de embedding do .env
        embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        
        if embedding_model:
            embedding_config = RagEmbeddingConfig(model=embedding_model)
            logger.info(f"RAG configurado com modelo de embedding: {embedding_model}")
            return RagConfig(
                enabled=True,
                embedding=embedding_config,
            )
        else:
            logger.warning("Base de conhecimento desativada - configuração de embedding ausente")
            return RagConfig(enabled=False)

    def _persist_rag_config(self, config: RagConfig) -> None:
        self._rag_config = config
        payload = config.model_dump()
        self._rag_config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _get_cached_rag_config(self) -> RagConfig | None:
        return self._rag_config

    def _get_knowledge_base(self) -> KnowledgeBaseService:
        if self._knowledge_base is None:
            rag_config = self._get_or_create_rag_config()
            self._knowledge_base = KnowledgeBaseService(
                root_dir=self._knowledge_root,
                rag_config_getter=self._get_cached_rag_config,
            )
            # Registrar o VectorStore para uso pelo RAG
            register_vector_store(self._knowledge_base.get_vector_store())
            # Configurar o RAG runtime para que agentes possam usar create_agent_context_provider
            configure_rag_runtime_from_config(rag_config)
            logger.info("Knowledge Base e RAG runtime inicializados")
        return self._knowledge_base

    @staticmethod
    def _parse_metadata_payload(metadata_raw: str | None) -> dict[str, Any]:
        if not metadata_raw:
            return {}
        try:
            payload = json.loads(metadata_raw)
        except json.JSONDecodeError as exc:  # pragma: no cover - validação simples
            raise HTTPException(status_code=400, detail=f"Metadados inválidos: {exc}") from exc
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Metadados devem ser um objeto JSON")
        return payload

    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        if self._app is None:
            self._app = self.create_app()
        return self._app
