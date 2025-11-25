/**
 * ParallelEditor - Editor visual para workflow paralelo (fan-out/fan-in)
 * Visualização: Dispatcher → [Agentes paralelos] → Aggregator
 */

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { 
  Plus, 
  Trash2, 
  GitBranch, 
  Bot,
  ArrowRight,
  Layers
} from "lucide-react";
import type { AgentConfig, WorkflowStep } from "../types";

interface ParallelStep extends WorkflowStep {
  isParallel?: boolean;
}

interface ParallelEditorProps {
  steps: ParallelStep[];
  agents: AgentConfig[];
  onStepsChange: (steps: ParallelStep[]) => void;
  onCreateAgent?: () => void;
}

export function ParallelEditor({
  steps,
  agents,
  onStepsChange,
  onCreateAgent,
}: ParallelEditorProps) {
  const handleAddParallelAgent = () => {
    const newStep: ParallelStep = {
      id: `parallel_${Date.now()}`,
      type: "agent",
      agent: agents[0]?.id || "",
      input_template: "{{user_input}}",
      isParallel: true,
    };
    onStepsChange([...steps, newStep]);
  };

  const handleUpdateStep = (id: string, updates: Partial<ParallelStep>) => {
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
          <h3 className="text-lg font-semibold">Workflow Paralelo</h3>
          <p className="text-sm text-muted-foreground">
            Execute múltiplos agentes simultaneamente e agregue os resultados.
          </p>
        </div>
        {onCreateAgent && (
          <Button variant="outline" size="sm" onClick={onCreateAgent}>
            <Plus className="h-4 w-4 mr-2" />
            Novo Agente
          </Button>
        )}
      </div>

      {/* Visual Flow */}
      <div className="flex items-stretch gap-4">
        {/* Dispatcher */}
        <Card className="w-32 border-green-500 border-2 flex flex-col justify-center">
          <CardContent className="p-4 text-center">
            <GitBranch className="h-8 w-8 mx-auto mb-2 text-green-500" />
            <p className="text-sm font-medium">Dispatcher</p>
            <p className="text-xs text-muted-foreground">Fan-out</p>
          </CardContent>
        </Card>

        {/* Arrow */}
        <div className="flex items-center">
          <ArrowRight className="h-6 w-6 text-muted-foreground" />
        </div>

        {/* Parallel Agents */}
        <div className="flex-1 space-y-3">
          {steps.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="p-8 text-center">
                <Bot className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground mb-3">
                  Adicione agentes para execução paralela
                </p>
                <Button size="sm" onClick={handleAddParallelAgent}>
                  <Plus className="h-4 w-4 mr-2" />
                  Adicionar Agente
                </Button>
              </CardContent>
            </Card>
          ) : (
            <>
              {steps.map((step, index) => {
                const agent = agents.find((a) => a.id === step.agent);
                return (
                  <Card key={step.id} className="border-l-4 border-l-blue-500">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                          <Badge variant="outline">{index + 1}</Badge>
                          <Select
                            value={step.agent || ""}
                            onValueChange={(val) => handleUpdateStep(step.id, { agent: val })}
                          >
                            <SelectTrigger className="w-[200px]">
                              <SelectValue placeholder="Selecione" />
                            </SelectTrigger>
                            <SelectContent>
                              {agents.map((a) => (
                                <SelectItem key={a.id} value={a.id}>
                                  {a.role}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          {agent && (
                            <span className="text-xs text-muted-foreground">
                              {agent.description || agent.model}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <Input
                            value={step.input_template || ""}
                            onChange={(e) =>
                              handleUpdateStep(step.id, { input_template: e.target.value })
                            }
                            placeholder="{{user_input}}"
                            className="w-40 font-mono text-xs"
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-red-500 hover:text-red-600"
                            onClick={() => handleDeleteStep(step.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
              <Button
                variant="outline"
                className="w-full"
                onClick={handleAddParallelAgent}
              >
                <Plus className="h-4 w-4 mr-2" />
                Adicionar Agente Paralelo
              </Button>
            </>
          )}
        </div>

        {/* Arrow */}
        <div className="flex items-center">
          <ArrowRight className="h-6 w-6 text-muted-foreground" />
        </div>

        {/* Aggregator */}
        <Card className="w-32 border-purple-500 border-2 flex flex-col justify-center">
          <CardContent className="p-4 text-center">
            <Layers className="h-8 w-8 mx-auto mb-2 text-purple-500" />
            <p className="text-sm font-medium">Aggregator</p>
            <p className="text-xs text-muted-foreground">Fan-in</p>
          </CardContent>
        </Card>
      </div>

      {/* Info */}
      <Card className="bg-muted/30">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <GitBranch className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-medium text-foreground mb-1">Como funciona:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>O Dispatcher distribui a entrada para todos os agentes</li>
                <li>Cada agente processa independentemente em paralelo</li>
                <li>O Aggregator combina todas as respostas no resultado final</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
