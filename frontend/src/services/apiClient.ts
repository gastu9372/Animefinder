import { HealthResponse, ProblemDetails, SearchResponse } from "../types/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  public problem: ProblemDetails;

  constructor(problem: ProblemDetails) {
    super(problem.detail || problem.title);
    this.name = "ApiError";
    this.problem = problem;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let problem: ProblemDetails;
    try {
      problem = await response.json();
    } catch {
      problem = {
        type: "about:blank",
        title: response.statusText || "Error de red",
        status: response.status,
        detail: "No fue posible interpretar la respuesta del servidor.",
        code: "NETWORK_ERROR",
      };
    }
    throw new ApiError(problem);
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  async getHealth(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/health`);
    return handleResponse<HealthResponse>(response);
  },

  async searchByText(description: string, limit = 5): Promise<SearchResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/search/text`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ description, limit }),
    });
    return handleResponse<SearchResponse>(response);
  },

  async searchByImage(file: File): Promise<SearchResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/api/v1/search/image`, {
      method: "POST",
      body: formData,
    });
    return handleResponse<SearchResponse>(response);
  },
};
