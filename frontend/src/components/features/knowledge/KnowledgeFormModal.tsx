/**
 * KnowledgeFormModal - Formulário de Configuração RAG
 * Configura o pipeline de Retrieval Augmented Generation
 */

import { useState, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Database,
  Settings2,
  Layers,
  Hash,
  MessageSquare,
  FileText,
  Sparkles,
  AlertCircle,
  Minus,
  Plus,
} from "lucide-react";
import type { RagConfig, RagEmbeddingConfig } from "@/services/api";
import { DEFAULT_RAG_CONFIG } from "@/stores";

interface KnowledgeFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: RagConfig;
  onSave: (config: RagConfig) => Promise<void>;
  isSaving: boolean;
}

// Modelos de embedding disponíveis
const EMBEDDING_MODELS = [
  { value: "text-embedding-3-small", label: "text-embedding-3-small (Recomendado)" },
  { value: "text-embedding-3-large", label: "text-embedding-3-large" },
  { value: "text-embedding-ada-002", label: "text-embedding-ada-002 (Legacy)" },
];

export function KnowledgeFormModal({
  open,
  onOpenChange,
  config,
  onSave,
  isSaving,
}: KnowledgeFormModalProps) {
  // Estado local do formulário
  const [formData, setFormData] = useState<RagConfig>(config);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Sincronizar com config externo quando modal abre
  useEffect(() => {
    if (open) {
      setFormData(config);
      setValidationError(null);
    }
  }, [open, config]);

  // Atualizar campo do formulário
  const updateField = useCallback(<K extends keyof RagConfig>(
    field: K,
    value: RagConfig[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setValidationError(null);
  }, []);

  // Atualizar configuração de embedding
  const updateEmbedding = useCallback((
    field: keyof RagEmbeddingConfig,
    value: string | number | boolean | undefined
  ) => {
    setFormData((prev) => ({
      ...prev,
      embedding: {
        model: prev.embedding?.model || "text-embedding-3-small",
        normalize: prev.embedding?.normalize ?? true,
        ...prev.embedding,
        [field]: value,
      },
    }));
  }, []);

  // Validação do formulário
  const validateForm = (): boolean => {
    // Se RAG está habilitado e provider é memory, embedding é obrigatório
    if (formData.enabled && formData.provider === "memory") {
      if (!formData.embedding || !formData.embedding.model) {
        setValidationError("Configuração de Embedding é obrigatória quando o provider é 'Memory'");
        return false;
      }
    }

    // Validar top_k
    if (formData.top_k < 1 || formData.top_k > 50) {
      setValidationError("Top K deve estar entre 1 e 50");
      return false;
    }

    // Validar min_score
    if (formData.min_score < 0 || formData.min_score > 1) {
      setValidationError("Pontuação mínima deve estar entre 0.0 e 1.0");
      return false;
    }

    setValidationError(null);
    return true;
  };

  // Handler de submit
  const handleSubmit = async () => {
    if (!validateForm()) return;

    // Limpar embedding config se não for necessário
    const configToSave: RagConfig = { ...formData };
    if (configToSave.provider !== "memory" || !configToSave.enabled) {
      // Manter embedding apenas se provider for memory e RAG estiver habilitado
      if (configToSave.provider !== "memory") {
        configToSave.embedding = undefined;
      }
    }

    await onSave(configToSave);
    onOpenChange(false);
  };

  // Handler para resetar ao padrão
  const handleReset = () => {
    setFormData(DEFAULT_RAG_CONFIG);
    setValidationError(null);
  };

  // Componente de input numérico com botões
  const NumberInput = ({
    value,
    onChange,
    min,
    max,
    step = 1,
    disabled = false,
  }: {
    value: number;
    onChange: (v: number) => void;
    min: number;
    max: number;
    step?: number;
    disabled?: boolean;
  }) => (
    <div className="flex items-center gap-1">
      <Button
        type="button"
        variant="outline"
        size="icon"
        className="h-8 w-8"
        onClick={() => onChange(Math.max(min, value - step))}
        disabled={disabled || value <= min}
      >
        <Minus className="h-3 w-3" />
      </Button>
      <Input
        type="number"
        value={value}
        onChange={(e) => {
          const v = parseFloat(e.target.value);
          if (!isNaN(v)) {
            onChange(Math.min(max, Math.max(min, v)));
          }
        }}
        min={min}
        max={max}
        step={step}
        className="w-20 text-center h-8"
        disabled={disabled}
      />
      <Button
        type="button"
        variant="outline"
        size="icon"
        className="h-8 w-8"
        onClick={() => onChange(Math.min(max, value + step))}
        disabled={disabled || value >= max}
      >
        <Plus className="h-3 w-3" />
      </Button>
    </div>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Configuração do Knowledge Base (RAG)
          </DialogTitle>
          <DialogDescription>
            Configure o pipeline de Retrieval Augmented Generation para enriquecer
            as respostas dos agentes com conhecimento contextual.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Toggle Principal */}
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${formData.enabled ? "bg-green-100 dark:bg-green-900" : "bg-muted"}`}>
                <Sparkles className={`h-5 w-5 ${formData.enabled ? "text-green-600 dark:text-green-400" : "text-muted-foreground"}`} />
              </div>
              <div>
                <Label className="text-base font-medium">RAG Habilitado</Label>
                <p className="text-sm text-muted-foreground">
                  {formData.enabled 
                    ? "Agentes utilizarão contexto da base de conhecimento" 
                    : "Agentes responderão apenas com conhecimento do modelo"}
                </p>
              </div>
            </div>
            <Switch
              checked={formData.enabled}
              onCheckedChange={(checked) => updateField("enabled", checked)}
            />
          </div>

          {/* Configurações - visíveis apenas quando habilitado */}
          {formData.enabled && (
            <>
              <Separator />

              {/* Provider e Namespace */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <Layers className="h-4 w-4" />
                    Provedor
                  </Label>
                  <Select
                    value={formData.provider}
                    onValueChange={(v) => updateField("provider", v as RagConfig["provider"])}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="memory">
                        <div className="flex items-center gap-2">
                          <Database className="h-4 w-4" />
                          Memory (Vector Store Local)
                        </div>
                      </SelectItem>
                      <SelectItem value="azure_search">
                        <div className="flex items-center gap-2">
                          <Settings2 className="h-4 w-4" />
                          Azure AI Search
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    {formData.provider === "memory"
                      ? "Armazenamento vetorial em memória"
                      : "Azure Cognitive Search para produção"}
                  </p>
                </div>

                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <Hash className="h-4 w-4" />
                    Namespace
                  </Label>
                  <Input
                    value={formData.namespace}
                    onChange={(e) => updateField("namespace", e.target.value)}
                    placeholder="default"
                  />
                  <p className="text-xs text-muted-foreground">
                    Identificador lógico para segmentar conhecimento
                  </p>
                </div>
              </div>

              {/* Parâmetros de Retrieval */}
              <Card>
                <CardContent className="pt-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium flex items-center gap-2">
                      <Settings2 className="h-4 w-4" />
                      Parâmetros de Retrieval
                    </h4>
                    <Badge variant="secondary">Ajuste Fino</Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-6">
                    {/* Top K */}
                    <div className="space-y-2">
                      <Label>Top K (Quantidade de Trechos)</Label>
                      <NumberInput
                        value={formData.top_k}
                        onChange={(v) => updateField("top_k", v)}
                        min={1}
                        max={50}
                        step={1}
                      />
                      <p className="text-xs text-muted-foreground">
                        Número máximo de trechos retornados (1-50)
                      </p>
                    </div>

                    {/* Min Score */}
                    <div className="space-y-2">
                      <Label>Pontuação Mínima</Label>
                      <NumberInput
                        value={formData.min_score}
                        onChange={(v) => updateField("min_score", v)}
                        min={0}
                        max={1}
                        step={0.05}
                      />
                      <p className="text-xs text-muted-foreground">
                        Similaridade mínima para considerar (0.0-1.0)
                      </p>
                    </div>
                  </div>

                  {/* Strategy */}
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <MessageSquare className="h-4 w-4" />
                      Estratégia de Busca
                    </Label>
                    <Select
                      value={formData.strategy}
                      onValueChange={(v) => updateField("strategy", v as RagConfig["strategy"])}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="last_message">
                          Última Mensagem
                        </SelectItem>
                        <SelectItem value="conversation">
                          Conversação Completa
                        </SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      {formData.strategy === "last_message"
                        ? "Busca baseada apenas na última mensagem do usuário"
                        : "Busca considerando todo o histórico da conversa"}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Context Prompt */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Prompt de Contexto
                </Label>
                <Textarea
                  value={formData.context_prompt}
                  onChange={(e) => updateField("context_prompt", e.target.value)}
                  placeholder="Instrução que antecede os trechos recuperados..."
                  rows={3}
                />
                <p className="text-xs text-muted-foreground">
                  Mensagem que antecede os trechos recuperados no prompt do agente
                </p>
              </div>

              {/* Embedding Config - Condicional */}
              {formData.provider === "memory" && (
                <>
                  <Separator />
                  
                  <Card className="border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-950/20">
                    <CardContent className="pt-4 space-y-4">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium flex items-center gap-2">
                          <Sparkles className="h-4 w-4 text-amber-600" />
                          Configuração de Embeddings
                        </h4>
                        <Badge variant="outline" className="text-amber-600 border-amber-300">
                          Obrigatório
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        {/* Model */}
                        <div className="space-y-2">
                          <Label>Modelo de Embedding</Label>
                          <Select
                            value={formData.embedding?.model || "text-embedding-3-small"}
                            onValueChange={(v) => updateEmbedding("model", v)}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {EMBEDDING_MODELS.map((model) => (
                                <SelectItem key={model.value} value={model.value}>
                                  {model.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Dimensions */}
                        <div className="space-y-2">
                          <Label>Dimensões (Opcional)</Label>
                          <Input
                            type="number"
                            value={formData.embedding?.dimensions || ""}
                            onChange={(e) => {
                              const v = e.target.value;
                              updateEmbedding("dimensions", v ? parseInt(v) : undefined);
                            }}
                            placeholder="Auto"
                            min={1}
                          />
                          <p className="text-xs text-muted-foreground">
                            Deixe vazio para usar dimensão padrão do modelo
                          </p>
                        </div>
                      </div>

                      {/* Normalize */}
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="normalize"
                          checked={formData.embedding?.normalize ?? true}
                          onCheckedChange={(checked) => 
                            updateEmbedding("normalize", checked as boolean)
                          }
                        />
                        <Label htmlFor="normalize" className="text-sm font-normal cursor-pointer">
                          Normalizar vetores de embedding
                        </Label>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </>
          )}

          {/* Erro de validação */}
          {validationError && (
            <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-400 rounded-lg text-sm">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {validationError}
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="ghost"
            onClick={handleReset}
            disabled={isSaving}
          >
            Restaurar Padrão
          </Button>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSaving}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              onClick={handleSubmit}
              disabled={isSaving}
            >
              {isSaving ? "Salvando..." : "Salvar Configuração"}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
