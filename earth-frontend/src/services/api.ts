import {
  ApiResponse,
  Endpoint,
  EndpointSearchResult,
  PaginationParams,
  Schema,
  SearchQuery,
} from '@/types/models';

// Base URL for the API
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'; // Fallback to localhost if env var not set

// HTTP methods
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

// Generic fetch function
const fetchApi = async <T>(
  endpoint: string,
  method: HttpMethod = 'GET',
  body?: any,
  isFormData = false
): Promise<ApiResponse<T>> => {
  try {
    const headers: HeadersInit = {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    };

    const config: RequestInit = {
      method,
      headers,
      body: isFormData ? body : body ? JSON.stringify(body) : undefined,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    // For DELETE with 204 No Content
    if (response.status === 204) {
      return { data: undefined };
    }

    const data = await response.json();

    if (!response.ok) {
      return {
        error: {
          status: response.status,
          message: data.message || 'An error occurred',
          details: data.detail,
        },
      };
    }

    return { data };
  } catch (error) {
    console.error('API error:', error);
    return {
      error: {
        status: 500,
        message: 'Network error or server unavailable',
      },
    };
  }
};

// Schemas API
export const schemasApi = {
  // Get all schemas
  getSchemas: async (params?: PaginationParams): Promise<ApiResponse<Schema[]>> => {
    const queryParams = new URLSearchParams();
    if (params?.offset !== undefined) queryParams.append('offset', params.offset.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());

    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';

    // Use real API instead of mock data
    return fetchApi<Schema[]>(`/v1/schemas${query}`);
  },

  // Get a specific schema by ID
  getSchema: async (schemaId: string): Promise<ApiResponse<Schema>> => {
    // Use real API instead of mock data
    return fetchApi<Schema>(`/v1/schemas/${schemaId}`);
  },

  // Upload a new schema
  uploadSchema: async (file: File): Promise<ApiResponse<Schema>> => {
    const formData = new FormData();
    formData.append('file', file);

    // Use real API instead of mock data
    return fetchApi<Schema>('/v1/schemas', 'POST', formData, true);
  },

  // Delete a schema
  deleteSchema: async (schemaId: string): Promise<ApiResponse<void>> => {
    // Use real API instead of mock data
    return fetchApi<void>(`/v1/schemas/${schemaId}`, 'DELETE');
  },
};

// Endpoints API
export const endpointsApi = {
  // Get all endpoints for a schema
  getEndpoints: async (
    schemaId: string,
    includeDeleted: boolean = false,
    params?: PaginationParams
  ): Promise<ApiResponse<Endpoint[]>> => {
    const queryParams = new URLSearchParams();
    queryParams.append('include_deleted', includeDeleted.toString());
    if (params?.offset !== undefined) queryParams.append('offset', params.offset.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());

    const query = `?${queryParams.toString()}`;

    // Use real API instead of mock data
    return fetchApi<Endpoint[]>(`/v1/management/schemas/${schemaId}/endpoints${query}`);
  },
};

// Search API
export const searchApi = {
  // Semantic search for endpoints
  searchEndpoints: async (query: SearchQuery): Promise<ApiResponse<EndpointSearchResult[]>> => {
    // Use real API instead of mock data
    return fetchApi<EndpointSearchResult[]>('/v1/search', 'POST', query);
  },
};

// Management API
export const managementApi = {
  getStatus: async (): Promise<ApiResponse<Stats>> => {
    return fetchApi('/v1/management/stats');
  },
  // Reindex vector store
  reindexVectorStore: async (schemaId?: string): Promise<ApiResponse<void>> => {
    const queryParams = new URLSearchParams();
    if (schemaId) queryParams.append('schema_id', schemaId);

    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';

    // Use real API instead of mock data
    return fetchApi<void>(`/v1/management/reindex${query}`, 'POST');
  },

  // Reindex a specific endpoint
  reindexEndpoint: async (endpointId: string): Promise<ApiResponse<void>> => {
    // Use real API instead of mock data
    return fetchApi<void>(`/v1/management/endpoints/${endpointId}/reindex`, 'POST');
  },
};

// Documents API
import type {
  Document,
  DocumentDetail,
  DocumentSearchRequest,
  DocumentSearchResult,
  Stats,
} from '@/types/models';

export const documentsApi = {
  listDocuments: async (): Promise<ApiResponse<Document[]>> =>
    fetchApi<Document[]>('/v1/documents'),

  uploadDocument: async (file: File, title: string): Promise<ApiResponse<Document>> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    return fetchApi<Document>('/v1/documents/upload', 'POST', formData, true);
  },

  getDocument: async (documentId: string): Promise<ApiResponse<DocumentDetail>> =>
    fetchApi<DocumentDetail>(`/v1/documents/${documentId}`),

  deleteDocument: async (documentId: string): Promise<ApiResponse<void>> =>
    fetchApi<void>(`/v1/documents/${documentId}`, 'DELETE'),

  searchDocuments: async (
    query: DocumentSearchRequest
  ): Promise<ApiResponse<DocumentSearchResult[]>> =>
    fetchApi<DocumentSearchResult[]>('/v1/search/documents/search', 'POST', query),
};

// Audit API
export type AuditLogByDay = {
  day: string;
  count: number;
};

export const auditApi = {
  // Get audit logs grouped by day
  getAuditLogsByDay: async (): Promise<ApiResponse<AuditLogByDay[]>> => {
    return fetchApi<AuditLogByDay[]>('/v1/audit/by-day');
  },
};
