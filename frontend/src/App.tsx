import React, { useState } from "react";
import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { ImageDropzone } from "./components/ImageDropzone";
import { TextSearchForm } from "./components/TextSearchForm";
import { ResultList } from "./components/ResultList";
import { SkeletonLoader } from "./components/SkeletonLoader";
import { ErrorAlert } from "./components/ErrorAlert";
import { EmptyState } from "./components/EmptyState";
import { apiClient, ApiError } from "./services/apiClient";
import { ProblemDetails, SearchResponse } from "./types/api";

export const App: React.FC = () => {
  const [activeMode, setActiveMode] = useState<"image" | "text">("image");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(
    null,
  );
  const [error, setError] = useState<ProblemDetails | null>(null);

  const handleImageSearch = async (file: File) => {
    setIsLoading(true);
    setError(null);
    setSearchResponse(null);

    try {
      const data = await apiClient.searchByImage(file);
      setSearchResponse(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem);
      } else {
        setError({
          type: "about:blank",
          title: "Error inesperado",
          status: 500,
          detail:
            "No se pudo conectar con el servidor. Comprobá tu conexión a internet.",
          code: "CLIENT_ERROR",
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleTextSearch = async (description: string) => {
    setIsLoading(true);
    setError(null);
    setSearchResponse(null);

    try {
      const data = await apiClient.searchByText(description);
      setSearchResponse(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem);
      } else {
        setError({
          type: "about:blank",
          title: "Error inesperado",
          status: 500,
          detail:
            "No se pudo conectar con el servidor. Comprobá tu conexión a internet.",
          code: "CLIENT_ERROR",
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleModeChange = (mode: "image" | "text") => {
    setActiveMode(mode);
    setError(null);
  };

  return (
    <div
      className="app-container"
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        padding: "0 1rem",
      }}
    >
      <Header />

      <main
        style={{
          flex: 1,
          maxWidth: "1000px",
          width: "100%",
          margin: "1.5rem auto 3rem",
          textAlign: "center",
        }}
      >
        {/* Hero Section */}
        <section className="hero-section" style={{ margin: "1.5rem 0 2rem" }}>
          <h2
            style={{
              fontSize: "2.5rem",
              fontWeight: 800,
              marginBottom: "0.75rem",
              letterSpacing: "-0.02em",
            }}
          >
            Descubrí qué anime estás buscando en{" "}
            <span className="text-gradient">segundos</span>
          </h2>
          <p
            style={{
              fontSize: "1.1rem",
              color: "var(--color-text-muted)",
              maxWidth: "640px",
              margin: "0 auto 1.75rem",
            }}
          >
            Subí una captura de cualquier escena o describí en lenguaje libre lo
            que recordás de la trama y personajes.
          </p>

          {/* Mode Selector Tabs */}
          <div
            className="mode-tabs"
            role="tablist"
            aria-label="Modo de búsqueda"
          >
            <button
              role="tab"
              aria-selected={activeMode === "image"}
              className={`mode-tab-button ${activeMode === "image" ? "active" : ""}`}
              onClick={() => handleModeChange("image")}
            >
              <span>📷</span>
              <span>Por Imagen</span>
            </button>
            <button
              role="tab"
              aria-selected={activeMode === "text"}
              className={`mode-tab-button ${activeMode === "text" ? "active" : ""}`}
              onClick={() => handleModeChange("text")}
            >
              <span>✍️</span>
              <span>Por Descripción</span>
            </button>
          </div>
        </section>

        {/* Search Input Forms */}
        <section aria-label="Formulario de búsqueda">
          {activeMode === "image" ? (
            <ImageDropzone onSearch={handleImageSearch} isLoading={isLoading} />
          ) : (
            <TextSearchForm onSearch={handleTextSearch} isLoading={isLoading} />
          )}
        </section>

        {/* Feedback & Result States */}
        {error && (
          <ErrorAlert problem={error} onDismiss={() => setError(null)} />
        )}

        {isLoading && <SkeletonLoader />}

        {!isLoading && searchResponse && searchResponse.results.length > 0 && (
          <ResultList response={searchResponse} />
        )}

        {!isLoading &&
          searchResponse &&
          searchResponse.results.length === 0 && (
            <EmptyState
              queryType={searchResponse.query_type}
              onReset={() => setSearchResponse(null)}
            />
          )}
      </main>

      <Footer />
    </div>
  );
};

export default App;
