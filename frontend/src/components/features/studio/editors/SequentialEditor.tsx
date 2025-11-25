/**
 * SequentialEditor - Editor visual para workflow sequencial
 * Lista ordenável de steps com drag-and-drop
 */

import { useCallback } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
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
import { 
  GripVertical, 
  Plus, 
  Trash2, 
  ArrowRight, 
  Bot
} from "lucide-react";
import type { AgentConfig, WorkflowStep } from "../types";

interface SequentialStep extends WorkflowStep {
  isNew?: boolean;
}

interface SequentialEditorProps {
  steps: SequentialStep[];
  agents: AgentConfig[];
  onStepsChange: (steps: SequentialStep[]) => void;
  onCreateAgent?: () => void;
}

interface SortableStepProps {
  step: SequentialStep;
  index: number;
  agents: AgentConfig[];
  onUpdate: (id: string, updates: Partial<SequentialStep>) => void;
  onDelete: (id: string) => void;
}

function SortableStep({ step, index, agents, onUpdate, onDelete }: SortableStepProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: step.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const selectedAgent = agents.find((a) => a.id === step.agent);

  return (
    <div ref={setNodeRef} style={style} className="flex items-center gap-2">
      {/* Drag Handle */}
      <button
        {...attributes}
        {...listeners}
        className="p-2 cursor-grab hover:bg-muted rounded active:cursor-grabbing"
      >
        <GripVertical className="h-4 w-4 text-muted-foreground" />
      </button>

      {/* Step Number */}
      <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-medium">
        {index + 1}
      </div>

      {/* Step Card */}
      <Card className="flex-1 border-l-4 border-l-blue-500">
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-3">
              {/* Agent Selector */}
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Agente</Label>
                <Select
                  value={step.agent || ""}
                  onValueChange={(val) => onUpdate(step.id, { agent: val })}
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

              {/* Input Template */}
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Input Template</Label>
                <Input
                  value={step.input_template || ""}
                  onChange={(e) => onUpdate(step.id, { input_template: e.target.value })}
                  placeholder="{{user_input}} ou {{previous_output}}"
                  className="font-mono text-sm"
                />
              </div>

              {/* Agent Info */}
              {selectedAgent && (
                <div className="text-xs text-muted-foreground bg-muted/50 rounded p-2">
                  <span className="font-medium">{selectedAgent.role}</span>
                  {selectedAgent.description && (
                    <span> - {selectedAgent.description}</span>
                  )}
                </div>
              )}
            </div>

            {/* Actions */}
            <Button
              variant="ghost"
              size="icon"
              className="text-red-500 hover:text-red-600 hover:bg-red-50"
              onClick={() => onDelete(step.id)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Arrow to next */}
      <ArrowRight className="h-5 w-5 text-muted-foreground shrink-0" />
    </div>
  );
}

export function SequentialEditor({
  steps,
  agents,
  onStepsChange,
  onCreateAgent,
}: SequentialEditorProps) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;

      if (over && active.id !== over.id) {
        const oldIndex = steps.findIndex((s) => s.id === active.id);
        const newIndex = steps.findIndex((s) => s.id === over.id);
        onStepsChange(arrayMove(steps, oldIndex, newIndex));
      }
    },
    [steps, onStepsChange]
  );

  const handleAddStep = () => {
    const newStep: SequentialStep = {
      id: `step_${Date.now()}`,
      type: "agent",
      agent: agents[0]?.id || "",
      input_template: steps.length === 0 ? "{{user_input}}" : "{{previous_output}}",
      isNew: true,
    };
    onStepsChange([...steps, newStep]);
  };

  const handleUpdateStep = (id: string, updates: Partial<SequentialStep>) => {
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
          <h3 className="text-lg font-semibold">Workflow Sequencial</h3>
          <p className="text-sm text-muted-foreground">
            Arraste para reordenar. Cada agente processa e passa para o próximo.
          </p>
        </div>
        {onCreateAgent && (
          <Button variant="outline" size="sm" onClick={onCreateAgent}>
            <Plus className="h-4 w-4 mr-2" />
            Novo Agente
          </Button>
        )}
      </div>

      {/* Steps List */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={steps.map((s) => s.id)} strategy={verticalListSortingStrategy}>
          <div className="space-y-3">
            {steps.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="p-8 text-center">
                  <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground mb-4">
                    Nenhum step adicionado ainda. Adicione o primeiro agente ao workflow.
                  </p>
                  <Button onClick={handleAddStep}>
                    <Plus className="h-4 w-4 mr-2" />
                    Adicionar Primeiro Step
                  </Button>
                </CardContent>
              </Card>
            ) : (
              steps.map((step, index) => (
                <SortableStep
                  key={step.id}
                  step={step}
                  index={index}
                  agents={agents}
                  onUpdate={handleUpdateStep}
                  onDelete={handleDeleteStep}
                />
              ))
            )}
          </div>
        </SortableContext>
      </DndContext>

      {/* Add Step Button */}
      {steps.length > 0 && (
        <Button variant="outline" className="w-full" onClick={handleAddStep}>
          <Plus className="h-4 w-4 mr-2" />
          Adicionar Step
        </Button>
      )}

      {/* Preview */}
      {steps.length > 0 && (
        <Card className="bg-muted/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Preview do Fluxo</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 flex-wrap">
              {steps.map((step, index) => {
                const agent = agents.find((a) => a.id === step.agent);
                return (
                  <div key={step.id} className="flex items-center gap-2">
                    <Badge variant="secondary" className="py-1.5">
                      {agent?.role || step.agent || "?"}
                    </Badge>
                    {index < steps.length - 1 && (
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
