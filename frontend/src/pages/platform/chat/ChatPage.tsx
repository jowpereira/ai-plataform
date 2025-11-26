import { useEffect, useState } from "react";
import { apiClient } from "@/services/api";
import { AssistantChat } from "@/components/features/chat/AssistantChat";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card } from "@/components/ui/card";

export default function ChatPage() {
  const [entities, setEntities] = useState<{ agents: any[]; workflows: any[] }>({
    agents: [],
    workflows: [],
  });
  const [selectedEntityId, setSelectedEntityId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadEntities() {
      try {
        const { agents, workflows } = await apiClient.getEntities();
        setEntities({ agents, workflows });

        const allEntities = [...agents, ...workflows];

        if (allEntities.length > 0) {
          // Try to preserve selection from URL or default to first
          const params = new URLSearchParams(window.location.search);
          const urlEntity = params.get("entity");
          if (urlEntity && allEntities.find((e) => e.id === urlEntity)) {
            setSelectedEntityId(urlEntity);
          } else {
            setSelectedEntityId(allEntities[0].id);
          }
        }
      } catch (error) {
        console.error("Failed to load entities", error);
      } finally {
        setLoading(false);
      }
    }
    loadEntities();
  }, []);

  const handleEntityChange = (value: string) => {
    setSelectedEntityId(value);
    // Update URL without reload
    const url = new URL(window.location.href);
    url.searchParams.set("entity", value);
    window.history.pushState({}, "", url);
  };

  if (loading) return <div className="p-4">Loading entities...</div>;

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] p-4 gap-4">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">Chat</h1>
        <div className="w-[300px]">
          <Select value={selectedEntityId} onValueChange={handleEntityChange}>
            <SelectTrigger>
              <SelectValue placeholder="Select an entity" />
            </SelectTrigger>
            <SelectContent>
              {entities.agents.length > 0 && (
                <SelectGroup>
                  <SelectLabel>Agents</SelectLabel>
                  {entities.agents.map((agent) => (
                    <SelectItem key={agent.id} value={agent.id}>
                      {agent.name}
                    </SelectItem>
                  ))}
                </SelectGroup>
              )}
              {entities.workflows.length > 0 && (
                <SelectGroup>
                  <SelectLabel>Workflows</SelectLabel>
                  {entities.workflows.map((workflow) => (
                    <SelectItem key={workflow.id} value={workflow.id}>
                      {workflow.name}
                    </SelectItem>
                  ))}
                </SelectGroup>
              )}
            </SelectContent>
          </Select>
        </div>
      </div>

      {selectedEntityId ? (
        <AssistantChat key={selectedEntityId} entityId={selectedEntityId} />
      ) : (
        <Card className="flex-1 flex items-center justify-center text-muted-foreground">
          Select an agent or workflow to start chatting
        </Card>
      )}
    </div>
  );
}
