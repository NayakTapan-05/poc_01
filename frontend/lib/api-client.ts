import axios from 'axios';

// API base URL - set via NEXT_PUBLIC_API_BASE_URL environment variable
// For local development: defaults to http://localhost:8000
// For Azure deployment: set to your backend App Service URL
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to handle FormData - let axios set Content-Type automatically
apiClient.interceptors.request.use((config) => {
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }
  return config;
});

export const api = {
  getBrands: () => apiClient.get('/api/brands'),
  getBrandSnippet: (brand: string) => apiClient.get(`/api/brands/${brand}/snippet`),
  uploadBrandDocument: (file: File, brand?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (brand) formData.append('brand', brand);
    return apiClient.post('/api/brands/upload', formData);
  },
  ingestBrandDocument: (filePath: string, brand?: string) => {
    const formData = new FormData();
    formData.append('file_path', filePath);
    if (brand) formData.append('brand', brand);
    return apiClient.post('/api/brands/ingest', formData);
  },

  previewPrompt: (data: any) => apiClient.post('/api/prompt/preview', data),
  enhancePrompt: (data: any) => apiClient.post('/api/prompt/enhance', data),
  getTemplates: (engineType: string = 'image') => 
    apiClient.get('/api/prompt/templates', { params: { engine_type: engineType } }),
  getPresets: () => apiClient.get('/api/prompt/presets'),

  generateImage: (data: any) => apiClient.post('/api/image/generate', data),

  generateVideo: (data: any) => apiClient.post('/api/video/generate', data),
  getVideoJobStatus: (jobId: string) => apiClient.get(`/api/video/job/${jobId}`),

  chat: (messages: any[], brand?: string, sessionId?: string) => 
    apiClient.post('/api/chat', { messages, brand, session_id: sessionId }),
  chatLegacy: (query: string, brand?: string) => 
    apiClient.post('/api/chat', { query, brand }),
  
  createChatSession: (title?: string, brand?: string) =>
    apiClient.post('/api/chat/sessions', { title, brand }),
  listChatSessions: () =>
    apiClient.get('/api/chat/sessions'),
  getChatSession: (sessionId: string) =>
    apiClient.get(`/api/chat/sessions/${sessionId}`),
  sendSessionMessage: (sessionId: string, content: string, brand?: string, modelId?: string) =>
    apiClient.post(`/api/chat/sessions/${sessionId}/messages`, { content, brand, model_id: modelId }),
  updateSession: (sessionId: string, data: { title?: string; brand?: string }) =>
    apiClient.patch(`/api/chat/sessions/${sessionId}`, data),
  deleteSession: (sessionId: string) =>
    apiClient.delete(`/api/chat/sessions/${sessionId}`),

  getMediaLibrary: (limit: number = 100, brandId?: string, type?: string, isFinal?: boolean) => 
    apiClient.get('/api/media', { params: { limit, brand_id: brandId, type, is_final: isFinal } }),
  getMediaItem: (itemId: string) => apiClient.get(`/api/media/${itemId}`),
  downloadMediaItem: (itemId: string) => apiClient.get(`/api/media/${itemId}/download`),
  finalizeAsset: (assetId: string) => apiClient.post(`/api/assets/${assetId}/finalize`),

  clearVectorStore: () => apiClient.post('/api/settings/clear-vector-store'),
  clearOutputs: () => apiClient.post('/api/settings/clear-outputs'),
  getModelRegistry: () => apiClient.get('/api/models/registry'),
  getModels: (type?: string) => apiClient.get('/api/models', { params: type ? { type } : {} }),
};
