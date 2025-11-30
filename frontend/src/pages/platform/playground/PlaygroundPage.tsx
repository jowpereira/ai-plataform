/**
 * PlaygroundPage - Ambiente de desenvolvimento e testes para agentes e workflows
 * Features: Entity selection, layout management, debug coordination
 * Nota: Header e carregamento de dados movidos para PlatformLayout
 */

import { useEffect, useCallback } from "react";
import { DebugPanel, SettingsModal, DeploymentModal } from "@/components/layout";
import { GalleryView } from "@/components/features/gallery";
import { AgentView } from "@/components/features/agent";
import { WorkflowView } from "@/components/features/workflow";
import { Toast, ToastContainer } from "@/components/ui/toast";
import { PanelRightOpen, ChevronLeft, Rocket } from "lucide-react";
import type {
  AgentInfo,
  WorkflowInfo,
  ExtendedResponseStreamEvent,
} from "@/types";
import { Button } from "@/components/ui/button";
import { useDevUIStore } from "@/stores";

export default function PlaygroundPage() {
  // Entity state from Zustand (carregado pelo PlatformLayout)
  const agents = useDevUIStore((state) => state.agents);
  const workflows = useDevUIStore((state) => state.workflows);
  const selectedAgent = useDevUIStore((state) => state.selectedAgent);
  const azureDeploymentEnabled = useDevUIStore((state) => state.azureDeploymentEnabled);

  // OpenAI proxy mode
  const oaiMode = useDevUIStore((state) => state.oaiMode);

  // UI mode
  const uiMode = useDevUIStore((state) => state.uiMode);

  // UI state from Zustand
  const showDebugPanel = useDevUIStore((state) => state.showDebugPanel);
  const debugPanelMinimized = useDevUIStore((state) => state.debugPanelMinimized);
  const debugPanelWidth = useDevUIStore((state) => state.debugPanelWidth);
  const debugEvents = useDevUIStore((state) => state.debugEvents);
  const isResizing = useDevUIStore((state) => state.isResizing);

  // UI actions
  const setShowDebugPanel = useDevUIStore((state) => state.setShowDebugPanel);
  const setDebugPanelMinimized = useDevUIStore((state) => state.setDebugPanelMinimized);
  const setDebugPanelWidth = useDevUIStore((state) => state.setDebugPanelWidth);
  const addDebugEvent = useDevUIStore((state) => state.addDebugEvent);
  const clearDebugEvents = useDevUIStore((state) => state.clearDebugEvents);
  const setIsResizing = useDevUIStore((state) => state.setIsResizing);
  const selectEntity = useDevUIStore((state) => state.selectEntity);

  // Modal state
  const showAboutModal = useDevUIStore((state) => state.showAboutModal);
  const showGallery = useDevUIStore((state) => state.showGallery);
  const showDeployModal = useDevUIStore((state) => state.showDeployModal);
  const showEntityNotFoundToast = useDevUIStore((state) => state.showEntityNotFoundToast);

  // Modal actions
  const setShowAboutModal = useDevUIStore((state) => state.setShowAboutModal);
  const setShowGallery = useDevUIStore((state) => state.setShowGallery);
  const setShowDeployModal = useDevUIStore((state) => state.setShowDeployModal);
  const setShowEntityNotFoundToast = useDevUIStore((state) => state.setShowEntityNotFoundToast);

  // Toast state and actions
  const toasts = useDevUIStore((state) => state.toasts);
  const removeToast = useDevUIStore((state) => state.removeToast);

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

  // Handle resize drag
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsResizing(true);

      const startX = e.clientX;
      const startWidth = debugPanelWidth;

      const handleMouseMove = (e: MouseEvent) => {
        const deltaX = startX - e.clientX; // Subtract because we're dragging from right
        const newWidth = Math.max(
          200,
          Math.min(window.innerWidth * 0.5, startWidth + deltaX)
        );
        setDebugPanelWidth(newWidth);
      };

      const handleMouseUp = () => {
        setIsResizing(false);
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
      };

      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    },
    [debugPanelWidth, setIsResizing, setDebugPanelWidth]
  );

  // Handle debug events from active view
  const handleDebugEvent = useCallback(
    (event: ExtendedResponseStreamEvent | "clear") => {
      if (event === "clear") {
        clearDebugEvents();
      } else {
        addDebugEvent(event);
      }
    },
    [addDebugEvent, clearDebugEvents]
  );

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col bg-background max-h-[calc(100vh-3.5rem)]">
      {/* Main Content - Split Panel or Gallery */}
      <div className="flex flex-1 overflow-hidden">
        {showGallery ? (
          // Show gallery full screen (w-full ensures it takes entire width)
          <div className="flex-1 w-full">
            <GalleryView
              variant="route"
              onClose={() => setShowGallery(false)}
              hasExistingEntities={
                agents.length > 0 || workflows.length > 0
              }
            />
          </div>
        ) : agents.length === 0 && workflows.length === 0 ? (
          // Empty state - show gallery inline (full width, no debug panel)
          <GalleryView variant="inline" />
        ) : (
          <>
            {/* Left Panel - Main View */}
            <div className="flex-1 min-w-0">
              {selectedAgent ? (
                selectedAgent.type === "agent" ? (
                  <AgentView
                    selectedAgent={selectedAgent as AgentInfo}
                    onDebugEvent={handleDebugEvent}
                  />
                ) : (
                  <WorkflowView
                    selectedWorkflow={selectedAgent as WorkflowInfo}
                    onDebugEvent={handleDebugEvent}
                  />
                )
              ) : (
                <div className="flex-1 flex items-center justify-center text-muted-foreground">
                  Select an agent or workflow to get started.
                </div>
              )}
            </div>

            {uiMode === "developer" && showDebugPanel ? (
              <>
                {/* Resize Handle */}
                <div
                  className={`w-1 cursor-col-resize flex-shrink-0 relative group transition-colors duration-200 ease-in-out ${
                    isResizing ? "bg-primary/40" : "bg-border hover:bg-primary/20"
                  }`}
                  onMouseDown={handleMouseDown}
                >
                  <div className="absolute inset-y-0 -left-2 -right-2 flex items-center justify-center">
                    <div
                      className={`h-12 w-1 rounded-full transition-all duration-200 ease-in-out ${
                        isResizing
                          ? "bg-primary shadow-lg shadow-primary/25"
                          : "bg-primary/30 group-hover:bg-primary group-hover:shadow-md group-hover:shadow-primary/20"
                      }`}
                    ></div>
                  </div>
                </div>

                {/* Right Panel - Debug */}
                <div
                  className="flex-shrink-0 flex flex-col h-full"
                  style={{ width: debugPanelMinimized ? '2.5rem' : `${debugPanelWidth}px` }}
                >
                  {debugPanelMinimized ? (
                    /* Minimized Debug Panel - Vertical Bar (fully clickable) */
                    <div
                      className="h-full w-10 bg-background border-l flex flex-col items-center py-2 cursor-pointer hover:bg-accent/50 transition-colors"
                      onClick={() => setDebugPanelMinimized(false)}
                      title="Expand debug panel"
                    >
                      {/* Expand button at top (visual affordance) */}
                      <div className="h-8 w-8 flex items-center justify-center">
                        <ChevronLeft className="h-4 w-4 text-muted-foreground" />
                      </div>

                      {/* Text and count centered in middle */}
                      <div className="flex-1 flex flex-col items-center justify-center gap-2 pointer-events-none">
                        <div
                          className="text-xs text-muted-foreground select-none"
                          style={{
                            writingMode: 'vertical-rl',
                            transform: 'rotate(180deg)'
                          }}
                        >
                          Debug Panel
                        </div>
                        {debugEvents.length > 0 && (
                          <div className="bg-primary text-primary-foreground rounded-full w-5 h-5 flex items-center justify-center"
                          style={{ fontSize: '10px' }}>
                            {debugEvents.length}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <>
                      <DebugPanel
                        events={debugEvents}
                        isStreaming={false} // Each view manages its own streaming state
                        onMinimize={() => setDebugPanelMinimized(true)}
                      />

                      {/* Deploy Footer - Pinned to bottom */}
                      <div className="border-t bg-muted/30 px-3 py-2.5 flex-shrink-0">
                        <Button
                          onClick={() => setShowDeployModal(true)}
                          className="w-full"
                          variant="outline"
                          size="sm"
                        >
                          <Rocket className="h-3 w-3 mr-2 flex-shrink-0" />
                          <span className="truncate text-xs">
                            {azureDeploymentEnabled && selectedAgent?.deployment_supported
                              ? "Deploy to Azure"
                              : "Deployment Guide"}
                          </span>
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              </>
            ) : uiMode === "developer" ? (
              /* Button to reopen when closed */
              <div className="flex-shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowDebugPanel(true)}
                  className="h-full w-10 rounded-none border-l"
                  title="Show debug panel"
                >
                  <PanelRightOpen className="h-4 w-4" />
                </Button>
              </div>
            ) : null}
          </>
        )}
      </div>

      {/* Settings Modal */}
      <SettingsModal open={showAboutModal} onOpenChange={setShowAboutModal} />

      {/* Deployment Modal */}
      <DeploymentModal
        open={showDeployModal}
        onClose={() => setShowDeployModal(false)}
        agentName={selectedAgent?.name}
        entity={selectedAgent}
      />

      {/* Toast Notification */}
      {showEntityNotFoundToast && (
        <Toast
          message="Entity not found. Showing first available entity instead."
          type="info"
          onClose={() => setShowEntityNotFoundToast(false)}
        />
      )}

      {/* Toast Container for reload and other notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}
