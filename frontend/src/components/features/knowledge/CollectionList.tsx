import { Plus, Trash2, Folder, Database, Calendar, RefreshCw, FileText, Hash } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { KnowledgeCollection } from "@/services/api";
import { formatDistanceToNow } from "date-fns";
import { ptBR } from "date-fns/locale";

interface CollectionListProps {
  collections: KnowledgeCollection[];
  selectedId: string | null;
  isLoading: boolean;
  onSelect: (collection: KnowledgeCollection) => void;
  onDelete: (id: string) => Promise<void> | void;
  onRefresh: () => Promise<void> | void;
  onCreateNew: () => void;
}

export function CollectionList({
  collections,
  selectedId,
  isLoading,
  onSelect,
  onDelete,
  onRefresh,
  onCreateNew,
}: CollectionListProps) {
  return (
    <div className="flex flex-col h-full border rounded-xl bg-background shadow-sm">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between bg-muted/20">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Database className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-sm">Coleções</h3>
            <p className="text-xs text-muted-foreground">{collections.length} total</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => onRefresh()}
            disabled={isLoading}
            title="Atualizar coleções"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
          <Button size="sm" className="h-8" onClick={onCreateNew}>
            <Plus className="h-4 w-4 mr-1" />
            Nova
          </Button>
        </div>
      </div>

      {/* List */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1.5">
          {isLoading && collections.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <RefreshCw className="h-6 w-6 animate-spin mb-2" />
              <p className="text-sm">Carregando coleções...</p>
            </div>
          ) : collections.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center px-4">
              <div className="p-4 bg-muted/30 rounded-full mb-4">
                <Database className="h-8 w-8 text-muted-foreground/50" />
              </div>
              <h4 className="font-medium text-sm mb-1">Nenhuma coleção ainda</h4>
              <p className="text-xs text-muted-foreground mb-4">
                Crie sua primeira coleção para começar a organizar documentos.
              </p>
              <Button size="sm" variant="outline" onClick={onCreateNew}>
                <Plus className="h-4 w-4 mr-1" />
                Criar Coleção
              </Button>
            </div>
          ) : (
            collections.map((collection) => (
              <div
                key={collection.id}
                className={cn(
                  "group relative p-3 rounded-lg border cursor-pointer transition-all duration-200",
                  "hover:shadow-md hover:border-primary/30",
                  selectedId === collection.id
                    ? "bg-primary/5 border-primary/50 shadow-sm ring-1 ring-primary/20"
                    : "bg-card hover:bg-accent/30"
                )}
                onClick={() => onSelect(collection)}
              >
                {/* Selection indicator */}
                {selectedId === collection.id && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-full" />
                )}

                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2.5 min-w-0 flex-1">
                    <div className={cn(
                      "p-1.5 rounded-md mt-0.5 shrink-0",
                      selectedId === collection.id 
                        ? "bg-primary/20 text-primary" 
                        : "bg-muted text-muted-foreground"
                    )}>
                      <Folder className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h4 className="font-medium text-sm truncate leading-tight">
                        {collection.name}
                      </h4>
                      {collection.description && (
                        <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                          {collection.description}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <Button
                    variant="ghost"
                    size="icon"
                    className={cn(
                      "h-7 w-7 shrink-0 transition-all",
                      "opacity-0 group-hover:opacity-100",
                      "text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                    )}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm("Excluir esta coleção? Todos os documentos serão removidos.")) {
                        onDelete(collection.id);
                      }
                    }}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>

                {/* Stats row */}
                <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-dashed">
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <FileText className="h-3 w-3" />
                      <span>{collection.document_count}</span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Hash className="h-3 w-3" />
                      <span>{collection.chunk_count}</span>
                    </div>
                  </div>
                  <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDistanceToNow(new Date(collection.updated_at), {
                      addSuffix: true,
                      locale: ptBR,
                    })}
                  </span>
                </div>

                {/* Tags */}
                {collection.tags && collection.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {collection.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-[10px] h-4 px-1.5">
                        {tag}
                      </Badge>
                    ))}
                    {collection.tags.length > 3 && (
                      <Badge variant="outline" className="text-[10px] h-4 px-1.5">
                        +{collection.tags.length - 3}
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
