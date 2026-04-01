import axios from 'axios';

// Use relative URLs in development to leverage Vite's proxy
// In production, set VITE_API_URL to your actual API URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Upload files
export const uploadFiles = async (files) => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });

  const response = await api.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

// Get all files
export const getFiles = async (skip = 0, limit = 100, status = null) => {
  const params = { skip, limit };
  if (status) {
    params.status = status;
  }

  const response = await api.get('/api/files', { params });
  return response.data;
};

// Get single file
export const getFile = async (fileId) => {
  const response = await api.get(`/api/files/${fileId}`);
  return response.data;
};

// Delete file
export const deleteFile = async (fileId) => {
  const response = await api.delete(`/api/files/${fileId}`);
  return response.data;
};

// Search
export const searchFiles = async (query, limit = 20) => {
  const response = await api.post('/api/search', null, {
    params: { query, limit }
  });
  return response.data;
};

// Get stats
export const getStats = async () => {
  const response = await api.get('/api/stats');
  return response.data;
};

// Download file
export const getDownloadUrl = (fileId) => {
  return `${API_BASE_URL}/api/download/${fileId}`;
};

// Get thumbnail URL - works with proxy setup
export const getThumbnailUrl = (thumbnailPath) => {
  if (!thumbnailPath) return null;
  // Remove leading slash if present to work with both proxy and direct URLs
  const cleanPath = thumbnailPath.startsWith('/') ? thumbnailPath.slice(1) : thumbnailPath;
  return API_BASE_URL ? `${API_BASE_URL}/${cleanPath}` : `/${cleanPath}`;
};

// Get file URL - works with proxy setup
export const getFileUrl = (filePath) => {
  if (!filePath) return null;
  // Remove leading slash if present to work with both proxy and direct URLs
  const cleanPath = filePath.startsWith('/') ? filePath.slice(1) : filePath;
  return API_BASE_URL ? `${API_BASE_URL}/${cleanPath}` : `/${cleanPath}`;
};

// Admin: Get all embeddings and extracted text
export const getAllEmbeddings = async () => {
  const response = await api.get('/api/admin/embeddings');
  return response.data;
};

// Admin: Get detailed embedding info for a specific file
export const getEmbeddingDetails = async (fileId) => {
  const response = await api.get(`/api/admin/embedding/${fileId}`);
  return response.data;
};

// Admin: Test search with detailed ranking
export const testSearchRanking = async (query, limit = 20) => {
  const response = await api.post('/api/admin/test-search', null, {
    params: { query, limit }
  });
  return response.data;
};

// Admin: Batch reprocess all files for improved OCR/embedding accuracy
export const batchReprocessAllFiles = async () => {
  const response = await api.post('/api/admin/reprocess-all');
  return response.data;
};

// Admin: Get status of batch reprocessing
export const getReprocessStatus = async () => {
  const response = await api.get('/api/admin/reprocess-status');
  return response.data;
};

// Admin: Reprocess a single file
export const reprocessSingleFile = async (fileId) => {
  const response = await api.post(`/api/admin/reprocess/${fileId}`);
  return response.data;
};

export default api;
