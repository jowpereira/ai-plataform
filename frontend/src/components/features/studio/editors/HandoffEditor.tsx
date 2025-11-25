/**
 * HandoffEditor - Editor visual para workflow de handoff/triagem
 * Coordenador transfere para especialistas
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
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
  ArrowRightLeft, 
  Bot,
  Shield,
  ArrowRight
} from "lucide-react";
import type { AgentConfig, WorkflowStep } from "../types";

interface HandoffStep extends WorkflowStep {
  isCoordinator?: boolean;
}

interface HandoffEditorProps {
  steps: HandoffStep[];
  agents: AgentConfig[];
  startStep?: string;
  onStepsChange: (steps: HandoffStep[]) => void;
  onStartStepChange: (stepId: string) => void;
  onCreateAgent?: () => void;
}

export function HandoffEditor({
  steps,
  agents,
  startStep,
  onStepsChange,
  onStartStepChange,
  onCreateAgent,
}: HandoffEditorProps) {
  const coordinatorStep = steps.find((s) => s.id === startStep);
  const specialistSteps = steps.filter((s) => s.id !== startStep);

  const handleSetCoordinator = (agentId: string) => {
    // Verificar se já existe um step para este agente
    const existingStep = steps.find((s) => s.agent === agentId);
    
    if (existingStep) {
      onStartStepChange(existingStep.id);
    } else {
      // Criar novo step de coordenador
      const newStep: HandoffStep = {
        id: `coordinator_${Date.now()}`,
        type: "agent",
        agent: agentId,
        input_template: "{{user_input}}",
        transitions: specialistSteps.map((s) => s.id),
        isCoordinator: true,
      };
      onStepsChange([newStep, ...steps.filter((s) => !s.isCoordinator)]);
      onStartStepChange(newStep.id);
    }
  };

  const handleAddSpecialist = () => {
    const newStep: HandoffStep = {
      id: `specialist_${Date.now()}`,
      type: "agent",
      agent: agents[0]?.id || "",
      input_template: "{{user_input}}",
    };
    
    // Atualizar transitions do coordenador
    const updatedSteps = steps.map((s) => {
      if (s.id === startStep) {
        return {
          ...s,
          transitions: [...(s.transitions || []), newStep.id],
        };
      }
      return s;
    });
    
    onStepsChange([...updatedSteps, newStep]);
  };

  const handleUpdateStep = (id: string, updates: Partial<HandoffStep>) => {
    onStepsChange(
      steps.map((s) => (s.id === id ? { ...s, ...updates } : s))
    );
  };

  const handleDeleteSpecialist = (id: string) => {
    // Remover das transitions do coordenador
    const updatedSteps = steps
      .filter((s) => s.id !== id)
      .map((s) => {
        if (s.id === startStep && s.transitions) {
          return {
            ...s,
            transitions: s.transitions.filter((t) => t !== id),
          };
        }
        return s;
      });
    onStepsChange(updatedSteps);
  };

  const handleToggleTransition = (specialistId: string, enabled: boolean) => {
    onStepsChange(
      steps.map((s) => {
        if (s.id === startStep) {
          const transitions = s.transitions || [];
          return {
            ...s,
            transitions: enabled
              ? [...transitions, specialistId]
              : transitions.filter((t) => t !== specialistId),
          };
        }
        return s;
      })
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Workflow Handoff</h3>
          <p className="text-sm text-muted-foreground">
            O coordenador analisa e transfere para especialistas.
          </p>
        </div>
        {onCreateAgent && (
          <Button variant="outline" size="sm" onClick={onCreateAgent}>
            <Plus className="h-4 w-4 mr-2" />
            Novo Agente
          </Button>
        )}
      </div>

      {/* Coordinator Selection */}
      <Card className="border-2 border-orange-500">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Shield className="h-5 w-5 text-orange-500" />
            Coordenador (Triagem)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Agente Coordenador</Label>
            <Select
              value={coordinatorStep?.agent || ""}
              onValueChange={handleSetCoordinator}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione o coordenador" />
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
            <p className="text-xs text-muted-foreground">
              O coordenador analisa a entrada e decide para qual especialista transferir
            </p>
          </div>

          {coordinatorStep && (
            <div className="space-y-2">
              <Label>Input Template</Label>
              <Input
                value={coordinatorStep.input_template || ""}
                onChange={(e) =>
                  handleUpdateStep(coordinatorStep.id, { input_template: e.target.value })
                }
                placeholder="{{user_input}}"
                className="font-mono text-sm"
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Separator />

      {/* Specialists */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ArrowRightLeft className="h-5 w-5" />
            <h4 className="font-medium">Especialistas</h4>
            <Badge variant="secondary">{specialistSteps.length}</Badge>
          </div>
        </div>

        {/* Visual Flow */}
        <div className="flex items-start gap-4">
          {/* Coordinator Node */}
          {coordinatorStep && (
            <div className="flex flex-col items-center">
              <div className="w-24 h-24 rounded-full bg-orange-100 border-2 border-orange-500 flex items-center justify-center">
                <Shield className="h-10 w-10 text-orange-600" />
              </div>
              <p className="text-sm font-medium mt-2 text-center max-w-[100px] truncate">
                {agents.find((a) => a.id === coordinatorStep.agent)?.role || "Coordenador"}
              </p>
            </div>
          )}

          {/* Arrows */}
          {coordinatorStep && specialistSteps.length > 0 && (
            <div className="flex flex-col justify-center h-24 gap-2">
              {specialistSteps.map((_, i) => (
                <ArrowRight key={i} className="h-4 w-4 text-muted-foreground" />
              ))}
            </div>
          )}

          {/* Specialists */}
          <div className="flex-1 space-y-3">
            {specialistSteps.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="p-6 text-center">
                  <Bot className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                  <p className="text-sm text-muted-foreground mb-3">
                    Adicione especialistas para receber handoffs
                  </p>
                  <Button size="sm" onClick={handleAddSpecialist}>
                    <Plus className="h-4 w-4 mr-2" />
                    Adicionar Especialista
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <>
                {specialistSteps.map((step) => {
                  const agent = agents.find((a) => a.id === step.agent);
                  const isConnected = coordinatorStep?.transitions?.includes(step.id);
                  
                  return (
                    <Card
                      key={step.id}
                      className={`border-l-4 ${
                        isConnected ? "border-l-green-500" : "border-l-gray-300"
                      }`}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <Checkbox
                              checked={isConnected}
                              onCheckedChange={(checked) =>
                                handleToggleTransition(step.id, !!checked)
                              }
                            />
                            <Select
                              value={step.agent || ""}
                              onValueChange={(val) =>
                                handleUpdateStep(step.id, { agent: val })
                              }
                            >
                              <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="Selecione" />
                              </SelectTrigger>
                              <SelectContent>
                                {agents
                                  .filter((a) => a.id !== coordinatorStep?.agent)
                                  .map((a) => (
                                    <SelectItem key={a.id} value={a.id}>
                                      <div className="flex items-center gap-2">
                                        <Bot className="h-4 w-4" />
                                        {a.role}
                                      </div>
                                    </SelectItem>
                                  ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="flex items-center gap-2">
                            <Input
                              value={step.input_template || ""}
                              onChange={(e) =>
                                handleUpdateStep(step.id, {
                                  input_template: e.target.value,
                                })
                              }
                              placeholder="{{user_input}}"
                              className="w-32 font-mono text-xs"
                            />
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-red-500 hover:text-red-600"
                              onClick={() => handleDeleteSpecialist(step.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        {agent && (
                          <p className="text-xs text-muted-foreground mt-2 ml-9">
                            {agent.description || `Modelo: ${agent.model}`}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleAddSpecialist}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Adicionar Especialista
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Info */}
      <Card className="bg-muted/30">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <ArrowRightLeft className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-medium text-foreground mb-1">Como funciona:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>O coordenador recebe a entrada inicial</li>
                <li>Analisa e decide para qual especialista transferir</li>
                <li>Apenas especialistas marcados podem receber handoffs</li>
                <li>O especialista processa e pode devolver ao coordenador</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
