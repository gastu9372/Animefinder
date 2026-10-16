import React from "react";

export const Header: React.FC = () => {
  return (
    <header
      className="site-header glass-panel"
      style={{
        margin: "1.5rem auto",
        maxWidth: "1200px",
        padding: "1rem 2rem",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <div
        className="logo-container"
        style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}
      >
        <span style={{ fontSize: "1.75rem" }} role="img" aria-label="sparkles">
          ✨
        </span>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 800 }}>
          Anime<span className="text-gradient">Finder</span>
        </h1>
      </div>
      <nav
        style={{
          display: "flex",
          gap: "1.5rem",
          fontSize: "0.95rem",
          fontWeight: 500,
        }}
      >
        <a href="#buscar-imagen">Buscar por Imagen</a>
        <a href="#buscar-descripcion">Buscar por Descripción</a>
      </nav>
    </header>
  );
};
