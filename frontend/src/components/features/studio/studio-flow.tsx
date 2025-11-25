import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  type NodeTypes,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useStudioStore, type StudioNodeType } from "./studio-store";
import { StudioNode } from "./nodes/studio-node";

const AVAILABLE_NODES: StudioNodeType[] = [
  "start",
  "agent",
  "router",
  "handoff",
  "condition",
  "rag",
  "tool",
];

const isStudioNodeType = (value: string): value is StudioNodeType =>
  AVAILABLE_NODES.includes(value as StudioNodeType);

export function StudioFlow() {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
  } = useStudioStore();

  const { screenToFlowPosition } = useReactFlow();

  const nodeTypes = useMemo<NodeTypes>(() => ({
    studioNode: StudioNode,
  }), []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData("application/reactflow");

      // check if the dropped element is valid
      if (typeof type === "undefined" || !type || !isStudioNodeType(type)) {
        return;
      }

      // Get extra data if available
      const dataString = event.dataTransfer.getData("application/reactflow-data");
      let initialData: Record<string, unknown> | undefined;
      
      if (dataString) {
          try {
              initialData = JSON.parse(dataString);
          } catch (e) {
              console.error("Failed to parse drop data", e);
          }
      }

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      addNode(type, position, initialData);
    },
    [addNode, screenToFlowPosition]
  );

  return (
    <div className="h-full w-full bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        onDragOver={onDragOver}
        onDrop={onDrop}
        fitView
        minZoom={0.1}
        maxZoom={1.5}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      >
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
