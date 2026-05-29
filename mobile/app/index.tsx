import { Redirect } from 'expo-router';

// App entry — immediately redirect to auth check
export default function Index() {
  return <Redirect href="/(auth)/login" />;
}
