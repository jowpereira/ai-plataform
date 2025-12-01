/**
 * AgentListPage - Lista de agentes do projeto
 * CRUD completo: criar, visualizar, editar, duplicar, deletar
 */

import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { AgentFormModal } from "@/components/features/studio/AgentFormModal";
import { useStudioStore } from "@/components/features/studio/studio-store";
import { apiClient } from "@/services/api";
import type { KnowledgeCollection } from "@/services/api";
import {
  Plus,
  Search,
  MoreVertical,
  Pencil,
  Copy,
  Trash2,
  Bot,
  Filter,
  Download,
  RefreshCw,
  Database,
} from "lucide-react";
import type { AgentConfig } from "@/components/features/studio/types";

export default function AgentListPage() {
  const { toast } = useToast();
  const workerConfig = useStudioStore((state) => state.workerConfig);
  const setWorkerConfig = useStudioStore((state) => state.setWorkerConfig);
  
  // Estado local
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [collections, setCollections] = useState<KnowledgeCollection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [modelFilter, setModelFilter] = useState<string>("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAgent, setEditingAgent] = useState<AgentConfig | null>(null);
  const [deletingAgent, setDeletingAgent] = useState<AgentConfig | null>(null);

  // Carregar agentes do backend
  const loadAgents = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("/v1/agents");
      if (response.ok) {
        const data = await response.json();
        setAgents(data.data || []);
        // Sincronizar com store também
        setWorkerConfig({ ...workerConfig, agents: data.data || [] });
      }
    } catch (error) {
      console.error("Erro ao carregar agentes:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Carregar coleções de conhecimento
  const loadCollections = async () => {
    try {
      const data = await apiClient.getKnowledgeCollections();
      setCollections(data);
    } catch (error) {
      console.error("Erro ao carregar coleções:", error);
    }
  };

  // Carregar na montagem
  useEffect(() => {
    loadAgents();
    loadCollections();
  }, []);

  // Modelos e ferramentas disponíveis
  const availableModels = useMemo(() => workerConfig.resources?.models || {}, [workerConfig.resources]);
  const availableTools = useMemo(() => workerConfig.resources?.tools || [], [workerConfig.resources]);

  // Lista de modelos únicos usados
  const usedModels = useMemo(() => {
    const models = new Set(agents.map((a) => a.model));
    return Array.from(models);
  }, [agents]);

  // Filtrar agentes
  const filteredAgents = useMemo(() => {
    return agents.filter((agent) => {
      const matchesSearch =
        searchQuery === "" ||
        agent.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (agent.description || "").toLowerCase().includes(searchQuery.toLowerCase());

      const matchesModel = modelFilter === "all" || agent.model === modelFilter;

      return matchesSearch && matchesModel;
    });
  }, [agents, searchQuery, modelFilter]);

  // Handlers
  const handleSaveAgent = async (agent: AgentConfig) => {
    try {
      // Salvar no backend
      const response = await fetch("/v1/agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(agent),
      });

      if (!response.ok) {
        throw new Error("Falha ao salvar agente");
      }

      // Recarregar lista
      await loadAgents();
      
      toast({ 
        title: editingAgent ? "Agente atualizado" : "Agente criado", 
        description: `${agent.role} foi salvo em exemplos/agentes/` 
      });
    } catch (error) {
      console.error("Erro ao salvar:", error);
      toast({ 
        title: "Erro ao salvar", 
        description: String(error), 
        variant: "destructive" 
      });
    }
    
    setEditingAgent(null);
    setShowCreateModal(false);
  };

  const handleDuplicate = async (agent: AgentConfig) => {
    const newAgent: AgentConfig = {
      ...agent,
      id: `${agent.id}_copy`,
      role: `${agent.role} (Cópia)`,
    };
    
    try {
      const response = await fetch("/v1/agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newAgent),
      });

      if (!response.ok) {
        throw new Error("Falha ao duplicar agente");
      }

      await loadAgents();
      toast({ title: "Agente duplicado", description: `${newAgent.role} foi criado.` });
    } catch (error) {
      toast({ title: "Erro ao duplicar", description: String(error), variant: "destructive" });
    }
  };

  const handleDelete = async () => {
    if (!deletingAgent) return;
    
    try {
      const response = await fetch(`/v1/agents/${encodeURIComponent(deletingAgent.id)}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Falha ao deletar agente");
      }

      await loadAgents();
      toast({
        title: "Agente removido",
        description: `${deletingAgent.role} foi deletado.`,
      });
    } catch (error) {
      toast({ title: "Erro ao deletar", description: String(error), variant: "destructive" });
    }
    
    setDeletingAgent(null);
  };

  const handleExportAgent = (agent: AgentConfig) => {
    // Remove campos internos antes de exportar
    const { _file, ...cleanAgent } = agent as AgentConfig & { _file?: string };
    const json = JSON.stringify(cleanAgent, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${agent.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast({ title: "Exportado", description: `${agent.role} foi baixado.` });
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] overflow-hidden">
      {/* Header */}
      <div className="h-14 border-b flex items-center justify-between px-6 bg-background shrink-0">
        <div>
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Agentes
          </h1>
          <p className="text-sm text-muted-foreground">
            {agents.length} agente{agents.length !== 1 ? "s" : ""} • exemplos/agentes/
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={loadAgents} disabled={isLoading} title="Atualizar lista">
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
          <Button size="default" className="px-4 py-2" onClick={() => setShowCreateModal(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Novo Agente
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="p-4 border-b bg-muted/30 shrink-0">
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar por nome, ID ou descrição..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={modelFilter} onValueChange={setModelFilter}>
            <SelectTrigger className="w-[180px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Filtrar por modelo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os modelos</SelectItem>
              {usedModels.map((model) => (
                <SelectItem key={model} value={model}>
                  {model}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Badge variant="secondary">
            {filteredAgents.length} de {agents.length} agentes
          </Badge>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto p-4">
        {filteredAgents.length === 0 ? (
          <Card className="max-w-md mx-auto mt-12">
            <CardContent className="p-8 text-center">
              <Bot className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">
                {agents.length === 0 ? "Nenhum agente criado" : "Nenhum resultado encontrado"}
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                {agents.length === 0
                  ? "Comece criando seu primeiro agente para usar nos workflows."
                  : "Tente ajustar os filtros de busca."}
              </p>
              {agents.length === 0 && (
                <Button onClick={() => setShowCreateModal(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Criar Primeiro Agente
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[250px]">Nome</TableHead>
                  <TableHead>ID</TableHead>
                  <TableHead>Modelo</TableHead>
                  <TableHead>Ferramentas</TableHead>
                  <TableHead>Knowledge</TableHead>
                  <TableHead className="w-[100px] text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAgents.map((agent) => (
                  <TableRow key={agent.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Bot className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{agent.role}</p>
                          {agent.description && (
                            <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                              {agent.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                        {agent.id}
                      </code>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{agent.model}</Badge>
                    </TableCell>
                    <TableCell>
                      {agent.tools && agent.tools.length > 0 ? (
                        <div className="flex gap-1">
                          {agent.tools.slice(0, 2).map((t) => (
                            <Badge key={t} variant="secondary" className="text-xs">
                              {t}
                            </Badge>
                          ))}
                          {agent.tools.length > 2 && (
                            <Badge variant="secondary" className="text-xs">
                              +{agent.tools.length - 2}
                            </Badge>
                          )}
                        </div>
                      ) : (
                        <span className="text-muted-foreground text-sm">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {agent.knowledge && agent.knowledge.enabled && agent.knowledge.collection_ids.length > 0 ? (
                        <Badge variant="outline" className="gap-1">
                          <Database className="h-3 w-3" />
                          {agent.knowledge.collection_ids.length} coleção{agent.knowledge.collection_ids.length > 1 ? "ões" : ""}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground text-sm">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => setEditingAgent(agent)}>
                            <Pencil className="h-4 w-4 mr-2" />
                            Editar
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDuplicate(agent)}>
                            <Copy className="h-4 w-4 mr-2" />
                            Duplicar
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleExportAgent(agent)}>
                            <Download className="h-4 w-4 mr-2" />
                            Exportar JSON
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => setDeletingAgent(agent)}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Excluir
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <AgentFormModal
        open={showCreateModal || editingAgent !== null}
        onOpenChange={(open) => {
          if (!open) {
            setShowCreateModal(false);
            setEditingAgent(null);
          }
        }}
        agent={editingAgent || undefined}
        availableModels={availableModels}
        availableTools={availableTools}
        availableCollections={collections}
        onSave={handleSaveAgent}
        mode={editingAgent ? "edit" : "create"}
      />

      {/* Delete Confirmation */}
      <AlertDialog open={deletingAgent !== null} onOpenChange={(open) => !open && setDeletingAgent(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir agente?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir <strong>{deletingAgent?.role}</strong>?
              <br />
              Esta ação não pode ser desfeita e o agente será removido de todos os workflows.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
