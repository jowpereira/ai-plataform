import { memo } from "react";
import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Bot, Play, GitFork, ArrowRightLeft, Split, BookOpen, Wrench } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { StudioNodeData, StudioNodeType } from "../studio-store";

const icons: Record<StudioNodeType | "default", LucideIcon> = {
  agent: Bot,
  start: Play,
  router: GitFork,
  handoff: ArrowRightLeft,
  condition: Split,
  rag: BookOpen,
  tool: Wrench,
  default: Bot,
};

const colors: Record<StudioNodeType | "default", string> = {
  agent: "border-blue-500",
  start: "border-green-500",
  router: "border-purple-500",
  handoff: "border-orange-500",
  condition: "border-emerald-500",
  rag: "border-sky-500",
  tool: "border-indigo-500",
  default: "border-gray-200",
};

type StudioNodeProps = NodeProps<Node<StudioNodeData>>;

export const StudioNode = memo(({ data, selected }: StudioNodeProps) => {
  const Icon = icons[data.type] ?? icons.default;
  const borderColor = colors[data.type] ?? colors.default;

  const config = data.config as Record<string, unknown> | undefined;
  const role = data.type === "agent" && typeof config?.role === "string" ? (config.role as string) : undefined;
  const model = data.type === "agent" && typeof config?.model === "string" ? (config.model as string) : undefined;
  const conditionExpression =
    data.type === "condition" && typeof config?.expression === "string"
      ? (config.expression as string)
      : undefined;
  const ragSource =
    data.type === "rag" && typeof config?.knowledge_base === "string"
      ? (config.knowledge_base as string)
      : data.type === "rag" && typeof config?.retriever === "string"
        ? (config.retriever as string)
        : undefined;
  const toolId = data.type === "tool" && typeof config?.tool_id === "string" ? (config.tool_id as string) : undefined;

  return (
    <Card className={`w-64 shadow-md ${selected ? "ring-2 ring-primary" : ""} ${borderColor} border-l-4 transition-all duration-200`}>
      <CardHeader className="p-3 pb-1">
        <div className="flex items-center gap-2">
          <div className={`p-2 rounded-md bg-muted`}>
            <Icon className="w-4 h-4" />
          </div>
          <div className="flex flex-col overflow-hidden">
            <CardTitle className="text-sm font-medium truncate" title={data.label}>
              {data.label}
            </CardTitle>
            {role && (
              <span className="text-[10px] text-muted-foreground truncate" title={role}>
                {role}
              </span>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-3 pt-2">
        <div className="flex justify-between items-center">
          <div className="text-xs text-muted-foreground capitalize">{data.type} Node</div>
          {model && (
            <div className="text-[10px] px-1.5 py-0.5 bg-primary/10 text-primary rounded-full font-mono">
              {model}
            </div>
          )}
        </div>
        {conditionExpression && (
          <p className="mt-2 text-[11px] font-mono bg-muted/60 rounded px-2 py-1 text-muted-foreground line-clamp-2">
            {conditionExpression}
          </p>
        )}
        {ragSource && (
          <p className="mt-2 text-[11px] text-muted-foreground truncate">
            Source: {ragSource}
          </p>
        )}
        {toolId && (
          <p className="mt-2 text-[11px] font-mono bg-muted/60 rounded px-2 py-1 text-muted-foreground truncate">
            Tool: {toolId}
          </p>
        )}
      </CardContent>

      {data.type !== "start" && (
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 bg-muted-foreground border-2 border-background"
        />
      )}
      
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-muted-foreground border-2 border-background"
      />
    </Card>
  );
});
