import React, { useEffect, useState } from "react";
import { ProblemDetails } from "../types/api";
import { IconAlert, IconClock } from "./Icons";

interface ErrorAlertProps {
  problem: ProblemDetails;
  onDismiss?: () => void;
  onRetry?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  problem,
  onDismiss,
  onRetry,
}) => {
  const [countdown, setCountdown] = useState<number | null>(
    problem.retry_after_seconds ?? null,
  );

  useEffect(() => {
    if (countdown === null || countdown <= 0) return;
    const timer = setInterval(() => {
      setCountdown((prev) => (prev && prev > 1 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  return (
    <div className="error-alert" role="alert">
      <div style={{ color: "var(--color-danger)", flexShrink: 0 }}>
        <IconAlert size={20} />
      </div>
      <div className="error-details" style={{ flex: 1 }}>
        <h4>
          {problem.title || "Ocurrió un error"}{" "}
          {problem.status ? `(${problem.status})` : ""}
        </h4>
        <p>{problem.detail}</p>

        {countdown !== null && countdown > 0 && (
          <span
            className="retry-countdown"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.35rem",
            }}
          >
            <IconClock size={13} />
            <span>
              Podés reintentar en {countdown} segundo{countdown > 1 ? "s" : ""}
            </span>
          </span>
        )}

        <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.75rem" }}>
          {onRetry && (
            <button
              onClick={onRetry}
              disabled={countdown !== null && countdown > 0}
              className="btn-secondary"
              style={{ padding: "0.4rem 0.9rem", fontSize: "0.8rem" }}
            >
              Reintentar
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="btn-secondary"
              style={{
                padding: "0.4rem 0.9rem",
                fontSize: "0.8rem",
                background: "transparent",
              }}
            >
              Cerrar
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
