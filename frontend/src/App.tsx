import React, { useState } from "react";
import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { ImageDropzone } from "./components/ImageDropzone";
import { TextSearchForm } from "./components/TextSearchForm";
import { ResultList } from "./components/ResultList";
import { SkeletonLoader } from "./components/SkeletonLoader";
import { ErrorAlert } from "./components/ErrorAlert";
import { EmptyState } from "./components/EmptyState";
import { IconImage, IconText } from "./components/Icons";
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
          title: "Error de conexión",
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
          title: "Error de conexión",
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
      }}
    >
      <Header />

      <main
        style={{
          flex: 1,
          maxWidth: "1000px",
          width: "100%",
          margin: "0 auto",
          padding: "0 1.25rem 3rem",
        }}
      >
        {/* Hero Section */}
        <section className="hero-section">
          <h1 className="hero-title">Encontrá el anime que estás buscando</h1>
          <p className="hero-subtitle">
            Subí una captura de cualquier escena o describí la trama y
            personajes que recordás para identificar el anime.
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
              <IconImage size={16} />
              <span>Por Imagen</span>
            </button>
            <button
              role="tab"
              aria-selected={activeMode === "text"}
              className={`mode-tab-button ${activeMode === "text" ? "active" : ""}`}
              onClick={() => handleModeChange("text")}
            >
              <IconText size={16} />
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
