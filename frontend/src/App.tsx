import React from "react";
import { Header } from "./components/Header";
import { Footer } from "./components/Footer";

export const App: React.FC = () => {
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
          margin: "2rem auto",
          textAlign: "center",
        }}
      >
        <section className="hero-section" style={{ margin: "3rem 0" }}>
          <h2
            style={{
              fontSize: "2.75rem",
              fontWeight: 800,
              marginBottom: "1rem",
              letterSpacing: "-0.02em",
            }}
          >
            Descubrí qué anime estás buscando en{" "}
            <span className="text-gradient">segundos</span>
          </h2>
          <p
            style={{
              fontSize: "1.15rem",
              color: "var(--color-text-muted)",
              maxWidth: "650px",
              margin: "0 auto 2.5rem",
            }}
          >
            Subí una captura de pantalla de cualquier escena o describí
            libremente lo que recordás de la trama y personajes.
          </p>

          <div
            style={{
              display: "flex",
              justifyContent: "center",
              gap: "1rem",
              flexWrap: "wrap",
            }}
          >
            <button
              className="glass-panel"
              style={{
                padding: "0.9rem 1.75rem",
                fontSize: "1rem",
                fontWeight: 600,
                color: "var(--color-text-main)",
                border: "1px solid var(--color-border-glow)",
                background: "var(--gradient-glass)",
              }}
            >
              📷 Subir o Pegar Imagen
            </button>
            <button
              className="glass-panel"
              style={{
                padding: "0.9rem 1.75rem",
                fontSize: "1rem",
                fontWeight: 600,
                color: "var(--color-text-main)",
              }}
            >
              ✍️ Buscar por Descripción
            </button>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default App;
