import React from "react";

export const Footer: React.FC = () => {
  return (
    <footer
      className="site-footer"
      style={{
        marginTop: "auto",
        padding: "3rem 1.5rem",
        textAlign: "center",
        borderTop: "1px solid var(--color-border-subtle)",
        color: "var(--color-text-muted)",
        fontSize: "0.875rem",
      }}
    >
      <div
        style={{
          maxWidth: "800px",
          margin: "0 auto",
          display: "flex",
          flexDirection: "column",
          gap: "0.75rem",
        }}
      >
        <p>
          Reconocimiento de escenas impulsado por{" "}
          <a href="https://trace.moe" target="_blank" rel="noopener noreferrer">
            trace.moe
          </a>
          . Metadatos, portadas y sinopsis provistos por{" "}
          <a
            href="https://anilist.co"
            target="_blank"
            rel="noopener noreferrer"
          >
            AniList GraphQL API
          </a>
          .
        </p>
        <p style={{ fontSize: "0.8rem", color: "var(--color-text-dim)" }}>
          <strong>Privacidad:</strong> Las imágenes subidas se procesan
          exclusivamente en memoria volátil para cotejar fotogramas mediante
          trace.moe y no se almacenan en disco. Las descripciones se analizan
          mediante modelos de IA y AniList.
        </p>
        <p style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>
          © {new Date().getFullYear()} AnimeFinder — Uso no comercial con fines
          de referencia.
        </p>
      </div>
    </footer>
  );
};
