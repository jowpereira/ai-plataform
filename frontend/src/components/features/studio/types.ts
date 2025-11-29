export interface ToolConfig {
  id: string;
  path: string;
  description?: string;
}

export interface ModelConfig {
  type: "openai" | "azure-openai";
  deployment?: string;
  env_vars?: Record<string, string>;
}

export interface AgentConfig {
  id: string;
  role: string;
  description?: string;
  model: string;
  instructions: string;
  tools: string[];
}

export interface WorkflowStep {
  id: string;
  type: "agent" | "human";
  agent?: string;
  input_template: string;
  next?: string;
  transitions?: string[];
}

export type WorkflowNodeType =
  | "agent"
  | "human"
  | "condition"
  | "router"
  | "tool"
  | "rag"
  | "code"
  | "http";

export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  label?: string;
  agent?: string;
  input_template?: string;
  config?: Record<string, unknown>;
}

export interface WorkflowEdge {
  source: string;
  target: string;
  type?: string;
  label?: string;
  condition?: string;
}

// Tipos de workflow suportados (builders de alto nível)
// TODO: Reativar DAG quando validação estiver pronta
export type WorkflowType = "sequential" | "parallel" | "router" | "group_chat" | "handoff" | "magentic";

// Mantido para compatibilidade futura - não usar diretamente
// export type WorkflowTypeWithDag = WorkflowType | "dag";

export interface WorkflowConfig {
  type: WorkflowType;
  start_step?: string;
  steps?: WorkflowStep[];
  // TODO: Reativar DAG quando validação estiver pronta
  // nodes?: WorkflowNode[];
  // edges?: WorkflowEdge[];
}

export interface ResourcesConfig {
  models: Record<string, ModelConfig>;
  tools: ToolConfig[];
}

export interface WorkerConfig {
  version: string;
  name: string;
  checkpoint_file?: string;
  resources: ResourcesConfig;
  agents: AgentConfig[];
  workflow: WorkflowConfig;
}
