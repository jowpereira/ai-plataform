/**
 * RouterEditor - Editor visual para workflow com roteamento condicional
 * Roteador decide para qual destino enviar baseado na saída
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  Plus, 
  Trash2, 
  GitFork, 
  Bot,
  Target,
  ArrowRight,
  Info
} from "lucide-react";
import type { AgentConfig, WorkflowStep } from "../types";

interface RouterStep extends WorkflowStep {
  isRouter?: boolean;
  isDefault?: boolean;
}

interface RouterEditorProps {
  steps: RouterStep[];
  agents: AgentConfig[];
  startStep?: string;
  onStepsChange: (steps: RouterStep[]) => void;
  onStartStepChange: (stepId: string) => void;
  onCreateAgent?: () => void;
}

export function RouterEditor({
  steps,
  agents,
  startStep,
  onStepsChange,
  onStartStepChange,
  onCreateAgent,
}: RouterEditorProps) {
  const routerStep = steps.find((s) => s.id === startStep);
  const destinationSteps = steps.filter((s) => s.id !== startStep);

  const handleSetRouter = (agentId: string) => {
    const existingStep = steps.find((s) => s.agent === agentId);
    
    if (existingStep) {
      onStartStepChange(existingStep.id);
    } else {
      const newStep: RouterStep = {
        id: `router_${Date.now()}`,
        type: "agent",
        agent: agentId,
        input_template: "{{user_input}}",
        isRouter: true,
      };
      onStepsChange([newStep, ...steps.filter((s) => !s.isRouter)]);
      onStartStepChange(newStep.id);
    }
  };

  const handleAddDestination = () => {
    const newStep: RouterStep = {
      id: `destination_${Date.now()}`,
      type: "agent",
      agent: agents[0]?.id || "",
      input_template: "{{user_input}}",
    };
    onStepsChange([...steps, newStep]);
  };

  const handleUpdateStep = (id: string, updates: Partial<RouterStep>) => {
    onStepsChange(
      steps.map((s) => (s.id === id ? { ...s, ...updates } : s))
    );
  };

  const handleDeleteDestination = (id: string) => {
    onStepsChange(steps.filter((s) => s.id !== id));
  };

  const handleMoveToDefault = (id: string) => {
    // Move o step para o final (tornando-o default)
    const step = steps.find((s) => s.id === id);
    if (!step) return;
    
    const otherSteps = steps.filter((s) => s.id !== id);
    onStepsChange([...otherSteps, step]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Workflow Router</h3>
          <p className="text-sm text-muted-foreground">
            O roteador analisa e direciona para o destino apropriado.
          </p>
        </div>
        {onCreateAgent && (
          <Button variant="outline" size="sm" onClick={onCreateAgent}>
            <Plus className="h-4 w-4 mr-2" />
            Novo Agente
          </Button>
        )}
      </div>

      {/* Router Agent Selection */}
      <Card className="border-2 border-cyan-500">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <GitFork className="h-5 w-5 text-cyan-500" />
            Agente Roteador
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Selecione o Agente Roteador</Label>
            <Select
              value={routerStep?.agent || ""}
              onValueChange={handleSetRouter}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione o roteador" />
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

          {routerStep && (
            <div className="space-y-2">
              <Label>Input Template</Label>
              <Input
                value={routerStep.input_template || ""}
                onChange={(e) =>
                  handleUpdateStep(routerStep.id, { input_template: e.target.value })
                }
                placeholder="{{user_input}}"
                className="font-mono text-sm"
              />
            </div>
          )}

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription className="text-xs">
              O agente roteador deve retornar o <strong>ID exato</strong> do destino.
              <br />
              Exemplo: Se o destino tem ID "vendas", o roteador deve responder "vendas".
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Separator />

      {/* Destinations */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            <h4 className="font-medium">Destinos</h4>
            <Badge variant="secondary">{destinationSteps.length}</Badge>
          </div>
        </div>

        {/* Visual Flow */}
        <div className="flex items-start gap-4">
          {/* Router Node */}
          {routerStep && (
            <div className="flex flex-col items-center shrink-0">
              <div className="w-24 h-24 rounded-lg bg-cyan-100 border-2 border-cyan-500 flex items-center justify-center">
                <GitFork className="h-10 w-10 text-cyan-600" />
              </div>
              <p className="text-sm font-medium mt-2 text-center max-w-[100px] truncate">
                {agents.find((a) => a.id === routerStep.agent)?.role || "Router"}
              </p>
            </div>
          )}

          {/* Conditional Arrows */}
          {routerStep && destinationSteps.length > 0 && (
            <div className="flex flex-col justify-center min-h-[96px] gap-1">
              {destinationSteps.map((step) => (
                <div key={step.id} className="flex items-center gap-1">
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  <code className="text-[10px] bg-muted px-1 rounded">
                    {step.agent || step.id}
                  </code>
                </div>
              ))}
            </div>
          )}

          {/* Destinations List */}
          <div className="flex-1 space-y-2">
            {destinationSteps.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="p-6 text-center">
                  <Target className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                  <p className="text-sm text-muted-foreground mb-3">
                    Adicione destinos para o roteamento
                  </p>
                  <Button size="sm" onClick={handleAddDestination}>
                    <Plus className="h-4 w-4 mr-2" />
                    Adicionar Destino
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <>
                {destinationSteps.map((step, index) => {
                  const agent = agents.find((a) => a.id === step.agent);
                  const isLast = index === destinationSteps.length - 1;
                  
                  return (
                    <Card
                      key={step.id}
                      className={`border-l-4 ${
                        isLast
                          ? "border-l-amber-500 bg-amber-50/50 dark:bg-amber-950/20"
                          : "border-l-green-500"
                      }`}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <Badge
                              variant={isLast ? "default" : "outline"}
                              className={isLast ? "bg-amber-500" : ""}
                            >
                              {isLast ? "Default" : `Case ${index + 1}`}
                            </Badge>
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
                                  .filter((a) => a.id !== routerStep?.agent)
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
                            {!isLast && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-xs"
                                onClick={() => handleMoveToDefault(step.id)}
                              >
                                Tornar Default
                              </Button>
                            )}
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
                              onClick={() => handleDeleteDestination(step.id)}
                              disabled={destinationSteps.length <= 1}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        {agent && (
                          <p className="text-xs text-muted-foreground mt-2 ml-20">
                            Roteador retorna: <code className="bg-muted px-1 rounded">{agent.id}</code>
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleAddDestination}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Adicionar Destino
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
            <GitFork className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-medium text-foreground mb-1">Como funciona:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>O roteador recebe a entrada e analisa</li>
                <li>Deve retornar o ID do agente de destino</li>
                <li>Se nenhum case corresponder, usa o Default</li>
                <li>O último destino na lista é sempre o Default</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
