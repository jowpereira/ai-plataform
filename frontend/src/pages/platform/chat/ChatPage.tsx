/**
 * ChatPage - Interface de chat unificada para agentes e workflows
 * Utiliza a mesma engine robusta do Playground (AgentView)
 * mas focada apenas na conversação, sem painel de debug
 * 
 * NOTA: Workflows são tratados como agentes para fins de chat,
 * já que a API de conversação é unificada para ambos.
 */

import { useEffect, useCallback } from "react";
import { AgentView } from "@/components/features/agent";
import { GalleryView } from "@/components/features/gallery";
import { Card } from "@/components/ui/card";
import { MessageSquare } from "lucide-react";
import type { AgentInfo, ExtendedResponseStreamEvent } from "@/types";
import { useDevUIStore } from "@/stores";

export default function ChatPage() {
  // Entity state from Zustand (carregado pelo PlatformLayout)
  const agents = useDevUIStore((state) => state.agents);
  const workflows = useDevUIStore((state) => state.workflows);
  const selectedAgent = useDevUIStore((state) => state.selectedAgent);

  // OpenAI proxy mode
  const oaiMode = useDevUIStore((state) => state.oaiMode);

  // Garantir que o painel de debug esteja desabilitado na página de Chat
  const setShowDebugPanel = useDevUIStore((state) => state.setShowDebugPanel);
  const selectEntity = useDevUIStore((state) => state.selectEntity);

  // Desabilitar painel de debug ao entrar na página de Chat
  useEffect(() => {
    // Esconder o painel de debug quando estiver na página de Chat
    // Isso garante uma experiência focada na conversação
    setShowDebugPanel(false);
  }, [setShowDebugPanel]);

  // Auto-switch from workflow to agent when OpenAI proxy mode is enabled
  useEffect(() => {
    if (oaiMode.enabled && selectedAgent?.type === "workflow") {
      // Workflows don't work with OpenAI proxy - switch to first available agent
      const firstAgent = agents[0];
      if (firstAgent) {
        selectEntity(firstAgent);
      }
    }
  }, [oaiMode.enabled, selectedAgent, agents, selectEntity]);

  // Handle debug events - no-op para a página de Chat (não mostramos debug)
  const handleDebugEvent = useCallback(
    (_event: ExtendedResponseStreamEvent | "clear") => {
      // Não fazemos nada com eventos de debug na página de Chat
      // Eles são ignorados para manter a interface limpa
    },
    []
  );

  // Se não há agentes nem workflows, mostrar gallery inline
  if (agents.length === 0 && workflows.length === 0) {
    return (
      <div className="h-[calc(100vh-3.5rem)] flex flex-col">
        <GalleryView variant="inline" />
      </div>
    );
  }

  // Se não há entidade selecionada, mostrar placeholder
  if (!selectedAgent) {
    return (
      <div className="h-[calc(100vh-3.5rem)] flex flex-col p-4">
        <Card className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
          <MessageSquare className="h-12 w-12 mb-4 opacity-50" />
          <h2 className="text-lg font-medium mb-2">Nenhum agente selecionado</h2>
          <p className="text-sm text-center max-w-md">
            Selecione um agente ou workflow no header acima para iniciar uma conversa.
          </p>
        </Card>
      </div>
    );
  }

  // Usar AgentView para TODOS os tipos (agent e workflow)
  // A API de chat trata ambos da mesma forma, permitindo uma interface unificada
  // Para workflows, o AgentView funciona perfeitamente pois a API é a mesma
  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col">
      <AgentView
        selectedAgent={selectedAgent as AgentInfo}
        onDebugEvent={handleDebugEvent}
      />
    </div>
  );
}
