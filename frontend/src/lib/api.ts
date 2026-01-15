/**
 * API client with authentication support.
 */
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });

    // Load tokens from localStorage
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('accessToken');
      this.refreshToken = localStorage.getItem('refreshToken');
    }

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest: any = error.config;

        // If 401 and we have a refresh token, try to refresh
        if (error.response?.status === 401 && !originalRequest._retry && this.refreshToken) {
          originalRequest._retry = true;

          try {
            const response = await axios.post(
              `${API_URL}/api/auth/refresh`,
              { refresh_token: this.refreshToken }
            );

            const { access_token } = response.data;
            this.setAccessToken(access_token);

            // Retry original request
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, logout
            this.logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  setAccessToken(token: string) {
    this.accessToken = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('accessToken', token);
    }
  }

  setRefreshToken(token: string) {
    this.refreshToken = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('refreshToken', token);
    }
  }

  setTokens(accessToken: string, refreshToken: string) {
    this.setAccessToken(accessToken);
    this.setRefreshToken(refreshToken);
  }

  logout() {
    this.accessToken = null;
    this.refreshToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  // Auth endpoints
  async register(email: string, password: string, fullName?: string) {
    const response = await this.client.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', {
      email,
      password,
    });
    
    const { access_token, refresh_token } = response.data;
    this.setTokens(access_token, refresh_token);
    
    return response.data;
  }

  async logoutUser() {
    if (this.refreshToken) {
      try {
        await this.client.post('/auth/logout', {
          refresh_token: this.refreshToken,
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    this.logout();
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // MT5 endpoints
  async addMT5Account(data: {
    account_number: string;
    password: string;
    broker_name: string;
    server_name: string;
    account_name?: string;
  }) {
    const response = await this.client.post('/mt5/accounts', data);
    return response.data;
  }

  async getMT5Accounts() {
    const response = await this.client.get('/mt5/accounts');
    return response.data;
  }

  async syncMT5Account(accountId: number) {
    const response = await this.client.post(`/mt5/accounts/${accountId}/sync`);
    return response.data;
  }

  async deleteMT5Account(accountId: number) {
    const response = await this.client.delete(`/mt5/accounts/${accountId}`);
    return response.data;
  }

  // Trade endpoints
  async createTrade(data: any) {
    const response = await this.client.post('/trades', data);
    return response.data;
  }

  async getTrades(params?: {
    symbol?: string;
    start_date?: string;
    end_date?: string;
    is_closed?: boolean;
    limit?: number;
    offset?: number;
  }) {
    const response = await this.client.get('/trades', { params });
    return response.data;
  }

  async getTrade(tradeId: number) {
    const response = await this.client.get(`/trades/${tradeId}`);
    return response.data;
  }

  async updateTrade(tradeId: number, data: any) {
    const response = await this.client.patch(`/trades/${tradeId}`, data);
    return response.data;
  }

  async deleteTrade(tradeId: number) {
    const response = await this.client.delete(`/trades/${tradeId}`);
    return response.data;
  }

  async getAnalytics(params?: { start_date?: string; end_date?: string }) {
    const response = await this.client.get('/trades/analytics/summary', { params });
    return response.data;
  }

  // Journal endpoints
  async createOrUpdateJournalEntry(tradeId: number, data: any) {
    const response = await this.client.post(`/journal/entries/${tradeId}`, data);
    return response.data;
  }

  async getJournalEntry(tradeId: number) {
    const response = await this.client.get(`/journal/entries/${tradeId}`);
    return response.data;
  }

  async createTag(data: { name: string; color?: string; category?: string }) {
    const response = await this.client.post('/journal/tags', data);
    return response.data;
  }

  async getTags() {
    const response = await this.client.get('/journal/tags');
    return response.data;
  }

  async addTagToTrade(tradeId: number, tagId: number) {
    const response = await this.client.post(`/journal/trades/${tradeId}/tags/${tagId}`);
    return response.data;
  }

  async removeTagFromTrade(tradeId: number, tagId: number) {
    const response = await this.client.delete(`/journal/trades/${tradeId}/tags/${tagId}`);
    return response.data;
  }
}

export const apiClient = new ApiClient();
