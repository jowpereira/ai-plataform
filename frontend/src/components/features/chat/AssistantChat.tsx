import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, Wrench, CheckCircle2, Clock3 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { apiClient } from "@/services/api";
import type {
  ExtendedResponseStreamEvent,
  ResponseErrorEvent,
  ResponseFailedEvent,
  ResponseFunctionCallArgumentsDelta,
  ResponseFunctionCallComplete,
  ResponseFunctionCallDelta,
  ResponseFunctionResultComplete,
  ResponseFunctionToolCall,
  ResponseOutputItemAddedEvent,
  ResponseTextDeltaEvent,
} from "@/types/openai";

type MessageRole = "user" | "assistant" | "system" | "tool";

type MessageKind = "text" | "function_call" | "function_result";

interface Message {
  id: string;
  role: MessageRole;
  content: string;
  kind?: MessageKind;
  functionCall?: {
    name: string;
    arguments: string;
    status: "in_progress" | "completed";
    callId?: string;
  };
  metadata?: Record<string, any>;
}

interface AssistantChatProps {
  entityId: string;
}

const createMessageId = (): string => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `msg_${Date.now()}_${Math.random().toString(16).slice(2)}`;
};

const safeFormatJson = (value: string): string => {
  if (!value) {
    return "";
  }
  try {
    const parsed = JSON.parse(value);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return value;
  }
};

