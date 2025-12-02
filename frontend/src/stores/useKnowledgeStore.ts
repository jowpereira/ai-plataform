/**
 * Knowledge Store - Gerenciamento de estado da configuração RAG
 * Separado do DevUI Store para manter responsabilidades únicas
 */

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type {
  RagConfig,
  RagEmbeddingConfig,
  KnowledgeCollection,
  KnowledgeDocument,
  KnowledgeSearchResult,
} from "@/services/api";

// ========================================
// State Interface
// ========================================

interface KnowledgeState {
  // RAG Configuration
  ragConfig: RagConfig;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  lastUpdated: Date | null;
  collections: KnowledgeCollection[];
  documents: Record<string, KnowledgeDocument[]>;
  searchResults: KnowledgeSearchResult[];
  selectedCollectionId: string | null;
  isCollectionsLoading: boolean;
  isDocumentsLoading: boolean;
  isUploading: boolean;
  isSearching: boolean;
}

// ========================================
// Actions Interface
// ========================================

interface KnowledgeActions {
  // Configuration Actions
  setRagConfig: (config: RagConfig) => void;
  updateRagConfig: (partial: Partial<RagConfig>) => void;
  updateEmbeddingConfig: (embedding: RagEmbeddingConfig | undefined) => void;
  
  // Loading State
  setIsLoading: (loading: boolean) => void;
  setIsSaving: (saving: boolean) => void;
  setError: (error: string | null) => void;
  setLastUpdated: (date: Date | null) => void;
  setCollections: (collections: KnowledgeCollection[]) => void;
  addCollection: (collection: KnowledgeCollection) => void;
  removeCollection: (collectionId: string) => void;
  setDocuments: (collectionId: string, docs: KnowledgeDocument[]) => void;
  removeDocument: (collectionId: string, documentId: string) => void;
  setSearchResults: (results: KnowledgeSearchResult[]) => void;
  setSelectedCollectionId: (collectionId: string | null) => void;
  setIsCollectionsLoading: (loading: boolean) => void;
  setIsDocumentsLoading: (loading: boolean) => void;
  setIsUploading: (uploading: boolean) => void;
  setIsSearching: (searching: boolean) => void;
  
  // Reset
  resetToDefaults: () => void;
}

type KnowledgeStore = KnowledgeState & KnowledgeActions;

// ========================================
// Default Configuration
// ========================================

const DEFAULT_RAG_CONFIG: RagConfig = {
  enabled: false,
  provider: "memory",
  top_k: 4,
  min_score: 0.25,
  strategy: "last_message",
  context_prompt: "Os trechos a seguir são da base de conhecimento interna. Use-os para responder à pergunta do usuário.\n\nIMPORTANTE: Ao usar informações de um trecho, cite a fonte usando o número entre colchetes (por exemplo: [1], [2]). Sempre cite as fontes relevantes no final da frase ou parágrafo onde a informação é usada.",
  namespace: "default",
  embedding: undefined,
};

// ========================================
// Store Implementation
// ========================================

export const useKnowledgeStore = create<KnowledgeStore>()(
  devtools(
    (set) => ({
      // ========================================
      // Initial State
      // ========================================
      ragConfig: DEFAULT_RAG_CONFIG,
      isLoading: false,
      isSaving: false,
      error: null,
      lastUpdated: null,
      collections: [],
      documents: {},
      searchResults: [],
      selectedCollectionId: null,
      isCollectionsLoading: false,
      isDocumentsLoading: false,
      isUploading: false,
      isSearching: false,

      // ========================================
      // Configuration Actions
      // ========================================

      setRagConfig: (config) => 
        set({ 
          ragConfig: config, 
          error: null,
          lastUpdated: new Date(),
        }),

      updateRagConfig: (partial) =>
        set((state) => ({
          ragConfig: { ...state.ragConfig, ...partial },
        })),

      updateEmbeddingConfig: (embedding) =>
        set((state) => ({
          ragConfig: { ...state.ragConfig, embedding },
        })),

      // ========================================
      // Loading State Actions
      // ========================================

      setIsLoading: (loading) => set({ isLoading: loading }),
      setIsSaving: (saving) => set({ isSaving: saving }),
      setError: (error) => set({ error }),
      setLastUpdated: (date) => set({ lastUpdated: date }),

      setCollections: (collections) =>
        set({ collections }),

      addCollection: (collection) =>
        set((state) => ({ collections: [collection, ...state.collections] })),

      removeCollection: (collectionId) =>
        set((state) => ({
          collections: state.collections.filter((collection) => collection.id !== collectionId),
          documents: Object.fromEntries(
            Object.entries(state.documents).filter(([key]) => key !== collectionId)
          ),
          searchResults: state.selectedCollectionId === collectionId ? [] : state.searchResults,
          selectedCollectionId:
            state.selectedCollectionId === collectionId ? null : state.selectedCollectionId,
        })),

      setDocuments: (collectionId, docs) =>
        set((state) => ({
          documents: { ...state.documents, [collectionId]: docs },
        })),

      removeDocument: (collectionId, documentId) =>
        set((state) => ({
          documents: {
            ...state.documents,
            [collectionId]: (state.documents[collectionId] || []).filter((doc) => doc.id !== documentId),
          },
        })),

      setSearchResults: (results) => set({ searchResults: results }),
      setSelectedCollectionId: (collectionId) => set({ selectedCollectionId: collectionId }),
      setIsCollectionsLoading: (loading) => set({ isCollectionsLoading: loading }),
      setIsDocumentsLoading: (loading) => set({ isDocumentsLoading: loading }),
      setIsUploading: (uploading) => set({ isUploading: uploading }),
      setIsSearching: (searching) => set({ isSearching: searching }),

      // ========================================
      // Reset Action
      // ========================================

      resetToDefaults: () =>
        set({
          ragConfig: DEFAULT_RAG_CONFIG,
          error: null,
        }),
    }),
    { name: "Knowledge Store" }
  )
);

// ========================================
// Exports
// ========================================

export { DEFAULT_RAG_CONFIG };
