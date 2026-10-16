import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "../src/App";
import { EmptyState } from "../src/components/EmptyState";
import { ErrorAlert } from "../src/components/ErrorAlert";
import { ResultCard } from "../src/components/ResultCard";
import { ResultList } from "../src/components/ResultList";
import { AnimeResult, ProblemDetails, SearchResponse } from "../src/types/api";

const mockAnimeResult: AnimeResult = {
  id: 1535,
  title: {
    romaji: "Death Note",
    english: "Death Note",
    native: "デスノート",
  },
  cover_image: "https://example.com/dn.jpg",
  synopsis: "Light Yagami finds a notebook that kills anyone whose name is written in it.",
  year: 2006,
  format: "TV",
  is_adult: false,
  confidence_percentage: 0.962,
  confidence_level: "high",
  match_reason: "Cuaderno sobrenatural que causa la muerte.",
  scene_info: {
    episode: 1,
    timestamp_seconds: 320,
    timestamp_formatted: "05:20",
    preview_video_url: "https://example.com/preview.mp4",
  },
};

describe("ResultCard Component", () => {
  it("renderiza correctamente los títulos, badges y porcentaje de confianza", () => {
    render(<ResultCard result={mockAnimeResult} />);

    expect(screen.getByRole("heading", { name: "Death Note" })).toBeInTheDocument();
    expect(screen.getByText(/96.2% de precisión/i)).toBeInTheDocument();
    expect(screen.getByText(/Episodio 1/i)).toBeInTheDocument();

    expect(screen.getByText(/05:20/i)).toBeInTheDocument();
    expect(screen.getByText("2006")).toBeInTheDocument();
    expect(screen.getByText("TV")).toBeInTheDocument();
    expect(screen.getByText(/Cuaderno sobrenatural que causa la muerte/i)).toBeInTheDocument();
  });

  it("protege contenido adulto con blur y botón de revelar", () => {
    const adultAnime: AnimeResult = {
      ...mockAnimeResult,
      is_adult: true,
    };
    render(<ResultCard result={adultAnime} />);

    expect(screen.getByText(/Contenido \+18/i)).toBeInTheDocument();
    const revealBtn = screen.getByRole("button", { name: /revelar/i });
    expect(revealBtn).toBeInTheDocument();

    fireEvent.click(revealBtn);
    expect(screen.queryByText(/Contenido \+18/i)).not.toBeInTheDocument();
  });
});

describe("ResultList Component", () => {
  it("renderiza la barra de estado con modo, tiempo y badge de caché", () => {
    const mockResponse: SearchResponse = {
      query_type: "text",
      search_mode: "llm",
      cached: true,
      filtered_count: 1,
      processing_time_ms: 15,
      results: [mockAnimeResult],
    };

    render(<ResultList response={mockResponse} />);

    expect(screen.getByText(/Análisis de descripción/i)).toBeInTheDocument();
    expect(screen.getByText(/En caché/i)).toBeInTheDocument();
    expect(screen.getByText(/15 ms/i)).toBeInTheDocument();
    expect(screen.getByText(/Se omitieron 1 resultado/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Death Note" })).toBeInTheDocument();
  });
});


describe("ErrorAlert Component", () => {
  it("muestra el código y detalle del problema RFC 7807", () => {
    const problem: ProblemDetails = {
      type: "https://errors.animefinder.com/rate-limit-exceeded",
      title: "Rate Limit Exceeded",
      status: 429,
      detail: "Has superado el límite de 10 peticiones por minuto.",
      code: "RATE_LIMIT_EXCEEDED",
      retry_after_seconds: 30,
    };

    render(<ErrorAlert problem={problem} />);

    expect(screen.getByText(/Rate Limit Exceeded \(429\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Has superado el límite de 10 peticiones/i)).toBeInTheDocument();
    expect(screen.getByText(/Podés reintentar en 30 segundos/i)).toBeInTheDocument();
  });
});

describe("EmptyState Component", () => {
  it("muestra mensaje orientativo cuando no hay resultados", () => {
    render(<EmptyState queryType="image" />);
    expect(screen.getByText(/No encontramos ningún anime que coincida/i)).toBeInTheDocument();
    expect(screen.getByText(/captura nítida directamente de un episodio/i)).toBeInTheDocument();
  });
});

describe("App Mode Switcher", () => {
  it("alterna entre modo imagen y modo descripción al hacer click en las pestañas", () => {
    render(<App />);

    // Por defecto inicia en modo imagen
    expect(screen.getByText(/Arrastrá una captura o hacé click para seleccionar/i)).toBeInTheDocument();

    // Cambiar a modo descripción
    const textTab = screen.getByRole("tab", { name: /Por Descripción/i });
    fireEvent.click(textTab);

    expect(screen.getByPlaceholderText(/Describí lo que recordás/i)).toBeInTheDocument();
    expect(screen.getByText(/0\/500/i)).toBeInTheDocument();

    // Volver a modo imagen
    const imageTab = screen.getByRole("tab", { name: /Por Imagen/i });
    fireEvent.click(imageTab);
    expect(screen.getByText(/Arrastrá una captura o hacé click para seleccionar/i)).toBeInTheDocument();
  });
});