const FunctionCallCard = ({ message }: { message: Message }) => {
  if (!message.functionCall) {
    return null;
  }

  const statusLabel =
    message.functionCall.status === "completed" ? "Concluída" : "Em andamento";
  const statusIcon =
    message.functionCall.status === "completed" ? (
      <CheckCircle2 className="h-3 w-3 text-emerald-500" />
    ) : (
      <Clock3 className="h-3 w-3 text-amber-500 animate-pulse" />
    );

  return (
    <div className="space-y-3 rounded-lg border border-border/70 bg-background/70 p-3 text-xs">
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2">
          <Wrench className="h-4 w-4 text-primary" />
          <div className="font-semibold text-sm">{message.functionCall.name}</div>
        </div>
        {message.functionCall.callId && (
          <span className="rounded bg-muted px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
            #{message.functionCall.callId}
          </span>
        )}
        <div className="ml-auto flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
          {statusIcon}
          {statusLabel}
        </div>
      </div>
      <div className="space-y-1">
        <p className="text-[10px] font-semibold uppercase text-muted-foreground">Argumentos</p>
        {safeFormatJson(message.functionCall.arguments) ? (
          <pre className="max-h-64 overflow-auto rounded border border-border/40 bg-muted/40 p-2 font-mono text-[11px] leading-relaxed">
            {safeFormatJson(message.functionCall.arguments)}
          </pre>
        ) : (
          <p className="text-[11px] text-muted-foreground">Aguardando argumentos...</p>
        )}

        {/* Small helper actions */}
        <div className="flex items-center justify-between pt-2">
          <div className="text-[11px] text-muted-foreground">Status: {statusLabel}</div>
          {message.functionCall.callId && (
            <div className="flex items-center gap-2">
              <span className="rounded bg-muted px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                #{message.functionCall.callId}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ToolResultCard = ({
  message,
  onRetry,
  onUse,
}: {
  message: Message;
  onRetry?: (callId?: string, toolName?: string) => Promise<void> | void;
  onUse?: (content?: string) => void;
}) => {
  const [expanded, setExpanded] = useState(false);
  const formatted = safeFormatJson(message.content);
  const status = message.metadata?.status || "in_progress";
  const statusColor = status === "completed" ? "text-emerald-500" : "text-amber-500";

  // Provide a short preview for long results (first 3 lines)
  const preview = formatted ? formatted.split("\n").slice(0, 3).join("\n") : "";
  const isLong = formatted.split("\n").length > 3;

  const createdAt = message.metadata?.createdAt ? new Date(message.metadata.createdAt) : null;
  const startedAt = message.metadata?.startedAt ? new Date(message.metadata.startedAt) : null;
  const durationMs = message.metadata?.durationMs ?? (startedAt && createdAt ? createdAt.getTime() - startedAt.getTime() : undefined);

  return (
    <div className="space-y-2 rounded-lg border border-primary/30 bg-primary/5 p-3 text-xs">
      <div className="flex items-start gap-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        <CheckCircle2 className={`h-3 w-3 ${statusColor}`} />
        <div className="flex flex-col">
          <div>Resultado da ferramenta</div>
          <div className="text-[11px] text-muted-foreground font-normal mt-0.5">
            {message.metadata?.callId && <span className="mr-2">#{message.metadata.callId}</span>}
            {createdAt && <span>{createdAt.toLocaleTimeString()}</span>}
            {startedAt && (
              <span className="mx-2">• Iniciado {startedAt.toLocaleTimeString()}</span>
            )}
            {typeof durationMs === "number" && (
              <span className="ml-2 text-xs text-muted-foreground">{Math.round(durationMs)} ms</span>
            )}
          </div>
        </div>
        <div className="ml-auto text-[11px] text-muted-foreground">{status}</div>
      </div>

      <div>
        {expanded ? (
          <pre className="max-h-72 overflow-auto rounded border border-border/40 bg-background/70 p-2 font-mono text-[11px] leading-relaxed">
            {formatted}
          </pre>
        ) : (
          <pre className="max-h-32 overflow-hidden rounded border border-border/40 bg-background/70 p-2 font-mono text-[11px] leading-relaxed">
            {preview || "(Sem conteúdo)"}
          </pre>
        )}

        {isLong && (
          <div className="flex justify-end pt-1">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setExpanded((s) => !s)}
              className="text-[11px]"
            >
              {expanded ? "Mostrar menos" : "Mostrar mais"}
            </Button>
          </div>
        )}

        <div className="flex gap-2 justify-end pt-2">
          {onRetry && message.metadata?.toolName && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onRetry(message.metadata?.callId, message.metadata?.toolName)}
              className="text-[11px]"
            >
              Executar novamente
            </Button>
          )}

          {onUse && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => onUse(message.content)}
              className="text-[11px]"
            >
              Usar resultado como resposta
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export function AssistantChat({ entityId }: AssistantChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: createMessageId(),
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const baseUrl = apiClient.getBaseUrl();
      const token = apiClient.getAuthToken();
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const history = [...messages, userMessage]
        .filter((m) => m.kind !== "function_call" && m.role !== "tool")
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));

      const response = await fetch(`${baseUrl}/v1/responses`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          input: history,
          metadata: {
            entity_id: entityId,
          },
          stream: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const assistantMessageId = createMessageId();
      setMessages((prev) => [
        ...prev,
        { id: assistantMessageId, role: "assistant", content: "", kind: "text" },
      ]);

      const functionCallMessages = new Map<string, { messageId: string; name?: string; startAt?: string }>();
      // Map to track tool-result messages so we can update instead of duplicating
      const toolResultMessages = new Map<string, { messageId: string }>();
      let assistantBuffer = "";
      let streamClosed = false;

      const appendAssistantText = (delta?: string) => {
        if (!delta) return;
        assistantBuffer += delta;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: assistantBuffer }
              : msg
          )
        );
      };

      const ensureFunctionCallMessage = (callId: string, name?: string) => {
        if (!callId) return;
        const current = functionCallMessages.get(callId);
        if (current) {
          if (name) {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === current.messageId && msg.functionCall
                  ? {
                      ...msg,
                      functionCall: {
                        ...msg.functionCall,
                        name,
                      },
                    }
                  : msg
              )
            );
          }
          return current.messageId;
        }

        const messageId = createMessageId();
        const functionName = name || "Função";
        const startAt = new Date().toISOString();
        functionCallMessages.set(callId, { messageId, name: functionName, startAt });
        setMessages((prev) => [
          ...prev,
          {
            id: messageId,
            role: "assistant",
            content: "",
            kind: "function_call",
            functionCall: {
              name: functionName,
              arguments: "",
              status: "in_progress",
              callId,
            },
          },
        ]);
        return messageId;
      };

      const updateFunctionCallArguments = (callId: string, delta?: string) => {
        if (!callId || !delta) return;
        const entry = functionCallMessages.get(callId);
        if (!entry) {
          ensureFunctionCallMessage(callId);
          updateFunctionCallArguments(callId, delta);
          return;
        }
        setMessages((prev) =>
          prev.map((msg) => {
            if (msg.id !== entry.messageId || !msg.functionCall) {
              return msg;
            }
            const existingArgs = msg.functionCall.arguments || "";
            if (!existingArgs && delta === "{}") {
              return msg;
            }
            return {
              ...msg,
              functionCall: {
                ...msg.functionCall,
                arguments: `${existingArgs}${delta}`,
              },
            };
          })
        );
      };

      const finalizeFunctionCall = (callId: string) => {
        const entry = functionCallMessages.get(callId);
        if (!entry) return;
        setMessages((prev) =>
          prev.map((msg) => {
            if (msg.id !== entry.messageId || !msg.functionCall) {
              return msg;
            }
            return {
              ...msg,
              functionCall: {
                ...msg.functionCall,
                status: "completed",
                // Attach timestamps when available
                ...(entry.startAt ? { startedAt: entry.startAt, finishedAt: new Date().toISOString() } : {}),
              },
            };
          })
        );
      };

      const handleFunctionResult = (event: ResponseFunctionResultComplete) => {
        const output = event.output ?? "";
        if (event.call_id) {
          finalizeFunctionCall(event.call_id);
        }

        // If we already added a tool result for this call, update it instead of duplicating
        if (event.call_id && toolResultMessages.has(event.call_id)) {
          const entry = toolResultMessages.get(event.call_id)!;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === entry.messageId
                ? {
                    ...msg,
                    content: output,
                    metadata: { ...msg.metadata, status: event.status, updatedAt: new Date().toISOString() },
                  }
                : msg
            )
          );

          return;
        }

        // Otherwise append a new tool-result message and remember it so future results update the same card
        const newId = createMessageId();
        if (event.call_id) {
          toolResultMessages.set(event.call_id, { messageId: newId });
        }

        // Copy toolName and start timestamps if we know them
        const callMeta = event.call_id ? functionCallMessages.get(event.call_id) : undefined;
        const toolName = callMeta?.name;
        const startedAt = callMeta?.startAt;
        const createdAt = new Date().toISOString();
        const durationMs = startedAt ? new Date(createdAt).getTime() - new Date(startedAt).getTime() : undefined;

        setMessages((prev) => [
          ...prev,
          {
            id: newId,
            role: "tool",
            content: output,
            kind: "function_result",
            metadata: {
              callId: event.call_id,
              status: event.status,
              toolName: toolName,
              startedAt: startedAt,
              createdAt: createdAt,
              durationMs: durationMs,
            },
          },
        ]);
      };

      const handleOutputItemAdded = (event: ResponseOutputItemAddedEvent) => {
        const item = event.item as ResponseFunctionToolCall & { content?: Array<{ text?: string }>; text?: string };
        if (!item) return;

        if (item.type === "function_call") {
          ensureFunctionCallMessage(item.call_id, item.name);
          if (item.arguments) {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.functionCall?.callId === item.call_id
                  ? {
                      ...msg,
                      functionCall: {
                        ...msg.functionCall,
                        arguments: item.arguments,
                      },
                    }
                  : msg
              )
            );
          }
          return;
        }

        if (Array.isArray(item.content)) {
          const text = item.content.map((part) => part?.text ?? "").join("");
          appendAssistantText(text);
          return;
        }

        if (typeof (item as any).text === "string") {
          appendAssistantText((item as any).text as string);
        }
      };

      const handleStreamEvent = (rawEvent: ExtendedResponseStreamEvent | any) => {
        if (rawEvent?.choices?.[0]?.delta?.content) {
          appendAssistantText(rawEvent.choices[0].delta.content as string);
          return;
        }

        const event = rawEvent as ExtendedResponseStreamEvent;
        switch (event.type) {
          case "response.output_text.delta":
          case "response.text.delta": {
            const deltaEvent = event as ResponseTextDeltaEvent;
            appendAssistantText(deltaEvent.delta);
            break;
          }
          case "response.output_item.added":
            handleOutputItemAdded(event as ResponseOutputItemAddedEvent);
            break;
          case "response.function_call.delta": {
            const data = (event as ResponseFunctionCallDelta).data;
            if (data?.call_id) {
              ensureFunctionCallMessage(data.call_id, data.name);
            }
            break;
          }
          case "response.function_call_arguments.delta": {
            const fnEvent = event as ResponseFunctionCallArgumentsDelta;
            const callId = fnEvent.data?.call_id || fnEvent.item_id || "";
            updateFunctionCallArguments(callId, fnEvent.delta);
            break;
          }
          case "response.function_call.complete": {
            const data = (event as ResponseFunctionCallComplete).data;
            if (data?.call_id) {
              ensureFunctionCallMessage(data.call_id, data.name);
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.functionCall?.callId === data.call_id
                    ? {
                        ...msg,
                        functionCall: {
                          ...msg.functionCall,
                          arguments:
                            typeof data.arguments === "string"
                              ? data.arguments
                              : JSON.stringify(data.arguments),
                        },
                      }
                    : msg
                )
              );
              finalizeFunctionCall(data.call_id);
            }
            break;
          }
          case "response.function_result.complete":
            handleFunctionResult(event as ResponseFunctionResultComplete);
            break;
          case "response.failed": {
            const failedEvent = event as ResponseFailedEvent;
            const errorMessage =
              (failedEvent.response?.error as { message?: string } | undefined)?.message ||
              "Falha ao gerar resposta.";
            setMessages((prev) => [
              ...prev,
              {
                id: createMessageId(),
                role: "assistant",
                content: errorMessage,
              },
            ]);
            streamClosed = true;
            break;
          }
          case "error": {
            const errorEvent = event as ResponseErrorEvent;
            setMessages((prev) => [
              ...prev,
              {
                id: createMessageId(),
                role: "assistant",
                content: errorEvent.message || "Falha ao gerar resposta.",
              },
            ]);
            streamClosed = true;
            break;
          }
          default:
            break;
        }
      };

      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (!streamClosed) {
          const { done, value } = await reader.read();
          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split("\n\n");
          buffer = events.pop() || "";

          for (const eventChunk of events) {
            const lines = eventChunk.split("\n");
            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              const payload = line.slice(6);
              if (payload === "[DONE]") {
                streamClosed = true;
                break;
              }
              try {
                const parsed = JSON.parse(payload);
                handleStreamEvent(parsed);
              } catch (parseError) {
                console.error("Erro ao analisar evento SSE:", parseError);
              }
            }
            if (streamClosed) {
              break;
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: createMessageId(),
          role: "assistant",
          content: "Desculpe, ocorreu um erro. Tente novamente.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Retry a tool by calling backend tool invoke endpoint
  const handleRetryTool = async (callId?: string, toolName?: string) => {
    if (!callId || !toolName) return;
    try {
      const baseUrl = apiClient.getBaseUrl();
      const token = apiClient.getAuthToken();

      // Find the function call message with arguments
      const fc = messages.find((m) => m.kind === "function_call" && m.functionCall?.callId === callId);
      let args: any = undefined;
      if (fc?.functionCall?.arguments) {
        try {
          args = JSON.parse(fc.functionCall.arguments);
        } catch {
          // not JSON, pass as raw
          args = fc.functionCall.arguments;
        }
      }

      // Mark or create a tool result placeholder for UX
      let updated = false;
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.kind === "function_result" && msg.metadata?.callId === callId) {
            updated = true;
            return {
              ...msg,
              metadata: { ...msg.metadata, status: "in_progress", startedAt: new Date().toISOString() },
            };
          }
          return msg;
        })
      );

      if (!updated) {
        // Append a placeholder
        const placeholderId = createMessageId();
        setMessages((prev) => [
          ...prev,
          {
            id: placeholderId,
            role: "tool",
            content: "Executando...",
            kind: "function_result",
            metadata: { callId, toolName, status: "in_progress", createdAt: new Date().toISOString(), startedAt: new Date().toISOString() },
          },
        ]);
      }

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${baseUrl}/v1/tools/${encodeURIComponent(toolName)}/invoke`, {
        method: "POST",
        headers,
        body: JSON.stringify({ arguments: args }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Tool invoke failed: ${res.status} ${text}`);
      }

      const payload = await res.json();
      const result = payload.result ?? payload.output ?? JSON.stringify(payload);

      // Update existing tool message with result
      setMessages((prev) =>
        prev.map((msg) =>
          msg.kind === "function_result" && msg.metadata?.callId === callId
            ? {
                ...msg,
                content: typeof result === "string" ? result : JSON.stringify(result, null, 2),
                metadata: { ...msg.metadata, status: "completed", updatedAt: new Date().toISOString(), durationMs: msg.metadata?.startedAt ? new Date().getTime() - new Date(msg.metadata.startedAt).getTime() : undefined },
              }
            : msg
        )
      );
    } catch (e: any) {
      console.error("Retry tool failed:", e);
      setMessages((prev) => [
        ...prev,
        {
          id: createMessageId(),
          role: "assistant",
          content: `Falha ao executar ferramenta: ${e?.message ?? e}`,
        },
      ]);
    }
  };

  // Use a tool result (apply to assistant) — insert assistant message with content
  const handleUseToolResult = (content?: string) => {
    if (!content) return;
    setMessages((prev) => [
      ...prev,
      { id: createMessageId(), role: "assistant", content, kind: "text" },
    ]);
  };

  return (
    <Card className="flex flex-col h-full overflow-hidden border-0 shadow-none">
      <div className="flex-1 overflow-y-auto p-4 space-y-6" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground opacity-50">
            <Bot className="h-12 w-12 mb-2" />
            <p>Comece uma conversa com {entityId}</p>
          </div>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex gap-3 ${
              m.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {m.role === "assistant" && (
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                <Bot className="h-4 w-4 text-primary" />
              </div>
            )}
            <div
              className={`rounded-lg p-3 max-w-[80%] ${
                m.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}
            >
              <div className="prose dark:prose-invert text-sm break-words max-w-none">
                {m.kind === "function_call" && m.functionCall ? (
                  <FunctionCallCard message={m} />
                ) : m.role === "tool" ? (
                  <ToolResultCard message={m} onRetry={handleRetryTool} onUse={handleUseToolResult} />
                ) : (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      pre: ({ node, ...props }) => (
                        <div className="overflow-auto w-full my-2 bg-black/10 dark:bg-black/30 p-2 rounded">
                          <pre {...props} />
                        </div>
                      ),
                      code: ({ node, ...props }) => (
                        <code
                          className="bg-black/10 dark:bg-black/30 rounded px-1"
                          {...props}
                        />
                      ),
                    }}
                  >
                    {m.content || (m.role === "assistant" ? "…" : "")}
                  </ReactMarkdown>
                )}
              </div>
            </div>
            {m.role === "user" && (
              <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center shrink-0">
                <User className="h-4 w-4" />
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
             <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mr-3">
                <Bot className="h-4 w-4 text-primary" />
              </div>
            <div className="bg-muted p-3 rounded-lg">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
          </div>
        )}
      </div>
      <div className="p-4 border-t bg-background">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite sua mensagem..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" size="icon" disabled={isLoading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </Card>
  );
}
