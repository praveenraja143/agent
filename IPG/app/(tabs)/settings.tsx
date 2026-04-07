import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity, Switch, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

export default function SettingsScreen() {
  const [linkedinEmail, setLinkedinEmail] = useState('');
  const [linkedinPassword, setLinkedinPassword] = useState('');
  const [openrouterKey, setOpenrouterKey] = useState('');
  const [whatsappPhone, setWhatsappPhone] = useState('');
  const [skills, setSkills] = useState('');
  const [locations, setLocations] = useState('');
  const [saving, setSaving] = useState(false);

  const [schedule, setSchedule] = useState({
    enabled: true,
    morningTime: '09:00',
    afternoonTime: '12:30',
    eveningTime: '18:00',
    morningEnabled: true,
    afternoonEnabled: true,
    eveningEnabled: true,
    includeHashtags: true,
  });

  useEffect(() => { loadSettings(); }, []);

  const loadSettings = async () => {
    try {
      const email = await AsyncStorage.getItem('LINKEDIN_EMAIL');
      const password = await AsyncStorage.getItem('LINKEDIN_PASSWORD');
      const apiKey = await AsyncStorage.getItem('OPENROUTER_API_KEY');
      const whatsapp = await AsyncStorage.getItem('WHATSAPP_PHONE');
      const userSkills = await AsyncStorage.getItem('SKILLS');
      const userLocations = await AsyncStorage.getItem('JOB_LOCATIONS');
      const savedSchedule = await AsyncStorage.getItem('POST_SCHEDULE');
      if (email) setLinkedinEmail(email);
      if (password) setLinkedinPassword(password);
      if (apiKey) setOpenrouterKey(apiKey);
      if (whatsapp) setWhatsappPhone(whatsapp);
      if (userSkills) setSkills(userSkills);
      if (userLocations) setLocations(userLocations);
      if (savedSchedule) setSchedule(JSON.parse(savedSchedule));
    } catch (error) { console.error(error); }
  };

  const saveSettings = async () => {
    if (!linkedinEmail || !openrouterKey) { Alert.alert('Missing', 'LinkedIn Email and API Key required'); return; }
    setSaving(true);
    try {
      await AsyncStorage.setItem('LINKEDIN_EMAIL', linkedinEmail);
      await AsyncStorage.setItem('LINKEDIN_PASSWORD', linkedinPassword);
      await AsyncStorage.setItem('OPENROUTER_API_KEY', openrouterKey);
      await AsyncStorage.setItem('WHATSAPP_PHONE', whatsappPhone);
      await AsyncStorage.setItem('SKILLS', skills);
      await AsyncStorage.setItem('JOB_LOCATIONS', locations);
      await AsyncStorage.setItem('POST_SCHEDULE', JSON.stringify(schedule));
      Alert.alert('Success!', 'Settings saved. Auto-posting active!');
    } catch (error) { Alert.alert('Error', 'Failed to save'); }
    finally { setSaving(false); }
  };

  const clearAllData = () => {
    Alert.alert('Clear All', 'Delete all data?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: async () => { await AsyncStorage.clear(); Alert.alert('Done', 'All data cleared'); } },
    ]);
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}><Text style={styles.title}>Settings</Text><Text style={styles.subtitle}>Configure auto-posting and preferences</Text></View>

      {schedule.enabled && (
        <View style={styles.statusBar}>
          <View style={styles.statusDot} />
          <View><Text style={styles.statusText}>Auto-Posting Active</Text><Text style={styles.statusSubtext}>Morning {schedule.morningTime} | Afternoon {schedule.afternoonTime} | Evening {schedule.eveningTime}</Text></View>
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Auto-Post Schedule</Text>
        <View style={styles.toggleRow}><Text style={styles.toggleLabel}>Enable Daily Auto-Post</Text><Switch value={schedule.enabled} onValueChange={(val) => setSchedule({ ...schedule, enabled: val })} trackColor={{ false: '#ccc', true: '#057642' }} thumbColor="#fff" /></View>
        {schedule.enabled && (
          <>
            <View style={styles.scheduleCard}>
              <View style={styles.scheduleItem}><Ionicons name="sunny" size={20} color="#c25e0a" /><Text style={styles.scheduleLabel}>Morning</Text><Text style={styles.timeText}>{schedule.morningTime}</Text><Switch value={schedule.morningEnabled} onValueChange={(val) => setSchedule({ ...schedule, morningEnabled: val })} trackColor={{ false: '#ccc', true: '#057642' }} thumbColor="#fff" /></View>
              <View style={styles.scheduleItem}><Ionicons name="partly-sunny" size={20} color="#0a66c2" /><Text style={styles.scheduleLabel}>Afternoon</Text><Text style={styles.timeText}>{schedule.afternoonTime}</Text><Switch value={schedule.afternoonEnabled} onValueChange={(val) => setSchedule({ ...schedule, afternoonEnabled: val })} trackColor={{ false: '#ccc', true: '#057642' }} thumbColor="#fff" /></View>
              <View style={styles.scheduleItem}><Ionicons name="moon" size={20} color="#7c3aed" /><Text style={styles.scheduleLabel}>Evening</Text><Text style={styles.timeText}>{schedule.eveningTime}</Text><Switch value={schedule.eveningEnabled} onValueChange={(val) => setSchedule({ ...schedule, eveningEnabled: val })} trackColor={{ false: '#ccc', true: '#057642' }} thumbColor="#fff" /></View>
            </View>
            <View style={styles.toggleRow}><Text style={styles.toggleLabel}>Include Hashtags</Text><Switch value={schedule.includeHashtags} onValueChange={(val) => setSchedule({ ...schedule, includeHashtags: val })} trackColor={{ false: '#ccc', true: '#0a66c2' }} thumbColor="#fff" /></View>
          </>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>LinkedIn Account</Text>
        <TextInput style={styles.input} value={linkedinEmail} onChangeText={setLinkedinEmail} placeholder="LinkedIn Email" placeholderTextColor="#999" keyboardType="email-address" autoCapitalize="none" />
        <TextInput style={styles.input} value={linkedinPassword} onChangeText={setLinkedinPassword} placeholder="LinkedIn Password" placeholderTextColor="#999" secureTextEntry />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>AI Configuration</Text>
        <TextInput style={styles.input} value={openrouterKey} onChangeText={setOpenrouterKey} placeholder="OpenRouter API Key" placeholderTextColor="#999" secureTextEntry />
        <Text style={styles.hint}>Free key from openrouter.ai</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Job Search</Text>
        <TextInput style={[styles.input, styles.multilineInput]} value={skills} onChangeText={setSkills} placeholder="Skills: Python, JavaScript, React" placeholderTextColor="#999" multiline />
        <TextInput style={[styles.input, styles.multilineInput]} value={locations} onChangeText={setLocations} placeholder="Locations: Chennai, Bangalore, Remote" placeholderTextColor="#999" multiline />
      </View>

      <TouchableOpacity style={styles.saveBtn} onPress={saveSettings} disabled={saving}>
        <Ionicons name="save" size={20} color="#fff" /><Text style={styles.saveBtnText}>Save All Settings</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.clearBtn} onPress={clearAllData}>
        <Ionicons name="trash" size={18} color="#c20a0a" /><Text style={styles.clearBtnText}>Clear All Data</Text>
      </TouchableOpacity>

      <View style={styles.footer}><Text style={styles.footerText}>IPG v1.0 - LinkedIn Auto Poster</Text><Text style={styles.footerText}>Auto-post 3x daily with AI content</Text></View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { padding: 20, paddingTop: 50, backgroundColor: '#0a66c2' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff' },
  subtitle: { fontSize: 14, color: '#e0e0e0', marginTop: 4 },
  statusBar: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#e8f5e9', margin: 16, padding: 14, borderRadius: 10 },
  statusDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#057642', marginRight: 10 },
  statusText: { fontSize: 14, fontWeight: '600', color: '#057642' },
  statusSubtext: { fontSize: 12, color: '#666', marginTop: 2 },
  section: { backgroundColor: '#fff', margin: 16, marginTop: 0, borderRadius: 12, padding: 16, elevation: 2 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 16, color: '#333' },
  toggleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10 },
  toggleLabel: { fontSize: 15, color: '#333' },
  scheduleCard: { backgroundColor: '#f9f9f9', borderRadius: 10, padding: 12, marginBottom: 12 },
  scheduleItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#eee' },
  scheduleLabel: { flex: 1, marginLeft: 10, fontSize: 14, fontWeight: '600', color: '#333' },
  timeText: { backgroundColor: '#0a66c2', color: '#fff', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 6, marginRight: 10, fontSize: 14, fontWeight: '600' },
  input: { backgroundColor: '#f9f9f9', borderRadius: 8, padding: 12, fontSize: 15, borderWidth: 1, borderColor: '#e0e0e0', marginBottom: 12, minHeight: 44 },
  multilineInput: { minHeight: 70, textAlignVertical: 'top' },
  hint: { fontSize: 12, color: '#0a66c2', marginTop: -8, marginBottom: 8 },
  saveBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#0a66c2', marginHorizontal: 16, padding: 16, borderRadius: 12, elevation: 2 },
  saveBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginLeft: 8 },
  clearBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginHorizontal: 16, padding: 14, borderRadius: 12, borderWidth: 1, borderColor: '#c20a0a' },
  clearBtnText: { color: '#c20a0a', fontSize: 15, fontWeight: '600', marginLeft: 8 },
  footer: { alignItems: 'center', padding: 30 },
  footerText: { fontSize: 12, color: '#999' },
});
