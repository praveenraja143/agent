import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabLayout() {
  return (
    <Tabs screenOptions={{ headerStyle: { backgroundColor: '#0a66c2' }, headerTintColor: '#fff', headerTitleStyle: { fontWeight: 'bold' }, tabBarStyle: { backgroundColor: '#0a66c2' }, tabBarActiveTintColor: '#fff', tabBarInactiveTintColor: '#b0b0b0' }}>
      <Tabs.Screen name="index" options={{ title: 'Home', tabBarIcon: ({ color, size }) => <Ionicons name="home" size={size} color={color} /> }} />
      <Tabs.Screen name="upload" options={{ title: 'Upload Cert', tabBarIcon: ({ color, size }) => <Ionicons name="cloud-upload" size={size} color={color} /> }} />
      <Tabs.Screen name="resume" options={{ title: 'Resume', tabBarIcon: ({ color, size }) => <Ionicons name="document-text" size={size} color={color} /> }} />
      <Tabs.Screen name="history" options={{ title: 'History', tabBarIcon: ({ color, size }) => <Ionicons name="time" size={size} color={color} /> }} />
      <Tabs.Screen name="settings" options={{ title: 'Settings', tabBarIcon: ({ color, size }) => <Ionicons name="settings" size={size} color={color} /> }} />
    </Tabs>
  );
}
