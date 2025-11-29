/**
 * MagenticEditor - Editor visual para workflow Magentic One
 * 
 * Magentic One é um orquestrador AI-driven que:
 * - Analisa a tarefa e extrai fatos relevantes
 * - Cria um plano de execução dinâmico
 * - Seleciona agentes baseado no progresso
 * - Replana quando encontra obstáculos
 * 
 * Campos específicos:
 * - manager_model (obrigatório): Modelo do orquestrador
 * - max_rounds: Limite de iterações (default: 20)
 * - max_stall_count: Limite de stalls antes de falhar (default: 3)
 * - enable_plan_review: Permite revisão humana do plano
 * - manager_instructions: Instruções customizadas para o orquestrador
 */

import { useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { 
  Plus, 
  Trash2, 
  Bot,
  Sparkles,
  Settings2,
  Info,
  Users,
  Brain,
} from "lucide-react";
import type { AgentConfig, WorkflowStep, ModelConfig } from "../types";

interface MagenticConfig {
  manager_model: string;
  manager_instructions: string;
  max_rounds: number;
  max_stall_count: number;
  enable_plan_review: boolean;
}

interface MagenticEditorProps {
  steps: WorkflowStep[];
  agents: AgentConfig[];
  availableModels: Record<string, ModelConfig>;
  config: MagenticConfig;
  onStepsChange: (steps: WorkflowStep[]) => void;
  onConfigChange: (config: MagenticConfig) => void;
  onCreateAgent?: () => void;
}

export function MagenticEditor({
  steps,
  agents,
  availableModels,
  config,
  onStepsChange,
  onConfigChange,
  onCreateAgent,
}: MagenticEditorProps) {
  const modelKeys = Object.keys(availableModels);

  // Handlers para config
  const handleConfigUpdate = useCallback(
    (updates: Partial<MagenticConfig>) => {
      onConfigChange({ ...config, ...updates });
    },
    [config, onConfigChange]
  );

  // Handlers para participantes
  const handleAddParticipant = useCallback(() => {
    const newStep: WorkflowStep = {
      id: `step_${Date.now()}`,
      type: "agent",
      agent: agents[0]?.id || "",
      input_template: "{{context}}",
    };
    onStepsChange([...steps, newStep]);
  }, [steps, agents, onStepsChange]);

  const handleUpdateParticipant = useCallback(
    (id: string, updates: Partial<WorkflowStep>) => {
      onStepsChange(steps.map((s) => (s.id === id ? { ...s, ...updates } : s)));
    },
    [steps, onStepsChange]
  );

  const handleRemoveParticipant = useCallback(
    (id: string) => {
      onStepsChange(steps.filter((s) => s.id !== id));
    },
    [steps, onStepsChange]
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold">Magentic One</h3>
            <p className="text-sm text-muted-foreground">
              Orquestração AI-driven com planejamento dinâmico
            </p>
          </div>
        </div>
        {onCreateAgent && (
          <Button variant="outline" size="sm" onClick={onCreateAgent}>
            <Plus className="h-4 w-4 mr-2" />
            Novo Agente
          </Button>
        )}
      </div>

      {/* Explicação do tipo */}
      <Card className="bg-gradient-to-r from-violet-50 to-purple-50 dark:from-violet-950/20 dark:to-purple-950/20 border-violet-200 dark:border-violet-800">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Brain className="h-5 w-5 text-violet-600 dark:text-violet-400 shrink-0 mt-0.5" />
            <div className="text-sm text-violet-700 dark:text-violet-300">
              <p className="font-medium mb-1">Como funciona o Magentic One?</p>
              <ul className="list-disc list-inside space-y-0.5 text-violet-600 dark:text-violet-400">
                <li>O <strong>Manager</strong> analisa a tarefa e cria um plano</li>
                <li>Seleciona dinamicamente qual agente deve executar</li>
                <li>Monitora progresso e replana quando necessário</li>
                <li>Ideal para tarefas complexas com múltiplos especialistas</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Configuração do Manager */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Settings2 className="h-4 w-4" />
            Configuração do Manager (Orquestrador)
          </CardTitle>
          <CardDescription>
            O Manager é o LLM responsável por planejar e coordenar a execução
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Manager Model */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              Modelo do Manager *
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-3.5 w-3.5 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent side="right" className="max-w-xs">
                    <p>O modelo responsável por criar planos, selecionar agentes e coordenar a execução. Recomenda-se modelos mais capazes (ex: gpt-4o).</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </Label>
            <Select
              value={config.manager_model}
              onValueChange={(val) => handleConfigUpdate({ manager_model: val })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione o modelo do manager" />
              </SelectTrigger>
              <SelectContent>
                {modelKeys.map((modelId) => (
                  <SelectItem key={modelId} value={modelId}>
                    {modelId}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {!config.manager_model && (
              <p className="text-xs text-red-500">⚠️ Modelo do manager é obrigatório</p>
            )}
          </div>

          {/* Manager Instructions */}
          <div className="space-y-2">
            <Label>Instruções do Manager</Label>
            <Textarea
              value={config.manager_instructions || ""}
              onChange={(e) => handleConfigUpdate({ manager_instructions: e.target.value })}
              placeholder="Você é o coordenador de uma equipe de especialistas. Analise a tarefa, crie um plano de execução e coordene os participantes para alcançar o objetivo de forma eficiente."
              rows={3}
              className="text-sm"
            />
          </div>

          {/* Parâmetros de controle */}
          <div className="grid grid-cols-2 gap-4">
            {/* Max Rounds */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                Max Rounds
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-3.5 w-3.5 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent side="right" className="max-w-xs">
                      <p>Número máximo de iterações. Aumentar para tarefas complexas.</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </Label>
              <Input
                type="number"
                min={5}
                max={100}
                value={config.max_rounds}
                onChange={(e) => handleConfigUpdate({ max_rounds: parseInt(e.target.value, 10) || 20 })}
              />
            </div>

            {/* Max Stall Count */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                Max Stall Count
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-3.5 w-3.5 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent side="right" className="max-w-xs">
                      <p>Número de iterações sem progresso antes de falhar. Evita loops infinitos.</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </Label>
              <Input
                type="number"
                min={1}
                max={10}
                value={config.max_stall_count}
                onChange={(e) => handleConfigUpdate({ max_stall_count: parseInt(e.target.value, 10) || 3 })}
              />
            </div>
          </div>

          {/* Enable Plan Review */}
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <Label>Revisão de Plano (Human-in-the-Loop)</Label>
              <p className="text-xs text-muted-foreground">
                Permite revisar e aprovar o plano antes da execução
              </p>
            </div>
            <Switch
              checked={config.enable_plan_review}
              onCheckedChange={(val) => handleConfigUpdate({ enable_plan_review: val })}
            />
          </div>
        </CardContent>
      </Card>

      {/* Participantes */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Users className="h-4 w-4" />
                Participantes ({steps.length})
              </CardTitle>
              <CardDescription>
                Agentes disponíveis para o Manager coordenar
              </CardDescription>
            </div>
            <Button size="sm" onClick={handleAddParticipant}>
              <Plus className="h-4 w-4 mr-2" />
              Adicionar
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {steps.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg">
              <Bot className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="mb-2">Nenhum participante adicionado</p>
              <p className="text-sm">Adicione pelo menos 2 agentes para o Manager coordenar</p>
              <Button variant="outline" size="sm" className="mt-4" onClick={handleAddParticipant}>
                <Plus className="h-4 w-4 mr-2" />
                Adicionar Primeiro Participante
              </Button>
            </div>
          ) : (
            <>
              {steps.map((step, index) => {
                const selectedAgent = agents.find((a) => a.id === step.agent);
                return (
                  <div
                    key={step.id}
                    className="flex items-center gap-3 p-3 rounded-lg border bg-card"
                  >
                    <div className="w-8 h-8 rounded-full bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center text-violet-600 dark:text-violet-400 text-sm font-medium">
                      {index + 1}
                    </div>
                    
                    <div className="flex-1">
                      <Select
                        value={step.agent || ""}
                        onValueChange={(val) => handleUpdateParticipant(step.id, { agent: val })}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Selecione um agente" />
                        </SelectTrigger>
                        <SelectContent>
                          {agents.map((agent) => (
                            <SelectItem key={agent.id} value={agent.id}>
                              <div className="flex items-center gap-2">
                                <Bot className="h-4 w-4" />
                                <span>{agent.role}</span>
                                <Badge variant="outline" className="text-[10px]">
                                  {agent.model}
                                </Badge>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {selectedAgent && (
                      <p className="text-xs text-muted-foreground max-w-[200px] truncate">
                        {selectedAgent.description}
                      </p>
                    )}

                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                      onClick={() => handleRemoveParticipant(step.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                );
              })}

              {/* Aviso para poucos participantes */}
              {steps.length < 2 && (
                <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
                  <Info className="h-3.5 w-3.5" />
                  Recomenda-se pelo menos 2 participantes para melhor aproveitamento
                </p>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Preview dos participantes */}
      {steps.length > 0 && (
        <Card className="bg-muted/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-violet-500" />
              Equipe do Magentic
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="secondary" className="py-1.5 bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300">
                🧠 Manager ({config.manager_model || "?"})
              </Badge>
              <span className="text-muted-foreground">coordena:</span>
              {steps.map((step) => {
                const agent = agents.find((a) => a.id === step.agent);
                return (
                  <Badge key={step.id} variant="outline" className="py-1.5">
                    {agent?.role || step.agent || "?"}
                  </Badge>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
