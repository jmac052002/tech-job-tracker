import * as SecureStore from 'expo-secure-store';

// Why SecureStore instead of AsyncStorage?
// AsyncStorage is unencrypted — anyone with ADB access can read it.
// SecureStore uses Android Keystore — encrypted at rest, tied to the device.
// Always use SecureStore for tokens, passwords, and sensitive data.

const TOKEN_KEY = 'auth_token';

export const tokenStorage = {
  async save(token: string): Promise<void> {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
  },

  async get(): Promise<string | null> {
    return await SecureStore.getItemAsync(TOKEN_KEY);
  },

  async remove(): Promise<void> {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
  },
};
