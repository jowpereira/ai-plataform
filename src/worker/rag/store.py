from typing import List, Dict, Any

class SimpleVectorStore:
    def __init__(self):
        self.documents = []

    def add_documents(self, documents: List[str]):
        """Adiciona documentos ao store."""
        self.documents.extend(documents)

    def search(self, query: str, k: int = 3) -> List[str]:
        """Busca simples (keyword match para teste)."""
        # TODO: Implementar busca vetorial real (Chroma/FAISS)
        results = []
        for doc in self.documents:
            if query.lower() in doc.lower():
                results.append(doc)
        return results[:k]

# Instância global para teste
_store = SimpleVectorStore()

def add_to_store(documents: List[str]):
    _store.add_documents(documents)
    return f"Adicionados {len(documents)} documentos."

def search_store(query: str) -> List[str]:
    return _store.search(query)
