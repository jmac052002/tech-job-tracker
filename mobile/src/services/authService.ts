import apiClient from './apiClient';
import { tokenStorage } from './tokenStorage';
import { User, AuthToken, RegisterResponse } from '../types';

// Why a services layer?
// Components should not call fetch/axios directly.
// Services are the single source of truth for how data moves between app and API.
// Makes it easy to swap implementations, mock in tests, and find all API calls.

export const authService = {
  async register(email: string, password: string): Promise<RegisterResponse> {
    const response = await apiClient.post<RegisterResponse>('/auth/register', {
      email,
      password,
    });
    // Save token immediately after registration
    await tokenStorage.save(response.data.token.access_token);
    return response.data;
  },

  async login(email: string, password: string): Promise<AuthToken> {
    // Backend uses OAuth2PasswordRequestForm — requires form-encoded data, not JSON
    const formData = new URLSearchParams();
    formData.append('username', email); // OAuth2 spec uses 'username' field
    formData.append('password', password);

    const response = await apiClient.post<AuthToken>('/auth/login', formData.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    await tokenStorage.save(response.data.access_token);
    return response.data;
  },

  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  async logout(): Promise<void> {
    await tokenStorage.remove();
  },
};
