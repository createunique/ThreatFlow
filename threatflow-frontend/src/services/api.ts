/**
 * API Service for ThreatFlow Middleware
 * Connects to FastAPI backend on port 8030
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  AnalyzerInfo,
  ExecuteWorkflowResponse,
  JobStatusResponse,
  CustomNode,
  Edge,
} from '../types/workflow';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8030';

// Create axios instance with default config
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor (for debugging)
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Response interceptor (for error handling)
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.status} ${response.config.url}`);
    return response;
  },
  (error: AxiosError) => {
    console.error('[API Response Error]', error.message);
    if (error.response) {
      console.error('Error Data:', error.response.data);
    }
    return Promise.reject(error);
  }
);

// ============= API Methods =============

export const api = {
  /**
   * Health check endpoints
   */
  healthCheck: async (): Promise<{ status: string; service: string }> => {
    const response = await apiClient.get('/health/');
    return response.data;
  },

  intelowlHealth: async (): Promise<{ status: string; analyzers_available: number }> => {
    const response = await apiClient.get('/health/intelowl');
    return response.data;
  },

  /**
   * Get available analyzers from IntelOwl
   * @param type - Filter by 'file' or 'observable'
   */
  getAnalyzers: async (type?: 'file' | 'observable'): Promise<AnalyzerInfo[]> => {
    const params = type ? { type } : {};
    const response = await apiClient.get<AnalyzerInfo[]>('/api/analyzers', { params });
    return response.data;
  },

  /**
   * Execute workflow: submit file and workflow JSON
   * @param nodes - Workflow nodes
   * @param edges - Workflow edges
   * @param file - File to analyze
   */
  executeWorkflow: async (
    nodes: CustomNode[],
    edges: Edge[],
    file: File
  ): Promise<ExecuteWorkflowResponse> => {
    const formData = new FormData();

    // Serialize workflow to JSON
    const workflowJson = JSON.stringify({ nodes, edges });
    formData.append('workflow_json', workflowJson);

    // Attach file
    formData.append('file', file);

    const response = await apiClient.post<ExecuteWorkflowResponse>(
      '/api/execute',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  },

  /**
   * Get job status from IntelOwl
   * @param jobId - IntelOwl job identifier
   */
  getJobStatus: async (jobId: number): Promise<JobStatusResponse> => {
    const response = await apiClient.get<JobStatusResponse>(`/api/status/${jobId}`);
    return response.data;
  },

  /**
   * Poll job status until completion
   * @param jobId - Job identifier
   * @param onUpdate - Callback for status updates
   * @param maxAttempts - Maximum polling attempts
   */
  pollJobStatus: async (
    jobId: number,
    onUpdate?: (status: JobStatusResponse) => void,
    maxAttempts: number = 60
  ): Promise<JobStatusResponse> => {
    const pollInterval = parseInt(process.env.REACT_APP_POLL_INTERVAL || '5000');
    let attempts = 0;

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          attempts++;
          const status = await api.getJobStatus(jobId);

          // Call update callback
          if (onUpdate) {
            onUpdate(status);
          }

          // Check if complete
          if (status.results) {
            resolve(status);
            return;
          }

          // Check if timeout
          if (attempts >= maxAttempts) {
            reject(new Error('Job polling timeout'));
            return;
          }

          // Continue polling
          setTimeout(poll, pollInterval);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  },
};

export default api;
