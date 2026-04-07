import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as DocumentPicker from 'expo-document-picker';

export default function ResumeScreen() {
  const [skills, setSkills] = useState<string[]>([]);
  const [resumeName, setResumeName] = useState('');
  const [certificates, setCertificates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const storedSkills = await AsyncStorage.getItem('SKILLS');
      const storedResume = await AsyncStorage.getItem('RESUME_NAME');
      const storedCerts = await AsyncStorage.getItem('certificates_added');
      if (storedSkills) setSkills(storedSkills.split(',').map(s => s.trim()));
      if (storedResume) setResumeName(storedResume);
      if (storedCerts) setCertificates(JSON.parse(storedCerts));
    } catch (error) { console.error(error); }
    finally { setLoading(false); }
  };

  const uploadNewResume = async () => {
    const result = await DocumentPicker.getDocumentAsync({ type: ['application/pdf'], copyToCacheDirectory: true });
    if (!result.canceled && result.assets[0]) {
      await AsyncStorage.setItem('RESUME_FILE', result.assets[0].uri);
      await AsyncStorage.setItem('RESUME_NAME', result.assets[0].name);
      setResumeName(result.assets[0].name);
      Alert.alert('Resume Updated!', result.assets[0].name);
    }
  };

  const addSkillManually = () => {
    Alert.prompt('Add Skill', 'Enter skill:', async (skill) => {
      if (skill?.trim()) {
        const updated = [...skills, skill.trim()];
        setSkills(updated);
        await AsyncStorage.setItem('SKILLS', updated.join(','));
      }
    }, 'plain-text');
  };

  const removeSkill = async (index: number) => {
    const updated = skills.filter((_, i) => i !== index);
    setSkills(updated);
    await AsyncStorage.setItem('SKILLS', updated.join(','));
  };

  if (loading) return <View style={styles.loadingContainer}><ActivityIndicator size="large" color="#0a66c2" /></View>;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}><Text style={styles.title}>My Resume</Text><Text style={styles.subtitle}>{skills.length} skills tracked</Text></View>
      <View style={styles.section}>
        <View style={styles.sectionHeader}><Ionicons name="document-text" size={22} color="#0a66c2" /><Text style={styles.sectionTitle}>Current Resume</Text></View>
        {resumeName ? <View style={styles.resumeCard}><Ionicons name="checkmark-circle" size={20} color="#057642" /><Text style={styles.resumeName}>{resumeName}</Text></View> : <Text style={styles.emptyText}>No resume uploaded</Text>}
        <TouchableOpacity style={styles.uploadBtn} onPress={uploadNewResume}><Ionicons name="cloud-upload" size={18} color="#fff" /><Text style={styles.uploadBtnText}>Upload New Resume</Text></TouchableOpacity>
      </View>
      <View style={styles.section}>
        <View style={styles.sectionHeader}><Ionicons name="code-slash" size={22} color="#057642" /><Text style={styles.sectionTitle}>Skills ({skills.length})</Text><TouchableOpacity style={styles.addSkillBtn} onPress={addSkillManually}><Ionicons name="add" size={18} color="#fff" /></TouchableOpacity></View>
        <View style={styles.skillsGrid}>
          {skills.map((skill, index) => (
            <TouchableOpacity key={index} style={styles.skillCard} onPress={() => removeSkill(index)} activeOpacity={0.7}>
              <Text style={styles.skillName}>{skill}</Text><Ionicons name="close-circle" size={16} color="#c20a0a" />
            </TouchableOpacity>
          ))}
        </View>
        {skills.length === 0 && <Text style={styles.emptyText}>No skills yet</Text>}
      </View>
      <View style={styles.section}>
        <View style={styles.sectionHeader}><Ionicons name="award" size={22} color="#c25e0a" /><Text style={styles.sectionTitle}>Certificates ({certificates.length})</Text></View>
        {certificates.map((cert, index) => (
          <View key={index} style={styles.certCard}>
            <View style={styles.certIcon}><Ionicons name="checkmark-done" size={20} color="#fff" /></View>
            <View style={styles.certContent}><Text style={styles.certName}>{cert.certName}</Text><Text style={styles.certSkills}>{cert.skills?.join(' + ')}</Text><Text style={styles.certDate}>{new Date(cert.date).toLocaleDateString('en-IN')}</Text></View>
          </View>
        ))}
        {certificates.length === 0 && <Text style={styles.emptyText}>No certificates added yet</Text>}
      </View>
      <View style={styles.statsSection}>
        <Text style={styles.statsTitle}>Growth Stats</Text>
        <View style={styles.statsGrid}>
          <View style={styles.statCard}><Text style={styles.statNumber}>{skills.length}</Text><Text style={styles.statLabel}>Total Skills</Text></View>
          <View style={styles.statCard}><Text style={styles.statNumber}>{certificates.length}</Text><Text style={styles.statLabel}>Certificates</Text></View>
          <View style={styles.statCard}><Text style={styles.statNumber}>{certificates.reduce((a, c) => a + (c.skills?.length || 0), 0)}</Text><Text style={styles.statLabel}>Skills from Certs</Text></View>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { padding: 20, paddingTop: 50, backgroundColor: '#0a66c2' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff' },
  subtitle: { fontSize: 14, color: '#e0e0e0', marginTop: 4 },
  section: { backgroundColor: '#fff', margin: 16, borderRadius: 12, padding: 16, elevation: 2 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 14 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', marginLeft: 8, flex: 1, color: '#333' },
  resumeCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f0f7ff', borderRadius: 8, padding: 12, marginBottom: 12 },
  resumeName: { fontSize: 14, fontWeight: '600', color: '#0a66c2', marginLeft: 8, flex: 1 },
  uploadBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#0a66c2', padding: 12, borderRadius: 8 },
  uploadBtnText: { color: '#fff', fontWeight: '600', marginLeft: 6 },
  addSkillBtn: { backgroundColor: '#057642', width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  skillsGrid: { flexDirection: 'row', flexWrap: 'wrap' },
  skillCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f0f7ff', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, marginRight: 8, marginBottom: 8, borderWidth: 1, borderColor: '#d0e3f7' },
  skillName: { fontSize: 13, color: '#0a66c2', fontWeight: '600', marginRight: 6 },
  certCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f9f9f9', borderRadius: 8, padding: 12, marginBottom: 10 },
  certIcon: { backgroundColor: '#c25e0a', width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  certContent: { flex: 1, marginLeft: 12 },
  certName: { fontSize: 14, fontWeight: '600', color: '#333' },
  certSkills: { fontSize: 12, color: '#666', marginTop: 2 },
  certDate: { fontSize: 11, color: '#999', marginTop: 4 },
  emptyText: { fontSize: 14, color: '#999', textAlign: 'center', padding: 20 },
  statsSection: { margin: 16 },
  statsTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 12, color: '#333' },
  statsGrid: { flexDirection: 'row', justifyContent: 'space-around' },
  statCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, alignItems: 'center', width: '30%', elevation: 2 },
  statNumber: { fontSize: 24, fontWeight: 'bold', color: '#0a66c2' },
  statLabel: { fontSize: 11, color: '#666', marginTop: 4, textAlign: 'center' },
});
