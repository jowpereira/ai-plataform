import { useMemo, useCallback, useEffect, memo, useState } from "react";
import {
  MoreVertical,
  Map,
  Grid3X3,
  RotateCcw,
  Maximize,
  Shuffle,
  Zap,
  ArrowDown,
  ArrowLeftRight,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  BackgroundVariant,
  type NodeTypes,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { ExecutorNode, type ExecutorNodeData } from "./executor-node";
import {
  convertWorkflowDumpToNodes,
  convertWorkflowDumpToEdges,
  applyDagreLayout,
  processWorkflowEvents,
  updateNodesWithEvents,
  updateEdgesWithSequenceAnalysis,
  consolidateBidirectionalEdges,
  type NodeUpdate,
} from "@/utils/workflow-utils";
import type { ExtendedResponseStreamEvent } from "@/types";
import type { Workflow } from "@/types/workflow";
import { NodePropertiesPanel } from "./node-properties-panel";

const nodeTypes: NodeTypes = {
  executor: ExecutorNode,
};

// ViewOptions panel component that renders inside ReactFlow
function ViewOptionsPanel({
  workflowDump,
  onNodeSelect,
  viewOptions,
  onToggleViewOption,
  layoutDirection,
  onLayoutDirectionChange,
}: {
  workflowDump?: Workflow;
  onNodeSelect?: (executorId: string, data: ExecutorNodeData) => void;
  viewOptions: { showMinimap: boolean; showGrid: boolean; animateRun: boolean; consolidateBidirectionalEdges: boolean };
  onToggleViewOption?: (key: keyof typeof viewOptions) => void;
  layoutDirection: "LR" | "TB";
  onLayoutDirectionChange?: (direction: "LR" | "TB") => void;
}) {
  const { fitView, setViewport, setNodes } = useReactFlow();

  const handleResetZoom = () => {
    setViewport({ x: 0, y: 0, zoom: 1 });
  };

  const handleFitToScreen = () => {
    fitView({ padding: 0.2 });
  };

  const handleAutoArrange = () => {
    if (!workflowDump) return;
    const currentNodes = convertWorkflowDumpToNodes(
      workflowDump,
      onNodeSelect,
      layoutDirection
    );
    const currentEdges = convertWorkflowDumpToEdges(workflowDump);
    const layoutedNodes = applyDagreLayout(
      currentNodes,
      currentEdges,
      layoutDirection
    );
    setNodes(layoutedNodes);
  };

  return (
    <div className="absolute top-4 right-4 z-10">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="h-8 w-8 p-0 bg-white/90 backdrop-blur-sm border-gray-200 shadow-sm hover:bg-white dark:bg-gray-800/90 dark:border-gray-600 dark:hover:bg-gray-800"
          >
            <MoreVertical className="h-4 w-4" />
            <span className="sr-only">View options</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuItem
            className="flex items-center justify-between"
            onClick={() => onToggleViewOption?.("showMinimap")}
          >
            <div className="flex items-center">
              <Map className="mr-2 h-4 w-4" />
              Show Minimap
            </div>
            <Checkbox checked={viewOptions.showMinimap} onChange={() => {}} />
          </DropdownMenuItem>
          <DropdownMenuItem
            className="flex items-center justify-between"
            onClick={() => onToggleViewOption?.("showGrid")}
          >
            <div className="flex items-center">
              <Grid3X3 className="mr-2 h-4 w-4" />
              Show Grid
            </div>
            <Checkbox checked={viewOptions.showGrid} onChange={() => {}} />
          </DropdownMenuItem>
          <DropdownMenuItem
            className="flex items-center justify-between"
            onClick={() => onToggleViewOption?.("animateRun")}
          >
            <div className="flex items-center">
              <Zap className="mr-2 h-4 w-4" />
              Animate Run
            </div>
            <Checkbox checked={viewOptions.animateRun} onChange={() => {}} />
          </DropdownMenuItem>
          <DropdownMenuItem
            className="flex items-center justify-between"
            onClick={() => onToggleViewOption?.("consolidateBidirectionalEdges")}
          >
            <div className="flex items-center">
              <ArrowLeftRight className="mr-2 h-4 w-4" />
              Merge Bidirectional Edges
            </div>
            <Checkbox checked={viewOptions.consolidateBidirectionalEdges} onChange={() => {}} />
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="flex items-center justify-between"
            onClick={() => {
              const newDirection = layoutDirection === "LR" ? "TB" : "LR";
              onLayoutDirectionChange?.(newDirection);
              // Re-apply layout with new direction
              if (workflowDump) {
                const currentNodes = convertWorkflowDumpToNodes(
                  workflowDump,
                  onNodeSelect,
                  newDirection
                );
                const currentEdges = convertWorkflowDumpToEdges(workflowDump);
                const layoutedNodes = applyDagreLayout(
                  currentNodes,
                  currentEdges,
                  newDirection
                );
                setNodes(layoutedNodes);
              }
            }}
          >
            <div className="flex items-center">
              <ArrowDown className="mr-2 h-4 w-4" />
              Vertical Layout
            </div>
            <Checkbox checked={layoutDirection === "TB"} onChange={() => {}} />
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleResetZoom}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Reset Zoom
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleFitToScreen}>
            <Maximize className="mr-2 h-4 w-4" />
            Fit to Screen
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleAutoArrange}>
            <Shuffle className="mr-2 h-4 w-4" />
            Auto-arrange
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

