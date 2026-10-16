import React, { useCallback, useEffect, useRef, useState } from "react";
import { IconAlert, IconSearch, IconUpload } from "./Icons";

interface ImageDropzoneProps {
  onSearch: (file: File) => void;
  isLoading: boolean;
}

const MAX_FILE_SIZE_BYTES = 8 * 1024 * 1024; // 8MB
const ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"];

export const ImageDropzone: React.FC<ImageDropzoneProps> = ({
  onSearch,
  isLoading,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = useCallback((file: File) => {
    setValidationError(null);

    if (!ALLOWED_MIME_TYPES.includes(file.type)) {
      setValidationError(
        "Formato no compatible. Por favor subí una imagen JPEG, PNG o WebP.",
      );
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setValidationError("La imagen supera el límite de 8 MB.");
      return;
    }

    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  }, []);

  // Cleanup blob URL on unmount or file change
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // Handle global paste event (Ctrl+V)
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      if (isLoading) return;
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.startsWith("image/")) {
          const file = items[i].getAsFile();
          if (file) {
            validateAndSetFile(file);
            break;
          }
        }
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, [isLoading, validateAndSetFile]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isLoading) setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (isLoading) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      validateAndSetFile(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      validateAndSetFile(files[0]);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setValidationError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = () => {
    if (selectedFile && !isLoading) {
      onSearch(selectedFile);
    }
  };

  return (
    <div
      className="dropzone-wrapper"
      style={{ width: "100%", maxWidth: "620px", margin: "0 auto" }}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInputChange}
        accept="image/jpeg,image/png,image/webp"
        style={{ display: "none" }}
        disabled={isLoading}
      />

      {validationError && (
        <div
          className="error-alert"
          style={{ padding: "0.75rem 1rem", marginBottom: "1rem" }}
        >
          <IconAlert size={18} />
          <div className="error-details">
            <p>{validationError}</p>
          </div>
        </div>
      )}

      {!previewUrl ? (
        <div
          className={`dropzone-container ${isDragOver ? "is-dragover" : ""}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              fileInputRef.current?.click();
            }
          }}
          aria-label="Zona de carga de captura. Hacé click o arrastrá un archivo aquí."
        >
          <div className="dropzone-icon-wrap">
            <IconUpload size={28} />
          </div>
          <div className="dropzone-instructions">
            <h3>Arrastrá una captura o hacé click para seleccionar</h3>
            <p>Admite JPEG, PNG o WebP (hasta 8 MB)</p>
            <div className="dropzone-paste-badge">
              <span>Podés pegar directamente con</span>
              <kbd>Ctrl + V</kbd>
            </div>
          </div>
        </div>
      ) : (
        <div className="preview-container">
          <div className="preview-image-wrapper">
            <img
              src={previewUrl}
              alt="Vista previa de captura"
              className="preview-image"
            />
          </div>
          <p style={{ fontSize: "0.85rem", color: "var(--color-text-muted)" }}>
            {selectedFile?.name} (
            {(Number(selectedFile?.size) / (1024 * 1024)).toFixed(2)} MB)
          </p>
          <div className="preview-actions">
            <button
              onClick={handleSubmit}
              disabled={isLoading}
              className="btn-primary"
            >
              <IconSearch size={16} />
              <span>
                {isLoading ? "Buscando escena..." : "Identificar Anime"}
              </span>
            </button>
            <button
              onClick={handleClear}
              disabled={isLoading}
              className="btn-secondary"
            >
              Cambiar captura
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
