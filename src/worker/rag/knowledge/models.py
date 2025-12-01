from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


def _serialize_datetime(dt: datetime) -> str:
    """Serializa datetime para ISO8601."""
    return dt.isoformat() if dt else None


class KnowledgeCollection(BaseModel):
    """Representa um conjunto lógico de documentos da base de conhecimento."""

    model_config = ConfigDict(
        ser_json_timedelta="iso8601",
        json_encoders={datetime: _serialize_datetime},
    )

    id: str = Field(..., description="Identificador único da coleção")
    name: str = Field(..., description="Nome amigável da coleção")
    namespace: str = Field(..., description="Namespace utilizado no vector store")
    description: str | None = Field(None, description="Descrição opcional da coleção")
    tags: list[str] = Field(default_factory=list, description="Lista de tags livres")
    embedding_model: str | None = Field(
        None,
        description="Modelo de embedding utilizado na última indexação",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    document_count: int = Field(0, description="Quantidade de documentos na coleção")
    chunk_count: int = Field(0, description="Quantidade total de chunks indexados")


class KnowledgeDocument(BaseModel):
    """Metadados de um documento individual presente em uma coleção."""

    model_config = ConfigDict(
        ser_json_timedelta="iso8601",
        json_encoders={datetime: _serialize_datetime},
    )

    id: str = Field(..., description="Identificador único do documento")
    collection_id: str = Field(..., description="Coleção à qual o documento pertence")
    filename: str = Field(..., description="Nome original do arquivo")
    content_type: str | None = Field(None, description="MIME type detectado")
    size_bytes: int = Field(..., ge=0, description="Tamanho do arquivo em bytes")
    checksum: str = Field(..., description="Checksum SHA256 do conteúdo para deduplicação")
    status: str = Field("processed", description="Status de processamento")
    chunk_count: int = Field(0, description="Chunks gerados a partir do documento")
    error: str | None = Field(None, description="Mensagem de erro, se houver")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeChunk(BaseModel):
    """Representa um chunk de texto pronto para indexação vetorial."""

    id: str = Field(...)
    text: str = Field(...)
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = Field(None, description="Embedding pré-calculado")


class KnowledgeSearchResult(BaseModel):
    document_id: str
    chunk_id: str
    content: str
    score: float
    metadata: dict[str, Any]


class KnowledgeBaseState(BaseModel):
    """Persistência simplificada da base de conhecimento."""

    collections: dict[str, KnowledgeCollection] = Field(default_factory=dict)
    documents: dict[str, KnowledgeDocument] = Field(default_factory=dict)
    embedding_signature: str | None = Field(
        None,
        description="Assinatura do modelo de embedding usado nos vetores persistidos",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "collections": {key: value.model_dump(mode="json") for key, value in self.collections.items()},
            "documents": {key: value.model_dump(mode="json") for key, value in self.documents.items()},
            "embedding_signature": self.embedding_signature,
        }

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> "KnowledgeBaseState":
        collections = {
            key: KnowledgeCollection(**value)
            for key, value in (payload.get("collections") or {}).items()
        }
        documents = {
            key: KnowledgeDocument(**value)
            for key, value in (payload.get("documents") or {}).items()
        }
        signature = payload.get("embedding_signature")
        return KnowledgeBaseState(collections=collections, documents=documents, embedding_signature=signature)
