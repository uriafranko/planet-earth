// Authentication related types
export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'admin' | 'user' | 'viewer';
}

export interface Stats {
  schemaCount: number;
  endpointCount: number;
  searchCount: number;
  documentCount: number;
  chunksCount: number;
}

// OpenAPI schema related types
export interface Schema {
  id: string;
  title: string;
  version: string;
  checksum: string;
  created_at: string;
}

export interface Endpoint {
  id: string;
  schema_id: string;
  path: string;
  method: string;
  operation_id: string | null;
  summary: string | null;
  description: string | null;
  tags: string | null;
  created_at: string;
  deleted_at: string | null;
}

export interface EndpointSearchResult extends Omit<Endpoint, 'created_at' | 'deleted_at'> {
  score: number;
  schema_title: string;
  schema_version: string;
}

export interface SearchQuery {
  q: string;
  top_k?: number;
  filter_schema_id?: string | null;
  filter_method?: string | null;
  include_deprecated?: boolean;
}

// Pagination related types
export interface PaginationParams {
  offset?: number;
  limit?: number;
}

// API related types
export interface ApiError {
  status: number;
  message: string;
  details?: any;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
}

// Document related types
export interface Document {
  id: string;
  title: string;
  created_at: string;
  original_filename?: string | null;
  file_type: string;
}

export interface DocumentDetail extends Document {
  text?: string | null;
}

export interface DocumentSearchRequest {
  query: string;
  top_k?: number;
  created_at?: string | null;
}

export interface DocumentSearchResult {
  document_id: string;
  chunk_id: string;
  title: string;
  chunk_text: string;
  document_text?: string | null;
  score: number;
  created_at: string;
}
