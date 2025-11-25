/**
 * WorkflowListPage - Lista de workflows do projeto
 * CRUD: visualizar, editar, deletar
 * Base: pasta exemplos/workflows/
 */

import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
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
import {
  Plus,
  Search,
  MoreVertical,
  Pencil,
  Trash2,
  GitFork,
  RefreshCw,
  Play,
  FileJson,
} from "lucide-react";
import { ApiClient, type SavedWorkflow } from "@/services/api";

export default function WorkflowListPage() {
  const { toast } = useToast();
  const navigate = useNavigate();
  const api = useMemo(() => new ApiClient(), []);
  
  // Estado local
  const [workflows, setWorkflows] = useState<SavedWorkflow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [deletingWorkflow, setDeletingWorkflow] = useState<SavedWorkflow | null>(null);

  // Carregar workflows salvos da pasta exemplos/workflows/
  const loadWorkflows = async () => {
    setIsLoading(true);
    try {
      const data = await api.getSavedWorkflows();
      setWorkflows(data || []);
    } catch (error) {
      console.error("Erro ao carregar workflows:", error);
      toast({ 
        title: "Erro ao carregar workflows", 
        description: String(error), 
        variant: "destructive" 
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Carregar na montagem
  useEffect(() => {
    loadWorkflows();
  }, []);

  // Filtrar workflows
  const filteredWorkflows = useMemo(() => {
    return workflows.filter((workflow) => {
      const matchesSearch =
        searchQuery === "" ||
        (workflow.name || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (workflow._file || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (workflow.workflow?.type || "").toLowerCase().includes(searchQuery.toLowerCase());

      return matchesSearch;
    });
  }, [workflows, searchQuery]);

  // Handlers
  const handleCreate = () => {
    navigate("/platform/studio");
  };

  const handleEdit = (workflow: SavedWorkflow) => {
    // Passa o nome do arquivo para o studio carregar
    navigate(`/platform/studio?file=${encodeURIComponent(workflow._file)}`);
  };

  const handleDelete = async () => {
    if (!deletingWorkflow) return;
    
    try {
      await api.deleteSavedWorkflow(deletingWorkflow._file);

      await loadWorkflows();
      toast({
        title: "Workflow removido",
        description: `${deletingWorkflow.name} foi deletado.`,
      });
    } catch (error) {
      toast({ title: "Erro ao deletar", description: String(error), variant: "destructive" });
    } finally {
      setDeletingWorkflow(null);
    }
  };

  // Helper para contar agentes
  const getAgentCount = (workflow: SavedWorkflow) => {
    return workflow.agents?.length || 0;
  };

  // Helper para contar steps
  const getStepCount = (workflow: SavedWorkflow) => {
    return workflow.workflow?.steps?.length || 0;
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Workflows</h1>
          <p className="text-muted-foreground">
            Gerencie os fluxos de trabalho salvos em <code className="text-xs bg-muted px-1 rounded">exemplos/workflows/</code>
          </p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          Novo Workflow
        </Button>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-6 gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar workflows..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8"
              />
            </div>
            <Button variant="outline" size="icon" onClick={loadWorkflows} title="Recarregar">
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Arquivo</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Agentes</TableHead>
                  <TableHead>Steps</TableHead>
                  <TableHead className="w-[100px]">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center">
                      Carregando...
                    </TableCell>
                  </TableRow>
                ) : filteredWorkflows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center">
                      <div className="flex flex-col items-center gap-2">
                        <FileJson className="h-8 w-8 text-muted-foreground" />
                        <p>Nenhum workflow encontrado.</p>
                        <Button variant="outline" size="sm" onClick={handleCreate}>
                          <Plus className="mr-2 h-4 w-4" />
                          Criar primeiro workflow
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredWorkflows.map((workflow) => (
                    <TableRow key={workflow._file}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <GitFork className="h-4 w-4 text-muted-foreground" />
                          {workflow.name || workflow._file}
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {workflow._file}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {workflow.workflow?.type || "unknown"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {getAgentCount(workflow)} agentes
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {getStepCount(workflow)} steps
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <span className="sr-only">Abrir menu</span>
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleEdit(workflow)}>
                              <Pencil className="mr-2 h-4 w-4" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => navigate(`/platform/chat?workflow=${encodeURIComponent(workflow.name || workflow._file)}`)}>
                              <Play className="mr-2 h-4 w-4" />
                              Executar
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              className="text-destructive focus:text-destructive"
                              onClick={() => setDeletingWorkflow(workflow)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Excluir
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <AlertDialog open={!!deletingWorkflow} onOpenChange={(open) => !open && setDeletingWorkflow(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Você tem certeza?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. Isso excluirá permanentemente o workflow
              <span className="font-semibold text-foreground"> {deletingWorkflow?.name || deletingWorkflow?._file} </span>
              e removerá o arquivo do disco.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
