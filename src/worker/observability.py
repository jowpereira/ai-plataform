"""
Observability module for the Worker.

This module handles OpenTelemetry configuration and provides an adapter
to bridge the internal EventBus with OpenTelemetry spans and metrics.
"""

import logging
import os
import atexit
from typing import Dict, Optional, Any
from contextlib import contextmanager

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.trace import Status, StatusCode

# Import from agent_framework for compliance
try:
    from agent_framework.observability import setup_observability as af_setup_observability
    from agent_framework.observability import OBSERVABILITY_SETTINGS
    HAS_AGENT_FRAMEWORK_OBSERVABILITY = True
except ImportError:
    HAS_AGENT_FRAMEWORK_OBSERVABILITY = False

# Flag to track if Agent Framework observability is actually active
USING_AGENT_FRAMEWORK_OBSERVABILITY = False

from src.worker.interfaces import WorkerEvent, WorkerEventType, EventBus

logger = logging.getLogger(__name__)

class OpenTelemetryAdapter:
    """
    Adapts Worker events to OpenTelemetry spans and metrics.
    """

    def __init__(self, event_bus: EventBus, tracer_name: str = "ai-platform-worker"):
        self.event_bus = event_bus
        self.tracer = trace.get_tracer(tracer_name)
        self.meter = metrics.get_meter(tracer_name)
        
        # Active spans map: execution_id -> { span_key -> Span }
        self._active_spans: Dict[str, Dict[str, trace.Span]] = {}
        
        # Metrics
        self.workflow_counter = self.meter.create_counter(
            "workflow_runs", description="Number of workflow runs"
        )
        self.agent_counter = self.meter.create_counter(
            "agent_runs", description="Number of agent runs"
        )
        self.tool_counter = self.meter.create_counter(
            "tool_calls", description="Number of tool calls"
        )
        self.error_counter = self.meter.create_counter(
            "errors", description="Number of errors"
        )

        # Subscribe to all events
        self.event_bus.subscribe("*", self._handle_event)

    def _get_execution_id(self, event: WorkerEvent) -> str:
        return str(event.metadata.get("execution_id", "default"))

    def _get_spans(self, execution_id: str) -> Dict[str, trace.Span]:
        if execution_id not in self._active_spans:
            self._active_spans[execution_id] = {}
        return self._active_spans[execution_id]

    def _handle_event(self, event: WorkerEvent) -> None:
        """Dispatch event to appropriate handler."""
        try:
            if event.type == WorkerEventType.WORKFLOW_START:
                self._start_workflow_span(event)
            elif event.type == WorkerEventType.WORKFLOW_COMPLETE:
                self._end_workflow_span(event, status=StatusCode.OK)
            elif event.type == WorkerEventType.WORKFLOW_ERROR:
                self._end_workflow_span(event, status=StatusCode.ERROR)
            
            elif event.type in (WorkerEventType.AGENT_START, WorkerEventType.AGENT_RUN_START):
                self._start_agent_span(event)
            elif event.type in (WorkerEventType.AGENT_RESPONSE, WorkerEventType.AGENT_RUN_COMPLETE):
                self._end_agent_span(event)
            
            elif event.type == WorkerEventType.TOOL_CALL_START:
                self._start_tool_span(event)
            elif event.type == WorkerEventType.TOOL_CALL_COMPLETE:
                self._end_tool_span(event, status=StatusCode.OK)
            elif event.type == WorkerEventType.TOOL_CALL_ERROR:
                self._end_tool_span(event, status=StatusCode.ERROR)

            elif event.type == WorkerEventType.LLM_REQUEST_START:
                self._start_llm_span(event)
            elif event.type == WorkerEventType.LLM_REQUEST_COMPLETE:
                self._end_llm_span(event, status=StatusCode.OK)
            elif event.type == WorkerEventType.LLM_REQUEST_ERROR:
                self._end_llm_span(event, status=StatusCode.ERROR)

            elif event.type == WorkerEventType.PROMPT_RENDER_START:
                self._start_render_span(event)
            elif event.type == WorkerEventType.PROMPT_RENDER_COMPLETE:
                self._end_render_span(event)
                
            # Add event to current span for other types
            else:
                self._add_event_to_current_span(event)
                
        except Exception as e:
            logger.error(f"Error handling telemetry event: {e}")

    def _start_workflow_span(self, event: WorkerEvent):
        """Start a root span for the workflow."""
        execution_id = self._get_execution_id(event)
        spans = self._get_spans(execution_id)
        
        span = self.tracer.start_span(
            name=f"workflow_{event.data.get('workflow_type', 'unknown')}",
            attributes={
                "workflow.input": str(event.data.get("input", ""))[:100],
                "workflow.id": execution_id,
            }
        )
        spans["workflow"] = span
        self.workflow_counter.add(1)

    def _end_workflow_span(self, event: WorkerEvent, status: StatusCode):
        """End the workflow span."""
        execution_id = self._get_execution_id(event)
        spans = self._get_spans(execution_id)
        
        span = spans.pop("workflow", None)
        if span:
            if status == StatusCode.ERROR:
                span.record_exception(Exception(event.data.get("error", "Unknown error")))
                span.set_status(Status(status))
                self.error_counter.add(1, {"type": "workflow"})
            else:
                span.set_status(Status(status))
                span.set_attribute("workflow.result", str(event.data.get("result", ""))[:200])
            
            span.end()
        
        # Clean up execution context if empty
        if not spans:
            self._active_spans.pop(execution_id, None)

    def _start_agent_span(self, event: WorkerEvent):
        """Start a span for an agent execution."""
        # If Agent Framework is handling observability, it traces agents automatically.
        if USING_AGENT_FRAMEWORK_OBSERVABILITY:
            return

        execution_id = self._get_execution_id(event)
        spans = self._get_spans(execution_id)
        
        parent_span = spans.get("workflow")
        context = trace.set_span_in_context(parent_span) if parent_span else None
        
        agent_name = event.data.get("agent_name", "unknown")
        span = self.tracer.start_span(
            name=f"agent_{agent_name}",
            context=context,
            attributes={
                "agent.name": agent_name,
                "agent.role": event.data.get("agent_role", ""),
            }
        )
        spans[f"agent_{agent_name}"] = span
        self.agent_counter.add(1, {"agent": agent_name})

    def _end_agent_span(self, event: WorkerEvent):
        """End the agent span."""
        if USING_AGENT_FRAMEWORK_OBSERVABILITY:
            return

        execution_id = self._get_execution_id(event)
        spans = self._get_spans(execution_id)
        
        agent_name = event.data.get("agent_name", "unknown")
        span = spans.pop(f"agent_{agent_name}", None)
        if span:
            span.set_attribute("agent.response", str(event.data.get("content", ""))[:200])
            span.end()

    def _start_tool_span(self, event: WorkerEvent):
        """Start a span for a tool call."""
        # If Agent Framework is handling observability, it likely traces tool calls automatically.
        # We skip manual tool tracing to avoid duplicate spans.
        if USING_AGENT_FRAMEWORK_OBSERVABILITY:
            return

        execution_id = self._get_execution_id(event)
        spans = self._get_spans(execution_id)
        
        # Try to find parent agent span, otherwise workflow span
        agent_name = event.data.get("agent", None)
        parent_span = spans.get(f"agent_{agent_name}") if agent_name else spans.get("workflow")
        context = trace.set_span_in_context(parent_span) if parent_span else None
        
        tool_name = event.data.get("tool", "unknown")
        span = self.tracer.start_span(
            name=f"tool_{tool_name}",
            context=context,
            attributes={
                "tool.name": tool_name,
                "tool.arguments": str(event.data.get("arguments", ""))[:500],
            }
        )
        # Use a unique key for tool calls if possible, or a stack
        # For simplicity, assuming sequential tool calls per agent or unique tool names
        # A better approach would be to use an ID in the event
        spans[f"tool_{tool_name}"] = span
        self.tool_counter.add(1, {"tool": tool_name})

    def _end_tool_span(self, event: WorkerEvent, status: StatusCode = StatusCode.OK):
        """End the tool span."""
        if USING_AGENT_FRAMEWORK_OBSERVABILITY:
            return

        execution_id = self._get_execution_id(event)
        spans = self._get_spans(execution_id)
        
        tool_name = event.data.get("tool", "unknown")
        span = spans.pop(f"tool_{tool_name}", None)
        if span:
            if status == StatusCode.ERROR:
                span.record_exception(Exception(event.data.get("error", "Unknown error")))
                span.set_status(Status(status))
                self.error_counter.add(1, {"type": "tool", "tool": tool_name})
            else:
                span.set_status(Status(status))
                span.set_attribute("tool.result", str(event.data.get("result", ""))[:200])
            span.end()

    def _start_llm_span(self, event: WorkerEvent):
        """Start a span for an LLM request."""
        if USING_AGENT_FRAMEWORK_OBSERVABILITY:
            return

        execution_id = self._get_execution_id(event)
        spans = self._get_spans(execution_id)
        
        # Parent is usually the agent
        agent_name = event.metadata.get("agent_name")
        parent_span = spans.get(f"agent_{agent_name}") if agent_name else spans.get("workflow")
        context = trace.set_span_in_context(parent_span) if parent_span else None
        
        model = event.data.get("model_config", {}).get("deployment") or event.data.get("model_config", {}).get("type", "unknown")
        
        span = self.tracer.start_span(
            name=f"llm_request_{model}",
            context=context,
            attributes={
                "llm.model": model,
                "llm.provider": event.data.get("model_config", {}).get("type", "unknown"),
            }
        )
        spans["llm_request"] = span

    def _end_llm_span(self, event: WorkerEvent, status: StatusCode = StatusCode.OK):
        """End the LLM request span."""
        if USING_AGENT_FRAMEWORK_OBSERVABILITY:
            return

        execution_id = self._get_execution_id(event)
        spans = self._get_spans(execution_id)
        
        span = spans.pop("llm_request", None)
        if span:
            if status == StatusCode.ERROR:
                span.record_exception(Exception(event.data.get("error", "Unknown error")))
                span.set_status(Status(status))
                self.error_counter.add(1, {"type": "llm"})
            else:
                span.set_status(Status(status))
                # Record token usage if available
                usage = event.data.get("usage", {})
                if usage:
                    span.set_attribute("llm.usage.prompt_tokens", usage.get("prompt_tokens", 0))
                    span.set_attribute("llm.usage.completion_tokens", usage.get("completion_tokens", 0))
                    span.set_attribute("llm.usage.total_tokens", usage.get("total_tokens", 0))
            span.end()

    def _start_render_span(self, event: WorkerEvent):
        """Start a span for prompt rendering."""
        if USING_AGENT_FRAMEWORK_OBSERVABILITY:
            return

        execution_id = self._get_execution_id(event)
        spans = self._get_spans(execution_id)
        
        agent_name = event.metadata.get("agent_name")
        parent_span = spans.get(f"agent_{agent_name}") if agent_name else spans.get("workflow")
        context = trace.set_span_in_context(parent_span) if parent_span else None
        
        span = self.tracer.start_span(
            name="prompt_render",
            context=context,
            attributes={
                "render.template": event.data.get("template_name", "unknown")
            }
        )
        spans["prompt_render"] = span

    def _end_render_span(self, event: WorkerEvent):
        """End the prompt render span."""
        if USING_AGENT_FRAMEWORK_OBSERVABILITY:
            return

        execution_id = self._get_execution_id(event)
        spans = self._get_spans(execution_id)
        
        span = spans.pop("prompt_render", None)
        if span:
            span.set_status(Status(StatusCode.OK))
            span.end()

    def _add_event_to_current_span(self, event: WorkerEvent):
        """Add a log event to the current active span."""
        execution_id = self._get_execution_id(event)
        spans = self._get_spans(execution_id)
        
        # Find the most specific active span
        # This is a heuristic; ideally we'd track context more strictly
        span = None
        if spans:
            # Get the last added span (assuming dict preserves insertion order in Python 3.7+)
            span = list(spans.values())[-1]
        
        if span:
            span.add_event(
                name=event.type.value,
                attributes={
                    "data": str(event.data)[:500],
                    "timestamp": event.timestamp
                }
            )

