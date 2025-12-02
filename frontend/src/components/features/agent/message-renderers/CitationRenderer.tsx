/**
 * CitationRenderer - Componente para renderizar citações RAG
 * Inspirado no Azure Search OpenAI Demo
 */

import { useState } from "react";
import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  FileText,
  ExternalLink,
  Quote,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export interface Citation {
  id: string;
  filename: string;
  content: string;
  url?: string;
  page?: number;
  score?: number;
  metadata?: Record<string, any>;
}

interface CitationRendererProps {
  citations: Citation[];
  className?: string;
}

interface CitationCardProps {
  citation: Citation;
  index: number;
}

function CitationCard({ citation, index }: CitationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div className="p-3 bg-muted/30 rounded-lg border border-muted-foreground/20 hover:bg-muted/50 transition-colors">
      <div className="flex items-start gap-3">
        {/* Número da citação */}
        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center">
          {index}
        </div>

        <div className="flex-1 min-w-0">
          {/* Cabeçalho da citação */}
          <div className="flex items-center gap-2 mb-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium text-sm truncate">
              {citation.filename}
            </span>
            {citation.page && (
              <span className="text-xs text-muted-foreground">
                Página {citation.page}
              </span>
            )}
            {citation.score && (
              <span className="text-xs text-muted-foreground ml-auto">
                {Math.round(citation.score * 100)}% relevância
              </span>
            )}
          </div>

          {/* Preview do conteúdo */}
          <div className="text-sm text-muted-foreground mb-2">
            <Quote className="h-3 w-3 inline mr-1" />
            <span className="italic">
              {citation.content.length > 150
                ? `${citation.content.substring(0, 150)}...`
                : citation.content}
            </span>
          </div>

          {/* Ações */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-xs h-7"
            >
              {isExpanded ? (
                <>
                  <ChevronDown className="h-3 w-3 mr-1" />
                  Menos
                </>
              ) : (
                <>
                  <ChevronRight className="h-3 w-3 mr-1" />
                  Ver mais
                </>
              )}
            </Button>
            
            {citation.url && (
              <Button
                variant="ghost"
                size="sm"
                asChild
                className="text-xs h-7"
              >
                <a href={citation.url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-3 w-3 mr-1" />
                  Abrir
                </a>
              </Button>
            )}
          </div>

          {/* Conteúdo expandido */}
          {isExpanded && (
            <div className="mt-3 p-3 bg-background rounded border">
              <blockquote className="text-sm leading-relaxed border-l-2 border-primary/30 pl-3 italic">
                {citation.content}
              </blockquote>
              
              {citation.metadata && Object.keys(citation.metadata).length > 0 && (
                <div className="mt-2 pt-2 border-t">
                  <div className="text-xs text-muted-foreground">
                    <strong>Metadados:</strong>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {Object.entries(citation.metadata).map(([key, value]) => (
                      <div key={key}>
                        <span className="font-medium">{key}:</span> {String(value)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function CitationRenderer({ citations, className }: CitationRendererProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!citations || citations.length === 0) return null;

  return (
    <div className={`mt-4 border-t pt-4 ${className || ""}`}>
      <Button
        variant="ghost"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm font-medium p-0 h-auto hover:bg-transparent"
      >
        <BookOpen className="h-4 w-4 text-primary" />
        <span>Fontes consultadas ({citations.length})</span>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 ml-auto" />
        ) : (
          <ChevronRight className="h-4 w-4 ml-auto" />
        )}
      </Button>

      {isExpanded && (
        <div className="mt-3 space-y-3">
          {citations.map((citation, index) => (
            <CitationCard
              key={citation.id}
              citation={citation}
              index={index + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Hook para extrair citações de uma resposta de texto
 * Procura por padrões como [1], [2], etc. e mapeia para citações
 */
export function useCitationExtraction(text: string, availableCitations: Citation[]) {
  const extractedCitations: Citation[] = [];
  
  // Regex para encontrar referências no formato [1], [2], etc.
  const citationRegex = /\[(\d+)\]/g;
  const matches = text.match(citationRegex);
  
  if (matches) {
    matches.forEach(match => {
      const index = parseInt(match.replace(/[\[\]]/g, '')) - 1;
      if (availableCitations[index]) {
        extractedCitations.push(availableCitations[index]);
      }
    });
  }
  
  return extractedCitations;
}