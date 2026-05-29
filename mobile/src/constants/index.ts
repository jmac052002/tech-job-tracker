import Constants from 'expo-constants';

// API base URL comes from app.config.ts extra.apiUrl
// Set API_URL in mobile/.env — never hardcode here
export const API_BASE_URL: string =
  (Constants.expoConfig?.extra?.apiUrl as string) ?? 'http://10.0.2.2:8000';
