import { create } from "zustand";
import {
  type Edge,
  type Node,
  type XYPosition,
  addEdge,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
  applyNodeChanges,
  applyEdgeChanges,
} from "@xyflow/react";
import type {
  WorkerConfig,
  WorkflowStep,
} from "./types";

export interface AgentNodeConfig {
  role?: string;
  model?: string;
  instructions?: string;
  tools?: string[];
  input_template?: string;
  description?: string;
}

export interface ConditionNodeConfig {
  expression?: string;
  description?: string;
}

export interface RagNodeConfig {
  knowledge_base?: string;
  retriever?: string;
  top_k?: number;
  prompt_template?: string;
}

export interface RouterNodeConfig {
  strategy?: string;
}

export interface HandoffNodeConfig {
  instructions?: string;
}

export interface ToolNodeConfig {
  tool_id?: string;
  description?: string;
}

export type StudioNodeType = "agent" | "start" | "router" | "handoff" | "condition" | "rag" | "tool";

export interface StudioNodeData extends Record<string, unknown> {
  label: string;
  type: StudioNodeType;
  config?: Record<string, unknown>;
}

export type StudioNode = Node<StudioNodeData>;

interface NodeConfigUpdate extends Record<string, unknown> {
  label?: string;
}

interface StudioState {
  nodes: StudioNode[];
  edges: Edge[];
  workerConfig: WorkerConfig;
  
  // Flow Actions
  onNodesChange: OnNodesChange<StudioNode>;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  addNode: (type: StudioNodeType, position: XYPosition, initialData?: Record<string, unknown>) => void;
  updateNodeConfig: (id: string, updates: NodeConfigUpdate) => void;
  
  // Config Actions
  setWorkerConfig: (config: WorkerConfig) => void;
  generateConfig: () => WorkerConfig;
}

const initialConfig: WorkerConfig = {
  version: "1.0",
  name: "New Agent",
  resources: {
    models: {
      "gpt-4o-mini": { type: "azure-openai", deployment: "gpt-4o-mini" }
    },
    tools: [
      { id: "consultar_clima", path: "mock_tools.basic:consultar_clima", description: "Retorna previão do tempo simulada" },
      { id: "resumir_diretrizes", path: "mock_tools.basic:resumir_diretrizes", description: "Resume diretrizes de um tópico" },
      { id: "calcular_custos", path: "mock_tools.basic:calcular_custos", description: "Calcula custos de carga de trabalho" },
      { id: "verificar_status_sistema", path: "mock_tools.basic:verificar_status_sistema", description: "Verifica status de um sistema" },
      { id: "verificar_resolucao", path: "mock_tools.basic:verificar_resolucao", description: "Verifica resolução de um ticket" }
    ]
  },
  agents: [],
  workflow: {
    type: "sequential",
    steps: [],
    // TODO: Reativar DAG quando validação estiver pronta
    // nodes: [],
    // edges: []
  }
};

const defaultLabels: Record<StudioNodeType, string> = {
  start: "Start",
  agent: "New Agent",
  router: "Router",
  handoff: "Handoff",
  condition: "Condition",
  rag: "RAG Retriever",
  tool: "Tool Execution",
};

const defaultConfigs: Partial<Record<StudioNodeType, Record<string, unknown>>> = {
  agent: {
    role: "Agent",
    model: "gpt-4o-mini",
    instructions: "You are a helpful assistant.",
    tools: [],
    description: "Default agent role",
  },
  condition: {
    expression: "True",
    description: "Describe your branching logic",
  },
  rag: {
    knowledge_base: "knowledge_base",
    retriever: "azure_search",
    top_k: 4,
    prompt_template: "Answer using retrieved documents",
  },
  tool: {
    tool_id: "basic_tool",
    description: "Execute a specific tool",
  },
  router: {
    strategy: "auto",
  },
  handoff: {
    instructions: "Escalate to a human operator.",
  },
};

// TODO: Reativar DAG quando validação estiver pronta
// type SerializableStudioType = Exclude<StudioNodeType, "start">;
// function mapToWorkflowNodeType(type: SerializableStudioType): WorkflowNode["type"] {
//   if (type === "handoff") {
//     return "human";
//   }
//   return type as WorkflowNode["type"];
// }

