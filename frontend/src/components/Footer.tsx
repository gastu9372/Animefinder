import React from "react";

export const Footer: React.FC = () => {
  return (
    <footer
      className="site-footer"
      style={{
        marginTop: "auto",
        padding: "2.5rem 1.5rem",
        textAlign: "center",
        borderTop: "1px solid var(--color-border-subtle)",
        color: "var(--color-text-dim)",
        fontSize: "0.82rem",
      }}
    >
      <div
        style={{
          maxWidth: "760px",
          margin: "0 auto",
          display: "flex",
          flexDirection: "column",
          gap: "0.6rem",
        }}
      >
        <p>
          Reconocimiento de fotogramas vía{" "}
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
        <p style={{ fontSize: "0.78rem" }}>
          Las capturas se cotejan en memoria volátil y no se almacenan en
          servidores permanentes.
        </p>
        <p style={{ fontSize: "0.75rem", opacity: 0.8 }}>
          © {new Date().getFullYear()} AnimeFinder — Plataforma de referencia
          sin fines comerciales.
        </p>
      </div>
    </footer>
  );
};
