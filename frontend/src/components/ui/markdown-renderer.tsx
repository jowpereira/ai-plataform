/**
 * Lightweight Markdown Renderer
 *
 * A minimal markdown renderer with zero dependencies for rendering LLM responses.
 * Handles the most common markdown patterns without bloating bundle size.
 *
 * Supported syntax:
 * - **bold** and __bold__
 * - *italic* and _italic_
 * - `inline code`
 * - ```code blocks``` (with copy button on hover)
 * - [links](url)
 * - **[bold links](url)** and *[italic links](url)*
 * - # Headers (H1-H6)
 * - Lists (ordered and unordered)
 * - > Blockquotes
 * - Tables (| col1 | col2 |)
 * - Horizontal rules (---)
 * - Citation markers ([1], [doc1], [fonte: file.pdf])
 */

import React, { useState, useRef, useEffect } from "react";
import { FileText } from "lucide-react";
import type { Annotation, FileCitationAnnotation } from "@/types/openai";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface MarkdownRendererProps {
  content: string;
  className?: string;
  /** Anotações de citação para vincular marcadores no texto */
  annotations?: Annotation[];
}

interface CodeBlockProps {
  code: string;
  language?: string;
}

/**
 * Code block component with copy button
 */
function CodeBlock({ code, language }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);

      // Clear any existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set new timeout and store reference
      timeoutRef.current = setTimeout(() => {
        setCopied(false);
        timeoutRef.current = null;
      }, 2000);
    } catch (err) {
      console.error("Failed to copy code:", err);
    }
  };

  return (
    <div className="relative group">
      <pre className="my-3 p-3 bg-foreground/5 dark:bg-foreground/10 rounded overflow-x-auto border border-foreground/10">
        <code className="text-xs font-mono block whitespace-pre-wrap break-words">
          {language && (
            <span className="opacity-60 text-[10px] mb-1 block uppercase">
              {language}
            </span>
          )}
          {code}
        </code>
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-1.5 rounded-md border shadow-sm
                   bg-background hover:bg-accent
                   text-muted-foreground hover:text-foreground
                   transition-all duration-200
                   opacity-0 group-hover:opacity-100"
        title={copied ? "Copied!" : "Copy code"}
      >
        {copied ? (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-green-600 dark:text-green-400"
          >
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
        )}
      </button>
    </div>
  );
}

/**
 * Componente de Popup para Citações
 */
