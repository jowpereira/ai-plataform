/**
 * WorkflowTypeSelector - Seletor visual de tipo de workflow
 * Exibe cards para cada tipo de builder de alto nível
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  ArrowRight, 
  GitBranch, 
  Users, 
  ArrowRightLeft, 
  GitFork,
  Sparkles,
  // Network // TODO: Reativar DAG quando validação estiver pronta
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { WorkflowType } from "./types";

interface WorkflowTypeOption {
  type: WorkflowType;
  name: string;
  description: string;
  icon: React.ElementType;
  color: string;
  example: string;
}

const workflowTypes: WorkflowTypeOption[] = [
  {
    type: "sequential",
    name: "Sequential",
    description: "Cadeia linear de agentes onde cada um processa e passa para o próximo",
    icon: ArrowRight,
    color: "border-blue-500 hover:border-blue-400",
    example: "Pesquisador → Escritor → Revisor",
  },
  {
    type: "parallel",
    name: "Parallel",
    description: "Execução simultânea de múltiplos agentes com agregação de resultados",
    icon: GitBranch,
    color: "border-green-500 hover:border-green-400",
    example: "Dispatcher → [Agente1, Agente2, Agente3] → Aggregator",
  },
  {
    type: "group_chat",
    name: "Group Chat",
    description: "Discussão multi-agente coordenada por um Manager",
    icon: Users,
    color: "border-purple-500 hover:border-purple-400",
    example: "Manager coordena: Dev, Designer, PM",
  },
  {
    type: "handoff",
    name: "Handoff",
    description: "Triagem com coordenador que transfere para especialistas",
    icon: ArrowRightLeft,
    color: "border-orange-500 hover:border-orange-400",
    example: "Triagem → Vendas | Suporte | Financeiro",
  },
  {
    type: "router",
    name: "Router",
    description: "Roteamento condicional baseado na saída do primeiro agente",
    icon: GitFork,
    color: "border-cyan-500 hover:border-cyan-400",
    example: "Classificador → [Destino A | Destino B | Default]",
  },
  {
    type: "magentic",
    name: "Magentic One",
    description: "Orquestração AI-driven com planejamento dinâmico e replanning",
    icon: Sparkles,
    color: "border-violet-500 hover:border-violet-400",
    example: "Manager planeja → [Especialista1, Especialista2, ...]",
  },
  // TODO: Reativar DAG quando validação estiver pronta
  // {
  //   type: "dag",
  //   name: "DAG (Advanced)",
  //   description: "Grafo direcionado acíclico para workflows complexos",
  //   icon: Network,
  //   color: "border-gray-500 hover:border-gray-400",
  //   example: "Nós e arestas customizados",
  // },
];

interface WorkflowTypeSelectorProps {
  selectedType: WorkflowType;
  onTypeSelect: (type: WorkflowType) => void;
  disabled?: boolean;
}

export function WorkflowTypeSelector({ 
  selectedType, 
  onTypeSelect,
  disabled = false 
}: WorkflowTypeSelectorProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {workflowTypes.map((option) => {
        const Icon = option.icon;
        const isSelected = selectedType === option.type;
        
        return (
          <Card
            key={option.type}
            className={cn(
              "cursor-pointer transition-all duration-200 border-2",
              option.color,
              isSelected && "ring-2 ring-primary ring-offset-2",
              disabled && "opacity-50 cursor-not-allowed"
            )}
            onClick={() => !disabled && onTypeSelect(option.type)}
          >
            <CardHeader className="pb-2">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "p-2 rounded-lg",
                  isSelected ? "bg-primary text-primary-foreground" : "bg-muted"
                )}>
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle className="text-lg">{option.name}</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="mb-3">
                {option.description}
              </CardDescription>
              <div className="text-xs font-mono bg-muted/50 rounded px-2 py-1 text-muted-foreground">
                {option.example}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
