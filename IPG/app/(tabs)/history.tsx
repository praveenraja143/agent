import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

export default function HistoryScreen() {
  const [posts, setPosts] = useState<any[]>([]);
  useEffect(() => { loadHistory(); }, []);
  const loadHistory = async () => {
    const history = await AsyncStorage.getItem('post_history');
    if (history) setPosts(JSON.parse(history));
  };
  const getStatusIcon = (status: string) => {
    if (status === 'posted') return { name: 'checkmark-circle' as const, color: '#057642' };
    if (status === 'failed') return { name: 'close-circle' as const, color: '#c20a0a' };
    return { name: 'time' as const, color: '#c25e0a' };
  };
  const renderItem = ({ item }: { item: any }) => {
    const icon = getStatusIcon(item.status);
    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.typeBadge}><Ionicons name={item.type === 'certificate' ? 'award' : 'document-text'} size={16} color="#0a66c2" /><Text style={[styles.typeText, { color: '#0a66c2' }]}>{item.type}</Text></View>
          <View style={styles.status}><Ionicons name={icon.name} size={18} color={icon.color} /><Text style={[styles.statusText, { color: icon.color }]}>{item.status}</Text></View>
        </View>
        <Text style={styles.content} numberOfLines={3}>{item.content}</Text>
        <Text style={styles.date}>{item.date}</Text>
      </View>
    );
  };
  return (
    <View style={styles.container}>
      <View style={styles.header}><Text style={styles.title}>Post History</Text><Text style={styles.subtitle}>{posts.length} posts total</Text></View>
      {posts.length === 0 ? (
        <View style={styles.emptyState}><Ionicons name="document-text-outline" size={64} color="#ccc" /><Text style={styles.emptyTitle}>No posts yet</Text><Text style={styles.emptySubtitle}>Upload a certificate to get started</Text></View>
      ) : (
        <FlatList data={posts} renderItem={renderItem} keyExtractor={(item) => item.id} contentContainerStyle={styles.list} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { padding: 20, paddingTop: 50, backgroundColor: '#0a66c2' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff' },
  subtitle: { fontSize: 14, color: '#e0e0e0', marginTop: 4 },
  list: { padding: 16 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12, elevation: 2 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  typeBadge: { flexDirection: 'row', alignItems: 'center' },
  typeText: { marginLeft: 6, fontWeight: '600', fontSize: 14 },
  status: { flexDirection: 'row', alignItems: 'center' },
  statusText: { marginLeft: 4, fontSize: 12, fontWeight: '600' },
  content: { fontSize: 14, color: '#333', lineHeight: 20, marginBottom: 8 },
  date: { fontSize: 12, color: '#999' },
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyTitle: { fontSize: 20, fontWeight: 'bold', color: '#666', marginTop: 16 },
  emptySubtitle: { fontSize: 14, color: '#999', marginTop: 8, textAlign: 'center' },
});
