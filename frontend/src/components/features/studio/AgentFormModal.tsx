/**
 * AgentFormModal - Modal completo para criar/editar agentes
 * Campos: id, role, model, instructions, tools, description
 */

import { useState, useEffect, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Bot, Code, Save, Eye } from "lucide-react";
import type { AgentConfig, ToolConfig, ModelConfig } from "./types";

interface AgentFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agent?: AgentConfig;
  availableModels: Record<string, ModelConfig>;
  availableTools: ToolConfig[];
  onSave: (agent: AgentConfig) => void;
  mode?: "create" | "edit";
}

// Gerar ID único baseado no role
function generateAgentId(role: string): string {
  const slug = role
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
  return slug || `agent_${Date.now()}`;
}

export function AgentFormModal({
  open,
  onOpenChange,
  agent,
  availableModels,
  availableTools,
  onSave,
  mode = "create",
}: AgentFormModalProps) {
  const [formData, setFormData] = useState<Partial<AgentConfig>>({
    id: "",
    role: "",
    description: "",
    model: Object.keys(availableModels)[0] || "gpt-4o",
    instructions: "You are a helpful assistant.",
    tools: [],
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState("form");

  // Sincronizar com agent prop quando abrir em modo edição
  useEffect(() => {
    if (open && agent) {
      setFormData({ ...agent });
    } else if (open && !agent) {
      setFormData({
        id: "",
        role: "",
        description: "",
        model: Object.keys(availableModels)[0] || "gpt-4o",
        instructions: "You are a helpful assistant.",
        tools: [],
      });
    }
    setErrors({});
  }, [open, agent, availableModels]);

  // Auto-gerar ID quando role mudar (apenas em modo criação)
  useEffect(() => {
    if (mode === "create" && formData.role) {
      setFormData((prev) => ({
        ...prev,
        id: generateAgentId(formData.role || ""),
      }));
    }
  }, [formData.role, mode]);

  const handleToolToggle = (toolId: string) => {
    setFormData((prev) => {
      const currentTools = prev.tools || [];
      const newTools = currentTools.includes(toolId)
        ? currentTools.filter((t) => t !== toolId)
        : [...currentTools, toolId];
      return { ...prev, tools: newTools };
    });
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.id?.trim()) {
      newErrors.id = "ID é obrigatório";
    }
    if (!formData.role?.trim()) {
      newErrors.role = "Role é obrigatório";
    }
    if (!formData.model?.trim()) {
      newErrors.model = "Modelo é obrigatório";
    }
    if (!formData.instructions?.trim()) {
      newErrors.instructions = "Instruções são obrigatórias";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validate()) return;

    onSave({
      id: formData.id!,
      role: formData.role!,
      description: formData.description,
      model: formData.model!,
      instructions: formData.instructions!,
      tools: formData.tools || [],
    });
    onOpenChange(false);
  };

  // Preview do JSON gerado
  const jsonPreview = useMemo(() => {
    return JSON.stringify(
      {
        id: formData.id || "<id>",
        role: formData.role || "<role>",
        description: formData.description || undefined,
        model: formData.model || "<model>",
        instructions: formData.instructions || "<instructions>",
        tools: formData.tools || [],
      },
      null,
      2
    );
  }, [formData]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col p-6 border-2">
        <DialogHeader className="pb-4 border-b">
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            {mode === "create" ? "Criar Novo Agente" : "Editar Agente"}
          </DialogTitle>
          <DialogClose onClose={() => onOpenChange(false)} />
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="form" className="gap-2">
              <Bot className="h-4 w-4" />
              Configuração
            </TabsTrigger>
            <TabsTrigger value="preview" className="gap-2">
              <Eye className="h-4 w-4" />
              Preview JSON
            </TabsTrigger>
          </TabsList>

          <TabsContent value="form" className="flex-1 overflow-hidden mt-4">
            <ScrollArea className="h-[350px] pr-4">
              <div className="space-y-5 pb-4">
                {/* ID e Role */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="role">
                      Role <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="role"
                      placeholder="Ex: Customer Support Agent"
                      value={formData.role || ""}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, role: e.target.value }))
                      }
                      className={errors.role ? "border-red-500" : ""}
                    />
                    {errors.role && (
                      <p className="text-xs text-red-500">{errors.role}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="id">
                      ID <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="id"
                      placeholder="customer_support_agent"
                      value={formData.id || ""}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, id: e.target.value }))
                      }
                      className={errors.id ? "border-red-500" : ""}
                      disabled={mode === "edit"}
                    />
                    {errors.id && (
                      <p className="text-xs text-red-500">{errors.id}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      Identificador único (gerado automaticamente)
                    </p>
                  </div>
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <Label htmlFor="description">Descrição (para orquestração)</Label>
                  <Textarea
                    id="description"
                    placeholder="Agente especializado em atendimento ao cliente..."
                    value={formData.description || ""}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, description: e.target.value }))
                    }
                    className="min-h-[60px]"
                  />
                  <p className="text-xs text-muted-foreground">
                    Usado pelo orquestrador para entender as capacidades do agente
                  </p>
                </div>

                {/* Model */}
                <div className="space-y-2">
                  <Label>
                    Modelo <span className="text-red-500">*</span>
                  </Label>
                  <Select
                    value={formData.model || ""}
                    onValueChange={(val) =>
                      setFormData((prev) => ({ ...prev, model: val }))
                    }
                  >
                    <SelectTrigger className={errors.model ? "border-red-500" : ""}>
                      <SelectValue placeholder="Selecione o modelo" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(availableModels).map(([id, config]) => (
                        <SelectItem key={id} value={id}>
                          <div className="flex items-center gap-2">
                            <span>{id}</span>
                            <Badge variant="outline" className="text-[10px]">
                              {config.type}
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
                      {Object.keys(availableModels).length === 0 && (
                        <SelectItem value="gpt-4o">gpt-4o (default)</SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                  {errors.model && (
                    <p className="text-xs text-red-500">{errors.model}</p>
                  )}
                </div>

                {/* Instructions */}
                <div className="space-y-2">
                  <Label htmlFor="instructions">
                    Instruções <span className="text-red-500">*</span>
                  </Label>
                  <Textarea
                    id="instructions"
                    placeholder="You are a helpful assistant that..."
                    value={formData.instructions || ""}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, instructions: e.target.value }))
                    }
                    className={`min-h-[150px] font-mono text-sm ${
                      errors.instructions ? "border-red-500" : ""
                    }`}
                  />
                  {errors.instructions && (
                    <p className="text-xs text-red-500">{errors.instructions}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    System prompt do agente. Suporta Markdown.
                  </p>
                </div>

                {/* Tools */}
                <div className="space-y-2">
                  <Label>Ferramentas</Label>
                  <div className="border rounded-lg p-4 max-h-[200px] overflow-y-auto">
                    {availableTools.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        Nenhuma ferramenta disponível. Adicione ferramentas em Recursos.
                      </p>
                    ) : (
                      <div className="space-y-3">
                        {availableTools.map((tool) => (
                          <div
                            key={tool.id}
                            className="flex items-start gap-3 p-2 rounded hover:bg-muted/50"
                          >
                            <Checkbox
                              id={`tool-${tool.id}`}
                              checked={(formData.tools || []).includes(tool.id)}
                              onCheckedChange={() => handleToolToggle(tool.id)}
                            />
                            <div className="flex-1">
                              <Label
                                htmlFor={`tool-${tool.id}`}
                                className="font-medium cursor-pointer"
                              >
                                {tool.id}
                              </Label>
                              {tool.description && (
                                <p className="text-xs text-muted-foreground mt-0.5">
                                  {tool.description}
                                </p>
                              )}
                              <code className="text-[10px] text-muted-foreground">
                                {tool.path}
                              </code>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="preview" className="flex-1 overflow-hidden mt-4">
            <div className="h-[400px] border rounded-lg bg-muted/30">
              <div className="flex items-center gap-2 px-3 py-2 border-b bg-muted/50">
                <Code className="h-4 w-4" />
                <span className="text-sm font-medium">agent.json</span>
              </div>
              <ScrollArea className="h-[calc(100%-40px)]">
                <pre className="p-4 text-sm font-mono whitespace-pre-wrap">
                  {jsonPreview}
                </pre>
              </ScrollArea>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSave} className="gap-2">
            <Save className="h-4 w-4" />
            {mode === "create" ? "Criar Agente" : "Salvar Alterações"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
