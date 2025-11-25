import { useEffect, useState } from "react";
import {
  useStudioStore,
  type StudioNode,
  type AgentNodeConfig,
  type ConditionNodeConfig,
  type RagNodeConfig,
  type ToolNodeConfig,
} from "./studio-store";
import type { WorkerConfig } from "./types";
import { CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { apiClient } from "@/services/api";
import type { ToolInfo } from "@/types/workflow";

export function StudioConfigPanel() {
  const { nodes, updateNodeConfig, workerConfig, setWorkerConfig } = useStudioStore();
  const [selectedNode, setSelectedNode] = useState<StudioNode | null>(null);
  const [availableTools, setAvailableTools] = useState<ToolInfo[]>([]);

  // Sync selection
  useEffect(() => {
    const found = nodes.find((n) => n.selected);
    setSelectedNode(found || null);
  }, [nodes]);

  // Fetch tools
  useEffect(() => {
      apiClient.listTools().then(setAvailableTools).catch(console.error);
  }, []);

  if (!selectedNode) {
    return (
      <GlobalConfigPanel
        config={workerConfig}
        onChange={setWorkerConfig}
      />
    );
  }

  return (
    <div className="w-80 border-l bg-background h-full flex flex-col">
      <CardHeader className="border-b py-4">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          {selectedNode.data.label} Configuration
          <span className="text-xs text-muted-foreground font-normal uppercase px-2 py-0.5 bg-muted rounded">
            {selectedNode.data.type}
          </span>
        </CardTitle>
      </CardHeader>
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-6">
          <div className="space-y-2">
            <Label>Label</Label>
            <Input
              value={selectedNode.data.label}
              onChange={(e) =>
                updateNodeConfig(selectedNode.id, { label: e.target.value })
              }
            />
          </div>

          {selectedNode.data.type === "agent" && (
            <AgentConfigForm
              node={selectedNode}
              availableTools={availableTools}
              onChange={(updates) => updateNodeConfig(selectedNode.id, updates)}
            />
          )}

          {selectedNode.data.type === "tool" && (
            <ToolConfigForm
              node={selectedNode}
              availableTools={availableTools}
              onChange={(updates) => updateNodeConfig(selectedNode.id, updates)}
            />
          )}

          {selectedNode.data.type === "router" && (
             <RouterConfigForm
               node={selectedNode}
               onChange={(updates) => updateNodeConfig(selectedNode.id, updates)}
             />
          )}

          {selectedNode.data.type === "condition" && (
            <ConditionConfigForm
              node={selectedNode}
              onChange={(updates) => updateNodeConfig(selectedNode.id, updates)}
            />
          )}

          {selectedNode.data.type === "rag" && (
            <RagConfigForm
              node={selectedNode}
              onChange={(updates) => updateNodeConfig(selectedNode.id, updates)}
            />
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

function GlobalConfigPanel({ config, onChange }: { config: WorkerConfig; onChange: (c: WorkerConfig) => void }) {
  return (
    <div className="w-80 border-l bg-background h-full flex flex-col">
      <CardHeader className="border-b py-4">
        <CardTitle className="text-sm font-medium">Global Settings</CardTitle>
      </CardHeader>
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-6">
          <div className="space-y-2">
            <Label>Project Name</Label>
            <Input
              value={config.name}
              onChange={(e) => onChange({ ...config, name: e.target.value })}
            />
          </div>
          
          <div className="space-y-2">
            <Label>Workflow Type</Label>
            <Select
              value={config.workflow.type}
              onValueChange={(val) =>
                onChange({
                  ...config,
                  workflow: { ...config.workflow, type: val as WorkerConfig["workflow"]["type"] },
                })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sequential">Sequential</SelectItem>
                <SelectItem value="parallel">Parallel</SelectItem>
                <SelectItem value="router">Router</SelectItem>
                <SelectItem value="group_chat">Group Chat</SelectItem>
                <SelectItem value="handoff">Handoff</SelectItem>
                {/* TODO: Reativar DAG quando validação estiver pronta */}
                {/* <SelectItem value="dag">Graph (DAG)</SelectItem> */}
              </SelectContent>
            </Select>
          </div>

          <Separator />
          
          <div className="space-y-2">
             <Label>Version</Label>
             <Input value={config.version} disabled />
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}

function AgentConfigForm({ node, onChange, availableTools }: { node: StudioNode; onChange: (u: Partial<AgentNodeConfig>) => void; availableTools: ToolInfo[] }) {
  const config = (node.data.config || {}) as AgentNodeConfig;

  const handleToolToggle = (toolId: string) => {
    const currentTools = config.tools || [];
    const newTools = currentTools.includes(toolId)
      ? currentTools.filter((t) => t !== toolId)
      : [...currentTools, toolId];
    onChange({ tools: newTools });
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Role</Label>
        <Input
          placeholder="e.g. Customer Support"
          value={config.role || ""}
          onChange={(e) => onChange({ role: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label>Description</Label>
        <Textarea
          placeholder="Short summary of this agent"
          value={config.description || ""}
          onChange={(e) => onChange({ description: e.target.value })}
          className="text-sm"
        />
      </div>

      <div className="space-y-2">
        <Label>Model</Label>
        <Select
          value={config.model || "gpt-4o"}
          onValueChange={(val) => onChange({ model: val })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select model" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="gpt-4o">GPT-4o</SelectItem>
            <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Instructions</Label>
        <Textarea
          className="min-h-[150px] font-mono text-xs"
          placeholder="You are a helpful assistant..."
          value={config.instructions || ""}
          onChange={(e) => onChange({ instructions: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label>Tools</Label>
        <div className="border rounded-md p-3 space-y-2 max-h-[150px] overflow-y-auto">
          {availableTools.length === 0 ? (
            <p className="text-xs text-muted-foreground">No tools available.</p>
          ) : (
            availableTools.map((tool) => (
              <div key={tool.id} className="flex items-center space-x-2">
                <Checkbox
                  id={`tool-${tool.id}`}
                  checked={(config.tools || []).includes(tool.id)}
                  onCheckedChange={() => handleToolToggle(tool.id)}
                />
                <Label
                  htmlFor={`tool-${tool.id}`}
                  className="text-sm font-normal cursor-pointer"
                >
                  {tool.name || tool.id}
                </Label>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function ConditionConfigForm({
  node,
  onChange,
}: {
  node: StudioNode;
  onChange: (u: Partial<ConditionNodeConfig>) => void;
}) {
  const config = (node.data.config || {}) as ConditionNodeConfig;

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Expression</Label>
        <Textarea
          className="font-mono text-xs min-h-[120px]"
          placeholder="len(input) > 0"
          value={config.expression || ""}
          onChange={(e) => onChange({ expression: e.target.value })}
        />
        <p className="text-[11px] text-muted-foreground">
          Use Python-style expressions. Available variables: <code>input</code>, <code>context</code>.
        </p>
      </div>

      <div className="space-y-2">
        <Label>Description</Label>
        <Textarea
          value={config.description || ""}
          onChange={(e) => onChange({ description: e.target.value })}
          placeholder="Explain what this branch does"
        />
      </div>
    </div>
  );
}

function RagConfigForm({
  node,
  onChange,
}: {
  node: StudioNode;
  onChange: (u: Partial<RagNodeConfig>) => void;
}) {
  const config = (node.data.config || {}) as RagNodeConfig;

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Knowledge Base</Label>
        <Input
          placeholder="e.g. contoso_search"
          value={config.knowledge_base || ""}
          onChange={(e) => onChange({ knowledge_base: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label>Retriever</Label>
        <Select
          value={config.retriever || "azure_search"}
          onValueChange={(val) => onChange({ retriever: val })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select retriever" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="azure_search">Azure AI Search</SelectItem>
            <SelectItem value="cognitive">Cognitive Search</SelectItem>
            <SelectItem value="custom">Custom Retriever</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Top K</Label>
        <Input
          type="number"
          min={1}
          value={String(config.top_k ?? 4)}
          onChange={(e) => {
            const parsed = Number(e.target.value);
            onChange({ top_k: Number.isNaN(parsed) ? 1 : parsed });
          }}
        />
      </div>

      <div className="space-y-2">
        <Label>Prompt Template</Label>
        <Textarea
          className="font-mono text-xs min-h-[120px]"
          placeholder="Use the retrieved documents to answer..."
          value={config.prompt_template || ""}
          onChange={(e) => onChange({ prompt_template: e.target.value })}
        />
      </div>
    </div>
  );
}

function ToolConfigForm({
  node,
  onChange,
  availableTools,
}: {
  node: StudioNode;
  onChange: (u: Partial<ToolNodeConfig>) => void;
  availableTools: ToolInfo[];
}) {
  const config = (node.data.config || {}) as ToolNodeConfig;

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Select Tool</Label>
        <Select
          value={config.tool_id || ""}
          onValueChange={(val) => onChange({ tool_id: val })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select a tool to execute" />
          </SelectTrigger>
          <SelectContent>
            {availableTools.map((tool) => (
              <SelectItem key={tool.id} value={tool.id}>
                {tool.name || tool.id}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {availableTools.length === 0 && (
          <p className="text-[11px] text-muted-foreground text-red-500">
            No tools available.
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label>Description</Label>
        <Textarea
          value={config.description || ""}
          onChange={(e) => onChange({ description: e.target.value })}
          placeholder="Why is this tool being used?"
        />
      </div>
    </div>
  );
}

function RouterConfigForm({
  node,
  onChange,
}: {
  node: StudioNode;
  onChange: (u: Record<string, unknown>) => void;
}) {
  const config = node.data.config || {};

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Router Strategy</Label>
        <Select
          value={(config.strategy as string) || "auto"}
          onValueChange={(val) => onChange({ strategy: val })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="auto">Auto (LLM Decision)</SelectItem>
            <SelectItem value="expression">Expression Based</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {config.strategy === "expression" && (
        <div className="space-y-2">
          <Label>Expression</Label>
          <Textarea
            className="font-mono text-xs"
            placeholder="input.contains('help')"
            value={(config.expression as string) || ""}
            onChange={(e) => onChange({ expression: e.target.value })}
          />
        </div>
      )}
    </div>
  );
}
