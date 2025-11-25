/**
 * workflowSerializer - Funções para serializar/deserializar WorkerConfig
 * Gera JSON válido para o backend
 */

import type { WorkerConfig, AgentConfig, WorkflowStep, WorkflowType } from "@/components/features/studio/types";

/**
 * Serializa o estado do Studio para WorkerConfig JSON
 */
export function serializeWorkerConfig(
  name: string,
  version: string,
  resources: WorkerConfig["resources"],
  agents: AgentConfig[],
  workflowType: WorkflowType,
  steps: WorkflowStep[],
  startStep?: string
): WorkerConfig {
  return {
    version,
    name,
    resources,
    agents: agents.map((agent) => ({
      id: agent.id,
      role: agent.role,
      description: agent.description,
      model: agent.model,
      instructions: agent.instructions,
      tools: agent.tools || [],
    })),
    workflow: {
      type: workflowType,
      start_step: startStep,
      steps: steps.map((step) => ({
        id: step.id,
        type: step.type,
        agent: step.agent,
        input_template: step.input_template,
        transitions: step.transitions,
      })),
    },
  };
}

/**
 * Valida um WorkerConfig
 */
export function validateWorkerConfig(config: unknown): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!config || typeof config !== "object") {
    return { valid: false, errors: ["Configuração inválida"] };
  }

  const c = config as Record<string, unknown>;

  // Campos obrigatórios
  if (!c.name || typeof c.name !== "string") {
    errors.push("Campo 'name' é obrigatório");
  }

  if (!c.version || typeof c.version !== "string") {
    errors.push("Campo 'version' é obrigatório");
  }

  if (!c.resources || typeof c.resources !== "object") {
    errors.push("Campo 'resources' é obrigatório");
  }

  if (!Array.isArray(c.agents)) {
    errors.push("Campo 'agents' deve ser um array");
  } else {
    c.agents.forEach((agent: unknown, index: number) => {
      if (!agent || typeof agent !== "object") {
        errors.push(`Agent ${index}: deve ser um objeto`);
        return;
      }
      const a = agent as Record<string, unknown>;
      if (!a.id) errors.push(`Agent ${index}: 'id' é obrigatório`);
      if (!a.role) errors.push(`Agent ${index}: 'role' é obrigatório`);
      if (!a.model) errors.push(`Agent ${index}: 'model' é obrigatório`);
      if (!a.instructions) errors.push(`Agent ${index}: 'instructions' é obrigatório`);
    });
  }

  if (!c.workflow || typeof c.workflow !== "object") {
    errors.push("Campo 'workflow' é obrigatório");
  } else {
    const w = c.workflow as Record<string, unknown>;
    const validTypes = ["sequential", "parallel", "router", "group_chat", "handoff"];
    if (!validTypes.includes(w.type as string)) {
      errors.push(`Tipo de workflow '${w.type}' não é válido. Use: ${validTypes.join(", ")}`);
    }
    if (!Array.isArray(w.steps)) {
      errors.push("Campo 'workflow.steps' deve ser um array");
    }
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Parseia JSON e retorna WorkerConfig tipado
 */
export function parseWorkerConfig(jsonString: string): WorkerConfig {
  const parsed = JSON.parse(jsonString);
  const validation = validateWorkerConfig(parsed);
  
  if (!validation.valid) {
    throw new Error(`Configuração inválida:\n${validation.errors.join("\n")}`);
  }

  return parsed as WorkerConfig;
}

/**
 * Formata WorkerConfig como JSON string
 */
export function formatWorkerConfig(config: WorkerConfig): string {
  return JSON.stringify(config, null, 2);
}

/**
 * Exporta config como arquivo para download
 */
export function downloadWorkerConfig(config: WorkerConfig, filename?: string): void {
  const json = formatWorkerConfig(config);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || `${config.name.replace(/\s+/g, "_").toLowerCase()}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Importa config de arquivo
 */
export function importWorkerConfig(file: File): Promise<WorkerConfig> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const config = parseWorkerConfig(content);
        resolve(config);
      } catch (err) {
        reject(err);
      }
    };
    
    reader.onerror = () => reject(new Error("Erro ao ler arquivo"));
    reader.readAsText(file);
  });
}

/**
 * Salva rascunho no localStorage
 */
const DRAFT_KEY = "studio_draft";

export function saveDraft(config: WorkerConfig): void {
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify({
      config,
      savedAt: Date.now(),
    }));
  } catch (err) {
    console.error("Erro ao salvar rascunho:", err);
  }
}

export function loadDraft(): { config: WorkerConfig; savedAt: number } | null {
  try {
    const data = localStorage.getItem(DRAFT_KEY);
    if (!data) return null;
    return JSON.parse(data);
  } catch (err) {
    console.error("Erro ao carregar rascunho:", err);
    return null;
  }
}

export function clearDraft(): void {
  localStorage.removeItem(DRAFT_KEY);
}
