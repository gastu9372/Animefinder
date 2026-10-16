import React from "react";

export const SkeletonLoader: React.FC = () => {
  return (
    <div
      className="results-grid"
      aria-busy="true"
      aria-label="Cargando resultados de búsqueda"
    >
      {[1, 2, 3].map((idx) => (
        <div key={idx} className="skeleton-card">
          <div
            className="skeleton-box"
            style={{ width: "100%", aspectRatio: "2 / 3" }}
          />
          <div
            style={{ display: "flex", flexDirection: "column", gap: "1rem" }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div
                className="skeleton-box"
                style={{ width: "60%", height: "28px" }}
              />
              <div
                className="skeleton-box"
                style={{
                  width: "80px",
                  height: "24px",
                  borderRadius: "9999px",
                }}
              />
            </div>
            <div
              className="skeleton-box"
              style={{ width: "35%", height: "18px" }}
            />
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <div
                className="skeleton-box"
                style={{ width: "60px", height: "20px" }}
              />
              <div
                className="skeleton-box"
                style={{ width: "70px", height: "20px" }}
              />
            </div>
            <div
              className="skeleton-box"
              style={{ width: "100%", height: "70px" }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};
