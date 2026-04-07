import { Redirect } from 'expo-router';
import { useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function Index() {
  const [isReady, setIsReady] = useState(false);
  const [isConfigured, setIsConfigured] = useState(false);

  useEffect(() => {
    checkSetup();
  }, []);

  const checkSetup = async () => {
    try {
      const email = await AsyncStorage.getItem('LINKEDIN_EMAIL');
      const apiKey = await AsyncStorage.getItem('OPENROUTER_API_KEY');
      setIsConfigured(!!email && !!apiKey);
    } catch (error) {
      console.error(error);
    } finally {
      setIsReady(true);
    }
  };

  if (!isReady) return null;
  if (!isConfigured) return <Redirect href="/setup" />;
  return <Redirect href="/(tabs)" />;
}
