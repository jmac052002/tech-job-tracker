import { Stack, Redirect } from 'expo-router';
import { useAuth } from '../../src/context/AuthContext';
import { ActivityIndicator, View } from 'react-native';

// Auth stack layout — if user is already logged in, redirect to app
export default function AuthLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0a0a0a' }}>
        <ActivityIndicator color="#4f9eff" />
      </View>
    );
  }

  if (isAuthenticated) {
    return <Redirect href="/(app)/jobs" />;
  }

  return <Stack screenOptions={{ headerShown: false }} />;
}
