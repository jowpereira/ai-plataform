import { useRef, useState, useCallback } from "react";
import { Upload, FileText, Trash2, File, Loader2, CloudUpload, Clock, Hash } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { KnowledgeCollection, KnowledgeDocument } from "@/services/api";
import { formatDistanceToNow } from "date-fns";
import { ptBR } from "date-fns/locale";

interface DocumentListProps {
  collection: KnowledgeCollection | null;
  documents: KnowledgeDocument[];
  isLoading: boolean;
  isUploading: boolean;
  onUpload: (files: File[]) => Promise<void> | void;
  onDelete: (id: string) => Promise<void> | void;
}

const FILE_ICONS: Record<string, string> = {
  "application/pdf": "📄",
  "text/csv": "📊",
  "text/plain": "📝",
  "text/markdown": "📑",
  "application/json": "🔧",
};

const getFileIcon = (contentType: string | null | undefined): string => {
  if (!contentType) return "📎";
  return FILE_ICONS[contentType] || "📎";
};

export function DocumentList({
  collection,
  documents,
  isLoading,
  isUploading,
  onUpload,
  onDelete,
}: DocumentListProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const getDocumentType = (doc: KnowledgeDocument): string | undefined => {
    if (typeof doc.content_type === "string" && doc.content_type.length > 0) {
      return doc.content_type;
    }
    const metadataType = doc.metadata?.file_type;
    if (typeof metadataType === "string" && metadataType.length > 0) {
      return metadataType;
    }
    return undefined;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(Array.from(e.target.files));
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onUpload(files);
    }
  }, [onUpload]);

  if (!collection) {
    return (
      <div className="h-full flex flex-col items-center justify-center border rounded-xl bg-gradient-to-b from-muted/20 to-muted/5 text-muted-foreground p-8 text-center">
        <div className="p-6 bg-muted/30 rounded-full mb-6">
          <FileText className="h-12 w-12 opacity-30" />
        </div>
        <h3 className="text-lg font-medium mb-2">Nenhuma coleção selecionada</h3>
        <p className="text-sm max-w-xs text-muted-foreground">
          Selecione uma coleção no painel da esquerda para visualizar e gerenciar seus documentos.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full border rounded-xl bg-background shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between bg-muted/20">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <File className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-sm">{collection.name}</h3>
            <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
              <span className="flex items-center gap-1">
                <FileText className="h-3 w-3" />
                {documents.length} documentos
              </span>
              <span className="flex items-center gap-1">
                <Hash className="h-3 w-3" />
                {collection.chunk_count ?? 0} chunks
              </span>
            </div>
          </div>
        </div>
        <div>
          <input
            type="file"
            multiple
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".txt,.md,.csv,.json,.pdf"
          />
          <Button 
            size="sm"
            className="h-8"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
          >
            {isUploading ? (
              <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
            ) : (
              <Upload className="h-4 w-4 mr-1.5" />
            )}
            Enviar
          </Button>
        </div>
      </div>

      {/* Content */}
      <div 
        className="flex-1 overflow-hidden"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Drag overlay */}
        {isDragOver && (
          <div className="absolute inset-0 bg-primary/5 border-2 border-dashed border-primary rounded-xl z-10 flex items-center justify-center">
            <div className="text-center">
              <CloudUpload className="h-12 w-12 text-primary mx-auto mb-3" />
              <p className="text-lg font-medium text-primary">Solte os arquivos aqui</p>
              <p className="text-sm text-muted-foreground">PDF, TXT, CSV, JSON, MD</p>
            </div>
          </div>
        )}

        <ScrollArea className="h-full">
          {isLoading && documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-60 text-muted-foreground">
              <Loader2 className="h-8 w-8 animate-spin mb-3" />
              <p className="text-sm">Carregando documentos...</p>
            </div>
          ) : documents.length === 0 ? (
            <div 
              className="flex flex-col items-center justify-center h-full min-h-[300px] text-muted-foreground p-8 cursor-pointer hover:bg-muted/10 transition-colors"
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="p-6 bg-muted/20 rounded-full mb-4 border-2 border-dashed border-muted-foreground/20">
                <CloudUpload className="h-10 w-10 opacity-40" />
              </div>
              <h4 className="font-medium text-base mb-1">Nenhum documento ainda</h4>
              <p className="text-sm text-center max-w-xs mb-4">
                Arraste e solte arquivos aqui ou clique para enviar
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {["PDF", "TXT", "CSV", "JSON", "MD"].map((type) => (
                  <Badge key={type} variant="outline" className="text-xs">
                    .{type.toLowerCase()}
                  </Badge>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-3 space-y-2">
              {documents.map((doc) => (
                <div 
                  key={doc.id}
                  className="group flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/30 transition-colors"
                >
                  {/* File icon */}
                  <div className="text-2xl shrink-0">
                    {getFileIcon(doc.content_type)}
                  </div>

                  {/* File info */}
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm truncate" title={doc.filename}>
                      {doc.filename}
                    </h4>
                    <div className="flex items-center gap-3 mt-1">
                      <Badge variant="outline" className="text-[10px] h-4 uppercase font-mono">
                        {getDocumentType(doc)?.split("/").pop() || "file"}
                      </Badge>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Hash className="h-3 w-3" />
                        {doc.chunk_count} chunks
                      </span>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDistanceToNow(new Date(doc.created_at), {
                          addSuffix: true,
                          locale: ptBR,
                        })}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className={cn(
                      "h-8 w-8 shrink-0",
                      "opacity-0 group-hover:opacity-100 transition-opacity",
                      "text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                    )}
                    onClick={() => {
                      if (confirm(`Excluir "${doc.filename}"?`)) {
                        onDelete(doc.id);
                      }
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  );
}
