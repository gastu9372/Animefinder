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
            Análisis de descripción
          </span>
        );
      case "fallback":
        return (
          <span className="badge-tag badge-mode-fallback">
            Búsqueda directa
          </span>
        );
      case "trace.moe":
      default:
        return (
          <span
            className="badge-tag"
            style={{
              background: "var(--color-bg-elevated)",
              color: "var(--color-text-muted)",
            }}
          >
            trace.moe
          </span>
        );
    }
  };

  return (
    <section aria-label="Resultados de búsqueda" style={{ marginTop: "1rem" }}>
      {/* Search Meta Status Bar */}
      <div className="search-meta-bar">
        <div className="meta-stats">
          <span>{getSearchModeLabel()}</span>
          {response.cached && (
            <span className="badge-tag badge-cached">En caché</span>
          )}
          <span>{response.processing_time_ms} ms</span>
        </div>

        <div>
          <span style={{ color: "var(--color-text-muted)" }}>
            {response.results.length} resultado
            {response.results.length !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {response.filtered_count > 0 && (
        <div
          style={{
            fontSize: "0.82rem",
            color: "var(--color-text-dim)",
            textAlign: "left",
            marginBottom: "0.75rem",
            padding: "0 0.25rem",
          }}
        >
          Se omitieron {response.filtered_count} resultado
          {response.filtered_count > 1 ? "s" : ""} por baja coincidencia.
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
