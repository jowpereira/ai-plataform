from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel

from src.worker.config import ModelConfig, RagConfig
from src.worker.providers.embeddings import EmbeddingProvider, EmbeddingRegistry
from src.worker.rag.interfaces import VectorDocument, VectorStore
from src.worker.rag.knowledge.loader import UnsupportedFileError, extract_text
from src.worker.rag.knowledge.models import (
    KnowledgeBaseState,
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeDocument,
    KnowledgeSearchResult,
)
from src.worker.rag.knowledge.splitter import chunk_text
from src.worker.rag.stores import InMemoryVectorStore


logger = logging.getLogger("worker.rag.knowledge")


class KnowledgeIngestionResult(BaseModel):
    document: KnowledgeDocument
    collection: KnowledgeCollection


class KnowledgeBaseService:
    """Serviço de gerenciamento da base de conhecimento local."""

    def __init__(
        self,
        *,
        root_dir: Path,
        rag_config_getter: Callable[[], RagConfig | None],
        vector_store: VectorStore | None = None,
    ) -> None:
        self._root_dir = root_dir
        self._state_path = self._root_dir / "state.json"
        self._chunks_dir = self._root_dir / "chunks"
        self._rag_config_getter = rag_config_getter
        self._store = vector_store or InMemoryVectorStore()
        self._state = KnowledgeBaseState()
        self._lock = asyncio.Lock()
        self._embedding_provider: EmbeddingProvider | None = None
        self._embedding_signature: str | None = None

        self._root_dir.mkdir(parents=True, exist_ok=True)
        self._chunks_dir.mkdir(parents=True, exist_ok=True)
        self._load_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_collections(self) -> list[KnowledgeCollection]:
        return sorted(self._state.collections.values(), key=lambda item: item.created_at)

    def get_collection(self, collection_id: str) -> KnowledgeCollection:
        collection = self._state.collections.get(collection_id)
        if not collection:
            raise ValueError(f"Coleção '{collection_id}' não encontrada")
        return collection

    def list_documents(self, collection_id: str) -> list[KnowledgeDocument]:
        return [doc for doc in self._state.documents.values() if doc.collection_id == collection_id]

    async def ingest_file(
        self,
        *,
        collection_id: str,
        filename: str,
        content_type: str | None,
        raw_bytes: bytes,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeIngestionResult:
        collection = self.get_collection(collection_id)
        rag_config = self._require_rag_config(allow_disabled=True)
        provider = await self._ensure_embedding_provider(rag_config)

        checksum = hashlib.sha256(raw_bytes).hexdigest()
        if self._has_duplicate_document(collection_id, checksum):
            raise ValueError("Um documento com o mesmo conteúdo já foi ingerido nesta coleção.")

        try:
            text = extract_text(filename, content_type, raw_bytes)
        except UnsupportedFileError:
            raise
        except Exception as exc:  # pragma: no cover - fallback defensivo
            raise RuntimeError(f"Falha ao processar arquivo '{filename}': {exc}") from exc

        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("Não foram gerados trechos a partir do documento fornecido.")

        embeddings = await provider.embed_documents(chunks)
        chunk_objects = self._build_chunk_objects(
            chunks,
            embeddings,
            collection=collection,
            filename=filename,
            metadata=metadata or {},
        )

        async with self._lock:
            document = self._create_document_entry(
                collection_id=collection.id,
                filename=filename,
                content_type=content_type,
                size=len(raw_bytes),
                checksum=checksum,
                chunk_count=len(chunk_objects),
                metadata=metadata or {},
            )
            self._ensure_chunk_metadata_has_document(document.id, chunk_objects)
            await self._store.add_documents(self._to_vector_documents(chunk_objects, collection.namespace))
            self._persist_chunks(document.id, collection.id, chunk_objects)
            self._state.embedding_signature = self._embedding_signature
            self._save_state()

        return KnowledgeIngestionResult(document=document, collection=self._state.collections[collection.id])

    def create_collection(
        self,
        *,
        name: str,
        description: str | None = None,
        namespace: str | None = None,
        tags: list[str] | None = None,
    ) -> KnowledgeCollection:
        # Não exige embedding para criar coleção - só para ingestão
        rag_config = self._require_rag_config(allow_disabled=True, require_embedding=False)
        collection = KnowledgeCollection(
            id=uuid.uuid4().hex,
            name=name,
            description=description,
            namespace=namespace or rag_config.namespace,
            tags=tags or [],
            embedding_model=rag_config.embedding.model if rag_config.embedding else None,
        )
        self._state.collections[collection.id] = collection
        self._save_state()
        return collection

    async def delete_collection(self, collection_id: str) -> None:
        if collection_id not in self._state.collections:
            raise ValueError(f"Coleção '{collection_id}' não encontrada")

        document_ids = [doc_id for doc_id, doc in self._state.documents.items() if doc.collection_id == collection_id]

        async with self._lock:
            for doc_id in document_ids:
                self._delete_document_files(doc_id)
                self._state.documents.pop(doc_id, None)
            self._state.collections.pop(collection_id, None)
            await self.rebuild_vector_index(force_reembed=False)
            self._save_state()

    async def delete_document(self, document_id: str) -> None:
        document = self._state.documents.get(document_id)
        if not document:
            raise ValueError("Documento não encontrado")

        async with self._lock:
            self._delete_document_files(document_id)
            self._state.documents.pop(document_id, None)
            collection = self._state.collections.get(document.collection_id)
            if collection:
                collection.document_count = max(0, collection.document_count - 1)
                collection.chunk_count = max(0, collection.chunk_count - document.chunk_count)
                collection.updated_at = datetime.utcnow()
            await self.rebuild_vector_index(force_reembed=False)
            self._save_state()

    async def rebuild_vector_index(self, *, force_reembed: bool) -> None:
        """Reconstrói o índice vetorial a partir dos arquivos persistidos."""

        if not self._state.documents:
            await self._store.clear()
            self._state.embedding_signature = self._embedding_signature
            self._save_state()
            return

        rag_config = self._require_rag_config(allow_disabled=True)
        provider = await self._ensure_embedding_provider(rag_config)

        await self._store.clear()

        for document in self._state.documents.values():
            collection = self._state.collections.get(document.collection_id)
            if not collection:
                continue
            chunk_path = self._chunk_file(document.id)
            if not chunk_path.exists():
                continue
            payload = json.loads(chunk_path.read_text(encoding="utf-8"))
            chunks_data = payload.get("chunks", [])
            if not chunks_data:
                continue

            chunk_objs: list[KnowledgeChunk] = []
            reembed_required = force_reembed or self._state.embedding_signature != self._embedding_signature
            texts_to_embed: list[str] = []
            embed_indexes: list[int] = []

            for idx, chunk_payload in enumerate(chunks_data):
                chunk = KnowledgeChunk(**chunk_payload)
                if reembed_required or not chunk.embedding:
                    texts_to_embed.append(chunk.text)
                    embed_indexes.append(idx)
                chunk_objs.append(chunk)

            self._ensure_chunk_metadata_has_document(document.id, chunk_objs)

            if texts_to_embed:
                new_embeddings = await provider.embed_documents(texts_to_embed)
                for pos, embedding in zip(embed_indexes, new_embeddings):
                    chunk_objs[pos].embedding = embedding

                # Atualizar arquivo persistido com os novos vetores
                self._persist_chunks(document.id, document.collection_id, chunk_objs)

            await self._store.add_documents(self._to_vector_documents(chunk_objs, collection.namespace))

        self._state.embedding_signature = self._embedding_signature
        self._save_state()

    async def search(
        self,
        *,
        query: str,
        collection_id: str | None = None,
        top_k: int = 5,
    ) -> list[KnowledgeSearchResult]:
        if not query.strip():
            raise ValueError("Consulta não pode ser vazia")

        rag_config = self._require_rag_config(allow_disabled=True)
        provider = await self._ensure_embedding_provider(rag_config)

        metadata_filters: dict[str, Any] | None = None
        if collection_id:
            collection = self.get_collection(collection_id)
            namespace = collection.namespace
            metadata_filters = {"collection_id": collection_id}
        else:
            namespace = "*"

        query_vector = await provider.embed_query(query)
        matches = await self._store.similarity_search(
            query_vector,
            top_k=top_k,
            namespace=namespace,
            metadata_filters=metadata_filters,
        )

        results: list[KnowledgeSearchResult] = []
        for match in matches:
            chunk_id = match.metadata.get("chunk_id") or match.document_id
            results.append(
                KnowledgeSearchResult(
                    document_id=match.metadata.get("document_id", match.document_id),
                    chunk_id=chunk_id,
                    content=match.metadata.get("text", match.content),
                    score=match.score,
                    metadata=match.metadata,
                )
            )
        return results

    async def sync_with_config(self, new_config: RagConfig) -> None:
        """Atualiza o provider e reindexa se a assinatura do embedding mudar."""

        if not new_config.embedding:
            logger.warning("Base de conhecimento desativada - configuração de embedding ausente")
            await self._store.clear()
            self._embedding_provider = None
            self._embedding_signature = None
            self._state.embedding_signature = None
            self._save_state()
            return

        signature = self._build_embedding_signature(new_config)
        # Mesmo provider → apenas garantir que vetor store está alinhado
        if signature == self._state.embedding_signature:
            self._embedding_signature = signature
            await self.rebuild_vector_index(force_reembed=False)
            return

        self._embedding_signature = signature
        await self.rebuild_vector_index(force_reembed=True)

    def get_state_snapshot(self) -> KnowledgeBaseState:
        return self._state

    def get_vector_store(self) -> VectorStore:
        return self._store

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _load_state(self) -> None:
        if not self._state_path.exists():
            self._save_state()
            return
        try:
            payload = json.loads(self._state_path.read_text(encoding="utf-8"))
            self._state = KnowledgeBaseState.from_dict(payload)
            self._state.embedding_signature = payload.get("embedding_signature")
        except Exception:
            # Corrupção do arquivo não pode travar o servidor
            self._state = KnowledgeBaseState()
        self._embedding_signature = self._state.embedding_signature

    def _save_state(self) -> None:
        payload = self._state.to_dict()
        self._state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _chunk_file(self, document_id: str) -> Path:
        return self._chunks_dir / f"{document_id}.json"

    def _persist_chunks(
        self,
        document_id: str,
        collection_id: str,
        chunks: list[KnowledgeChunk],
    ) -> None:
        payload = {
            "document_id": document_id,
            "collection_id": collection_id,
            "chunks": [chunk.model_dump() for chunk in chunks],
        }
        self._chunk_file(document_id).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _delete_document_files(self, document_id: str) -> None:
        chunk_path = self._chunk_file(document_id)
        if chunk_path.exists():
            chunk_path.unlink()

    def _to_vector_documents(
        self,
        chunks: list[KnowledgeChunk],
        namespace: str,
    ) -> list[VectorDocument]:
        documents: list[VectorDocument] = []
        for chunk in chunks:
            if not chunk.embedding:
                raise ValueError("Chunk sem embedding não pode ser indexado")
            documents.append(
                VectorDocument(
                    id=chunk.id,
                    text=chunk.text,
                    metadata=chunk.metadata,
                    namespace=namespace,
                    embedding=chunk.embedding,
                )
            )
        return documents

    def _create_document_entry(
        self,
        *,
        collection_id: str,
        filename: str,
        content_type: str | None,
        size: int,
        checksum: str,
        chunk_count: int,
        metadata: dict[str, Any],
    ) -> KnowledgeDocument:
        document = KnowledgeDocument(
            id=uuid.uuid4().hex,
            collection_id=collection_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size,
            checksum=checksum,
            chunk_count=chunk_count,
            metadata=metadata,
        )
        self._state.documents[document.id] = document
        collection = self._state.collections[collection_id]
        collection.document_count += 1
        collection.chunk_count += chunk_count
        collection.updated_at = datetime.utcnow()
        return document

    def _has_duplicate_document(self, collection_id: str, checksum: str) -> bool:
        return any(
            doc.checksum == checksum and doc.collection_id == collection_id for doc in self._state.documents.values()
        )

    def _build_chunk_objects(
        self,
        chunks: list[str],
        embeddings: list[list[float]],
        *,
        collection: KnowledgeCollection,
        filename: str,
        metadata: dict[str, Any],
    ) -> list[KnowledgeChunk]:
        items: list[KnowledgeChunk] = []
        for index, (chunk_text, embedding) in enumerate(zip(chunks, embeddings), start=1):
            chunk_id = f"{collection.id}_{uuid.uuid4().hex[:8]}_{index}"
            chunk_metadata = {
                "collection_id": collection.id,
                "document_id": None,  # preenchido após criação
                "chunk_index": index,
                "source": filename,
                "text": chunk_text,
                **metadata,
            }
            items.append(
                KnowledgeChunk(
                    id=chunk_id,
                    text=chunk_text,
                    metadata=chunk_metadata,
                    embedding=embedding,
                )
            )
        return items

    def _ensure_chunk_metadata_has_document(self, document_id: str, chunks: list[KnowledgeChunk]) -> None:
        for chunk in chunks:
            chunk.metadata["document_id"] = document_id
            chunk.metadata["chunk_id"] = chunk.id
            chunk.metadata["text"] = chunk.text

    def _require_rag_config(self, allow_disabled: bool = False, require_embedding: bool = True) -> RagConfig:
        config = self._rag_config_getter()
        if not config:
            raise ValueError("Configuração RAG não encontrada. Configure antes de ingerir documentos.")
        if not allow_disabled and not config.enabled:
            raise ValueError("RAG precisa estar habilitado para operar a base de conhecimento.")
        if require_embedding and not config.embedding:
            raise ValueError("Configuração de embeddings é obrigatória para a base de conhecimento.")
        return config

    async def _ensure_embedding_provider(self, rag_config: RagConfig) -> EmbeddingProvider:
        if not rag_config.embedding:
            raise ValueError("Configuração de embedding não encontrada")

        signature = self._build_embedding_signature(rag_config)
        if self._embedding_provider and signature == self._embedding_signature:
            return self._embedding_provider

        provider_type = _detect_provider_type()
        model_config = ModelConfig(type=provider_type, deployment=rag_config.embedding.model)
        provider = EmbeddingRegistry.create_provider(
            model_config,
            dimensions=rag_config.embedding.dimensions,
            normalize=rag_config.embedding.normalize,
        )
        self._embedding_provider = provider
        self._embedding_signature = signature
        return provider

    def _build_embedding_signature(self, config: RagConfig) -> str:
        normalize = config.embedding.normalize if config.embedding else True
        dimensions = config.embedding.dimensions if config.embedding else None
        provider_type = _detect_provider_type()
        return f"{provider_type}:{config.embedding.model}:{normalize}:{dimensions}"

    def _require_chunks(self, document_id: str) -> list[KnowledgeChunk]:
        path = self._chunk_file(document_id)
        if not path.exists():
            raise ValueError("Chunks não encontrados para o documento informado")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [KnowledgeChunk(**item) for item in payload.get("chunks", [])]

    def _delete_vector_entries(self, document_id: str) -> None:
        # Atualmente o VectorStore não suporta remoção granular, por isso reindexamos
        return

    def _build_metadata_filters(self, collection_id: str | None) -> dict[str, Any] | None:
        if not collection_id:
            return None
        return {"collection_id": collection_id}


def _detect_provider_type() -> str:
    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        return "azure-openai"
    return "openai"
