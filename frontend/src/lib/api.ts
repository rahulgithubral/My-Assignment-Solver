import axios, { AxiosResponse } from 'axios';
import { Assignment, Plan, FileUploadResponse, ChatMessage, ExecutionResult } from '../types';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API functions
export const api = {
  // Assignment endpoints
  getAssignments: async (): Promise<Assignment[]> => {
    const response: AxiosResponse<Assignment[]> = await apiClient.get('/api/assignments/');
    return response.data;
  },

  getAssignment: async (id: string): Promise<Assignment> => {
    const response: AxiosResponse<Assignment> = await apiClient.get(`/api/assignments/${id}`);
    return response.data;
  },

  uploadAssignment: async (file: File, title?: string, description?: string): Promise<FileUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    if (title) formData.append('title', title);
    if (description) formData.append('description', description);

    const response: AxiosResponse<FileUploadResponse> = await apiClient.post(
      '/api/assignments/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  generatePlan: async (assignmentId: string): Promise<{ message: string; assignment_id: string; status: string }> => {
    const response = await apiClient.post(`/api/assignments/${assignmentId}/plan`);
    return response.data;
  },

  updateAssignment: async (id: string, data: Partial<Assignment>): Promise<Assignment> => {
    const response: AxiosResponse<Assignment> = await apiClient.put(`/api/assignments/${id}`, data);
    return response.data;
  },

  deleteAssignment: async (id: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/api/assignments/${id}`);
    return response.data;
  },

  // Plan endpoints
  getPlans: async (assignmentId?: string): Promise<Plan[]> => {
    const params = assignmentId ? { assignment_id: assignmentId } : {};
    const response: AxiosResponse<Plan[]> = await apiClient.get('/api/plans/', { params });
    return response.data;
  },

  getPlan: async (id: string): Promise<Plan> => {
    const response: AxiosResponse<Plan> = await apiClient.get(`/api/plans/${id}`);
    return response.data;
  },

  createPlan: async (data: { assignment_id: string; name: string; description?: string }): Promise<Plan> => {
    const response: AxiosResponse<Plan> = await apiClient.post('/api/plans/', data);
    return response.data;
  },

  updatePlan: async (id: string, data: Partial<Plan>): Promise<Plan> => {
    const response: AxiosResponse<Plan> = await apiClient.put(`/api/plans/${id}`, data);
    return response.data;
  },

  executePlan: async (planId: string, dryRun: boolean = false): Promise<ExecutionResult> => {
    const response = await apiClient.post(`/api/plans/${planId}/execute`, {
      plan_id: planId,
      dry_run: dryRun,
      parallel_execution: true,
      max_parallel_tasks: 3,
    });
    return response.data;
  },

  getPlanStatus: async (planId: string): Promise<{
    plan_id: string;
    plan_status: string;
    execution_started_at?: string;
    execution_completed_at?: string;
    task_statuses: Record<string, any>;
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
  }> => {
    const response = await apiClient.get(`/api/plans/${planId}/status`);
    return response.data;
  },

  deletePlan: async (id: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/api/plans/${id}`);
    return response.data;
  },

  // Chat endpoints
  sendMessage: async (message: string, assignmentId?: string): Promise<ChatMessage> => {
    const response: AxiosResponse<ChatMessage> = await apiClient.post('/api/chat/', {
      message,
      assignment_id: assignmentId,
    });
    return response.data;
  },

  getChatHistory: async (assignmentId?: string): Promise<ChatMessage[]> => {
    const params = assignmentId ? { assignment_id: assignmentId } : {};
    const response: AxiosResponse<ChatMessage[]> = await apiClient.get('/api/chat/', { params });
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ status: string; service: string; version: string }> => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Utility functions
  downloadFile: async (filePath: string): Promise<Blob> => {
    const response = await apiClient.get(`/api/files/download?path=${encodeURIComponent(filePath)}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Search endpoints
  searchDocuments: async (query: string, k: number = 5): Promise<any[]> => {
    const response = await apiClient.post('/api/search/', {
      query,
      k,
    });
    return response.data;
  },
};

// Error handling utilities
export const handleApiError = (error: any): string => {
  if (error.response?.data?.error) {
    return error.response.data.error;
  }
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

// File upload utilities
export const validateFile = (file: File): { valid: boolean; error?: string } => {
  const maxSize = 10 * 1024 * 1024; // 10MB
  const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];

  if (file.size > maxSize) {
    return { valid: false, error: 'File size must be less than 10MB' };
  }

  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: 'Only PDF, TXT, and DOCX files are allowed' };
  }

  return { valid: true };
};

// Export the axios instance for direct use if needed
export { apiClient };