def configure_observability(
    service_name: str = "ai-platform-worker",
    version: str = "0.0.1",
    endpoint: Optional[str] = None,
    insecure: bool = True
):
    """
    Configures OpenTelemetry SDK.
    """
    # If Agent Framework observability is available, use it for compliance
    if HAS_AGENT_FRAMEWORK_OBSERVABILITY:
        global USING_AGENT_FRAMEWORK_OBSERVABILITY
        try:
            # Check if already configured
            if OBSERVABILITY_SETTINGS._executed_setup:
                logger.info("Agent Framework observability already configured")
                USING_AGENT_FRAMEWORK_OBSERVABILITY = True
                return

            # Set up resource first if needed (Agent Framework might do this internally)
            # But we want to ensure service name is correct
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: service_name,
                ResourceAttributes.SERVICE_VERSION: version,
            })
            
            # Check if provider exists
            current_provider = trace.get_tracer_provider()
            if not isinstance(current_provider, TracerProvider):
                provider = TracerProvider(resource=resource)
                trace.set_tracer_provider(provider)
            
            # Use Agent Framework setup
            otlp_endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            af_setup_observability(enable_sensitive_data=True, otlp_endpoint=otlp_endpoint)
            USING_AGENT_FRAMEWORK_OBSERVABILITY = True
            logger.info(f"Agent Framework observability configured for {service_name}")
            return
        except Exception as e:
            logger.warning(f"Failed to use Agent Framework observability: {e}. Falling back to manual setup.")
            USING_AGENT_FRAMEWORK_OBSERVABILITY = False

    # Fallback to manual setup
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: version,
    })

    # Trace Provider
    current_provider = trace.get_tracer_provider()
    if isinstance(current_provider, TracerProvider):
        logger.info("TracerProvider already configured, using existing one")
        provider = current_provider
    else:
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
    
    # Exporters
    otlp_endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=insecure)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Always add console exporter for dev/debug if env var set
    if os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true":
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Metrics Provider
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint, insecure=insecure) if otlp_endpoint else ConsoleMetricExporter()
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    logger.info(f"Observability configured for {service_name} (Manual)")

