
// Authentication related types
export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'admin' | 'user' | 'viewer';
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
