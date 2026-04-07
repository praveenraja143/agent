import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function HomeScreen() {
  const router = useRouter();
  const [stats, setStats] = useState({ posts: 0, certificates: 0, jobs: 0 });

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    const posts = await AsyncStorage.getItem('total_posts');
    const certs = await AsyncStorage.getItem('total_certificates');
    const jobs = await AsyncStorage.getItem('total_jobs_found');
    setStats({ posts: parseInt(posts || '0'), certificates: parseInt(certs || '0'), jobs: parseInt(jobs || '0') });
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.greeting}>Welcome to IPG!</Text>
        <Text style={styles.subtitle}>LinkedIn Auto Poster</Text>
      </View>
      <View style={styles.statsContainer}>
        <View style={styles.statCard}><Ionicons name="document-text" size={32} color="#0a66c2" /><Text style={styles.statNumber}>{stats.posts}</Text><Text style={styles.statLabel}>Posts</Text></View>
        <View style={styles.statCard}><Ionicons name="award" size={32} color="#057642" /><Text style={styles.statNumber}>{stats.certificates}</Text><Text style={styles.statLabel}>Certificates</Text></View>
        <View style={styles.statCard}><Ionicons name="briefcase" size={32} color="#c25e0a" /><Text style={styles.statNumber}>{stats.jobs}</Text><Text style={styles.statLabel}>Jobs Found</Text></View>
      </View>
      <Text style={styles.sectionTitle}>Quick Actions</Text>
      <TouchableOpacity style={[styles.actionCard, { backgroundColor: '#0a66c2' }]} onPress={() => router.push('/(tabs)/upload')}>
        <Ionicons name="cloud-upload" size={28} color="#fff" />
        <View style={styles.actionText}><Text style={styles.actionTitle}>Upload Certificate</Text><Text style={styles.actionSubtitle}>Auto-generate and post to LinkedIn</Text></View>
        <Ionicons name="chevron-forward" size={24} color="#fff" />
      </TouchableOpacity>
      <TouchableOpacity style={[styles.actionCard, { backgroundColor: '#057642' }]} onPress={() => router.push('/(tabs)/resume')}>
        <Ionicons name="document-text" size={28} color="#fff" />
        <View style={styles.actionText}><Text style={styles.actionTitle}>View Resume</Text><Text style={styles.actionSubtitle}>Check skills and certificates</Text></View>
        <Ionicons name="chevron-forward" size={24} color="#fff" />
      </TouchableOpacity>
      <TouchableOpacity style={[styles.actionCard, { backgroundColor: '#7c3aed' }]} onPress={() => router.push('/(tabs)/settings')}>
        <Ionicons name="settings" size={28} color="#fff" />
        <View style={styles.actionText}><Text style={styles.actionTitle}>Auto-Post Settings</Text><Text style={styles.actionSubtitle}>Schedule daily posts</Text></View>
        <Ionicons name="chevron-forward" size={24} color="#fff" />
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { padding: 20, paddingTop: 50, backgroundColor: '#0a66c2' },
  greeting: { fontSize: 28, fontWeight: 'bold', color: '#fff' },
  subtitle: { fontSize: 16, color: '#e0e0e0', marginTop: 4 },
  statsContainer: { flexDirection: 'row', justifyContent: 'space-around', padding: 20, marginTop: -30 },
  statCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, alignItems: 'center', width: '30%', elevation: 3 },
  statNumber: { fontSize: 24, fontWeight: 'bold', marginTop: 8, color: '#333' },
  statLabel: { fontSize: 12, color: '#666', marginTop: 4 },
  sectionTitle: { fontSize: 20, fontWeight: 'bold', paddingHorizontal: 20, marginBottom: 12, color: '#333' },
  actionCard: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 20, marginBottom: 12, padding: 16, borderRadius: 12, elevation: 2 },
  actionText: { flex: 1, marginLeft: 12 },
  actionTitle: { fontSize: 16, fontWeight: 'bold', color: '#fff' },
  actionSubtitle: { fontSize: 12, color: '#e0e0e0', marginTop: 2 },
});