function CitationPopup({
  annotation,
  children,
}: {
  annotation: FileCitationAnnotation;
  children: React.ReactNode;
}) {
  // Suporte para campos flat (novo) ou aninhados (legado)
  const filename = annotation.filename || annotation.file_citation?.filename || "Documento desconhecido";
  const quote = annotation.quote || annotation.file_citation?.quote;
  const score = annotation.score ?? annotation.file_citation?.score;
  const file_id = annotation.file_id || annotation.file_citation?.file_id;
  
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="cursor-pointer hover:bg-primary/10 rounded transition-colors">
            {children}
          </span>
        </TooltipTrigger>
        <TooltipContent className="max-w-sm p-0 overflow-hidden border shadow-md bg-popover text-popover-foreground">
          <div className="p-3 space-y-2">
            <div className="flex items-start gap-2">
              <div className="p-1.5 bg-muted rounded-md shrink-0">
                <FileText className="h-4 w-4 text-primary" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="font-medium text-sm truncate" title={filename}>
                  {filename}
                </div>
                {score !== undefined && score > 0 && (
                  <div className="text-xs text-muted-foreground">
                    Relevância: {(score * 100).toFixed(0)}%
                  </div>
                )}
              </div>
            </div>
            
            {quote && (
              <div className="relative pl-3 border-l-2 border-primary/30">
                <p className="text-xs text-muted-foreground italic line-clamp-4">
                  "{quote}"
                </p>
              </div>
            )}
          </div>
          <div className="bg-muted/50 px-3 py-1.5 text-[10px] text-muted-foreground border-t flex justify-between">
             <span>Clique para ver detalhes</span>
             {file_id && <span>ID: {file_id.slice(0, 8)}</span>}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * Parse markdown text into React elements
 */
export function MarkdownRenderer({
  content,
  className = "",
  annotations = [],
}: MarkdownRendererProps) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  // DEBUG: logar sempre que há annotations
  if (annotations.length > 0) {
    console.log("[MarkdownRenderer] 🎯 INICIANDO com annotations:", {
      contentPreview: content.substring(0, 100),
      contentLength: content.length,
      annotationsCount: annotations.length,
      annotationsDetail: annotations.map(a => ({
        type: a.type,
        text: (a as FileCitationAnnotation).text,
        filename: (a as FileCitationAnnotation).filename,
        file_id: (a as FileCitationAnnotation).file_id,
        quote: (a as FileCitationAnnotation).quote?.substring(0, 80),
        score: (a as FileCitationAnnotation).score,
      })),
    });
  } else {
    // Log quando NÃO há annotations mas deveria haver (texto contém [número])
    if (content.match(/\[\d+\]/)) {
      console.warn("[MarkdownRenderer] ⚠️ TEXTO CONTÉM [n] MAS SEM ANNOTATIONS!", {
        contentPreview: content.substring(0, 200),
        matches: content.match(/\[\d+\]/g),
      });
    }
  }

  // Criar mapa de citações por texto para lookup rápido
  // Usamos múltiplas chaves para garantir match
  const citationMap = new Map<string, FileCitationAnnotation>();
  
  for (const annotation of annotations) {
    if (annotation.type === "file_citation") {
      // Chave primária: texto exato da anotação (ex: "[4]")
      if (annotation.text) {
        citationMap.set(annotation.text, annotation);
        console.log(`[MarkdownRenderer] 📍 Mapeando chave primária: "${annotation.text}"`);
        
        // Extrair número da citação se possível e usar como chave direta
        const numMatch = annotation.text.match(/\[(?:doc|source|fonte)?\s*(\d+)\]/i);
        if (numMatch) {
          const num = numMatch[1];
          // Adicionar variações comuns
          citationMap.set(`[${num}]`, annotation);
          citationMap.set(`[doc${num}]`, annotation);
          citationMap.set(`[Doc${num}]`, annotation);
          citationMap.set(num, annotation); // Chave apenas com o número "4"
          console.log(`[MarkdownRenderer] 📍 Mapeando variações para número ${num}`);
        }
      }
      
      // Se tem filename, adicionar como chave também
      const filename = annotation.filename || annotation.file_citation?.filename;
      if (filename) {
        citationMap.set(`[fonte: ${filename}]`, annotation);
        citationMap.set(`[source: ${filename}]`, annotation);
      }
    }
  }
  
  // Log final do mapa de citações
  if (citationMap.size > 0) {
    console.log("[MarkdownRenderer] 🗺️ CitationMap final:", {
      size: citationMap.size,
      keys: Array.from(citationMap.keys()),
    });
  }

  while (i < lines.length) {
    const line = lines[i];

    // Code blocks (multiline)
    if (line.trim().startsWith("```")) {
      const codeLines: string[] = [];
      const langMatch = line.trim().match(/^```(\w+)?/);
      const language = langMatch?.[1] || "";
      i++; // Skip opening ```

      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // Skip closing ```

      elements.push(
        <CodeBlock
          key={elements.length}
          code={codeLines.join("\n")}
          language={language}
        />
      );
      continue;
    }

    // Headers
    const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      const text = headerMatch[2];
      const sizes = [
        "text-2xl",
        "text-xl",
        "text-lg",
        "text-base",
        "text-sm",
        "text-sm",
      ];
      const className = `${
        sizes[level - 1]
      } font-semibold mt-4 mb-2 first:mt-0 break-words`;

      // Render appropriate header level
      const header =
        level === 1 ? (
          <h1 key={elements.length} className={className}>
            {parseInlineMarkdown(text, citationMap, annotations)}
          </h1>
        ) : level === 2 ? (
          <h2 key={elements.length} className={className}>
            {parseInlineMarkdown(text, citationMap, annotations)}
          </h2>
        ) : level === 3 ? (
          <h3 key={elements.length} className={className}>
            {parseInlineMarkdown(text, citationMap, annotations)}
          </h3>
        ) : level === 4 ? (
          <h4 key={elements.length} className={className}>
            {parseInlineMarkdown(text, citationMap, annotations)}
          </h4>
        ) : level === 5 ? (
          <h5 key={elements.length} className={className}>
            {parseInlineMarkdown(text, citationMap, annotations)}
          </h5>
        ) : (
          <h6 key={elements.length} className={className}>
            {parseInlineMarkdown(text, citationMap, annotations)}
          </h6>
        );

      elements.push(header);
      i++;
      continue;
    }

    // Unordered lists
    if (line.match(/^[\s]*[-*+]\s+/)) {
      const listItems: string[] = [];

      while (i < lines.length && lines[i].match(/^[\s]*[-*+]\s+/)) {
        const itemText = lines[i].replace(/^[\s]*[-*+]\s+/, "");
        listItems.push(itemText);
        i++;
      }

      elements.push(
        <ul
          key={elements.length}
          className="my-2 ml-4 list-disc space-y-1 break-words"
        >
          {listItems.map((item, idx) => (
            <li key={idx} className="text-sm break-words">
              {parseInlineMarkdown(item, citationMap, annotations)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Ordered lists
    if (line.match(/^[\s]*\d+\.\s+/)) {
      const listItems: string[] = [];

      while (i < lines.length && lines[i].match(/^[\s]*\d+\.\s+/)) {
        const itemText = lines[i].replace(/^[\s]*\d+\.\s+/, "");
        listItems.push(itemText);
        i++;
      }

      elements.push(
        <ol
          key={elements.length}
          className="my-2 ml-4 list-decimal space-y-1 break-words"
        >
          {listItems.map((item, idx) => (
            <li key={idx} className="text-sm break-words">
              {parseInlineMarkdown(item, citationMap, annotations)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // Tables
    if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
      const tableLines: string[] = [];

      // Collect all table lines
      while (
        i < lines.length &&
        lines[i].trim().startsWith("|") &&
        lines[i].trim().endsWith("|")
      ) {
        tableLines.push(lines[i].trim());
        i++;
      }

      // Parse table (need at least 2 lines: header + separator)
      if (tableLines.length >= 2) {
        const headerCells = tableLines[0]
          .split("|")
          .slice(1, -1)
          .map((cell) => cell.trim());

        // Check if second line is a separator (contains dashes)
        const isSeparator = tableLines[1].match(/^\|[\s\-:|]+\|$/);

        if (isSeparator) {
          const bodyRows = tableLines.slice(2).map((row) =>
            row
              .split("|")
              .slice(1, -1)
              .map((cell) => cell.trim())
          );

          elements.push(
            <div key={elements.length} className="my-3 overflow-x-auto">
              <table className="min-w-full border border-foreground/10 text-sm">
                <thead className="bg-foreground/5">
                  <tr>
                    {headerCells.map((header, idx) => (
                      <th
                        key={idx}
                        className="border-b border-foreground/10 px-3 py-2 text-left font-semibold break-words"
                      >
                        {parseInlineMarkdown(header, citationMap, annotations)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {bodyRows.map((row, rowIdx) => (
                    <tr
                      key={rowIdx}
                      className="border-b border-foreground/5 last:border-b-0"
                    >
                      {row.map((cell, cellIdx) => (
                        <td
                          key={cellIdx}
                          className="px-3 py-2 border-r border-foreground/5 last:border-r-0 break-words"
                        >
                          {parseInlineMarkdown(cell, citationMap, annotations)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
          continue;
        }
      }

      // Not a valid table, render as regular paragraphs
      for (const tableLine of tableLines) {
        elements.push(
          <p key={elements.length} className="my-1">
            {parseInlineMarkdown(tableLine, citationMap, annotations)}
          </p>
        );
      }
      continue;
    }

    // Blockquotes
    if (line.trim().startsWith(">")) {
      const quoteLines: string[] = [];

      while (i < lines.length && lines[i].trim().startsWith(">")) {
        quoteLines.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }

      elements.push(
        <blockquote
          key={elements.length}
          className="my-2 pl-4 border-l-4 border-current/30 opacity-80 italic break-words"
        >
          {quoteLines.map((quoteLine, idx) => (
            <div key={idx} className="break-words">
              {parseInlineMarkdown(quoteLine, citationMap, annotations)}
            </div>
          ))}
        </blockquote>
      );
      continue;
    }

    // Horizontal rule
    if (line.match(/^[\s]*[-*_]{3,}[\s]*$/)) {
      elements.push(
        <hr key={elements.length} className="my-4 border-t border-border" />
      );
      i++;
      continue;
    }

    // Empty line
    if (line.trim() === "") {
      elements.push(<div key={elements.length} className="h-2" />);
      i++;
      continue;
    }

    // Regular paragraph
    elements.push(
      <p key={elements.length} className="my-1 break-words">
        {parseInlineMarkdown(line, citationMap, annotations)}
      </p>
    );
    i++;
  }

  return (
    <div className={`markdown-content break-words ${className}`}>
      {elements}
    </div>
  );
}

/**
 * Parse inline markdown patterns (bold, italic, code, links)
 */
/**
 * Parse inline markdown patterns (bold, italic, code, links)
 */
function parseInlineMarkdown(text: string, citationMap?: Map<string, FileCitationAnnotation>, annotations?: Annotation[]): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  // Pattern priority: code > bold > italic > links
  // This prevents conflicts between overlapping patterns

  while (remaining.length > 0) {
    // Inline code (highest priority to avoid parsing inside code)
    const codeMatch = remaining.match(/`([^`]+)`/);
    if (codeMatch && codeMatch.index !== undefined) {
      // Add text before code
      if (codeMatch.index > 0) {
        parts.push(
          <span key={key++}>
            {parseBoldItalicLinks(remaining.slice(0, codeMatch.index), citationMap, annotations)}
          </span>
        );
      }

      // Add code
      parts.push(
        <code
          key={key++}
          className="px-1.5 py-0.5 bg-foreground/10 rounded text-xs font-mono border border-foreground/20"
        >
          {codeMatch[1]}
        </code>
      );

      remaining = remaining.slice(codeMatch.index + codeMatch[0].length);
      continue;
    }

    // No more special patterns, parse remaining text for bold/italic/links
    parts.push(<span key={key++}>{parseBoldItalicLinks(remaining, citationMap, annotations)}</span>);
    break;
  }

  return parts;
}

/**
 * Parse bold, italic, links, and citation markers (after code has been extracted)
 */
function parseBoldItalicLinks(text: string, citationMap?: Map<string, FileCitationAnnotation>, annotations?: Annotation[]): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // Try to match patterns in order of priority
    // CITATION PATTERNS MUST COME FIRST to prevent [4] being eaten by link patterns
    const patterns = [
      // 1. Citation patterns - HIGHEST PRIORITY (antes de qualquer link)
      { regex: /【(\d+)†([^】]+)】/, component: "citation-openai" }, // 【1†source】
      { regex: /\[(fonte|source):\s*([^\]]+)\]/i, component: "citation-file" }, // [fonte: file.pdf]
      { regex: /\[doc(\d+)\]/i, component: "citation-num" }, // [doc1], [doc2]
      { regex: /\[(\d+)\](?!\()/, component: "citation-num" }, // [1], [2], [4] - negative lookahead to not match [1](
      // 2. Link patterns - after citations
      { regex: /\*\*\[([^\]]+)\]\(([^)]+)\)\*\*/, component: "strong-link" }, // **[text](url)**
      { regex: /__\[([^\]]+)\]\(([^)]+)\)__/, component: "strong-link" }, // __[text](url)__
      { regex: /\*\[([^\]]+)\]\(([^)]+)\)\*/, component: "em-link" }, // *[text](url)*
      { regex: /_\[([^\]]+)\]\(([^)]+)\)_/, component: "em-link" }, // _[text](url)_
      { regex: /\[([^\]]+)\]\(([^)]+)\)/, component: "link" }, // [text](url)
      // 3. Text formatting - lowest priority
      { regex: /\*\*(.+?)\*\*/, component: "strong" }, // **bold**
      { regex: /__(.+?)__/, component: "strong" }, // __bold__
      { regex: /\*(.+?)\*/, component: "em" }, // *italic*
      { regex: /_(.+?)_/, component: "em" }, // _italic_
    ];

    let bestMatch: {
      match: RegExpMatchArray;
      pattern: typeof patterns[0];
      index: number;
    } | null = null;

    // Find the earliest match among all patterns
    for (const pattern of patterns) {
      const match = remaining.match(pattern.regex);

      if (match && match.index !== undefined) {
        if (!bestMatch || match.index < bestMatch.index) {
          bestMatch = { match, pattern, index: match.index };
        }
      }
    }

    if (bestMatch) {
      const { match, pattern } = bestMatch;

      // Add text before match
      if (match.index! > 0) {
        parts.push(remaining.slice(0, match.index));
      }

      // Add matched element
      if (pattern.component === "strong") {
        parts.push(
          <strong key={key++} className="font-semibold">
            {match[1]}
          </strong>
        );
      } else if (pattern.component === "em") {
        parts.push(
          <em key={key++} className="italic">
            {match[1]}
          </em>
        );
      } else if (pattern.component === "strong-link") {
        // **[text](url)** - Bold link
        const linkText = match[1];
        const linkUrl = match[2];
        const formattedLinkText = parseBoldItalicLinks(linkText, citationMap, annotations);

        parts.push(
          <strong key={key++} className="font-semibold">
            <a
              href={linkUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline break-words"
            >
              {formattedLinkText}
            </a>
          </strong>
        );
      } else if (pattern.component === "em-link") {
        // *[text](url)* - Italic link
        const linkText = match[1];
        const linkUrl = match[2];
        const formattedLinkText = parseBoldItalicLinks(linkText, citationMap, annotations);

        parts.push(
          <em key={key++} className="italic">
            <a
              href={linkUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline break-words"
            >
              {formattedLinkText}
            </a>
          </em>
        );
      } else if (pattern.component === "link") {
        // [text](url) - Regular link
        const linkText = match[1];
        const linkUrl = match[2];
        const formattedLinkText = parseBoldItalicLinks(linkText, citationMap, annotations);

        parts.push(
          <a
            key={key++}
            href={linkUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline break-words"
          >
            {formattedLinkText}
          </a>
        );
        } else if (pattern.component === "citation-num" || pattern.component === "citation-file" || pattern.component === "citation-openai") {
          // Citações
          const fullMatch = match[0];
          
          // Tentar encontrar anotação de várias formas
          let annotation = citationMap?.get(fullMatch);
          
          // Se não encontrou, tentar normalizar o match
          if (!annotation && citationMap) {
            // Para citation-num [1], [2], etc - tentar [1], [doc1], ou apenas o número
            if (pattern.component === "citation-num") {
              const num = match[1];
              annotation = citationMap.get(`[${num}]`) || citationMap.get(`[doc${num}]`) || citationMap.get(num);
            }
          }

          // Fallback final: procurar na lista de anotações se o texto contém o número
          if (!annotation && annotations && pattern.component === "citation-num") {
             const num = match[1];
             annotation = annotations.find(a => 
               a.type === "file_citation" && 
               a.text && 
               (a.text === fullMatch || a.text.includes(`[${num}]`))
             ) as FileCitationAnnotation | undefined;
          }

          // Se ainda não encontrou, procurar por índice nas anotações
          if (!annotation && annotations && annotations.length > 0) {
            // Pegar a primeira anotação disponível como fallback
            // (quando há apenas uma citação e ela corresponde)
            if (annotations.length === 1) {
              annotation = annotations[0] as FileCitationAnnotation;
            } else if (pattern.component === "citation-num") {
              // Tentar encontrar pelo número (índice 1-based)
              const num = parseInt(match[1], 10);
              if (num > 0 && num <= annotations.length) {
                annotation = annotations[num - 1] as FileCitationAnnotation;
              }
            }
          }        let content: React.ReactNode;
        
        if (pattern.component === "citation-num") {
            const citationNum = match[1];
            content = (
              <span className="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1 mx-0.5 text-xs font-medium rounded bg-primary/10 text-primary border border-primary/20">
                {citationNum}
              </span>
            );
        } else if (pattern.component === "citation-file") {
            const filename = match[2].trim();
            content = (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 mx-0.5 text-xs font-medium rounded bg-primary/10 text-primary border border-primary/20">
                <FileText className="w-3 h-3" />
                {filename}
              </span>
            );
        } else {
            // OpenAI
            const citationNum = match[1];
            content = (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 mx-0.5 text-xs font-medium rounded bg-primary/10 text-primary border border-primary/20">
                {citationNum}
              </span>
            );
        }

        if (annotation) {
          console.log(`[MarkdownRenderer] ✅ Citação '${fullMatch}' encontrada:`, {
            filename: annotation.filename || annotation.file_citation?.filename,
            quote: (annotation.quote || annotation.file_citation?.quote)?.substring(0, 30),
          });
          parts.push(
            <CitationPopup key={key++} annotation={annotation}>
              {content}
            </CitationPopup>
          );
        } else {
          console.log(`[MarkdownRenderer] ❌ Citação '${fullMatch}' NÃO encontrada. Keys disponíveis:`, Array.from(citationMap?.keys() || []));
          // Fallback se não houver anotação (apenas renderiza o span estático)
          parts.push(<span key={key++} title="Referência não encontrada">{content}</span>);
        }
      }

      remaining = remaining.slice(match.index! + match[0].length);
    } else {
      // No pattern matched, add remaining text and exit
      if (remaining.length > 0) {
        parts.push(remaining);
      }
      break;
    }
  }

  return parts;
}