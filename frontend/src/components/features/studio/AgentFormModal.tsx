/**
 * AgentFormModal - Modal completo para criar/editar agentes
 * Campos: id, role, model, instructions, tools, description, knowledge
 */

import { useState, useEffect, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
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
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Bot, Code, Save, Eye, Database, Wrench, Brain, Info, Minus, Plus } from "lucide-react";
import type { AgentConfig, ToolConfig, ModelConfig, AgentKnowledgeConfig } from "./types";
import type { KnowledgeCollection } from "@/services/api";

interface AgentFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agent?: AgentConfig;
  availableModels: Record<string, ModelConfig>;
  availableTools: ToolConfig[];
  availableCollections?: KnowledgeCollection[];
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

const DEFAULT_KNOWLEDGE: AgentKnowledgeConfig = {
  enabled: false,
  collection_ids: [],
  top_k: 5,
  min_score: 0.25,
};

export function AgentFormModal({
  open,
  onOpenChange,
  agent,
  availableModels,
  availableTools,
  availableCollections = [],
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
    knowledge: DEFAULT_KNOWLEDGE,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState("basic");

  // Sincronizar com agent prop quando abrir em modo edição
  useEffect(() => {
    if (open && agent) {
      setFormData({ 
        ...agent,
        knowledge: agent.knowledge || DEFAULT_KNOWLEDGE,
      });
    } else if (open && !agent) {
      setFormData({
        id: "",
        role: "",
        description: "",
        model: Object.keys(availableModels)[0] || "gpt-4o",
        instructions: "You are a helpful assistant.",
        tools: [],
        knowledge: DEFAULT_KNOWLEDGE,
      });
    }
    setErrors({});
    setActiveTab("basic");
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

  const handleCollectionToggle = (collectionId: string) => {
    setFormData((prev) => {
      const currentKnowledge = prev.knowledge || DEFAULT_KNOWLEDGE;
      const currentIds = currentKnowledge.collection_ids || [];
      const newIds = currentIds.includes(collectionId)
        ? currentIds.filter((id) => id !== collectionId)
        : [...currentIds, collectionId];
      return {
        ...prev,
        knowledge: {
          ...currentKnowledge,
          collection_ids: newIds,
          enabled: newIds.length > 0,
        },
      };
    });
  };

  const updateKnowledge = <K extends keyof AgentKnowledgeConfig>(
    key: K,
    value: AgentKnowledgeConfig[K]
  ) => {
    setFormData((prev) => ({
      ...prev,
      knowledge: {
        ...(prev.knowledge || DEFAULT_KNOWLEDGE),
        [key]: value,
      },
    }));
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

    // Limpar knowledge se não tiver coleções selecionadas
    const knowledge = formData.knowledge;
    const cleanKnowledge = knowledge && knowledge.collection_ids.length > 0
      ? knowledge
      : undefined;

    onSave({
      id: formData.id!,
      role: formData.role!,
      description: formData.description,
      model: formData.model!,
      instructions: formData.instructions!,
      tools: formData.tools || [],
      knowledge: cleanKnowledge,
    });
    onOpenChange(false);
  };

  // Preview do JSON gerado
  const jsonPreview = useMemo(() => {
    const agentData: Record<string, unknown> = {
      id: formData.id || "<id>",
      role: formData.role || "<role>",
      description: formData.description || undefined,
      model: formData.model || "<model>",
      instructions: formData.instructions || "<instructions>",
      tools: formData.tools || [],
    };
    
    // Incluir knowledge apenas se houver coleções
    if (formData.knowledge && formData.knowledge.collection_ids.length > 0) {
      agentData.knowledge = formData.knowledge;
    }
    
    return JSON.stringify(agentData, null, 2);
  }, [formData]);

  const knowledgeConfig = formData.knowledge || DEFAULT_KNOWLEDGE;
  const selectedCollectionCount = knowledgeConfig.collection_ids.length;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col p-6 border-2">
        <DialogHeader className="pb-4 border-b">
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            {mode === "create" ? "Criar Novo Agente" : "Editar Agente"}
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="basic" className="gap-2">
              <Bot className="h-4 w-4" />
              Básico
            </TabsTrigger>
            <TabsTrigger value="tools" className="gap-2">
              <Wrench className="h-4 w-4" />
              Ferramentas
              {(formData.tools?.length ?? 0) > 0 && (
                <Badge variant="secondary" className="ml-1 h-5 text-xs">
                  {formData.tools?.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="knowledge" className="gap-2">
              <Database className="h-4 w-4" />
              Knowledge
              {selectedCollectionCount > 0 && (
                <Badge variant="secondary" className="ml-1 h-5 text-xs">
                  {selectedCollectionCount}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="preview" className="gap-2">
              <Eye className="h-4 w-4" />
              Preview
            </TabsTrigger>
          </TabsList>

          {/* Tab: Básico */}
          <TabsContent value="basic" className="flex-1 overflow-hidden mt-4">
            <ScrollArea className="h-[350px] pr-4">
              <div className="space-y-5 pb-4">
                {/* ID e Role */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="role">
                      Nome do Agente <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="role"
                      placeholder="Ex: Assistente de Vendas"
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
                      placeholder="assistente_vendas"
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
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Tab: Ferramentas */}
          <TabsContent value="tools" className="flex-1 overflow-hidden mt-4">
            <ScrollArea className="h-[350px] pr-4">
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Info className="h-4 w-4" />
                  Selecione as ferramentas que este agente pode usar
                </div>
                
                {availableTools.length === 0 ? (
                  <Card className="border-dashed">
                    <CardContent className="p-8 text-center">
                      <Wrench className="h-10 w-10 mx-auto text-muted-foreground/50 mb-3" />
                      <p className="text-sm text-muted-foreground">
                        Nenhuma ferramenta disponível.
                        <br />
                        Adicione ferramentas em Recursos.
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-2">
                    {availableTools.map((tool) => (
                      <div
                        key={tool.id}
                        className="flex items-start gap-3 p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
                        onClick={() => handleToolToggle(tool.id)}
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
            </ScrollArea>
          </TabsContent>

          {/* Tab: Knowledge (RAG) */}
          <TabsContent value="knowledge" className="flex-1 overflow-hidden mt-4">
            <ScrollArea className="h-[350px] pr-4">
              <div className="space-y-4">
                <Card className={knowledgeConfig.enabled ? "border-primary/50" : ""}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${knowledgeConfig.enabled ? "bg-primary/10" : "bg-muted"}`}>
                          <Brain className={`h-5 w-5 ${knowledgeConfig.enabled ? "text-primary" : "text-muted-foreground"}`} />
                        </div>
                        <div>
                          <CardTitle className="text-base">Knowledge Base</CardTitle>
                          <CardDescription>
                            Conecte coleções de documentos para enriquecer as respostas
                          </CardDescription>
                        </div>
                      </div>
                      <Switch
                        checked={knowledgeConfig.enabled}
                        onCheckedChange={(checked) => updateKnowledge("enabled", checked)}
                      />
                    </div>
                  </CardHeader>
                  
                  {knowledgeConfig.enabled && (
                    <CardContent className="space-y-4">
                      {/* Seleção de Coleções */}
                      <div className="space-y-2">
                        <Label>Coleções Disponíveis</Label>
                        {availableCollections.length === 0 ? (
                          <div className="p-4 border rounded-lg border-dashed text-center">
                            <Database className="h-8 w-8 mx-auto text-muted-foreground/50 mb-2" />
                            <p className="text-sm text-muted-foreground">
                              Nenhuma coleção disponível.
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              Crie coleções na página de Knowledge Base.
                            </p>
                          </div>
                        ) : (
                          <div className="space-y-2 max-h-[150px] overflow-y-auto">
                            {availableCollections.map((collection) => (
                              <div
                                key={collection.id}
                                className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
                                onClick={() => handleCollectionToggle(collection.id)}
                              >
                                <Checkbox
                                  checked={knowledgeConfig.collection_ids.includes(collection.id)}
                                  onCheckedChange={() => handleCollectionToggle(collection.id)}
                                />
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium truncate">{collection.name}</p>
                                  {collection.description && (
                                    <p className="text-xs text-muted-foreground truncate">
                                      {collection.description}
                                    </p>
                                  )}
                                </div>
                                <div className="flex gap-1 shrink-0">
                                  <Badge variant="secondary" className="text-[10px]">
                                    {collection.document_count} docs
                                  </Badge>
                                  <Badge variant="outline" className="text-[10px]">
                                    {collection.chunk_count} chunks
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Configurações de Retrieval */}
                      {selectedCollectionCount > 0 && (
                        <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                          <div className="space-y-2">
                            <Label className="text-sm">Top K (resultados)</Label>
                            <div className="flex items-center gap-1">
                              <Button
                                type="button"
                                variant="outline"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => updateKnowledge("top_k", Math.max(1, (knowledgeConfig.top_k || 5) - 1))}
                              >
                                <Minus className="h-3 w-3" />
                              </Button>
                              <Input
                                type="number"
                                value={knowledgeConfig.top_k || 5}
                                onChange={(e) => updateKnowledge("top_k", Math.max(1, Math.min(20, parseInt(e.target.value) || 5)))}
                                min={1}
                                max={20}
                                className="w-16 text-center h-8"
                              />
                              <Button
                                type="button"
                                variant="outline"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => updateKnowledge("top_k", Math.min(20, (knowledgeConfig.top_k || 5) + 1))}
                              >
                                <Plus className="h-3 w-3" />
                              </Button>
                            </div>
                            <p className="text-xs text-muted-foreground">Quantidade de trechos retornados</p>
                          </div>
                          <div className="space-y-2">
                            <Label className="text-sm">Score Mínimo</Label>
                            <div className="flex items-center gap-1">
                              <Button
                                type="button"
                                variant="outline"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => updateKnowledge("min_score", Math.max(0, (knowledgeConfig.min_score || 0.25) - 0.05))}
                              >
                                <Minus className="h-3 w-3" />
                              </Button>
                              <Input
                                type="number"
                                value={((knowledgeConfig.min_score || 0.25) * 100).toFixed(0)}
                                onChange={(e) => updateKnowledge("min_score", Math.max(0, Math.min(1, (parseInt(e.target.value) || 25) / 100)))}
                                min={0}
                                max={100}
                                step={5}
                                className="w-16 text-center h-8"
                              />
                              <Button
                                type="button"
                                variant="outline"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => updateKnowledge("min_score", Math.min(1, (knowledgeConfig.min_score || 0.25) + 0.05))}
                              >
                                <Plus className="h-3 w-3" />
                              </Button>
                              <span className="text-sm text-muted-foreground">%</span>
                            </div>
                            <p className="text-xs text-muted-foreground">Similaridade mínima para considerar</p>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  )}
                </Card>

                {!knowledgeConfig.enabled && (
                  <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg text-sm text-muted-foreground">
                    <Info className="h-4 w-4 shrink-0" />
                    <span>
                      Ative para permitir que o agente consulte documentos da base de conhecimento.
                    </span>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Tab: Preview */}
          <TabsContent value="preview" className="flex-1 overflow-hidden mt-4">
            <div className="h-[350px] border rounded-lg bg-muted/30">
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