interface WorkflowFlowProps {
  workflowDump?: Workflow;
  events: ExtendedResponseStreamEvent[];
  isStreaming: boolean;
  onNodeSelect?: (executorId: string, data: ExecutorNodeData) => void;
  className?: string;
  viewOptions?: {
    showMinimap: boolean;
    showGrid: boolean;
    animateRun: boolean;
    consolidateBidirectionalEdges: boolean;
  };
  onToggleViewOption?: (
    key: keyof NonNullable<WorkflowFlowProps["viewOptions"]>
  ) => void;
  layoutDirection?: "LR" | "TB";
  onLayoutDirectionChange?: (direction: "LR" | "TB") => void;
  timelineVisible?: boolean;
  onWorkflowChange?: (nodes: Node[], edges: Edge[]) => void;
}

// Animation handler component that runs inside ReactFlow context
function WorkflowAnimationHandler({
  nodes,
  nodeUpdates,
  isStreaming,
  animateRun,
}: {
  nodes: Node<ExecutorNodeData>[];
  nodeUpdates: Record<string, NodeUpdate>;
  isStreaming: boolean;
  animateRun: boolean;
}) {
  const { fitView } = useReactFlow();

  // Smooth animation to center on running node when workflow starts/progresses
  useEffect(() => {
    if (!animateRun) return;

    if (isStreaming) {
      // Zoom in on running nodes during execution
      const runningNodes = nodes.filter(
        (node) => node.data.state === "running"
      );
      if (runningNodes.length > 0) {
        const targetNode = runningNodes[0];

        // Use fitView to smoothly focus on the running node with animation
        fitView({
          nodes: [targetNode],
          duration: 800,
          padding: 0.3,
          minZoom: 0.8,
          maxZoom: 1.5,
        });
      }
    } else if (nodes.length > 0) {
      // Zoom back out to show full workflow when execution completes
      fitView({
        duration: 1000,
        padding: 0.2,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeUpdates, isStreaming, animateRun, nodes]);

  return null; // This component doesn't render anything
}

// Timeline resize handler component that runs inside ReactFlow context
const TimelineResizeHandler = memo(({ timelineVisible }: { timelineVisible: boolean }) => {
  const { fitView } = useReactFlow();

  // Trigger fitView when timeline visibility changes to adjust ReactFlow viewport
  useEffect(() => {
    // Delay fitView to let CSS transition complete (timeline animation is 300ms)
    const timeoutId = setTimeout(() => {
      fitView({ padding: 0.2, duration: 300 });
    }, 350); // Slightly longer than timeline animation duration

    return () => clearTimeout(timeoutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timelineVisible]); // Only trigger when timelineVisible changes, not fitView reference

  return null; // This component doesn't render anything
});

export function WorkflowFlow({
  workflowDump,
  events = [],
  isStreaming = false,
  onNodeSelect,
  className,
  viewOptions = { showMinimap: true, showGrid: true, animateRun: true, consolidateBidirectionalEdges: true },
  onToggleViewOption,
  layoutDirection = "LR",
  onLayoutDirectionChange,
  timelineVisible = false,
  onWorkflowChange,
}: WorkflowFlowProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<ExecutorNodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [rfInstance, setRfInstance] = useState<any>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Notify parent of changes
  useEffect(() => {
    if (onWorkflowChange) {
      onWorkflowChange(nodes, edges);
    }
  }, [nodes, edges, onWorkflowChange]);

  // Create initial nodes and edges from workflow dump
  const { initialNodes, initialEdges } = useMemo(() => {
    if (!workflowDump) {
      return { initialNodes: [], initialEdges: [] };
    }

    const nodes = convertWorkflowDumpToNodes(
      workflowDump,
      onNodeSelect,
      layoutDirection
    );
    const edges = convertWorkflowDumpToEdges(workflowDump);

    // Apply bidirectional edge consolidation if enabled
    const finalEdges = viewOptions.consolidateBidirectionalEdges
      ? consolidateBidirectionalEdges(edges)
      : edges;

    // Apply auto-layout if we have nodes and edges
    const layoutedNodes =
      nodes.length > 0
        ? applyDagreLayout(nodes, finalEdges, layoutDirection)
        : nodes;

    return {
      initialNodes: layoutedNodes,
      initialEdges: finalEdges,
    };
  }, [workflowDump, onNodeSelect, layoutDirection, viewOptions.consolidateBidirectionalEdges]);

  // Process events and update node/edge states
  const nodeUpdates = useMemo(() => {
    return processWorkflowEvents(events, workflowDump?.start_executor_id);
  }, [events, workflowDump?.start_executor_id]);

  // Update nodes and edges with real-time state from events
  useMemo(() => {
    if (Object.keys(nodeUpdates).length > 0) {
      setNodes((currentNodes) =>
        updateNodesWithEvents(currentNodes, nodeUpdates)
      );
    } else if (events.length === 0) {
      // Reset all nodes to pending state when events are cleared
      setNodes((currentNodes) =>
        currentNodes.map((node) => ({
          ...node,
          data: {
            ...node.data,
            state: "pending" as const,
            outputData: undefined,
            error: undefined,
          },
        }))
      );
    }
  }, [nodeUpdates, setNodes, events.length]);

  // Update edges with sequence-based analysis (separate from nodeUpdates)
  useMemo(() => {
    if (events.length > 0) {
      setEdges((currentEdges) => {
        const updatedEdges = updateEdgesWithSequenceAnalysis(
          currentEdges,
          events
        );
        // Apply consolidation if enabled (preserves updated styling from sequence analysis)
        return viewOptions.consolidateBidirectionalEdges
          ? consolidateBidirectionalEdges(updatedEdges)
          : updatedEdges;
      });
    } else {
      // Reset all edges to default state when events are cleared
      setEdges((currentEdges) => {
        const resetEdges = currentEdges.map((edge) => ({
          ...edge,
          animated: false,
          style: {
            stroke: "#6b7280", // Gray
            strokeWidth: 2,
          },
        }));
        // Apply consolidation if enabled
        return viewOptions.consolidateBidirectionalEdges
          ? consolidateBidirectionalEdges(resetEdges)
          : resetEdges;
      });
    }
  }, [events, setEdges, viewOptions.consolidateBidirectionalEdges]);

  // Initialize nodes and edges when workflow structure OR consolidation setting changes
  useEffect(() => {
    if (initialNodes.length > 0) {
      setNodes(initialNodes);
      setEdges(initialEdges);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflowDump, viewOptions.consolidateBidirectionalEdges]); // Re-initialize when workflow or consolidation toggle changes

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNodeId(node.id);
      if (onNodeSelect) {
        onNodeSelect(node.data.executorId as string, node.data as ExecutorNodeData);
      }
    },
    [onNodeSelect]
  );

  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
    if (onNodeSelect) {
      // @ts-ignore
      onNodeSelect(null, null);
    }
  }, [onNodeSelect]);

  const handleNodeUpdate = (nodeId: string, newData: any) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return { ...node, data: { ...node.data, ...newData } };
        }
        return node;
      })
    );
  };

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      const toolId = event.dataTransfer.getData('application/toolId');
      const dataString = event.dataTransfer.getData('application/reactflow-data');
      
      // check if the dropped element is valid
      if (typeof type === 'undefined' || !type) {
        return;
      }

      let label = `${type} node`;
      let additionalData = {};
      if (dataString) {
        try {
          const data = JSON.parse(dataString);
          if (data.label) {
            label = data.label;
          }
          additionalData = data;
        } catch (e) {
          console.error("Failed to parse drop data", e);
        }
      }

      const position = rfInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });
      
      const nodeId = `node_${Date.now()}`;
      const newNode: Node<ExecutorNodeData> = {
        id: nodeId,
        type: 'executor',
        position,
        data: { 
          executorId: nodeId,
          name: label,
          executorType: type,
          tool_id: toolId,
          state: 'pending',
          ...additionalData
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [rfInstance, setNodes],
  );

  const selectedNode = useMemo(() => {
    return nodes.find((n) => n.id === selectedNodeId) || null;
  }, [nodes, selectedNodeId]);

  return (
    <div className={`relative w-full h-full ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onInit={setRfInstance}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-right"
        minZoom={0.1}
        maxZoom={2}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={12}
          size={1}
          className={viewOptions.showGrid ? "" : "hidden"}
        />
        <Controls />
        {viewOptions.showMinimap && <MiniMap />}
        
        <ViewOptionsPanel
          workflowDump={workflowDump}
          onNodeSelect={onNodeSelect}
          viewOptions={viewOptions}
          onToggleViewOption={onToggleViewOption}
          layoutDirection={layoutDirection}
          onLayoutDirectionChange={onLayoutDirectionChange}
        />

        <WorkflowAnimationHandler
          nodes={nodes}
          nodeUpdates={nodeUpdates}
          isStreaming={isStreaming}
          animateRun={viewOptions.animateRun}
        />
        
        <TimelineResizeHandler timelineVisible={timelineVisible} />
      </ReactFlow>

      {/* Node Properties Panel Overlay */}
      {selectedNode && (
        <div className="absolute top-0 right-0 bottom-0 z-10">
          <NodePropertiesPanel 
            node={selectedNode} 
            onUpdate={handleNodeUpdate}
            onClose={() => setSelectedNodeId(null)}
          />
        </div>
      )}
    </div>
  );
}
