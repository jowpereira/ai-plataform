import { useState, useMemo, useCallback, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { 
  Save, 
  Loader2, 
  Download, 
  Upload, 
  Code,
  Bot,
  FileJson,
  GitBranch,
  Plus,
  Pencil,
  Trash2,
  AlertCircle,
  CheckCircle2,
  RefreshCw
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { ApiClient } from "@/services/api";

import { 
  StudioConfigPanel, 
  useStudioStore,
  WorkflowTypeSelector,
  AgentFormModal,
  SequentialEditor,
  ParallelEditor,
  GroupChatEditor,
  HandoffEditor,
  RouterEditor,
  MagenticEditor,
} from "@/components/features/studio";
import type { WorkflowType, AgentConfig, WorkflowStep } from "@/components/features/studio/types";
import { 
  downloadWorkerConfig, 
  importWorkerConfig, 
  saveDraft 
} from "@/utils/workflowSerializer";

export default function StudioPage() {
  const { toast } = useToast();
  
  // Store state
  const workerConfig = useStudioStore((state) => state.workerConfig);
  const setWorkerConfig = useStudioStore((state) => state.setWorkerConfig);
  const generateConfig = useStudioStore((state) => state.generateConfig);
  
  // Local state
  const [searchParams] = useSearchParams();
  const workflowFile = searchParams.get("file"); // Nome do arquivo para carregar
  const api = useMemo(() => new ApiClient(), []);

  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [activeTab, setActiveTab] = useState<"editor" | "preview">("editor");
  const [showAgentModal, setShowAgentModal] = useState(false);
  const [editingAgent, setEditingAgent] = useState<AgentConfig | null>(null);
  const [savedAgents, setSavedAgents] = useState<AgentConfig[]>([]); // Agentes salvos na API
  const [, setLoadedFileName] = useState<string | null>(null); // Arquivo carregado

  // Carregar workflow se file estiver na URL
  useEffect(() => {
    const loadWorkflowFromFile = async (filename: string) => {
      try {
        // Buscar todos os workflows e encontrar pelo nome do arquivo
        const workflows = await api.getSavedWorkflows();
        const workflow = workflows.find(w => w._file === filename);
        
        if (workflow) {
          // Carregar a configuração completa no store
          setWorkerConfig(workflow as any);
          setLoadedFileName(filename);
          toast({ title: "Workflow carregado", description: workflow.name || filename });
        } else {
          toast({
            title: "Erro ao carregar workflow",
            description: `Arquivo não encontrado: ${filename}`,
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Error loading workflow:", error);
        toast({
          title: "Erro ao carregar workflow",
          description: String(error),
          variant: "destructive",
        });
      }
    };

    if (workflowFile) {
      loadWorkflowFromFile(workflowFile);
    }
  }, [workflowFile, api, setWorkerConfig, toast]);

  // Carregar agentes existentes da API
  const loadSavedAgents = useCallback(async () => {
    console.log("Carregando agentes salvos...");
    setIsLoadingAgents(true);
    try {
      const response = await fetch("/v1/agents");
      if (response.ok) {
        const data = await response.json();
        console.log("Agentes carregados:", data.data);
        setSavedAgents(data.data || []);
      }
    } catch (error) {
      console.error("Erro ao carregar agentes:", error);
    } finally {
      setIsLoadingAgents(false);
    }
  }, []);

  // Carregar agentes ao montar o componente
  useEffect(() => {
    loadSavedAgents();
  }, [loadSavedAgents]);

  // Agentes salvos que NÃO estão no workflow atual (disponíveis para adicionar)
  const availableSavedAgents = useMemo(() => {
    const workflowAgentIds = new Set((workerConfig.agents || []).map((a) => a.id));
    return savedAgents.filter((a) => !workflowAgentIds.has(a.id));
  }, [savedAgents, workerConfig.agents]);

  // Handler para adicionar agente existente ao workflow
  const handleAddExistingAgent = useCallback((agent: AgentConfig) => {
    // Remover campo _file se existir
    const { _file, ...cleanAgent } = agent as AgentConfig & { _file?: string };
    setWorkerConfig({
      ...workerConfig,
      agents: [...(workerConfig.agents || []), cleanAgent],
    });
    toast({ title: "Agente adicionado ao workflow" });
  }, [workerConfig, setWorkerConfig, toast]);
  
  // Derived state
  const workflowType = workerConfig.workflow.type as WorkflowType;
  const agents = workerConfig.agents || [];
  const steps = workerConfig.workflow.steps || [];
  const startStep = workerConfig.workflow.start_step;
  const availableModels = useMemo(() => workerConfig.resources?.models || {}, [workerConfig.resources]);
  const availableTools = useMemo(() => workerConfig.resources?.tools || [], [workerConfig.resources]);

  // Group Chat config (extrair de workerConfig.workflow ou usar defaults)
  const groupChatConfig = useMemo(() => ({
    manager_model: (workerConfig.workflow as any).manager_model || Object.keys(availableModels)[0] || "gpt-4o",
    manager_instructions: (workerConfig.workflow as any).manager_instructions || "Select the next speaker based on the conversation context.",
    max_rounds: (workerConfig.workflow as any).max_rounds || 8,
    termination_condition: (workerConfig.workflow as any).termination_condition,
  }), [workerConfig.workflow, availableModels]);

  // Magentic One config (extrair de workerConfig.workflow ou usar defaults)
  const magenticConfig = useMemo(() => ({
    manager_model: (workerConfig.workflow as any).manager_model || Object.keys(availableModels)[0] || "gpt-4o-mini",
    manager_instructions: (workerConfig.workflow as any).manager_instructions || "Você é o coordenador de uma equipe de especialistas. Analise a tarefa, crie um plano de execução e coordene os participantes para alcançar o objetivo de forma eficiente.",
    max_rounds: (workerConfig.workflow as any).max_rounds || 20,
    max_stall_count: (workerConfig.workflow as any).max_stall_count || 3,
    enable_plan_review: (workerConfig.workflow as any).enable_plan_review || false,
  }), [workerConfig.workflow, availableModels]);

  // Handlers
  const handleWorkflowTypeChange = useCallback((type: WorkflowType) => {
    setWorkerConfig({
      ...workerConfig,
      workflow: {
        ...workerConfig.workflow,
        type,
        steps: [], // Reset steps quando muda o tipo
        start_step: undefined,
      },
    });
  }, [workerConfig, setWorkerConfig]);

  const handleStepsChange = useCallback((newSteps: WorkflowStep[]) => {
    setWorkerConfig({
      ...workerConfig,
      workflow: {
        ...workerConfig.workflow,
        steps: newSteps,
      },
    });
  }, [workerConfig, setWorkerConfig]);

  const handleStartStepChange = useCallback((stepId: string) => {
    setWorkerConfig({
      ...workerConfig,
      workflow: {
        ...workerConfig.workflow,
        start_step: stepId,
      },
    });
  }, [workerConfig, setWorkerConfig]);

  interface GroupChatConfig {
    manager_model: string;
    manager_instructions: string;
    max_rounds: number;
    termination_condition?: string;
  }

  const handleGroupChatConfigChange = useCallback((config: GroupChatConfig) => {
    setWorkerConfig({
      ...workerConfig,
      workflow: {
        ...workerConfig.workflow,
        ...config,
      } as any,
    });
  }, [workerConfig, setWorkerConfig]);

  interface MagenticConfigType {
    manager_model: string;
    manager_instructions: string;
    max_rounds: number;
    max_stall_count: number;
    enable_plan_review: boolean;
  }

  const handleMagenticConfigChange = useCallback((config: MagenticConfigType) => {
    setWorkerConfig({
      ...workerConfig,
      workflow: {
        ...workerConfig.workflow,
        ...config,
      } as any,
    });
  }, [workerConfig, setWorkerConfig]);

  const handleSaveAgent = useCallback((agent: AgentConfig) => {
    if (editingAgent) {
      // Update existing
      const updatedAgents = agents.map((a) => a.id === editingAgent.id ? agent : a);
      setWorkerConfig({ ...workerConfig, agents: updatedAgents });
    } else {
      // Add new
      setWorkerConfig({ ...workerConfig, agents: [...agents, agent] });
    }
    setEditingAgent(null);
    setShowAgentModal(false);
    toast({ title: editingAgent ? "Agente atualizado" : "Agente criado" });
  }, [editingAgent, agents, workerConfig, setWorkerConfig, toast]);

  const handleEditAgent = useCallback((agent: AgentConfig) => {
    setEditingAgent(agent);
    setShowAgentModal(true);
  }, []);

  const handleDeleteAgent = useCallback((agentId: string) => {
    // Verificar se o agente está sendo usado em algum step
    const isUsedInWorkflow = steps.some((s) => s.agent === agentId);
    if (isUsedInWorkflow) {
      toast({
        title: "Não é possível remover",
        description: "Este agente está sendo usado em um step do workflow. Remova o step primeiro.",
        variant: "destructive",
      });
      return;
    }
    const updatedAgents = agents.filter((a) => a.id !== agentId);
    setWorkerConfig({ ...workerConfig, agents: updatedAgents });
    toast({ title: "Agente removido" });
  }, [agents, steps, workerConfig, setWorkerConfig, toast]);

  // Validação do workflow
  const validationErrors = useMemo(() => {
    const errors: string[] = [];
    if (!workerConfig.name?.trim()) errors.push("Nome do workflow é obrigatório");
    if (agents.length === 0) errors.push("Adicione pelo menos um agente");
    if (steps.length === 0) errors.push("Adicione pelo menos um step ao workflow");
    // Verificar se todos os steps têm agentes válidos
    steps.forEach((step, i) => {
      if (!step.agent) errors.push(`Step ${i + 1} não tem agente selecionado`);
      else if (!agents.find((a) => a.id === step.agent)) {
        errors.push(`Step ${i + 1} referencia agente inexistente`);
      }
    });
    // Validação específica para Magentic
    if (workflowType === "magentic") {
      if (!magenticConfig.manager_model) {
        errors.push("Magentic requer 'manager_model' definido");
      }
      if (steps.length < 2) {
        errors.push("Magentic é mais efetivo com 2+ participantes");
      }
      if (magenticConfig.max_rounds < 5) {
        errors.push(`max_rounds=${magenticConfig.max_rounds} pode ser insuficiente. Considere aumentar para 10+`);
      }
    }
    return errors;
  }, [workerConfig.name, agents, steps, workflowType, magenticConfig]);

  const handleSave = async () => {
    // Validar antes de salvar
    if (validationErrors.length > 0) {
      toast({
        title: "Workflow inválido",
        description: validationErrors[0],
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);
    try {
      const config = generateConfig();
      console.log("Generated Config:", config);
      
      // Salvar rascunho local
      saveDraft(config);
      
      // Salvar workflow no backend (nova API)
      const response = await fetch("/v1/workflows", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`Failed to save: ${response.statusText}`);
      }

      const result = await response.json();
      toast({
        title: "Workflow Salvo",
        description: `Configuração salva em exemplos/workflows/${result.filename}`,
      });
    } catch (error) {
      console.error("Save error:", error);
      toast({
        title: "Erro ao Salvar",
        description: String(error),
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleExport = () => {
    const config = generateConfig();
    downloadWorkerConfig(config, `${config.name || "workflow"}.json`);
    toast({ title: "Exportado", description: "Arquivo JSON baixado." });
  };

  const handleImport = async () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json";
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      
      try {
        const config = await importWorkerConfig(file);
        setWorkerConfig(config);
        toast({ title: "Importado", description: `${config.name} carregado com sucesso.` });
      } catch (err) {
        toast({ 
          title: "Erro na Importação", 
          description: String(err), 
          variant: "destructive" 
        });
      }
    };
    input.click();
  };

  // Render workflow editor baseado no tipo
  const renderWorkflowEditor = () => {
    switch (workflowType) {
      case "sequential":
        return (
          <SequentialEditor
            steps={steps}
            agents={agents}
            onStepsChange={handleStepsChange}
            onCreateAgent={() => setShowAgentModal(true)}
          />
        );
      case "parallel":
        return (
          <ParallelEditor
            steps={steps}
            agents={agents}
            onStepsChange={handleStepsChange}
            onCreateAgent={() => setShowAgentModal(true)}
          />
        );
      case "group_chat":
        return (
          <GroupChatEditor
            steps={steps}
            agents={agents}
            availableModels={availableModels}
            config={groupChatConfig}
            onStepsChange={handleStepsChange}
            onConfigChange={handleGroupChatConfigChange}
            onCreateAgent={() => setShowAgentModal(true)}
          />
        );
      case "handoff":
        return (
          <HandoffEditor
            steps={steps}
            agents={agents}
            startStep={startStep}
            onStepsChange={handleStepsChange}
            onStartStepChange={handleStartStepChange}
            onCreateAgent={() => setShowAgentModal(true)}
          />
        );
      case "router":
        return (
          <RouterEditor
            steps={steps}
            agents={agents}
            startStep={startStep}
            onStepsChange={handleStepsChange}
            onStartStepChange={handleStartStepChange}
            onCreateAgent={() => setShowAgentModal(true)}
          />
        );
      case "magentic":
        return (
          <MagenticEditor
            steps={steps}
            agents={agents}
            availableModels={availableModels}
            config={magenticConfig}
            onStepsChange={handleStepsChange}
            onConfigChange={handleMagenticConfigChange}
            onCreateAgent={() => setShowAgentModal(true)}
          />
        );
      default:
        return (
          <div className="text-center text-muted-foreground py-12">
            Selecione um tipo de workflow
          </div>
        );
    }
  };

  // Preview JSON
  const previewJson = useMemo(() => {
    try {
      return JSON.stringify(generateConfig(), null, 2);
    } catch {
      return "// Erro ao gerar preview";
    }
  }, [generateConfig]);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] overflow-hidden">
      {/* Header */}
      <div className="border-b flex items-center justify-between px-6 py-4 bg-background shrink-0">
        <div className="flex items-center gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-primary" />
              <h1 className="text-lg font-semibold">Workflow Studio</h1>
            </div>
            <div className="flex items-center gap-3">
              <Input
                value={workerConfig.name || ""}
                onChange={(e) => setWorkerConfig({ ...workerConfig, name: e.target.value })}
                placeholder="Nome do workflow..."
                className="h-8 w-[250px] text-sm"
              />
              <Badge variant="secondary">{workflowType}</Badge>
              <Badge variant="outline">
                {agents.length} agentes • {steps.length} steps
              </Badge>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Validation Status */}
          {validationErrors.length > 0 ? (
            <Badge variant="destructive" className="gap-1">
              <AlertCircle className="h-3 w-3" />
              {validationErrors.length} erro{validationErrors.length > 1 ? "s" : ""}
            </Badge>
          ) : (
            <Badge variant="default" className="gap-1 bg-green-600">
              <CheckCircle2 className="h-3 w-3" />
              Válido
            </Badge>
          )}

          <Button variant="outline" size="sm" onClick={handleImport}>
            <Upload className="w-4 h-4 mr-2" />
            Importar
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Exportar
          </Button>
          <Button 
            size="sm" 
            onClick={handleSave} 
            disabled={isSaving} 
            className="bg-green-600 hover:bg-green-700"
          >
            {isSaving ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Salvar Workflow
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)} className="h-full flex flex-col">
          <div className="border-b px-6 bg-muted/30">
            <TabsList className="h-12">
              <TabsTrigger value="editor" className="gap-2">
                <Bot className="h-4 w-4" />
                Editor
              </TabsTrigger>
              <TabsTrigger value="preview" className="gap-2">
                <Code className="h-4 w-4" />
                Preview JSON
              </TabsTrigger>
            </TabsList>
          </div>

          {/* Editor Tab */}
          <TabsContent value="editor" className="flex-1 overflow-hidden m-0">
            <div className="flex h-full">
              {/* Left: Workflow Type + Editor */}
              <div className="flex-1 overflow-auto p-6">
                <div className="max-w-4xl mx-auto space-y-6">
                  
                  {/* Validation Errors */}
                  {validationErrors.length > 0 && (
                    <Card className="border-red-200 bg-red-50 dark:bg-red-950/20">
                      <CardContent className="pt-4">
                        <div className="flex items-start gap-2 text-red-600 dark:text-red-400">
                          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                          <div className="space-y-1">
                            <p className="font-medium">Corrija os erros antes de salvar:</p>
                            <ul className="text-sm list-disc list-inside space-y-0.5">
                              {validationErrors.map((err, i) => (
                                <li key={i}>{err}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Step 1: Workflow Type */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm">1</span>
                        Tipo de Workflow
                      </CardTitle>
                      <CardDescription>Escolha como os agentes serão orquestrados</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <WorkflowTypeSelector
                        selectedType={workflowType}
                        onTypeSelect={handleWorkflowTypeChange}
                      />
                    </CardContent>
                  </Card>

                  {/* Step 2: Agents */}
                  <Card>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-base flex items-center gap-2">
                            <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm">2</span>
                            Gerenciamento de Agentes
                          </CardTitle>
                          <CardDescription>Selecione agentes existentes ou crie novos para o workflow</CardDescription>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button 
                            variant="outline" 
                            size="icon" 
                            onClick={loadSavedAgents} 
                            disabled={isLoadingAgents}
                            title="Atualizar lista de agentes salvos"
                          >
                            <RefreshCw className={`h-4 w-4 ${isLoadingAgents ? "animate-spin" : ""}`} />
                          </Button>
                          <Button size="sm" onClick={() => setShowAgentModal(true)}>
                            <Plus className="h-4 w-4 mr-2" />
                            Novo Agente
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      {isLoadingAgents ? (
                        <div className="text-center py-8 text-muted-foreground">
                          <Loader2 className="h-8 w-8 mx-auto mb-2 animate-spin" />
                          <p>Carregando agentes...</p>
                        </div>
                      ) : (
                        <>
                          {/* Agentes no Workflow Atual */}
                          <div>
                            <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                              <Bot className="h-4 w-4" />
                              No Workflow ({agents.length})
                            </h4>
                            {agents.length === 0 ? (
                              <div className="text-center py-6 text-muted-foreground border-2 border-dashed rounded-lg">
                                <p className="text-sm">Nenhum agente adicionado ao workflow</p>
                                <p className="text-xs mt-1">Selecione um agente existente abaixo ou crie um novo</p>
                              </div>
                            ) : (
                              <div className="grid gap-2">
                                {agents.map((agent) => {
                                  const isUsedInWorkflow = steps.some((s) => s.agent === agent.id);
                                  return (
                                    <div
                                      key={agent.id}
                                      className={`flex items-center justify-between p-3 rounded-lg border ${
                                        isUsedInWorkflow ? "bg-green-50 border-green-200 dark:bg-green-950/20" : "bg-muted/50"
                                      }`}
                                    >
                                      <div className="flex items-center gap-3">
                                        <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
                                          <Bot className="h-4 w-4 text-primary" />
                                        </div>
                                        <div>
                                          <div className="flex items-center gap-2">
                                            <span className="font-medium text-sm">{agent.role}</span>
                                            <Badge variant="outline" className="text-[10px]">{agent.model}</Badge>
                                            {isUsedInWorkflow && (
                                              <Badge variant="default" className="text-[10px] bg-green-600">Em uso</Badge>
                                            )}
                                          </div>
                                          {agent.tools && agent.tools.length > 0 && (
                                            <div className="flex gap-1 mt-1">
                                              {agent.tools.slice(0, 2).map((t) => (
                                                <Badge key={t} variant="secondary" className="text-[9px]">{t}</Badge>
                                              ))}
                                              {agent.tools.length > 2 && (
                                                <Badge variant="secondary" className="text-[9px]">+{agent.tools.length - 2}</Badge>
                                              )}
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-1">
                                        <Button
                                          variant="ghost"
                                          size="icon"
                                          className="h-8 w-8"
                                          onClick={() => handleEditAgent(agent)}
                                          title="Editar agente"
                                        >
                                          <Pencil className="h-4 w-4" />
                                        </Button>
                                        <Button
                                          variant="ghost"
                                          size="icon"
                                          className="h-8 w-8 text-red-500 hover:text-red-600"
                                          onClick={() => handleDeleteAgent(agent.id)}
                                          disabled={isUsedInWorkflow}
                                          title={isUsedInWorkflow ? "Remova o step primeiro" : "Remover do workflow"}
                                        >
                                          <Trash2 className="h-4 w-4" />
                                        </Button>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>

                          {/* Agentes Salvos Disponíveis */}
                          {availableSavedAgents.length > 0 && (
                            <div>
                              <h4 className="text-sm font-medium mb-3 flex items-center gap-2 text-muted-foreground">
                                <Download className="h-4 w-4" />
                                Agentes Salvos Disponíveis ({availableSavedAgents.length})
                              </h4>
                              <div className="grid gap-2">
                                {availableSavedAgents.map((agent) => (
                                  <div
                                    key={agent.id}
                                    className="flex items-center justify-between p-3 rounded-lg border bg-background hover:bg-muted/50 transition-colors"
                                  >
                                    <div className="flex items-center gap-3">
                                      <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center">
                                        <Bot className="h-4 w-4 text-muted-foreground" />
                                      </div>
                                      <div>
                                        <div className="flex items-center gap-2">
                                          <span className="font-medium text-sm">{agent.role}</span>
                                          <Badge variant="outline" className="text-[10px]">{agent.model}</Badge>
                                        </div>
                                        <p className="text-xs text-muted-foreground line-clamp-1">
                                          {agent.description || "Sem descrição"}
                                        </p>
                                      </div>
                                    </div>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => handleAddExistingAgent(agent)}
                                      className="shrink-0"
                                    >
                                      <Plus className="h-4 w-4 mr-1" />
                                      Adicionar
                                    </Button>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Mensagem se não há agentes salvos */}
                          {savedAgents.length === 0 && agents.length === 0 && (
                            <div className="text-center py-6 text-muted-foreground border-2 border-dashed rounded-lg">
                              <Bot className="h-8 w-8 mx-auto mb-2 opacity-50" />
                              <p>Nenhum agente encontrado</p>
                              <p className="text-sm mt-1">Crie um novo agente para começar</p>
                            </div>
                          )}
                        </>
                      )}
                    </CardContent>
                  </Card>

                  {/* Step 3: Configure Steps */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm">3</span>
                        Configurar Steps
                      </CardTitle>
                      <CardDescription>Monte a sequência de execução dos agentes</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {renderWorkflowEditor()}
                    </CardContent>
                  </Card>

                  {/* Save Button Area */}
                  <div className="flex items-center justify-end gap-4 pt-4 pb-12">
                    <div className="text-sm text-muted-foreground">
                      {validationErrors.length > 0 ? (
                        <span className="text-red-500 flex items-center gap-1">
                          <AlertCircle className="h-4 w-4" />
                          {validationErrors.length} erro(s) impedem o salvamento
                        </span>
                      ) : (
                        <span className="text-green-600 flex items-center gap-1">
                          <CheckCircle2 className="h-4 w-4" />
                          Pronto para salvar
                        </span>
                      )}
                    </div>
                    <Button 
                      size="lg" 
                      onClick={handleSave} 
                      disabled={isSaving} 
                      className="bg-green-600 hover:bg-green-700 min-w-[200px]"
                    >
                      {isSaving ? (
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      ) : (
                        <Save className="w-5 h-5 mr-2" />
                      )}
                      Salvar Workflow
                    </Button>
                  </div>
                </div>
              </div>

              {/* Right: Config Panel */}
              <StudioConfigPanel />
            </div>
          </TabsContent>

          {/* TODO: Canvas Tab (DAG) - Reativar quando suporte a drag-and-drop visual estiver pronto
          <TabsContent value="canvas" className="flex-1 overflow-hidden m-0">
            <div className="flex h-full">
              <StudioSidebar />
              <div className="flex-1 h-full relative">
                <ReactFlowProvider>
                  <StudioFlow />
                </ReactFlowProvider>
              </div>
              <StudioConfigPanel />
            </div>
          </TabsContent>
          */}

          {/* Preview Tab */}
          <TabsContent value="preview" className="flex-1 overflow-hidden m-0">
            <div className="h-full p-6">
              <Card className="h-full">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <FileJson className="h-5 w-5" />
                    worker_config.json
                  </CardTitle>
                </CardHeader>
                <CardContent className="h-[calc(100%-60px)]">
                  <ScrollArea className="h-full">
                    <pre className="text-sm font-mono bg-muted/30 p-4 rounded-lg whitespace-pre-wrap">
                      {previewJson}
                    </pre>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Agent Modal */}
      <AgentFormModal
        open={showAgentModal || editingAgent !== null}
        onOpenChange={(open) => {
          if (!open) {
            setShowAgentModal(false);
            setEditingAgent(null);
          }
        }}
        agent={editingAgent || undefined}
        availableModels={availableModels}
        availableTools={availableTools}
        onSave={handleSaveAgent}
        mode={editingAgent ? "edit" : "create"}
      />
    </div>
  );
}
