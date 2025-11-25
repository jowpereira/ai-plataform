/**
 * GroupChatEditor - Editor visual para workflow de chat em grupo
 * Multi-agente coordenado por um Manager
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  Plus, 
  Trash2, 
  Users, 
  Bot,
  Crown
} from "lucide-react";
import type { AgentConfig, WorkflowStep, ModelConfig } from "../types";

interface GroupChatConfig {
  manager_model: string;
  manager_instructions: string;
  max_rounds: number;
  termination_condition?: string;
}

interface GroupChatEditorProps {
  steps: WorkflowStep[];
  agents: AgentConfig[];
  availableModels: Record<string, ModelConfig>;
  config: GroupChatConfig;
  onStepsChange: (steps: WorkflowStep[]) => void;
  onConfigChange: (config: GroupChatConfig) => void;
  onCreateAgent?: () => void;
}

export function GroupChatEditor({
  steps,
  agents,
  availableModels,
  config,
  onStepsChange,
  onConfigChange,
  onCreateAgent,
}: GroupChatEditorProps) {
  const handleAddParticipant = () => {
    const newStep: WorkflowStep = {
      id: `participant_${Date.now()}`,
      type: "agent",
      agent: agents[0]?.id || "",
      input_template: "{{user_input}}",
    };
    onStepsChange([...steps, newStep]);
  };

  const handleUpdateStep = (id: string, updates: Partial<WorkflowStep>) => {
    onStepsChange(
      steps.map((s) => (s.id === id ? { ...s, ...updates } : s))
    );
  };

  const handleDeleteStep = (id: string) => {
    onStepsChange(steps.filter((s) => s.id !== id));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Group Chat</h3>
          <p className="text-sm text-muted-foreground">
            Discussão multi-agente coordenada por um Manager central.
          </p>
        </div>
        {onCreateAgent && (
          <Button variant="outline" size="sm" onClick={onCreateAgent}>
            <Plus className="h-4 w-4 mr-2" />
            Novo Agente
          </Button>
        )}
      </div>

      {/* Manager Configuration */}
      <Card className="border-2 border-amber-500">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Crown className="h-5 w-5 text-amber-500" />
            Manager (Coordenador)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Modelo do Manager</Label>
              <Select
                value={config.manager_model}
                onValueChange={(val) =>
                  onConfigChange({ ...config, manager_model: val })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione o modelo" />
                </SelectTrigger>
                <SelectContent>
                  {Object.keys(availableModels).map((modelId) => (
                    <SelectItem key={modelId} value={modelId}>
                      {modelId}
                    </SelectItem>
                  ))}
                  {Object.keys(availableModels).length === 0 && (
                    <SelectItem value="gpt-4o">gpt-4o</SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Máximo de Rodadas</Label>
              <Input
                type="number"
                min={1}
                max={50}
                value={config.max_rounds}
                onChange={(e) =>
                  onConfigChange({
                    ...config,
                    max_rounds: parseInt(e.target.value) || 8,
                  })
                }
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Instruções do Manager</Label>
            <Textarea
              value={config.manager_instructions}
              onChange={(e) =>
                onConfigChange({ ...config, manager_instructions: e.target.value })
              }
              placeholder="Instruções para o manager selecionar o próximo speaker..."
              className="min-h-[100px] font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground">
              Define como o manager escolhe qual agente fala a seguir
            </p>
          </div>

          <div className="space-y-2">
            <Label>Condição de Término (opcional)</Label>
            <Input
              value={config.termination_condition || ""}
              onChange={(e) =>
                onConfigChange({ ...config, termination_condition: e.target.value })
              }
              placeholder="Ex: 'TERMINATE' quando concluído"
              className="font-mono text-sm"
            />
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Participants */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            <h4 className="font-medium">Participantes</h4>
            <Badge variant="secondary">{steps.length}</Badge>
          </div>
        </div>

        {/* Visual Circle Layout */}
        <div className="relative min-h-[300px] border rounded-lg bg-muted/20 p-8">
          {/* Manager in center */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
            <div className="w-20 h-20 rounded-full bg-amber-100 border-2 border-amber-500 flex items-center justify-center">
              <Crown className="h-8 w-8 text-amber-600" />
            </div>
            <p className="text-center text-xs mt-2 font-medium">Manager</p>
          </div>

          {/* Participants around */}
          {steps.map((step, index) => {
            const angle = (index * 360) / Math.max(steps.length, 1) - 90;
            const radius = 120;
            const x = Math.cos((angle * Math.PI) / 180) * radius;
            const y = Math.sin((angle * Math.PI) / 180) * radius;
            const agent = agents.find((a) => a.id === step.agent);

            return (
              <div
                key={step.id}
                className="absolute transform -translate-x-1/2 -translate-y-1/2"
                style={{
                  left: `calc(50% + ${x}px)`,
                  top: `calc(50% + ${y}px)`,
                }}
              >
                <div className="w-16 h-16 rounded-full bg-blue-100 border-2 border-blue-500 flex items-center justify-center cursor-pointer hover:bg-blue-200 transition-colors group">
                  <Bot className="h-6 w-6 text-blue-600" />
                  <button
                    className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                    onClick={() => handleDeleteStep(step.id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
                <p className="text-center text-xs mt-1 max-w-[80px] truncate">
                  {agent?.role || "?"}
                </p>
              </div>
            );
          })}
        </div>

        {/* Participants List */}
        <div className="space-y-2">
          {steps.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="p-6 text-center">
                <Users className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground mb-3">
                  Adicione participantes ao chat em grupo
                </p>
                <Button size="sm" onClick={handleAddParticipant}>
                  <Plus className="h-4 w-4 mr-2" />
                  Adicionar Participante
                </Button>
              </CardContent>
            </Card>
          ) : (
            <>
              {steps.map((step, index) => {
                const agent = agents.find((a) => a.id === step.agent);
                return (
                  <Card key={step.id}>
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between gap-3">
                        <Badge variant="outline">{index + 1}</Badge>
                        <Select
                          value={step.agent || ""}
                          onValueChange={(val) => handleUpdateStep(step.id, { agent: val })}
                        >
                          <SelectTrigger className="flex-1">
                            <SelectValue placeholder="Selecione" />
                          </SelectTrigger>
                          <SelectContent>
                            {agents.map((a) => (
                              <SelectItem key={a.id} value={a.id}>
                                <div className="flex items-center gap-2">
                                  <Bot className="h-4 w-4" />
                                  {a.role}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {agent && (
                          <span className="text-xs text-muted-foreground truncate max-w-[150px]">
                            {agent.description || agent.model}
                          </span>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-red-500 hover:text-red-600"
                          onClick={() => handleDeleteStep(step.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
              <Button
                variant="outline"
                className="w-full"
                onClick={handleAddParticipant}
              >
                <Plus className="h-4 w-4 mr-2" />
                Adicionar Participante
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
