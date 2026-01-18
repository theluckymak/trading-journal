/**
 * API client with authentication support.
 */
import axios, { AxiosInstance, AxiosError } from 'axios';

// Use backend service name for server-side calls, localhost for browser
const API_URL = typeof window === 'undefined' 
  ? (process.env.NEXT_PUBLIC_API_URL_SERVER || 'http://backend:8000')
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

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
      timeout: 60000, // 60 seconds timeout
    });

    // Load tokens from localStorage
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('accessToken');
      this.refreshToken = localStorage.getItem('refreshToken');
    }

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        // Always check localStorage for latest token
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem('accessToken');
          if (token) {
            this.accessToken = token;
            config.headers.Authorization = `Bearer ${token}`;
          }
        } else if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error: any) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response: any) => response,
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
    // Use native fetch instead of axios due to network issues
    const response = await fetch(`${API_URL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw { response: { data: errorData, status: response.status } };
    }

    return await response.json();
  }

  async login(email: string, password: string) {
    // Use native fetch instead of axios due to network issues
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        email,
        password,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw { response: { data: errorData, status: response.status } };
    }

    const data = await response.json();
    const { access_token, refresh_token } = data;
    this.setTokens(access_token, refresh_token);
    
    return data;
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
    // ative fetch instead of axios cause network issues
    const accessToken = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : this.accessToken;
    
    if (!accessToken) {
      throw { response: { status: 401, data: { detail: 'Not authenticated' } } };
    }

    const response = await fetch(`${API_URL}/api/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw { response: { data: errorData, status: response.status } };
    }

    return await response.json();
  }

  async updateProfile(data: { full_name?: string; email?: string }) {
    console.log('[updateProfile] Starting with data:', data);
    
    // Use native fetch instead of axios due to network issues
    const accessToken = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : this.accessToken;
    
    console.log('[updateProfile] Access token:', accessToken ? `${accessToken.substring(0, 20)}...` : 'NONE');
    
    if (!accessToken) {
      throw { response: { status: 401, data: { detail: 'Not authenticated' } } };
    }

    const url = `${API_URL}/api/auth/me`;
    console.log('[updateProfile] URL:', url);
    console.log('[updateProfile] Request body:', JSON.stringify(data));

    try {
      const response = await fetch(url, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      console.log('[updateProfile] Response status:', response.status);
      console.log('[updateProfile] Response ok:', response.ok);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('[updateProfile] Error response:', errorData);
        throw { response: { data: errorData, status: response.status } };
      }

      const result = await response.json();
      console.log('[updateProfile] Success result:', result);
      return result;
    } catch (error: any) {
      console.error('[updateProfile] Fetch error:', error);
      throw error;
    }
  }

  async oauthLogin(provider: string, accessToken: string) {
    const response = await this.client.post(`/auth/oauth/${provider}/token`, {
      access_token: accessToken,
    });
    
    const { access_token, refresh_token } = response.data;
    this.setTokens(access_token, refresh_token);
    
    return response.data;
  }

  // Trade endpoints
  async createTrade(data: any) {
    const response = await this.client.post('/trades', data);
    return response.data;
  }

  async getTrade(tradeId: number) {
    const response = await this.client.get(`/trades/${tradeId}`);
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
  async getJournalEntries() {
    const response = await this.client.get('/journal/entries');
    return response.data;
  }

  async getJournalEntryById(entryId: number) {
    const response = await this.client.get(`/journal/entries/${entryId}`);
    return response.data;
  }

  async createJournalEntry(data: any) {
    const response = await this.client.post('/journal/entries', data);
    return response.data;
  }

  async updateJournalEntry(entryId: number, data: any) {
    const response = await this.client.patch(`/journal/entries/${entryId}`, data);
    return response.data;
  }

  async deleteJournalEntry(entryId: number) {
    const response = await this.client.delete(`/journal/entries/${entryId}`);
    return response.data;
  }

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

  // =====================================
  // Chat Methods
  // =====================================

  /**
   * Send a chat message
   */
  async sendChatMessage(message: string, conversationUserId?: number) {
    console.log('[sendChatMessage] Sending message');
    const accessToken = localStorage.getItem('accessToken');
    
    const body: any = { message };
    if (conversationUserId) {
      body.conversation_user_id = conversationUserId;
    }
    
    const response = await fetch(`${API_URL}/api/chat/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      credentials: 'include',
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('[sendChatMessage] Error:', errorData);
      throw { response: { data: errorData, status: response.status } };
    }

    return await response.json();
  }

  /**
   * Get chat messages
   */
  async getChatMessages(conversationUserId?: number, limit: number = 100, offset: number = 0) {
    console.log('[getChatMessages] Fetching messages');
    const accessToken = localStorage.getItem('accessToken');
    
    let url = `${API_URL}/api/chat/messages?limit=${limit}&offset=${offset}`;
    if (conversationUserId) {
      url += `&conversation_user_id=${conversationUserId}`;
    }
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('[getChatMessages] Error:', errorData);
      throw { response: { data: errorData, status: response.status } };
    }

    return await response.json();
  }

  /**
   * Delete a chat message
   */
  async deleteChatMessage(messageId: number) {
    console.log('[deleteChatMessage] Deleting message:', messageId);
    const accessToken = localStorage.getItem('accessToken');
    
    const response = await fetch(`${API_URL}/api/chat/messages/${messageId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('[deleteChatMessage] Error:', errorData);
      throw { response: { data: errorData, status: response.status } };
    }

    return true;
  }

  /**
   * Get list of users with messages (admin only)
   */
  async getUsersWithMessages() {
    console.log('[getUsersWithMessages] Fetching users');
    const accessToken = localStorage.getItem('accessToken');
    
    const response = await fetch(`${API_URL}/api/chat/admin/users`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('[getUsersWithMessages] Error:', errorData);
      throw { response: { data: errorData, status: response.status } };
    }

    return await response.json();
  }

  /**
   * Get admin statistics
   */
  async getAdminStats() {
    console.log('[getAdminStats] Fetching admin stats');
    const accessToken = localStorage.getItem('accessToken');
    
    const response = await fetch(`${API_URL}/api/chat/admin/stats`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('[getAdminStats] Error:', errorData);
      throw { response: { data: errorData, status: response.status } };
    }

    return await response.json();
  }
}

export const apiClient = new ApiClient();
