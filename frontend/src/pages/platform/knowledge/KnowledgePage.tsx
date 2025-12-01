/**
 * KnowledgePage - Gerencia configurações, coleções e buscas do Knowledge Base.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { useKnowledgeStore } from "@/stores";
import { apiClient } from "@/services/api";
import {
  CollectionFormModal,
  CollectionList,
  DocumentList,
  KnowledgeFormModal,
  KnowledgeSearch,
} from "@/components/features/knowledge";
import {
  AlertCircle,
  CheckCircle2,
  Database,
  FolderOpen,
  Hash,
  Layers,
  MessageSquare,
  Pencil,
  RefreshCw,
  Search,
  Settings2,
  Sparkles,
  FileText,
  XCircle,
} from "lucide-react";

export default function KnowledgePage() {
  const { toast } = useToast();

  // ========================= Store State =========================
  const ragConfig = useKnowledgeStore((state) => state.ragConfig);
  const isLoading = useKnowledgeStore((state) => state.isLoading);
  const isSaving = useKnowledgeStore((state) => state.isSaving);
  const error = useKnowledgeStore((state) => state.error);
  const lastUpdated = useKnowledgeStore((state) => state.lastUpdated);
  const collections = useKnowledgeStore((state) => state.collections);
  const documents = useKnowledgeStore((state) => state.documents);
  const searchResults = useKnowledgeStore((state) => state.searchResults);
  const selectedCollectionId = useKnowledgeStore((state) => state.selectedCollectionId);
  const isCollectionsLoading = useKnowledgeStore((state) => state.isCollectionsLoading);
  const isDocumentsLoading = useKnowledgeStore((state) => state.isDocumentsLoading);
  const isUploading = useKnowledgeStore((state) => state.isUploading);
  const isSearching = useKnowledgeStore((state) => state.isSearching);

  // ========================= Store Actions ======================
  const setRagConfig = useKnowledgeStore((state) => state.setRagConfig);
  const setIsLoading = useKnowledgeStore((state) => state.setIsLoading);
  const setIsSaving = useKnowledgeStore((state) => state.setIsSaving);
  const setError = useKnowledgeStore((state) => state.setError);
  const setCollections = useKnowledgeStore((state) => state.setCollections);
  const addCollection = useKnowledgeStore((state) => state.addCollection);
  const removeCollection = useKnowledgeStore((state) => state.removeCollection);
  const setDocuments = useKnowledgeStore((state) => state.setDocuments);
  const removeDocument = useKnowledgeStore((state) => state.removeDocument);
  const setSearchResults = useKnowledgeStore((state) => state.setSearchResults);
  const setSelectedCollectionId = useKnowledgeStore((state) => state.setSelectedCollectionId);
  const setIsCollectionsLoading = useKnowledgeStore((state) => state.setIsCollectionsLoading);
  const setIsDocumentsLoading = useKnowledgeStore((state) => state.setIsDocumentsLoading);
  const setIsUploading = useKnowledgeStore((state) => state.setIsUploading);
  const setIsSearching = useKnowledgeStore((state) => state.setIsSearching);

  // ========================= Local State ========================
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showCollectionModal, setShowCollectionModal] = useState(false);
  const [activeTab, setActiveTab] = useState("collections");

  const selectedCollection = useMemo(
    () => collections.find((collection) => collection.id === selectedCollectionId) ?? null,
    [collections, selectedCollectionId]
  );

  // ========================= Data Fetching ======================
  const loadConfig = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const config = await apiClient.getRagConfig();
      setRagConfig(config);
    } catch (err) {
      console.error("Erro ao carregar configuração RAG:", err);
      setError(err instanceof Error ? err.message : "Falha ao carregar configuração");
    } finally {
      setIsLoading(false);
    }
  }, [setError, setIsLoading, setRagConfig]);

  const loadCollections = useCallback(async () => {
    setIsCollectionsLoading(true);
    try {
      const data = await apiClient.getKnowledgeCollections();
      setCollections(data);
    } catch (err) {
      console.error("Erro ao carregar coleções:", err);
      toast({
        title: "Erro ao carregar coleções",
        description: err instanceof Error ? err.message : "Falha desconhecida",
        variant: "destructive",
      });
    } finally {
      setIsCollectionsLoading(false);
    }
  }, [setCollections, setIsCollectionsLoading, toast]);

  const loadDocuments = useCallback(async (collectionId: string) => {
    setIsDocumentsLoading(true);
    try {
      const docs = await apiClient.getKnowledgeDocuments(collectionId);
      setDocuments(collectionId, docs);
    } catch (err) {
      console.error(`Erro ao carregar documentos (${collectionId}):`, err);
      toast({
        title: "Erro ao carregar documentos",
        description: err instanceof Error ? err.message : "Falha desconhecida",
        variant: "destructive",
      });
    } finally {
      setIsDocumentsLoading(false);
    }
  }, [setDocuments, setIsDocumentsLoading, toast]);

  useEffect(() => {
    loadConfig();
    loadCollections();
  }, [loadConfig, loadCollections]);

  useEffect(() => {
    if (selectedCollectionId) {
      loadDocuments(selectedCollectionId);
    }
  }, [selectedCollectionId, loadDocuments]);

  // ========================= Handlers ===========================
  const handleSaveConfig = async (config: typeof ragConfig) => {
    setIsSaving(true);
    setError(null);
    try {
      const updatedConfig = await apiClient.updateRagConfig(config);
      setRagConfig(updatedConfig);
      toast({
        title: "Configuração salva",
        description: "As configurações de RAG foram atualizadas com sucesso.",
      });
    } catch (err) {
      console.error("Erro ao salvar configuração RAG:", err);
      const errorMessage = err instanceof Error ? err.message : "Falha ao salvar configuração";
      setError(errorMessage);
      toast({
        title: "Erro ao salvar",
        description: errorMessage,
        variant: "destructive",
      });
      throw err;
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateCollection = async (payload: {
    name: string;
    description?: string;
    namespace?: string;
    tags?: string[];
  }) => {
    setIsSaving(true);
    try {
      const newCollection = await apiClient.createKnowledgeCollection(payload);
      addCollection(newCollection);
      setSelectedCollectionId(newCollection.id);
      toast({
        title: "Coleção criada",
        description: `A coleção "${newCollection.name}" foi criada com sucesso.`,
      });
    } catch (err) {
      console.error("Erro ao criar coleção:", err);
      toast({
        title: "Erro ao criar coleção",
        description: err instanceof Error ? err.message : "Falha desconhecida",
        variant: "destructive",
      });
      throw err;
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteCollection = async (collectionId: string) => {
    try {
      await apiClient.deleteKnowledgeCollection(collectionId);
      removeCollection(collectionId);
      toast({
        title: "Coleção excluída",
        description: "A coleção foi removida com sucesso.",
      });
    } catch (err) {
      console.error("Erro ao excluir coleção:", err);
      toast({
        title: "Erro ao excluir",
        description: err instanceof Error ? err.message : "Falha desconhecida",
        variant: "destructive",
      });
    }
  };

  const handleUploadDocuments = async (files: File[]) => {
    if (!selectedCollectionId) return;
    setIsUploading(true);
    try {
      const response = await apiClient.ingestKnowledgeDocuments(selectedCollectionId, files);
      await loadDocuments(selectedCollectionId);
      const currentCollections = useKnowledgeStore.getState().collections;
      const updatedCollections = currentCollections.map((collection) =>
        collection.id === selectedCollectionId
          ? { ...collection, document_count: collection.document_count + response.count }
          : collection
      );
      setCollections(updatedCollections);
      toast({
        title: "Upload concluído",
        description: `${response.count} documento(s) enviado(s) para processamento.`,
      });
    } catch (err) {
      console.error("Erro no upload:", err);
      toast({
        title: "Erro no upload",
        description: err instanceof Error ? err.message : "Falha ao enviar documentos",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (!selectedCollectionId) return;
    try {
      await apiClient.deleteKnowledgeDocument(documentId);
      removeDocument(selectedCollectionId, documentId);
      const currentCollections = useKnowledgeStore.getState().collections;
      const updatedCollections = currentCollections.map((collection) =>
        collection.id === selectedCollectionId
          ? { ...collection, document_count: Math.max(0, collection.document_count - 1) }
          : collection
      );
      setCollections(updatedCollections);
      toast({
        title: "Documento excluído",
        description: "O documento foi removido com sucesso.",
      });
    } catch (err) {
      console.error("Erro ao excluir documento:", err);
      toast({
        title: "Erro ao excluir",
        description: err instanceof Error ? err.message : "Falha desconhecida",
        variant: "destructive",
      });
    }
  };

  const handleSearch = async (query: string, collectionId?: string, topK?: number) => {
    setIsSearching(true);
    try {
      const results = await apiClient.searchKnowledge({ query, collection_id: collectionId, top_k: topK });
      setSearchResults(results);
    } catch (err) {
      console.error("Erro na busca:", err);
      toast({
        title: "Erro na busca",
        description: err instanceof Error ? err.message : "Falha ao realizar busca",
        variant: "destructive",
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleClearSearch = () => setSearchResults([]);

  // ========================= Helpers ============================
  const StatusIndicator = ({ enabled }: { enabled: boolean }) => (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
        enabled
          ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
          : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
      }`}
    >
      {enabled ? (
        <>
          <CheckCircle2 className="h-4 w-4" />
          Ativo
        </>
      ) : (
        <>
          <XCircle className="h-4 w-4" />
          Inativo
        </>
      )}
    </div>
  );

  const ConfigCard = ({
    icon: Icon,
    label,
    value,
    description,
    badge,
  }: {
    icon: React.ElementType;
    label: string;
    value: string | number;
    description?: string;
    badge?: string;
  }) => (
    <div className="flex items-start gap-3 p-4 bg-muted/30 rounded-xl border border-border/50">
      <div className="p-2 bg-background rounded-lg border shadow-sm">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{label}</span>
          {badge && <Badge variant="secondary" className="text-[10px]">{badge}</Badge>}
        </div>
        <p className="text-sm text-muted-foreground truncate">{value}</p>
        {description && <p className="text-xs text-muted-foreground/70 mt-1">{description}</p>}
      </div>
    </div>
  );

  // ========================= Render =============================
  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] overflow-hidden">
      <div className="h-14 border-b flex items-center justify-between px-6 bg-background shrink-0">
        <div>
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <Database className="h-5 w-5" />
            Knowledge Base
          </h1>
          <p className="text-sm text-muted-foreground">
            Gerencie coleções, documentos e configurações RAG
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => {
              loadConfig();
              loadCollections();
            }}
            disabled={isLoading || isCollectionsLoading}
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading || isCollectionsLoading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <div className="px-6 pt-4 border-b bg-background/60 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <TabsList className="grid w-full max-w-lg grid-cols-3">
              <TabsTrigger value="collections" className="flex items-center gap-2">
                <FolderOpen className="h-4 w-4" />
                Collections
              </TabsTrigger>
              <TabsTrigger value="search" className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                Search
              </TabsTrigger>
              <TabsTrigger value="config" className="flex items-center gap-2">
                <Settings2 className="h-4 w-4" />
                Settings
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="collections" className="flex-1 overflow-hidden p-6 m-0">
            <div className="grid grid-cols-12 gap-6 h-full">
              <div className="col-span-4 h-full overflow-hidden flex flex-col">
                <CollectionList
                  collections={collections}
                  selectedId={selectedCollectionId}
                  isLoading={isCollectionsLoading}
                  onSelect={(collection) => setSelectedCollectionId(collection.id)}
                  onDelete={handleDeleteCollection}
                  onRefresh={loadCollections}
                  onCreateNew={() => setShowCollectionModal(true)}
                />
              </div>
              <div className="col-span-8 h-full overflow-hidden flex flex-col">
                <DocumentList
                  collection={selectedCollection}
                  documents={selectedCollectionId ? documents[selectedCollectionId] || [] : []}
                  isLoading={isDocumentsLoading}
                  isUploading={isUploading}
                  onUpload={handleUploadDocuments}
                  onDelete={handleDeleteDocument}
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="search" className="flex-1 overflow-auto p-6 m-0">
            <div className="max-w-4xl mx-auto">
              <KnowledgeSearch
                collections={collections}
                results={searchResults}
                isSearching={isSearching}
                onSearch={handleSearch}
                onClear={handleClearSearch}
              />
            </div>
          </TabsContent>

          <TabsContent value="config" className="flex-1 overflow-auto p-6 m-0">
            <div className="max-w-4xl mx-auto space-y-6">
              {error && (
                <Card className="border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-950/20">
                  <CardContent className="flex items-center gap-3 p-4">
                    <AlertCircle className="h-5 w-5 text-red-500" />
                    <div>
                      <p className="font-medium text-red-700 dark:text-red-400">Falha ao carregar configuração</p>
                      <p className="text-sm text-red-600 dark:text-red-500">{error}</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Main RAG Status Card */}
              <Card className="overflow-hidden">
                <div className={`h-1 ${ragConfig.enabled ? "bg-gradient-to-r from-green-500 to-emerald-500" : "bg-gray-300"}`} />
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-xl ${ragConfig.enabled ? "bg-green-100 dark:bg-green-900/30" : "bg-muted"}`}>
                      <Sparkles className={`h-6 w-6 ${ragConfig.enabled ? "text-green-600 dark:text-green-400" : "text-muted-foreground"}`} />
                    </div>
                    <div>
                      <CardTitle className="text-xl">Retrieval Augmented Generation</CardTitle>
                    <CardDescription className="mt-1">
                      {ragConfig.enabled
                        ? "Agentes utilizam conhecimento contextual para respostas mais precisas"
                        : "Agentes respondem usando apenas o conhecimento do modelo base"}
                      </CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusIndicator enabled={ragConfig.enabled} />
                    <Button onClick={() => setShowConfigModal(true)} variant="outline" size="sm">
                      <Pencil className="h-4 w-4 mr-2" />
                      Editar
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {lastUpdated && (
                    <p className="text-xs text-muted-foreground">Última atualização: {lastUpdated.toLocaleString("pt-BR")}</p>
                  )}
                </CardContent>
              </Card>

              {ragConfig.enabled && (
                <>
                  {/* Provider Section */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Layers className="h-4 w-4 text-primary" />
                        Provedor de Contexto
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="grid md:grid-cols-2 gap-4">
                      <ConfigCard
                        icon={Database}
                        label="Provedor"
                        value={ragConfig.provider === "memory" ? "Memory (Vector Store Local)" : "Azure AI Search"}
                        description={ragConfig.provider === "memory" ? "Armazenamento vetorial em memória" : "Azure Cognitive Search para produção"}
                      />
                      <ConfigCard
                        icon={Hash}
                        label="Namespace"
                        value={ragConfig.namespace}
                        description="Identificador lógico para segmentar conhecimento"
                      />
                    </CardContent>
                  </Card>

                  {/* Retrieval Parameters */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Settings2 className="h-4 w-4 text-primary" />
                        Parâmetros de Retrieval
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="grid md:grid-cols-3 gap-4">
                      <ConfigCard icon={Layers} label="Top K" value={ragConfig.top_k.toString()} badge="chunks" description="Máximo de trechos retornados" />
                      <ConfigCard icon={Sparkles} label="Score Mínimo" value={ragConfig.min_score.toFixed(2)} description="Limiar mínimo de similaridade" />
                      <ConfigCard icon={MessageSquare} label="Estratégia" value={ragConfig.strategy === "last_message" ? "Última Mensagem" : "Conversação"} description={ragConfig.strategy === "last_message" ? "Busca baseada na última mensagem" : "Busca considerando histórico"} />
                    </CardContent>
                  </Card>

                  {/* Context Prompt */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <FileText className="h-4 w-4 text-primary" />
                        Prompt de Contexto
                      </CardTitle>
                      <CardDescription>Instrução exibida antes dos trechos recuperados no prompt do agente</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="p-4 bg-muted/30 rounded-xl border border-border/50">
                        <p className="text-sm whitespace-pre-wrap leading-relaxed">{ragConfig.context_prompt || "(Nenhum prompt configurado)"}</p>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Embeddings Config */}
                  {ragConfig.provider === "memory" && ragConfig.embedding && (
                    <Card className="border-amber-200/50 dark:border-amber-800/50 bg-amber-50/30 dark:bg-amber-950/10">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-base flex items-center gap-2">
                          <Sparkles className="h-4 w-4 text-amber-600" />
                          Configuração de Embeddings
                        </CardTitle>
                        <CardDescription>Modelo utilizado para vetorização do conhecimento</CardDescription>
                      </CardHeader>
                      <CardContent className="grid md:grid-cols-3 gap-4">
                        <ConfigCard icon={Layers} label="Modelo" value={ragConfig.embedding.model} />
                        <ConfigCard icon={Hash} label="Dimensões" value={ragConfig.embedding.dimensions?.toString() || "Auto"} description="Dimensões dos vetores gerados" />
                        <ConfigCard icon={Sparkles} label="Normalizar" value={ragConfig.embedding.normalize ? "Sim" : "Não"} description="Normalização de vetores" />
                      </CardContent>
                    </Card>
                  )}
                </>
              )}

              {!ragConfig.enabled && (
                <Card className="border-dashed border-2">
                  <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                    <div className="p-6 bg-muted/30 rounded-full mb-6">
                      <Database className="h-12 w-12 text-muted-foreground/40" />
                    </div>
                    <h3 className="text-lg font-medium mb-2">RAG não configurado</h3>
                    <p className="text-sm text-muted-foreground mb-6 max-w-md">
                      Habilite o Retrieval Augmented Generation para enriquecer as respostas dos agentes com conhecimento contextual dos seus documentos.
                    </p>
                    <Button onClick={() => setShowConfigModal(true)} size="lg">
                      <Settings2 className="h-4 w-4 mr-2" />
                      Configurar RAG
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      <KnowledgeFormModal
        open={showConfigModal}
        onOpenChange={setShowConfigModal}
        config={ragConfig}
        onSave={handleSaveConfig}
        isSaving={isSaving}
      />

      <CollectionFormModal
        open={showCollectionModal}
        onOpenChange={setShowCollectionModal}
        onSubmit={handleCreateCollection}
        isSaving={isSaving}
      />
    </div>
  );
}
