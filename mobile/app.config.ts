import { ExpoConfig, ConfigContext } from 'expo/config';

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: 'Tech Job Tracker',
  slug: 'tech-job-tracker',
  version: '1.0.0',
  orientation: 'portrait',
  platforms: ['android'],
  scheme: 'techjobtracker',
  android: {
    adaptiveIcon: {
      foregroundImage: './assets/android-icon-foreground.png',
      backgroundColor: '#0a0a0a',
    },
  },
  extra: {
    apiUrl: process.env.API_URL ?? 'http://10.0.2.2:8000',
  },
  plugins: ['expo-router'],
});
