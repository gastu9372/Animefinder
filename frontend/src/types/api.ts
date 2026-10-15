export type QueryType = "image" | "text";
export type SearchMode = "trace.moe" | "llm" | "fallback";
export type ConfidenceLevel = "high" | "medium" | "low";

export interface AnimeTitle {
  romaji: string;
  english: string | null;
  native: string | null;
}

export interface SceneInfo {
  episode: number | null;
  timestamp_seconds: number | null;
  timestamp_formatted: string | null;
  preview_video_url: string | null;
}

export interface AnimeResult {
  id: number;
  title: AnimeTitle;
  cover_image: string;
  synopsis: string;
  year: number | null;
  format: string | null;
  is_adult: boolean;
  confidence_percentage: number | null;
  confidence_level: ConfidenceLevel;
  match_reason: string | null;
  scene_info: SceneInfo | null;
}

export interface SearchResponse {
  query_type: QueryType;
  search_mode: SearchMode;
  cached: boolean;
  filtered_count: number;
  processing_time_ms: number;
  results: AnimeResult[];
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  code: string;
  retry_after_seconds?: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}
