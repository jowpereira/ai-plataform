import { useState, useEffect } from "react";
import type { Node } from "@xyflow/react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { X } from "lucide-react";

interface NodePropertiesPanelProps {
  node: Node | null;
  onUpdate: (nodeId: string, data: any) => void;
  onClose: () => void;
}

export function NodePropertiesPanel({ node, onUpdate, onClose }: NodePropertiesPanelProps) {
  const [formData, setFormData] = useState<any>({});

  useEffect(() => {
    if (node) {
      setFormData({ ...node.data });
    }
  }, [node]);

  if (!node) return null;

  const handleChange = (key: string, value: any) => {
    const newData = { ...formData, [key]: value };
    setFormData(newData);
    onUpdate(node.id, newData);
  };

  const type = (node.data?.executorType as string) || "agent";

  return (
    <div className="h-full border-l bg-background w-80 flex flex-col shadow-xl">
      <div className="p-4 border-b flex items-center justify-between bg-muted/10">
        <h3 className="font-semibold">Properties</h3>
        <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="space-y-2">
          <Label>Label</Label>
          <Input
            value={formData.label || ""}
            onChange={(e) => handleChange("label", e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label>Type</Label>
          <div className="text-sm text-muted-foreground capitalize border p-2 rounded bg-muted/5">
            {type}
          </div>
        </div>

        {/* Type Specific Fields */}
        
        {(type === "condition" || type === "router") && (
          <div className="space-y-2">
            <Label>Expression (Python)</Label>
            <Textarea
              placeholder="e.g., len(input) > 0"
              value={formData.expression || ""}
              onChange={(e) => handleChange("expression", e.target.value)}
              className="font-mono text-xs"
            />
            <p className="text-[10px] text-muted-foreground">
              Available variables: <code>input</code>, <code>value</code>
            </p>
          </div>
        )}

        {type === "tool" && (
          <div className="space-y-2">
            <Label>Tool ID</Label>
            <Input
              value={formData.tool_id || ""}
              readOnly
              className="bg-muted"
            />
          </div>
        )}

        {(type === "agent" || type === "human") && (
          <div className="space-y-2">
            <Label>Input Template</Label>
            <Textarea
              placeholder="e.g., {{user_input}}"
              value={formData.input_template || ""}
              onChange={(e) => handleChange("input_template", e.target.value)}
            />
          </div>
        )}
        
        {type === "agent" && (
           <div className="space-y-2">
            <Label>Agent ID</Label>
            <Input
              placeholder="e.g., agent_researcher"
              value={formData.agent_id || ""}
              onChange={(e) => handleChange("agent_id", e.target.value)}
            />
          </div>
        )}

      </div>
    </div>
  );
}
