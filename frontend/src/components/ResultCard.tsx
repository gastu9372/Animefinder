import React, { useState } from "react";
import { AnimeResult } from "../types/api";
import {
  IconCalendar,
  IconClock,
  IconClose,
  IconPlay,
  IconTarget,
  IconTv,
} from "./Icons";

interface ResultCardProps {
  result: AnimeResult;
}

export const ResultCard: React.FC<ResultCardProps> = ({ result }) => {
  const [showFullSynopsis, setShowFullSynopsis] = useState(false);
  const [isAdultRevealed, setIsAdultRevealed] = useState(!result.is_adult);
  const [showVideo, setShowVideo] = useState(false);

  // Confidence styling
  const getConfidenceBadge = () => {
    if (result.confidence_percentage !== null) {
      const value =
        result.confidence_percentage > 1
          ? result.confidence_percentage
          : result.confidence_percentage * 100;
      const pct = value.toFixed(1);
      const levelClass =
        value >= 85
          ? "confidence-high"
          : value >= 70
            ? "confidence-medium"
            : "confidence-low";
      return (
        <span className={`confidence-pill ${levelClass}`}>
          <IconTarget size={13} />
          <span>{pct}% de precisión</span>
        </span>
      );
    }

    const levelClass =
      result.confidence_level === "high"
        ? "confidence-high"
        : result.confidence_level === "medium"
          ? "confidence-medium"
          : "confidence-low";

    const label =
      result.confidence_level === "high"
        ? "Alta coincidencia"
        : result.confidence_level === "medium"
          ? "Coincidencia media"
          : "Sugerencia aproximada";

    return (
      <span className={`confidence-pill ${levelClass}`}>
        <IconTarget size={13} />
        <span>{label}</span>
      </span>
    );
  };

  const isSynopsisLong = result.synopsis && result.synopsis.length > 240;
  const displayedSynopsis =
    isSynopsisLong && !showFullSynopsis
      ? `${result.synopsis.slice(0, 240)}...`
      : result.synopsis;

  return (
    <article className="result-card">
      {/* Cover Image & Blur protection */}
      <div className="result-cover-wrapper">
        <img
          src={result.cover_image}
          alt={`Portada de ${result.title.romaji}`}
          className={`result-cover ${result.is_adult && !isAdultRevealed ? "is-blurred" : ""}`}
          loading="lazy"
        />
        {result.is_adult && !isAdultRevealed && (
          <div className="cover-blur-overlay">
            <span
              style={{ fontSize: "0.75rem", color: "#fff", fontWeight: 600 }}
            >
              Contenido +18
            </span>
            <button
              onClick={() => setIsAdultRevealed(true)}
              className="cover-blur-btn"
            >
              Revelar
            </button>
          </div>
        )}
      </div>

      {/* Main Details */}
      <div className="result-content">
        <div className="result-header">
          <div>
            <h3 className="result-title-romaji">{result.title.romaji}</h3>
            <div className="result-subtitles">
              {result.title.english && <span>{result.title.english}</span>}
              {result.title.english && result.title.native && <span> • </span>}
              {result.title.native && <span>{result.title.native}</span>}
            </div>
          </div>
          <div>{getConfidenceBadge()}</div>
        </div>

        {/* Badges Bar */}
        <div className="result-badges">
          {result.year && (
            <span className="meta-badge">
              <IconCalendar size={13} />
              <span>{result.year}</span>
            </span>
          )}
          {result.format && (
            <span className="meta-badge">
              <IconTv size={13} />
              <span>{result.format}</span>
            </span>
          )}
          {result.scene_info?.episode !== null &&
            result.scene_info?.episode !== undefined && (
              <span className="meta-badge scene-badge">
                Episodio {result.scene_info.episode}
              </span>
            )}
          {result.scene_info?.timestamp_formatted && (
            <span className="meta-badge scene-badge">
              <IconClock size={13} />
              <span>{result.scene_info.timestamp_formatted}</span>
            </span>
          )}
          {result.is_adult && (
            <span
              className="meta-badge"
              style={{
                background: "var(--color-danger-subtle)",
                color: "var(--color-danger)",
              }}
            >
              +18
            </span>
          )}
        </div>

        {/* Match Reason */}
        {result.match_reason && (
          <div className="match-reason-box">
            <strong>Por qué coincide</strong>
            <p>{result.match_reason}</p>
          </div>
        )}

        {/* Synopsis */}
        {result.synopsis && (
          <p className="result-synopsis">
            {displayedSynopsis}
            {isSynopsisLong && (
              <button
                type="button"
                className="synopsis-toggle-btn"
                onClick={() => setShowFullSynopsis((prev) => !prev)}
              >
                {showFullSynopsis ? "Mostrar menos" : "Leer más"}
              </button>
            )}
          </p>
        )}

        {/* Video Preview Action if present */}
        {result.scene_info?.preview_video_url && (
          <div>
            {!showVideo ? (
              <button
                type="button"
                onClick={() => setShowVideo(true)}
                className="btn-secondary"
                style={{
                  padding: "0.35rem 0.75rem",
                  fontSize: "0.8rem",
                  marginTop: "0.25rem",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.4rem",
                }}
              >
                <IconPlay size={12} />
                <span>Ver escena</span>
              </button>
            ) : (
              <div className="video-preview-section">
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "0.5rem",
                  }}
                >
                  <span
                    style={{
                      fontSize: "0.8rem",
                      color: "var(--color-text-muted)",
                    }}
                  >
                    Escena en {result.scene_info.timestamp_formatted}
                  </span>
                  <button
                    onClick={() => setShowVideo(false)}
                    style={{
                      background: "none",
                      color: "var(--color-text-muted)",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.25rem",
                      fontSize: "0.8rem",
                    }}
                  >
                    <IconClose size={14} />
                    <span>Cerrar</span>
                  </button>
                </div>
                <video
                  src={result.scene_info.preview_video_url}
                  controls
                  autoPlay
                  muted
                  loop
                  className="video-player"
                />
              </div>
            )}
          </div>
        )}
      </div>
    </article>
  );
};
