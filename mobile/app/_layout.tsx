import { Stack } from 'expo-router';
import { AuthProvider } from '../src/context/AuthContext';

// Root layout — wraps the entire app with AuthProvider
// Every screen in the app can now call useAuth()
export default function RootLayout() {
  return (
    <AuthProvider>
      <Stack screenOptions={{ headerShown: false }} />
    </AuthProvider>
  );
}
