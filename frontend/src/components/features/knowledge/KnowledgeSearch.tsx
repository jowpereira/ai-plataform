import { useState } from "react";
import { Search, Loader2, FileText, Sparkles, Zap, X, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { KnowledgeCollection, KnowledgeSearchResult } from "@/services/api";

interface KnowledgeSearchProps {
  collections: KnowledgeCollection[];
  results: KnowledgeSearchResult[];
  isSearching: boolean;
  onSearch: (query: string, collectionId?: string, topK?: number) => Promise<void> | void;
  onClear: () => void;
}

export function KnowledgeSearch({
  collections,
  results,
  isSearching,
  onSearch,
  onClear,
}: KnowledgeSearchProps) {
  const [query, setQuery] = useState("");
  const [collectionId, setCollectionId] = useState<string>("all");
  const [topK, setTopK] = useState("5");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    onSearch(
      query,
      collectionId === "all" ? undefined : collectionId,
      parseInt(topK)
    );
  };

  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return "text-green-600 bg-green-50 border-green-200";
    if (score >= 0.6) return "text-blue-600 bg-blue-50 border-blue-200";
    if (score >= 0.4) return "text-amber-600 bg-amber-50 border-amber-200";
    return "text-gray-600 bg-gray-50 border-gray-200";
  };

  const getScoreLabel = (score: number): string => {
    if (score >= 0.8) return "Ótimo";
    if (score >= 0.6) return "Bom";
    if (score >= 0.4) return "Regular";
    return "Baixo";
  };

  return (
    <div className="space-y-6">
      {/* Search Card */}
      <Card className="border-2 border-dashed border-primary/20 bg-gradient-to-b from-primary/5 to-transparent">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 rounded-xl">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">Busca Semântica</CardTitle>
              <CardDescription>
                Teste a recuperação da base de conhecimento com consultas em linguagem natural
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            {/* Search input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Faça uma pergunta ou descreva o que você procura..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-10 pr-24 h-12 text-base"
              />
              <Button 
                type="submit" 
                size="sm"
                disabled={isSearching || !query.trim()}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 h-9"
              >
                {isSearching ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    Buscar
                    <ArrowRight className="h-4 w-4 ml-1" />
                  </>
                )}
              </Button>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-3">
              <div className="flex-1 max-w-[250px]">
                <Select value={collectionId} onValueChange={setCollectionId}>
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Todas as coleções" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas as Coleções</SelectItem>
                    {collections.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="w-[130px]">
                <Select value={topK} onValueChange={setTopK}>
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Results" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="3">Top 3</SelectItem>
                    <SelectItem value="5">Top 5</SelectItem>
                    <SelectItem value="10">Top 10</SelectItem>
                    <SelectItem value="20">Top 20</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {results.length > 0 && (
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm"
                  className="h-9"
                  onClick={() => {
                    setQuery("");
                    onClear();
                  }}
                >
                  <X className="h-4 w-4 mr-1" />
                  Limpar
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium flex items-center gap-2">
              <Zap className="h-4 w-4 text-primary" />
              {results.length} resultados encontrados
            </h3>
            <p className="text-sm text-muted-foreground">
              Ordenados por relevância
            </p>
          </div>
          
          <div className="space-y-3">
            {results.map((result, index) => {
              const metadata = result.metadata as Record<string, unknown>;
              const filename = typeof metadata.filename === "string" ? metadata.filename : "Unknown document";
              const collectionId = typeof metadata.collection_id === "string" ? metadata.collection_id : undefined;
              const collectionName = collections.find((c) => c.id === collectionId)?.name;

              return (
                <Card 
                  key={index} 
                  className={cn(
                    "overflow-hidden transition-all hover:shadow-md",
                    "border-l-4",
                    result.score >= 0.7 ? "border-l-green-500" : 
                    result.score >= 0.5 ? "border-l-blue-500" : 
                    "border-l-gray-300"
                  )}
                >
                  <CardContent className="p-4">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-lg font-mono text-muted-foreground">
                          #{index + 1}
                        </span>
                        <div className="flex items-center gap-1.5 text-sm text-muted-foreground truncate">
                          <FileText className="h-4 w-4 shrink-0" />
                          <span className="truncate">{filename}</span>
                        </div>
                        {collectionName && (
                          <Badge variant="outline" className="text-[10px] shrink-0">
                            {collectionName}
                          </Badge>
                        )}
                      </div>
                      <div className={cn(
                        "flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium border shrink-0",
                        getScoreColor(result.score)
                      )}>
                        <span>{(result.score * 100).toFixed(0)}%</span>
                        <span className="text-[10px] opacity-70">{getScoreLabel(result.score)}</span>
                      </div>
                    </div>

                    {/* Content */}
                    <div className="bg-muted/30 p-4 rounded-lg text-sm leading-relaxed">
                      {result.content}
                    </div>

                    {/* Footer */}
                    <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="font-mono">
                        Chunk: {result.chunk_id.slice(0, 8)}...
                      </span>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isSearching && results.length === 0 && query === "" && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <div className="p-4 bg-muted/30 rounded-full mb-4">
              <Search className="h-8 w-8 text-muted-foreground/50" />
            </div>
            <h3 className="font-medium mb-2">Pronto para buscar</h3>
            <p className="text-sm text-muted-foreground max-w-md">
              Digite uma consulta acima para testar a recuperação semântica da sua base de conhecimento.
              Os resultados serão ordenados por score de similaridade.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