// Comentado - será usado quando DAG for reativado
// function isAgentNode(
//   node: StudioNode
// ): node is StudioNode & { data: StudioNodeData & { type: "agent" } } {
//   return node.data.type === "agent";
// }

export const useStudioStore = create<StudioState>((set, get) => ({
  nodes: [],
  edges: [],
  workerConfig: initialConfig,

  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges<StudioNode>(changes, get().nodes),
    });
  },

  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },

  onConnect: (connection) => {
    set({
      edges: addEdge(connection, get().edges),
    });
  },

  addNode: (type, position, initialData) => {
    const id = crypto.randomUUID();
    
    let label = defaultLabels[type] ?? "Node";
    let config = defaultConfigs[type] ? { ...defaultConfigs[type]! } : {};

    if (initialData) {
        // Override label if provided in initialData (e.g. agent name or tool name)
        if (initialData.name && typeof initialData.name === 'string') {
            label = initialData.name;
        } else if (initialData.label && typeof initialData.label === 'string') {
            label = initialData.label;
        }

        // Merge other properties into config
        config = { ...config, ...initialData };
        
        // Specific handling for Tool ID
        if (type === 'tool' && initialData.tool_id) {
            config.tool_id = initialData.tool_id;
        }
        
        // Specific handling for Agent
        if (type === 'agent') {
             if (initialData.agent_name) {
                 config.role = initialData.agent_name;
             }
             if (initialData.description) {
                 config.description = initialData.description;
             }
        }
    }

    const newNode: StudioNode = {
      id,
      type: "studioNode", // We'll use a generic wrapper or specific types
      position,
      data: { 
        label,
        type,
        config: Object.keys(config).length > 0 ? config : undefined,
      },
    };
    set({ nodes: [...get().nodes, newNode] });
  },

  updateNodeConfig: (id, updates) => {
    set({
      nodes: get().nodes.map((node) =>
        node.id === id
          ? (() => {
              const nextData = { ...node.data };
              const newConfig: Record<string, unknown> = {
                ...(nextData.config || {}),
              };
              const mergedUpdates = { ...updates };

              if ("label" in mergedUpdates) {
                nextData.label = mergedUpdates.label as string;
                delete mergedUpdates.label;
              }

              Object.keys(mergedUpdates).forEach((key) => {
                newConfig[key] = mergedUpdates[key];
              });

              nextData.config = Object.keys(newConfig).length > 0 ? newConfig : undefined;
              return { ...node, data: nextData };
            })()
          : node
      ),
    });
  },

  setWorkerConfig: (config) => set({ workerConfig: config }),

  generateConfig: (): WorkerConfig => {
    const { workerConfig } = get();
    
    // Limpar agents - remover campos internos como _file
    const agents = (workerConfig.agents || []).map(({ _file, ...agent }: any) => agent);
    
    // Coletar tools usadas pelos agentes
    const usedToolIds = new Set<string>();
    agents.forEach((agent) => {
      (agent.tools || []).forEach((toolId: string) => usedToolIds.add(toolId));
    });
    
    // Filtrar só as tools que são realmente usadas
    const allTools = workerConfig.resources?.tools || [];
    const filteredTools = allTools.filter((tool) => usedToolIds.has(tool.id));
    
    // Garantir que steps está no formato correto (WorkflowStep[])
    const rawSteps = workerConfig.workflow.steps || [];
    
    // Garantir que cada step tem a estrutura correta
    const steps: WorkflowStep[] = rawSteps.map((step) => {
      // Se já for um WorkflowStep válido, retornar
      if (typeof step === "object" && step !== null && "id" in step) {
        return {
          id: step.id,
          type: step.type || "agent",
          agent: step.agent,
          input_template: step.input_template || "{{output}}",
          next: step.next,
          transitions: step.transitions,
        };
      }
      // Fallback para string (não deveria acontecer com os editores visuais)
      const stepId = String(step);
      return {
        id: stepId,
        type: "agent" as const,
        agent: stepId,
        input_template: "{{output}}",
      };
    });

    // Determinar start_step
    const startStep = workerConfig.workflow.start_step || (steps[0]?.id) || "";

    return {
      ...workerConfig,
      resources: {
        ...workerConfig.resources,
        tools: filteredTools,
      },
      agents,
      workflow: {
        ...workerConfig.workflow,
        start_step: startStep,
        steps,
      },
    };
  },
}));
