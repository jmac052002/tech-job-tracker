import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL } from '../constants';
import { tokenStorage } from './tokenStorage';

// Why a single axios instance?
// - One place to set baseURL, headers, timeouts
// - Request interceptor attaches the JWT automatically — no component needs to know about tokens
// - Response interceptor can handle 401s globally (force logout when token expires)

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — attach JWT token to every outgoing request
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig): Promise<InternalAxiosRequestConfig> => {
    const token = await tokenStorage.get();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: unknown) => Promise.reject(error)
);

export default apiClient;
