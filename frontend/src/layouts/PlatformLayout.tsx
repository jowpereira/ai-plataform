import { Link, Outlet, useLocation, useSearchParams } from "react-router-dom";
import { useEffect, useCallback, useState } from "react";
import { Button } from "@/components/ui/button";
import { Toaster } from "@/components/ui/toaster";
import { Input } from "@/components/ui/input";
import { AppHeader, SettingsModal } from "@/components/layout";
import { useDevUIStore } from "@/stores";
import { apiClient } from "@/services/api";
import type { AgentInfo, WorkflowInfo } from "@/types";
import { 
  LayoutDashboard, 
  Bot, 
  MessageSquare, 
  Play, 
  Settings,
  LogOut,
  Users,
  Workflow,
  Boxes,
  ServerOff,
  Lock,
  ChevronDown,
  Database,
} from "lucide-react";

export default function PlatformLayout() {
  const location = useLocation();
  const [searchParams] = useSearchParams();

  // Local state for auth handling
  const [authRequired, setAuthRequired] = useState(false);
  const [authToken, setAuthToken] = useState("");
  const [isTestingToken, setIsTestingToken] = useState(false);
  const [authError, setAuthError] = useState("");

  // Entity state from Zustand
  const agents = useDevUIStore((state) => state.agents);
  const workflows = useDevUIStore((state) => state.workflows);
  const entities = useDevUIStore((state) => state.entities);
  const selectedAgent = useDevUIStore((state) => state.selectedAgent);
  const isLoadingEntities = useDevUIStore((state) => state.isLoadingEntities);
  const entityError = useDevUIStore((state) => state.entityError);

  // Entity actions
  const setAgents = useDevUIStore((state) => state.setAgents);
  const setWorkflows = useDevUIStore((state) => state.setWorkflows);
  const setEntities = useDevUIStore((state) => state.setEntities);
  const selectEntity = useDevUIStore((state) => state.selectEntity);
  const updateAgent = useDevUIStore((state) => state.updateAgent);
  const updateWorkflow = useDevUIStore((state) => state.updateWorkflow);
  const setIsLoadingEntities = useDevUIStore((state) => state.setIsLoadingEntities);
  const setEntityError = useDevUIStore((state) => state.setEntityError);
  const setShowEntityNotFoundToast = useDevUIStore((state) => state.setShowEntityNotFoundToast);

  // Modal state
  const showAboutModal = useDevUIStore((state) => state.showAboutModal);
  const setShowAboutModal = useDevUIStore((state) => state.setShowAboutModal);
  const setShowGallery = useDevUIStore((state) => state.setShowGallery);

  const isActive = (path: string) => location.pathname.startsWith(path);

  // Initialize app - load agents and workflows
  useEffect(() => {
    const loadData = async () => {
      try {
        // Fetch server metadata first (ui_mode, capabilities, auth status)
        const meta = await apiClient.getMeta();

        // Check if auth is required
        if (meta.auth_required) {
          setAuthRequired(true);

          // If we don't have a token, stop here and show auth UI
          if (!apiClient.getAuthToken()) {
            setEntityError("UNAUTHORIZED");
            setIsLoadingEntities(false);
            return;
          }
        }

        useDevUIStore.getState().setServerMeta({
          uiMode: meta.ui_mode,
          runtime: meta.runtime,
          capabilities: meta.capabilities,
          authRequired: meta.auth_required,
        });

        // Single API call instead of two parallel calls to same endpoint
        const { entities: allEntities, agents: agentList, workflows: workflowList } = await apiClient.getEntities();

        setEntities(allEntities);
        setAgents(agentList);
        setWorkflows(workflowList);

        // Check if there's an entity_id in the URL
        const entityId = searchParams.get("entity_id");

        let selectedEntity: AgentInfo | WorkflowInfo | undefined;

        // Try to find entity from URL parameter first
        if (entityId) {
          selectedEntity = allEntities.find((e) => e.id === entityId);

          // If entity not found but was requested, show notification
          if (!selectedEntity) {
            setShowEntityNotFoundToast(true);
          }
        }

        // Fallback to first available entity if URL entity not found
        if (!selectedEntity) {
          // Use the first entity from the backend's original order
          selectedEntity = allEntities.length > 0 ? allEntities[0] : undefined;
        }

        if (selectedEntity) {
          selectEntity(selectedEntity);

          // Load full info for the first entity immediately
          if (selectedEntity.metadata?.lazy_loaded === false) {
            try {
              if (selectedEntity.type === "agent") {
                const fullAgent = await apiClient.getAgentInfo(selectedEntity.id);
                updateAgent(fullAgent);
              } else {
                const fullWorkflow = await apiClient.getWorkflowInfo(selectedEntity.id);
                updateWorkflow(fullWorkflow);
              }
            } catch (error) {
              console.error(`Failed to load full info for first entity ${selectedEntity.id}:`, error);
            }
          }
        }

        setIsLoadingEntities(false);
      } catch (error) {
        console.error("Failed to load agents/workflows:", error);
        const errorMessage = error instanceof Error ? error.message : "Failed to load data";

        // Check if this is an auth error
        if (errorMessage === "UNAUTHORIZED") {
          setAuthRequired(true);
        }

        setEntityError(errorMessage);
        setIsLoadingEntities(false);
      }
    };

    loadData();
  }, [searchParams, setAgents, setWorkflows, setEntities, selectEntity, updateAgent, updateWorkflow, setIsLoadingEntities, setEntityError, setShowEntityNotFoundToast]);

  // Handle auth token submission
  const handleAuthTokenSubmit = useCallback(async () => {
    if (!authToken.trim()) return;

    setIsTestingToken(true);
    setAuthError("");

    try {
      // Set token in API client (stores in localStorage)
      apiClient.setAuthToken(authToken.trim());

      // Test the token with an actual PROTECTED endpoint (not /meta which is public)
      await apiClient.getEntities();

      // If successful, reload to initialize with new token
      window.location.reload();
    } catch (error) {
      // Token is invalid - clear it and show error
      apiClient.clearAuthToken();
      setIsTestingToken(false);

      const errorMsg = error instanceof Error ? error.message : "Unknown error";
      if (errorMsg === "UNAUTHORIZED") {
        setAuthError("Invalid token. Please check and try again.");
      } else {
        setAuthError(`Failed to connect: ${errorMsg}`);
      }
    }
  }, [authToken]);

  // Handle entity selection - uses Zustand's selectEntity which handles ALL side effects
  const handleEntitySelect = useCallback(
    async (item: AgentInfo | WorkflowInfo) => {
      selectEntity(item); // This clears conversation state, debug events, and updates URL!

      // If entity is sparse (not fully loaded), load full details
      if (item.metadata?.lazy_loaded === false) {
        try {
          if (item.type === "agent") {
            const fullAgent = await apiClient.getAgentInfo(item.id);
            updateAgent(fullAgent);
          } else {
            const fullWorkflow = await apiClient.getWorkflowInfo(item.id);
            updateWorkflow(fullWorkflow);
          }
        } catch (error) {
          console.error(`Failed to load full info for ${item.id}:`, error);
        }
      }
    },
    [selectEntity, updateAgent, updateWorkflow]
  );

  // Show loading state while initializing
  if (isLoadingEntities) {
    return (
      <div className="flex h-screen bg-background">
        {/* Sidebar - Skeleton */}
        <aside className="w-64 border-r bg-muted/30 flex flex-col">
          <div className="p-6 border-b">
            <div className="w-32 h-6 bg-muted animate-pulse rounded-md" />
          </div>
          <nav className="flex-1 p-4 space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="w-full h-9 bg-muted animate-pulse rounded-md" />
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header Skeleton */}
          <header className="flex h-14 items-center gap-4 border-b px-4">
            <div className="w-64 h-9 bg-muted animate-pulse rounded-md" />
            <div className="flex items-center gap-2 ml-auto">
              <div className="w-8 h-8 bg-muted animate-pulse rounded-md" />
              <div className="w-8 h-8 bg-muted animate-pulse rounded-md" />
            </div>
          </header>

          {/* Loading Content */}
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="text-lg font-medium">Initializing MAIA...</div>
              <div className="text-sm text-muted-foreground mt-2">Loading agents and workflows from your configuration</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show error state if loading failed
  if (entityError) {
    const currentBackendUrl = apiClient.getBaseUrl();
    const isAuthError = entityError === "UNAUTHORIZED" || authRequired;

    // Extract port from the backend URL for the command suggestion
    let backendPort = "8080"; // default fallback
    try {
      if (currentBackendUrl) {
        const url = new URL(currentBackendUrl);
        backendPort = url.port || (url.protocol === "https:" ? "443" : "80");
      }
    } catch {
      // If URL parsing fails, keep default
    }

    return (
      <div className="flex h-screen bg-background">
        {/* Sidebar */}
        <aside className="w-64 border-r bg-muted/30 flex flex-col">
          <div className="p-6 border-b">
            <h1 className="text-xl font-bold flex items-center gap-2">
              <Bot className="h-6 w-6" />
              MAIA
            </h1>
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          <AppHeader
            agents={[]}
            workflows={[]}
            entities={[]}
            selectedItem={undefined}
            onSelect={() => {}}
            isLoading={false}
            onSettingsClick={() => setShowAboutModal(true)}
          />

          {/* Error Content */}
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center space-y-6 max-w-2xl">
              {/* Icon */}
              <div className="flex justify-center">
                <div className="rounded-full bg-muted p-4 animate-pulse">
                  {isAuthError ? (
                    <Lock className="h-12 w-12 text-muted-foreground" />
                  ) : (
                    <ServerOff className="h-12 w-12 text-muted-foreground" />
                  )}
                </div>
              </div>

              {/* Heading */}
              <div className="space-y-2">
                <h2 className="text-2xl font-semibold text-foreground">
                  {isAuthError ? "Authentication Required" : "Can't Connect to Backend"}
                </h2>
                <p className="text-muted-foreground text-base">
                  {isAuthError
                    ? "This backend requires a bearer token to access."
                    : "No worries! Just start the DevUI backend server and you'll be good to go."}
                </p>
              </div>

              {/* Auth Input or Command Instructions */}
              {isAuthError ? (
                <div className="space-y-4">
                  <div className="text-left bg-muted/50 rounded-lg p-4 space-y-3">
                    <p className="text-sm font-medium text-foreground">
                      Enter Authentication Token
                    </p>
                    <Input
                      type="password"
                      placeholder="Paste token from server logs"
                      value={authToken}
                      onChange={(e) => setAuthToken(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !isTestingToken) {
                          handleAuthTokenSubmit();
                        }
                      }}
                      disabled={isTestingToken}
                      className="font-mono text-sm"
                    />
                    <Button
                      onClick={handleAuthTokenSubmit}
                      disabled={!authToken.trim() || isTestingToken}
                      className="w-full"
                    >
                      {isTestingToken ? "Verifying..." : "Connect"}
                    </Button>

                    {/* Error message */}
                    {authError && (
                      <p className="text-sm text-red-600 dark:text-red-400 text-center">
                        {authError}
                      </p>
                    )}
                  </div>

                  <details className="text-left group">
                    <summary className="text-sm text-muted-foreground cursor-pointer hover:text-foreground flex items-center gap-2 justify-center">
                      <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
                      Where do I find the token?
                    </summary>
                    <div className="mt-3 text-left bg-muted/30 rounded-lg p-3 space-y-2">
                      <p className="text-xs text-muted-foreground">
                        Look for this in your DevUI server startup logs:
                      </p>
                      <code className="block bg-background px-2 py-1 rounded text-xs font-mono text-foreground">
                        🔑 DEV TOKEN (localhost only, shown once):
                        <br />
                        &nbsp;&nbsp; abc123xyz...
                      </code>
                    </div>
                  </details>
                </div>
              ) : (
                <>
                  <div className="space-y-3">
                    <div className="text-left bg-muted/50 rounded-lg p-4 space-y-3">
                      <p className="text-sm font-medium text-foreground">
                        Start the backend:
                      </p>
                      <code className="block bg-background px-3 py-2 rounded border text-sm font-mono text-foreground">
                        devui ./agents --port {backendPort}
                      </code>
                      <p className="text-xs text-muted-foreground">
                        Or launch programmatically with{" "}
                        <code className="text-xs">serve(entities=[agent])</code>
                      </p>
                    </div>

                    <p className="text-xs text-muted-foreground">
                      Default:{" "}
                      <span className="font-mono">{currentBackendUrl}</span>
                    </p>
                  </div>

                  {/* Error Details (Collapsible) */}
                  {entityError && (
                    <details className="text-left group">
                      <summary className="text-sm text-muted-foreground cursor-pointer hover:text-foreground flex items-center gap-2">
                        <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
                        Error details
                      </summary>
                      <p className="mt-2 text-xs text-muted-foreground font-mono bg-muted/30 p-3 rounded border">
                        {entityError}
                      </p>
                    </details>
                  )}

                  {/* Retry Button */}
                  <Button
                    onClick={() => window.location.reload()}
                    variant="default"
                    className="mt-2"
                  >
                    Retry Connection
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Settings Modal */}
        <SettingsModal open={showAboutModal} onOpenChange={setShowAboutModal} />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-muted/30 flex flex-col">
        {/* Sidebar Navigation - sem título já que o Header tem a marca */}
        <div className="p-6 border-b">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Menu</span>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          <Link to="/platform/dashboard">
            <Button 
              variant={isActive("/platform/dashboard") ? "secondary" : "ghost"} 
              className="w-full justify-start gap-2"
            >
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </Button>
          </Link>
          <Link to="/platform/agents">
            <Button 
              variant={isActive("/platform/agents") ? "secondary" : "ghost"} 
              className="w-full justify-start gap-2"
            >
              <Boxes className="h-4 w-4" />
              Agentes
            </Button>
          </Link>
          <Link to="/platform/workflows">
            <Button 
              variant={isActive("/platform/workflows") || isActive("/platform/studio") ? "secondary" : "ghost"} 
              className="w-full justify-start gap-2"
            >
              <Workflow className="h-4 w-4" />
              Workflows
            </Button>
          </Link>
          <Link to="/platform/knowledge">
            <Button 
              variant={isActive("/platform/knowledge") ? "secondary" : "ghost"} 
              className="w-full justify-start gap-2"
            >
              <Database className="h-4 w-4" />
              Knowledge
            </Button>
          </Link>
          
          <div className="pt-4 mt-4 border-t">
            <p className="px-4 text-xs font-medium text-muted-foreground mb-2">Interação</p>
            <Link to="/platform/playground">
              <Button 
                variant={isActive("/platform/playground") ? "secondary" : "ghost"} 
                className="w-full justify-start gap-2"
              >
                <Play className="h-4 w-4" />
                Playground
              </Button>
            </Link>
            <Link to="/platform/chat">
              <Button 
                variant={isActive("/platform/chat") ? "secondary" : "ghost"} 
                className="w-full justify-start gap-2"
              >
                <MessageSquare className="h-4 w-4" />
                Chat
              </Button>
            </Link>
          </div>

          <div className="pt-4 mt-4 border-t">
            <p className="px-4 text-xs font-medium text-muted-foreground mb-2">Admin</p>
            <Link to="/platform/users">
              <Button 
                variant={isActive("/platform/users") ? "secondary" : "ghost"} 
                className="w-full justify-start gap-2"
              >
                <Users className="h-4 w-4" />
                Users
              </Button>
            </Link>
          </div>
        </nav>

        <div className="p-4 border-t space-y-2">
          <Button variant="ghost" className="w-full justify-start gap-2" onClick={() => setShowAboutModal(true)}>
            <Settings className="h-4 w-4" />
            Settings
          </Button>
          <Link to="/">
            <Button variant="ghost" className="w-full justify-start gap-2 text-red-500 hover:text-red-600 hover:bg-red-50">
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Global Header - Entity selector only on Playground/Chat */}
        <AppHeader
          agents={agents}
          workflows={workflows}
          entities={entities}
          selectedItem={selectedAgent}
          onSelect={handleEntitySelect}
          onBrowseGallery={() => setShowGallery(true)}
          isLoading={isLoadingEntities}
          onSettingsClick={() => setShowAboutModal(true)}
          showEntitySelector={isActive("/platform/playground") || isActive("/platform/chat")}
        />

        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>

      {/* Modals */}
      <SettingsModal open={showAboutModal} onOpenChange={setShowAboutModal} />
      <Toaster />
    </div>
  );
}
