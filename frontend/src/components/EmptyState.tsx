import React from "react";

interface EmptyStateProps {
  queryType: "image" | "text";
  onReset?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  queryType,
  onReset,
}) => {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" aria-hidden="true">
        🔍
      </div>
      <h3>No encontramos ningún anime que coincida</h3>
      <p>
        {queryType === "image"
          ? "Asegurate de que la imagen sea una captura nítida directamente de un episodio de anime (no fanart ni fotografías editadas)."
          : "Probá agregando más detalles característicos: colores de pelo, poderes especiales, nombres de acompañantes o momentos clave de la trama."}
      </p>
      {onReset && (
        <button
          onClick={onReset}
          className="btn-secondary"
          style={{ marginTop: "1.25rem", padding: "0.5rem 1.25rem" }}
        >
          Intentar con otra búsqueda
        </button>
      )}
    </div>
  );
};
