import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, ScrollView, TextInput, Alert, ActivityIndicator } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function UploadScreen() {
  const [certificate, setCertificate] = useState<string | null>(null);
  const [certName, setCertName] = useState('');
  const [issuingOrg, setIssuingOrg] = useState('');
  const [skills, setSkills] = useState('');
  const [generatedContent, setGeneratedContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [autoUpdateResume, setAutoUpdateResume] = useState(true);
  const [currentSkills, setCurrentSkills] = useState<string[]>([]);
  const [newSkills, setNewSkills] = useState<string[]>([]);

  useEffect(() => { loadCurrentSkills(); }, []);

  const loadCurrentSkills = async () => {
    const stored = await AsyncStorage.getItem('SKILLS');
    if (stored) setCurrentSkills(stored.split(',').map(s => s.trim()));
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, allowsEditing: true, aspect: [4, 3], quality: 0.8 });
    if (!result.canceled && result.assets[0]) {
      setCertificate(result.assets[0].uri);
      setCertName(result.assets[0].uri.split('/').pop()?.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ') || 'Certificate');
    }
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') { Alert.alert('Permission needed', 'Camera permission required'); return; }
    const result = await ImagePicker.launchCameraAsync({ allowsEditing: true, aspect: [4, 3], quality: 0.8 });
    if (!result.canceled && result.assets[0]) { setCertificate(result.assets[0].uri); setCertName('New Certificate'); }
  };

  const suggestSkills = () => {
    const suggestions: string[] = [];
    const c = certName.toLowerCase();
    if (c.includes('python')) suggestions.push('Python');
    if (c.includes('javascript') || c.includes('js')) suggestions.push('JavaScript');
    if (c.includes('react')) suggestions.push('React');
    if (c.includes('machine') || c.includes('ml')) suggestions.push('Machine Learning');
    if (c.includes('data')) suggestions.push('Data Analysis');
    if (c.includes('web')) suggestions.push('Web Development');
    if (c.includes('cloud') || c.includes('aws')) suggestions.push('Cloud Computing');
    const newS = suggestions.filter(s => !currentSkills.includes(s));
    if (newS.length > 0) Alert.alert('Suggested Skills', `Add: ${newS.join(', ')}`, [{ text: 'Skip' }, { text: 'Add All', onPress: () => setSkills(newS.join(', ')) }]);
  };

  const generateContent = async () => {
    if (!certName || !issuingOrg) { Alert.alert('Missing Info', 'Enter certificate name and organization'); return; }
    setLoading(true);
    try {
      const apiKey = await AsyncStorage.getItem('OPENROUTER_API_KEY');
      const skillsArr = skills.split(',').map(s => s.trim()).filter(s => s);
      const prompt = `Create a professional LinkedIn post for earning: ${certName} from ${issuingOrg}. Skills: ${skillsArr.join(', ')}. Professional tone, emojis, under 200 words. No hashtags.`;
      const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: 'qwen/qwen-2.5-coder-32b-instruct', messages: [{ role: 'user', content: prompt }], max_tokens: 400, temperature: 0.8 }),
      });
      const data = await res.json();
      const content = data.choices?.[0]?.message?.content || `Excited to share I earned ${certName} from ${issuingOrg}! Skills: ${skillsArr.join(', ')}. Always learning!`;
      const hashtags = getHashtags(certName, skillsArr, issuingOrg);
      setGeneratedContent(`${content}\n\n${hashtags}`);
      setStep(2);
    } catch (error) { Alert.alert('Error', 'Failed to generate content'); }
    finally { setLoading(false); }
  };

  const handlePost = async () => {
    setLoading(true);
    try {
      const skillsArr = skills.split(',').map(s => s.trim()).filter(s => s);
      if (autoUpdateResume && skillsArr.length > 0) {
        const existing = await AsyncStorage.getItem('SKILLS');
        const existingArr = existing ? existing.split(',').map(s => s.trim()) : [];
        const newSk = skillsArr.filter(s => !existingArr.some(e => e.toLowerCase() === s.toLowerCase()));
        if (newSk.length > 0) {
          const all = [...existingArr, ...newSk];
          await AsyncStorage.setItem('SKILLS', all.join(','));
          setCurrentSkills(all); setNewSkills(newSk);
        }
      }
      const count = await AsyncStorage.getItem('total_certificates');
      await AsyncStorage.setItem('total_certificates', String(parseInt(count || '0') + 1));
      const history = await AsyncStorage.getItem('post_history');
      const posts = history ? JSON.parse(history) : [];
      posts.unshift({ id: Date.now().toString(), type: 'certificate', content: generatedContent, date: new Date().toLocaleString('en-IN'), status: 'posted' });
      await AsyncStorage.setItem('post_history', JSON.stringify(posts.slice(0, 50)));
      Alert.alert('Success!', 'Certificate posted and resume updated!', [{ text: 'OK', onPress: resetForm }]);
    } catch (error) { Alert.alert('Error', 'Failed to post'); }
    finally { setLoading(false); }
  };

  const resetForm = () => { setCertificate(null); setCertName(''); setIssuingOrg(''); setSkills(''); setGeneratedContent(''); setStep(1); setNewSkills([]); };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}><Text style={styles.title}>Upload Certificate</Text><Text style={styles.subtitle}>AI generates content, hashtags, updates resume</Text></View>
      {step === 1 && (
        <View style={styles.form}>
          <Text style={styles.label}>Certificate Image</Text>
          {certificate ? (
            <View style={styles.imageContainer}><Image source={{ uri: certificate }} style={styles.image} /><TouchableOpacity style={styles.changeBtn} onPress={pickImage}><Ionicons name="refresh" size={20} color="#fff" /><Text style={styles.changeBtnText}>Change</Text></TouchableOpacity></View>
          ) : (
            <View style={styles.uploadButtons}>
              <TouchableOpacity style={styles.uploadBtn} onPress={pickImage}><Ionicons name="image" size={24} color="#0a66c2" /><Text style={styles.uploadBtnText}>Gallery</Text></TouchableOpacity>
              <TouchableOpacity style={[styles.uploadBtn, styles.cameraBtn]} onPress={takePhoto}><Ionicons name="camera" size={24} color="#fff" /><Text style={[styles.uploadBtnText, styles.cameraBtnText]}>Camera</Text></TouchableOpacity>
            </View>
          )}
          <View style={styles.inputGroup}><Text style={styles.label}>Certificate Name</Text><TextInput style={styles.input} value={certName} onChangeText={setCertName} placeholder="e.g., Python for Data Science" placeholderTextColor="#999" /></View>
          <View style={styles.inputGroup}><Text style={styles.label}>Issuing Organization</Text><TextInput style={styles.input} value={issuingOrg} onChangeText={setIssuingOrg} placeholder="e.g., Coursera, Udemy" placeholderTextColor="#999" /></View>
          <View style={styles.inputGroup}>
            <View style={styles.labelRow}><Text style={styles.label}>Skills Learned</Text><TouchableOpacity style={styles.suggestBtn} onPress={suggestSkills}><Ionicons name="bulb" size={16} color="#c25e0a" /><Text style={styles.suggestBtnText}>Suggest</Text></TouchableOpacity></View>
            <TextInput style={[styles.input, styles.multilineInput]} value={skills} onChangeText={setSkills} placeholder="e.g., Python, Machine Learning" placeholderTextColor="#999" multiline />
          </View>
          {currentSkills.length > 0 && (
            <View style={styles.currentSkills}><Text style={styles.currentSkillsTitle}>Current Skills ({currentSkills.length})</Text>
              <View style={styles.skillsWrap}>{currentSkills.slice(0, 8).map((s, i) => <View key={i} style={styles.skillChip}><Text style={styles.skillChipText}>{s}</Text></View>)}</View>
            </View>
          )}
          <View style={styles.toggleRow}><View><Text style={styles.toggleTitle}>Auto-Update Resume</Text><Text style={styles.toggleDesc}>New skills added to resume</Text></View><Switch value={autoUpdateResume} onValueChange={setAutoUpdateResume} trackColor={{ false: '#ccc', true: '#057642' }} thumbColor="#fff" /></View>
          <TouchableOpacity style={[styles.primaryBtn, (!certificate || loading) && styles.disabledBtn]} onPress={generateContent} disabled={!certificate || loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <><Ionicons name="sparkles" size={20} color="#fff" /><Text style={styles.primaryBtnText}>Generate and Preview</Text></>}
          </TouchableOpacity>
        </View>
      )}
      {step === 2 && (
        <View style={styles.form}>
          <View style={styles.previewSection}>
            <View style={styles.previewHeader}><Ionicons name="checkmark-circle" size={24} color="#057642" /><Text style={styles.previewTitle}>Generated Content</Text></View>
            {certificate && <Image source={{ uri: certificate }} style={styles.previewImage} />}
            <View style={styles.contentPreview}><Text style={styles.contentText}>{generatedContent}</Text></View>
            {autoUpdateResume && newSkills.length > 0 && (
              <View style={styles.resumeUpdateBox}><Ionicons name="document-text" size={20} color="#057642" /><View style={styles.resumeUpdateContent}><Text style={styles.resumeUpdateTitle}>Resume Updated!</Text><Text style={styles.resumeUpdateSkills}>{newSkills.join(' + ')}</Text></View></View>
            )}
            <TouchableOpacity style={styles.editBtn} onPress={() => setStep(1)}><Ionicons name="create" size={18} color="#0a66c2" /><Text style={styles.editBtnText}>Edit Details</Text></TouchableOpacity>
          </View>
          <TouchableOpacity style={styles.postBtn} onPress={handlePost} disabled={loading}>{loading ? <ActivityIndicator color="#fff" /> : <><Ionicons name="send" size={20} color="#fff" /><Text style={styles.postBtnText}>Post to LinkedIn</Text></>}</TouchableOpacity>
          <TouchableOpacity style={styles.cancelBtn} onPress={resetForm}><Text style={styles.cancelBtnText}>Cancel</Text></TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

function getHashtags(certName: string, skills: string[], org: string): string {
  const tags = new Set<string>();
  tags.add('#Certification'); tags.add('#ContinuousLearning'); tags.add('#ProfessionalDevelopment'); tags.add('#CareerGrowth'); tags.add('#Learning'); tags.add('#Achievement'); tags.add('#LinkedIn'); tags.add('#SkillDevelopment');
  if (org) tags.add(`#${org.replace(/\s+/g, '')}`);
  skills.slice(0, 3).forEach(s => tags.add(`#${s.replace(/\s+/g, '')}`));
  return Array.from(tags).slice(0, 12).join(' ');
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { padding: 20, paddingTop: 50, backgroundColor: '#0a66c2' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff' },
  subtitle: { fontSize: 13, color: '#e0e0e0', marginTop: 4 },
  form: { padding: 20 },
  label: { fontSize: 16, fontWeight: '600', marginBottom: 8, color: '#333' },
  labelRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  uploadButtons: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 20 },
  uploadBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', padding: 20, borderRadius: 12, width: '45%', justifyContent: 'center', elevation: 2 },
  cameraBtn: { backgroundColor: '#0a66c2' },
  uploadBtnText: { marginLeft: 8, fontSize: 14, fontWeight: '600', color: '#0a66c2' },
  cameraBtnText: { color: '#fff' },
  imageContainer: { alignItems: 'center', marginBottom: 20 },
  image: { width: '100%', height: 200, borderRadius: 12 },
  changeBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#0a66c2', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8, marginTop: 8 },
  changeBtnText: { color: '#fff', marginLeft: 6, fontWeight: '600' },
  inputGroup: { marginBottom: 16 },
  input: { backgroundColor: '#fff', borderRadius: 8, padding: 12, fontSize: 16, borderWidth: 1, borderColor: '#ddd', minHeight: 48 },
  multilineInput: { minHeight: 70, textAlignVertical: 'top' },
  primaryBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#0a66c2', padding: 16, borderRadius: 12, marginTop: 10 },
  disabledBtn: { opacity: 0.5 },
  primaryBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginLeft: 8 },
  previewSection: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 16, elevation: 2 },
  previewHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  previewTitle: { fontSize: 18, fontWeight: 'bold', marginLeft: 8, color: '#333' },
  previewImage: { width: '100%', height: 180, borderRadius: 8, marginBottom: 12 },
  contentPreview: { backgroundColor: '#f9f9f9', borderRadius: 8, padding: 12, marginBottom: 12 },
  contentText: { fontSize: 14, lineHeight: 22, color: '#333' },
  editBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', padding: 10 },
  editBtnText: { color: '#0a66c2', fontWeight: '600', marginLeft: 6 },
  postBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#057642', padding: 16, borderRadius: 12, marginBottom: 10 },
  postBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginLeft: 8 },
  cancelBtn: { alignItems: 'center', padding: 12 },
  cancelBtnText: { color: '#c25e0a', fontSize: 16, fontWeight: '600' },
  suggestBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff3e0', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16 },
  suggestBtnText: { fontSize: 12, color: '#c25e0a', fontWeight: '600', marginLeft: 4 },
  currentSkills: { backgroundColor: '#f0f7ff', borderRadius: 10, padding: 12, marginBottom: 16 },
  currentSkillsTitle: { fontSize: 13, fontWeight: '600', color: '#0a66c2', marginBottom: 8 },
  skillsWrap: { flexDirection: 'row', flexWrap: 'wrap' },
  skillChip: { backgroundColor: '#fff', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 14, marginRight: 6, marginBottom: 4, borderWidth: 1, borderColor: '#d0e3f7' },
  skillChipText: { fontSize: 11, color: '#0a66c2', fontWeight: '500' },
  toggleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 16, elevation: 1 },
  toggleTitle: { fontSize: 15, fontWeight: '600', color: '#333' },
  toggleDesc: { fontSize: 12, color: '#999', marginTop: 2 },
  resumeUpdateBox: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#e8f5e9', borderRadius: 8, padding: 12, marginBottom: 12 },
  resumeUpdateContent: { flex: 1, marginLeft: 10 },
  resumeUpdateTitle: { fontSize: 14, fontWeight: '600', color: '#057642' },
  resumeUpdateSkills: { fontSize: 12, color: '#333', marginTop: 2 },
});