_adapter: Optional[OpenTelemetryAdapter] = None

def setup_observability(
    service_name: str = "ai-platform-worker",
    version: str = "0.0.1",
    endpoint: Optional[str] = None,
    insecure: bool = True,
    event_bus: Optional[EventBus] = None
) -> None:
    """
    Sets up OpenTelemetry and the EventBus adapter.
    Idempotent: will only setup once.
    """
    global _adapter
    
    if _adapter is not None:
        return

    # Configure SDK
    configure_observability(service_name, version, endpoint, insecure)
    
    # Create adapter
    if event_bus is None:
        from src.worker.events import get_event_bus
        event_bus = get_event_bus()
        
    _adapter = OpenTelemetryAdapter(event_bus)
    logger.info("OpenTelemetry adapter initialized and subscribed to EventBus")

def shutdown_observability() -> None:
    """
    Shuts down OpenTelemetry providers to ensure clean exit.
    This is crucial to stop background threads like PeriodicExportingMetricReader.
    """
    global _adapter
    
    if _adapter is None:
        return

    logger.info("Shutting down observability...")
    
    try:
        # Shutdown TracerProvider
        tracer_provider = trace.get_tracer_provider()
        if hasattr(tracer_provider, "shutdown"):
            tracer_provider.shutdown()
            
        # Shutdown MeterProvider
        meter_provider = metrics.get_meter_provider()
        if hasattr(meter_provider, "shutdown"):
            meter_provider.shutdown()
            
        # Shutdown LoggerProvider (if configured)
        # Note: opentelemetry._logs is internal/experimental in some versions
        try:
            from opentelemetry._logs import get_logger_provider
            logger_provider = get_logger_provider()
            if hasattr(logger_provider, "shutdown"):
                logger_provider.shutdown()
        except ImportError:
            pass
            
        _adapter = None
        logger.info("Observability shutdown complete")
        
    except Exception as e:
        logger.warning(f"Error shutting down observability: {e}")

atexit.register(shutdown_observability)
