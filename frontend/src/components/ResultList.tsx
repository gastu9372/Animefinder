import React from "react";
import { SearchResponse } from "../types/api";
import { ResultCard } from "./ResultCard";

interface ResultListProps {
  response: SearchResponse;
}

export const ResultList: React.FC<ResultListProps> = ({ response }) => {
  const getSearchModeLabel = () => {
    switch (response.search_mode) {
      case "llm":
        return (
          <span className="badge-tag badge-mode-llm">
            🧠 Motor IA: Google Gemini
          </span>
        );
      case "fallback":
        return (
          <span className="badge-tag badge-mode-fallback">
            🔄 Modo Fallback: AniList Directo
          </span>
        );
      case "trace.moe":
      default:
        return (
          <span className="badge-tag" style={{ background: "hsla(210, 80%, 55%, 0.15)", color: "var(--color-info)" }}>
            📷 Motor de Imagen: trace.moe
          </span>
        );
    }
  };

  return (
    <section aria-label="Resultados de búsqueda" style={{ marginTop: "2rem" }}>
      {/* Search Meta Status Bar */}
      <div className="search-meta-bar">
        <div className="meta-stats">
          <span>{getSearchModeLabel()}</span>
          {response.cached && (
            <span className="badge-tag badge-cached">⚡ Desde Caché</span>
          )}
          <span>⏱ {response.processing_time_ms} ms</span>
        </div>

        <div>
          <span style={{ color: "var(--color-text-muted)" }}>
            {response.results.length} anime{response.results.length !== 1 ? "s" : ""} encontrado{response.results.length !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {response.filtered_count > 0 && (
        <div
          style={{
            fontSize: "0.85rem",
            color: "var(--color-text-dim)",
            textAlign: "left",
            marginBottom: "1rem",
            padding: "0 0.5rem",
          }}
        >
          ℹ️ Se descartaron {response.filtered_count} resultado{response.filtered_count > 1 ? "s" : ""} por umbral de similitud o filtro de contenido.
        </div>
      )}

      {/* Results Grid */}
      <div className="results-grid">
        {response.results.map((result) => (
          <ResultCard key={result.id} result={result} />
        ))}
      </div>
    </section>
  );
};
