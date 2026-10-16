import React, { useState } from "react";

interface TextSearchFormProps {
  onSearch: (description: string) => void;
  isLoading: boolean;
}

const SUGGESTIONS = [
  "Un chico con un cuaderno sobrenatural que mata a quien escribe su nombre",
  "Una elfa maga de pelo blanco que emprende un viaje tras la muerte del héroe",
  "Un mundo donde toda la humanidad fue petrificada en piedra por miles de años",
  "Un chico con demonio motosierra en el pecho que se une a cazadores de demonios",
];

export const TextSearchForm: React.FC<TextSearchFormProps> = ({
  onSearch,
  isLoading,
}) => {
  const [description, setDescription] = useState("");

  const trimmed = description.trim();
  const charCount = description.length;
  const isTooShort = trimmed.length > 0 && trimmed.length < 3;
  const isTooLong = charCount > 500;
  const isValid = trimmed.length >= 3 && !isTooLong;

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (isValid && !isLoading) {
      onSearch(trimmed);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey || !e.shiftKey) && e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleApplySuggestion = (suggestion: string) => {
    setDescription(suggestion);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="text-search-form"
      style={{ width: "100%", maxWidth: "700px", margin: "0 auto" }}
    >
      <div className="textarea-wrapper">
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describí lo que recordás: personajes, escena inicial, poderes, ambientación... (ej: 'anime de un chef invocado a otro mundo que cocina para un lobo')"
          className="text-search-input"
          disabled={isLoading}
          maxLength={550}
          aria-label="Descripción de la trama o personajes"
        />
        <div className="textarea-footer">
          <span>Presioná <strong>Enter</strong> para buscar</span>
          <span
            className={`char-counter ${
              isTooLong ? "is-danger" : charCount > 450 ? "is-warning" : ""
            }`}
          >
            {charCount}/500
          </span>
        </div>
      </div>

      {isTooShort && (
        <p style={{ fontSize: "0.8rem", color: "var(--color-warning)", marginTop: "-0.5rem" }}>
          La descripción debe tener al menos 3 caracteres.
        </p>
      )}

      {/* Suggestion Chips */}
      <div className="suggestion-chips">
        <span className="suggestion-chips-label">Ejemplos:</span>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            type="button"
            className="chip-btn"
            onClick={() => handleApplySuggestion(s)}
            disabled={isLoading}
          >
            "{s.slice(0, 32)}..."
          </button>
        ))}
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>
        <button
          type="submit"
          disabled={!isValid || isLoading}
          className="btn-primary"
        >
          {isLoading ? "🧠 Razonando trama con IA..." : "✨ Buscar Anime"}
        </button>
      </div>
    </form>
  );
};
