import { Card, CardContent } from "@/components/ui/card";
import { Bot, Play, GitFork, ArrowRightLeft, Split, BookOpen, Wrench, Loader2 } from "lucide-react";
import type { StudioNodeType } from "./studio-store";
import { useEffect, useState } from "react";
import { apiClient } from "@/services/api";
import type { ToolInfo } from "@/types/workflow";
import type { AgentInfo } from "@/types";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

export function StudioSidebar() {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [toolsData, entitiesData] = await Promise.all([
          apiClient.listTools(),
          apiClient.getEntities()
        ]);
        setTools(toolsData);
        setAgents(entitiesData.agents);
      } catch (err) {
        console.error("Failed to load data", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const onDragStart = (event: React.DragEvent, nodeType: string, data?: any) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    if (data) {
        event.dataTransfer.setData("application/reactflow-data", JSON.stringify(data));
        if (data.tool_id) {
             event.dataTransfer.setData("application/toolId", data.tool_id);
        }
    }
    event.dataTransfer.effectAllowed = "move";
  };

  if (loading) {
      return <div className="w-64 border-r bg-muted/10 h-full flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
  }

  return (
    <div className="w-64 border-r bg-muted/10 h-full flex flex-col">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold">Components</h2>
        <p className="text-xs text-muted-foreground">
          Drag nodes to the canvas
        </p>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-6">
            
            {/* Logic Nodes */}
            <div className="space-y-2">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Flow Logic</h3>
                <DraggableNode type="start" label="Start" icon={Play} onDragStart={onDragStart} />
                <DraggableNode type="condition" label="Condition" description="If/Else Logic" icon={Split} onDragStart={onDragStart} />
                <DraggableNode type="router" label="Router" description="Switch/Case Logic" icon={GitFork} onDragStart={onDragStart} />
                <DraggableNode type="handoff" label="Handoff" description="Transfer control" icon={ArrowRightLeft} onDragStart={onDragStart} />
            </div>

            <Separator />

            {/* Agents */}
            <div className="space-y-2">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Agents</h3>
                <DraggableNode type="agent" label="Generic Agent" description="Empty Agent Node" icon={Bot} onDragStart={onDragStart} />
                {agents.map(agent => (
                    <DraggableNode 
                        key={agent.name} 
                        type="agent" 
                        label={agent.name || "Unnamed Agent"} 
                        description={agent.description} 
                        icon={Bot} 
                        onDragStart={onDragStart}
                        data={{ agent_name: agent.name, ...agent }}
                    />
                ))}
            </div>

            <Separator />

            {/* Tools */}
            <div className="space-y-2">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Tools</h3>
                 <DraggableNode type="tool" label="Generic Tool" description="Empty Tool Node" icon={Wrench} onDragStart={onDragStart} />
                 <DraggableNode type="rag" label="RAG Knowledge" description="Retrieve & Generate" icon={BookOpen} onDragStart={onDragStart} />
                 
                 {tools.map(tool => (
                    <DraggableNode 
                        key={tool.id} 
                        type="tool" 
                        label={tool.name} 
                        description={tool.description} 
                        icon={Wrench} 
                        onDragStart={onDragStart}
                        data={{ tool_id: tool.id, ...tool }}
                    />
                ))}
            </div>

        </div>
      </ScrollArea>
    </div>
  );
}

interface DraggableNodeProps {
  type: StudioNodeType;
  label: string;
  icon: React.ElementType;
  description?: string;
  onDragStart: (event: React.DragEvent, nodeType: string, data?: any) => void;
  data?: any;
}

function DraggableNode({ type, label, description, icon: Icon, onDragStart, data }: DraggableNodeProps) {
  return (
    <Card
      className="cursor-grab hover:border-primary transition-colors"
      draggable
      onDragStart={(event) => onDragStart(event, type, data)}
    >
      <CardContent className="p-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-muted">
            <Icon className="w-4 h-4" />
          </div>
          <div className="overflow-hidden">
            <div className="text-sm font-medium truncate">{label}</div>
            {description && (
              <p className="text-[11px] text-muted-foreground truncate">{description}</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
